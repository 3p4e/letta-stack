"""
Letta/MemGPT Service — Connection to self-hosted Letta server.

Manages chapter agents, archives (DB1/DB2), document ingestion,
and RAG search via the Letta Python SDK.
"""

import logging
import os
from pathlib import Path
from typing import Dict, List, Optional, Any

from letta_client import Letta

from CONTENT_CREATOR_FRAMEWORK.file_handlers import get_handler, is_supported

logger = logging.getLogger(__name__)

# Model priority: best available
PRIMARY_MODEL = "deepseek/deepseek-reasoner"
FALLBACK_MODELS = [
    "openai/gpt-4o",
    "google_ai/gemini-2.5-pro",
]

# Embedding model handle for the app's own archives (DB1/DB2). Must be a
# handle the Letta server actually serves — the kvm4 server exposes the
# OpenAI-family handles (e.g. openai/text-embedding-3-small, which the shared
# specialist agents also use), not an Ollama handle. Overridable via env.
EMBEDDING_MODEL = os.getenv("LETTA_EMBEDDING_MODEL", "openai/text-embedding-3-small")


class LettaService:
    """
    Central service for all Letta/MemGPT interactions.

    Manages:
    - 10 chapter agents + 1 assembler agent
    - 2 archives: db1_regulatory, db2_entity_qms
    - Document ingestion into archives
    - RAG search across archives
    """

    def __init__(self, base_url: str = None):
        url = base_url or os.getenv("LETTA_BASE_URL", "http://localhost:8283")
        # Authenticate with the server token when provided (self-hosted Letta on
        # kvm4 requires it); fall back to "local" for an unsecured dev server.
        api_key = os.getenv("LETTA_API_KEY") or "local"
        self.client = Letta(base_url=url, api_key=api_key, timeout=300)
        self._agents: Dict[str, Any] = {}  # {role_name: agent_state}
        self._archives: Dict[str, Any] = {}  # {"db1": archive, "db2": archive}
        self._tools: Dict[str, str] = {}  # {tool_name: tool_id}
        self._external_agents: Dict[str, Any] = {}  # {server_name: agent_state}
        self._model = self._resolve_model()
        logger.info(f"LettaService connected to {url}, model={self._model}")

    def _resolve_model(self) -> str:
        """Pick the best available model from priority list."""
        available = {m.handle for m in self.client.models.list()}
        if PRIMARY_MODEL in available:
            return PRIMARY_MODEL
        for model in FALLBACK_MODELS:
            if model in available:
                logger.info(f"Primary model unavailable, using fallback: {model}")
                return model
        # Last resort
        return "openai/gpt-4o"

    # ─── Agent Management ───────────────────────────────────────

    def ensure_agents(self, agent_configs: Dict[str, dict]) -> Dict[str, Any]:
        """
        Create or retrieve all chapter agents.

        Args:
            agent_configs: Dict from agent_definitions.AGENT_CONFIGS

        Returns:
            Dict mapping role name to agent state.
        """
        # Get archive IDs to attach
        archive_ids = [a.id for a in self._archives.values()]

        # Look up agents already present on the Letta server by name
        existing = {a.name: a for a in self.client.agents.list()}

        for role, config in agent_configs.items():
            agent_name = config["name"]
            if agent_name in existing:
                agent = existing[agent_name]
                self._agents[role] = agent
                logger.info(f"Agent '{role}' already exists: {agent.id}")
            else:
                # Ensure tools are registered before agent creation
                if role == "researcher" or "perplexity_search" in config.get("tools", []):
                    self._register_research_tool()

                agent = self._create_agent(role, config)
                self._agents[role] = agent
                logger.info(f"Created agent '{role}': {agent.id}")

            # Attach archives (Direct RAG)
            for archive_id in archive_ids:
                try:
                    self.client.agents.archives.attach(agent_id=agent.id, archive_id=archive_id)
                except Exception as e:
                    # Often errors if already attached, which is fine
                    pass

        return self._agents

    def _create_agent(self, role: str, config: dict) -> Any:
        """Create a single Letta agent with role-specific configuration."""
        # Register tools if not yet done
        tool_ids = []
        for tool_name in config.get("tools", []):
            if tool_name in self._tools:
                tool_ids.append(self._tools[tool_name])

        # Define high-impact memory blocks
        memory_blocks = [
            {"label": "persona", "value": config.get("persona", f"EU GMP {role} specialist agent.")},
            {"label": "human", "value": "Initializing..."},
            {"label": "facility", "value": "Purely Plant GmbH - Cannabis EU GMP Facility. Standard: PREFIX - XX.YY.00"},
            {"label": "research", "value": "No research data yet."},
        ]

        agent = self.client.agents.create(
            name=config["name"],
            model=self._model,
            embedding=EMBEDDING_MODEL,
            system=config["system"],
            memory_blocks=memory_blocks,
            tool_ids=tool_ids if tool_ids else None,
            include_base_tools=True,
            tags=[f"role:{role}", "gmp-qms"],
        )
        return agent

    def get_agent(self, role: str) -> Any:
        """Get agent state by role name."""
        return self._agents.get(role)

    def send_message(self, role: str, message: str) -> str:
        """
        Send a message to a chapter agent and return the text response.

        Args:
            role: Agent role name (e.g., "purpose", "scope")
            message: The prompt/instruction to send

        Returns:
            Generated text content from the agent.
        """
        agent = self._agents.get(role)
        if not agent:
            raise ValueError(f"Agent '{role}' not found. Call ensure_agents() first.")

        return self._send_to_agent_id(agent.id, message)

    def _send_to_agent_id(self, agent_id: str, message: str) -> str:
        """Send a message to an agent by id and return its concatenated text."""
        response = self.client.agents.messages.create(
            agent_id=agent_id,
            input=message,
        )

        # Extract text from response messages
        texts = []
        for msg in response.messages:
            # LettaResponse messages have different types
            if hasattr(msg, "content") and msg.content:
                if isinstance(msg.content, str):
                    texts.append(msg.content)
                elif isinstance(msg.content, list):
                    for part in msg.content:
                        if hasattr(part, "text"):
                            texts.append(part.text)

        return "\n".join(texts) if texts else ""

    # ─── External (pre-existing) server agents ──────────────────

    def resolve_external_agent(self, name: str) -> Optional[Any]:
        """Look up an already-existing server agent by name (cached).

        Used for the hybrid strategy: reuse shared specialists that live on the
        Letta server (e.g. ``eu_gmp_compliance_expert``, ``gmp_rag_agent``)
        rather than recreating them. Returns None if the agent is absent.
        """
        if name in self._external_agents:
            return self._external_agents[name]
        try:
            for agent in self.client.agents.list():
                if agent.name == name:
                    self._external_agents[name] = agent
                    logger.info(f"Resolved external agent '{name}': {agent.id}")
                    return agent
        except Exception as e:
            logger.warning(f"Failed to resolve external agent '{name}': {e}")
        logger.warning(f"External agent '{name}' not found on Letta server")
        return None

    def send_to_external(self, name: str, message: str) -> str:
        """Send a message to a named pre-existing server agent.

        Returns "" if the agent cannot be resolved or the call fails, so callers
        can degrade gracefully to their own agents.
        """
        agent = self.resolve_external_agent(name)
        if not agent:
            return ""
        try:
            return self._send_to_agent_id(agent.id, message)
        except Exception as e:
            logger.warning(f"External agent '{name}' message failed: {e}")
            return ""

    def update_agent_context(self, role: str, context: str, block_label: str = "human"):
        """Update a specific memory block for an agent."""
        agent = self._agents.get(role)
        if not agent:
            return

        try:
            self.client.agents.blocks.update(
                block_label,
                agent_id=agent.id,
                value=context,
            )
        except Exception as e:
            logger.warning(f"Failed to update {block_label} context for agent '{role}': {e}")

    def update_facility_context(self, context: str):
        """Update the 'facility' memory block for ALL agents to ensure persistence."""
        for role, agent in self._agents.items():
            try:
                self.client.agents.blocks.update(
                    "facility",
                    agent_id=agent.id,
                    value=context,
                )
            except Exception as e:
                logger.warning(f"Failed to update facility context for agent '{role}': {e}")

    def reset_agent_messages(self, role: str):
        """Clear conversation history for an agent (between SOP generations)."""
        agent = self._agents.get(role)
        if agent:
            self.client.agents.messages.reset(agent_id=agent.id)

    # ─── Tool Registration ──────────────────────────────────────

    def register_tool(self, name: str, source_code: str, description: str) -> str:
        """
        Register a custom tool in Letta.

        Returns:
            Tool ID.
        """
        # Check if tool already exists
        for tool in self.client.tools.list():
            if tool.name == name:
                self._tools[name] = tool.id
                return tool.id

        tool = self.client.tools.create(
            source_code=source_code,
            description=description,
        )
        self._tools[name] = tool.id
        logger.info(f"Registered tool '{name}': {tool.id}")
        return tool.id

    # ─── Archive Management ─────────────────────────────────────

    def ensure_archives(self) -> Dict[str, Any]:
        """Create or retrieve DB1 and DB2 archives."""
        existing = {a.name: a for a in self.client.archives.list()}

        for archive_name in ["db1_regulatory", "db2_entity_qms"]:
            if archive_name in existing:
                self._archives[archive_name] = existing[archive_name]
                logger.info(f"Archive '{archive_name}' exists: {existing[archive_name].id}")
            else:
                archive = self.client.archives.create(
                    name=archive_name,
                    description=f"{'Official EU GMP regulatory guides' if 'db1' in archive_name else 'Previous entity QMS documents'}",
                    embedding=EMBEDDING_MODEL,
                )
                self._archives[archive_name] = archive
                logger.info(f"Created archive '{archive_name}': {archive.id}")

        return self._archives

    def get_archive(self, name: str) -> Any:
        """Get archive by name."""
        return self._archives.get(name)

    def clear_archive(self, archive_name: str) -> int:
        """
        Delete all passages from an archive.

        Args:
            archive_name: Name of the archive to clear.

        Returns:
            Number of passages deleted.
        """
        archive = self._archives.get(archive_name)
        if not archive:
            raise ValueError(f"Archive '{archive_name}' not found. Call ensure_archives() first.")

        # Get all passages
        try:
            passages = self.client.archives.passages.list(archive_id=archive.id)
            count = 0
            for passage in passages:
                try:
                    self.client.archives.passages.delete(passage_id=passage.id)
                    count += 1
                except Exception as e:
                    logger.warning(f"Failed to delete passage {passage.id}: {e}")

            logger.info(f"Cleared {count} passages from archive '{archive_name}'")
            return count
        except Exception as e:
            logger.error(f"Error clearing archive '{archive_name}': {e}")
            return 0

    def delete_archive(self, archive_name: str) -> bool:
        """
        Delete an archive completely.

        Args:
            archive_name: Name of the archive to delete.

        Returns:
            True if deleted.
        """
        archive = self._archives.get(archive_name)
        if archive:
            self.client.archives.delete(archive_id=archive.id)
            del self._archives[archive_name]
            return True
        return False

    # ─── Autonomous Research Tool ───────────────────────────────

    def _register_research_tool(self):
        """Register the Perplexity-powered research tool."""
        source_code = '''
def perplexity_search(query: str) -> str:
    """
    Perform an autonomous web search using the Perplexity API to find up-to-date EU GMP regulations, 
    industrial benchmarks, or cannabis-specific manufacturing standards.
    
    Args:
        query: The search query (e.g., 'latest EU GMP Annex 1 requirements for sterile cannabis oil')
        
    Returns:
        A clinical and technical summary of the search results with citations.
    """
    import os
    import requests
    import json
    
    api_key = os.getenv("PERPLEXITY_API_KEY")
    if not api_key:
        return "Error: PERPLEXITY_API_KEY not found in environment."
        
    url = "https://api.perplexity.ai/chat/completions"
    
    payload = {
        "model": "sonar-reasoning-pro",
        "messages": [
            {
                "role": "system",
                "content": "You are a specialized EU GMP Regulatory Research Agent. Provide technical, clinical, and precise summaries with citations. Focus on authoritative sources like EMA, EudraLex, ICH, and WHO."
            },
            {
                "role": "user",
                "content": query
            }
        ],
        "temperature": 0.2,
        "top_p": 0.9,
        "return_citations": True
    }
    
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    
    try:
        response = requests.post(url, json=payload, headers=headers, timeout=60)
        response.raise_for_status()
        data = response.json()
        content = data["choices"][0]["message"]["content"]
        
        # Format citations if present
        citations = data.get("citations", [])
        if citations:
            content += "\\n\\n**Sources:**\\n" + "\\n".join([f"- {c}" for c in citations])
            
        return content
    except Exception as e:
        return f"Error executing Perplexity search: {str(e)}"
'''
        self.register_tool("perplexity_search", source_code, "Autonomous web research for GMP regulations.")

    def recreate_archive(self, archive_name: str, description: str = None) -> Any:
        """
        Delete and recreate an archive with the current embedding model.

        Args:
            archive_name: Name of the archive.
            description: Optional description.

        Returns:
            New archive object.
        """
        # Delete if exists
        self.delete_archive(archive_name)

        # Create new archive with current embedding model
        desc = description or f"Archive: {archive_name}"
        archive = self.client.archives.create(
            name=archive_name,
            description=desc,
            embedding=EMBEDDING_MODEL,
        )
        self._archives[archive_name] = archive
        logger.info(f"Recreated archive '{archive_name}' with embedding model '{EMBEDDING_MODEL}': {archive.id}")
        return archive

    # ─── Document Ingestion ─────────────────────────────────────

    def ingest_file(
        self,
        archive_name: str,
        file_path: Path,
        tags: Optional[List[str]] = None,
        chunk_size: int = 1000,
        chunk_overlap: int = 200,
    ) -> int:
        """
        Parse a file and create passages in a Letta archive.

        Returns:
            Number of passages created.
        """
        archive = self._archives.get(archive_name)
        if not archive:
            raise ValueError(f"Archive '{archive_name}' not found. Call ensure_archives() first.")

        if not is_supported(file_path):
            logger.debug(f"Skipping unsupported file: {file_path.name}")
            return 0

        handler = get_handler(file_path)
        if not handler:
            return 0

        # Extract text
        text = handler.extract_text(file_path)
        if not text or not text.strip():
            logger.debug(f"No text extracted from: {file_path.name}")
            return 0

        # Chunk text
        chunks = self._chunk_text(text, chunk_size, chunk_overlap)
        if not chunks:
            return 0

        # Create passages
        file_tags = tags or []
        file_tags.append(f"file:{file_path.name}")
        file_tags.append(f"ext:{file_path.suffix.lower()}")

        count = 0
        for i, chunk in enumerate(chunks):
            try:
                self.client.archives.passages.create(
                    archive_id=archive.id,
                    text=chunk,
                    tags=file_tags + [f"chunk:{i+1}/{len(chunks)}"],
                )
                count += 1
            except Exception as e:
                logger.warning(f"Failed to create passage for {file_path.name} chunk {i+1}: {e}")

        logger.info(f"Ingested {file_path.name}: {count}/{len(chunks)} passages")
        return count

    def ingest_folder(
        self,
        archive_name: str,
        folder_path: str,
        tag_fn=None,
        recursive: bool = True,
    ) -> Dict[str, Any]:
        """
        Bulk ingest all supported files from a folder into an archive.

        Args:
            archive_name: Target archive name.
            folder_path: Path to folder.
            tag_fn: Optional function(file_path) -> List[str] for custom tags.
            recursive: Whether to recurse into subfolders.

        Returns:
            Stats dict.
        """
        folder = Path(folder_path)
        if not folder.exists():
            return {"error": f"Folder not found: {folder_path}"}

        pattern = "**/*" if recursive else "*"
        files = [f for f in folder.glob(pattern) if f.is_file() and not f.name.startswith(".")]

        stats = {"total": len(files), "ingested": 0, "skipped": 0, "errors": 0, "passages": 0}

        for file_path in sorted(files):
            if not is_supported(file_path):
                stats["skipped"] += 1
                continue

            tags = tag_fn(file_path) if tag_fn else []
            try:
                count = self.ingest_file(archive_name, file_path, tags=tags)
                if count > 0:
                    stats["ingested"] += 1
                    stats["passages"] += count
                else:
                    stats["skipped"] += 1
            except Exception as e:
                logger.error(f"Ingestion error for {file_path.name}: {e}")
                stats["errors"] += 1

        logger.info(
            f"Folder ingestion complete: {stats['ingested']} files, "
            f"{stats['passages']} passages, {stats['skipped']} skipped, {stats['errors']} errors"
        )
        return stats

    # ─── RAG Search ─────────────────────────────────────────────

    def search_archive(
        self,
        archive_name: str,
        query: str,
        top_k: int = 5,
        tags: Optional[List[str]] = None,
    ) -> List[Dict[str, Any]]:
        """
        Search an archive for relevant passages.

        Returns:
            List of dicts with text, tags, and score.
        """
        archive = self._archives.get(archive_name)
        if not archive:
            return []

        # Resolve the archival-search call across Letta SDK versions. Ingestion
        # in this service uses ``client.archives.passages.*``; older builds also
        # exposed a top-level ``client.passages.search``. Try the archive-scoped
        # namespace first (consistent with create/list/delete) and fall back.
        search_fn = None
        archives_ns = getattr(self.client, "archives", None)
        archive_passages = getattr(archives_ns, "passages", None)
        if archive_passages is not None and hasattr(archive_passages, "search"):
            search_fn = archive_passages.search
        elif hasattr(getattr(self.client, "passages", None), "search"):
            search_fn = self.client.passages.search

        if search_fn is None:
            # Surface loudly: a missing search API means RAG retrieval is
            # silently empty and every section generates with no archive context.
            logger.error(
                "Letta archival search API not found on client "
                "(neither archives.passages.search nor passages.search); "
                "RAG retrieval is disabled. Check the installed letta-client version."
            )
            return []

        try:
            results = search_fn(
                archive_id=archive.id,
                query=query,
                limit=top_k,
            )
            return [
                {
                    "text": r.passage.text,
                    "tags": r.passage.tags if hasattr(r.passage, "tags") else [],
                    "score": r.score,
                    "id": r.passage.id,
                }
                for r in results
            ]
        except Exception as e:
            logger.error(f"Archive search error ({archive_name}): {e}")
            return []

    def dual_db_search(
        self,
        query: str,
        db1_top_k: int = 5,
        db2_top_k: int = 5,
    ) -> Dict[str, List[Dict]]:
        """
        Search both DB1 (regulatory) and DB2 (entity QMS) archives with separate top_k values.

        Args:
            query: Search query
            db1_top_k: Number of results from DB1 (regulatory guidance)
            db2_top_k: Number of results from DB2 (entity QMS examples)

        Returns:
            {"db1_results": [...], "db2_results": [...]}
        """
        return {
            "db1_results": self.search_archive("db1_regulatory", query, db1_top_k),
            "db2_results": self.search_archive("db2_entity_qms", query, db2_top_k),
        }

    # ─── Helpers ────────────────────────────────────────────────

    @staticmethod
    def _chunk_text(text: str, chunk_size: int = 1000, overlap: int = 200) -> List[str]:
        """Split text into overlapping chunks."""
        if len(text) <= chunk_size:
            return [text]

        chunks = []
        start = 0
        while start < len(text):
            end = start + chunk_size
            chunk = text[start:end]
            if chunk.strip():
                chunks.append(chunk.strip())
            start += chunk_size - overlap

        return chunks

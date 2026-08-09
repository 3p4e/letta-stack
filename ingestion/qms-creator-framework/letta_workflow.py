"""
Letta SOP Workflow Orchestrator

Executes the 10-section SOP generation pipeline by sending messages
to Letta agents sequentially, collecting outputs, and generating DOCX.

Enhanced with KB metadata awareness for intelligent retrieval and gap detection.
"""

import logging
import json
import os
import re
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional, List, Callable

from CONTENT_CREATOR_FRAMEWORK.letta_service import LettaService
from CONTENT_CREATOR_FRAMEWORK.agent_definitions import (
    AGENT_CONFIGS,
    SECTION_ORDER,
    RAG_QUERY_TEMPLATES,
    USER_INPUT_MAPPING,
)

logger = logging.getLogger(__name__)

# Hybrid strategy: the per-section authoring/assembler agents are this app's own
# (created via ensure_agents), but the research and RAG-grounding steps reuse
# shared specialists already living on the Letta server. Names are overridable
# via env so a different server layout can be pointed at without code changes.
SPECIALIST_COMPLIANCE_AGENT = os.getenv("LETTA_COMPLIANCE_AGENT", "eu_gmp_compliance_expert")
SPECIALIST_RAG_AGENT = os.getenv("LETTA_RAG_AGENT", "gmp_rag_agent")

# Load KB metadata configuration
CONFIG_DIR = Path(__file__).parent / "config"


def _load_kb_metadata() -> Dict[str, Any]:
    """Load KB metadata configuration."""
    kb_config_path = CONFIG_DIR / "kb_metadata_config.json"
    if kb_config_path.exists():
        try:
            with open(kb_config_path, "r") as f:
                return json.load(f)
        except Exception as e:
            logger.warning(f"Failed to load KB metadata config: {e}")
    return {}


def _load_classification_rules() -> Dict[str, Any]:
    """Load category classification rules."""
    rules_path = CONFIG_DIR / "category_classification_rules.json"
    if rules_path.exists():
        try:
            with open(rules_path, "r") as f:
                return json.load(f)
        except Exception as e:
            logger.warning(f"Failed to load classification rules: {e}")
    return {}


# Pre-load configurations
KB_METADATA = _load_kb_metadata()
CLASSIFICATION_RULES = _load_classification_rules()

# RAG database weighting per section (prioritize which DB for each agent)
RAG_DB_WEIGHTS = {
    "regulatory": {"db1": 5, "db2": 2},  # Official guidance priority
    "procedure": {"db1": 2, "db2": 5},  # Entity examples priority
    "definitions": {"db1": 4, "db2": 3},  # Regulatory terms priority
    "documentation": {"db1": 4, "db2": 3},  # Official guidance priority
    "training": {"db1": 3, "db2": 4},  # Examples priority
    # Default: balanced 3:3 for other sections
}


def _detect_gap_topic(query: str, sop_name: str) -> Optional[Dict[str, Any]]:
    """
    Detect if query relates to a DB2 gap topic that lacks operational examples.

    Returns:
        Dict with gap info (topic, skill_fallback) if gap detected, None otherwise.
    """
    gaps = KB_METADATA.get("databases", {}).get("db2_entity_qms", {}).get("gaps", [])
    gap_keywords = KB_METADATA.get("gap_detection", {}).get("keywords", {})

    # Create mapping from gap topic key to gap info
    # e.g., "product_recall" -> "Product Recall" gap entry
    topic_key_map = {
        "product_recall": "Product Recall",
        "complaint_management": "Complaint Management",
        "deviation_capa": "Deviation/CAPA",
        "computerized_systems": "Computerized Systems Validation",
        "change_control": "Change Control",
        "self_inspection": "Self-Inspection/Audit",
    }

    # Combine query and SOP name for matching
    search_text = f"{query} {sop_name}".lower()

    # Check each keyword group
    for keyword_key, keywords in gap_keywords.items():
        keywords_lower = [kw.lower() for kw in keywords]

        # Check if any keyword matches
        if any(kw in search_text for kw in keywords_lower):
            # Find corresponding gap entry
            topic_name = topic_key_map.get(keyword_key)
            if topic_name:
                for gap in gaps:
                    if gap.get("topic") == topic_name:
                        return {
                            "topic": gap.get("topic"),
                            "skill_fallback": gap.get("skill_fallback"),
                            "description": gap.get("description"),
                            "severity": gap.get("status", "medium")
                        }

    # Also check direct topic name match in query
    for gap in gaps:
        topic = gap.get("topic", "").lower()
        if topic in search_text:
            return {
                "topic": gap.get("topic"),
                "skill_fallback": gap.get("skill_fallback"),
                "description": gap.get("description"),
                "severity": gap.get("status", "medium")
            }

    return None


def _enrich_passage_metadata(text: str, tags: List[str]) -> Dict[str, Any]:
    """
    Compute metadata for a passage at query time.

    Uses classification rules from config to determine category,
    quality score, and regulatory alignment.
    """
    rules = CLASSIFICATION_RULES.get("classification_rules", {})
    filename_patterns = rules.get("filename_patterns", {})
    content_keywords = rules.get("content_keywords", {})

    # Extract filename from tags
    filename = ""
    for tag in tags:
        if tag.startswith("file:"):
            filename = tag[5:].lower()
            break

    # Classify category
    category = "General"
    if filename:
        for cat, config in filename_patterns.items():
            patterns = config.get("patterns", [])
            if any(pattern in filename for pattern in patterns):
                category = cat
                break

    # Fallback: content-based classification
    if category == "General":
        text_lower = text.lower()[:2000]
        category_scores = {}
        for cat, config in content_keywords.items():
            keywords = config.get("keywords", [])
            weight = config.get("weight", 0.8)
            score = sum(weight for kw in keywords if kw in text_lower)
            if score > 0:
                category_scores[cat] = score
        if category_scores:
            category = max(category_scores, key=category_scores.get)

    # Calculate quality score (simplified)
    quality = 5.0
    scoring = CLASSIFICATION_RULES.get("quality_scoring", {})
    structure = scoring.get("structure_indicators", {})

    if re.search(r"^#{1,3}\s+\w+", text, re.MULTILINE):
        quality += structure.get("has_headers", {}).get("points", 1.5)
    if re.search(r"^\d+\.\s+\w+", text, re.MULTILINE):
        quality += structure.get("has_numbering", {}).get("points", 1.0)
    if "|" in text and "---" in text:
        quality += structure.get("has_tables", {}).get("points", 1.0)

    quality = min(quality, 10.0)

    # Determine source authority
    source_authority = "operational_example"
    if any("db1" in tag or "regulatory" in tag for tag in tags):
        source_authority = "official_regulatory"

    return {
        "category": category,
        "quality": round(quality, 1),
        "source_authority": source_authority
    }


class LettaSOPWorkflow:
    """
    Orchestrates SOP generation via Letta agents.

    Flow:
    1. Update agent context memory with SOP metadata
    2. For each section: search archives → build prompt → send to agent
    3. Run assembler for QA review
    4. Generate DOCX
    5. Return results
    """

    def __init__(self, letta_service: LettaService, project_root: str = None):
        self.letta = letta_service
        self.project_root = Path(project_root) if project_root else Path.cwd()

    async def execute(
        self,
        sop_name: str,
        sop_code: str,
        department: str = "",
        facility_type: str = "Cannabis EU GMP",
        document_type: str = "SOP",
        user_inputs: Optional[Dict[str, str]] = None,
        user_selections: Optional[Dict[str, Any]] = None,
        on_progress: Optional[Callable[[str, str, Optional[str]], None]] = None,
    ) -> Dict[str, Any]:
        """
        Execute the full SOP generation workflow.

        Args:
            sop_name: Title of the SOP (e.g., "Document Control")
            sop_code: Document code (e.g., "QA_00.02")
            department: Department name
            facility_type: Facility type description
            document_type: Document type (SOP, WI, Policy, etc.)
            user_inputs: Optional per-section user input text
            user_selections: Optional questionnaire selections

        Returns:
            Dict with sections, quality_report, docx_path, metadata.
        """
        user_inputs = user_inputs or {}
        user_selections = user_selections or {}

        start_time = datetime.now()
        logger.info(f"Starting SOP workflow: {sop_code} - {sop_name}")

        # Build SOP context string for agent memory
        sop_context = self._build_context_string(
            sop_name, sop_code, department, facility_type, document_type, user_selections
        )

        # Reset all agents and update context
        for role in SECTION_ORDER:
            self.letta.reset_agent_messages(role)
            self.letta.update_agent_context(role, sop_context)
        self.letta.reset_agent_messages("assembler")
        self.letta.update_agent_context("assembler", sop_context)
        self.letta.reset_agent_messages("researcher")
        self.letta.update_agent_context("researcher", sop_context)

        # Phase 0: Research (New)
        research_brief = ""
        logger.info("Starting Research Phase...")
        if on_progress:
            on_progress("agent_start", "researcher", "Finding latest regulatory requirements...")
        
        try:
            # Hybrid: prefer the shared compliance specialist (grounded in 500+
            # regulatory passages) for the research brief; fall back to this
            # app's own researcher agent if that specialist isn't on the server.
            compliance_query = (
                f"Provide an authoritative EU GMP regulatory brief for authoring the SOP '{sop_name}'. "
                "Cite the relevant EudraLex Vol.4 chapters/annexes, EMA/ICH guidance, and any "
                "cannabis-specific pharmaceutical requirements for this document. "
                "Be concise and technical, with citations."
            )
            research_brief = self.letta.send_to_external(SPECIALIST_COMPLIANCE_AGENT, compliance_query)

            if not research_brief:
                logger.info(
                    f"Specialist '{SPECIALIST_COMPLIANCE_AGENT}' unavailable; "
                    "falling back to internal researcher agent"
                )
                research_brief = self.letta.send_message("researcher", (
                    f"Perform exhaustive research on: {sop_name}. "
                    "Use the perplexity_search tool to find the LATEST EU GMP requirements (2023-2025), "
                    "EMA guidelines, and cannabis-specific pharmaceutical benchmarks. "
                    "Provide a technical summary with citations."
                ))
            logger.info(f"Research phase complete: {len(research_brief)} chars")
            if on_progress:
                on_progress("agent_done", "researcher", "Research complete. Brief generated.")
        except Exception as e:
            logger.error(f"Research phase failed: {e}")
            research_brief = "[Research phase unavailable - falling back to internal knowledge]"
            if on_progress:
                on_progress("agent_error", "researcher", str(e))

        # Update ALL agents with the research brief and facility persona (Persistent Memory)
        facility_info = f"Purely Plant GmbH - Cannabis EU GMP Facility. Standard Coding: {sop_code.split(' - ')[0]} - XX.YY.00"
        for role in SECTION_ORDER + ["assembler"]:
            self.letta.update_agent_context(role, research_brief, block_label="research")
            self.letta.update_agent_context(role, facility_info, block_label="facility")

        # Generate each section
        sections = {}
        errors = []

        for role in SECTION_ORDER:
            logger.info(f"Generating section: {role}")
            if on_progress:
                on_progress("agent_start", role, None)
            try:
                # Search archives for relevant context (with user input keywords)
                rag_context = self._search_for_section(role, sop_name, user_inputs)

                # Build prompt (now injects relevant wizard answers per USER_INPUT_MAPPING)
                prompt = self._build_section_prompt(
                    role, sop_name, sop_code, department,
                    user_inputs,  # Pass full user_inputs dict
                    rag_context,
                    sections,  # Previous sections for context
                    research_brief=research_brief,  # Pass newly generated research
                )

                # Send to agent
                content = self.letta.send_message(role, prompt)

                if content and content.strip():
                    sections[role] = content.strip()
                    logger.info(f"Section '{role}' generated: {len(content)} chars")
                    if on_progress:
                        on_progress("agent_done", role, content.strip())
                else:
                    sections[role] = f"[Section '{role}' generation returned empty result]"
                    errors.append({"section": role, "error": "Empty response"})
                    if on_progress:
                        on_progress("agent_error", role, "Empty response")

            except Exception as e:
                logger.error(f"Error generating section '{role}': {e}")
                sections[role] = f"[Error generating '{role}': {str(e)}]"
                errors.append({"section": role, "error": str(e)})
                if on_progress:
                    on_progress("agent_error", role, str(e))

        # Run assembler for QA
        quality_report = ""
        try:
            logger.info("Running assembler QA review")
            assembly_prompt = self._build_assembly_prompt(sections, sop_name, sop_code)
            quality_report = self.letta.send_message("assembler", assembly_prompt)
        except Exception as e:
            logger.error(f"Assembler error: {e}")
            quality_report = f"Assembler review failed: {e}"

        # Generate DOCX (main SOP)
        docx_path = ""
        try:
            docx_path = self._generate_docx(sections, sop_name, sop_code, department)
            logger.info(f"Main SOP DOCX generated: {docx_path}")
        except Exception as e:
            logger.error(f"DOCX generation error: {e}")
            errors.append({"section": "docx_generation", "error": str(e)})

        # Phase 2: Generate annexes separately (if any requested)
        annexes = user_selections.get("annexes", [])
        annex_sections = {}
        if annexes and docx_path:
            logger.info(f"Generating {len(annexes)} annexes...")
            annex_sections = await self.generate_annexes(
                annexes=annexes,
                sections=sections,
                sop_name=sop_name,
                sop_code=sop_code,
                on_progress=on_progress,
            )
            # Append annexes to existing DOCX
            if annex_sections:
                try:
                    self._append_annexes_to_docx(docx_path, annex_sections)
                    logger.info(f"Annexes appended to DOCX: {len(annex_sections)}")
                except Exception as e:
                    logger.error(f"Error appending annexes: {e}")
                    errors.append({"section": "annex_append", "error": str(e)})

        elapsed = (datetime.now() - start_time).total_seconds()

        result = {
            "sop_code": sop_code,
            "sop_name": sop_name,
            "sections": sections,
            "annexes": annex_sections,
            "quality_report": quality_report,
            "docx_path": docx_path,
            "errors": errors,
            "metadata": {
                "department": department,
                "facility_type": facility_type,
                "document_type": document_type,
                "generated_at": datetime.now().isoformat(),
                "elapsed_seconds": round(elapsed, 1),
                "section_count": len([s for s in sections.values() if not s.startswith("[")]),
                "annex_count": len(annex_sections),
            },
        }

        logger.info(
            f"Workflow complete: {sop_code} in {elapsed:.1f}s, "
            f"{len(sections)} sections, {len(annex_sections)} annexes, {len(errors)} errors"
        )
        return result

    async def generate_annexes(
        self,
        annexes: List[str],
        sections: Dict[str, str],
        sop_name: str,
        sop_code: str,
        on_progress: Optional[Callable[[str, str, Optional[str]], None]] = None,
    ) -> Dict[str, str]:
        """
        Generate annexes separately after main SOP completion.

        Args:
            annexes: List of annex titles from wizard (e.g., ["Transport Form", "Checklist"])
            sections: Generated main sections (for procedure summary context)
            sop_name: SOP name
            sop_code: SOP code
            on_progress: Progress callback

        Returns:
            Dict mapping annex labels (Annex A, B, C...) to content
        """
        annex_sections = {}
        procedure_summary = sections.get("procedure", "")[:1000]  # First 1000 chars of procedure

        for idx, annex_title in enumerate(annexes):
            annex_label = f"Annex {chr(65 + idx)}"  # A, B, C...
            logger.info(f"Generating {annex_label}: {annex_title}")

            if on_progress:
                on_progress("annex_start", annex_label, None)

            try:
                prompt = self._build_annex_prompt(
                    annex_title=annex_title,
                    annex_label=annex_label,
                    sop_name=sop_name,
                    sop_code=sop_code,
                    procedure_summary=procedure_summary,
                )

                content = self.letta.send_message("annex", prompt)

                if content and content.strip():
                    annex_sections[annex_label] = content.strip()
                    logger.info(f"{annex_label} generated: {len(content)} chars")
                    if on_progress:
                        on_progress("annex_done", annex_label, content.strip())
                else:
                    annex_sections[annex_label] = f"[{annex_label} generation returned empty result]"
                    if on_progress:
                        on_progress("annex_error", annex_label, "Empty response")

            except Exception as e:
                logger.error(f"Error generating {annex_label}: {e}")
                annex_sections[annex_label] = f"[Error generating {annex_label}: {str(e)}]"
                if on_progress:
                    on_progress("annex_error", annex_label, str(e))

        return annex_sections

    def _build_annex_prompt(
        self,
        annex_title: str,
        annex_label: str,
        sop_name: str,
        sop_code: str,
        procedure_summary: str,
    ) -> str:
        """Build prompt for annex generation."""
        return f"""Generate {annex_label}: {annex_title}

For SOP: {sop_code} - {sop_name}

Context from main procedure:
{procedure_summary}

Requirements:
- Create a standalone, printable document for: {annex_title}
- Include all necessary fields for GMP traceability
- Use markdown table format for forms
- Include signature/date/approval blocks
- Add instructions for completion if it's a form
- Ensure compliance with EU GMP documentation requirements

Output the complete {annex_label} content now."""

    def _append_annexes_to_docx(self, docx_path: str, annex_sections: Dict[str, str]):
        """Append generated annexes to existing DOCX file."""
        try:
            from CONTENT_CREATOR_FRAMEWORK.docx_engine.workflow_to_docx import append_annexes

            append_annexes(docx_path, annex_sections)
            logger.info(f"Appended {len(annex_sections)} annexes to {docx_path}")

        except ImportError:
            logger.warning("Annex append function not available in docx engine")
        except Exception as e:
            logger.error(f"Failed to append annexes: {e}")
            raise

    def _build_context_string(
        self, sop_name, sop_code, department, facility_type, document_type, user_selections
    ) -> str:
        """Build context string for agent human memory block."""
        lines = [
            f"Current SOP: {sop_code} - {sop_name}",
            f"Department: {department}",
            f"Facility Type: {facility_type}",
            f"Document Type: {document_type}",
        ]
        if user_selections:
            lines.append(f"User Selections: {json.dumps(user_selections, indent=2)[:1000]}")
        return "\n".join(lines)

    def _search_for_section(self, role: str, sop_name: str, user_inputs: Dict[str, str] = None) -> str:
        """
        Search both archives for content relevant to this section.

        Enhanced with:
        - KB metadata-aware gap detection
        - Query-time passage enrichment
        - Skill fallback recommendations for gap topics
        """
        template = RAG_QUERY_TEMPLATES.get(role, "EU GMP {sop_name}")
        query = template.format(sop_name=sop_name)

        # Append relevant user input keywords to query for better retrieval
        if user_inputs:
            user_keywords = []
            for key, agents in USER_INPUT_MAPPING.items():
                if role in agents and key in user_inputs and user_inputs[key]:
                    # Extract first 50 chars of user input as keywords
                    user_keywords.append(user_inputs[key][:50])
            if user_keywords:
                query += " " + " ".join(user_keywords)

        # Detect gap topics (areas with limited DB2 coverage)
        gap_info = _detect_gap_topic(query, sop_name)

        # Adjust DB weights based on gap detection
        weights = RAG_DB_WEIGHTS.get(role, {"db1": 3, "db2": 3})
        db1_top_k = weights["db1"]
        db2_top_k = weights["db2"]

        # If gap topic detected, increase DB1 weight for official guidance
        if gap_info:
            logger.info(f"Gap topic detected for {role}: {gap_info['topic']}")
            db1_top_k = max(db1_top_k + 2, 5)  # Boost DB1 for official guidance
            db2_top_k = max(db2_top_k - 1, 1)  # Reduce DB2 (limited content)

        results = self.letta.dual_db_search(query, db1_top_k=db1_top_k, db2_top_k=db2_top_k)

        parts = []

        # Hybrid RAG fallback: if this app's own archives return nothing (e.g. not
        # yet ingested), consult the shared gmp_rag_agent specialist so sections
        # still get regulatory grounding rather than generating blind.
        if not results.get("db1_results") and not results.get("db2_results"):
            rag_answer = self.letta.send_to_external(
                SPECIALIST_RAG_AGENT,
                f"Retrieve and summarize regulatory guidance relevant to: {query}",
            )
            if rag_answer:
                parts.append("=== GMP RAG SPECIALIST (external retrieval) ===")
                parts.append(rag_answer[:1500] + "\n")

        # Add gap warning if applicable
        if gap_info:
            parts.append(f"⚠️ **KNOWLEDGE GAP NOTICE**: {gap_info['topic']}")
            parts.append(f"DB2 has limited operational examples for this topic.")
            if gap_info.get("skill_fallback"):
                parts.append(f"Recommended skill for templates: {gap_info['skill_fallback']}")
            parts.append("Rely primarily on DB1 (official regulatory guidance) below.\n")

        # Format DB1 results with enriched metadata
        if results["db1_results"]:
            parts.append("=== DB1: OFFICIAL REGULATORY GUIDANCE (Authoritative) ===")
            for r in results["db1_results"]:
                text = r["text"][:1000]
                tags = r.get("tags", [])
                metadata = _enrich_passage_metadata(text, tags)

                # Format with metadata annotation
                parts.append(
                    f"[Category: {metadata['category']} | "
                    f"Quality: {metadata['quality']}/10 | "
                    f"Source: {metadata['source_authority']}]"
                )
                parts.append(f"{text}\n")

        # Format DB2 results with enriched metadata
        if results["db2_results"]:
            header = "=== DB2: ENTITY QMS EXAMPLES"
            if gap_info:
                header += " (LIMITED FOR THIS TOPIC)"
            header += " ==="
            parts.append(header)

            for r in results["db2_results"]:
                text = r["text"][:1000]
                tags = r.get("tags", [])
                metadata = _enrich_passage_metadata(text, tags)

                # Format with metadata annotation
                parts.append(
                    f"[Category: {metadata['category']} | "
                    f"Quality: {metadata['quality']}/10 | "
                    f"Source: {metadata['source_authority']}]"
                )
                parts.append(f"{text}\n")

        # Add skill guidance for gaps at the end
        if gap_info and gap_info.get("skill_fallback"):
            parts.append(f"\n📋 For structured templates on {gap_info['topic']}, ")
            parts.append(f"use the {gap_info['skill_fallback']} skill which provides ")
            parts.append("complete EU GMP compliant document structures.")

        return "\n".join(parts) if parts else ""

    def _build_section_prompt(
        self, role, sop_name, sop_code, department, user_inputs: Dict[str, str], rag_context, prev_sections, research_brief=""
    ) -> str:
        """
        Build a concise prompt for the chapter agent.
        Harnesses Letta's CORE MEMORY and autonomous tool-use.
        """
        parts = [
            f"### MISSION: Generate {role.upper()} section for {sop_name}",
            f"**Context**: {sop_code} | {department}",
            "",
            "**AGENTIC INSTRUCTIONS**:",
            "1. **SEARCH**: Use `archival_memory_search` to fetch details from attached archives (DB1/DB2).",
            "2. **RESEARCH**: Check your `research` memory block for the latest AI-researched trends.",
            "3. **FACILITY**: Check your `facility` memory block for Purely Plant GmbH standards.",
            "4. **OUTPUT**: Professional markdown, no placeholders, pharma-clinical tone.",
        ]

        # Inject relevant wizard answers for this agent (using USER_INPUT_MAPPING)
        relevant_inputs = []
        for key, agents in USER_INPUT_MAPPING.items():
            if role in agents and key in user_inputs and user_inputs.get(key):
                value = user_inputs[key]
                label = key.replace("_", " ").title()
                relevant_inputs.append(f"**{label}:** {value}")

        if relevant_inputs:
            parts.append(f"\n**USER INPUTS (Human Memory):**\n" + "\n".join(relevant_inputs))

        if rag_context:
            parts.append(f"\n**PRE-SEARCH SUMMARY (Initial Context):**\n{rag_context[:1000]}")

        # Provide previous sections summary for coherence
        if prev_sections:
            summary = [f"- {s}: {c[:150]}..." for s, c in prev_sections.items()]
            parts.append(f"\n**COHERENCE CONTEXT (Previous Sections):**\n" + "\n".join(summary))

        parts.append("\nProceed with generation. Lead with tools if more data is needed.")

        return "\n\n".join(parts)

    def _build_assembly_prompt(self, sections, sop_name, sop_code) -> str:
        """
        Build prompt for the assembler agent using metrics instead of full content.

        This prevents timeout by sending structured metrics instead of 87K+ chars.
        """
        import re

        parts = [
            f"Review and assess the complete SOP: {sop_code} - {sop_name}",
            f"Total sections: {len(sections)}",
            "",
            "SECTION METRICS:",
            "",
        ]

        for role, content in sections.items():
            # Calculate metrics
            word_count = len(content.split())
            has_headings = bool(re.search(r'^##\s+', content, re.MULTILINE))
            has_table = "|" in content and "---" in content
            has_numbered_list = bool(re.search(r'^\d+\.', content, re.MULTILINE))
            mentions_eu_gmp = "EU GMP" in content or "EudraLex" in content
            mentions_cannabis = "cannabis" in content.lower()
            first_100 = content[:100].replace("\n", " ")
            last_100 = content[-100:].replace("\n", " ")

            parts.append(f"**{role.upper()}:**")
            parts.append(f"  - Word count: {word_count}")
            parts.append(f"  - Has headings (##): {has_headings}")
            parts.append(f"  - Has tables: {has_table}")
            parts.append(f"  - Has numbered lists: {has_numbered_list}")
            parts.append(f"  - Mentions EU GMP: {mentions_eu_gmp}")
            parts.append(f"  - Cannabis-specific: {mentions_cannabis}")
            parts.append(f"  - First 100 chars: \"{first_100}...\"")
            parts.append(f"  - Last 100 chars: \"...{last_100}\"")
            parts.append("")

        parts.append(
            "Based on these metrics, provide a quality assessment in JSON format:\n"
            "{\n"
            '  "score": 0-100,\n'
            '  "section_scores": {"purpose": 85, "scope": 90, ...},\n'
            '  "issues": ["Issue 1", "Issue 2", ...],\n'
            '  "recommendations": ["Recommendation 1", ...]\n'
            "}\n\n"
            "Assess:\n"
            "1. Overall quality score (0-100)\n"
            "2. Per-section scores (0-100)\n"
            "3. Issues: placeholder text, missing headings, too short/long, missing tables\n"
            "4. Recommendations for improvement\n"
            "5. Regulatory compliance (does it mention EU GMP/cannabis where expected?)"
        )

        return "\n".join(parts)

    def _generate_docx(self, sections, sop_name, sop_code, department) -> str:
        """Generate DOCX from sections using the docx engine."""
        try:
            from CONTENT_CREATOR_FRAMEWORK.docx_engine.workflow_to_docx import generate_docx_from_sections

            output_dir = self.project_root / "output" / "generated_sops"
            output_dir.mkdir(parents=True, exist_ok=True)

            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"{sop_code}_{timestamp}.docx"
            output_path = output_dir / filename

            generate_docx_from_sections(
                sections=sections,
                sop_name=sop_name,
                sop_code=sop_code,
                department=department,
                output_path=str(output_path),
            )

            logger.info(f"DOCX generated: {output_path}")
            return str(output_path)

        except ImportError:
            # Engine genuinely unavailable — a soft skip, not a failure.
            logger.warning("DOCX engine not available, skipping DOCX generation")
            return ""
        except Exception as e:
            # A real generation failure must not be silently swallowed and
            # reported as success; re-raise so execute() records it in errors.
            logger.error(f"DOCX generation failed: {e}")
            raise

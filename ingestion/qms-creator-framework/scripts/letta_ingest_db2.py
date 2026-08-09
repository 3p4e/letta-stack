"""
DB2 Ingestion into Letta — Previous Entity QMS Documents

Ingests documents from 2ndDataKnowledge into the Letta db2_entity_qms archive.
Files are tagged with their entity name (top-level subfolder name).

Usage:
    cd /home/azzu/PROJ/Cannabis\ EU\ GMP\ QMS\ Creator
    source .venv/bin/activate
    python -m CONTENT_CREATOR_FRAMEWORK.scripts.letta_ingest_db2

Prerequisites:
    - Letta server running (docker compose up -d in letta-main/)
    - OPENAI_API_KEY set (for embeddings)
"""

import sys
import logging
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT))

from dotenv import load_dotenv
load_dotenv(PROJECT_ROOT / ".env")

from CONTENT_CREATOR_FRAMEWORK.letta_service import LettaService

DB2_FOLDER = PROJECT_ROOT / "Knowledgebase" / "2ndDataKnowledge"

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("letta_ingest_db2")


def main():
    if not DB2_FOLDER.exists():
        logger.error(f"DB2 folder not found: {DB2_FOLDER}")
        sys.exit(1)

    # List entity subfolders
    entities = [d for d in DB2_FOLDER.iterdir() if d.is_dir() and not d.name.startswith(".")]
    if not entities:
        logger.warning(f"No entity subfolders found in {DB2_FOLDER}")
        sys.exit(1)

    logger.info(f"Found {len(entities)} entity folders: {[e.name for e in entities]}")

    # Connect to Letta
    service = LettaService()
    service.ensure_archives()

    # Tag function: entity name from top-level subfolder
    def tag_fn(file_path: Path):
        try:
            rel = file_path.relative_to(DB2_FOLDER)
            entity = rel.parts[0] if rel.parts else "Unknown"
        except ValueError:
            entity = "Unknown"
        return [f"entity:{entity}", "database:db2"]

    # Ingest
    stats = service.ingest_folder("db2_entity_qms", str(DB2_FOLDER), tag_fn=tag_fn)

    print("\n" + "=" * 60)
    print("DB2 LETTA INGESTION COMPLETE")
    print("=" * 60)
    for k, v in stats.items():
        print(f"  {k}: {v}")


if __name__ == "__main__":
    main()

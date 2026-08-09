"""
DB1 Ingestion into Letta — Official Regulatory Guides

Ingests documents from 1stDataKnowledge into the Letta db1_regulatory archive.
Files are tagged with their regulatory body (parent folder name).

Usage:
    cd /home/azzu/PROJ/Cannabis\ EU\ GMP\ QMS\ Creator
    source .venv/bin/activate
    python -m CONTENT_CREATOR_FRAMEWORK.scripts.letta_ingest_db1

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

DB1_FOLDER = PROJECT_ROOT / "Knowledgebase" / "1stDataKnowledge"

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("letta_ingest_db1")


def main():
    if not DB1_FOLDER.exists():
        logger.error(f"DB1 folder not found: {DB1_FOLDER}")
        sys.exit(1)

    logger.info(f"DB1 folder: {DB1_FOLDER}")

    # Connect to Letta
    service = LettaService()
    service.ensure_archives()

    # Tag function: use parent folder as regulatory body
    def tag_fn(file_path: Path):
        try:
            rel = file_path.parent.relative_to(DB1_FOLDER)
            body = rel.parts[0] if rel.parts else "General"
        except ValueError:
            body = "General"
        return [f"regulatory_body:{body}", "database:db1"]

    # Ingest
    stats = service.ingest_folder("db1_regulatory", str(DB1_FOLDER), tag_fn=tag_fn)

    print("\n" + "=" * 60)
    print("DB1 LETTA INGESTION COMPLETE")
    print("=" * 60)
    for k, v in stats.items():
        print(f"  {k}: {v}")


if __name__ == "__main__":
    main()

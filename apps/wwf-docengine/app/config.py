# docengine.app.config — environment-driven settings (no pydantic dependency:
# this service stays lean; every knob is a 12-factor env var).
import os
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]          # docengine/
ENGINE_SCRIPTS = ROOT / "engine" / "scripts"
ENGINE_ASSETS = ROOT / "engine" / "assets"


class Settings:
    # Auth: the WWF backend proxy injects this header server-side (same
    # pattern as qms-api). Empty key = service refuses to start in prod mode.
    api_key: str = os.environ.get("DOCENGINE_API_KEY", "")

    # Letta (direct REST — the Rust MCP bridge has a known decode bug).
    letta_base: str = os.environ.get("LETTA_BASE_URL", "").rstrip("/")
    letta_key: str = os.environ.get("LETTA_API_KEY", "")
    # A stateful-agent generation can take minutes; the read timeout must cover
    # ONE agent turn (the pipeline makes ~11 sequential calls, each polled as a
    # background job). Connect stays short so an unreachable server fails fast.
    letta_read_timeout: float = float(os.environ.get("LETTA_READ_TIMEOUT", "300"))
    letta_connect_timeout: float = float(os.environ.get("LETTA_CONNECT_TIMEOUT", "15"))
    # Retries of one Letta call (letta.py), with exponential back-off from this base in seconds, and repeats
    # of one pipeline step on a fresh clone when its message failed transiently (pipeline.ask).
    letta_retries: int = int(os.environ.get("DOCENGINE_LETTA_RETRIES", "2"))
    letta_retry_base: float = float(os.environ.get("DOCENGINE_LETTA_RETRY_BASE", "2"))
    ask_retries: int = int(os.environ.get("DOCENGINE_ASK_RETRIES", "1"))
    # Workflow repair loops (pipeline.py). A section whose Markdown breaks the engine grammar goes back
    # to its author this many times; a §6A FIX verdict sends the named sections back this many rounds
    # before the job goes to review (or fails, see fix_to_review). 0 turns a loop off.
    lint_repair_rounds: int = int(os.environ.get("DOCENGINE_LINT_REPAIR_ROUNDS", "1"))
    qa_repair_rounds: int = int(os.environ.get("DOCENGINE_QA_REPAIR_ROUNDS", "2"))
    # A §6A FIX that survives every repair round: 1 (default) builds and verifies the .docx and parks the
    # job as awaiting_review for a person (EU GMP Ch. 4 §4.3 — a person approves every document anyway);
    # nothing is registered until POST /workflows/{id}/review approves it. 0 fails the job instead.
    fix_to_review: bool = os.environ.get("DOCENGINE_FIX_TO_REVIEW", "1") not in ("0", "false", "no")
    # Per-section regulatory checks run concurrently, at most this many at once.
    reg_concurrency: int = max(1, int(os.environ.get("DOCENGINE_REG_CONCURRENCY", "4")))

    # Postgres for workflow state (fixes the per-worker in-memory bug class).
    # e.g. postgresql://docengine:...@wwf-tasks-db:5432/wwf_tasks
    database_url: str = os.environ.get("DOCENGINE_DATABASE_URL", "")

    # Where produced .docx artifacts live (volume-mounted in the stack).
    out_dir: Path = Path(os.environ.get("DOCENGINE_OUT_DIR", "/data/docengine-out"))

    # Gotenberg for DOCX→PDF (already in the kvm4 letta stack).
    gotenberg_url: str = os.environ.get("GOTENBERG_URL", "").rstrip("/")
    # Basic auth, when Gotenberg is reached through its public route (pp_render reads the same names).
    gotenberg_user: str = os.environ.get("GOTENBERG_USERNAME", "")
    gotenberg_password: str = os.environ.get("GOTENBERG_PASSWORD", "")

    # Regulatory sources the checker agents are bound to (names, resolved to
    # ids at fleet-ensure time). PQ1 is deliberately excluded (3072-dim outlier).
    reg_sources: tuple = tuple(
        s.strip()
        for s in os.environ.get(
            "DOCENGINE_REG_SOURCES", "DB1_REGULATORY,DB3_PP_CURRENT_unified"
        ).split(",")
        if s.strip()
    )


    # RAGFlow on KVM4 (in-stack address, e.g. http://ragflow-cpu:9380; the public
    # https://ragflow.srv1231216.hstgr.cloud also works). Tenant API key from RAGFlow
    # (Avatar › API). Unset => the regulatory check falls back to the Letta sources above.
    ragflow_base: str = os.environ.get("RAGFLOW_BASE_URL", "").rstrip("/")
    ragflow_key: str = os.environ.get("RAGFLOW_API_KEY", "")
    # Dataset ids (not secrets). Defaults are the KVM4 instance's DB01_REG and eCOA_INGEST
    # (the complete eCoA re-ingestion, 482 documents, 11.10.2026; eCOA_DB is retired — Head of QC, 22.10.2026).
    ragflow_reg_datasets: tuple = tuple(s.strip() for s in os.environ.get(
        "RAGFLOW_REG_DATASETS", "a33b0812a3d411f1858cf58865604f65").split(",") if s.strip())
    ragflow_ecoa_datasets: tuple = tuple(s.strip() for s in os.environ.get(
        "RAGFLOW_ECOA_DATASETS", "71b9c168b4a311f1a370a99b32e82467").split(",") if s.strip())
    # Approved, in-use house documents the authors consult (DB3_PP_CURRENT, 18.10.2026). The first id is also where
    # PUT /reference indexes an approved document's text.
    ragflow_example_datasets: tuple = tuple(s.strip() for s in os.environ.get(
        "RAGFLOW_EXAMPLE_DATASETS", "880312c6cb1411f18ed047989fb7f345").split(",") if s.strip())
    # The official potency specifications: grades and ranges per strain (Head of QC, 19.10.2026: "the specification
    # grades and ranges actualy are officialy as in https://specs.srv1231216.hstgr.cloud"). Read-only. Empty = off.
    potency_specs_url: str = os.environ.get("POTENCY_SPECS_URL", "https://specs.srv1231216.hstgr.cloud").rstrip("/")
    ragflow_top_n: int = int(os.environ.get("RAGFLOW_TOP_N", "6"))


settings = Settings()

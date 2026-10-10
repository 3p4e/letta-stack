import os
import sys
from pathlib import Path

# backend/ is deliberately NOT a package: app.py does a flat `import wizard` and
# the Dockerfile runs `uvicorn app:app` with backend/ as the working directory.
# The tests reproduce that import root rather than restructuring the app around
# them — mirrors apps/wwf-docengine/tests/conftest.py, which does the same for
# its own layout.
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))

# app.py resolves the engine at import time. In a checkout the relative guess
# (apps/pp-document-suite) does not exist, so point it at the real tree; without
# this the module still imports, but nothing else in the repo would tell a reader
# which engine these tests exercise.
os.environ.setdefault("PP_SUITE_DIR", str(ROOT.parents[1] / "pp-document-suite"))

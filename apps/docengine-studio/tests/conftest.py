import os
import sys
import tempfile
from pathlib import Path

TMP = Path(tempfile.mkdtemp(prefix="studio-test-"))
os.environ["STUDIO_DATA_DIR"] = str(TMP)
os.environ["STUDIO_DB_PATH"] = str(TMP / "studio.db")
os.environ["STUDIO_API_KEY"] = "test-studio-key"
os.environ["STUDIO_TRUST_HEADERS"] = "1"
os.environ["DOCENGINE_ENDPOINT"] = "http://docengine.invalid:8000"
os.environ["LETTA_ENDPOINT"] = ""
os.environ["RAGFLOW_ENDPOINT"] = ""
os.environ.pop("RAGFLOW_API_KEY", None)

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import pytest
from fastapi.testclient import TestClient


@pytest.fixture(scope="session")
def client():
    from app.main import app
    with TestClient(app) as c:
        yield c


@pytest.fixture()
def viewer():
    return {"X-Auth-Request-User": "u-viewer", "X-Auth-Request-Role": "viewer"}


@pytest.fixture()
def author():
    return {"X-Auth-Request-User": "u-author", "X-Auth-Request-Role": "author"}


@pytest.fixture()
def approver():
    return {"X-Auth-Request-User": "u-qa", "X-Auth-Request-Role": "qa_approver"}


@pytest.fixture()
def admin():
    return {"X-Auth-Request-User": "u-admin", "X-Auth-Request-Role": "admin"}

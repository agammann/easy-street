from pathlib import Path
import sys

import pytest
from fastapi.testclient import TestClient

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from backend.main import create_app


@pytest.fixture
def client(tmp_path):
    with TestClient(create_app(data_dir=tmp_path, budget_limit=0.01), base_url="http://127.0.0.1:8000") as client:
        yield client

@pytest.fixture
def api_factory(tmp_path):
    from contextlib import ExitStack
    with ExitStack() as stack:
        def factory(provider, budget=1.0):
            return stack.enter_context(TestClient(
                create_app(data_dir=tmp_path, provider=provider, budget_limit=budget),
                base_url="http://127.0.0.1:8000",
            ))
        yield factory

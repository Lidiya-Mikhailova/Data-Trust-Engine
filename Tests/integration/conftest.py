from __future__ import annotations

import pytest


@pytest.fixture(scope="session")
def docker_compose_files() -> list[str]:
    return ["docker-compose.yml"]

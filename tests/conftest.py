"""pytest 共享夹具：统一指向项目自带的知识库与演示模型。"""

from __future__ import annotations

import tempfile
import uuid
from pathlib import Path

import pytest

from smartqa.config import ROOT, Settings
from smartqa.retriever import load_documents


@pytest.fixture(scope="session")
def knowledge_dir() -> Path:
    return ROOT / "data" / "knowledge"


@pytest.fixture(scope="session")
def demo_settings(knowledge_dir: Path) -> Settings:
    return Settings(provider="demo", knowledge_dir=knowledge_dir, top_k=3, temperature=0.0)


@pytest.fixture(scope="session")
def documents(knowledge_dir: Path):
    return load_documents(knowledge_dir)


@pytest.fixture()
def temp_dir() -> Path:
    """临时目录：优先系统临时目录，受限环境下退回仓库内的隐藏目录。"""
    try:
        path = Path(tempfile.mkdtemp(prefix="smartqa-"))
    except OSError:
        path = ROOT / ".pytest-tmp" / uuid.uuid4().hex
        path.mkdir(parents=True, exist_ok=True)

    yield path

    import shutil

    shutil.rmtree(path, ignore_errors=True)

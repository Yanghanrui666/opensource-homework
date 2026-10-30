"""配置读取测试：环境变量解析与容错。"""

from __future__ import annotations

from pathlib import Path

import pytest

from smartqa.config import Settings


def test_defaults_are_demo_provider(monkeypatch):
    for name in ("PROVIDER", "MODEL", "TOP_K", "TEMPERATURE", "KNOWLEDGE_DIR", "API_KEY"):
        monkeypatch.delenv(f"SMARTQA_{name}", raising=False)
    settings = Settings.from_env()
    assert settings.provider == "demo"
    assert settings.top_k == 4
    assert settings.temperature == pytest.approx(0.2)


def test_env_values_are_parsed(monkeypatch, temp_dir: Path):
    monkeypatch.setenv("SMARTQA_PROVIDER", "openai")
    monkeypatch.setenv("SMARTQA_MODEL", "qwen-plus")
    monkeypatch.setenv("SMARTQA_TOP_K", "6")
    monkeypatch.setenv("SMARTQA_TEMPERATURE", "0.7")
    monkeypatch.setenv("SMARTQA_KNOWLEDGE_DIR", str(temp_dir))

    settings = Settings.from_env()
    assert settings.provider == "openai"
    assert settings.model == "qwen-plus"
    assert settings.top_k == 6
    assert settings.temperature == pytest.approx(0.7)
    assert settings.knowledge_dir == temp_dir


def test_invalid_values_fall_back(monkeypatch):
    monkeypatch.setenv("SMARTQA_PROVIDER", "not-a-provider")
    monkeypatch.setenv("SMARTQA_TOP_K", "abc")
    settings = Settings.from_env()
    assert settings.provider == "demo"
    assert settings.top_k == 4


def test_replace_returns_new_instance():
    original = Settings()
    changed = original.replace(top_k=8)
    assert changed.top_k == 8
    assert original.top_k == 4

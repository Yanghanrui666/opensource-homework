"""问答链的端到端测试（演示模型，不依赖网络与 API Key）。"""

from __future__ import annotations

import pytest
from langchain_core.messages import AIMessage, HumanMessage

from smartqa.chain import Assistant, Answer
from smartqa.config import Settings
from smartqa.llm import DemoChatModel, build_llm, describe


@pytest.fixture()
def assistant(demo_settings: Settings, documents) -> Assistant:
    return Assistant(demo_settings, docs=documents)


def test_build_llm_returns_demo_model(demo_settings: Settings):
    llm = build_llm(demo_settings)
    assert isinstance(llm, DemoChatModel)
    assert "演示模式" in describe(demo_settings)


def test_online_provider_requires_api_key():
    with pytest.raises(RuntimeError, match="API Key"):
        build_llm(Settings(provider="openai", api_key=""))


def test_assistant_indexes_knowledge_base(assistant: Assistant):
    assert assistant.chunk_count > 0


def test_ask_returns_answer_with_sources(assistant: Assistant):
    answer = assistant.ask("GPL 和 MIT 许可证有什么区别？")
    assert isinstance(answer, Answer)
    assert answer.text.strip()
    assert answer.sources
    assert "演示模式" in answer.text
    assert all(label for label in answer.source_labels())


def test_answer_cites_relevant_document(assistant: Assistant):
    answer = assistant.ask("提交代码前为什么不能提交 API Key？")
    assert any("Git" in label for label in answer.source_labels())


def test_multi_turn_history_is_accepted(assistant: Assistant):
    history = [
        HumanMessage(content="什么是开源许可证？"),
        AIMessage(content="开源许可证是版权持有人授予使用者的许可。"),
    ]
    answer = assistant.ask("那 GPL 属于哪一类？", history)
    assert answer.text.strip()


def test_empty_question_is_rejected(assistant: Assistant):
    with pytest.raises(ValueError):
        assistant.ask("   ")


def test_empty_knowledge_base_is_safe(demo_settings: Settings):
    assistant = Assistant(demo_settings, docs=[])
    assert assistant.chunk_count == 0
    answer = assistant.ask("知识库为空时会怎样？")
    assert "没有检索到" in answer.text

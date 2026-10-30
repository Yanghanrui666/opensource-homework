"""模型接入层：在线大模型、离线大模型，以及可离线自检的演示模型。

对外只暴露一个 ``build_llm(settings)``，上层无需关心具体厂商。
"""

from __future__ import annotations

import re
from typing import Any, List, Optional, Sequence

from langchain_core.callbacks import CallbackManagerForLLMRun
from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.messages import AIMessage, BaseMessage, HumanMessage
from langchain_core.outputs import ChatGeneration, ChatResult

from .config import Settings


class DemoChatModel(BaseChatModel):
    """零依赖的规则模型，用于无网络 / 无 API Key 时演示与自动化测试。

    它不做真正的语言生成，而是从提示词中的参考资料里抽取与问题最相关的句子，
    拼成一段带来源标注的回答。这样"检索 → 提示词 → 模型 → 解析"整条链路
    依然被真实执行，只是把最后一步换成了确定性实现。
    """

    model_name: str = "smartqa-demo"

    @property
    def _llm_type(self) -> str:
        return "smartqa-demo"

    def _generate(
        self,
        messages: List[BaseMessage],
        stop: Optional[List[str]] = None,
        run_manager: Optional[CallbackManagerForLLMRun] = None,
        **kwargs: Any,
    ) -> ChatResult:
        prompt = "\n".join(_message_text(m) for m in messages)
        answer = _compose_answer(prompt)
        return ChatResult(generations=[ChatGeneration(message=AIMessage(content=answer))])


def _message_text(message: BaseMessage) -> str:
    content = message.content
    if isinstance(content, str):
        return content
    # 少数模型会返回 content blocks，这里统一拼成文本
    parts = [c.get("text", "") if isinstance(c, dict) else str(c) for c in content]
    return "\n".join(p for p in parts if p)


def _compose_answer(prompt: str) -> str:
    """从提示词里的标记块中抽取资料，生成确定性的演示回答。"""
    question = _extract(prompt, "【问题】", "【/问题】") or "（未识别到问题）"
    context = _extract(prompt, "【参考资料】", "【/参考资料】")

    if context.strip() in {"", "（无相关资料）"}:
        return (
            "（演示模式）知识库中没有检索到相关资料。\n"
            "建议换一种问法，或确认 data/knowledge 下是否已放入文档。"
        )

    sentences = _split_sentences(context)
    keywords = _keywords(question)
    ranked = sorted(
        sentences,
        key=lambda s: -sum(1 for k in keywords if k in s),
    )
    picked = [s for s in ranked[:3] if len(s.strip()) >= 8] or sentences[:2]
    body = "\n".join(f"- {s.strip()}" for s in picked)

    return (
        f"（演示模式回答）关于「{question.strip()}」，知识库中的相关信息如下：\n\n"
        f"{body}\n\n"
        "以上内容由本地规则模型根据检索结果整理；配置 SMARTQA_PROVIDER=openai "
        "或 ollama 后可获得大模型生成的完整回答。"
    )


def _extract(text: str, start: str, end: str) -> str:
    """取最后一个标记块，避免提示词里的示例文本被误当成正文。"""
    matches = re.findall(re.escape(start) + r"(.*?)" + re.escape(end), text, re.S)
    return matches[-1] if matches else ""


def _split_sentences(text: str) -> List[str]:
    chunks = re.split(r"(?<=[。！？；\n])", text)
    return [c.strip(" -\t") for c in chunks if c.strip()]


def _keywords(question: str) -> List[str]:
    tokens = re.findall(r"[\u4e00-\u9fff]{2,4}|[a-zA-Z]{2,}", question)
    return tokens[:6]


def build_llm(settings: Settings) -> BaseChatModel:
    """按配置构造聊天模型实例。"""
    provider = settings.provider

    if provider == "demo":
        return DemoChatModel()

    if provider == "openai":
        if not settings.api_key:
            raise RuntimeError(
                "在线模式需要 API Key：请在 .env 中设置 SMARTQA_API_KEY，"
                "或改用 SMARTQA_PROVIDER=demo / ollama。"
            )
        from langchain_openai import ChatOpenAI

        # base_url 指向任意 OpenAI 兼容网关（DeepSeek、通义、Kimi、vLLM…）
        return ChatOpenAI(
            model=settings.model,
            api_key=settings.api_key,
            base_url=settings.base_url or None,
            temperature=settings.temperature,
            timeout=60,
            max_retries=2,
        )

    if provider == "ollama":
        try:
            from langchain_ollama import ChatOllama
        except ImportError as exc:  # pragma: no cover - 可选依赖
            raise RuntimeError(
                "离线模式需要安装可选依赖：pip install langchain-ollama，并本地运行 Ollama。"
            ) from exc

        return ChatOllama(
            model=settings.model,
            base_url=settings.base_url or "http://localhost:11434",
            temperature=settings.temperature,
        )

    raise ValueError(f"未知的模型提供方：{provider}")


def describe(settings: Settings) -> str:
    """给界面用的模型描述文本。"""
    labels = {
        "demo": "演示模式（无需网络，规则模型）",
        "openai": f"在线模型（{settings.model} @ {settings.base_url}）",
        "ollama": f"离线模型（{settings.model} @ {settings.base_url}）",
    }
    return labels.get(settings.provider, settings.provider)


def make_messages(question: str, context: str) -> Sequence[BaseMessage]:
    """构造单轮消息，供脚本与测试直接调用。"""
    return [HumanMessage(content=f"【参考资料】\n{context}\n【/参考资料】\n\n【问题】{question}【/问题】")]

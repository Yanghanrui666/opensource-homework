"""smartqa —— 基于 LangChain 的课程知识库智能问答助手。

公开 API::

    from smartqa import Assistant, Settings

    assistant = Assistant(Settings.from_env())
    answer = assistant.ask("GPL 和 MIT 有什么区别？")
    print(answer.text)
"""

from .chain import Answer, Assistant, build_chain, build_prompt
from .config import PROVIDERS, Settings
from .llm import build_llm, describe
from .retriever import (
    TfidfRetriever,
    build_retriever,
    format_documents,
    load_documents,
    split_documents,
    tokenize,
)

__version__ = "1.0.0"

__all__ = [
    "Answer",
    "Assistant",
    "PROVIDERS",
    "Settings",
    "TfidfRetriever",
    "build_chain",
    "build_llm",
    "build_prompt",
    "build_retriever",
    "describe",
    "format_documents",
    "load_documents",
    "split_documents",
    "tokenize",
    "__version__",
]

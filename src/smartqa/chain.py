"""提示词与 LCEL 对话链：检索 → 拼装提示词 → 模型 → 解析 → 溯源。

整个问答流程用一个 Runnable 表达，便于 invoke / batch / 异步复用。
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional, Sequence

from langchain_core.documents import Document
from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.messages import BaseMessage
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.runnables import Runnable, RunnableLambda, RunnablePassthrough

from .config import Settings
from .llm import build_llm
from .retriever import build_retriever, format_documents

SYSTEM_PROMPT = """你是《开源软件》课程的学习助手「开源小答」。

回答规则：
1. 只依据下方"参考资料"中的内容作答，不要编造资料之外的事实。
2. 如果参考资料不足以回答，请直接说明"资料中没有找到相关内容"，并给出可尝试的方向。
3. 回答使用简体中文，先给结论，再给要点，必要时用小标题或列表。
4. 引用资料时标注来源编号，例如 [来源: 01-开源许可证.md #3]。
5. 教学场景下优先解释概念之间的联系，而不只是罗列结论。"""

HUMAN_TEMPLATE = """【参考资料】
{context}
【/参考资料】

【问题】{question}【/问题】"""


@dataclass
class Answer:
    """一次问答的结果：答案文本 + 命中的知识片段。"""

    text: str
    sources: List[Document]

    def source_labels(self) -> List[str]:
        labels = []
        for doc in self.sources:
            source = doc.metadata.get("source", "unknown")
            chunk = doc.metadata.get("chunk", "-")
            labels.append(f"{source} #{chunk}")
        return labels


def build_prompt() -> ChatPromptTemplate:
    """构造多轮提示词模板：系统角色 + 历史消息 + 参考资料与问题。"""
    return ChatPromptTemplate.from_messages(
        [
            ("system", SYSTEM_PROMPT),
            MessagesPlaceholder("history", optional=True),
            ("human", HUMAN_TEMPLATE),
        ]
    )


def build_chain(
    llm: BaseChatModel, retriever, prompt: Optional[ChatPromptTemplate] = None
) -> Runnable:
    """组合出完整的 RAG 链，输入 {"question": str, "history": [...]}，输出 Answer。"""
    prompt = prompt or build_prompt()

    def retrieve(payload: dict) -> List[Document]:
        return retriever.invoke(payload["question"])

    return (
        RunnablePassthrough.assign(documents=RunnableLambda(retrieve))
        | RunnablePassthrough.assign(
            context=RunnableLambda(lambda payload: format_documents(payload["documents"]))
        )
        | RunnablePassthrough.assign(
            answer=prompt | llm | StrOutputParser()
        )
        | RunnableLambda(
            lambda payload: Answer(text=payload["answer"], sources=payload["documents"])
        )
    )


class Assistant:
    """对外门面：持有检索器与模型，提供 ask() 供界面 / CLI / 测试调用。"""

    def __init__(
        self,
        settings: Settings,
        docs: Optional[Sequence[Document]] = None,
        llm: Optional[BaseChatModel] = None,
    ) -> None:
        self.settings = settings
        self.llm = llm or build_llm(settings)
        self.retriever, self.chunks = build_retriever(settings, docs)
        self.chain = build_chain(self.llm, self.retriever)

    @property
    def chunk_count(self) -> int:
        return len(self.chunks)

    def ask(self, question: str, history: Optional[Sequence[BaseMessage]] = None) -> Answer:
        question = (question or "").strip()
        if not question:
            raise ValueError("问题不能为空。")
        return self.chain.invoke({"question": question, "history": list(history or [])})

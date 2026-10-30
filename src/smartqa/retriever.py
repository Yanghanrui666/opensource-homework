"""知识库加载与检索。

默认使用零依赖的 TF-IDF 关键词检索（中文按字/二元组切分），
无需下载 embedding 模型即可离线运行；也可切换为向量检索。
"""

from __future__ import annotations

import math
import re
from collections import Counter
from pathlib import Path
from typing import Any, Iterable, List, Optional, Sequence

from langchain_core.callbacks import CallbackManagerForRetrieverRun
from langchain_core.documents import Document
from langchain_core.retrievers import BaseRetriever

from .config import Settings

SUPPORTED_SUFFIXES = {".md", ".markdown", ".txt"}

_TOKEN_RE = re.compile(r"[A-Za-z][A-Za-z0-9_+#.-]*|\d+(?:\.\d+)*|[\u4e00-\u9fff]")


def tokenize(text: str) -> List[str]:
    """英文按词、数字按整体、中文按单字 + 相邻二元组切分。

    二元组能显著改善中文短查询的召回（例如"开源许可证"能命中"许可证"）。
    """
    raw = _TOKEN_RE.findall(text.lower())
    tokens: List[str] = []
    cjk_run: List[str] = []

    def flush() -> None:
        if not cjk_run:
            return
        tokens.extend(cjk_run)
        tokens.extend(a + b for a, b in zip(cjk_run, cjk_run[1:]))
        cjk_run.clear()

    for token in raw:
        if len(token) == 1 and "\u4e00" <= token <= "\u9fff":
            cjk_run.append(token)
        else:
            flush()
            tokens.append(token)
    flush()
    return tokens


def load_documents(directory: Path) -> List[Document]:
    """读取目录下所有 Markdown / 文本文件，附带来源元数据。"""
    directory = Path(directory)
    if not directory.exists():
        return []

    docs: List[Document] = []
    for path in sorted(directory.rglob("*")):
        if not path.is_file() or path.suffix.lower() not in SUPPORTED_SUFFIXES:
            continue
        text = path.read_text(encoding="utf-8", errors="ignore").strip()
        if not text:
            continue
        docs.append(
            Document(
                page_content=text,
                metadata={"source": str(path.relative_to(directory)).replace("\\", "/")},
            )
        )
    return docs


def split_documents(
    docs: Sequence[Document], chunk_size: int = 500, chunk_overlap: int = 80
) -> List[Document]:
    """按语义边界递归切块，保留来源与块序号，便于回答时溯源。"""
    from langchain_text_splitters import RecursiveCharacterTextSplitter

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        separators=["\n\n", "\n", "。", "；", "，", " ", ""],
    )
    chunks = splitter.split_documents(list(docs))
    for index, chunk in enumerate(chunks):
        chunk.metadata["chunk"] = index
    return chunks


class TfidfRetriever(BaseRetriever):
    """基于 TF-IDF 余弦相似度的检索器（纯 Python，无外部模型）。"""

    documents: List[Document]
    k: int = 4

    _idf: dict = {}
    _vectors: List[dict] = []
    _norms: List[float] = []

    def model_post_init(self, __context: Any) -> None:
        self._build_index()

    def _build_index(self) -> None:
        token_lists = [tokenize(doc.page_content) for doc in self.documents]
        doc_freq: Counter = Counter()
        for tokens in token_lists:
            doc_freq.update(set(tokens))

        total = max(len(token_lists), 1)
        self._idf = {
            term: math.log((total + 1) / (freq + 1)) + 1.0 for term, freq in doc_freq.items()
        }

        self._vectors = []
        self._norms = []
        for tokens in token_lists:
            vector = self._weigh(tokens)
            self._vectors.append(vector)
            self._norms.append(math.sqrt(sum(v * v for v in vector.values())) or 1.0)

    def _weigh(self, tokens: Iterable[str]) -> dict:
        counts = Counter(tokens)
        vector = {}
        for term, count in counts.items():
            idf = self._idf.get(term)
            if idf is None:
                continue
            vector[term] = (1.0 + math.log(count)) * idf
        return vector

    def _get_relevant_documents(
        self, query: str, *, run_manager: Optional[CallbackManagerForRetrieverRun] = None
    ) -> List[Document]:
        if not self.documents:
            return []

        query_vector = self._weigh(tokenize(query))
        query_norm = math.sqrt(sum(v * v for v in query_vector.values())) or 1.0

        scored = []
        for index, vector in enumerate(self._vectors):
            dot = sum(weight * vector.get(term, 0.0) for term, weight in query_vector.items())
            if dot > 0:
                scored.append((dot / (query_norm * self._norms[index]), index))

        if not scored:  # 完全没有词面重叠时退化为前 k 篇，保证仍有上下文
            return list(self.documents[: self.k])

        scored.sort(key=lambda item: (-item[0], item[1]))
        return [self.documents[index] for _, index in scored[: self.k]]


def build_vector_retriever(docs: Sequence[Document], settings: Settings):
    """可选的向量检索：OpenAI 兼容 embedding 接口 + 内存向量库（无需本地模型）。"""
    from langchain_core.vectorstores import InMemoryVectorStore
    from langchain_openai import OpenAIEmbeddings

    if not settings.api_key:
        raise RuntimeError("向量检索需要 SMARTQA_API_KEY。")

    embeddings = OpenAIEmbeddings(
        model=settings.embedding_model,
        api_key=settings.api_key,
        base_url=settings.base_url or None,
    )
    store = InMemoryVectorStore.from_documents(list(docs), embeddings)
    return store.as_retriever(search_kwargs={"k": settings.top_k})


def build_retriever(settings: Settings, docs: Optional[Sequence[Document]] = None):
    """加载、切块并构造检索器；返回 (retriever, chunks)。"""
    source = list(docs) if docs is not None else load_documents(settings.knowledge_dir)
    chunks = split_documents(source)
    if not chunks:
        # 空知识库也返回合法检索器，避免界面崩溃
        return TfidfRetriever(documents=[], k=max(settings.top_k, 1)), []

    if settings.use_embeddings and settings.api_key:
        return build_vector_retriever(chunks, settings), chunks
    return TfidfRetriever(documents=chunks, k=max(settings.top_k, 1)), chunks


def format_documents(docs: Sequence[Document]) -> str:
    """把检索结果拼成提示词中的参考资料块，带可读的来源标注。"""
    if not docs:
        return "（无相关资料）"
    blocks = []
    for doc in docs:
        source = doc.metadata.get("source", "unknown")
        chunk = doc.metadata.get("chunk", "-")
        blocks.append(f"[来源: {source} #{chunk}]\n{doc.page_content.strip()}")
    return "\n\n".join(blocks)

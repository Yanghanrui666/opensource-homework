"""检索层单元测试：分词、加载、切块、TF-IDF 排序。"""

from __future__ import annotations

from smartqa.retriever import TfidfRetriever, load_documents, split_documents, tokenize


def docs_with_chunks(documents):
    return split_documents(documents, chunk_size=300, chunk_overlap=40)


def test_tokenize_keeps_english_words_and_chinese_bigrams():
    tokens = tokenize("GPL 许可证与 MIT")
    assert "gpl" in tokens
    assert "mit" in tokens
    # 中文按单字 + 相邻二元组切分，"许可"应当出现
    assert "许可" in tokens


def test_load_documents_reads_markdown_with_source_metadata(documents):
    assert len(documents) >= 4
    sources = {doc.metadata["source"] for doc in documents}
    assert any("许可证" in name for name in sources)
    assert all(doc.page_content.strip() for doc in documents)


def test_load_documents_handles_missing_directory(temp_dir):
    assert load_documents(temp_dir / "not-exists") == []


def test_split_documents_keeps_metadata_and_respects_chunk_size(documents):
    chunks = split_documents(documents, chunk_size=300, chunk_overlap=50)
    assert len(chunks) > len(documents)
    assert all(chunk.metadata.get("source") for chunk in chunks)
    assert all(len(chunk.page_content) <= 400 for chunk in chunks)


def test_tfidf_retriever_ranks_license_document_first(documents):
    retriever = TfidfRetriever(documents=docs_with_chunks(documents), k=2)
    hits = retriever.invoke("GPL 和 MIT 许可证有什么区别")
    assert hits
    assert "许可证" in hits[0].metadata["source"]


def test_tfidf_retriever_returns_empty_without_documents():
    assert TfidfRetriever(documents=[], k=3).invoke("任意问题") == []


def test_tfidf_retriever_falls_back_when_no_term_overlap(documents):
    retriever = TfidfRetriever(documents=docs_with_chunks(documents), k=2)
    hits = retriever.invoke("zzzz-完全不相关的词")
    assert len(hits) == 2

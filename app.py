"""Streamlit 界面：课程知识库智能问答助手。

启动::

    streamlit run app.py
"""

from __future__ import annotations

import sys
from pathlib import Path

import streamlit as st
from langchain_core.messages import AIMessage, HumanMessage

# 允许直接 `streamlit run app.py`，无需先 pip install -e .
SRC = Path(__file__).resolve().parent / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from smartqa import Assistant, Settings, describe  # noqa: E402
from smartqa.llm import DemoChatModel  # noqa: E402

st.set_page_config(
    page_title="开源小答 · 课程知识库助手",
    page_icon="🦜",
    layout="wide",
)

EXAMPLES = [
    "GPL 和 MIT 许可证有什么区别？",
    "开源项目为什么不能提交 API Key？",
    "LangChain 的 LCEL 是什么？",
    "RAG 的切块大小一般设多少？",
]


def knowledge_signature(directory: Path) -> str:
    """知识库文件指纹，用于判断是否需要重建检索索引。"""
    if not directory.exists():
        return "missing"
    files = sorted(directory.rglob("*"))
    parts = [f"{f.name}:{f.stat().st_mtime_ns}" for f in files if f.is_file()]
    return str(hash("|".join(parts)))


@st.cache_resource(show_spinner=False)
def get_assistant(
    provider: str,
    model: str,
    base_url: str,
    api_key: str,
    temperature: float,
    top_k: int,
    knowledge_dir: str,
    use_embeddings: bool,
    signature: str,
) -> Assistant:
    settings = Settings(
        provider=provider,
        model=model,
        base_url=base_url,
        api_key=api_key,
        temperature=temperature,
        top_k=top_k,
        knowledge_dir=Path(knowledge_dir),
        use_embeddings=use_embeddings,
    )
    return Assistant(settings)


def sidebar() -> dict:
    st.sidebar.title("⚙️ 运行配置")
    st.sidebar.caption("配置变更后会自动重建模型与索引")

    provider = st.sidebar.selectbox(
        "模型提供方",
        options=["demo", "openai", "ollama"],
        index=0,
        help="demo 无需网络；openai 为任意 OpenAI 兼容接口；ollama 为本地离线模型",
    )

    defaults = {
        "demo": ("smartqa-demo", ""),
        "openai": ("deepseek-chat", "https://api.deepseek.com/v1"),
        "ollama": ("qwen2.5:7b", "http://localhost:11434"),
    }[provider]

    model = st.sidebar.text_input("模型名称", value=defaults[0])
    base_url = st.sidebar.text_input("接口地址", value=defaults[1])

    api_key = ""
    if provider == "openai":
        api_key = st.sidebar.text_input("API Key", type="password", help="仅保存在当前会话，不落盘")

    st.sidebar.divider()
    temperature = st.sidebar.slider("温度 temperature", 0.0, 1.0, 0.2, 0.05)
    top_k = st.sidebar.slider("检索片段数 top-k", 1, 8, 4)
    use_embeddings = st.sidebar.checkbox(
        "使用向量检索", value=False, help="需要 API Key 调用 embedding 接口；默认使用本地 TF-IDF"
    )

    knowledge_dir = st.sidebar.text_input(
        "知识库目录", value=str(Settings.from_env().knowledge_dir)
    )

    st.sidebar.divider()
    st.sidebar.caption("知识库支持 Markdown / TXT，修改文件后界面会自动重新索引。")

    return {
        "provider": provider,
        "model": model,
        "base_url": base_url,
        "api_key": api_key,
        "temperature": temperature,
        "top_k": top_k,
        "use_embeddings": use_embeddings,
        "knowledge_dir": knowledge_dir,
    }


def build_history() -> list:
    history = []
    for message in st.session_state.messages:
        if message["role"] == "user":
            history.append(HumanMessage(content=message["content"]))
        else:
            history.append(AIMessage(content=message["content"]))
    return history


def render_sources(answer) -> None:
    if not answer.sources:
        return
    with st.expander(f"📚 参考资料（{len(answer.sources)} 段）"):
        for doc, label in zip(answer.sources, answer.source_labels()):
            st.markdown(f"**{label}**")
            st.caption(doc.page_content.strip()[:400] + ("…" if len(doc.page_content) > 400 else ""))


def main() -> None:
    config = sidebar()

    st.title("🦜 开源小答 · 课程知识库智能助手")
    st.caption("基于 LangChain + 检索增强生成（RAG）｜支持在线大模型、本地离线模型与无网络演示")

    knowledge_dir = Path(config["knowledge_dir"])
    signature = knowledge_signature(knowledge_dir)

    try:
        assistant = get_assistant(
            config["provider"],
            config["model"],
            config["base_url"],
            config["api_key"],
            config["temperature"],
            config["top_k"],
            str(knowledge_dir),
            config["use_embeddings"],
            signature,
        )
    except Exception as exc:  # 配置错误时给出可操作提示，而不是整页崩溃
        st.error(f"初始化失败：{exc}")
        st.info("检查右侧配置：在线模式需要 API Key，离线模式需要先启动 Ollama。")
        st.stop()

    col1, col2, col3 = st.columns(3)
    col1.metric("知识片段", assistant.chunk_count)
    col2.metric("检索方式", "向量检索" if config["use_embeddings"] else "TF-IDF")
    col3.metric("模型", describe(assistant.settings).split("（")[0])

    if assistant.chunk_count == 0:
        st.warning("知识库为空：请在 data/knowledge 放入 Markdown 或 TXT 文档后重试。")

    if "messages" not in st.session_state:
        st.session_state.messages = []

    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])
            if message.get("sources"):
                with st.expander(f"📚 参考资料（{len(message['sources'])} 段）"):
                    for label, content in message["sources"]:
                        st.markdown(f"**{label}**")
                        st.caption(content)

    if not st.session_state.messages:
        st.markdown("#### 试试这些问题")
        cols = st.columns(2)
        for index, example in enumerate(EXAMPLES):
            if cols[index % 2].button(example, use_container_width=True):
                st.session_state.pending = example
                st.rerun()

    prompt = st.chat_input("输入你的问题，例如：AGPL 和 GPL 的区别是什么？")
    if "pending" in st.session_state:
        prompt = st.session_state.pop("pending")

    if not prompt:
        return

    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        with st.spinner("正在检索知识库并生成回答…"):
            try:
                answer = assistant.ask(prompt, build_history()[:-1])
            except Exception as exc:
                st.error(f"调用模型失败：{exc}")
                st.info(
                    "演示模式可直接使用；在线模式请检查 API Key、接口地址与余额；"
                    "离线模式请确认 Ollama 已启动并已拉取模型。"
                )
                st.session_state.messages.pop()
                st.stop()

        st.markdown(answer.text)
        render_sources(answer)

    st.session_state.messages.append(
        {
            "role": "assistant",
            "content": answer.text,
            "sources": [
                (label, doc.page_content.strip()[:400] + ("…" if len(doc.page_content) > 400 else ""))
                for doc, label in zip(answer.sources, answer.source_labels())
            ],
        }
    )

    if isinstance(assistant.llm, DemoChatModel):
        st.caption("当前为演示模式：回答由本地规则模型整理，配置真实模型后可获得完整生成效果。")


if __name__ == "__main__":
    main()

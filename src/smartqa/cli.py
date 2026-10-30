"""命令行入口：单轮问答与交互式会话。

用法::

    python -m smartqa.cli -q "GPL 和 MIT 有什么区别？"
    python -m smartqa.cli -i
    python -m smartqa.cli -i --provider openai --model deepseek-chat
"""

from __future__ import annotations

import argparse
import sys
from typing import List

from langchain_core.messages import AIMessage, BaseMessage, HumanMessage

from .chain import Assistant
from .config import PROVIDERS, Settings
from .llm import describe


def parse_args(argv: List[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="smartqa",
        description="课程知识库智能问答助手（LangChain + RAG）",
    )
    parser.add_argument("-q", "--question", help="单轮提问，回答后退出")
    parser.add_argument("-i", "--interactive", action="store_true", help="进入交互式多轮会话")
    parser.add_argument("--provider", choices=PROVIDERS, help="模型提供方，覆盖环境变量")
    parser.add_argument("--model", help="模型名称，覆盖环境变量")
    parser.add_argument("--base-url", dest="base_url", help="OpenAI 兼容接口或 Ollama 地址")
    parser.add_argument("--api-key", dest="api_key", help="API Key，覆盖环境变量")
    parser.add_argument("--top-k", dest="top_k", type=int, help="检索片段数")
    parser.add_argument("--knowledge-dir", dest="knowledge_dir", help="知识库目录")
    parser.add_argument("--show-sources", action="store_true", help="打印命中的知识片段")
    return parser.parse_args(argv)


def build_settings(args: argparse.Namespace) -> Settings:
    settings = Settings.from_env()
    overrides = {
        "provider": args.provider,
        "model": args.model,
        "base_url": args.base_url,
        "api_key": args.api_key,
        "top_k": args.top_k,
    }
    if args.knowledge_dir:
        from pathlib import Path

        overrides["knowledge_dir"] = Path(args.knowledge_dir)
    return settings.replace(**{k: v for k, v in overrides.items() if v is not None})


def print_answer(answer, show_sources: bool) -> None:
    print()
    print(answer.text)
    if show_sources and answer.sources:
        print("\n--- 参考来源 ---")
        for label in answer.source_labels():
            print(f"  · {label}")
    print()


def interact(assistant: Assistant, show_sources: bool) -> int:
    print("开源小答 · 交互模式（输入 exit 退出，输入 /clear 清空上下文）")
    print(f"模型：{describe(assistant.settings)} | 知识片段：{assistant.chunk_count}")
    history: List[BaseMessage] = []

    while True:
        try:
            question = input("你 > ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\n再见。")
            return 0

        if not question:
            continue
        if question.lower() in {"exit", "quit", "q"}:
            print("再见。")
            return 0
        if question == "/clear":
            history.clear()
            print("上下文已清空。\n")
            continue

        answer = assistant.ask(question, history)
        print_answer(answer, show_sources)
        history.extend([HumanMessage(content=question), AIMessage(content=answer.text)])


def main(argv: List[str] | None = None) -> int:
    args = parse_args(argv)
    if not args.question and not args.interactive:
        print("请使用 -q 提问，或使用 -i 进入交互模式。", file=sys.stderr)
        return 2

    assistant = Assistant(build_settings(args))

    if assistant.chunk_count == 0:
        print("警告：知识库为空，回答将缺少参考资料。", file=sys.stderr)

    if args.interactive:
        return interact(assistant, args.show_sources)

    print(f"模型：{describe(assistant.settings)} | 知识片段：{assistant.chunk_count}")
    print_answer(assistant.ask(args.question), args.show_sources)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

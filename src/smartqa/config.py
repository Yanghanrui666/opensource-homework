"""集中配置：从环境变量 / .env 读取，所有模块共用。

配置项按"模型 + 检索 + 界面"三类组织，避免在业务代码里散落 os.environ。
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv

# 仓库根目录（src/smartqa/config.py -> 上三级）
ROOT = Path(__file__).resolve().parents[2]

# 只在存在 .env 时加载，缺失不报错，方便 CI 与离线环境
load_dotenv(ROOT / ".env", override=False)

# 支持的模型提供方：演示 / 在线（OpenAI 兼容接口）/ 离线（Ollama）
PROVIDERS = ("demo", "openai", "ollama")


@dataclass(frozen=True)
class Settings:
    """运行期配置快照，不可变，便于测试与跨线程传递。"""

    provider: str = "demo"
    model: str = "deepseek-chat"
    api_key: str = ""
    base_url: str = "https://api.deepseek.com/v1"
    temperature: float = 0.2
    top_k: int = 4
    knowledge_dir: Path = ROOT / "data" / "knowledge"
    use_embeddings: bool = False
    embedding_model: str = "text-embedding-3-small"

    @classmethod
    def from_env(cls) -> "Settings":
        """从环境变量构造配置；非法值回落到默认值而不是抛异常。"""
        provider = os.getenv("SMARTQA_PROVIDER", "demo").strip().lower()
        if provider not in PROVIDERS:
            provider = "demo"

        return cls(
            provider=provider,
            model=os.getenv("SMARTQA_MODEL", "deepseek-chat").strip() or "deepseek-chat",
            api_key=os.getenv("SMARTQA_API_KEY", "").strip(),
            base_url=os.getenv("SMARTQA_BASE_URL", "https://api.deepseek.com/v1").strip(),
            temperature=_to_float(os.getenv("SMARTQA_TEMPERATURE"), 0.2),
            top_k=_to_int(os.getenv("SMARTQA_TOP_K"), 4),
            knowledge_dir=Path(
                os.getenv("SMARTQA_KNOWLEDGE_DIR", str(ROOT / "data" / "knowledge"))
            ),
            use_embeddings=_to_bool(os.getenv("SMARTQA_USE_EMBEDDINGS"), False),
            embedding_model=os.getenv("SMARTQA_EMBEDDING_MODEL", "text-embedding-3-small"),
        )

    def replace(self, **kwargs) -> "Settings":
        """返回修改后的副本，用于界面上的即时调参。"""
        from dataclasses import replace

        return replace(self, **kwargs)


def _to_float(raw: str | None, default: float) -> float:
    try:
        return float(raw) if raw not in (None, "") else default
    except (TypeError, ValueError):
        return default


def _to_int(raw: str | None, default: int) -> int:
    try:
        return int(raw) if raw not in (None, "") else default
    except (TypeError, ValueError):
        return default


def _to_bool(raw: str | None, default: bool) -> bool:
    if raw is None or raw == "":
        return default
    return raw.strip().lower() in {"1", "true", "yes", "on"}

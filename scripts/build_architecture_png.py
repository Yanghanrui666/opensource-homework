"""生成 README 用的系统架构图（无需联网，纯 Pillow 绘制）。"""

from __future__ import annotations

import math
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

OUT = Path(__file__).resolve().parents[1] / "docs" / "assets" / "architecture.png"
FONT = r"C:\Windows\Fonts\msyh.ttc"

W, H = 1320, 590
BG = "#FFFFFF"
PROC_FILL, PROC_LINE = "#E8F1FB", "#2F6FBA"
DATA_FILL, DATA_LINE = "#E9F5EA", "#3F9142"
MODEL_FILL, MODEL_LINE = "#FDF0E3", "#D97706"
CHIP_FILL, CHIP_LINE = "#F7F8FA", "#9AA5B1"
ARROW = "#5B6570"


def font(size: int) -> ImageFont.FreeTypeFont:
    return ImageFont.truetype(FONT, size)


def box(draw, xy, title, subtitle, fill, line, title_size=20, sub_size=14):
    x0, y0, x1, y1 = xy
    draw.rounded_rectangle(xy, radius=12, fill=fill, outline=line, width=2)
    cy = (y0 + y1) / 2
    if subtitle:
        draw.text(((x0 + x1) / 2, cy - 12), title, font=font(title_size), fill="#1F2937", anchor="mm")
        draw.text(((x0 + x1) / 2, cy + 14), subtitle, font=font(sub_size), fill="#4B5563", anchor="mm")
    else:
        draw.text(((x0 + x1) / 2, cy), title, font=font(title_size), fill="#1F2937", anchor="mm")


def arrow(draw, start, end, dashed=False, color=ARROW, width=2, head=True):
    x0, y0 = start
    x1, y1 = end
    if dashed:
        total = math.hypot(x1 - x0, y1 - y0)
        n = max(int(total // 10), 2)
        for i in range(0, n, 2):
            a, b = i / n, min((i + 1) / n, 1)
            draw.line(
                [x0 + (x1 - x0) * a, y0 + (y1 - y0) * a, x0 + (x1 - x0) * b, y0 + (y1 - y0) * b],
                fill=color,
                width=width,
            )
    else:
        draw.line([x0, y0, x1, y1], fill=color, width=width)

    if head:
        angle = math.atan2(y1 - y0, x1 - x0)
        size = 9
        p1 = (x1 - size * math.cos(angle - 0.4), y1 - size * math.sin(angle - 0.4))
        p2 = (x1 - size * math.cos(angle + 0.4), y1 - size * math.sin(angle + 0.4))
        draw.polygon([(x1, y1), p1, p2], fill=color)


def main() -> None:
    OUT.parent.mkdir(parents=True, exist_ok=True)
    img = Image.new("RGB", (W, H), BG)
    d = ImageDraw.Draw(img)

    # 数据层
    box(d, (40, 40, 330, 130), "课程知识库", "data/knowledge · Markdown / TXT", DATA_FILL, DATA_LINE)
    box(d, (380, 40, 670, 130), "递归切块", "500 字 / 重叠 80", DATA_FILL, DATA_LINE)
    arrow(d, (334, 85), (376, 85))

    # 主链路
    y0, y1 = 235, 335
    xs = [40, 262, 484, 706, 928, 1150]
    labels = [
        ("用户提问", "自然语言问题"),
        ("检索器", "TF-IDF / 向量检索"),
        ("资料拼装", "Top-K 片段 + 来源"),
        ("提示词模板", "系统指令 + 历史 + 资料"),
        ("大模型", "在线 / 离线 / 演示"),
        ("回答", "结论 + 引用标注"),
    ]
    for x, (title, sub) in zip(xs, labels):
        fill, line = (MODEL_FILL, MODEL_LINE) if title == "大模型" else (PROC_FILL, PROC_LINE)
        box(d, (x, y0, x + 170, y1), title, sub, fill, line, title_size=19, sub_size=13)

    for i in range(len(xs) - 1):
        arrow(d, (xs[i] + 170, (y0 + y1) // 2), (xs[i + 1] - 4, (y0 + y1) // 2))

    # 切块 → 检索器（折线）
    d.line([(525, 130), (525, 185)], fill=ARROW, width=2)
    d.line([(525, 185), (347, 185)], fill=ARROW, width=2)
    arrow(d, (347, 185), (347, 231), dashed=True)

    # 模型接入层
    layer = (40, 425, 1098, 545)
    d.rounded_rectangle(layer, radius=12, fill="#FFFBF4", outline=MODEL_LINE, width=2)
    d.text((60, 440), "模型接入层（llm.py）· 同一套链与提示词，切换只需改环境变量", font=font(14), fill="#92400E")
    chips = [
        (70, "演示模式", "DemoChatModel · 无网络"),
        (430, "在线模式", "OpenAI 兼容接口"),
        (790, "离线模式", "Ollama 本地模型"),
    ]
    for x, title, sub in chips:
        box(d, (x, 470, x + 280, 528), title, sub, CHIP_FILL, CHIP_LINE, title_size=16, sub_size=12)

    arrow(d, (1013, 335), (1013, 421), dashed=True)

    img.save(OUT)
    print(f"saved {OUT} ({OUT.stat().st_size} bytes)")


if __name__ == "__main__":
    main()

"""把 README 内容排版成可上传的 Word 文档说明。"""

from __future__ import annotations

from pathlib import Path

from docx import Document
from docx.enum.section import WD_SECTION
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_BREAK, WD_TAB_ALIGNMENT, WD_TAB_LEADER
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Cm, Pt, RGBColor

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "docs" / "开源小答-README文档说明.docx"
ARCH = ROOT / "docs" / "assets" / "architecture.png"

REPO = "https://github.com/Yanghanrui666/opensource-homework"
EA_BODY = "宋体"
EA_HEAD = "微软雅黑"
LATIN_BODY = "Times New Roman"
LATIN_HEAD = "Microsoft YaHei"
MONO = "Consolas"

DARK_BLUE = RGBColor(0x1F, 0x38, 0x64)
GRAY = RGBColor(0x59, 0x5F, 0x69)


# --------------------------------------------------------------------------- #
# 基础排版工具
# --------------------------------------------------------------------------- #
def set_run_font(run, latin=LATIN_BODY, ea=EA_BODY, size=10.5, bold=False, color=None):
    run.font.name = latin
    run.font.size = Pt(size)
    run.font.bold = bold
    if color is not None:
        run.font.color.rgb = color
    rpr = run._element.get_or_add_rPr()
    rfonts = rpr.find(qn("w:rFonts"))
    if rfonts is None:
        rfonts = OxmlElement("w:rFonts")
        rpr.append(rfonts)
    rfonts.set(qn("w:ascii"), latin)
    rfonts.set(qn("w:hAnsi"), latin)
    rfonts.set(qn("w:eastAsia"), ea)


def style_font(style, latin, ea, size, bold=False, color=None):
    style.font.name = latin
    style.font.size = Pt(size)
    style.font.bold = bold
    if color is not None:
        style.font.color.rgb = color
    rpr = style.element.get_or_add_rPr()
    rfonts = rpr.find(qn("w:rFonts"))
    if rfonts is None:
        rfonts = OxmlElement("w:rFonts")
        rpr.append(rfonts)
    rfonts.set(qn("w:ascii"), latin)
    rfonts.set(qn("w:hAnsi"), latin)
    rfonts.set(qn("w:eastAsia"), ea)


def shade(paragraph, fill="F5F6F8"):
    ppr = paragraph._p.get_or_add_pPr()
    shd = OxmlElement("w:shd")
    shd.set(qn("w:val"), "clear")
    shd.set(qn("w:color"), "auto")
    shd.set(qn("w:fill"), fill)
    ppr.append(shd)


def left_border(paragraph, color="2F6FBA"):
    ppr = paragraph._p.get_or_add_pPr()
    pbdr = OxmlElement("w:pBdr")
    left = OxmlElement("w:left")
    left.set(qn("w:val"), "single")
    left.set(qn("w:sz"), "18")
    left.set(qn("w:space"), "8")
    left.set(qn("w:color"), color)
    pbdr.append(left)
    ppr.append(pbdr)


def body(doc, text, space_after=6, indent=True, size=10.5):
    p = doc.add_paragraph()
    p.paragraph_format.space_after = Pt(space_after)
    p.paragraph_format.line_spacing = 1.4
    if indent:
        p.paragraph_format.first_line_indent = Pt(21)
    run = p.add_run(text)
    set_run_font(run, size=size)
    return p


def bullet(doc, text, size=10.5):
    p = doc.add_paragraph(style="List Bullet")
    p.paragraph_format.space_after = Pt(3)
    p.paragraph_format.line_spacing = 1.3
    run = p.add_run(text)
    set_run_font(run, size=size)
    return p


def heading(doc, text, level=1):
    p = doc.add_paragraph()
    p.paragraph_format.space_before = Pt(16 if level == 1 else 10)
    p.paragraph_format.space_after = Pt(8 if level == 1 else 5)
    p.paragraph_format.keep_with_next = True
    run = p.add_run(text)
    if level == 1:
        set_run_font(run, LATIN_HEAD, EA_HEAD, 15, bold=True, color=DARK_BLUE)
    else:
        set_run_font(run, LATIN_HEAD, EA_HEAD, 12, bold=True, color=RGBColor(0x2F, 0x54, 0x96))
    return p


def caption(doc, text):
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p.paragraph_format.space_before = Pt(4)
    p.paragraph_format.space_after = Pt(10)
    run = p.add_run(text)
    set_run_font(run, LATIN_HEAD, EA_HEAD, 9, color=GRAY)


def code_block(doc, text):
    p = doc.add_paragraph()
    p.paragraph_format.space_before = Pt(4)
    p.paragraph_format.space_after = Pt(8)
    p.paragraph_format.left_indent = Cm(0.35)
    p.paragraph_format.line_spacing = 1.15
    p.paragraph_format.keep_together = True  # 代码块不跨页拆分
    shade(p)
    left_border(p)

    lines = text.strip("\n").split("\n")
    for index, line in enumerate(lines):
        run = p.add_run(line)
        set_run_font(run, MONO, EA_BODY, 8.5)
        if index < len(lines) - 1:
            run.add_break()
    return p


def table(doc, headers, rows, widths, font_size=9.5, keep_together=True):
    t = doc.add_table(rows=1, cols=len(headers))
    t.style = "Light Grid Accent 1"
    t.alignment = WD_TABLE_ALIGNMENT.CENTER
    t.autofit = False

    for index, text in enumerate(headers):
        cell = t.rows[0].cells[index]
        cell.text = ""
        run = cell.paragraphs[0].add_run(text)
        set_run_font(run, LATIN_HEAD, EA_HEAD, font_size, bold=True)

    for row in rows:
        cells = t.add_row().cells
        for index, text in enumerate(row):
            cells[index].text = ""
            run = cells[index].paragraphs[0].add_run(str(text))
            set_run_font(run, LATIN_BODY, EA_BODY, font_size)

    for row in t.rows:
        for index, width in enumerate(widths):
            row.cells[index].width = Cm(width)
        for cell in row.cells:
            for paragraph in cell.paragraphs:
                paragraph.paragraph_format.space_before = Pt(2)
                paragraph.paragraph_format.space_after = Pt(2)
                paragraph.paragraph_format.line_spacing = 1.15

    # 表头跨页重复；单元格内容不跨页拆行
    header_tr = t.rows[0]._tr
    tr_pr = header_tr.get_or_add_trPr()
    tbl_header = OxmlElement("w:tblHeader")
    tbl_header.set(qn("w:val"), "true")
    tr_pr.append(tbl_header)

    for row in t.rows:
        pr = row._tr.get_or_add_trPr()
        cant_split = OxmlElement("w:cantSplit")
        pr.append(cant_split)

    # 小表整体保持在同一页：除最后一行外都设置"与下段同页"
    if keep_together:
        for row in t.rows[:-1]:
            for cell in row.cells:
                for paragraph in cell.paragraphs:
                    paragraph.paragraph_format.keep_with_next = True

    doc.add_paragraph().paragraph_format.space_after = Pt(2)
    return t


def add_footer_page_number(section):
    p = section.footer.paragraphs[0]
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run = p.add_run("第 ")
    set_run_font(run, LATIN_BODY, EA_BODY, 9, color=GRAY)

    fld_begin = OxmlElement("w:fldChar")
    fld_begin.set(qn("w:fldCharType"), "begin")
    instr = OxmlElement("w:instrText")
    instr.set(qn("xml:space"), "preserve")
    instr.text = "PAGE"
    fld_end = OxmlElement("w:fldChar")
    fld_end.set(qn("w:fldCharType"), "end")

    run_field = p.add_run()
    set_run_font(run_field, LATIN_BODY, EA_BODY, 9, color=GRAY)
    run_field._r.append(fld_begin)
    run_field._r.append(instr)
    run_field._r.append(fld_end)

    tail = p.add_run(" 页")
    set_run_font(tail, LATIN_BODY, EA_BODY, 9, color=GRAY)


def cover(doc):
    for _ in range(3):
        doc.add_paragraph()

    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run = p.add_run("开源小答")
    set_run_font(run, LATIN_HEAD, EA_HEAD, 34, bold=True, color=DARK_BLUE)

    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p.paragraph_format.space_after = Pt(18)
    run = p.add_run("课程知识库智能问答助手")
    set_run_font(run, LATIN_HEAD, EA_HEAD, 20, bold=True, color=RGBColor(0x2F, 0x54, 0x96))

    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p.paragraph_format.space_after = Pt(6)
    run = p.add_run("基于 LangChain 框架与检索增强生成（RAG）的智能应用")
    set_run_font(run, LATIN_BODY, EA_BODY, 12, color=GRAY)

    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p.paragraph_format.space_after = Pt(40)
    run = p.add_run("《开源软件》课程 · 第七章 智能应用开发 · 期末作业")
    set_run_font(run, LATIN_BODY, EA_BODY, 11, color=GRAY)

    info = [
        ("项目名称", "开源小答 · 课程知识库智能问答助手"),
        ("开源仓库", REPO),
        ("技术栈", "Python 3.12 · LangChain 0.3 · Streamlit · Ollama"),
        ("开源许可证", "MIT License"),
        ("文档版本", "v1.0"),
    ]
    t = doc.add_table(rows=0, cols=2)
    t.style = "Table Grid"
    t.alignment = WD_TABLE_ALIGNMENT.CENTER
    for key, value in info:
        cells = t.add_row().cells
        cells[0].width = Cm(3.6)
        cells[1].width = Cm(10.4)
        shade_cell(cells[0], "EDF2F9")
        run = cells[0].paragraphs[0].add_run(key)
        set_run_font(run, LATIN_HEAD, EA_HEAD, 10, bold=True, color=DARK_BLUE)
        run = cells[1].paragraphs[0].add_run(value)
        set_run_font(run, LATIN_BODY, EA_BODY, 10)

    doc.add_paragraph().add_run().add_break(WD_BREAK.PAGE)


def shade_cell(cell, fill):
    tcpr = cell._tc.get_or_add_tcPr()
    shd = OxmlElement("w:shd")
    shd.set(qn("w:val"), "clear")
    shd.set(qn("w:color"), "auto")
    shd.set(qn("w:fill"), fill)
    tcpr.append(shd)


# --------------------------------------------------------------------------- #
# 正文
# --------------------------------------------------------------------------- #
def build() -> Path:
    doc = Document()

    section = doc.sections[0]
    section.page_width = Cm(21)
    section.page_height = Cm(29.7)
    section.top_margin = Cm(2.4)
    section.bottom_margin = Cm(2.2)
    section.left_margin = Cm(2.4)
    section.right_margin = Cm(2.4)

    normal = doc.styles["Normal"]
    style_font(normal, LATIN_BODY, EA_BODY, 10.5)

    add_footer_page_number(section)

    cover(doc)

    # 目录
    heading(doc, "目　录", 1)
    toc_items = [
        ("一、项目简介", 3),
        ("二、功能特性", 3),
        ("三、系统架构", 4),
        ("四、技术实现", 5),
        ("五、运行与配置", 6),
        ("六、使用说明", 7),
        ("七、测试与验证", 8),
        ("八、项目目录结构", 9),
        ("九、常见问题", 9),
        ("十、许可证与致谢", 10),
    ]
    for item, page in toc_items:
        p = doc.add_paragraph()
        p.paragraph_format.space_after = Pt(6)
        p.paragraph_format.left_indent = Cm(0.8)
        p.paragraph_format.tab_stops.add_tab_stop(
            Cm(15.0), WD_TAB_ALIGNMENT.RIGHT, WD_TAB_LEADER.DOTS
        )
        run = p.add_run(item)
        set_run_font(run, LATIN_BODY, EA_BODY, 11)
        run = p.add_run(f"\t{page}")
        set_run_font(run, LATIN_BODY, EA_BODY, 11)

    # 文档说明，避免目录页过于空旷
    p = doc.add_paragraph()
    p.paragraph_format.space_before = Pt(28)
    run = p.add_run("文档说明")
    set_run_font(run, LATIN_HEAD, EA_HEAD, 10.5, bold=True, color=DARK_BLUE)
    body(
        doc,
        "本文档为智能应用「开源小答」的 README 文档说明，共 10 章，包含 1 幅系统架构图、"
        "8 张参数与配置表、5 段示例代码与命令。内容覆盖项目定位、技术实现、运行配置、"
        "使用方法与测试验证，可作为仓库 README 的完整离线版本提交。",
        space_after=4,
    )
    body(
        doc,
        "对应的开源仓库地址见封面与附录，仓库内 README.md 与本文档内容一致。"
        "若需复现文中结果，请按第五章的步骤安装依赖并启动应用；不配置 API Key 时应用默认运行在演示模式。",
        space_after=4,
    )

    doc.add_paragraph().add_run().add_break(WD_BREAK.PAGE)

    # 一、项目简介
    heading(doc, "一、项目简介", 1)
    body(
        doc,
        "「开源小答」是一款面向课程学习的智能问答助手。它把课程资料（开源许可证、Git 协作流程、"
        "LangChain 框架、检索增强生成等）作为本地知识库，用户提问时先从知识库中检索相关片段，"
        "再交由大模型基于这些片段生成回答，并在答案中标注来源。",
    )
    body(doc, "与传统“直接询问大模型”的方式相比，该应用具有三点差异：")
    bullet(doc, "答案有据可依：模型只依据检索到的资料作答，资料不足时明确说明，降低幻觉风险。")
    bullet(doc, "结果可溯源：每个回答附带来源文件名与片段编号，便于人工核对。")
    bullet(doc, "知识可更新：只需向 data/knowledge 目录放入新的 Markdown 或 TXT 文件，无需重新训练模型。")

    heading(doc, "1.1 设计目标", 2)
    table(
        doc,
        ["目标", "具体做法"],
        [
            ["可复现", "克隆仓库后无需任何 API Key 即可跑通全流程（内置演示模式）"],
            ["可切换", "同一套代码支持在线模型、本地离线模型与规则模型，只改一个环境变量"],
            ["可解释", "回答附带检索来源与片段编号，界面可展开查看原文"],
        ],
        [3.0, 12.6],
    )

    heading(doc, "1.2 应用形态", 2)
    body(
        doc,
        "应用提供两种交互形态：一是基于 Streamlit 的 Web 聊天界面，支持多轮对话、参数实时调节与命中片段查看；"
        "二是命令行工具，支持单轮提问与交互式会话，便于脚本化验证与无图形环境使用。",
    )

    # 二、功能特性
    heading(doc, "二、功能特性", 1)
    table(
        doc,
        ["功能模块", "说明"],
        [
            ["RAG 问答", "文档加载 → 递归切块 → 检索 → 提示词拼装 → 大模型生成 → 来源溯源"],
            ["三种模型模式", "demo（离线规则模型）/ openai（OpenAI 兼容接口）/ ollama（本地离线模型）"],
            ["双检索后端", "默认零依赖 TF-IDF（中文单字 + 二元组切分）；可切换向量检索"],
            ["多轮对话", "历史消息通过 MessagesPlaceholder 注入提示词，支持上下文追问"],
            ["Web 界面", "Streamlit 聊天界面，参数实时可调，命中片段可展开查看"],
            ["命令行", "单轮提问与交互式会话，适合脚本化与快速验证"],
            ["可测试", "演示模型使端到端链路可在无网络环境下被 pytest 覆盖"],
        ],
        [3.2, 12.4],
    )

    # 三、系统架构
    heading(doc, "三、系统架构", 1)
    heading(doc, "3.1 总体架构", 2)
    body(
        doc,
        "系统自上而下分为四层：交互层（Web 界面与命令行）、编排层（LCEL 问答链）、能力层（模型接入与检索）、"
        "配置层（.env 解析）。依赖方向单向，交互层不直接接触模型 SDK，替换模型或检索实现不影响界面。",
    )
    doc.add_picture(str(ARCH), width=Cm(15.6))
    doc.paragraphs[-1].alignment = WD_ALIGN_PARAGRAPH.CENTER
    caption(doc, "图 1　系统总体架构与请求流转路径")

    heading(doc, "3.2 核心问答链", 2)
    body(
        doc,
        "问答流程使用 LangChain 表达式语言（LCEL）组合为一个 Runnable，逐级追加字段而不覆盖原始输入，"
        "因此调试时可以直接打印任一阶段的中间结果。",
    )
    code_block(
        doc,
        """chain = (
    RunnablePassthrough.assign(documents=retrieve)
    | RunnablePassthrough.assign(context=format_documents)
    | RunnablePassthrough.assign(answer=prompt | llm | StrOutputParser())
    | RunnableLambda(lambda x: Answer(text=x["answer"], sources=x["documents"]))
)
answer = chain.invoke({"question": "GPL 和 MIT 有什么区别？", "history": []})""",
    )

    heading(doc, "3.3 数据传递", 2)
    body(
        doc,
        "链的输入是一个字典，随流程依次增加 documents（检索结果）、context（拼装后的参考资料）、"
        "answer（模型回答）三个字段，最后转换为 Answer 数据类，携带答案文本与来源文档列表返回给交互层。",
    )

    # 四、技术实现
    heading(doc, "四、技术实现", 1)
    heading(doc, "4.1 文档加载与切块", 2)
    body(
        doc,
        "使用 RecursiveCharacterTextSplitter 按“段落 → 换行 → 句号 → 逗号”的优先级递归切分，"
        "默认块大小 500 字、重叠 80 字。每个片段保留来源文件名与块序号，写入 metadata，供回答时溯源。",
    )

    heading(doc, "4.2 中文检索", 2)
    body(
        doc,
        "默认检索器为纯 Python 实现的 TF-IDF 余弦相似度，不依赖任何 embedding 模型，因此完全离线可用。"
        "针对中文，分词采用“单字 + 相邻二元组”策略：",
    )
    bullet(doc, "英文与数字按词整体切分，例如 langchain、3.12。")
    bullet(doc, "中文连续字符先按单字切分，再补充相邻二元组，使“开源许可证”能命中“许可证”等子串。")
    bullet(doc, "IDF 由语料统计得出，查询与片段分别计算 TF-IDF 向量后取余弦相似度排序。")
    body(
        doc,
        "当配置了 API Key 并开启 SMARTQA_USE_EMBEDDINGS 时，检索后端切换为 InMemoryVectorStore + "
        "embedding 接口，接口签名保持一致，上层代码无需修改。",
    )

    heading(doc, "4.3 提示词设计", 2)
    table(
        doc,
        ["规则", "作用"],
        [
            ["只依据参考资料作答", "把模型的自由度约束在检索结果内，抑制幻觉"],
            ["资料不足时明确说明", "避免模型用常识“补全”，提高可信度"],
            ["先结论后要点", "符合教学场景的阅读习惯，便于快速抓取重点"],
            ["标注来源编号", "支持人工核对，也为后续评估提供依据"],
        ],
        [5.0, 10.6],
    )

    heading(doc, "4.4 三种模型接入", 2)
    table(
        doc,
        ["模式", "实现类", "特点", "适用场景"],
        [
            ["demo", "DemoChatModel", "规则抽取，零依赖、无网络", "本地自检、单元测试、无 Key 演示"],
            ["openai", "ChatOpenAI", "自定义 base_url，兼容多家厂商", "DeepSeek / 通义 / Kimi / OpenAI"],
            ["ollama", "ChatOllama", "本地量化模型，数据不出本机", "完全离线、隐私敏感场景"],
        ],
        [2.2, 3.4, 5.0, 5.0],
    )
    body(
        doc,
        "三种模式共享同一条链、同一套提示词与同一个检索器，因此切换模型不会改变应用行为，"
        "这也使得自动化测试可以在无网络环境下覆盖完整链路。",
    )

    heading(doc, "4.5 多轮对话", 2)
    body(
        doc,
        "LangChain 0.3 推荐由应用层管理消息历史。界面把每轮的用户消息与模型消息存入会话状态，"
        "提问时整体装入 MessagesPlaceholder，既保留上下文，又便于在界面上清空或截断历史。",
    )

    # 五、运行与配置
    heading(doc, "五、运行与配置", 1)
    heading(doc, "5.1 环境要求", 2)
    table(
        doc,
        ["项目", "要求"],
        [["Python", "3.10 及以上（本项目在 3.12 验证）"], ["操作系统", "Windows / macOS / Linux"], ["硬件", "无需 GPU；演示模式完全离线"]],
        [4.0, 11.6],
    )

    heading(doc, "5.2 安装", 2)
    code_block(
        doc,
        """git clone https://github.com/Yanghanrui666/opensource-homework.git smartqa
cd smartqa

python -m venv .venv
.venv\\Scripts\\activate          # Windows
source .venv/bin/activate        # macOS / Linux

pip install -r requirements.txt""",
    )

    heading(doc, "5.3 配置项", 2)
    table(
        doc,
        ["环境变量", "默认值", "说明"],
        [
            ["SMARTQA_PROVIDER", "demo", "模型提供方：demo / openai / ollama"],
            ["SMARTQA_MODEL", "deepseek-chat", "模型名称"],
            ["SMARTQA_BASE_URL", "https://api.deepseek.com/v1", "OpenAI 兼容接口或 Ollama 地址"],
            ["SMARTQA_API_KEY", "（空）", "在线模式必填；不会写入仓库"],
            ["SMARTQA_TEMPERATURE", "0.2", "生成温度，越低越稳定"],
            ["SMARTQA_TOP_K", "4", "每次检索的片段数"],
            ["SMARTQA_KNOWLEDGE_DIR", "./data/knowledge", "知识库目录"],
            ["SMARTQA_USE_EMBEDDINGS", "false", "是否启用向量检索"],
        ],
        [5.4, 4.6, 5.6],
        keep_together=False,
    )

    heading(doc, "5.4 启动", 2)
    code_block(
        doc,
        """# Web 界面
streamlit run app.py

# 命令行：单轮问答
python -m smartqa.cli -q "GPL 和 MIT 许可证有什么区别？"

# 命令行：交互式多轮会话
python -m smartqa.cli -i --show-sources""",
    )

    # 六、使用说明
    heading(doc, "六、使用说明", 1)
    heading(doc, "6.1 Web 界面", 2)
    body(
        doc,
        "浏览器打开终端提示的地址（默认 http://localhost:8501）。左侧栏可切换模型提供方、填写 API Key、"
        "调节温度与检索片段数、指定知识库目录；主区域为对话窗口，回答下方的“参考资料”折叠面板可展开查看命中的原文片段。",
    )

    heading(doc, "6.2 命令行示例", 2)
    body(doc, "在演示模式下执行一条真实提问，实际输出如下（节选）：")
    code_block(
        doc,
        """$ python -m smartqa.cli -q "GPL 和 MIT 许可证有什么区别？" --show-sources
模型：演示模式（无需网络，规则模型） | 知识片段：12

（演示模式回答）关于「GPL 和 MIT 许可证有什么区别？」，知识库中的相关信息如下：

- **许可证兼容性**：把 GPL 代码并入 MIT 项目会迫使整个项目遵循 GPL；
- | MIT | 宽松 | 是 | 否 | 是 |
- | LGPL-3.0 | 弱 copyleft | 是 | 动态链接可闭源 | 是 |

--- 参考来源 ---
  · 01-开源许可证.md #0
  · 01-开源许可证.md #1
  · 02-Git与协作流程.md #3""",
    )
    body(
        doc,
        "演示模式的回答由规则模型根据检索结果整理，用于验证“检索 → 提示词 → 解析”整条链路；"
        "配置真实模型后，同样的命令会返回大模型生成的完整回答。",
    )

    # 七、测试与验证
    heading(doc, "七、测试与验证", 1)
    body(
        doc,
        "测试全部使用演示模型，不依赖网络与 API Key，可直接在 CI 中运行。执行 pytest 即可复现下表结果。",
    )
    table(
        doc,
        ["测试范围", "覆盖内容", "数量"],
        [
            ["配置解析", "默认值、环境变量覆盖、非法值回落、不可变替换", "4"],
            ["检索层", "中文分词、文档加载、切块元数据、TF-IDF 排序、空库与无重叠兜底", "7"],
            ["问答链", "模型构造、缺 Key 校验、索引构建、回答与来源、多轮历史、空问题校验", "8"],
            ["合计", "全部通过（pytest，19 passed）", "19"],
        ],
        [3.2, 10.4, 2.0],
    )
    body(
        doc,
        "除自动化测试外，还进行了两项手工验证：其一，在无网络环境启动 Streamlit 服务，确认首页返回 200 且健康检查为 ok；"
        "其二，在命令行执行真实提问，确认回答内容与来源标注正确。",
    )

    # 八、目录结构
    heading(doc, "八、项目目录结构", 1)
    code_block(
        doc,
        """.
├── app.py                     # Streamlit Web 界面
├── src/smartqa/
│   ├── __init__.py            # 公开 API
│   ├── config.py              # .env 配置解析
│   ├── llm.py                 # 三种模型接入 + 演示模型
│   ├── retriever.py           # 文档加载、切块、TF-IDF / 向量检索
│   ├── chain.py               # 提示词与 LCEL 问答链
│   └── cli.py                 # 命令行入口
├── data/knowledge/            # 知识库（4 篇课程资料）
├── tests/                     # pytest 单元与端到端测试
├── docs/architecture.md       # 架构说明
├── requirements.txt           # 运行依赖
├── pyproject.toml             # 包元数据与 pytest 配置
├── .env.example               # 配置模板
└── LICENSE                    # MIT""",
    )

    # 九、常见问题
    heading(doc, "九、常见问题", 1)
    faq = [
        ("启动报 API Key 相关错误？", "在线模式必须设置 SMARTQA_API_KEY；若只想先看效果，把 SMARTQA_PROVIDER 改回 demo。"),
        ("Ollama 连接失败？", "确认 ollama serve 正在运行，SMARTQA_BASE_URL 与端口一致（默认 11434），且模型已 pull。"),
        ("回答提示“资料中没有找到相关内容”？", "说明检索未命中。可换用文档中的术语提问、调大 SMARTQA_TOP_K，或向知识库补充资料。"),
        ("如何换成自己的知识库？", "把 Markdown / TXT 文件放入 data/knowledge，或修改 SMARTQA_KNOWLEDGE_DIR，界面会自动重新索引。"),
        ("为什么默认不用向量检索？", "为了“克隆即可运行”。开启 SMARTQA_USE_EMBEDDINGS 并提供 API Key 后即切换为向量检索。"),
    ]
    for question, answer in faq:
        p = doc.add_paragraph()
        p.paragraph_format.space_before = Pt(8)
        p.paragraph_format.space_after = Pt(2)
        p.paragraph_format.keep_with_next = True
        run = p.add_run("Q：" + question)
        set_run_font(run, LATIN_HEAD, EA_HEAD, 10.5, bold=True, color=DARK_BLUE)
        p2 = doc.add_paragraph()
        p2.paragraph_format.space_after = Pt(4)
        p2.paragraph_format.line_spacing = 1.35
        run = p2.add_run("A：" + answer)
        set_run_font(run, size=10.5)

    # 十、许可证与致谢
    heading(doc, "十、许可证与致谢", 1)
    body(
        doc,
        "本项目采用 MIT License 开源，允许自由使用、修改与再分发，只需保留版权声明与许可声明。"
        "完整许可证文本见仓库根目录 LICENSE 文件。",
    )
    body(doc, "致谢以下开源项目：")
    bullet(doc, "LangChain —— 大模型应用编排框架，提供 Runnable、Prompt、Retriever 等核心抽象。")
    bullet(doc, "Streamlit —— 快速构建数据与 AI 应用界面。")
    bullet(doc, "Ollama —— 本地大模型运行时，使应用可以完全离线运行。")

    heading(doc, "附录　仓库信息", 2)
    table(
        doc,
        ["项目", "内容"],
        [
            ["开源仓库", REPO],
            ["分支", "main"],
            ["许可证", "MIT"],
            ["运行方式", "streamlit run app.py / python -m smartqa.cli"],
        ],
        [3.6, 12.0],
    )

    props = doc.core_properties
    props.title = "开源小答 · 课程知识库智能问答助手 —— README 文档说明"
    props.subject = "《开源软件》第七章 智能应用开发 期末作业"
    props.author = "Yanghanrui666"
    props.keywords = "LangChain, RAG, Streamlit, 智能问答, 开源软件"

    OUT.parent.mkdir(parents=True, exist_ok=True)
    doc.save(OUT)
    return OUT


if __name__ == "__main__":
    path = build()
    print(f"saved {path} ({path.stat().st_size} bytes)")

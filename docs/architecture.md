# 架构说明

## 分层

```
┌──────────────────────────────────────────────┐
│ 交互层  app.py (Streamlit) / cli.py (终端)     │
├──────────────────────────────────────────────┤
│ 编排层  chain.py  Assistant / LCEL RAG 链      │
├──────────────────────────────────────────────┤
│ 能力层  llm.py (模型)  retriever.py (检索)      │
├──────────────────────────────────────────────┤
│ 配置层  config.py  Settings(.env)              │
└──────────────────────────────────────────────┘
```

依赖方向自上而下单向，交互层不直接接触模型 SDK，替换模型或检索实现不影响界面。

## 数据流

1. `Settings.from_env()` 读取 `.env`，得到模型与知识库参数。
2. `build_retriever()` 加载 `data/knowledge` 下的文档，递归切块，建立 TF-IDF 索引。
3. 用户提问后，`Assistant.ask()` 触发 LCEL 链：
   - `retriever.invoke(question)` 取回 Top-K 片段；
   - `format_documents()` 把片段拼成带来源标注的参考资料块；
   - `ChatPromptTemplate` 注入系统指令、历史消息、参考资料与问题；
   - `ChatModel` 生成回答，`StrOutputParser` 取出纯文本；
   - 结果封装为 `Answer(text, sources)`，界面据此渲染引用。
4. 多轮对话由界面维护消息列表，每轮把历史消息装入 `MessagesPlaceholder`。

## LCEL 链结构

```python
RunnablePassthrough.assign(documents=retrieve)
  | RunnablePassthrough.assign(context=format)
  | RunnablePassthrough.assign(answer=prompt | llm | StrOutputParser())
  | RunnableLambda(to_answer)
```

`assign` 逐级追加字段而不覆盖原输入，因此 `question`、`history`、`documents`、`context`、`answer` 始终在同一个字典里流动，调试时可直接打印任一阶段的中间结果。

## 三种模型模式

| 模式 | 实现 | 适用场景 |
| --- | --- | --- |
| demo | `DemoChatModel`，规则抽取，无网络 | 本地自检、单元测试、无 API Key 演示 |
| openai | `ChatOpenAI` + 自定义 `base_url` | DeepSeek / 通义 / Kimi / OpenAI / vLLM |
| ollama | `ChatOllama` | 完全离线，本地量化模型 |

三种模式共享同一条链与同一套提示词，切换只需改一个环境变量。

## 检索实现取舍

默认 TF-IDF 检索是为了让项目"克隆即可运行"：不需要下载 embedding 模型，也不消耗 API 额度。
中文按单字与相邻二元组切分，能在没有分词词典的情况下获得可接受的召回率。
对精度要求高的场景，可在配置中开启 `SMARTQA_USE_EMBEDDINGS=true` 切换到向量检索（`InMemoryVectorStore`），接口保持一致。

## 可扩展点

- 新增文档格式（PDF、DOCX）：在 `retriever.load_documents` 中增加解析分支。
- 新增模型厂商：在 `llm.build_llm` 中增加 provider 分支。
- 新增界面（微信、API 服务）：复用 `Assistant.ask()`，无需改动核心链路。
- 增加重排（rerank）：在 `build_chain` 的检索步骤后插入一个 `RunnableLambda` 即可。

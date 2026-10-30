# LangChain 框架要点

## 定位

LangChain 是一个用于构建大模型应用的编排框架，把"提示词、模型、检索、工具、记忆"抽象成可组合的 Runnable 组件，使应用逻辑可以像管道一样拼接与复用。

## 核心抽象

**ChatModel**：聊天模型接口，输入消息列表，输出消息。`ChatOpenAI`、`ChatOllama` 都是它的实现。

**PromptTemplate / ChatPromptTemplate**：提示词模板，支持变量插值与多角色消息（system / human / ai）。

**OutputParser**：把模型输出解析成结构化数据，`StrOutputParser` 最常用。

**Retriever**：检索器接口，输入查询字符串，输出相关文档列表。向量库、关键词检索都实现该接口。

**Runnable**：统一的可执行协议，提供 `invoke`、`batch`、`stream` 以及同步/异步变体。

## LCEL 表达式语言

LangChain Expression Language 用管道符 `|` 组合组件：

```python
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate

prompt = ChatPromptTemplate.from_template("用一句话解释：{topic}")
chain = prompt | llm | StrOutputParser()
print(chain.invoke({"topic": "LCEL"}))
```

`RunnablePassthrough` 原样传递输入，`RunnableParallel` 并行分发，`RunnableLambda` 包装普通函数。

## 典型 RAG 链

```python
from langchain_core.runnables import RunnablePassthrough

chain = (
    RunnablePassthrough.assign(context=retriever | format_docs)
    | prompt
    | llm
    | StrOutputParser()
)
```

`assign` 在保留原输入的同时注入检索结果，这是构建检索增强问答最简洁的写法。

## 记忆与多轮对话

LangChain 0.3 推荐由应用层管理消息历史：把历史消息放进 `MessagesPlaceholder`，每轮结束后追加用户与模型消息即可，比早期的 Memory 类更透明、更易调试。

## 生态组件

- `langchain-openai`：OpenAI 及所有兼容接口
- `langchain-ollama`：本地 Ollama 模型
- `langchain-text-splitters`：文本切块
- `langchain-community`：社区集成（向量库、加载器等）

## 学习建议

先掌握 LCEL 的组合方式与 Runnable 协议，再学习检索与代理。
调试时优先打印中间结果：提示词渲染后的文本、检索到的文档、模型的原始输出。

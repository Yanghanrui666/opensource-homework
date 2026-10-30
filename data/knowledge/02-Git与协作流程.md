# Git 与开源协作流程

## 为什么用分布式版本控制

Git 每个克隆都是完整仓库，包含全部历史，因此离线也能提交、查看日志与分支。相比集中式版本控制，它没有单点故障，分支操作也几乎是常数时间。

## 常用命令

```
git init                      # 初始化仓库
git clone <url>               # 克隆远程仓库
git status                    # 查看工作区状态
git add -A                    # 暂存全部改动
git commit -m "feat: ..."     # 提交
git log --oneline --graph     # 查看历史
git switch -c feature/login   # 新建并切换分支
git push -u origin feature/login
git pull --rebase origin main
```

## 分支模型

主流做法是主干开发：`main` 始终保持可发布状态，功能在短生命周期分支上完成，通过 Pull Request 合并。
分支命名建议 `<类型>/<简短描述>`，例如 `feat/rag-retriever`、`fix/empty-kb`、`docs/readme`。

## 提交信息规范

采用 Conventional Commits：

- `feat:` 新功能
- `fix:` 缺陷修复
- `docs:` 文档变更
- `refactor:` 重构（不改变行为）
- `test:` 测试相关
- `chore:` 构建、依赖、配置

一条提交只做一件事，标题不超过 50 个字符，正文说明"为什么"而不是"做了什么"。

## Pull Request 与代码审查

1. 从最新 `main` 切出功能分支。
2. 提交前本地运行测试与格式化工具。
3. 推送分支并创建 PR，描述中写清动机、改动点与验证方式。
4. 至少一位维护者审查通过后合并，优先使用 squash merge 保持历史整洁。

代码审查关注：正确性、边界条件、可读性、测试覆盖、是否引入不必要的依赖、是否有敏感信息泄露。

## 忽略文件

`.gitignore` 用于排除虚拟环境、缓存、日志与 `.env` 等本地文件。
**切勿提交任何 API Key、令牌或私钥**；一旦提交，即使后续删除，历史记录中仍然存在，需要立即吊销并轮换密钥。

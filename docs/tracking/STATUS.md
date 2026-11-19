# Agent-Workflow-Kit 当前状态

## 接入盘点 · 2026-11-19

接入前，main 与已知 origin/main 同在 baaf366，工作区干净。远端为 lslalalatry/Agent-Workflow-Kit。

使用者从 README.md、使用指南.html 或已安装的 skills/project-guardian/SKILL.md 进入。初始化入口是 skills/project-guardian/scripts/init_project.py。两端安装入口是 scripts/sync_global.py。

接入盘点未发现数据库文件或持久化业务服务。

- **初始化实测**：2026-11-19T13:39:57+08:00 · 通过（仓库结构、分支、存储和追踪文档）  <!-- guardian-init -->

## 断点接力锚点

D-001 已同步到决策、产品说明与交付待办。本轮用临时仓库运行 11 项回归，覆盖实际提交和向本地裸仓库推送。

下轮修改先看本轮提交及工作区差异。运行 python3 -B -m unittest discover -s tests -v 核对提交和推送行为。

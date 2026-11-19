# Agent-Workflow-Kit 产品说明

## 现有入口与数据

使用者从 README.md、使用指南.html 或已安装的 skills/project-guardian/SKILL.md 进入。初始化入口是 skills/project-guardian/scripts/init_project.py。两端安装入口是 scripts/sync_global.py。

接入盘点未发现数据库文件或持久化业务服务。

## 提交与上传的验收条件

D-001 要求 AI 实读本次差异，核对重复实现、复杂分支、依赖与回归风险。阻断问题必须修复并复审。提交时核对最终暂存内容。推送时逐项核对将上传的提交。同一差异沿用本地审查记录。

实现复用已有 Git 钩子、Git 快照与本地记录的原子写入工具。审阅方法借鉴 ECC 的差异审查与具体问题分级。2026-11-19 查询时仓库有 306,702 星，审阅器在 2026-07-26 修复了工具声明格式。[审阅器来源](https://github.com/affaan-m/ECC/blob/6a9f075cd97c139a5f7e84e1e3f2c9ab095adf64/agents/code-reviewer.md)

## 老项目升级入口

D-002 要求 README 提供可直接复制的升级口令。离线指南提供同名独立场景，复制的内容与 README 一致。

# Agent-Workflow-Kit 产品说明

## 现有入口与数据

使用者从 README.md、使用指南.html 或已安装的 skills/project-guardian/SKILL.md 进入。初始化入口是 skills/project-guardian/scripts/init_project.py。两端安装入口是 scripts/sync_global.py。

接入盘点未发现数据库文件或持久化业务服务。

## 提交与上传的验收条件

D-001 要求 AI 实读本次差异，核对重复实现、复杂分支、依赖与回归风险。阻断问题必须修复并复审。提交时核对最终暂存内容。推送时逐项核对将上传的提交。同一差异沿用本地审查记录。

实现复用已有 Git 钩子、Git 快照与本地记录的原子写入工具。审阅方法借鉴 ECC 的差异审查与具体问题分级。2026-11-19 查询时仓库有 306,702 星，审阅器在 2026-07-26 修复了工具声明格式。[审阅器来源](https://github.com/affaan-m/ECC/blob/6a9f075cd97c139a5f7e84e1e3f2c9ab095adf64/agents/code-reviewer.md)

## 老项目升级入口

D-002 要求 README 提供可直接复制的升级口令。离线指南提供同名独立场景，复制的内容与 README 一致。

## 按需红队与日常快车道

D-003 要求默认关闭双盲红队平行挑刺。新项目首次立项与日常迭代均禁止自动派发红队子任务，仅当用户当轮明确要求红队、辩论或挑刺审查时才执行 `02-dual-redteam-audit.md`。范围明确的常规功能修改跳过阶段 1 至阶段 3 仪式，直接实读实测并更新受影响追踪文档。

## 跨学科理论白皮书与常驻规则分离

D-004 新增独立离线文档 `docs/THEORETICAL_FOUNDATIONS.md`，以「学术理论原名与出处 + 生活化直白解释」双轨结构沉淀脱敏双领域实证样本、七大跨学科理论与工程机制映射表。`README.md` 提供导读链接，常驻 `AGENTS.md` 与 `SKILL.md` 不混入理论长文。

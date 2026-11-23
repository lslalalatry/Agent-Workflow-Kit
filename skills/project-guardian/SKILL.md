---
name: project-guardian
description: >-
  仅当用户明确点名 project-guardian、要求初始化项目治理或执行双盲红队审查时使用；普通代码修改、技能优化或日常问答禁止主动调用。
  Explicit-invocation project governance workflow (ASD-STE tracking docs, dual red-team specification audit, single-trunk Git & storage guardrails). Use ONLY for explicit project-guardian, governance initialization, or dual red-team audit requests; NEVER invoke proactively on ordinary coding, skill optimization, debugging, or Q&A.
---

# Project Guardian — 通用项目一致性与追踪文档工作流

本 Skill 为软件、数据、AI 管线或混合工程项目提供按需启用的生命周期管控。**仅当用户明确点名 `project-guardian`、要求初始化项目治理或当轮明确要求执行双盲红队审查时使用（或当前仓库 `AGENTS.md` 明确要求运行对应门禁脚本时按需调用）；普通代码修改、技能优化、范围明确的常规功能迭代或日常问答禁止主动启动立项访谈与红队辩论仪式。**

---

准备提交或上传时，先按[AI 代码审查](./references/07-code-review.md)实读本次差异，修复阻断问题并登记对应版本。推送时复用已经核对的记录。

收到用户拍板、在旧对话继续动手或准备 Git 交接时，先读[多对话决策与交接](./references/06-shared-decisions.md)。收到拍板的对话在本轮同步所有受影响文档。多对话项目初始化时使用 `--with-decisions`。

## 一、核心工具脚本（零第三方依赖，Python 3 标准库）

1. **一键初始化项目骨架与自动安检闸机**：
   ```bash
   python3 "<本Skill目录>/scripts/init_project.py" "<目标项目根目录>" [--minimal | --with-formula] [--with-decisions]
   ```
   - 自动创建或补齐根目录 `AGENTS.md` 与 `docs/tracking/` 追踪文档（默认绝不覆盖已有文件）；
   - 若尚未初始化 Git，自动初始化单主线 `main`；
   - 安装 Git 提交与推送检查，实际检查初始状态，将通过或失败原因写回 STATUS.md。

2. **手动运行自动安检闸机（收尾提交前必跑）**：
   ```bash
   python3 "<本Skill目录>/scripts/verify_guardrails.py" --root "<目标项目根目录>"
   ```
   - 核查项：① 本地是否仅剩唯一主分支（无悬空 `exp/*` 残留分支）；② 是否存在未在 `AGENTS.md` 白名单登记的数据库或超大副本；③ 代码变更是否同步更新了 `STATUS.md`；④ `AGENTS.md <= 20KB` 且 `STATUS.md <= 100` 行，且无带日期后缀的重复追踪文档。

---

## 二、按阶段渐进式披露路由（仅读取当前所处阶段的手册）

| 所处生命周期阶段 | 必读参考手册 | 阶段产出与通关条件 |
| :--- | :--- | :--- |
| **Phase 1 · 需求挖掘与公式锁死** | [01-discovery-and-formula.md](./references/01-discovery-and-formula.md) | **仅新项目立项或边界未定的跨模块大改执行**（常规明确功能跳过本步直达 Phase 4）：先盘点现有能力并调研高星且近期实质更新的 GitHub 项目，带着取舍逐题单问；技术权衡必须用**生活化比喻**解释；生成 `SPEC.md` 初稿，含计算项目同步生成 `FORMULA.md` |
| **Phase 2 · 双盲红队对抗挑刺（仅点名触发）** | [02-dual-redteam-audit.md](./references/02-dual-redteam-audit.md) | **默认关闭（连新项目立项也不自动运行）**。仅当用户当轮明确开口要求红队、辩论或挑刺时，派发 2 个零历史上下文的独立审查子任务，合并真漏洞交用户拍板 |
| **Phase 3 · 追踪文档拆解与受控写作** | [03-bilingual-ste-rules.md](./references/03-bilingual-ste-rules.md) | 用中英双语 ASD-STE 法则生成/更新 `STATUS.md`（`<=100` 行）、`TODO.md`（2–5 分钟微任务，`[ ]/[~]/[x]` 三态）与 `BACKLOG.md` |
| **Phase 4 & 5 · 微步执行、隔离与收口** | [04-isolation-and-continuity.md](./references/04-isolation-and-continuity.md) | 单主线 `main`（`exp/*` 当轮必收口）、数据库/大资产零全量克隆、每步刷新 `STATUS.md` 断点接力锚点、通过 `verify_guardrails.py` 闸机提交 |

---

默认入口与公式样例的配置、实测命令和证据格式见 [验收手册](./references/05-acceptance.md)。配置公式、勾选任务或里程碑前读取。

## 三、面向非技术用户（小白友好）与长任务的五条硬约束

1. **禁止抛黑话**：凡需要用户拍板的技术选项，必须先打生活化比方（如装修工地、账本对账、流水线安检门），讲清选 A / 选 B 的实际业务后果，并把推荐项放第一位。
2. **禁止擅自加戏（YAGNI）**：用户未要求的额外功能、站内重绘/计费闭环或更换外部执行引擎，严禁自行脑补添加。
3. **禁止假勾选**：离线草稿、局部单测通过或未在正式默认入口验证的任务，最高只能标 `[~]`（候选待验），绝对禁止标 `[x]`。
4. **禁止把不可验证当通过**：测试与巡检结果必须区分 `pass`、`fail`、`unverifiable`；无条件验证的维度必须如实标出限制。
5. **禁止绕过闸机**：未经用户当轮明确书面要求，严禁执行 `git commit --no-verify` 或删除 `.git/hooks/pre-commit`。

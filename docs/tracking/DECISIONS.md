# Agent-Workflow-Kit 决策记录

## D-001 · 2026-11-19 · 生效

用户要求 AI 在提交和上传前审查待交付改动。修复阻断项后复审。上传时可复用匹配的记录。新接入项目通过初始化安装两个 Git 钩子。

<!-- guardian-decision D-001 affects=BACKLOG.md,SPEC.md,STATUS.md,TODO.md -->

## D-002 · 2026-11-19 · 生效

README 和离线使用指南分别列出首次接入和已接入项目升级。两处采用同一句升级口令，落实 D-001 的两项本地检查。

<!-- guardian-decision D-002 affects=SPEC.md,STATUS.md -->

## D-003 · 2026-11-23 · 生效

用户要求将双盲红队平行挑刺改为纯手动点名触发。新项目首次立项与日常功能迭代均禁止自动运行红队辩论，仅当用户当轮明确开口要求红队、辩论或挑刺时才调用。范围明确的常规功能修改直接快改快验并同步受影响文档，禁止启动繁琐立项仪式。改动同步至本机双端全局目录与 GitHub 远端。

<!-- guardian-decision D-003 affects=BACKLOG.md,SPEC.md,STATUS.md -->

## D-004 · 2026-11-24 · 生效

用户批准采用「学术理论原名与出处 + 生活化直白解释」双轨写法，将两类长周期项目的脱敏实证病灶与七大跨学科理论溯源写入独立离线白皮书 `docs/THEORETICAL_FOUNDATIONS.md`，在 `README.md` 增加导读入口并保持常驻 `AGENTS.md` 与 `SKILL.md` 零膨胀，同步推送至 GitHub 远端。

<!-- guardian-decision D-004 affects=BACKLOG.md,SPEC.md,STATUS.md -->

## D-005 · 2026-11-26 · 生效

用户参考外部模块化项目框架，要求将 `project-guardian` 升级为通用架构治理技能：每次新项目或重大架构启动前，支持先盘点已有数据库与基础设施并落盘完整通用架构蓝图（集中存储、图片对象存储、数据模型、权限与凭据、接口与 UI 多态清单、`DRAFT.md` 草稿缓冲区、QA 部署与回滚），新增 `--with-architecture` 与 `references/01a-architecture-blueprint.md`，并同步至双端全局技能目录。

<!-- guardian-decision D-005 affects=BACKLOG.md,SPEC.md,STATUS.md -->

## D-006 · 2026-11-26 · 生效

用户确认两项主线闭环与范围治理策略：1）新增 `delivery_mode` 配置项及 `--auto-push` 初始化选项（`auto_push_main_when_clean` 在测试全绿、代码审查、安检闸机与无冲突 `rebase` 全部通过后自动提交推送 `main`；默认 `prompt_push_on_done` 在结尾输出强提醒卡），并在子模块完结推平后主动提示“可以新开对话框”；2）一子模块一卡（`modules/_TEMPLATE.md`），临近收尾时的新功能需求默认先登记入 `DRAFT.md / BACKLOG.md` 待当前推完 `main` 后新开窗口处理，减功能按四步软下线清理代码、保留只读历史并登记决策。同步全局规则、模板、指南并推送 GitHub。

<!-- guardian-decision D-006 affects=BACKLOG.md,SPEC.md,STATUS.md -->

## D-007 · 2026-11-26 · 生效

用户批准结合 `GoogleChrome/modern-web-guidance-src` 设计思想同时落地四项强化：1）新增 `tests/test_coherence.py`，机械回归校验 `project-template` 与打包副本一致、`init_project.py` 全量 CLI 开关在 `SKILL.md` 文档齐全以及全仓内部 Markdown 相对链接无死链；2）`SPEC.md` 术语表增加 `代码/表落点（Reference）` 列，模块设计卡与 `API_AND_UI_STATES.md` 升级为带正常+反例的原子验收断言（`Expectations`），并在 `06-shared-decisions.md` 与 `07-code-review.md` 严禁凭长对话压缩记忆猜测约束/阈值、强制逐字核对 `D-编号`/`F-编号` 原文；3）在 `API_AND_UI_STATES.md` 与 `01a-architecture-blueprint.md` 增加 `Browser Baseline`（默认 `Baseline Widely Available`）策略位及 `modern-web-guidance`（`search -> retrieve`）原生前端协同指引；4）新增零第三方依赖脚本 `skills/project-guardian/scripts/query_docs.py`（`search` 紧凑索引 + `read` 章节/行号分段读取），供多模块大项目渐进式按需查询。

<!-- guardian-decision D-007 affects=BACKLOG.md,SPEC.md,STATUS.md -->

## D-008 · 2026-11-26 · 生效

用户选择方案 A，批准将 `project-guardian` 深度嵌入原生 `/swarm` 模式：1）新增按需触发手册 `skills/project-guardian/references/08-swarm-orchestration.md`（仅用户开启 `/swarm` 或已在 Swarm 会话中时按需读取，严禁擅自启动 Swarm），规定 Coordinator 独占修改 `docs/tracking/` 总账本并同步 `swarm_pane` 计划、Author 在 `workspace:"share"` 的 `swarm/<worker>` 分片分支开发并只更新各自 `modules/*.md`、合回清理后再由独立 `verifier` 完成审查验收；2）升级 `verify_guardrails.py`（新增 `--swarm-active` 与次级 git worktree 识别）：施工期在 `swarm/*` 分片或次级 worktree 内放行临时分支并豁免总账本同步拦截（存储零克隆仍严格强制），而在 `main` 收口提交时恢复零残留唯一主干强制拦截；3）打通 `02-dual-redteam-audit.md` 在 `/swarm` 下无 `fork` 盲审并在 `README.md` 与 `使用指南.html` 提供 `/swarm` 场景模板，配套 `tests/test_coherence.py` 多 worktree 生命周期回归测试。

<!-- guardian-decision D-008 affects=BACKLOG.md,SPEC.md,STATUS.md -->

## D-009 · 2026-11-26 · 生效 · 补充 D-008

用户确认采用方案 1 并新增「轻度 / 中度 / 深度任务」分级判定实现 `/swarm` 与 `project-guardian` 的自动感应联动：1）已在项目根目录接入 `AGENTS.md` 与 `docs/tracking/` 的仓库，启动 `/swarm` 时 Coordinator 自动读取 `08-swarm-orchestration.md` 按单写者总账本与 `swarm/<worker>` 分片规程执行，无需用户重复点名 `project-guardian`；2）未接入过的新/老项目开启 `/swarm` 时，在 `COLLABORATION_PRINCIPLES.md` 第 14 条依据任务分级（轻度任务：直跑原生 Swarm 不建档案；中度任务：`--with-decisions` 轻量防撞；深度任务：`--with-architecture --with-decisions` 含公式全套）自动判定或先用一句话确认后再建档开工；同步更新 `project-template/AGENTS.md` 第 5 节、`SKILL.md`、`08-swarm-orchestration.md`、`README.md` 与 `使用指南.html`。

<!-- guardian-decision D-009 affects=BACKLOG.md,SPEC.md,STATUS.md -->

## D-010 · 2026-11-26 · 生效

用户批准在推送前同步补齐三项 P1 优化并与 D-008、D-009 一并审查推送至 GitHub：1）`verify_guardrails.py` 在 `main` 正式收口（非 `--swarm-active` 且非次级 worktree）时将残留多余 `git worktree`（含游离态）升级为 `[残留 Worktree 拦截]` 硬阻断；2）`scripts/sync_global.py` 为 Antigravity 全局 `AGENTS.md` 补齐同款每日日期备份并新增 `--dry-run` 预览开关；3）`query_docs.py` 新增 `modules` 模块卡总表子命令（输出状态、已勾/总断言数与关联编号）及 `search --any` OR 宽松匹配，配套补充 `test_coherence.py` 回归覆盖。

<!-- guardian-decision D-010 affects=BACKLOG.md,SPEC.md,STATUS.md -->

## D-011 · 2026-11-27 · 生效

用户批准将 `project-guardian` 与 Orca 跨平台 6 岗 Bots（主理人、牛马 1 号-codex、牛马 2 号-antigravity、PR 评审、复盘沉淀官、工作区清理）深度打通：1）直接为本机 `~/.orca/bots/` 全部 6 个 Bot 写入协同 `SOUL.md`（主理人规划与总账合一、Codex/Antigravity 隔离写码禁碰总账、PR 评审异构只读盲审、复盘沉淀官事后异步沉淀 `AGENTS.md` 与 `DESIGN.md`、工作区清理定期卫生）；2）放宽 `verify_guardrails.py` 对任意次级 git worktree 分支名的施工期兼容（主分支收口时仍严格零残留拦截）并补充 Orca worktree 回归测试；3）在 `project-template/docs/architecture/` 新增机器可读 UI 复刻模板 `DESIGN.md` 并双端安装 `anthropics/skills` 的 `frontend-design`。

<!-- guardian-decision D-011 affects=BACKLOG.md,SPEC.md,STATUS.md -->

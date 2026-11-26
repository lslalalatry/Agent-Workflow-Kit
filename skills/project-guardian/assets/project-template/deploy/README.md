# 部署与运维目录（deploy）

本目录集中存放项目的容器编排、环境配置模板、发布检查与一键回滚脚本，与业务源码及文档解耦。

## 推荐文件清单

- `compose.yaml`：生产/测试标准服务编排（明确容器内存/CPU 上限与健康检查）
- `.env.example`：环境变量契约模板（**严禁填入任何真实密钥或线上密码**）
- `scripts/deploy_app.sh`：应用版本构建、幂等发布与 `--rollback` 回滚脚本
- `scripts/backup_and_restore_check.sh`：数据库逻辑/物理备份及无网络隔离还原校验脚本

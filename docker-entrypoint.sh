#!/bin/sh
# 容器启动前确保运行时数据文件存在（不覆盖已有数据）

[ -f /app/config.json ]      || echo '{}'                                      > /app/config.json
[ -f /app/projects.json ]    || echo '{"projects":{},"active_project":""}'     > /app/projects.json
[ -f /app/xp_presets.json ]  || echo '[]'                                      > /app/xp_presets.json

mkdir -p /app/output /app/styles /app/prompts

exec "$@"

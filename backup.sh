#!/bin/bash
# 生产数据库备份脚本
# 用法：./backup.sh
# 备份文件存放在 /opt/SV_Space/backups/

set -e

BACKUP_DIR="/opt/SV_Space/backups"
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
BACKUP_FILE="$BACKUP_DIR/db_$TIMESTAMP.sql.gz"

mkdir -p "$BACKUP_DIR"

echo "📦 备份数据库..."
docker exec postgres pg_dump -U platform tool_platform | gzip > "$BACKUP_FILE"

SIZE=$(du -sh "$BACKUP_FILE" | cut -f1)
echo "✅ 备份完成：$BACKUP_FILE ($SIZE)"

# 只保留最近 10 份，自动清理旧备份
ls -t "$BACKUP_DIR"/db_*.sql.gz | tail -n +11 | xargs -r rm -f
echo "🗑️  旧备份已清理，当前保留 $(ls $BACKUP_DIR/db_*.sql.gz | wc -l) 份"

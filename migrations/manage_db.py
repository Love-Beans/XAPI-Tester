#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
数据库迁移管理脚本
使用 Alembic 管理数据库结构变更
"""

import os
import sys
import subprocess
from pathlib import Path

# 添加项目根目录到 Python 路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Alembic 可执行文件路径
ALEMBIC_PATH = "/Users/xm/Library/Python/3.7/bin/alembic"

def run_alembic_command(command_args):
    """运行 Alembic 命令"""
    cmd = [ALEMBIC_PATH] + command_args
    try:
        result = subprocess.run(cmd, cwd=project_root, capture_output=True, text=True)
        if result.returncode == 0:
            print("✅ 命令执行成功:")
            print(result.stdout)
        else:
            print("❌ 命令执行失败:")
            print(result.stderr)
        return result.returncode == 0
    except Exception as e:
        print(f"❌ 执行命令时发生错误: {e}")
        return False

def create_migration(message):
    """创建新的迁移文件"""
    print(f"🔄 创建迁移: {message}")
    return run_alembic_command(["revision", "--autogenerate", "-m", message])

def upgrade_database(revision="head"):
    """升级数据库到指定版本"""
    print(f"🔄 升级数据库到: {revision}")
    return run_alembic_command(["upgrade", revision])

def downgrade_database(revision):
    """降级数据库到指定版本"""
    print(f"🔄 降级数据库到: {revision}")
    return run_alembic_command(["downgrade", revision])

def show_current_revision():
    """显示当前数据库版本"""
    print("📋 当前数据库版本:")
    return run_alembic_command(["current"])

def show_history():
    """显示迁移历史"""
    print("📋 迁移历史:")
    return run_alembic_command(["history"])

def stamp_database(revision):
    """标记数据库版本（不执行迁移）"""
    print(f"🏷️  标记数据库版本为: {revision}")
    return run_alembic_command(["stamp", revision])

def main():
    """主函数"""
    if len(sys.argv) < 2:
        print("使用方法:")
        print("  python manage_db.py create <message>     # 创建新迁移")
        print("  python manage_db.py upgrade [revision]   # 升级数据库")
        print("  python manage_db.py downgrade <revision> # 降级数据库")
        print("  python manage_db.py current              # 显示当前版本")
        print("  python manage_db.py history              # 显示迁移历史")
        print("  python manage_db.py stamp <revision>     # 标记数据库版本")
        return
    
    command = sys.argv[1]
    
    if command == "create":
        if len(sys.argv) < 3:
            print("❌ 请提供迁移消息")
            return
        message = " ".join(sys.argv[2:])
        create_migration(message)
    
    elif command == "upgrade":
        revision = sys.argv[2] if len(sys.argv) > 2 else "head"
        upgrade_database(revision)
    
    elif command == "downgrade":
        if len(sys.argv) < 3:
            print("❌ 请提供目标版本")
            return
        revision = sys.argv[2]
        downgrade_database(revision)
    
    elif command == "current":
        show_current_revision()
    
    elif command == "history":
        show_history()
    
    elif command == "stamp":
        if len(sys.argv) < 3:
            print("❌ 请提供版本号")
            return
        revision = sys.argv[2]
        stamp_database(revision)
    
    else:
        print(f"❌ 未知命令: {command}")

if __name__ == "__main__":
    main()
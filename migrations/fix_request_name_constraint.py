#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
修复 request_name 唯一约束的专用脚本
由于 SQLite 的限制，需要重建表来移除唯一约束
"""

import sqlite3
import os
import sys
from pathlib import Path

# 添加项目根目录到 Python 路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

DB_PATH = os.path.join(project_root, "api_tester.db")

def backup_database():
    """备份数据库"""
    backup_path = f"{DB_PATH}.backup"
    try:
        import shutil
        shutil.copy2(DB_PATH, backup_path)
        print(f"✅ 数据库已备份到: {backup_path}")
        return True
    except Exception as e:
        print(f"❌ 备份失败: {e}")
        return False

def fix_request_name_constraint():
    """修复 request_name 的唯一约束"""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        print("🔄 开始修复 request_name 唯一约束...")
        
        # 1. 创建新的 request_info 表（没有唯一约束）
        cursor.execute("""
        CREATE TABLE request_info_new (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT NOT NULL,
            url TEXT NOT NULL,
            method TEXT NOT NULL,
            headers TEXT,
            body TEXT,
            query TEXT,
            auth TEXT,
            request_name TEXT,
            is_deleted INTEGER DEFAULT 0
        )
        """)
        
        # 2. 复制数据到新表
        cursor.execute("""
        INSERT INTO request_info_new 
        (id, timestamp, url, method, headers, body, query, auth, request_name, is_deleted)
        SELECT id, timestamp, url, method, headers, body, query, auth, request_name, 
               CASE WHEN is_deleted IS NULL THEN 0 ELSE is_deleted END
        FROM request_info
        """)
        
        # 3. 删除旧表
        cursor.execute("DROP TABLE request_info")
        
        # 4. 重命名新表
        cursor.execute("ALTER TABLE request_info_new RENAME TO request_info")
        
        # 5. 重建索引（如果需要）
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_request_name ON request_info(request_name)")
        
        conn.commit()
        print("✅ request_name 唯一约束已成功移除")
        
        # 验证修改
        cursor.execute("PRAGMA table_info(request_info)")
        columns = cursor.fetchall()
        print("\n📋 新的 request_info 表结构:")
        for col in columns:
            print(f"  {col[1]} {col[2]} {'NOT NULL' if col[3] else 'NULL'} {'PRIMARY KEY' if col[5] else ''}")
        
        conn.close()
        return True
        
    except Exception as e:
        print(f"❌ 修复失败: {e}")
        if 'conn' in locals():
            conn.rollback()
            conn.close()
        return False

def verify_fix():
    """验证修复结果"""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        # 尝试插入重复的 request_name
        cursor.execute("INSERT INTO request_info (timestamp, url, method, request_name) VALUES (?, ?, ?, ?)", 
                      ("2025-08-31 11:30:00", "http://test.com", "GET", "测试请求"))
        cursor.execute("INSERT INTO request_info (timestamp, url, method, request_name) VALUES (?, ?, ?, ?)", 
                      ("2025-08-31 11:30:01", "http://test2.com", "POST", "测试请求"))
        
        conn.commit()
        
        # 查询结果
        cursor.execute("SELECT id, request_name, method FROM request_info WHERE request_name = ?", ("测试请求",))
        results = cursor.fetchall()
        
        print(f"\n✅ 验证成功: 成功插入 {len(results)} 条同名请求")
        for result in results:
            print(f"  ID: {result[0]}, 名称: {result[1]}, 方法: {result[2]}")
        
        # 清理测试数据
        cursor.execute("DELETE FROM request_info WHERE request_name = ?", ("测试请求",))
        conn.commit()
        conn.close()
        
        return True
        
    except Exception as e:
        print(f"❌ 验证失败: {e}")
        if 'conn' in locals():
            conn.rollback()
            conn.close()
        return False

def main():
    """主函数"""
    print("🔧 request_name 唯一约束修复工具")
    print("=" * 40)
    
    if not os.path.exists(DB_PATH):
        print(f"❌ 数据库文件不存在: {DB_PATH}")
        return
    
    # 备份数据库
    if not backup_database():
        print("❌ 备份失败，停止操作")
        return
    
    # 修复约束
    if fix_request_name_constraint():
        print("\n🔄 验证修复结果...")
        if verify_fix():
            print("\n🎉 修复完成！现在可以保存同名的请求了。")
        else:
            print("\n⚠️  修复可能不完整，请检查数据库状态")
    else:
        print("\n❌ 修复失败，请检查错误信息")

if __name__ == "__main__":
    main()
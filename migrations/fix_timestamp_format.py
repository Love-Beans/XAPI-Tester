#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
时间戳格式修复脚本
将数据库中的长格式时间戳（包含微秒）转换为短格式（精确到秒）
"""

import sqlite3
import re
from datetime import datetime
import os

def fix_timestamp_format():
    """修复数据库中的时间戳格式"""
    db_path = 'api_tester.db'
    
    if not os.path.exists(db_path):
        print(f"数据库文件 {db_path} 不存在")
        return False
    
    # 备份数据库
    backup_path = f"{db_path}.backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    import shutil
    shutil.copy2(db_path, backup_path)
    print(f"数据库已备份到: {backup_path}")
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # 定义需要修复的表和字段
        tables_fields = {
            'advanced_config': ['created_at', 'updated_at'],
            'project_env': ['created_at', 'updated_at'],
            'project_request_relations': ['created_at'],
            'projects': ['created_at', 'updated_at'],
            'user_project_permissions': ['granted_at'],
            'user_request_relations': ['created_at'],
            'users': ['created_at', 'last_login'],
            'request_info': ['timestamp'],
            'request_history': ['timestamp']
        }
        
        total_updated = 0
        
        for table, fields in tables_fields.items():
            # 检查表是否存在
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name=?", (table,))
            if not cursor.fetchone():
                print(f"表 {table} 不存在，跳过")
                continue
                
            for field in fields:
                # 检查字段是否存在
                cursor.execute(f"PRAGMA table_info({table})")
                columns = [row[1] for row in cursor.fetchall()]
                if field not in columns:
                    print(f"表 {table} 中字段 {field} 不存在，跳过")
                    continue
                
                print(f"正在修复表 {table} 的字段 {field}...")
                
                # 获取所有需要修复的记录
                cursor.execute(f"SELECT id, {field} FROM {table} WHERE {field} IS NOT NULL")
                records = cursor.fetchall()
                
                updated_count = 0
                for record_id, timestamp_str in records:
                    if timestamp_str:
                        # 尝试解析时间戳并转换格式
                        new_timestamp = convert_timestamp_format(timestamp_str)
                        if new_timestamp and new_timestamp != timestamp_str:
                            cursor.execute(f"UPDATE {table} SET {field} = ? WHERE id = ?", 
                                         (new_timestamp, record_id))
                            updated_count += 1
                
                print(f"  - 更新了 {updated_count} 条记录")
                total_updated += updated_count
        
        conn.commit()
        print(f"\n时间戳格式修复完成！总共更新了 {total_updated} 条记录")
        
        # 验证修复结果
        print("\n验证修复结果:")
        for table, fields in tables_fields.items():
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name=?", (table,))
            if not cursor.fetchone():
                continue
                
            for field in fields:
                cursor.execute(f"PRAGMA table_info({table})")
                columns = [row[1] for row in cursor.fetchall()]
                if field not in columns:
                    continue
                    
                cursor.execute(f"SELECT {field} FROM {table} WHERE {field} IS NOT NULL LIMIT 3")
                samples = cursor.fetchall()
                if samples:
                    print(f"  {table}.{field}: {[s[0] for s in samples]}")
        
        return True
        
    except Exception as e:
        conn.rollback()
        print(f"修复过程中发生错误: {e}")
        return False
    finally:
        conn.close()

def convert_timestamp_format(timestamp_str):
    """转换时间戳格式"""
    if not timestamp_str:
        return timestamp_str
    
    try:
        # 如果已经是短格式，直接返回
        if re.match(r'^\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}$', timestamp_str):
            return timestamp_str
        
        # 尝试解析 ISO 格式时间戳
        if 'T' in timestamp_str:
            # ISO 格式: 2025-08-31T08:40:57.718908
            dt = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
            return dt.strftime('%Y-%m-%d %H:%M:%S')
        
        # 尝试解析其他可能的格式
        formats = [
            '%Y-%m-%d %H:%M:%S.%f',  # 带微秒的格式
            '%Y-%m-%dT%H:%M:%S.%f',  # ISO 格式带微秒
            '%Y-%m-%dT%H:%M:%S',     # ISO 格式不带微秒
        ]
        
        for fmt in formats:
            try:
                dt = datetime.strptime(timestamp_str, fmt)
                return dt.strftime('%Y-%m-%d %H:%M:%S')
            except ValueError:
                continue
        
        # 如果无法解析，返回原值
        print(f"无法解析时间戳格式: {timestamp_str}")
        return timestamp_str
        
    except Exception as e:
        print(f"转换时间戳时发生错误: {e}, 原值: {timestamp_str}")
        return timestamp_str

if __name__ == '__main__':
    print("开始修复数据库时间戳格式...")
    success = fix_timestamp_format()
    if success:
        print("\n修复完成！")
    else:
        print("\n修复失败！")
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
数据库提取器 - 从AI处理结果中提取数据并写入数据库
"""

import os
import sqlite3
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, BarColumn, TextColumn
from rich.prompt import Prompt, Confirm
from rich.table import Table
from rich.panel import Panel

console = Console()

def print_step_header(step_num, step_name, description=""):
    """打印步骤标题"""
    console.print(f"\n{'='*60}")
    console.print(f"📋 步骤 {step_num}: {step_name}")
    if description:
        console.print(f"📝 {description}")
    console.print(f"{'='*60}")

def print_success(message):
    """打印成功信息"""
    console.print(f"✅ {message}")

def print_warning(message):
    """打印警告信息"""
    console.print(f"⚠️  {message}")

def print_error(message):
    """打印错误信息"""
    console.print(f"❌ {message}")

def parse_ai_output_file(file_path):
    """解析AI输出文件"""
    records = []
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
            
        for line in lines:
            line = line.strip()
            if not line or not line.startswith('|'):
                continue
                
            # 移除首尾的|符号并分割
            parts = line.strip('|').split('|')
            if len(parts) >= 5:  # 确保有足够的字段
                record = {
                    'en': parts[0],
                    'zh': parts[1],
                    'pro': parts[2] if parts[2] != 'NULL' else None,
                    'type': int(parts[3]),
                    'promt': parts[4] if parts[4] != 'NULL' else None
                }
                records.append(record)
    except Exception as e:
        print_error(f"解析文件 {file_path} 失败: {e}")
    
    return records

def create_database(db_path, table_name):
    """创建数据库和表"""
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # 创建表，使用与txt_to_excel_and_db.py相同的结构，但不包含index
        table_structure = [
            'en TEXT',
            'zh TEXT',
            'promt TEXT',
            'num INTEGER DEFAULT 0',
            'type INTEGER',
            'pro TEXT'
        ]
        create_table_sql = f"CREATE TABLE IF NOT EXISTS {table_name} (id INTEGER PRIMARY KEY AUTOINCREMENT, {', '.join(table_structure)})"
        cursor.execute(create_table_sql)
        
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        print_error(f"创建数据库失败: {e}")
        return False

def insert_records_to_db(db_path, table_name, records):
    """将记录插入数据库"""
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # 插入数据，不包含index字段
        for record in records:
            cursor.execute(f"""
                INSERT INTO {table_name} (en, zh, promt, num, type, pro)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (
                record.get('en', ''),
                record.get('zh', ''),
                record.get('promt', None),
                0,  # num
                record.get('type', 0),
                record.get('pro', None)
            ))
        
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        print_error(f"插入数据库记录失败: {e}")
        return False

def batch_extract_db(ai_output_dir='ai', db_path='words_ai.db'):
    """批量从AI输出目录提取数据并写入数据库"""
    # 检查AI输出目录是否存在
    if not os.path.exists(ai_output_dir):
        print_error(f"目录 {ai_output_dir} 不存在")
        return False
    
    # 创建数据库
    db_name = os.path.splitext(os.path.basename(db_path))[0]
    if not create_database(db_path, db_name):
        return False
    
    print_step_header(1, "数据库提取", f"从目录提取: {ai_output_dir}")
    
    # 获取所有字母目录
    subdirs = [d for d in os.listdir(ai_output_dir) if os.path.isdir(os.path.join(ai_output_dir, d))]
    subdirs.sort()
    
    if not subdirs:
        print_warning("未找到任何字母目录")
        return False
    
    # 过滤掉没有处理结果的子文件夹
    valid_subdirs = []
    for subdir in subdirs:
        subdir_path = os.path.join(ai_output_dir, subdir)
        txt_file = os.path.join(subdir_path, f'{subdir}.txt')
        # 检查目录是否存在且txt文件存在且非空
        if os.path.exists(txt_file) and os.path.getsize(txt_file) > 0:
            valid_subdirs.append(subdir)
        elif os.path.exists(txt_file):
            print_warning(f"跳过 {subdir}，文件为空: {txt_file}")
        else:
            print_warning(f"跳过 {subdir}，文件不存在: {txt_file}")
    
    if not valid_subdirs:
        print_warning("未找到任何有效的字母目录")
        return False
    
    # 显示处理概览
    table = Table(title="处理概览")
    table.add_column("字母", style="cyan")
    table.add_column("状态", style="magenta")
    table.add_column("文件大小", style="green")
    
    total_size = 0
    for subdir in valid_subdirs:
        subdir_path = os.path.join(ai_output_dir, subdir)
        txt_file = os.path.join(subdir_path, f'{subdir}.txt')
        size = os.path.getsize(txt_file)
        total_size += size
        table.add_row(subdir, "待处理", f"{size} bytes")
    
    console.print(table)
    console.print(Panel(f"总计: {len(valid_subdirs)} 个字母, {total_size} 字节", expand=False))
    
    # 处理每个字母目录
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
        expand=True,
        refresh_per_second=10
    ) as progress:
        # 主进度条 - 字母处理进度
        main_task = progress.add_task("总进度", total=len(valid_subdirs))
        
        for subdir in valid_subdirs:
            subdir_path = os.path.join(ai_output_dir, subdir)
            txt_file = os.path.join(subdir_path, f'{subdir}.txt')
            
            try:
                # 处理文件
                console.print(f"\n:database: 提取: {subdir}")
                
                # 确保表存在
                if not create_database(db_path, subdir):
                    print_error(f"创建表 {subdir} 失败")
                    progress.advance(main_task)
                    continue
                
                # 解析AI输出文件
                records = parse_ai_output_file(txt_file)
                
                if records:
                    # 写入数据库
                    if insert_records_to_db(db_path, subdir, records):
                        print_success(f"完成提取: {subdir} ({len(records)} 条记录)")
                    else:
                        print_error(f"数据库写入失败: {subdir}")
                else:
                    print_warning(f"提取完成但无有效记录: {subdir}")
                
            except Exception as e:
                print_error(f"提取 {subdir} 失败: {e}")
            finally:
                # 完成字母任务
                progress.advance(main_task)
    
    print_success(f"数据库提取完成，结果保存至: {db_path}")
    return True

def main():
    console.rule("[bold green]数据库提取器")
    console.print("[bold yellow]欢迎使用数据库提取器！[/bold yellow] :database:")
    
    # 获取AI输出目录
    ai_output_dir = Prompt.ask("请输入AI输出目录路径", default="ai")
    
    # 获取输出数据库路径
    db_path = Prompt.ask("请输入输出数据库文件路径", default="words_ai.db")
    
    # 确认执行
    if not Confirm.ask("是否开始数据库提取?"):
        console.print("[yellow]已取消操作[/yellow]")
        return
    
    # 执行数据库提取
    batch_extract_db(ai_output_dir, db_path)

if __name__ == "__main__":
    main()
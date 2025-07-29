#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AI批处理程序 - 协调AI处理和数据库提取
"""

import os
import subprocess
import sys
from rich.console import Console
from rich.prompt import Prompt, Confirm

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

def run_ai_processor(result_dir='result', ai_output_dir='ai', model="deepseek/deepseek-r1-0528:free"):
    """运行AI处理器"""
    try:
        # 构建命令
        cmd = [
            sys.executable, 'ai_processor.py'
        ]
        
        # 设置环境变量
        env = os.environ.copy()
            
        console.print(f"[bold cyan]运行AI处理器: {' '.join(cmd)}[/bold cyan]")
        
        # 运行AI处理器
        result = subprocess.run(cmd, env=env, check=True)
        return result.returncode == 0
    except subprocess.CalledProcessError as e:
        print_error(f"AI处理器运行失败: {e}")
        return False
    except Exception as e:
        print_error(f"运行AI处理器时出错: {e}")
        return False

def run_db_extractor(ai_output_dir='ai', db_path='words_ai.db'):
    """运行数据库提取器"""
    try:
        # 构建命令
        cmd = [
            sys.executable, 'db_extractor.py'
        ]
        
        console.print(f"[bold cyan]运行数据库提取器: {' '.join(cmd)}[/bold cyan]")
        
        # 运行数据库提取器
        result = subprocess.run(cmd, check=True)
        return result.returncode == 0
    except subprocess.CalledProcessError as e:
        print_error(f"数据库提取器运行失败: {e}")
        return False
    except Exception as e:
        print_error(f"运行数据库提取器时出错: {e}")
        return False

def main():
    console.rule("[bold green]AI批处理程序")
    console.print("[bold yellow]欢迎使用AI批处理程序！[/bold yellow] :brain: :database:")
    
    
    # 获取输入目录
    result_dir = Prompt.ask("请输入result目录路径", default="result")
    
    # 获取AI输出目录
    ai_output_dir = Prompt.ask("请输入AI输出目录路径", default="ai")
    
    # 获取输出数据库路径
    db_path = Prompt.ask("请输入输出数据库文件路径", default="words_ai.db")
    
    # 获取模型名称
    model = Prompt.ask("请输入模型名称", default="deepseek/deepseek-r1-0528:free")
    
    # 确认执行
    if not Confirm.ask("是否开始AI批处理?"):
        console.print("[yellow]已取消操作[/yellow]")
        return
    
    # 步骤1: 运行AI处理器
    print_step_header(1, "AI处理", "使用AI模型处理单词表")
    if not run_ai_processor(result_dir, ai_output_dir, api_key, model):
        print_error("AI处理失败，终止批处理")
        return
    
    print_success("AI处理完成")
    
    # 步骤2: 运行数据库提取器
    print_step_header(2, "数据库提取", "从AI处理结果提取数据并写入数据库")
    if not run_db_extractor(ai_output_dir, db_path):
        print_error("数据库提取失败")
        return
    
    print_success("数据库提取完成")
    
    print_step_header(3, "批处理完成", "")
    console.print(f"[bold green]AI批处理完成！[/bold green]")
    console.print(f"[bold]AI处理结果保存至: {ai_output_dir}[/bold]")
    console.print(f"[bold]数据库文件保存至: {db_path}[/bold]")

if __name__ == "__main__":
    main()
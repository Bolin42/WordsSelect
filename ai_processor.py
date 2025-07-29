#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AI处理器 - 专门处理AI相关功能
"""

import os
import time
import requests
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, BarColumn, TextColumn
from rich.prompt import Prompt, Confirm
import dotenv

# 加载环境变量
dotenv.load_dotenv()

# 从.env文件读取API密钥
SILICONFLOW_API_KEY = os.getenv("SILICONFLOW_API_KEY")

console = Console()

# 定义模型列表，均为硅基流动免费模型
MODELS = [
    "THUDM/GLM-4-9B-0414",
    "Qwen/Qwen2.5-7B-Instruct",
    "Qwen/Qwen2.5-Coder-7B-Instruct",
    "Qwen/Qwen2-7B-Instruct",
    "THUDM/GLM-4.1V-9B-Thinking",
    "deepseek-ai/DeepSeek-R1-0528-Qwen3-8B",
    "THUDM/GLM-Z1-9B-0414",
    "deepseek-ai/DeepSeek-R1-Distill-Qwen-7B",
    "Qwen/Qwen2.5-7B-Instruct",
    "Qwen/Qwen2.5-Coder-7B-Instruct",
    "THUDM/GLM-4-9B-0414",
    "Qwen/Qwen3-8B",
    "internlm/internlm2_5-7b-chat",
    "THUDM/glm-4-9b-chat",
    "Qwen/Qwen2-7B-Instruct"
]

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

def check_model_status(api_key, model):
    """检查模型状态"""
    try:
        url = "https://api.siliconflow.cn/v1/chat/completions"
        payload = {
            "model": model,
            "messages": [
                {
                    "role": "user",
                    "content": "Hello"
                }
            ],
            "max_tokens": 10,
            "temperature": 0.1
        }
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }

        response = requests.post(url, json=payload, headers=headers, timeout=10)
        if response.status_code == 200:
            return True
        else:
            return False
    except Exception:
        return False

def get_available_models(api_key):
    """获取可用模型列表"""
    console.print("🔍 检查模型状态...")
    available_models = []
    
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
        expand=True,
    ) as progress:
        task = progress.add_task("检查模型...", total=len(MODELS))
        
        for model in MODELS:
            progress.update(task, description=f"检查 {model}...", advance=1)
            if check_model_status(api_key, model):
                available_models.append(model)
                console.print(f"  ✅ {model} [green]可用[/green]")
            else:
                console.print(f"  ❌ {model} [red]不可用[/red]")
    
    if not available_models:
        print_error("没有可用的模型")
        return None
    
    return available_models

def split_file_by_size(file_path, chunk_size=2*1024):
    """按指定大小分割文件，返回分割后的内容列表"""
    chunks = []
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
            
        if len(content.encode('utf-8')) <= chunk_size:
            # 文件小于等于chunk_size，不需要分割
            chunks.append(content)
        else:
            # 按行分割文件，避免单词被截断
            lines = content.splitlines(True)  # 保留换行符
            current_chunk = ""
            
            for line in lines:
                # 检查添加这行后是否会超过chunk_size
                test_chunk = current_chunk + line
                if len(test_chunk.encode('utf-8')) > chunk_size and current_chunk:
                    # 当前块已满，保存并开始新块
                    chunks.append(current_chunk)
                    current_chunk = line
                else:
                    current_chunk += line
            
            # 添加最后一个块
            if current_chunk:
                chunks.append(current_chunk)
                
        return chunks
    except Exception as e:
        print_error(f"分割文件失败: {e}")
        return []

def call_qwen_api(content, api_key, model="Qwen/QwQ-32B", available_models=None):
    """调用硅基流动API"""
    prompt = (
        "请将以下单词表内容修正为标准格式，每行一个单词，格式如下：。\n"
        "每一行都由个元素组成，分别为：\n"
        "en：英文单词/词组/句子\n"
        "zh：中文释义，如果中文释义中间存在分号，则分号分割了2个不同的释义。\n"
        "pro：词性（注：只有单词有词性，词组与句子的词性设为NULL）\n"
        "type：en类型（注：句子的type为1,单词的type为0,词组的type为-1）\n"
        "promt：对于type为词组和句子的en,根据上文（不查找下文）找出最有可能的原单词，即该词组中保有的最低有效提示单词\n"
        "如果原始内容有格式错误、缺失、顺序混乱、缺少词性等，请自动补全和修正。\n"
        "同时，对于多个解释，请另起一行，重复英文，并继续输出相关内容。其中“/”之间可能混有音标，这个不管，直接丢弃。\n"
        "单词性、单释义示例：\n"
        "|abandon|放弃|vt.|0|NULL|\n"
        "多词性、多释义示例：\n"
        "输入为：contrary/'kontrari/ n./adj. 相反\n 输出为：\n"
        "|contrary|相反|n.|0|NULL|\n"
        "|contrary|相反|adj.|0|NULL|\n"
        "或者：\n"
        "输入为：shoulder/feulde/ n. 肩膀 vt. 挑起，扛起；担负 \n"
        "输出为：\n"
        "|shoulder|肩膀|n.|0|NULL|\n"
        "|shoulder|挑起，扛起；担负|vt.|0|NULL|\n"
        "单词性、多释义示例：\n"
        "输入为：consume /ken'sju:m/ vt.消费；吃，喝；消耗\n"
        "输出为：\n |consume|消费|vt.|0|NULL|\n |consume|吃，喝|vt.|0|NULL|\n |consume|消耗|vt.|0|NULL|\n"
        "词组示例：\n"
        "|consider doing|考虑做……|NULL|-1|consider|\n"
        "句子示例：\n"
        "|As we get older, we often find it difficult to understand music.|年龄增长时，我们常常发现难以理解音乐。|NULL|1|understand|\n"
        "如果有多词性或多义项，请分多行输出。不要输出多余解释和说明，只输出修正后的内容。\n"
        "每一列由\"|\"分割，\"|\"与内容之间不要添加空格\n"
        "原始内容如下：\n"
        f"{content}\n"
        "请严格按照上述格式输出。"
    )
    
    max_retries = 5
    retry_delay = 10
    
    # 显示发送的数据包大小
    payload = {
        "model": model,
        "messages": [
            {
                "role": "system",
                "content": "你是一个英语单词表格式修正助手。"
            },
            {
                "role": "user",
                "content": prompt
            }
        ],
        "max_tokens": 2048,
        "temperature": 0.2
    }
    
    payload_size = len(str(payload).encode('utf-8'))
    console.print(f"  📦 发送数据包大小: {payload_size} 字节")
    
    # 确定要尝试的模型列表
    if available_models:
        models_to_try = [model] if model in available_models else []
        # 添加其他可用模型作为备选
        for m in available_models:
            if m != model and m not in models_to_try:
                models_to_try.append(m)
    else:
        # 如果没有提供可用模型列表，则使用默认列表
        models_to_try = [model] + [m for m in MODELS if m != model]
    
    # 如果首选模型不在可用列表中，给出警告
    if model not in models_to_try:
        print_warning(f"首选模型 {model} 不可用，将使用其他可用模型")
    
    for model_idx, current_model in enumerate(models_to_try):
        if model_idx > 0:  # 如果是备用模型，给出提示
            print_warning(f"切换到备用模型: {current_model}")
            
        for attempt in range(max_retries):
            try:
                url = "https://api.siliconflow.cn/v1/chat/completions"
                
                # 更新当前尝试的模型
                payload["model"] = current_model
                
                start_time = time.time()
                headers = {
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json"
                }

                response = requests.post(url, json=payload, headers=headers, timeout=60)
                response.raise_for_status()
                
                end_time = time.time()
                response_time = end_time - start_time
                
                # 显示响应信息
                response_size = len(response.content)
                speed = response_size / response_time if response_time > 0 else 0
                console.print(f"  📥 响应数据包大小: {response_size} 字节")
                console.print(f"  🕒 响应时间: {response_time:.2f} 秒")
                console.print(f"  🚀 传输速度: {speed:.2f} 字节/秒")
                
                result = response.json()
                return result["choices"][0]["message"]["content"], 2*1024  # 2KB块大小
                
            except Exception as e:
                error_str = str(e)
                # 检查是否是502或503错误
                if "502" in error_str or "503" in error_str:
                    if attempt < max_retries - 1:  # 不是最后一次尝试
                        if "502" in error_str:
                            print_warning(f"遇到502错误，等待{retry_delay}秒后重试 (尝试 {attempt + 1}/{max_retries})...")
                        elif "503" in error_str:
                            print_warning(f"遇到503错误，等待{retry_delay}秒后重试 (尝试 {attempt + 1}/{max_retries})...")
                        time.sleep(retry_delay)
                        continue
                    else:
                        print_error(f"模型 {current_model} 重试{max_retries}次后仍然失败")
                else:
                    print_error(f"API调用失败: {e}")
                    # 对于非502/503错误，不尝试其他模型
                    if model_idx == 0:  # 只有主模型才尝试备用模型
                        break
                    return None, 2*1024
    
    return None, 2*1024

def parse_fixed_content(content):
    """解析修正后的内容"""
    records = []
    lines = content.strip().split('\n')
    
    for line_num, line in enumerate(lines, 1):
        line = line.strip()
        if not line or not line.startswith('|'):
            continue
            
        try:
            # 移除首尾的|符号并分割
            parts = line.strip('|').split('|')
            if len(parts) >= 5:  # 确保有足够的字段
                # 安全地转换type字段
                try:
                    type_value = int(parts[3])
                except ValueError:
                    print_warning(f"第{line_num}行type字段转换失败，使用默认值0: {parts[3]}")
                    type_value = 0
                
                record = {
                    'en': parts[0],
                    'zh': parts[1],
                    'pro': parts[2] if parts[2] != 'NULL' else None,
                    'type': type_value,
                    'promt': parts[4] if parts[4] != 'NULL' else None
                }
                records.append(record)
            else:
                print_warning(f"第{line_num}行字段不足，跳过: {line}")
        except Exception as e:
            print_warning(f"第{line_num}行解析失败: {line}, 错误: {e}")
    
    return records

def process_single_letter(subdir, txt_file, ai_output_dir, api_key, model, available_models):
    """处理单个字母目录"""
    try:
        # 创建输出目录
        ai_subdir = os.path.join(ai_output_dir, subdir)
        os.makedirs(ai_subdir, exist_ok=True)
        
        # 显示处理信息
        console.print(f"\n:brain: 处理: {subdir}")
        console.print(f"  📄 源文件: {txt_file}")
        console.print(f"  📁 输出目录: {ai_subdir}")
        
        # 检查文件是否为空
        if os.path.getsize(txt_file) == 0:
            print_warning(f"文件 {txt_file} 为空，跳过处理")
            return True
        
        # 获取文件大小
        file_size = os.path.getsize(txt_file)
        console.print(f"  📄 文件大小: {file_size} 字节")
        
        # 先尝试调用API获取合适的块大小
        with open(txt_file, 'r', encoding='utf-8') as f:
            test_content = f.read(1000)  # 读取前1000个字符作为测试
        
        # 获取模型和块大小
        fixed_content, chunk_size = call_qwen_api(test_content, api_key, model, available_models)
        if fixed_content is None:
            print_error(f"无法获取模型信息，使用默认块大小")
            chunk_size = 2*1024  # 默认2KB
        
        console.print(f"  🧠 使用模型推荐块大小: {chunk_size} 字节")
        
        # 分割文件为指定大小的块
        chunks = split_file_by_size(txt_file, chunk_size)
        console.print(f"  🔪 分割为 {len(chunks)} 块")
        
        if not chunks:
            print_warning(f"文件 {txt_file} 无法分割")
            return True
        
        # 检查是否存在已处理的块文件，实现断点恢复
        processed_chunks = set()
        if os.path.exists(ai_subdir):
            for file_name in os.listdir(ai_subdir):
                if file_name.startswith("chunk_") and file_name.endswith(".txt"):
                    try:
                        chunk_num = int(file_name.split("_")[1].split(".")[0])
                        processed_chunks.add(chunk_num - 1)  # 转换为0基索引
                    except:
                        pass
        
        # 收集所有记录
        all_records = []
        
        # 如果有已处理的块，加载它们的记录
        for chunk_idx in processed_chunks:
            if chunk_idx < len(chunks):
                chunk_output_path = os.path.join(ai_subdir, f"chunk_{chunk_idx + 1}.txt")
                if os.path.exists(chunk_output_path):
                    try:
                        with open(chunk_output_path, 'r', encoding='utf-8') as f:
                            fixed_content = f.read()
                        records = parse_fixed_content(fixed_content)
                        all_records.extend(records)
                        console.print(f"  🔄 恢复已处理块 {chunk_idx + 1}")
                    except Exception as e:
                        print_warning(f"恢复块 {chunk_idx + 1} 失败: {e}")
        
        # 处理未完成的块
        start_time = time.time()
        completed_chunks = len(processed_chunks)
        total_chunks = len(chunks)
        
        for i, chunk in enumerate(chunks):
            # 如果块已经处理过，跳过
            if i in processed_chunks:
                continue
                
            try:
                # 计算剩余时间
                if completed_chunks > 0:
                    elapsed_time = time.time() - start_time
                    avg_time_per_chunk = elapsed_time / completed_chunks
                    remaining_chunks = total_chunks - completed_chunks
                    estimated_remaining_time = avg_time_per_chunk * remaining_chunks
                else:
                    estimated_remaining_time = 0
                    
                # 显示实时统计信息
                stats_text = f"[cyan]已处理: {completed_chunks}/{total_chunks} 块, "
                stats_text += f"剩余: {total_chunks - completed_chunks} 块, "
                stats_text += f"预计剩余时间: {estimated_remaining_time:.1f} 秒[/cyan]"
                console.print(stats_text)
                
                # 显示当前块大小
                chunk_size_bytes = len(chunk.encode('utf-8'))
                console.print(f"  📦 块 {i+1} 大小: {chunk_size_bytes} 字节")
                
                # 调用AI API处理
                fixed_content, _ = call_qwen_api(chunk, api_key, model, available_models)
                if fixed_content is None:
                    print_error(f"AI处理块 {i+1} 失败")
                    return False
                
                # 显示AI返回内容的前200个字符用于调试
                preview_content = fixed_content[:200] + ("..." if len(fixed_content) > 200 else "")
                console.print(f"  🧾 AI返回内容预览: {preview_content}")
                
                # 保存AI输出到文件
                chunk_output_path = os.path.join(ai_subdir, f"chunk_{i+1}.txt")
                with open(chunk_output_path, 'w', encoding='utf-8') as f:
                    f.write(fixed_content)
                
                # 显示AI输出大小
                output_size = len(fixed_content.encode('utf-8'))
                console.print(f"  💾 保存块 {i+1} 输出到: {chunk_output_path} ({output_size} 字节)")
                
                # 解析处理结果
                records = parse_fixed_content(fixed_content)
                all_records.extend(records)
                
                completed_chunks += 1
                
                # 防止API限流
                time.sleep(0.5)
                
            except Exception as e:
                print_error(f"处理块 {i+1} 失败: {e}")
                # 打印完整的traceback以便调试
                import traceback
                traceback.print_exc()
                return False
        
        # 保存合并后的结果
        merged_output_path = os.path.join(ai_subdir, f'{subdir}.txt')
        with open(merged_output_path, 'w', encoding='utf-8') as f:
            for record in all_records:
                f.write(f"|{record['en']}|{record['zh']}|{record['pro'] or 'NULL'}|{record['type']}|{record['promt'] or 'NULL'}|\n")
        
        # 验证文件是否正确生成
        if os.path.exists(merged_output_path):
            merged_size = os.path.getsize(merged_output_path)
            print_success(f"完成处理: {subdir} ({len(all_records)} 条记录)，结果保存至: {merged_output_path} ({merged_size} 字节)")
        else:
            print_error(f"完成处理: {subdir} ({len(all_records)} 条记录)，但合并文件未正确生成: {merged_output_path}")
        
        return True
        
    except Exception as e:
        print_error(f"处理 {subdir} 失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def batch_process_ai(result_dir='result', ai_output_dir='ai', api_key=None, model="Qwen/QwQ-32B", available_models=None, selected_letters=None):
    """批量处理result目录下的文件，AI处理结果保存到ai目录"""
    if not api_key:
        print_error("未提供API密钥")
        return False
    
    # 检查result目录是否存在
    if not os.path.exists(result_dir):
        print_error(f"目录 {result_dir} 不存在")
        return False
    
    print_step_header(1, "AI处理", f"处理目录: {result_dir}")
    
    # 获取所有字母目录
    subdirs = [d for d in os.listdir(result_dir) if os.path.isdir(os.path.join(result_dir, d))]
    subdirs.sort()
    
    if not subdirs:
        print_warning("未找到任何字母目录")
        return False
    
    # 过滤掉空的子文件夹
    valid_subdirs = []
    for subdir in subdirs:
        subdir_path = os.path.join(result_dir, subdir)
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
    
    # 如果指定了要处理的字母，则过滤
    if selected_letters:
        filtered_subdirs = []
        for subdir in valid_subdirs:
            if subdir in selected_letters:
                filtered_subdirs.append(subdir)
        valid_subdirs = filtered_subdirs
    
    # 显示处理概览
    from rich.table import Table
    table = Table(title="处理概览")
    table.add_column("ID", style="blue", justify="right")
    table.add_column("字母", style="cyan")
    table.add_column("状态", style="magenta")
    table.add_column("文件大小", style="green")
    
    total_size = 0
    for idx, subdir in enumerate(valid_subdirs, 1):
        subdir_path = os.path.join(result_dir, subdir)
        txt_file = os.path.join(subdir_path, f'{subdir}.txt')
        size = os.path.getsize(txt_file)
        total_size += size
        table.add_row(str(idx), subdir, "待处理", f"{size} bytes")
    
    console.print(table)
    console.print(f"[bold]总计: {len(valid_subdirs)} 个字母, {total_size} 字节[/bold]")
    console.print(f"[bold]使用模型: {model}[/bold]")
    
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
        
        for subdir_idx, subdir in enumerate(valid_subdirs):
            subdir_path = os.path.join(result_dir, subdir)
            txt_file = os.path.join(subdir_path, f'{subdir}.txt')
            
            # 更新主进度条描述
            progress.update(main_task, description=f"处理 {subdir} ({subdir_idx+1}/{len(valid_subdirs)})")
            
            # 标记首字母是否处理成功
            letter_processed_successfully = False
            max_letter_attempts = 3
            
            for letter_attempt in range(max_letter_attempts):
                # 处理单个字母
                result = process_single_letter(subdir, txt_file, ai_output_dir, api_key, model, available_models)
                
                if result:  # 成功处理
                    letter_processed_successfully = True
                    break
                else:
                    # 处理失败，需要重新尝试
                    if letter_attempt < max_letter_attempts - 1:
                        print_warning(f"首字母 {subdir} 处理失败，等待15秒后重新尝试 (第 {letter_attempt + 2}/{max_letter_attempts} 次)...")
                        time.sleep(15)
                        continue
                    else:
                        print_error(f"首字母 {subdir} 处理失败，已尝试 {max_letter_attempts} 次，跳过处理")
            
            # 更新主进度条
            progress.advance(main_task)
            
            # 确保有适当的延迟，避免API限流
            time.sleep(2)
    
    print_success(f"AI处理完成，结果保存至: {ai_output_dir}")
    return True

def parse_letter_selection(selection_str, available_letters):
    """解析字母选择字符串，支持单个字母、范围和列表"""
    if not selection_str or selection_str.lower() == "all":
        return available_letters
    
    selected = set()
    parts = selection_str.split(',')
    
    for part in parts:
        part = part.strip().lower()
        if '-' in part and len(part) == 3:  # 范围，如 a-c
            start, end = part.split('-')
            if start.isalpha() and end.isalpha():
                start_ord = ord(start)
                end_ord = ord(end)
                for i in range(min(start_ord, end_ord), max(start_ord, end_ord) + 1):
                    letter = chr(i)
                    if letter in available_letters:
                        selected.add(letter)
        elif part.isalpha() and len(part) == 1:  # 单个字母
            if part in available_letters:
                selected.add(part)
    
    return sorted(list(selected))

def main():
    console.rule("[bold green]AI处理器")
    console.print("[bold yellow]欢迎使用AI处理器！[/bold yellow] :brain:")
    
    # 获取API密钥 - 优先从.env文件读取
    api_key = SILICONFLOW_API_KEY
    if not api_key:
        api_key = Prompt.ask("请输入SiliconFlow API密钥")
        if not api_key:
            print_error("未提供API密钥")
            return
    
    # 检查可用模型
    available_models = get_available_models(api_key)
    if not available_models:
        print_error("没有可用的模型，程序退出")
        return
    
    # 显示可用模型
    console.print("\n[bold green]可用模型列表:[/bold green]")
    for i, model in enumerate(available_models, 1):
        console.print(f"  {i}. {model}")
    
    # 获取输入目录
    result_dir = Prompt.ask("请输入result目录路径", default="result")
    
    # 获取AI输出目录
    ai_output_dir = Prompt.ask("请输入AI输出目录路径", default="ai")
    
    # 获取模型名称（默认选择第一个可用模型）
    default_model = available_models[0]
    model = Prompt.ask("请输入模型名称", default=default_model)
    
    # 获取所有可用字母
    if os.path.exists(result_dir):
        subdirs = [d for d in os.listdir(result_dir) if os.path.isdir(os.path.join(result_dir, d))]
        subdirs.sort()
        valid_subdirs = []
        for subdir in subdirs:
            subdir_path = os.path.join(result_dir, subdir)
            txt_file = os.path.join(subdir_path, f'{subdir}.txt')
            if os.path.exists(txt_file) and os.path.getsize(txt_file) > 0:
                valid_subdirs.append(subdir)
    else:
        valid_subdirs = []
    
    # 显示可用字母并获取用户选择
    if valid_subdirs:
        console.print("\n[bold green]可用字母:[/bold green]")
        letters_display = ", ".join(valid_subdirs)
        console.print(f"  {letters_display}")
        selection_help = "输入要处理的字母（如: a, b, c 或 a-c 或 all）"
        selected_str = Prompt.ask(selection_help, default="all")
        selected_letters = parse_letter_selection(selected_str, valid_subdirs)
    else:
        selected_letters = None
    
    # 确认执行
    if not Confirm.ask("是否开始AI处理?"):
        console.print("[yellow]已取消操作[/yellow]")
        return
    
    # 执行AI处理
    batch_process_ai(result_dir, ai_output_dir, api_key, model, available_models, selected_letters)

if __name__ == "__main__":
    main()
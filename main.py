import logging
import os
from image_process import process_images
from check_count import check_file_count
from ocr_alicloud import AliyunOCRBatch
from formatter import batch_process_json_to_txt
import subprocess
import shutil
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, BarColumn, TextColumn
from rich.prompt import Confirm
from concurrent.futures import ThreadPoolExecutor, as_completed

# 设置日志格式
logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s:%(message)s')

console = Console()

def print_step_header(step_num, step_name, description=""):
    """打印步骤标题"""
    print(f"\n{'='*60}")
    print(f"📋 步骤 {step_num}: {step_name}")
    if description:
        print(f"📝 {description}")
    print(f"{'='*60}")

def print_success(message):
    """打印成功信息"""
    print(f"✅ {message}")

def print_warning(message):
    """打印警告信息"""
    print(f"⚠️  {message}")

def print_error(message):
    """打印错误信息"""
    print(f"❌ {message}")

def ask_continue(step_name):
    """询问用户是否继续"""
    while True:
        response = input(f"\n是否继续执行 {step_name}？(y/n): ").strip().lower()
        if response in ['y', 'yes', '是']:
            return True
        elif response in ['n', 'no', '否']:
            return False
        else:
            print("请输入 y 或 n")

def get_sorted_folders(input_dir):
    """获取正常排序的文件夹列表"""
    if not os.path.exists(input_dir):
        print_error(f"输入目录 {input_dir} 不存在")
        return []
    
    folders = []
    for item in os.listdir(input_dir):
        item_path = os.path.join(input_dir, item)
        if os.path.isdir(item_path):
            folders.append(item)
    
    # 正常顺序排序
    folders.sort()
    return folders

def merge_txt_to_result(txt_dir='txt', result_dir='result', result_file='final.txt'):
    if not os.path.exists(result_dir):
        os.makedirs(result_dir)
    subdirs = [d for d in os.listdir(txt_dir) if os.path.isdir(os.path.join(txt_dir, d))]
    subdirs.sort()
    for subdir in subdirs:
        sub_txt_dir = os.path.join(txt_dir, subdir)
        sub_result_dir = os.path.join(result_dir, subdir)
        if not os.path.exists(sub_result_dir):
            os.makedirs(sub_result_dir)
        txt_files = [f for f in os.listdir(sub_txt_dir) if f.endswith('.txt')]
        txt_files.sort(key=lambda x: int(os.path.splitext(x)[0]) if os.path.splitext(x)[0].isdigit() else x)
        merged_path = os.path.join(sub_result_dir, 'merged.txt')
        with open(merged_path, 'w', encoding='utf-8') as outfile:
            for fname in txt_files:
                file_path = os.path.join(sub_txt_dir, fname)
                with open(file_path, 'r', encoding='utf-8') as infile:
                    outfile.write(infile.read())
                    outfile.write('\n')
        print_success(f"已合并 {len(txt_files)} 个txt文件到: {merged_path}")

def check_and_prompt_json_to_txt(json_dir='json', txt_dir='txt', result_dir='result'):
    subdirs = [d for d in os.listdir(json_dir) if os.path.isdir(os.path.join(json_dir, d))]
    subdirs.sort()
    for subdir in subdirs:
        sub_json_dir = os.path.join(json_dir, subdir)
        sub_result_dir = os.path.join(result_dir, subdir)
        has_json = any(f.endswith('.json') for f in os.listdir(sub_json_dir))
        has_result = os.path.exists(sub_result_dir) and any(f.endswith('.txt') for f in os.listdir(sub_result_dir))
        if has_json and not has_result:
            print_warning(f"检测到 {subdir} 文件夹下有json但无result/txt，是否先处理这些json?")
            resp = input(f"是否处理 {subdir} 的json文件？(y/n): ").strip().lower()
            if resp == 'y':
                from formatter import batch_process_json_to_txt
                batch_process_json_to_txt(json_dir, txt_dir, only_letter=subdir)
                print_success(f"已处理 {subdir} 的json文件并生成txt")

def get_done_letters(result_dir='result'):
    done_letters = set()
    for subdir in os.listdir(result_dir):
        sub_path = os.path.join(result_dir, subdir)
        if os.path.isdir(sub_path):
            target_file = os.path.join(sub_path, f'{subdir}.txt')
            # 检查文件是否存在且非空
            if os.path.exists(target_file) and os.path.getsize(target_file) > 0:
                done_letters.add(subdir)
    return done_letters

def get_json_processed_letters(json_dir='json'):
    """获取json目录中已有内容的字母文件夹"""
    processed_letters = set()
    for subdir in os.listdir(json_dir):
        sub_path = os.path.join(json_dir, subdir)
        if os.path.isdir(sub_path):
            # 检查文件夹是否非空
            if any(os.path.isfile(os.path.join(sub_path, f)) for f in os.listdir(sub_path)):
                processed_letters.add(subdir)
    return processed_letters


def run_llm_txt_to_db(txt_path, db_path, api_key, table='words'):
    cmd = [
        'python', 'llm_txt_to_db.py',
        '--input', txt_path,
        '--db', db_path,
        '--table', table,
        '--api_key', api_key
    ]
    console.print(f"[bold cyan]调用大模型分割+入库：{' '.join(cmd)}[/bold cyan]")
    subprocess.run(cmd, check=True)


def main():
    console.rule("[bold green]WordsSelect 智能单词处理系统 v3.0")
    console.print("[bold yellow]欢迎使用！[/bold yellow] :rocket:")
    console.print("[bold]请选择处理分支：[/bold]")
    use_ai = Confirm.ask("是否使用AI大模型分割+入库分支？（推荐高质量分割）", default=False)
    if use_ai:
        txt_path = console.input("请输入待分割的txt文件路径：")
        db_path = console.input("请输入输出sqlite db文件路径：")
        api_key = console.input("请输入OpenRouter API KEY：")
        table = console.input("请输入表名（默认words）：") or 'words'
        run_llm_txt_to_db(txt_path, db_path, api_key, table)
        console.print("[bold green]AI分割+入库流程已完成！[/bold green]")
        return

    # 传统OCR分支
    done_letters = get_done_letters('result')
    console.print(f"[bold blue]已完成的首字母: {sorted(done_letters)}[/bold blue]")
    
    # 获取json目录中已有内容的字母文件夹
    json_processed_letters = get_json_processed_letters('json')
    if json_processed_letters:
        console.print(f"[bold yellow]检测到JSON目录中已有内容的首字母: {sorted(json_processed_letters)}[/bold yellow]")
        # 只有当result目录中没有对应完成文件时，才将这些字母加入跳过列表
        for letter in json_processed_letters:
            result_letter_file = os.path.join('result', letter, f'{letter}.txt')
            # 如果result中没有对应文件或者文件为空，则跳过
            if not (os.path.exists(result_letter_file) and os.path.getsize(result_letter_file) > 0):
                done_letters.add(letter)
                console.print(f"[bold yellow]添加 {letter} 到跳过列表 (JSON已完成但result未完成)[/bold yellow]")

    input_dir = "input"
    processed_dir = "processed"
    json_dir = "json"
    txt_dir = "txt"
    result_dir = "result"
    y1, y2, x1, x2 = 156, 156, 163, 914

    # 步骤1: 图片预处理
    console.rule("[bold magenta]步骤1: 图片预处理")
    for subdir in os.listdir(input_dir):
        if subdir in done_letters:
            console.print(f":white_check_mark: 跳过图片预处理: {subdir}")
            continue
        try:
            process_images(os.path.join(input_dir, subdir), os.path.join(processed_dir, subdir), y1, y2, x1, x2)
            console.print(f":sparkles: 完成图片预处理: {subdir}")
        except Exception as e:
            console.print(f":x: [red]图片预处理失败: {subdir}，原因: {e}[/red]")

    # 步骤2: OCR识别（单线程）
    console.rule("[bold magenta]步骤2: OCR识别")
    need_ocr = [subdir for subdir in os.listdir(processed_dir) if subdir not in done_letters]
    
    # 使用单线程处理OCR识别，避免信号处理问题
    with Progress(SpinnerColumn(), TextColumn("{task.description}"), BarColumn(), transient=True) as progress:
        task = progress.add_task("OCR识别中...", total=len(need_ocr))
        for subdir in need_ocr:
            try:
                ocr = AliyunOCRBatch()
                ocr.batch_recognize(os.path.join(processed_dir, subdir), os.path.join(json_dir, subdir))
                console.print(f":sparkles: 完成OCR识别: {subdir}")
            except Exception as e:
                console.print(f":x: [red]OCR识别失败: {subdir}，原因: {e}[/red]")
            progress.advance(task)

    # 步骤3: JSON转TXT
    console.rule("[bold magenta]步骤3: JSON转TXT")
    for subdir in os.listdir(json_dir):
        if subdir in done_letters:
            console.print(f":white_check_mark: 跳过JSON转TXT: {subdir}")
            continue
        try:
            batch_process_json_to_txt(json_dir, txt_dir, only_letter=subdir)
            console.print(f":sparkles: 完成JSON转TXT: {subdir}")
        except Exception as e:
            console.print(f":x: [red]JSON转TXT失败: {subdir}，原因: {e}[/red]")

    # 步骤4: TXT合并到result
    console.rule("[bold magenta]步骤4: TXT合并")
    for subdir in os.listdir(txt_dir):
        if subdir in done_letters:
            console.print(f":white_check_mark: 跳过TXT合并: {subdir}")
            continue
        try:
            sub_txt_dir = os.path.join(txt_dir, subdir)
            sub_result_dir = os.path.join(result_dir, subdir)
            if not os.path.exists(sub_result_dir):
                os.makedirs(sub_result_dir)
            txt_files = [f for f in os.listdir(sub_txt_dir) if f.endswith('.txt')]
            txt_files.sort(key=lambda x: int(os.path.splitext(x)[0]) if os.path.splitext(x)[0].isdigit() else x)
            # 修复：正确合并txt文件到subdir.txt而不是merged.txt
            merged_path = os.path.join(sub_result_dir, f'{subdir}.txt')
            with open(merged_path, 'w', encoding='utf-8') as outfile:
                for fname in txt_files:
                    file_path = os.path.join(sub_txt_dir, fname)
                    with open(file_path, 'r', encoding='utf-8') as infile:
                        content = infile.read()
                        if content:  # 只有当内容非空时才写入
                            outfile.write(content)
                            outfile.write('\n')
            console.print(f":sparkles: 合并TXT完成: {merged_path}")
        except Exception as e:
            console.print(f":x: [red]TXT合并失败: {subdir}，原因: {e}[/red]")

    console.rule("[bold green]流程结束")
    console.print("如需批量导出Excel/DB或生成练习表，请运行对应脚本。", style="bold yellow")

if __name__ == '__main__':
    main() 
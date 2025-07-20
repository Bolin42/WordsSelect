import logging
import os
from image_process import process_images
from check_count import check_file_count
from ocr_alicloud import AliyunOCRBatch
from formatter import batch_process_json_to_txt
import subprocess
import shutil

# 设置日志格式
logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s:%(message)s')

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

def main():
    print("🎯 WordsSelect 单词提取系统")
    print("📁 处理流程：图片预处理 → OCR识别 → 单词提取 → 结果合并 → 元数据清理")
    print()

    # 配置参数
    input_dir = "input"
    processed_dir = "processed"
    json_dir = "json"
    txt_dir = "txt"
    result_dir = "result"
    y1, y2, x1, x2 = 156, 156, 163, 914

    # 步骤0: 启动时优先检测未转txt的json
    check_and_prompt_json_to_txt(json_dir, txt_dir, result_dir)

    # 检查输入目录
    folders = get_sorted_folders(input_dir)
    if not folders:
        print_error("没有找到任何输入文件夹")
        return
    
    print(f"📂 找到 {len(folders)} 个输入文件夹（正常顺序）:")
    for i, folder in enumerate(folders, 1):
        folder_path = os.path.join(input_dir, folder)
        jpg_count = len([f for f in os.listdir(folder_path) if f.lower().endswith('.jpg')])
        print(f"   {i}. {folder}/ ({jpg_count} 个jpg文件)")
    
    if not ask_continue("图片预处理"):
        print_warning("用户取消，流程终止")
        return

    # 步骤1: 图像预处理
    print_step_header(1, "图像预处理", "裁剪和拼接图片（每个文件夹单独询问页面类型）")
    print("🔄 开始图像预处理...")
    try:
        process_images(input_dir, processed_dir, y1, y2, x1, x2)
        print_success("图像预处理完成")
    except Exception as e:
        print_error(f"图像预处理失败: {e}")
        return

    # 步骤2: 文件数量校验
    print_step_header(2, "文件数量校验", "验证处理前后的文件数量")
    if not check_file_count(input_dir, processed_dir):
        print_error("文件数量校验失败，流程终止")
        return
    print_success("文件数量校验通过")
    
    if not ask_continue("OCR识别"):
        print_warning("用户取消，流程终止")
        return

    # 步骤3: 阿里云OCR识别
    print_step_header(3, "阿里云OCR识别", "云端文字识别（可能产生费用）")
    confirm = input("即将进行阿里云OCR云端识别，可能产生费用，是否继续？(y/n): ").strip().lower()
    if confirm != 'y':
        print_warning("已取消云端处理，流程终止")
        return
    
    print("🔄 开始阿里云OCR识别...")
    try:
        ocr = AliyunOCRBatch()
        ocr.batch_recognize(processed_dir, json_dir)
        print_success("阿里云OCR识别完成")
    except Exception as e:
        print_error(f"阿里云OCR识别失败: {e}")
        return

    if not ask_continue("JSON转TXT"):
        print_warning("用户取消，流程终止")
        return

    # 步骤4: JSON转TXT
    print_step_header(4, "JSON转TXT", "解析JSON生成单词表")
    print("🔄 开始解析json生成单词表...")
    try:
        batch_process_json_to_txt(json_dir, txt_dir)
        print_success("JSON转TXT完成")
    except Exception as e:
        print_error(f"JSON转TXT失败: {e}")
        return

    if not ask_continue("合并TXT文件"):
        print_warning("用户取消，流程终止")
        return

    # 步骤5: 合并TXT文件
    print_step_header(5, "合并TXT文件", "将所有txt文件合并为各自首字母总表")
    print("🔄 开始合并所有单词表...")
    try:
        merge_txt_to_result(txt_dir, result_dir, result_file='final.txt')
        print_success("TXT文件合并完成")
    except Exception as e:
        print_error(f"TXT文件合并失败: {e}")
        return

    if not ask_continue("元数据清理"):
        print_warning("用户取消，流程终止")
        return

    # 步骤6: 清理元数据
    print_step_header(6, "元数据清理", "清理可能的元数据")
    print("🔄 开始清理元数据...")
    try:
        subprocess.run(['python', 'clean_final_txt.py'], check=True)
        print_success("元数据清理完成")
    except subprocess.CalledProcessError as e:
        print_error(f"元数据清理失败: {e}")
    except FileNotFoundError:
        print_error("未找到clean_final_txt.py脚本")

    # 完成
    print(f"\n{'='*60}")
    print("🎉 全部流程已完成！")
    print("📁 结果文件位置：")
    print(f"   📄 最终结果: {os.path.join(result_dir, 'final.txt')}")
    print(f"   📄 清理后结果: {os.path.join(result_dir, 'cleaned_final.txt')}")
    print(f"{'='*60}")

if __name__ == "__main__":
    main() 
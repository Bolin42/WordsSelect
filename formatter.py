from curses import meta
import os
import json
from typing import final
import re
def ReadValidWords():
    path = os.path.join('alicloud', 'input', '1.json')
    if not os.path.exists(path):
        print(f"文件不存在: {path}")
        return None
    with open(path, 'r', encoding='utf-8') as f:
        data = json.load(f)
        if "Data" in data:
            inner_data = json.loads(data["Data"])
            if "content" in inner_data:
                print("content readed")
                print("content data:",len(inner_data["content"]))
                return inner_data["content"]
            else:
                print("Data字段中无content")
                return None
        else:
            print("无Data字段")
            return None

def RemoveMetaInfo(text):
    RemoveNum = 0
    in_meta = False  # 是否处于元信息状态
    left_bracket = False
    buffer = []  # 主缓存区
    meta_buffer = []  # 元信息缓存区
    final_buffer = []  # 最终缓存区
    i = 0
    while i < len(text):
        char = text[i]
        if not in_meta:  # 未处于元信息状态
            if char == '（' or char == '(':
                in_meta = True
                left_bracket = True
                meta_buffer = [char]
            else:
                buffer.append(char)
        else:
            meta_buffer.append(char)
            # 判断括号是否闭合
            if (left_bracket and char == '）') or (left_bracket and char == ')'):
                in_meta = False
                meta_str = ''.join(meta_buffer)
                # 新增：括号内有2位数字和/的模式
                has_two_digit_and_slash = bool(re.search(r'\d{2}[^)]*/[^)]*', meta_str))
                # 原有：三个/且有汉字
                has_three_slash = meta_str.count('/') >= 2
                has_chinese = any('\u4e00' <= c <= '\u9fff' for c in meta_str)
                if (has_three_slash and has_chinese) or has_two_digit_and_slash:
                    meta_buffer.clear()
                    RemoveNum += 1
                else:
                    buffer.append(meta_str)
                final_buffer.extend(buffer)  # 追加buffer内容到final_buffer
                buffer.clear()
                meta_buffer.clear()
        i += 1
    # 处理剩余未入final_buffer的内容
    final_buffer.extend(buffer)
    print("Meta Info Removed")
    print("Remove ", RemoveNum, " Meta Info")
    return ''.join(final_buffer)

def PreprocessText(text):
    return text.replace('→', '')

NO_BREAK_PREFIXES = [
    "v.","vr.", "vt.", "vi.", "v.link.", "mod.", "aux.", "n.", "[c].", "[pl.]", "[Cpl.]", "[Csing.]", "[U].",
    "adj.", "adv.", "prep.", "pron."
]

def is_chinese(char):
    return '\u4e00' <= char <= '\u9fff'

def is_english(char):
    return char.isalpha()

def AddReturnSymbol(text):
    Times = 0
    if not text:
        return text

    text_no_space = text.replace(' ', '')
    result = []
    in_chinese = None
    i = 0  # 指向原文text
    j = 0  # 指向无空格text_no_space
    length = len(text)
    length_no_space = len(text_no_space)

    while i < length:
        char = text[i]
        # 跳过空格，只用于原文输出
        if char == ' ':
            result.append(char)
            i += 1
            continue

        char_no_space = text_no_space[j] if j < length_no_space else ''
        if is_chinese(char_no_space):
            current_is_chinese = True
        elif is_english(char_no_space):
            current_is_chinese = False
        else:
            current_is_chinese = in_chinese

        # 只在“中文→英文”时考虑换行
        if in_chinese is not None and in_chinese == True and current_is_chinese == False:
            lookahead = text_no_space[j:]
            k = 0
            while k < len(lookahead) and lookahead[k].isspace():
                k += 1
            if k < len(lookahead) and lookahead[k] in ('(', '（'):
                # 先append当前char
                result.append(char)
                # 插入换行符
                result.append('\n')
                Times += 1
                # 跳过空格，推进到括号
                i += 1
                j += 1
                # 继续append括号
                if i < length and text[i] in ('(', '（'):
                    result.append(text[i])
                    i += 1
                    j += 1
                # 继续后续循环
                continue
            else:
                matched = False
                for prefix in NO_BREAK_PREFIXES:
                    if lookahead.startswith(prefix):
                        matched = True
                        break
                if not matched:
                    result.append('\n')
                    Times += 1

        result.append(char)
        in_chinese = current_is_chinese
        i += 1
        j += 1  # 只在非空格时推进

    print("Return Symbol added")
    print("Add ", Times, " Return Symbols")
    return ''.join(result)

def remove_space_between_chinese(text):
    # 匹配“汉字 空格 汉字”，替换为“汉字汉字”
    return re.sub(r'(?<=[\u4e00-\u9fff])\s+(?=[\u4e00-\u9fff])', '', text)

def IOWrite(text):
    path = os.path.join('alicloud', 'output', '1.txt')
    if not os.path.exists(path):
        print(f"文件不存在: {path}")
        # 创建 output 目录和 1.txt 文件
        output_dir = os.path.join('alicloud', 'output')
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
        with open(path, 'w', encoding='utf-8') as f:
            f.write('')
        return None
    with open(path, 'w', encoding='utf-8') as f:
        f.write(text)
        print("Write to file successfully")
        f.close()

def process_single_json(json_path, txt_path):
    # 读取json，处理并写入txt
    with open(json_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
        if "Data" in data:
            inner_data = json.loads(data["Data"])
            if "content" in inner_data:
                text = inner_data["content"]
                preprocessed = PreprocessText(text)
                removed = RemoveMetaInfo(preprocessed)
                result = AddReturnSymbol(removed)
                result = remove_space_between_chinese(result)
                with open(txt_path, 'w', encoding='utf-8') as out:
                    out.write(result)
                print(f"已处理: {os.path.basename(json_path)} -> {os.path.basename(txt_path)}")
            else:
                print(f"Data字段中无content: {json_path}")
        else:
            print(f"无Data字段: {json_path}")

def get_first_letter_from_json(json_path):
    """从JSON文件中提取第一个单词的首字母"""
    try:
        with open(json_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            if "Data" in data:
                inner_data = json.loads(data["Data"])
                if "content" in inner_data:
                    text = inner_data["content"]
                    # 查找第一个英文单词
                    match = re.search(r'[a-zA-Z]+', text)
                    if match:
                        first_word = match.group(0)
                        return first_word[0].upper()  # 返回首字母的大写形式
    except Exception as e:
        print(f"提取首字母时出错: {e}")
    
    # 如果无法提取首字母，返回默认值
    return "OTHER"

def batch_process_json_to_txt(json_dir='json', txt_dir='txt', only_letter=None):
    if not os.path.exists(txt_dir):
        os.makedirs(txt_dir)
    subdirs = [d for d in os.listdir(json_dir) if os.path.isdir(os.path.join(json_dir, d))]
    subdirs.sort()
    for subdir in subdirs:
        if only_letter and subdir != only_letter:
            continue
        sub_json_dir = os.path.join(json_dir, subdir)
        sub_txt_dir = os.path.join(txt_dir, subdir)
        if not os.path.exists(sub_txt_dir):
            os.makedirs(sub_txt_dir)
<<<<<<< HEAD
        
        # 修复：递归查找所有JSON文件，处理嵌套目录结构
        json_files = []
        for root, dirs, files in os.walk(sub_json_dir):
            for file in files:
                if file.endswith('.json'):
                    json_files.append(os.path.join(root, file))
        
        # 按文件名排序
        json_files.sort(key=lambda x: (
            os.path.dirname(x), 
            int(os.path.splitext(os.path.basename(x))[0]) if os.path.splitext(os.path.basename(x))[0].isdigit() else os.path.basename(x)
        ))
        
        if not json_files:
            print(f"警告: {subdir} 文件夹下未找到JSON文件")
            continue
            
        print(f"处理 {subdir} 文件夹下 {len(json_files)} 个JSON文件...")
        for i, json_path in enumerate(json_files):
            # 生成对应的txt文件名
            relative_path = os.path.relpath(json_path, sub_json_dir)
            txt_filename = os.path.splitext(relative_path)[0] + '.txt'
            txt_path = os.path.join(sub_txt_dir, txt_filename)
            
            # 确保txt文件的目录存在
            txt_path_dir = os.path.dirname(txt_path)
            if not os.path.exists(txt_path_dir):
                os.makedirs(txt_path_dir)
                
            process_single_json(json_path, txt_path)
        
=======
        files = [f for f in os.listdir(sub_json_dir) if f.endswith('.json')]
        files.sort(key=lambda x: int(os.path.splitext(x)[0]) if os.path.splitext(x)[0].isdigit() else x)
        print(f"处理 {subdir} 文件夹下 {len(files)} 个JSON文件...")
        for fname in files:
            json_path = os.path.join(sub_json_dir, fname)
            txt_path = os.path.join(sub_txt_dir, os.path.splitext(fname)[0] + '.txt')
            process_single_json(json_path, txt_path)
>>>>>>> 8e7781ddd5932940ce6300496ab4a8827ce32409
        # 合并该首字母下所有txt为 result/首字母/首字母.txt
        result_dir = os.path.join('result', subdir)
        if not os.path.exists(result_dir):
            os.makedirs(result_dir)
<<<<<<< HEAD
        
        # 递归查找所有txt文件
        txt_files = []
        for root, dirs, files in os.walk(sub_txt_dir):
            for file in files:
                if file.endswith('.txt'):
                    txt_files.append(os.path.join(root, file))
        
        txt_files.sort()
        merged_path = os.path.join(result_dir, f'{subdir}.txt')
        with open(merged_path, 'w', encoding='utf-8') as outfile:
            for txt_file in txt_files:
                with open(txt_file, 'r', encoding='utf-8') as infile:
                    content = infile.read()
                    if content:  # 只写入非空内容
                        outfile.write(content)
                        outfile.write('\n')
=======
        txt_files = [f for f in os.listdir(sub_txt_dir) if f.endswith('.txt')]
        txt_files.sort(key=lambda x: int(os.path.splitext(x)[0]) if os.path.splitext(x)[0].isdigit() else x)
        merged_path = os.path.join(result_dir, f'{subdir}.txt')
        with open(merged_path, 'w', encoding='utf-8') as outfile:
            for fname in txt_files:
                file_path = os.path.join(sub_txt_dir, fname)
                with open(file_path, 'r', encoding='utf-8') as infile:
                    outfile.write(infile.read())
                    outfile.write('\n')
>>>>>>> 8e7781ddd5932940ce6300496ab4a8827ce32409
        print(f"✅ 已合并 {len(txt_files)} 个txt文件到: {merged_path}")

if __name__ == '__main__':
    batch_process_json_to_txt()
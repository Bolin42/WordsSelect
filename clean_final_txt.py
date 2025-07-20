# -*- coding: utf-8 -*-
"""
清理final.txt中括号内包含2位数字和/的内容
用法：直接运行，处理 result/final.txt，输出 result/cleaned_final.txt
"""
import re
import os

def clean_text(text):
    # 这里是原有的清理逻辑
    # 示例：去除中括号内容和数字
    text = re.sub(r'\[.*?\]', '', text)
    text = re.sub(r'\d+', '', text)
    return text

def clean_final_txt_all(result_dir='result'):
    subdirs = [d for d in os.listdir(result_dir) if os.path.isdir(os.path.join(result_dir, d))]
    subdirs.sort()
    for subdir in subdirs:
        file_path = os.path.join(result_dir, subdir, f'{subdir}.txt')
        output_path = os.path.join(result_dir, subdir, f'{subdir}_cleaned.txt')
        if not os.path.exists(file_path):
            print(f'跳过 {file_path}，文件不存在')
            continue
        with open(file_path, 'r', encoding='utf-8') as fin, \
             open(output_path, 'w', encoding='utf-8') as fout:
            for line in fin:
                cleaned = clean_text(line)
                fout.write(cleaned)
        print(f'✅ 已清理: {file_path} -> {output_path}')

if __name__ == '__main__':
    clean_final_txt_all('result') 
# -*- coding: utf-8 -*-
"""
删除所有括号及括号内内容（支持跨行），并删除所有阿拉伯数字与²等角标。
用法：python remove_brackets_and_digits.py --input 输入文件 --output 输出文件
"""
import re
import argparse

def remove_brackets_cross_lines(text):
    # 支持 ( ) 和 （ ）, 跨行
    lefts = ['(', '（']
    rights = [')', '）']
    stack = []
    remove_ranges = []
    for idx, char in enumerate(text):
        if char in lefts:
            stack.append(idx)
        elif char in rights and stack:
            start = stack.pop()
            end = idx
            remove_ranges.append((start, end))
    # 合并区间并删除
    if not remove_ranges:
        return text
    # 合并重叠区间
    remove_ranges.sort()
    merged = []
    for start, end in remove_ranges:
        if not merged or start > merged[-1][1]:
            merged.append([start, end])
        else:
            merged[-1][1] = max(merged[-1][1], end)
    # 构造新文本
    result = []
    last = 0
    for start, end in merged:
        result.append(text[last:start])
        last = end + 1
    result.append(text[last:])
    return ''.join(result)

def remove_digits_and_superscripts(text):
    # 删除所有阿拉伯数字和常见角标
    return re.sub(r'[0-9²³¹º¼½¾⅓⅔⅕⅖⅗⅘⅙⅚⅛⅜⅝⅞]', '', text)

def process_file(input_path, output_path):
    with open(input_path, 'r', encoding='utf-8') as fin:
        text = fin.read()
    text = remove_brackets_cross_lines(text)
    text = remove_digits_and_superscripts(text)
    with open(output_path, 'w', encoding='utf-8') as fout:
        fout.write(text)
    print(f"已处理：{input_path} -> {output_path}")

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='删除所有括号及括号内内容（支持跨行），删除所有阿拉伯数字与²等角标')
    parser.add_argument('--input', type=str, required=True, help='输入文件路径')
    parser.add_argument('--output', type=str, required=True, help='输出文件路径')
    args = parser.parse_args()
    process_file(args.input, args.output) 
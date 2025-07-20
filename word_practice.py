# -*- coding: utf-8 -*-
import sqlite3
import random
import argparse
from docx import Document
from docx.enum.table import WD_CELL_VERTICAL_ALIGNMENT

def fetch_words(db_path, table, count):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute(f"SELECT english, chinese FROM {table}")
    rows = cursor.fetchall()
    conn.close()
    
    if count == -1:
        # 提取所有单词
        print(f"提取表 {table} 的所有 {len(rows)} 条记录")
        return rows
    elif len(rows) < count:
        print(f"警告：表 {table} 仅有 {len(rows)} 条，已全部抽取。")
        return rows
    else:
        return random.sample(rows, count)

def make_underline(text, ratio=1.5, keep_semicolon=False):
    result = []
    for ch in text:
        if keep_semicolon and ch in ['；', ';']:
            result.append(ch)
        elif ch.strip() == '':
            result.append(' ')
        else:
            n = max(1, int(round(len(ch) * ratio)))
            result.append('_' * n)
    return ''.join(result)



def generate_docx(words, mode, output_path, shuffled_words=None):
    doc = Document()
    doc.add_heading('单词填词表', 0)
    table = doc.add_table(rows=1, cols=3)
    
    # 设置表格样式
    table.style = 'Table Grid'
    
    # 设置表头并垂直居中
    hdr_cells = table.rows[0].cells
    hdr_cells[0].text = '英文'
    hdr_cells[1].text = '词性'
    hdr_cells[2].text = '中文+提示'
    for cell in hdr_cells:
        cell.vertical_alignment = WD_CELL_VERTICAL_ALIGNMENT.CENTER
    
    # 使用传入的随机序列或生成新的
    if shuffled_words is None:
        shuffled_words = list(words)
        random.shuffle(shuffled_words)
    
    for item in shuffled_words:
        # 兼容不同数据结构
        if isinstance(item, dict):
            eng = item.get('english') or item.get('en') or ''
            pro = item.get('pos') or item.get('pro') or ''
            chn = item.get('chinese') or item.get('zh') or ''
            promt = item.get('promt') or ''
        else:
            # 兼容原有tuple结构
            if len(item) == 2:
                eng, chn = item
                pro = ''
                promt = ''
            elif len(item) == 3:
                eng, pro, chn = item
                promt = ''
            elif len(item) == 4:
                eng, pro, chn, promt = item
            else:
                eng = chn = pro = promt = ''
        if eng is None and chn is None:
            continue
        row_cells = table.add_row().cells
        for cell in row_cells:
            cell.vertical_alignment = WD_CELL_VERTICAL_ALIGNMENT.CENTER
            row_cells[0].text = str(eng) if eng else ''
        row_cells[1].text = str(pro) if pro else ''
        # 中文+promt
        chn_text = str(chn) if chn else ''
        if promt:
            chn_text += f'（{promt}）'
        row_cells[2].text = chn_text
    doc.save(output_path)
    print(f"已生成填词表（随机排序）：{output_path}")
    return shuffled_words

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='单词/词组抽取与填词表生成')
    parser.add_argument('--db', type=str, default='words.db', help='sqlite db文件')
    parser.add_argument('--letter', type=str, required=True, help='首字母表（如a、b、c）')
    parser.add_argument('--count', type=int, default=10, help='抽取数量（输入-1提取所有单词）')
    parser.add_argument('--mode', type=str, choices=['chinese', 'english', 'both'], nargs='+', default=['chinese'], help='填词表模式（可多个）')
    parser.add_argument('--output', type=str, nargs='+', default=['fill_table.docx'], help='输出docx文件名（可多个，与mode一一对应）')
    args = parser.parse_args()

    table = args.letter.lower()
    words = fetch_words(args.db, table, args.count)
    if not words:
        print(f"未找到任何数据，请检查表名和数据库内容。")
        exit(1)
    
    # 确保mode和output数量一致
    if len(args.mode) != len(args.output):
        print(f"错误：mode参数数量({len(args.mode)})与output参数数量({len(args.output)})不匹配")
        exit(1)
    
    # 生成相同的随机序列
    shuffled_words = list(words)
    random.shuffle(shuffled_words)
    
    # 为每个mode-output对生成docx文件
    for i, (mode, output) in enumerate(zip(args.mode, args.output)):
        print(f"\n生成第{i+1}个文件：模式={mode}, 输出={output}")
        generate_docx(words, mode, output, shuffled_words) 
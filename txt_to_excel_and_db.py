# -*- coding: utf-8 -*-
"""
将txt单词表自动分组导出到excel和sqlite db，支持括号跨行清理
"""
import re
import os
import pandas as pd
import sqlite3

# 词性列表
POS_LIST = [
    "v.","vr.", "vt.", "vi.", "v.link.", "mod.", "aux.", "n.", "[c].", "[pl.]", "[Cpl.]", "[Csing.]", "[U].",
    "adj.", "adv.", "prep.", "pron."
]

def remove_brackets_cross_lines(text):
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
    if not remove_ranges:
        return text
    remove_ranges.sort()
    merged = []
    for start, end in remove_ranges:
        if not merged or start > merged[-1][1]:
            merged.append([start, end])
        else:
            merged[-1][1] = max(merged[-1][1], end)
    result = []
    last = 0
    for start, end in merged:
        result.append(text[last:start])
        last = end + 1
    result.append(text[last:])
    return ''.join(result)

<<<<<<< HEAD
def clean_text_keep_punct(text):
    # 保留中英文的'.'和','，去除其他特殊字符
    import re
    # 允许的标点：英文. , 中文。 ，
    allowed = set('.，。,')
    # 替换为只保留字母、数字、汉字、空格和上述标点
    return ''.join(c for c in text if c.isalnum() or c.isspace() or c in allowed or '\u4e00' <= c <= '\u9fff')

def remove_inline_slash_content(line):
    # 丢弃英文部分的'/'与'/'之间内容，不跨行
    import re
    # 只处理一行内的/xxx/，不跨行
    # 例如：life-jacket /abc/ n. 救生衣 -> life-jacket  n. 救生衣
    return re.sub(r'/[^/\n]*/', '', line)


=======
>>>>>>> 8e7781ddd5932940ce6300496ab4a8827ce32409
def parse_line(line):
    # 支持一行多词性多中文解释的精确拆分，返回多行结构
    line = line.strip()
    if not line:
        return []
<<<<<<< HEAD
    # 先丢弃英文部分的/xxx/，不跨行
    line = remove_inline_slash_content(line)
    import re
    pos_pattern = r'(' + '|'.join([re.escape(p) for p in POS_LIST]) + r')'
    pos_matches = list(re.finditer(pos_pattern, line))
    results = []
    if pos_matches:
        # 原始英文部分为第一个词性前的内容
        first_pos_start = pos_matches[0].start(1)
        eng = line[:first_pos_start].strip()
        eng_clean = clean_text_keep_punct(eng) if eng else ''
        for i, m in enumerate(pos_matches):
            pos = m.group(1)
            pos_end = m.end(1)
            next_pos_start = pos_matches[i+1].start(1) if i+1 < len(pos_matches) else len(line)
            chn = line[pos_end:next_pos_start].strip()
            chn_clean = clean_text_keep_punct(chn) if chn else ''
            results.append({'english': eng_clean, 'pos': pos, 'chinese': chn_clean})
    else:
        # 没有词性，直接找中文
        chn_match = re.search(r'[\u4e00-\u9fff].*', line)
        chn = chn_match.group(0).strip() if chn_match else None
        eng_match = re.match(r'^([A-Za-z][A-Za-z\-\.\s\"]*)', line)
        eng = eng_match.group(1).strip() if eng_match else None
        eng_clean = clean_text_keep_punct(eng) if eng else ''
        chn_clean = clean_text_keep_punct(chn) if chn else ''
        results.append({'english': eng_clean, 'pos': '', 'chinese': chn_clean})
=======
    # 英文部分
    eng_match = re.match(r'^([A-Za-z][A-Za-z\s\-\"]*)', line)
    eng = eng_match.group(1).strip() if eng_match else None
    # 词性+中文解释部分
    rest = line[len(eng):] if eng else line
    # 匹配所有“词性. 中文”片段
    pos_chn_pattern = re.compile(r'((?:' + '|'.join([re.escape(p) for p in POS_LIST]) + r'))\s*([\u4e00-\u9fff][^' + ''.join([re.escape(p) for p in POS_LIST]) + r']*)')
    matches = list(pos_chn_pattern.finditer(rest))
    results = []
    if matches:
        for m in matches:
            pos = m.group(1).strip()
            chn = m.group(2).strip()
            results.append({'english': eng, 'pos': pos, 'chinese': chn})
    else:
        # 没有词性，直接找中文
        chn_match = re.search(r'[\u4e00-\u9fff].*', rest)
        chn = chn_match.group(0).strip() if chn_match else None
        results.append({'english': eng, 'pos': '', 'chinese': chn})
>>>>>>> 8e7781ddd5932940ce6300496ab4a8827ce32409
    return results

def process_txt(input_path):
    # 先整体清理括号（支持跨行）
    with open(input_path, 'r', encoding='utf-8') as f:
        text = f.read()
    text = remove_brackets_cross_lines(text)
    lines = text.splitlines()
    # 解析
    records = []
    for line in lines:
        parsed_list = parse_line(line)
        for parsed in parsed_list:
            if parsed:
                records.append(parsed)
    return records

def remove_duplicates(records):
    """只有英文和中文都重复时才去重"""
    seen = set()
    unique_records = []
    duplicates_count = 0
    
    for record in records:
        english = (record.get('english') or '').strip().lower()
        chinese = (record.get('chinese') or '').strip()
        key = (english, chinese)
        if english and chinese and key not in seen:
            seen.add(key)
            unique_records.append(record)
        elif english and chinese:
            duplicates_count += 1
        else:
            # 如果英文或中文为空，直接保留
            unique_records.append(record)
    
    return unique_records, duplicates_count

def process_folder(input_folder):
    """只处理 input_folder/首字母/首字母.txt 文件"""
    all_tables = {}
    if not os.path.exists(input_folder):
        print(f"错误：文件夹 {input_folder} 不存在")
        return all_tables
    subdirs = [d for d in os.listdir(input_folder) if os.path.isdir(os.path.join(input_folder, d))]
    subdirs.sort()
    for subdir in subdirs:
        sub_path = os.path.join(input_folder, subdir)
        target_file = os.path.join(sub_path, f'{subdir}.txt')
        if not os.path.exists(target_file):
            print(f"跳过 {target_file}，文件不存在")
            continue
        print(f"处理文件：{target_file} -> 表名：{subdir}")
        try:
            records = process_txt(target_file)
            if records:
                unique_records, duplicates_count = remove_duplicates(records)
                all_tables[subdir] = unique_records
                print(f"  ✅ 成功解析 {len(records)} 条记录，去重后 {len(unique_records)} 条（移除 {duplicates_count} 条重复）")
            else:
                print(f"  ⚠️  文件 {target_file} 没有解析到有效记录")
        except Exception as e:
            print(f"  ❌ 处理文件 {target_file} 时出错：{e}")
    return all_tables

def group_by_first_letter(records):
    groups = {}
    for rec in records:
        eng = rec['english']
        if not eng:
            continue
        first = eng[0].lower()
        if not ('a' <= first <= 'z'):
            continue
        if first not in groups:
            groups[first] = []
        groups[first].append(rec)
    return groups

def enhance_records(records, table_letter=None):
    # 增加index、type、num、promt、pro列，en/zh/promt/num/type/pro
    enhanced = []
    for rec in records:
        eng = rec.get('english', '') or ''
        zh = rec.get('chinese', '') or ''
        pro = rec.get('pos', '') or ''
        # Type判定
        if '.' in eng:
            typ = 1
        else:
            words = eng.split()
            if len(words) == 1:
                typ = 0
            elif len(words) > 1:
                typ = -1
            else:
                typ = 0
        # 只保留en本体，不带词性
        en_clean = eng.strip()
        # 提示词逻辑：对于Type=-1/1，查找en中以table_letter为首字母的单词
        promt = ''
        if typ in (-1, 1) and table_letter:
            found = [w for w in en_clean.split() if w.lower().startswith(table_letter.lower())]
            promt = ','.join(found)
        enhanced.append({
            'en': en_clean,
            'zh': zh,
            'promt': promt,
            'num': 0,
            'type': typ,
            'pro': pro
        })
    # index列最后统一编号
    for idx, row in enumerate(enhanced, 1):
        row['index'] = idx
    # 保证列顺序
    cols = ['index', 'en', 'zh', 'promt', 'num', 'type', 'pro']
    enhanced = [{k: row.get(k, '') for k in cols} for row in enhanced]
    return enhanced

def export_to_excel(all_tables, output_path):
    with pd.ExcelWriter(output_path) as writer:
        for table_name, records in all_tables.items():
            enhanced = enhance_records(records, table_letter=table_name)
            df = pd.DataFrame(enhanced)
            df.to_excel(writer, sheet_name=table_name, index=False)
    print(f"已导出到Excel: {output_path}")

def export_to_db(all_tables, db_path):
    conn = sqlite3.connect(db_path)
    for table_name, records in all_tables.items():
        enhanced = enhance_records(records, table_letter=table_name)
        df = pd.DataFrame(enhanced)
        df.to_sql(table_name, conn, if_exists='replace', index=False)
        print(f"  ✅ 创建表：{table_name} ({len(df)} 条记录)")
    conn.close()
    print(f"已导出到数据库: {db_path}")

def detect_type(eng):
    eng = eng.strip()
    if '.' in eng:
        return 1  # 句子
    words = eng.split()
    if len(words) == 1:
        return 0  # 单词
    elif len(words) > 1:
        return -1  # 词组
    return 0

def process_txt_file(txt_path):
    # 假设每行格式：中文\t英文
    data = []
    with open(txt_path, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            if '\t' in line:
                zh, en = line.split('\t', 1)
            else:
                zh, en = '', line
            data.append({'zh': zh, 'en': en})
    # 生成DataFrame
    df = pd.DataFrame(data)
    if df.empty:
        return df
    # 生成Type列
    df['Type'] = df['en'].apply(detect_type)
    # 生成index列
    df['index'] = range(1, len(df)+1)
    # 生成Num列
    df['Num'] = 0
    # 处理词组/句子的中文加括号单词
    last_word = ''
    zh_list = df['zh'].tolist()
    en_list = df['en'].tolist()
    type_list = df['Type'].tolist()
    for i in range(len(df)):
        if type_list[i] == 0:
            # 记录最近的单词
            last_word = en_list[i].strip()
        elif type_list[i] in (-1, 1) and last_word:
            # 在中文后加括号单词
            zh_list[i] = zh_list[i] + f'（{last_word}）'
    df['zh'] = zh_list
    return df[['index', 'zh', 'en', 'Type', 'Num']]

def batch_txt_to_excel_and_db(txt_dir='txt', excel_path='words.xlsx', db_path='words.db'):
    writer = pd.ExcelWriter(excel_path, engine='xlsxwriter')
    conn = sqlite3.connect(db_path)
    subdirs = [d for d in os.listdir(txt_dir) if os.path.isdir(os.path.join(txt_dir, d))]
    subdirs.sort()
    for subdir in subdirs:
        sub_txt_dir = os.path.join(txt_dir, subdir)
        target_file = os.path.join(sub_txt_dir, f'{subdir}.txt')
        if not os.path.exists(target_file):
            print(f"跳过 {target_file}，文件不存在")
            continue
        df = process_txt_file(target_file)
        if not df.empty:
            # 重新编号index
            df['index'] = range(1, len(df)+1)
            # 写入Excel
            df.to_excel(writer, sheet_name=subdir, index=False)
            # 写入数据库
            df.to_sql(subdir, conn, if_exists='replace', index=False)
            print(f"✅ 已处理 {target_file}")
        else:
            print(f"⚠️  {target_file} 无有效内容")
    writer.close()
    conn.close()

if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(description='txt单词表批量导出到excel和db')
    parser.add_argument('--input', type=str, required=True, help='输入文件夹路径')
    parser.add_argument('--excel', type=str, default='words.xlsx', help='输出excel文件')
    parser.add_argument('--db', type=str, default='words.db', help='输出sqlite db文件')
    args = parser.parse_args()

    all_tables = process_folder(args.input)
    if all_tables:
        export_to_excel(all_tables, args.excel)
        export_to_db(all_tables, args.db)
    else:
        print("没有处理到任何文件，退出。") 
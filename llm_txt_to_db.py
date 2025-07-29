import argparse
import concurrent.futures
import requests
import sqlite3
import os
from tqdm import tqdm

def call_llm_api(batch_lines, api_key):
    prompt = (
        "请将以下单词原始文本纠错并分割为标准格式，每行一个单词，格式为：英文 词性. 中文。"
        "如果原始内容有格式错误、缺失、顺序混乱、缺少词性等，请自动补全和修正。"
        "示例：\n"
        "abandon vt. 放弃\n"
        "ability n. 能力\n"
        "如果有多词性或多义项，请分多行输出。不要输出多余解释和说明，只输出修正后的内容。\n"
        "原始内容如下：\n"
        + '\n'.join(batch_lines) +
        "\n请严格按照上述格式输出。"
    )
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    data = {
        "model": "deepseek/deepseek-v3-base:free",
        "messages": [
            {"role": "system", "content": "你是一个英语单词表格式修正与分割助手。"},
            {"role": "user", "content": prompt}
        ],
        "max_tokens": 2048,
        "temperature": 0.2
    }
    resp = requests.post("https://openrouter.ai/api/v1/chat/completions", headers=headers, json=data, timeout=120)
    resp.raise_for_status()
    result = resp.json()
    return result["choices"][0]["message"]["content"]

def parse_llm_result(result_txt):
    records = []
    for line in result_txt.splitlines():
        line = line.strip()
        if not line:
            continue
        # 只处理“英文 词性. 中文”格式
        parts = line.split(' ', 1)
        if len(parts) == 2:
            en, rest = parts
            if '.' in rest:
                pos, zh = rest.split('.', 1)
                records.append({'en': en, 'pro': pos.strip() + '.', 'zh': zh.strip()})
    return records

def write_to_db(records, db_path, table):
    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    c.execute(f'''CREATE TABLE IF NOT EXISTS {table} (
        en TEXT, pro TEXT, zh TEXT
    )''')
    for rec in records:
        c.execute(f'INSERT INTO {table} (en, pro, zh) VALUES (?, ?, ?)', (rec['en'], rec['pro'], rec['zh']))
    conn.commit()
    conn.close()

def main(txt_path, db_path, api_key, table='words'):
    with open(txt_path, 'r', encoding='utf-8') as f:
        lines = [line.strip() for line in f if line.strip()]
    batches = [lines[i:i+100] for i in range(0, len(lines), 100)]
    all_records = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
        futures = [executor.submit(call_llm_api, batch, api_key) for batch in batches]
        for fut in tqdm(concurrent.futures.as_completed(futures), total=len(futures), desc='大模型分割中'):
            result_txt = fut.result()
            all_records.extend(parse_llm_result(result_txt))
    write_to_db(all_records, db_path, table)
    print(f'已写入{len(all_records)}条记录到{db_path}')

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='大模型纠错+分割+入库')
    parser.add_argument('--input', type=str, required=True, help='输入txt文件')
    parser.add_argument('--db', type=str, required=True, help='输出sqlite db文件')
    parser.add_argument('--table', type=str, default='words', help='表名')
    parser.add_argument('--api_key', type=str, required=True, help='OpenRouter API KEY')
    args = parser.parse_args()
    main(args.input, args.db, args.api_key, args.table) 
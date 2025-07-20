import os
import json
import re
import sqlite3
import argparse
import csv
import traceback
from collections import defaultdict

def safe_json_loads(data):
    """安全解析JSON数据，处理可能的格式问题"""
    try:
        return json.loads(data)
    except json.JSONDecodeError:
        # 尝试修复常见的格式问题
        fixed_data = re.sub(r'([{\[,])\s*([a-zA-Z_][a-zA-Z0-9_]*)\s*:', r'\1"\2":', data)
        fixed_data = re.sub(r':\s*([a-zA-Z_][a-zA-Z0-9_]*)\s*([,\]}])', r':"\1"\2', fixed_data)
        return json.loads(fixed_data)

def parse_entry(entry_text):
    """解析单个词汇条目，返回结构化数据"""
    # 提取英文部分（可能包含多个单词）
    english_part = ""
    for match in re.finditer(r'[a-zA-Z][a-zA-Z\s\-\'\.]*[a-zA-Z]', entry_text):
        if not english_part:  # 只取第一个连续英文部分作为主词
            english_part = match.group(0).strip()
    
    if not english_part:
        return None
    
    # 提取所有词性标签
    pos_tags = []
    pos_matches = re.findall(r'(\b[a-z]+\.(?:/[a-z]+\.)*)', entry_text.lower())
    for match in pos_matches:
        # 分割组合词性如"n./v."
        combined = [p for p in match.split('/') if p.endswith('.')]
        pos_tags.extend(combined)
    
    # 如果没有显式词性标签，尝试推断
    if not pos_tags:
        if re.search(r'[a-z]+\s*[\u4e00-\u9fa5]', entry_text):
            pos_tags = ['unk.']  # 未知词性
    
    # 提取所有中文释义
    chinese_definitions = []
    # 匹配中文（包括中文标点）
    chinese_blocks = re.findall(r'[\u4e00-\u9fa5][\u4e00-\u9fa5，；、：（）《》【】\s\.]*', entry_text)
    
    for block in chinese_blocks:
        # 按分号分割多个释义
        definitions = re.split(r'[；;]', block)
        for definition in definitions:
            cleaned = definition.strip()
            if cleaned:
                # 分离词性和释义（如"n.地标"）
                if re.match(r'^[a-z]+\.', cleaned):
                    pos_part, _, def_text = cleaned.partition('.')
                    if def_text:
                        pos_tags.append(pos_part + '.')
                        cleaned = def_text.strip()
                
                chinese_definitions.append(cleaned)
    
    # 组织数据结构
    result = defaultdict(lambda: defaultdict(list))
    if not pos_tags:
        # 没有词性信息，所有释义归为同一词性
        result[english_part]['unk.'] = chinese_definitions
    else:
        # 每个词性都对应所有中文释义
        for pos in set(pos_tags):  # 去重
            result[english_part][pos] = chinese_definitions
    
    return dict(result)

def process_json_file(json_path):
    """处理单个JSON文件，提取所有词汇条目"""
    try:
        with open(json_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # 安全解析内层JSON数据
        inner_data = safe_json_loads(data['Data'])
        rows = inner_data['prism_rowsInfo']
        
        # 合并连续行形成完整条目
        entries = []
        current_entry = []
        
        for row in rows:
            text = row['word'].strip()
            if not text:
                continue
            
            # 新条目开始（以箭头→或英文开头）
            if re.match(r'^(→)?[a-zA-Z]', text):
                if current_entry:
                    entries.append(" ".join(current_entry))
                    current_entry = []
            
            current_entry.append(text)
        
        if current_entry:
            entries.append(" ".join(current_entry))
        
        # 解析所有条目
        vocabulary = {}
        for entry in entries:
            parsed = parse_entry(entry)
            if parsed:
                for eng, pos_data in parsed.items():
                    if eng not in vocabulary:
                        vocabulary[eng] = {}
                    
                    for pos, chn_list in pos_data.items():
                        if pos not in vocabulary[eng]:
                            vocabulary[eng][pos] = []
                        
                        # 添加新释义，避免重复
                        for chn in chn_list:
                            if chn not in vocabulary[eng][pos]:
                                vocabulary[eng][pos].append(chn)
        
        return vocabulary
    
    except Exception as e:
        print(f"  处理文件 {json_path} 时出错: {str(e)}")
        traceback.print_exc()
        return {}

def init_database(db_path):
    """初始化数据库并创建表"""
    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    
    # 创建表（如果不存在）
    c.execute('''CREATE TABLE IF NOT EXISTS vocabulary (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    english TEXT NOT NULL,
                    pos TEXT NOT NULL,
                    chinese TEXT NOT NULL,
                    source_file TEXT,
                    UNIQUE(english, pos, chinese)
                )''')
    
    # 创建索引
    c.execute("CREATE INDEX IF NOT EXISTS idx_english ON vocabulary (english)")
    c.execute("CREATE INDEX IF NOT EXISTS idx_pos ON vocabulary (pos)")
    c.execute("CREATE INDEX IF NOT EXISTS idx_chinese ON vocabulary (chinese)")
    
    conn.commit()
    conn.close()

def save_to_database(data, db_path, source_file):
    """将词汇数据保存到SQLite数据库"""
    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    
    # 插入数据
    total_count = 0
    for eng, pos_data in data.items():
        for pos, chn_list in pos_data.items():
            for chn in chn_list:
                try:
                    c.execute('''INSERT OR IGNORE INTO vocabulary 
                                (english, pos, chinese, source_file) 
                                VALUES (?, ?, ?, ?)''',
                             (eng, pos, chn, source_file))
                    total_count += 1
                except sqlite3.IntegrityError:
                    pass  # 忽略重复条目
    
    conn.commit()
    conn.close()
    return total_count

def export_to_csv(db_path, csv_path):
    """从数据库导出为CSV文件"""
    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    
    # 查询所有数据
    c.execute("SELECT english, pos, chinese, source_file FROM vocabulary ORDER BY english, pos")
    rows = c.fetchall()
    
    # 写入CSV
    with open(csv_path, 'w', newline='', encoding='utf-8-sig') as f:
        writer = csv.writer(f)
        writer.writerow(['英文', '词性', '中文释义', '来源文件'])
        writer.writerows(rows)
    
    conn.close()
    return len(rows)

def process_folder(folder_path, output_db):
    """处理文件夹中的所有JSON文件"""
    # 获取所有JSON文件并按数字排序
    files = [f for f in os.listdir(folder_path) if f.endswith('.json')]
    
    # 按文件名中的数字排序
    def extract_number(filename):
        match = re.search(r'(\d+)', filename)
        return int(match.group(1)) if match else 0
    
    files.sort(key=extract_number)
    
    # 初始化数据库
    if os.path.exists(output_db):
        # 备份旧数据库
        backup_db = os.path.splitext(output_db)[0] + "_backup.db"
        os.rename(output_db, backup_db)
        print(f"已备份旧数据库到: {backup_db}")
    
    # 创建数据库表结构
    init_database(output_db)
    print("已初始化数据库结构")
    
    total_entries = 0
    processed_files = 0
    
    for filename in files:
        json_path = os.path.join(folder_path, filename)
        print(f"处理文件: {filename}")
        
        try:
            # 解析JSON文件
            vocab_data = process_json_file(json_path)
            
            if vocab_data:
                # 保存到数据库
                count = save_to_database(vocab_data, output_db, filename)
                total_entries += count
                print(f"  添加 {count} 个词汇条目")
                processed_files += 1
            else:
                print("  未提取到有效词汇数据")
            
        except Exception as e:
            print(f"  处理出错: {str(e)}")
    
    # 导出CSV
    csv_path = os.path.splitext(output_db)[0] + ".csv"
    csv_count = export_to_csv(output_db, csv_path)
    
    print(f"\n处理完成! 共处理 {processed_files} 个文件")
    print(f"添加 {total_entries} 个词汇条目")
    print(f"数据库已保存到: {output_db}")
    print(f"CSV文件已导出到: {csv_path}")
    print(f"总记录数: {csv_count}")

def query_database(db_path, search_term):
    """在数据库中搜索词汇"""
    if not os.path.exists(db_path):
        print(f"错误: 数据库文件 '{db_path}' 不存在")
        return
    
    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    
    # 判断搜索类型
    if re.search(r'[\u4e00-\u9fa5]', search_term):
        # 中文搜索
        c.execute("SELECT english, pos, chinese, source_file FROM vocabulary WHERE chinese LIKE ?", 
                 (f'%{search_term}%',))
    else:
        # 英文搜索
        c.execute("SELECT english, pos, chinese, source_file FROM vocabulary WHERE english LIKE ?", 
                 (f'%{search_term}%',))
    
    results = c.fetchall()
    
    if not results:
        print("未找到匹配结果")
        return
    
    print(f"\n找到 {len(results)} 条匹配记录:")
    print("-" * 80)
    for i, (eng, pos, chn, source) in enumerate(results, 1):
        print(f"{i}. {eng} ({pos}) - {chn} (来源: {source})")
    print("-" * 80)
    
    conn.close()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='英语词汇解析与存储系统')
    parser.add_argument('command', choices=['process', 'search'], help='命令: process-处理文件夹, search-搜索数据库')
    parser.add_argument('--input', help='JSON文件夹路径(用于process命令)')
    parser.add_argument('--db', default='vocabulary.db', help='SQLite数据库路径(默认: vocabulary.db)')
    parser.add_argument('--term', help='搜索关键词(用于search命令)')
    
    args = parser.parse_args()
    
    if args.command == 'process':
        if not args.input:
            print("错误: 请使用 --input 指定JSON文件夹路径")
            exit(1)
            
        if not os.path.exists(args.input) or not os.path.isdir(args.input):
            print(f"错误: 文件夹 '{args.input}' 不存在或不是目录")
            exit(1)
            
        process_folder(args.input, args.db)
        
    elif args.command == 'search':
        if not args.term:
            print("错误: 请使用 --term 指定搜索关键词")
            exit(1)
            
        query_database(args.db, args.term)
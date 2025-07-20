# recover.py
import os
import requests
import time
from dotenv import load_dotenv

# 加载.env中的API_KEY
load_dotenv()
API_KEY = os.getenv("OPENROUTER_API_KEY")
if not API_KEY:
    raise RuntimeError("请在.env文件中设置OPENROUTER_API_KEY=你的key")

API_URL = "https://openrouter.ai/api/v1/chat/completions"
MODEL = "deepseek/deepseek-v3-base:free"

def call_deepseek_api(content):
    prompt = (
        "请将以下单词表内容修正为标准格式，每行一个单词，格式为：英文 词性. 中文。"
        "如果原始内容有格式错误、缺失、顺序混乱、缺少词性等，请自动补全和修正。"
        "示例：\n"
        "abandon vt. 放弃\n"
        "ability n. 能力\n"
        "如果有多词性或多义项，请分多行输出。不要输出多余解释和说明，只输出修正后的内容。\n"
        "原始内容如下：\n"
        f"{content}\n"
        "请严格按照上述格式输出。"
    )
    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json"
    }
    data = {
        "model": MODEL,
        "messages": [
            {"role": "system", "content": "你是一个英语单词表格式修正助手。"},
            {"role": "user", "content": prompt}
        ],
        "max_tokens": 2048,
        "temperature": 0.2
    }
    resp = requests.post(API_URL, headers=headers, json=data, timeout=60)
    resp.raise_for_status()
    result = resp.json()
    return result["choices"][0]["message"]["content"]

def process_file(file_path, out_path=None):
    with open(file_path, "r", encoding="utf-8") as f:
        content = f.read()
    try:
        fixed = call_deepseek_api(content)
        if out_path is None:
            out_path = file_path
        with open(out_path, "w", encoding="utf-8") as f:
            f.write(fixed.strip() + "\n")
        print(f"✅ 修正完成: {file_path}")
    except Exception as e:
        print(f"❌ 修正失败: {file_path}，原因: {e}")

def main():
    root = "result"
    for subdir, _, files in os.walk(root):
        for file in files:
            if file.endswith(".txt"):
                file_path = os.path.join(subdir, file)
                process_file(file_path)
                time.sleep(1)  # 防止API限流

if __name__ == "__main__":
    main()
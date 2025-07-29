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
<<<<<<< HEAD
        "请将以下单词表内容修正为标准格式，每行一个单词，格式如下：。\n"
        "每一行都由个元素组成，分别为：\n"
        "en：英文单词/词组/句子\n"
        "zh：中文释义，如果中文释义中间存在分号，则分号分割了2个不同的释义。\n"
        "pro：词性（注：只有单词有词性，词组与句子的词性设为NULL）\n"
        "type：en类型（注：句子的type为1,单词的type为0,词组的type为-1）\n"
        "promt：对于type为词组和句子的en,根据上文（不查找下文）找出最有可能的原单词，即该词组中保有的最低有效提示单词\n"
        "如果原始内容有格式错误、缺失、顺序混乱、缺少词性等，请自动补全和修正。\n"
        "同时，对于多个解释，请另起一行，重复英文，并继续输出相关内容。其中“/”之间可能混有音标，这个不管，直接丢弃。\n"
        "单词性、单释义示例：\n"
        "|abandon|放弃|vt.|0|NULL|\n"
        "多词性、多释义示例：\n"
        "输入为：contrary/'kontrari/ n./adj. 相反\n 输出为：\n"
        "|contrary|相反|n.|0|NULL|\n"
        "|contrary|相反|adj.|0|NULL|\n"
        "单词性、多释义示例：\n"
        "输入为：consume /ken'sju:m/ vt.消费；吃，喝；消耗\n"
        "输出为：\n |consume|消费|vt.|0|NULL|\n |consume|吃，喝|vt.|0|NULL|\n |consume|消耗|vt.|0|NULL|\n"
        "词组示例：\n"
        "|consider doing|考虑做……|NULL|-1|consider|\n"
        "句子示例：\n"
        "|As we get older, we often find it difficult to understand music.|年龄增长时，我们常常发现难以理解音乐。|NULL|1|understand|\n"
        "如果有多词性或多义项，请分多行输出。不要输出多余解释和说明，只输出修正后的内容。\n"
        "每一列由"|"分割，"|"与内容之间不要添加空格\n"
=======
        "请将以下单词表内容修正为标准格式，每行一个单词，格式为：英文 词性. 中文。"
        "如果原始内容有格式错误、缺失、顺序混乱、缺少词性等，请自动补全和修正。"
        "示例：\n"
        "abandon vt. 放弃\n"
        "ability n. 能力\n"
        "如果有多词性或多义项，请分多行输出。不要输出多余解释和说明，只输出修正后的内容。\n"
>>>>>>> 8e7781ddd5932940ce6300496ab4a8827ce32409
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
# WordsSelect 英语单词智能提取与练习系统

> 一站式从图片到单词表、数据库、练习文档的全流程自动化工具箱

---

## 🌟 项目简介

WordsSelect 是一个集图片批量处理、OCR识别、单词结构化提取、AI自动修正、格式化导出、单词练习表生成于一体的高效工具集。适用于英语学习、单词整理、教材数字化等多场景。

---

## 📂 目录结构

```
WordsSelect/
├── input/         # 原始图片（按字母分文件夹）
├── processed/     # 预处理后图片
├── json/          # OCR识别结果（JSON）
├── txt/           # 结构化单词txt（按字母分文件夹）
├── result/        # 合并后的单词txt（按字母分文件夹）
├── output/        # 其他输出
├── main.py        # 主流程入口
├── image_process.py         # 图片预处理
├── ocr_alicloud.py          # 阿里云OCR批量识别
├── formatter.py             # JSON转txt格式化
├── extract_words.py         # 复杂单词提取
├── txt_to_excel_and_db.py   # txt批量导出Excel/DB
├── word_practice.py         # 单词练习表生成
├── recover.py               # AI自动修正单词表
├── clean_final_txt.py       # 批量清理括号/数字
├── remove_brackets_and_digits.py # 批量去括号和数字
├── requirements.txt         # 依赖包
└── README.md                # 说明文档
```

---

## 🚀 全流程使用教程

### 1. 环境准备

```bash
pip install -r requirements.txt
# 若需AI修正，额外安装
pip install requests python-dotenv
```

### 2. 图片准备
- 将待处理的扫描图片按首字母分文件夹放入 `input/` 目录。

### 3. 图片预处理
```bash
python main.py
```
- 按提示完成图片裁剪、拼接、奇偶页选择。
- 自动完成图片数量校验、OCR识别、JSON转txt、合并txt。

### 4. AI自动修正（可选，强烈推荐）
- 需注册 [OpenRouter](https://openrouter.ai/) 并获取免费API Key。
- 在根目录新建 `.env` 文件，内容如下：
  ```
  OPENROUTER_API_KEY=sk-xxxxxxx
  ```
- 运行：
  ```bash
  python recover.py
  ```
- 自动遍历 `result/` 下所有txt，修正为标准格式（英文 词性. 中文），适配后续导出。

### 5. txt批量导出Excel/数据库
```bash
python txt_to_excel_and_db.py --input result --excel words.xlsx --db words.db
```
- 支持自动去重、分组、格式增强。
- 生成 `words.xlsx`（多sheet）和 `words.db`（多表）。

### 6. 单词练习表生成
```bash
python word_practice.py --db word_h_l.db --letter h l k --mode chinese
```
- 支持多种模式，输出美观的四列表格（序号/英文/词性/中文+提示）。
- 会自动生成 `<letter>_<mode>.docx` 和 `<letter>_key.docx` 文件。

#### 参数说明
| 参数         | 说明                                                                                 |
|--------------|--------------------------------------------------------------------------------------|
| --db         | 必填，指定sqlite数据库文件路径。                                                     |
| --letter     | 必填，支持一个或多个首字母（如 a b c），批量生成多组练习表。                         |
| --count      | 可选，抽取数量，-1为全部（默认10）。                                                 |
| --mode       | 可选，生成模式，支持 chinese/english/both，可多选（如 --mode chinese english）。      |
| --output     | 可选，输出文件名列表，若不指定则自动按 <letter>_<mode>.docx 命名。                   |

- 每个首字母的填词表和答案表用同一随机序列，但不同首字母之间随机序列独立。
- 填词表（mode=chinese）英文列为等长空格，中文列为“中文+提示词”；key答案表只显示真实英文和中文。

**示例：**
```bash
python word_practice.py --db word_h_l.db --letter h l --mode chinese english
```
会生成：
- h_chinese.docx, h_english.docx, h_key.docx
- l_chinese.docx, l_english.docx, l_key.docx

### 7. 其他批量清理工具
- `
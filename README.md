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
python word_practice.py --db words.db --letter a --count 20 --mode chinese --output a练习.docx
```
- 支持多种模式，输出美观的三列表格（英文/词性/中文+提示）。

### 7. 其他批量清理工具
- `clean_final_txt.py`：批量清理括号和数字。
- `remove_brackets_and_digits.py`：去除所有括号及内容、数字。

---

## 🧩 各脚本功能说明

- **main.py**：一键式主流程，涵盖图片→OCR→结构化→合并。
- **image_process.py**：图片批量裁剪、拼接、奇偶页处理。
- **ocr_alicloud.py**：阿里云OCR批量识别，输出结构化JSON。
- **formatter.py**：JSON转txt，自动格式化、合并。
- **extract_words.py**：复杂OCR结果的单词/释义/词性提取。
- **txt_to_excel_and_db.py**：批量txt导出Excel/DB，自动分组、去重、增强。
- **word_practice.py**：从数据库抽取单词，生成三列表格练习文档（.docx）。
- **recover.py**：AI自动修正单词表，调用OpenRouter DeepSeek免费API。
- **clean_final_txt.py**、**remove_brackets_and_digits.py**：批量清理文本杂质。

---

## 📝 标准单词表格式

每行：
```
英文 词性. 中文
```
- 支持多词性/多义项分多行
- 词性如：n. v. adj. adv. prep. pron. 等
- 示例：
  ```
  abandon vt. 放弃
  ability n. 能力
  account n. 账户
  account vi. 解释
  ```

---

## ❓ 常见问题与建议

- **OCR识别不准？**
  - 检查图片清晰度，适当调整预处理参数。
  - 可用AI修正脚本自动补全格式。
- **AI修正失败/超时？**
  - 检查API Key，适当降低并发，或分批处理。
- **导出Excel/DB乱码？**
  - 确保文件编码为UTF-8。
- **如何自定义词性/格式？**
  - 修改 `txt_to_excel_and_db.py` 的 `POS_LIST`。

---

## 🔒 .gitignore

- 已默认忽略 `.env`（API密钥）和 `node_modules`。

---

## 📑 许可证

本项目仅供学习和研究使用，严禁用于商业用途。

---

> 如有问题或建议，欢迎提Issue或PR！ 
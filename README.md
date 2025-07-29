# WordsSelect 英语单词智能提取与练习系统

> 一站式从图片到单词表、数据库、练习文档的全流程自动化工具箱

![版本](https://img.shields.io/badge/版本-1.0.0-blue)
![Python](https://img.shields.io/badge/Python-3.8+-green)
![许可证](https://img.shields.io/badge/许可证-MIT-orange)

## 📚 项目简介

WordsSelect 是一个集图片批量处理、OCR识别、单词结构化提取、AI自动修正、格式化导出、单词练习表生成于一体的高效工具集。适用于英语学习、单词整理、教材数字化等多场景。

## 🔍 功能特点

- **批量OCR识别**：利用阿里云OCR API自动识别扫描图片中的文本
- **智能分类整理**：按首字母自动分类存储
- **AI智能修正**：接入免费大模型自动修正OCR识别错误
- **结构化导出**：支持Excel、SQLite数据库等多种格式
- **练习表生成**：自动生成美观的单词练习表和答案表
- **全流程自动化**：从图片到练习表一站式解决方案

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
├── ai_processor.py          # AI智能处理
├── txt_to_excel_and_db.py   # txt批量导出Excel/DB
├── word_practice.py         # 单词练习表生成
├── recover.py               # AI自动修正单词表
├── clean_final_txt.py       # 批量清理括号/数字
├── remove_brackets_and_digits.py # 批量去括号和数字
├── requirements.txt         # 依赖包
└── README.md                # 说明文档
```

## 🚀 使用流程

### 📋 AI智能模式（推荐，适合大样本批量处理）

> ⚠️ **注意**：AI智能模式配置过程相对繁琐，但处理效率高。智能处理可能导致一些字段丢失，请注意核对。

#### 1️⃣ 配置阿里云OCR API

1. 注册[阿里云账号](https://www.aliyun.com/)并开通OCR服务
2. 获取AccessKey ID和AccessKey Secret
3. 配置环境变量或在代码中直接设置密钥

```bash
# 在系统中设置环境变量
export ALIBABA_CLOUD_ACCESS_KEY_ID="your_access_key_id"
export ALIBABA_CLOUD_ACCESS_KEY_SECRET="your_access_key_secret"
```

> ⚠️ **重要提示**：阿里云OCR每月有200次免费额度，超出需付费。具体政策请以阿里云官方最新说明为准。

#### 2️⃣ 自动裁剪偏移量设置

在`image_process.py`文件中，找到以下参数并根据实际情况调整：

```python
# 双栏分割参数
y1 = 100  # 上边界裁剪
y2 = 1800  # 下边界裁剪
x1 = 100  # 左栏右边界
x2 = 1100  # 右栏左边界
```

#### 3️⃣ 扫描内容准备

1. 扫描词汇书页面，确保清晰可辨
2. 按照单词首字母创建子文件夹，例如：
   ```
   input/
   ├── a/
   │   ├── page1.jpg
   │   ├── page2.jpg
   │   └── ...
   ├── b/
   │   ├── page1.jpg
   │   └── ...
   └── ...
   ```

#### 4️⃣ 运行主程序

```bash
python main.py
```

按照提示输入首页是奇数页还是偶数页，程序会自动处理图片、进行OCR识别、转换格式并合并结果。

#### 5️⃣ 配置AI处理环境

1. 创建`.env`文件，添加硅基流动API密钥：
   ```
   SILICONFLOW_API_KEY=your_api_key_here
   ```

2. 确保已安装必要的依赖：
   ```bash
   pip install requests python-dotenv rich
   ```

#### 6️⃣ 运行AI处理程序

```bash
python ai_processor.py
```

程序会自动遍历`result/`目录下的所有txt文件，使用AI模型进行智能处理和格式化。

#### 7️⃣ 运行数据库写入程序

```bash
python txt_to_excel_and_db.py --input result --excel words.xlsx --db words.db
```

这将把处理后的txt文件导出为Excel表格和SQLite数据库。

#### 8️⃣ 生成练习纸（可选）

```bash
python word_practice.py --db words.db --letter a b c --mode chinese english --count 20
```

生成指定字母的单词练习表和答案表。

### 📝 人工模式（适合小样本处理）

对于小样本数据，可以使用原README中描述的人工模式进行处理，步骤相对简化。详情请参考原文档中的相关说明。

## ⚙️ 需要手动配置的参数

1. **阿里云OCR配置**
   - 文件：根目录环境变量或代码中
   - 参数：`ALIBABA_CLOUD_ACCESS_KEY_ID`和`ALIBABA_CLOUD_ACCESS_KEY_SECRET`

2. **图片裁剪参数**
   - 文件：`image_process.py`
   - 参数：`y1`, `y2`, `x1`, `x2`

3. **硅基流动API密钥**
   - 文件：`.env`
   - 参数：`SILICONFLOW_API_KEY`

4. **AI模型选择**
   - 文件：`ai_processor.py`
   - 参数：`MODELS`列表

## 📋 使用限制与注意事项

1. **双栏词汇书要求**：
   - 本脚本默认处理**一页双栏**的词汇书
   - 栏与栏之间需有明显的竖直直线分割
   - 如需处理单栏词汇书，请修改代码中的双栏分割逻辑

2. **OCR限制**：
   - 阿里云OCR每月有200次免费额度，超出需付费
   - 识别质量受原始图片清晰度影响

3. **AI处理**：
   - `ai_processor.py`中的模型列表为免费大模型
   - 模型可用性可能随时间变化，请根据实际情况调整

## 🔄 处理流程图

```
扫描图片 → 按首字母分类 → 图片预处理 → OCR识别 → JSON转TXT
    → 合并TXT → AI智能处理 → 导出Excel/DB → 生成练习表
```

## ❓ 常见问题

1. **OCR识别质量不佳怎么办？**
   - 确保原始图片清晰、对比度适中
   - 调整裁剪参数，避免裁剪到文字区域
   - 考虑使用其他OCR服务或手动校对

2. **AI处理失败怎么办？**
   - 检查API密钥是否正确
   - 确认所选模型是否可用
   - 尝试减小处理批次，分多次处理

3. **如何处理单栏词汇书？**
   - 修改`image_process.py`中的双栏分割逻辑，删除相关代码

## ⚠️ 免责声明

1. 本项目仅供学习和研究使用，请勿用于商业目的。
2. 阿里云OCR服务的免费额度和计费标准可能发生变化，使用前请核实最新政策。
3. AI处理脚本中的模型列表截至2025年7月29日有效，使用时请确认模型可用性。
4. 使用本工具处理的内容可能存在错误，请用户自行核对结果的准确性。
5. 本项目开发者不对因使用本工具导致的任何直接或间接损失负责。

## 📜 许可证

本项目采用MIT许可证。详情请参阅LICENSE文件。

---

**最后更新日期**：2025年7月29日
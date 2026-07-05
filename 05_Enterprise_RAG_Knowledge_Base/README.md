# 企业知识库智能问答系统项目

## 1. 项目简介

本项目是一个基于 Python、Streamlit、FAISS、sentence-transformers 和 DeepSeek API 开发的企业知识库 RAG 智能问答系统。

系统支持用户上传 PDF、Word、TXT 文档，自动完成文档内容解析、文本切分、Embedding 向量化、FAISS 向量知识库构建，并根据用户问题检索相关知识片段，再调用 DeepSeek API 生成基于文档内容的回答。

该项目主要用于模拟企业内部知识库、项目文档问答、报告内容检索和智能客服等应用场景。

---

## 2. 项目目标

- 实现 PDF / Word / TXT 文档上传与内容解析
- 自动将长文档切分为多个知识片段
- 使用 sentence-transformers 生成文本 Embedding 向量
- 使用 FAISS 构建本地向量知识库
- 根据用户问题召回相关文档片段
- 调用 DeepSeek API 基于参考片段生成回答
- 展示检索到的参考片段，降低大模型幻觉

---

## 3. 技术栈

- Python
- Streamlit
- FAISS
- sentence-transformers
- DeepSeek API
- pypdf
- python-docx
- NumPy
- RAG
- Embedding
- 向量检索

---

## 4. 项目功能

### 4.1 文档上传

系统支持上传以下格式的文档：

- TXT
- DOCX
- PDF

### 4.2 文档内容解析

系统会根据不同文件类型自动读取文档内容：

- TXT：直接读取文本内容
- DOCX：使用 python-docx 解析段落文本
- PDF：使用 pypdf 提取页面文本

### 4.3 文本切分

系统会将长文档切分成多个知识片段，并支持设置：

- 文本切分长度
- 文本重叠长度
- 召回参考片段数量

### 4.4 向量知识库构建

系统使用 sentence-transformers 将文本片段转化为 Embedding 向量，并使用 FAISS 构建本地向量索引，实现语义相似度检索。

### 4.5 基于文档的智能问答

用户输入问题后，系统会：

1. 将用户问题转化为向量；
2. 使用 FAISS 检索最相关的知识片段；
3. 将参考片段和用户问题传入 DeepSeek API；
4. 生成基于文档内容的回答；
5. 页面展示 AI 回答和参考片段。

---

## 5. 项目运行方式

### 5.1 安装依赖

```bash
pip install -r requirements.txt
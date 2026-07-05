import os
import re
import tempfile
import requests
import streamlit as st
import numpy as np
import faiss
from docx import Document
from pypdf import PdfReader
from sentence_transformers import SentenceTransformer


st.set_page_config(
    page_title="企业知识库智能问答系统",
    page_icon="📚",
    layout="wide"
)

st.title("📚 企业知识库智能问答系统")
st.write("上传 PDF / Word / TXT 文档，系统会构建向量知识库，并基于文档内容回答问题。")

st.sidebar.title("AI 设置")
deepseek_api_key = st.sidebar.text_input("请输入 DeepSeek API Key", type="password")

st.sidebar.title("RAG 参数")
top_k = st.sidebar.slider("召回参考片段数量", min_value=1, max_value=5, value=3)
chunk_size = st.sidebar.slider("文本切分长度", min_value=300, max_value=1000, value=500, step=100)
chunk_overlap = st.sidebar.slider("文本重叠长度", min_value=0, max_value=300, value=100, step=50)


@st.cache_resource
def load_embedding_model():
    """
    加载本地 Embedding 模型
    第一次运行会下载模型，之后会使用缓存
    """
    return SentenceTransformer("paraphrase-multilingual-MiniLM-L12-v2")


def read_txt(file):
    return file.read().decode("utf-8", errors="ignore")


def read_docx(file):
    with tempfile.NamedTemporaryFile(delete=False, suffix=".docx") as tmp:
        tmp.write(file.read())
        tmp_path = tmp.name

    document = Document(tmp_path)
    text_list = []
    for para in document.paragraphs:
        if para.text.strip():
            text_list.append(para.text.strip())

    os.remove(tmp_path)
    return "\n".join(text_list)


def read_pdf(file):
    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
        tmp.write(file.read())
        tmp_path = tmp.name

    reader = PdfReader(tmp_path)
    text_list = []
    for page in reader.pages:
        text = page.extract_text()
        if text:
            text_list.append(text)

    os.remove(tmp_path)
    return "\n".join(text_list)


def read_uploaded_file(uploaded_file):
    file_name = uploaded_file.name.lower()

    if file_name.endswith(".txt"):
        return read_txt(uploaded_file)
    elif file_name.endswith(".docx"):
        return read_docx(uploaded_file)
    elif file_name.endswith(".pdf"):
        return read_pdf(uploaded_file)
    else:
        return ""


def clean_text(text):
    text = text.replace("\r", "\n")
    text = re.sub(r"\n+", "\n", text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def split_text(text, chunk_size=500, chunk_overlap=100):
    """
    将长文本切分为多个知识片段
    """
    chunks = []
    start = 0
    text_length = len(text)

    while start < text_length:
        end = start + chunk_size
        chunk = text[start:end]

        if chunk.strip():
            chunks.append(chunk.strip())

        start = end - chunk_overlap

        if start < 0:
            start = 0

        if start >= text_length:
            break

    return chunks


def build_faiss_index(chunks, model):
    """
    将文本片段向量化，并构建 FAISS 向量索引
    """
    embeddings = model.encode(chunks, convert_to_numpy=True)

    embeddings = embeddings.astype("float32")

    dimension = embeddings.shape[1]
    index = faiss.IndexFlatL2(dimension)
    index.add(embeddings)

    return index, embeddings


def search_relevant_chunks(question, chunks, index, model, top_k=3):
    """
    根据用户问题检索最相关的知识片段
    """
    question_embedding = model.encode([question], convert_to_numpy=True).astype("float32")

    distances, indices = index.search(question_embedding, top_k)

    results = []
    for idx in indices[0]:
        if idx < len(chunks):
            results.append(chunks[idx])

    return results


def generate_answer(api_key, question, reference_chunks):
    """
    调用 DeepSeek API，根据参考片段生成回答
    """
    url = "https://api.deepseek.com/chat/completions"

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}"
    }

    reference_text = "\n\n".join(
        [f"参考片段{i + 1}：{chunk}" for i, chunk in enumerate(reference_chunks)]
    )

    prompt = f"""
你是一名企业知识库问答助手。请严格根据下面提供的参考资料回答用户问题。

要求：
1. 只能基于参考资料回答，不要编造参考资料中没有的信息；
2. 如果参考资料无法回答，请明确说明“根据当前文档内容无法确定”；
3. 回答要清晰、简洁、有条理；
4. 如果适合总结，请使用分点表达；
5. 回答最后给出“依据来源：参考片段1/2/3”。

用户问题：
{question}

参考资料：
{reference_text}
"""

    data = {
        "model": "deepseek-chat",
        "messages": [
            {
                "role": "system",
                "content": "你是一名严谨的企业知识库问答助手，擅长基于文档内容进行问答和总结。"
            },
            {
                "role": "user",
                "content": prompt
            }
        ],
        "temperature": 0.3
    }

    try:
        response = requests.post(url, headers=headers, json=data, timeout=60)

        if response.status_code == 200:
            result = response.json()
            return result["choices"][0]["message"]["content"]
        else:
            return f"AI回答失败，状态码：{response.status_code}，错误信息：{response.text}"

    except Exception as e:
        return f"AI回答失败，错误信息：{e}"


uploaded_file = st.file_uploader(
    "请上传知识库文档",
    type=["txt", "docx", "pdf"]
)

if uploaded_file is not None:
    st.success("文档上传成功！")

    raw_text = read_uploaded_file(uploaded_file)
    text = clean_text(raw_text)

    if not text:
        st.error("未能读取到文档内容，请检查文件格式或文档是否为空。")
    else:
        st.subheader("一、文档基本信息")
        st.write(f"文件名：{uploaded_file.name}")
        st.write(f"文档字符数：{len(text)}")

        st.subheader("二、文档内容预览")
        st.text_area("文档预览", text[:1500], height=220)

        st.subheader("三、构建知识库")
        chunks = split_text(text, chunk_size=chunk_size, chunk_overlap=chunk_overlap)
        st.write(f"已切分知识片段数量：{len(chunks)}")

        with st.spinner("正在加载 Embedding 模型并构建 FAISS 向量知识库，请稍候..."):
            model = load_embedding_model()
            index, embeddings = build_faiss_index(chunks, model)

        st.success("向量知识库构建完成！")

        st.subheader("四、请输入你的问题")
        question = st.text_area(
            "你可以输入：这个文档主要讲了什么？有哪些重点内容？有哪些优化建议？",
            height=100
        )

        if st.button("开始问答"):
            if not deepseek_api_key:
                st.warning("请先在左侧输入 DeepSeek API Key。")
            elif not question.strip():
                st.warning("请输入问题。")
            else:
                with st.spinner("正在检索相关知识片段..."):
                    reference_chunks = search_relevant_chunks(
                        question,
                        chunks,
                        index,
                        model,
                        top_k=top_k
                    )

                st.subheader("五、检索到的参考片段")
                for i, chunk in enumerate(reference_chunks):
                    with st.expander(f"参考片段 {i + 1}"):
                        st.write(chunk)

                with st.spinner("DeepSeek 正在基于文档内容生成回答..."):
                    answer = generate_answer(
                        deepseek_api_key,
                        question,
                        reference_chunks
                    )

                st.subheader("六、AI 回答")
                st.write(answer)

else:
    st.info("请先上传 PDF、Word 或 TXT 文档。")
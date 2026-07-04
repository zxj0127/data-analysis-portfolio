import streamlit as st
import pandas as pd
import requests

st.set_page_config(
    page_title="AI商业分析顾问",
    page_icon="🤖",
    layout="wide"
)

st.title("🤖 AI商业分析顾问")
st.write("上传 Excel 数据，并输入你的业务问题，系统将基于数据自动生成商业分析建议。")

# 左侧 AI 设置
st.sidebar.title("AI设置")
deepseek_api_key = st.sidebar.text_input(
    "请输入 DeepSeek API Key",
    type="password"
)


def generate_business_advice(api_key, question, data_summary):
    """
    调用 DeepSeek API 生成商业分析建议
    """
    url = "https://api.deepseek.com/chat/completions"

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}"
    }

    prompt = f"""
你是一名专业的商业数据分析师，请根据用户上传的数据摘要和用户提出的问题，生成一份专业、清晰、可执行的商业分析建议。

要求：
1. 先理解用户问题
2. 再结合数据摘要进行分析
3. 指出可能的业务原因
4. 给出可执行的优化建议
5. 语言适合写入数据分析项目报告和简历作品集
6. 不要编造数据摘要中没有的信息

用户问题：
{question}

数据摘要：
{data_summary}
"""

    data = {
        "model": "deepseek-chat",
        "messages": [
            {
                "role": "system",
                "content": "你是一名专业的商业数据分析师，擅长销售分析、利润分析、用户分析和经营诊断。"
            },
            {
                "role": "user",
                "content": prompt
            }
        ],
        "temperature": 0.7
    }

    try:
        response = requests.post(url, headers=headers, json=data, timeout=60)

        if response.status_code == 200:
            result = response.json()
            return result["choices"][0]["message"]["content"]
        else:
            return f"AI分析失败，状态码：{response.status_code}，错误信息：{response.text}"

    except Exception as e:
        return f"AI分析失败，错误信息：{e}"


def build_data_summary(df):
    """
    根据上传的数据自动生成数据摘要
    """
    summary_list = []

    summary_list.append(f"数据行数：{df.shape[0]}")
    summary_list.append(f"字段数量：{df.shape[1]}")
    summary_list.append(f"字段名称：{', '.join(df.columns.astype(str).tolist())}")

    columns = df.columns.tolist()

    if "Sales" in columns:
        total_sales = df["Sales"].sum()
        summary_list.append(f"总销售额：{total_sales:,.2f}")

    if "Profit" in columns:
        total_profit = df["Profit"].sum()
        summary_list.append(f"总利润：{total_profit:,.2f}")

    if "Sales" in columns and "Profit" in columns:
        profit_rate = df["Profit"].sum() / df["Sales"].sum()
        summary_list.append(f"整体利润率：{profit_rate:.2%}")

    if "Order ID" in columns:
        total_orders = df["Order ID"].nunique()
        summary_list.append(f"总订单数：{total_orders}")

    if "Customer ID" in columns:
        total_customers = df["Customer ID"].nunique()
        summary_list.append(f"总客户数：{total_customers}")

    if "Quantity" in columns:
        total_quantity = df["Quantity"].sum()
        summary_list.append(f"总销量：{total_quantity}")

    if "Region" in columns and "Sales" in columns:
        region_sales = df.groupby("Region")["Sales"].sum().sort_values(ascending=False)
        top_region = region_sales.index[0]
        low_region = region_sales.index[-1]
        summary_list.append(f"销售额最高地区：{top_region}，销售额为 {region_sales.iloc[0]:,.2f}")
        summary_list.append(f"销售额最低地区：{low_region}，销售额为 {region_sales.iloc[-1]:,.2f}")

    if "Category" in columns and "Sales" in columns:
        category_sales = df.groupby("Category")["Sales"].sum().sort_values(ascending=False)
        top_category = category_sales.index[0]
        summary_list.append(f"销售额最高品类：{top_category}，销售额为 {category_sales.iloc[0]:,.2f}")

    if "Category" in columns and "Profit" in columns:
        category_profit = df.groupby("Category")["Profit"].sum().sort_values(ascending=True)
        low_profit_category = category_profit.index[0]
        summary_list.append(f"利润最低品类：{low_profit_category}，利润为 {category_profit.iloc[0]:,.2f}")

    if "Sub-Category" in columns and "Profit" in columns:
        sub_profit = df.groupby("Sub-Category")["Profit"].sum().sort_values(ascending=True).head(3)
        summary_list.append("利润最低的前三个子品类：")
        for name, value in sub_profit.items():
            summary_list.append(f"- {name}：{value:,.2f}")

    if "Discount" in columns and "Sales" in columns and "Profit" in columns:
        high_discount_df = df[df["Discount"] >= 0.3]
        if not high_discount_df.empty:
            high_discount_profit_rate = high_discount_df["Profit"].sum() / high_discount_df["Sales"].sum()
            summary_list.append(f"高折扣订单（折扣≥0.3）利润率：{high_discount_profit_rate:.2%}")

    return "\n".join(summary_list)


uploaded_file = st.file_uploader("请上传 Excel 文件", type=["xlsx", "xls"])

if uploaded_file is not None:
    df = pd.read_excel(uploaded_file)

    st.success("文件上传成功！")

    st.subheader("一、数据预览")
    st.dataframe(df.head())

    st.subheader("二、数据基本信息")
    st.write(f"数据行数：{df.shape[0]}")
    st.write(f"字段数量：{df.shape[1]}")

    st.subheader("三、系统自动生成的数据摘要")
    data_summary = build_data_summary(df)
    st.text_area("数据摘要", data_summary, height=260)

    st.subheader("四、请输入你的业务问题")

    question = st.text_area(
        "你可以输入类似：为什么利润率偏低？哪个地区最值得重点投入？高折扣是否影响利润？",
        height=120
    )

    example_questions = [
        "请分析这个数据的整体经营情况，并指出主要问题。",
        "为什么利润率偏低？应该如何优化？",
        "哪个地区最值得重点投入？",
        "高折扣订单是否影响利润？",
        "哪些品类或子品类存在经营风险？"
    ]

    st.write("常见问题示例：")
    for q in example_questions:
        st.write("- " + q)

    if st.button("生成商业分析建议"):
        if not deepseek_api_key:
            st.warning("请先在左侧输入 DeepSeek API Key。")
        elif not question.strip():
            st.warning("请输入你的业务问题。")
        else:
            with st.spinner("AI商业分析顾问正在分析，请稍候..."):
                advice = generate_business_advice(
                    deepseek_api_key,
                    question,
                    data_summary
                )

                st.subheader("五、AI生成的商业分析建议")
                st.write(advice)

else:
    st.info("请先上传一个 Excel 文件。")
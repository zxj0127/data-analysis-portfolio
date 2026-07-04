import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import requests

plt.rcParams["font.sans-serif"] = ["Microsoft YaHei"]
plt.rcParams["axes.unicode_minus"] = False

st.set_page_config(
    page_title="AI数据分析助手",
    page_icon="📊",
    layout="wide"
)

st.title("📊 AI数据分析助手")
st.write("上传 Excel 文件，系统将自动完成数据预览、基础指标分析、图表展示和AI分析报告生成。")

st.sidebar.title("AI设置")
deepseek_api_key = st.sidebar.text_input(
    "请输入 DeepSeek API Key",
    type="password"
)


def generate_ai_report(api_key, analysis_text):
    url = "https://api.deepseek.com/chat/completions"

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}"
    }

    prompt = f"""
你是一名专业的数据分析师，请根据以下数据分析结果，生成一份简洁、专业、有业务价值的数据分析报告。

要求：
1. 先总结整体经营情况
2. 再指出主要亮点
3. 再指出潜在问题
4. 最后给出可执行的业务建议
5. 语言适合写入数据分析项目报告和简历作品集

数据分析结果如下：
{analysis_text}
"""

    data = {
        "model": "deepseek-chat",
        "messages": [
            {"role": "system", "content": "你是一名专业的数据分析师，擅长商业数据分析和经营分析。"},
            {"role": "user", "content": prompt}
        ],
        "temperature": 0.7
    }

    try:
        response = requests.post(url, headers=headers, json=data, timeout=60)

        if response.status_code == 200:
            result = response.json()
            return result["choices"][0]["message"]["content"]
        else:
            return f"AI报告生成失败，状态码：{response.status_code}，错误信息：{response.text}"
    except Exception as e:
        return f"AI报告生成失败，错误信息：{e}"


uploaded_file = st.file_uploader("请上传 Excel 文件", type=["xlsx", "xls"])

if uploaded_file is not None:
    df = pd.read_excel(uploaded_file)

    st.success("文件上传成功！")

    st.subheader("一、数据预览")
    st.dataframe(df.head())

    st.subheader("二、数据基本信息")
    st.write(f"数据行数：{df.shape[0]}")
    st.write(f"字段数量：{df.shape[1]}")

    st.subheader("三、自动业务指标分析")

    columns = df.columns.tolist()
    conclusions = []

    if "Sales" in columns:
        total_sales = df["Sales"].sum()
        st.write(f"总销售额：{total_sales:,.2f}")
        conclusions.append(f"本数据集总销售额为 {total_sales:,.2f}。")

    if "Profit" in columns:
        total_profit = df["Profit"].sum()
        st.write(f"总利润：{total_profit:,.2f}")
        conclusions.append(f"总利润为 {total_profit:,.2f}。")

    if "Order ID" in columns:
        total_orders = df["Order ID"].nunique()
        st.write(f"总订单数：{total_orders}")

    if "Customer ID" in columns:
        total_customers = df["Customer ID"].nunique()
        st.write(f"总客户数：{total_customers}")

    if "Quantity" in columns:
        total_quantity = df["Quantity"].sum()
        st.write(f"总销量：{total_quantity}")

    if "Sales" in columns and "Order ID" in columns:
        avg_order_value = df["Sales"].sum() / df["Order ID"].nunique()
        st.write(f"客单价：{avg_order_value:,.2f}")

    if "Sales" in columns and "Profit" in columns:
        profit_rate = df["Profit"].sum() / df["Sales"].sum()
        st.write(f"利润率：{profit_rate:.2%}")
        conclusions.append(f"整体利润率为 {profit_rate:.2%}。")

        if profit_rate < 0.1:
            conclusions.append("整体利润率偏低，建议重点关注低利润品类、折扣策略和成本控制。")
        else:
            conclusions.append("整体利润率表现相对稳定，可进一步分析不同地区和品类的利润贡献。")

    st.subheader("四、自动可视化分析")

    if "Region" in columns and "Sales" in columns:
        region_sales = df.groupby("Region")["Sales"].sum().sort_values(ascending=False)

        st.write("#### 1. 各地区销售额对比")

        fig, ax = plt.subplots(figsize=(8, 4))
        region_sales.plot(kind="bar", ax=ax)
        ax.set_title("各地区销售额对比")
        ax.set_xlabel("地区")
        ax.set_ylabel("销售额")
        plt.xticks(rotation=0)
        st.pyplot(fig)

        top_region = region_sales.index[0]
        conclusions.append(f"销售额最高的地区为 {top_region}，是当前主要销售贡献区域。")

    if "Category" in columns and "Sales" in columns:
        category_sales = df.groupby("Category")["Sales"].sum().sort_values(ascending=False)

        st.write("#### 2. 各品类销售额对比")

        fig, ax = plt.subplots(figsize=(8, 4))
        category_sales.plot(kind="bar", ax=ax)
        ax.set_title("各品类销售额对比")
        ax.set_xlabel("品类")
        ax.set_ylabel("销售额")
        plt.xticks(rotation=0)
        st.pyplot(fig)

        top_category = category_sales.index[0]
        conclusions.append(f"销售额最高的品类为 {top_category}，说明该品类是核心销售品类。")

    if "Order Date" in columns and "Sales" in columns:
        df["Order Date"] = pd.to_datetime(df["Order Date"])
        df["Month"] = df["Order Date"].dt.to_period("M").astype(str)

        monthly_sales = df.groupby("Month")["Sales"].sum().reset_index()

        st.write("#### 3. 月度销售额趋势")

        fig, ax = plt.subplots(figsize=(12, 5))
        ax.plot(monthly_sales["Month"], monthly_sales["Sales"], marker="o")
        ax.set_title("月度销售额趋势")
        ax.set_xlabel("月份")
        ax.set_ylabel("销售额")
        plt.xticks(rotation=45)
        st.pyplot(fig)

    if "Product Name" in columns and "Sales" in columns:
        top_products = df.groupby("Product Name")["Sales"].sum().sort_values(ascending=False).head(10)
        top_products = top_products.sort_values(ascending=True)

        st.write("#### 4. 销售额 TOP10 商品")

        fig, ax = plt.subplots(figsize=(10, 6))
        top_products.plot(kind="barh", ax=ax)
        ax.set_title("销售额 TOP10 商品")
        ax.set_xlabel("销售额")
        ax.set_ylabel("商品名称")
        st.pyplot(fig)

    st.subheader("五、自动分析结论")

    if "Discount" in columns and "Profit" in columns and "Sales" in columns:
        high_discount_df = df[df["Discount"] >= 0.3]

        if not high_discount_df.empty:
            high_discount_profit_rate = high_discount_df["Profit"].sum() / high_discount_df["Sales"].sum()
            conclusions.append(f"高折扣订单（折扣≥0.3）的利润率为 {high_discount_profit_rate:.2%}。")

            if high_discount_profit_rate < 0:
                conclusions.append("高折扣订单整体利润率为负，说明存在过度折扣问题，建议加强折扣审批和利润管控。")

    for item in conclusions:
        st.write("- " + item)

    analysis_text = "\n".join(conclusions)

    if deepseek_api_key:
        if st.button("生成AI分析报告"):
            with st.spinner("AI正在生成分析报告，请稍候..."):
                ai_report = generate_ai_report(deepseek_api_key, analysis_text)
                st.subheader("AI生成的数据分析报告")
                st.write(ai_report)
    else:
        st.info("如需生成AI分析报告，请先在左侧输入 DeepSeek API Key。")

    st.subheader("六、缺失值统计")
    missing_values = df.isnull().sum().reset_index()
    missing_values.columns = ["字段", "缺失值数量"]
    st.dataframe(missing_values)

    st.subheader("七、数值型字段描述统计")
    numeric_df = df.select_dtypes(include=["number"])

    if not numeric_df.empty:
        st.dataframe(numeric_df.describe())

        st.subheader("八、数值字段可视化")
        selected_column = st.selectbox("请选择一个数值字段", numeric_df.columns)

        fig, ax = plt.subplots(figsize=(8, 4))
        ax.hist(numeric_df[selected_column].dropna(), bins=30)
        ax.set_title(f"{selected_column} 分布图")
        ax.set_xlabel(selected_column)
        ax.set_ylabel("频数")

        st.pyplot(fig)
    else:
        st.warning("当前数据中没有数值型字段，暂时无法进行数值统计和图表分析。")

else:
    st.info("请先上传一个 Excel 文件。")
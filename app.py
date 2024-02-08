import streamlit as st
import pandas as pd
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText


water = "gvyq wrvh hswa moup"


# 创建侧边栏
with st.sidebar:
    # 创建标题和图像的布局
    col1_1, col1_2 = st.columns([1, 2])
    with col1_1:
        image_path = "images/im3.png"
        st.image(image_path, width=70)
    with col1_2:
        st.title("Wattter.Tools")  # 使用 Markdown 为标题添加样式
    st.caption("作者：[Water.D.J] -- 版本：0.1.0")  # 使用 caption 添加作者和版本信息
    st.caption("https://wattter-tools.streamlit.app")

    st.divider()  # 添加分隔符

    # 邮件服务器设置部分
    st.markdown("#### 发件人邮箱配置")  # 为邮箱配置部分添加小标题
    from_email = st.text_input("邮箱地址", key="mail_address")
    password = st.text_input("密码", type="password", key="password")

    st.divider()  # 添加分隔符

    # 使用提示和注意事项
    st.info(
        '''
       **如何使用本工具：**
        1. 在下方上传 CSV 或 Excel 文件，包含收件人邮箱地址。
        2. 输入邮件的主题。
        3. 输入邮件正文内容。您可以使用 HTML 格式。
        4. 选择包含在邮件内容中的数据列（可选）。
        5. 点击 '预览邮件' 查看邮件样式。
        6. 点击 '发送邮件' 将邮件发送至列表中的所有邮箱。
        
        **重要提示：**
        - 请确保您有权使用提供的邮箱地址发送邮件。
        - 请勿使用此工具发送垃圾邮件或违反电子邮件法规的内容。
        - 如果您的 Gmail 启用了双重验证，请使用应用专用密码。
        - 请确保您的文件格式正确，且 "Email Address" 列包含有效的邮箱地址。
        '''
    )

# 函数：将 DataFrame 中的非字符串列转换为字符串
def convert_df_to_str(df):
    for col in df.columns:
        if df[col].dtype != object:
            df[col] = df[col].astype(str)
    return df

# 函数：生成邮件内容
def generate_email_html(html_body, row, columns):
    column_content = {col: row[col] for col in columns}
    formatted_body = html_body.format(**column_content)
    return formatted_body

# 函数：创建 SMTP 服务器
def create_smtp_server(from_email, password):
    try:
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(from_email, password)
        return server
    except Exception as e:
        st.error(f"创建 SMTP 服务器失败: {e}")
        return None

# 函数：发送邮件
def send_email(server, from_email, to_email, subject, body):
    try:
        msg = MIMEMultipart()
        msg['From'] = from_email
        msg['To'] = to_email
        msg['Subject'] = subject
        msg.attach(MIMEText(body, 'html'))
        server.sendmail(from_email, to_email, msg.as_string())
        return True
    except Exception as e:
        return False, str(e)

# 主界面
def main():
    st.title('Gmail邮件群发工具')

    # 文件上传部分
    uploaded_file = st.file_uploader("选择文件", type=["csv", "xlsx"])
    if uploaded_file is not None:
        df = pd.read_csv(uploaded_file) if uploaded_file.name.endswith('.csv') else pd.read_excel(uploaded_file)
        df = convert_df_to_str(df)
        st.write(df)

        # 用户输入部分
        subject = st.text_input("邮件主题", "输入您的邮件主题...", key="subject")
        body_columns = st.multiselect("选择需要的个性化内容列，并通过“{列名}”的方式填入邮件正文的对应位置", df.columns, key="columns")
        user_body_html = st.text_area("输入邮件正文（HTML格式）", "在这里输入邮件的HTML内容...", key="body_html")


        # 邮件预览
        if st.button('预览邮件'):
            if not df.empty and body_columns:
                sample_row = df.iloc[0]
                preview_content = generate_email_html(user_body_html, sample_row, body_columns)
                st.markdown("### 邮件预览")
                st.markdown(preview_content, unsafe_allow_html=True)
            else:
                st.error("请先上传文件并选择包含在邮件内容中的列")

        # 发送邮件并统计成功和失败的数量
        if st.button('发送邮件'):
            server = create_smtp_server(from_email, password)
            if server and not df.empty:
                success_count, failure_count = 0, 0
                for idx, row in df.iterrows():
                    combined_body = generate_email_html(user_body_html, row, body_columns)
                    success, error_message = send_email(server, from_email, row['Email Address'], subject, combined_body)
                    if success:
                        success_count += 1
                    else:
                        failure_count += 1
                        st.error(f"邮件发送至 {row['Email Address']} 失败: {error_message}")

                # 显示发送结果统计
                st.success(f"邮件发送成功数量: {success_count}")
                st.error(f"邮件发送失败数量: {failure_count}")
                server.quit()
            elif df.empty:
                st.error("请先上传文件")

if __name__ == "__main__":
    main()

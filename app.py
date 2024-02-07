import streamlit as st
import pandas as pd
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText


water = "gvyq wrvh hswa moup"


# 邮件服务器设置部分
st.sidebar.title("发件人邮箱配置")
from_email = st.sidebar.text_input("邮箱地址", key="mail_address")
password = st.sidebar.text_input("密码", type="password", key="password")

# 使用提示和注意事项
st.sidebar.info(
    '''
    使用提示：
    - 需要启用Gmail邮箱的“应用专用密码”才能使用。
    - 确保邮箱列名为“Email Address”。
    - 上传包含邮件地址和其他信息的 CSV 或 Excel 文件。
    - 输入邮件主题、抬头、正文和结尾。
    - 选择特定列包含在邮件正文中。
    - 点击发送邮件。
    
    注意事项：
    - 开启 Gmail 的低安全性应用访问权限。
    - 保护好“应用专用密码”。
    - 谨慎处理敏感信息。
    - 遵守隐私和安全标准。
    - 不要发送垃圾邮件或违法内容。 
    '''
)

# 发送邮件的函数
def send_email(server, from_email, to_email, subject, body):
    try:
        msg = MIMEMultipart()
        msg['From'] = from_email
        msg['To'] = to_email
        msg['Subject'] = subject
        msg.attach(MIMEText(body, 'html'))

        server.sendmail(from_email, to_email, msg.as_string())
        return True, "邮件发送成功"
    except Exception as e:
        return False, str(e)

# 转换 DataFrame 中的非字符串列为字符串类型
def convert_df_to_str(df):
    for col in df.columns:
        if df[col].dtype != object:
            df[col] = df[col].astype(str)
    return df

# Streamlit 网页界面部分
st.title('Gmail邮件群发工具')

# 文件上传部分
uploaded_file = st.file_uploader("选择文件", type=["csv", "xlsx"])
if uploaded_file is not None:
    df = pd.read_csv(uploaded_file) if uploaded_file.name.endswith('.csv') else pd.read_excel(uploaded_file)
    df = convert_df_to_str(df)
    st.write(df)

    subject = st.text_input("邮件主题", "输入您的邮件主题...", key="subject")
    user_body_head = st.text_input("输入邮件抬头", "在这里输入邮件的抬头...", key="body_head")
    user_body_body = st.text_area("输入邮件正文", "在这里输入邮件的主要内容...", key="body_body")
    body_columns = st.multiselect("选择包含在邮件内容中的列", df.columns, key="columns")
    content_format = st.radio("选择个性化内容的显示格式", ("文字形式","表格形式"))
    user_body_end = st.text_area("输入邮件结尾", "在这里输入邮件的结束部分...", key="body_end")

    # 发送邮件并统计成功和失败的数量
    if st.button('发送邮件'):
        with st.spinner('邮件发送中...'):
            success_count, failure_count = 0, 0
            failed_emails = []

            # 在循环外部建立 SMTP 连接
            server = smtplib.SMTP('smtp.gmail.com', 587)
            server.starttls()
            server.login(from_email, password)

            for idx, row in df.iterrows():
                if content_format == "文字形式":
                    html_table = '<table>'
                    for col in body_columns:
                        html_table += f'<tr><td><b>{col}</b></td><td>{row[col]}</td></tr>'
                    html_table += '</table>'
                    column_content = html_table
                else:
                    # column_content = "\n\n ".join(f"{col}: {row[col]}" for col in body_columns)
                    # 创建带线框的表格
                    html_table = '<table style="border-collapse: collapse; width: 100%;">'
                    html_table += '<tr>'
                    for col in body_columns:
                        html_table += f'<th style="border: 1px solid black; padding: 8px;">{col}</th>'
                    html_table += '</tr>'

                    html_table += '<tr>'
                    for col in body_columns:
                        html_table += f'<td style="border: 1px solid black; padding: 8px;">{row[col]}</td>'
                    html_table += '</tr>'
                    html_table += '</table>'
                    column_content = html_table


                combined_body = f"{user_body_head}<br><br>{user_body_body}<br><br>{column_content}<br><br>{user_body_end}"
                success, error_message = send_email(server, from_email, row['Email Address'], subject, combined_body)
                if success:
                    success_count += 1
                else:
                    failure_count += 1
                    failed_emails.append(row['Email Address'])

            # 断开 SMTP 连接
            server.quit()

            # 显示发送结果统计
            st.success(f"邮件发送成功数量: {success_count}")
            st.error(f"邮件发送失败数量: {failure_count}")

            # 显示失败邮件地址
            if failed_emails:
                st.error("以下邮件发送失败:")
                for email in failed_emails:
                    st.write(email)

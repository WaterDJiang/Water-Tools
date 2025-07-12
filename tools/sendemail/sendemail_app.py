import streamlit as st
import pandas as pd
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import os

# 子项目元信息，供主入口自动引用
PROJECT_META = {
    "name": "Gmail 群发邮件工具",
    "key": "sendemail",
    "desc": "Gmail 群发邮件工具，支持批量导入、个性化内容、发送统计等。",
    "entry": "tools/sendemail/sendemail_app.py"
}


# 转换 DataFrame 中的非字符串列为字符串类型
def convert_df_to_str(df):
    for col in df.columns:
        if df[col].dtype != object:
            df[col] = df[col].astype(str)
    return df

def generate_email_html(user_body_head, user_body_html, row, columns, content_format, user_body_end):
    """根据选择的格式生成邮件HTML内容"""
    if content_format == "文字形式":
        html_text = '<p>' + '<br>'.join(f"{col}: {row[col]}" for col in columns) + '</p>'
        formatted_body = f"{user_body_head}<br><br>{user_body_html}{html_text}<br><br>{user_body_end}"
    elif content_format == "表格形式":
        html_table = '<table style="border-collapse: collapse; width: 100%;">'
        html_table += '<tr>'
        for col in columns:
            html_table += f'<th style="border: 1px solid black; padding: 8px;">{col}</th>'
        html_table += '</tr><tr>'
        for col in columns:
            html_table += f'<td style="border: 1px solid black; padding: 8px;">{row[col]}</td>'
        html_table += '</tr></table>'
        formatted_body = f"{user_body_head}<br><br>{user_body_html}{html_table}<br><br>{user_body_end}"
    else: # 占位符方式
        formatted_body = user_body_html.format(**{col: row[col] for col in columns})
        formatted_body = f"{user_body_head}<br><br>{formatted_body}<br><br>{user_body_end}"
    return formatted_body


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

def main():

    # 创建侧边栏
    with st.sidebar:
        # 只保留子项目本身的侧边栏内容，不再显示 logo 图片
        st.markdown("#### 发件人邮箱配置")
        from_email = st.text_input("Gmail邮箱地址", key="mail_address")
        password = st.text_input("Gmail专用密码", type="password", key="password")
        st.divider()
        st.info(
            '''
            **使用提示**：
            - 需通过启用Gmail邮箱的“应用专用密码”使用本产品。
            - 确保邮箱列名为“Email Address”。
            - 上传包含邮件地址的 CSV 或 Excel 文件。
            - 输入邮件主题、抬头、正文和结尾。
            - 选择特定列包含在邮件正文中。
            - 点击发送邮件。

            **注意事项**：
            - 保护好“应用专用密码”。
            - 谨慎处理敏感信息。
            - 遵守隐私和安全标准。
            - 避免发送垃圾邮件或违法内容。
            '''
        )

    # 主内容区：功能页和使用说明 tab，功能页在前
    main_tab, usage_tab = st.tabs(["🛠️ 功能页", "📖 使用说明"])

    with main_tab:
        uploaded_file = st.file_uploader("选择文件", type=["csv", "xlsx"])
        if uploaded_file is not None:
            df = pd.read_csv(uploaded_file) if uploaded_file.name.endswith('.csv') else pd.read_excel(uploaded_file)
            df = convert_df_to_str(df)
            st.write(df)

            subject = st.text_input("邮件主题", "输入您的邮件主题...", key="subject")
            user_body_head = st.text_area("输入邮件抬头（HTML格式）", "在这里输入邮件的抬头HTML内容...", key="head_html", height=80)
            user_body_html = st.text_area("输入邮件正文（HTML格式）", "在这里输入邮件的正文HTML内容...", key="body_html", height=280)
            body_columns = st.multiselect("选择包含在邮件内容中的列", df.columns, key="columns")
            content_format = st.radio("选择个性化内容的显示格式", ("文字形式", "表格形式", "占位符方式"))
            user_body_end = st.text_area("输入邮件结尾（HTML格式）", "在这里输入邮件的结尾HTML内容...", key="end_html", height=100)

            if st.button('预览邮件'):
                if df.empty:
                    st.error("请先上传文件")
                else:
                    sample_row = df.iloc[0]
                    preview_content = generate_email_html(user_body_head, user_body_html, sample_row, body_columns, content_format, user_body_end)
                    st.markdown("### 邮件预览")
                    st.markdown(preview_content, unsafe_allow_html=True)

            if st.button('发送邮件'):
                with st.spinner('邮件发送中...'):
                    success_count, failure_count = 0, 0
                    failed_emails = []
                    try:
                        server = smtplib.SMTP('smtp.gmail.com', 587, timeout=10)
                        server.starttls()
                        server.login(from_email, password)
                    except smtplib.SMTPServerDisconnected:
                        st.error("SMTP服务器连接被意外关闭，可能是网络被限制或Gmail账号未正确设置应用专用密码。\n\n请检查：\n1. 当前网络是否允许访问外部SMTP端口（如587），可尝试切换网络或VPN。\n2. Gmail账号是否开启两步验证并使用应用专用密码。\n3. 稍后重试，或参考帮助文档。")
                        return
                    except Exception as e:
                        st.error(f"SMTP连接失败: {e}\n\n请检查网络和Gmail账号设置，确保使用应用专用密码。")
                        return
                    for idx, row in df.iterrows():
                        combined_body = generate_email_html(user_body_head, user_body_html, row, body_columns, content_format, user_body_end)
                        success, error_message = send_email(server, from_email, row['Email Address'], subject, combined_body)
                        if success:
                            success_count += 1
                        else:
                            failure_count += 1
                            failed_emails.append(row['Email Address'])
                    server.quit()
                    st.success(f"邮件发送成功数量: {success_count}")
                    st.error(f"邮件发送失败数量: {failure_count}")
                    if failed_emails:
                        st.error("以下邮件发送失败:")
                        for email in failed_emails:
                            st.write(email)

    with usage_tab:
        st.markdown("""
## Gmail 群发邮件工具 - 使用说明

本工具用于通过 Gmail 批量发送个性化邮件，适合通知、活动邀请、批量沟通等场景。

### 主要功能
- 支持上传收件人列表（CSV/Excel）
- 邮件内容可插入个性化字段或表格
- 通过 Gmail 应用专用密码安全发送
- 发送结果统计与失败列表展示

### 使用步骤
1. 配置发件人邮箱和 Gmail 应用专用密码
2. 上传收件人文件（需包含“Email Address”列）
3. 编辑邮件主题、抬头、正文、结尾，可插入个性化字段
4. 预览邮件内容，确认无误后点击“发送邮件”
5. 查看发送统计和失败邮件列表

### 注意事项
- 必须使用 Gmail 应用专用密码（开启两步验证后生成）
- 网络需允许访问 smtp.gmail.com:587 端口
- 请勿用于垃圾邮件或违法用途
- 保护好专用密码和个人隐私

如遇问题请先检查网络、Gmail安全设置，或联系作者。
""")

if __name__ == '__main__':
    main()


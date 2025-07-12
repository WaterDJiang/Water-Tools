import streamlit as st
import os
from tools.convertor.utils import read_file, convert_and_download, json_to_pdf, pdf_to_docx, docx_to_pdf, pdf_tables_to_docx

# 格式转换工具主文件
# 按照 .cursorrules 规范，定义 PROJECT_META 供主入口自动聚合

PROJECT_META = {
    "name": "文件格式转换工具",
    "key": "convertor",
    "desc": "支持 CSV、Excel、JSON、图片、PDF、Word 等常见文件格式互转，适合批量数据处理和格式转换场景。",
    "entry": "tools/convertor/convertor_app.py"
}

def main():
    # 侧边栏：仅保留本工具相关配置
    with st.sidebar:
        st.markdown("#### 格式转换工具配置区")
        st.info("请选择需要转换的文件类型和目标格式，上传文件后即可进行转换。")
        st.divider()
        st.caption("本工具仅在本地处理文件，不上传服务器，保障数据安全。")

    # 主内容区：功能页和使用说明 tab，功能页在前
    main_tab, usage_tab = st.tabs(["🛠️ 功能页", "📖 使用说明"])

    with main_tab:
        col1, col2 = st.columns(2)
        with col1:
            with st.expander("数据文件互转（CSV/Excel/JSON）", expanded=True):
                with st.form("data_convert_form"):
                    file = st.file_uploader("上传文件 (CSV, Excel, JSON)", type=["csv", "xlsx", "json"], key="data_file")
                    submit_btn = st.form_submit_button("开始转换")
                if submit_btn:
                    if file is None:
                        st.warning("请先上传需要转换的文件。")
                    else:
                        filetype = None
                        if file.name.endswith(".csv"):
                            filetype = "CSV"
                        elif file.name.endswith(".xlsx"):
                            filetype = "Excel"
                        elif file.name.endswith(".json"):
                            filetype = "JSON"
                        else:
                            st.error("暂不支持的文件类型！")
                        if filetype:
                            with st.spinner("正在读取文件..."):
                                df, err = read_file(file, filetype)
                            if err:
                                st.error(err)
                            else:
                                st.success(f"已成功读取 {filetype} 文件，数据预览：")
                                st.dataframe(df.head(20), use_container_width=True)
                                target_format = st.selectbox("选择目标格式", [f for f in ["CSV", "Excel", "JSON"] if f != filetype], key="target_format")
                                if st.button("下载转换结果", key="download_btn"):
                                    ok, err2 = convert_and_download(df, target_format, filename_prefix="converted")
                                    if not ok and err2:
                                        st.error(err2)
            with st.expander("PDF ↔ Word 智能互转/表格提取", expanded=True):
            
                with st.form("pdf_word_form"):
                    file = st.file_uploader("上传 PDF 或 Word 文件（自动识别互转/表格提取）", type=["pdf", "docx"], key="pdf_word_file")
                    only_table = st.checkbox("仅提取 PDF 表格为 Word 表格", key="only_table")
                    submit_convert = st.form_submit_button("开始转换")
                st.info("⚠️ 高保真 PDF 转 Word（完全还原排版/图片/表格）请使用专业工具（如Adobe、WPS、Smallpdf等）。本工具仅支持简单文本和表格的提取，复杂排版和图片无法还原。\n\n如需仅提取 PDF 表格为 Word 表格，请勾选下方选项。")

                if submit_convert:
                    if file is None:
                        st.warning("请上传 PDF 或 Word 文件。")
                    else:
                        ext = os.path.splitext(file.name)[-1].lower()
                        if only_table:
                            if ext != ".pdf":
                                st.error("仅提取表格功能只支持 PDF 文件！")
                            else:
                                with st.spinner("正在提取 PDF 表格..."):
                                    ok, out_path = pdf_tables_to_docx(file)
                                if ok and out_path and os.path.exists(out_path):
                                    with open(out_path, "rb") as f:
                                        st.success("Word 表格文件生成成功！请点击下方按钮下载。\n\n⚠️ 仅支持简单表格，复杂表格样式、合并单元格等无法还原。")
                                        st.download_button(
                                            label="下载 Word 文件",
                                            data=f.read(),
                                            file_name="pdf_tables.docx",
                                            mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
                                        )
                                else:
                                    st.error(f"PDF 表格提取失败：{out_path}")
                        else:
                            if ext == ".pdf":
                                with st.spinner("正在将 PDF 转为 Word..."):
                                    ok, out_path = pdf_to_docx(file)
                                if ok and out_path and os.path.exists(out_path):
                                    with open(out_path, "rb") as f:
                                        st.success("Word 文件生成成功！请点击下方按钮下载。\n\n⚠️ 仅支持简单文本，复杂排版/图片/表格无法还原。")
                                        st.download_button(
                                            label="下载 Word 文件",
                                            data=f.read(),
                                            file_name="converted.docx",
                                            mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
                                        )
                                else:
                                    st.error(f"PDF 转 Word 失败：{out_path}")
                            elif ext == ".docx":
                                with st.spinner("正在将 Word 转为 PDF..."):
                                    ok, out_path = docx_to_pdf(file)
                                if ok and out_path and os.path.exists(out_path):
                                    with open(out_path, "rb") as f:
                                        st.success("PDF 文件生成成功！请点击下方按钮下载。")
                                        st.download_button(
                                            label="下载 PDF 文件",
                                            data=f.read(),
                                            file_name="converted.pdf",
                                            mime="application/pdf"
                                        )
                                else:
                                    st.error(f"Word 转 PDF 失败：{out_path}")
                            else:
                                st.error("仅支持 PDF 或 Word 文件！")
        with col2:
            with st.expander("JSON 转 PDF", expanded=True):
                with st.form("json2pdf_form"):
                    json_file = st.file_uploader("上传 JSON 文件以生成 PDF", type=["json"], key="json2pdf_file")
                    submit_pdf = st.form_submit_button("生成 PDF")
                if submit_pdf:
                    if json_file is None:
                        st.warning("请上传 JSON 文件。")
                    else:
                        with st.spinner("正在生成 PDF..."):
                            ok, pdf_path_or_err = json_to_pdf(json_file.read())
                        if ok and pdf_path_or_err and os.path.exists(pdf_path_or_err):
                            with open(pdf_path_or_err, "rb") as f:
                                st.success("PDF 生成成功！请点击下方按钮下载。")
                                st.download_button(
                                    label="下载 PDF 文件",
                                    data=f.read(),
                                    file_name="converted.pdf",
                                    mime="application/pdf"
                                )
                        else:
                            st.error(f"PDF 生成失败：{pdf_path_or_err}")

    with usage_tab:
        st.markdown("""
## 文件格式转换工具 - 使用说明

本工具用于常见文件格式的互转，适合批量数据处理、格式兼容等场景。

### 主要功能
- 支持 CSV、Excel、JSON 文件互转
- 支持 PDF ↔ Word 智能互转（仅文本，复杂排版/图片/表格无法还原）
- 支持 PDF 表格提取为 Word 表格（仅结构化内容，复杂表格样式、合并单元格等无法还原）
- 支持 JSON 转 PDF
- 本地处理，保障数据安全

### 使用步骤
1. 在功能页上传需要转换的文件
2. 选择目标格式或功能，点击转换
3. 下载转换后的文件

### 注意事项
- 文件大小建议不超过 20MB
- 数据文件需为标准格式，避免乱码
- 图片格式互转功能暂未开放
- JSON 转 PDF 需保证 JSON 格式正确
- PDF ↔ Word 智能互转仅支持简单文本内容，复杂排版/图片/表格无法还原
- PDF 表格提取仅支持简单表格，复杂表格样式、合并单元格等无法还原
- **如需高保真 PDF 转 Word（完全还原排版/图片/表格），请使用专业工具（如 Adobe、WPS、Smallpdf 等）**

### 场景举例
- 批量将 Excel/CSV/JSON 数据互转，便于数据分析和导入导出
- 将 PDF 文本内容快速提取为 Word 文档，便于编辑和二次处理
- 将 PDF 中结构化表格内容导出为 Word 表格，便于数据整理
- 将 JSON 数据生成 PDF 报告，便于归档和分享

如有更多需求或建议，欢迎反馈！
""")

if __name__ == "__main__":
    main()

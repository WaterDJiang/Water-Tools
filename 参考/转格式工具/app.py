import streamlit as st
import json
import markdown
from pathlib import Path
import tempfile
import os
import zipfile
import io
from converters import FormatConverter
import concurrent.futures
from threading import Lock
import logging

# 设置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 设置页面配置
st.set_page_config(
    page_title="文件格式转换工具集",
    page_icon="🛠️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 自定义CSS样式
st.markdown("""
    <style>
    /* 通用样式 */
    .stApp {
        max-width: 1200px;
        margin: 0 auto;
        padding: 1rem;
    }
    
    /* 侧边栏样式 */
    .stSidebar {
        background-color: rgba(151, 166, 195, 0.15);
        padding: 2rem 1rem;
    }
    
    .stSidebar .stMarkdown {
        text-align: left;
    }
    
    /* 工具容器样式 */
    .tool-container {
        padding: 2rem;
        border-radius: 10px;
        border: 1px solid rgba(151, 166, 195, 0.2);
        margin-bottom: 2rem;
        background-color: rgba(255, 255, 255, 0.05);
    }
    
    /* 标题样式 */
    h1, h2, h3, h4, h5, h6 {
        color: var(--text-color);
    }
    
    /* 按钮样式 */
    .stButton button {
        width: 100%;
        border-radius: 5px;
        padding: 0.75rem 1.5rem;
        background-color: #2778c4;
        color: white;
        border: none;
        transition: all 0.3s ease;
        font-size: 1rem;
        font-weight: 500;
        margin-top: 1rem;
    }
    
    .stButton button:hover {
        background-color: #1c5c9c;
        box-shadow: 0 2px 4px rgba(0,0,0,0.2);
    }
    
    /* 上传区域样式 */
    .uploadedFile {
        border: 1px dashed rgba(151, 166, 195, 0.4);
        border-radius: 5px;
        padding: 1rem;
        margin: 1rem 0;
    }
    
    /* 进度条样式 */
    .stProgress > div > div {
        background-color: #2778c4;
    }
    
    /* 成功消息样式 */
    .stSuccess {
        padding: 1rem;
        border-radius: 5px;
        background-color: rgba(40, 167, 69, 0.2);
    }
    
    /* 信息提示样式 */
    .stInfo {
        background-color: rgba(151, 166, 195, 0.15);
        padding: 1rem;
        border-radius: 5px;
        margin: 1rem 0;
    }
    
    /* 卡片容器样式 */
    .card {
        background-color: rgba(255, 255, 255, 0.05);
        border-radius: 10px;
        padding: 1.5rem;
        margin-bottom: 1rem;
        border: 1px solid rgba(151, 166, 195, 0.2);
    }
    
    /* 分隔线样式 */
    hr {
        margin: 2rem 0;
        border: none;
        border-top: 1px solid rgba(151, 166, 195, 0.2);
    }
    
    /* 列表样式 */
    .sidebar-list {
        margin-left: 1rem;
        list-style-type: none;
    }
    .sidebar-list li {
        margin-bottom: 0.5rem;
    }
    .sidebar-list li:before {
        content: "•";
        color: #2778c4;
        font-weight: bold;
        display: inline-block;
        width: 1em;
        margin-left: -1em;
    }
    </style>
""", unsafe_allow_html=True)

def get_file_format(filename):
    """获取文件格式"""
    ext = Path(filename).suffix.lower()
    format_map = {
        '.json': 'json',
        '.md': 'md',
        '.txt': 'txt',
        '.pdf': 'pdf'
    }
    return format_map.get(ext, 'unknown')

def convert_single_file(file_data, input_format, output_format, temp_dir):
    """
    转换单个文件的函数
    """
    try:
        # 解包文件数据
        file_content, file_name, file_index = file_data
        
        # 记录文件信息
        logger.info(f"开始处理文件: {file_name}")
        logger.info(f"输入格式: {input_format}")
        logger.info(f"输出格式: {output_format}")
        
        # 转换内容
        logger.info("调用转换器...")
        converted_content = FormatConverter.convert_file(
            file_content,
            input_format,
            output_format
        )
        
        if isinstance(converted_content, str) and converted_content.startswith("错误"):
            logger.error(f"转换失败: {converted_content}")
            return None, converted_content, file_name
            
        logger.info("转换完成，准备保存文件...")
        
        # 确定输出文件名
        output_filename = f"{Path(file_name).stem}.{output_format}"
        output_path = os.path.join(temp_dir, output_filename)
        
        # 保存转换后的文件
        if output_format == 'pdf' and os.path.exists(converted_content):
            # 如果是PDF文件，直接移动临时文件
            os.rename(converted_content, output_path)
        else:
            # 其他格式直接写入文件
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(converted_content)
        
        return output_path, None, file_name
    except Exception as e:
        error_msg = str(e)
        logger.error(f"处理文件 {file_name} 时出错: {error_msg}")
        return None, error_msg, file_name

def main():
    # 侧边栏
    with st.sidebar:
        st.title("🛠️ 文件转换工具集")
        st.markdown("---")
        
        # 工具选择
        selected_tool = st.radio(
            "选择工具",
            ["格式转换器", "更多工具开发中..."],
            index=0,
            help="选择要使用的转换工具"
        )
        
        st.markdown("---")
        st.markdown("### 使用说明")
        st.markdown("""
        <ol class="sidebar-list">
            <li>选择要转换的文件（支持多选）</li>
            <li>选择目标输出格式</li>
            <li>点击转换按钮开始处理</li>
            <li>转换完成后下载文件</li>
        </ol>
        """, unsafe_allow_html=True)

        st.markdown("### 支持格式")
        st.markdown("""
        <ul class="sidebar-list">
            <li>JSON (.json)</li>
            <li>Markdown (.md)</li>
            <li>Text (.txt)</li>
            <li>PDF (.pdf)</li>
        </ul>
        """, unsafe_allow_html=True)
    
    # 主要内容区域
    if selected_tool == "格式转换器":
        # 使用两列布局
        col1, col2 = st.columns([2, 3])
        
        with col1:
            st.header("📄 文件转换器")
            st.markdown("""
            <div class="card">
                <p>支持多种格式文件的相互转换，包括：</p>
                <ul>
                    <li>JSON 转换</li>
                    <li>Markdown 转换</li>
                    <li>文本转换</li>
                    <li>PDF 生成</li>
                </ul>
            </div>
            """, unsafe_allow_html=True)
            
            # 文件上传区域
            uploaded_files = st.file_uploader(
                "上传文件（支持多文件）",
                type=['json', 'md', 'txt', 'pdf'],
                accept_multiple_files=True,
                help="可以同时选择多个文件进行转换"
            )
        
        with col2:
            if uploaded_files:
                st.markdown("""
                <div class="card">
                    <h3>转换设置</h3>
                """, unsafe_allow_html=True)
                
                # 获取第一个文件的格式作为输入格式
                first_file = uploaded_files[0]
                input_format = get_file_format(first_file.name)
                if input_format == 'unknown':
                    st.error(f"不支持的文件格式: {first_file.name}")
                    return
                
                # 获取支持的格式
                supported_formats = FormatConverter.get_supported_formats()
                
                # 根据输入格式显示可用的输出格式
                available_formats = supported_formats.get(input_format, [])
                if available_formats:
                    output_format = st.selectbox(
                        "选择输出格式",
                        available_formats,
                        format_func=lambda x: f"{x.upper()} (.{x})",
                        help="选择要转换成的目标格式"
                    )
                    
                    if st.button("🚀 开始转换", type="primary", use_container_width=True):
                        try:
                            # 创建进度显示容器
                            progress_container = st.container()
                            with progress_container:
                                st.markdown("### 转换进度")
                                progress_bar = st.progress(0)
                                status_text = st.empty()
                                error_container = st.empty()
                                
                                # 显示总文件数
                                total_files = len(uploaded_files)
                                st.info(f"总计需要转换 {total_files} 个文件")
                                
                                # 创建临时目录存储转换后的文件
                                with tempfile.TemporaryDirectory() as temp_dir:
                                    converted_files = []
                                    errors = []
                                    
                                    # 准备文件数据
                                    file_data = []
                                    for i, uploaded_file in enumerate(uploaded_files):
                                        try:
                                            content = uploaded_file.read()
                                            file_data.append((content, uploaded_file.name, i))
                                            # 重置文件指针，以便后续可能的读取
                                            uploaded_file.seek(0)
                                        except Exception as e:
                                            errors.append(f"{uploaded_file.name}: 读取文件失败 - {str(e)}")
                                            continue
                                    
                                    if not file_data:
                                        st.error("没有可以转换的文件")
                                        return
                                    
                                    # 使用线程池并发处理文件
                                    with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
                                        # 提交所有转换任务
                                        future_to_file = {
                                            executor.submit(
                                                convert_single_file,
                                                data,
                                                input_format,
                                                output_format,
                                                temp_dir
                                            ): data for data in file_data
                                        }
                                        
                                        # 收集结果
                                        completed = 0
                                        for future in concurrent.futures.as_completed(future_to_file):
                                            file_data = future_to_file[future]
                                            file_name = file_data[1]  # 获取文件名
                                            try:
                                                output_path, error, _ = future.result()
                                                completed += 1
                                                progress = completed / total_files
                                                
                                                # 更新进度
                                                progress_bar.progress(progress, f"进度: {int(progress * 100)}%")
                                                
                                                if error:
                                                    errors.append(f"{file_name}: {error}")
                                                    status_text.markdown(f"❌ 失败: **{file_name}** - {error}")
                                                elif output_path:
                                                    converted_files.append(output_path)
                                                    status_text.markdown(f"✅ 已完成: **{file_name}**")
                                            except Exception as e:
                                                completed += 1
                                                progress = completed / total_files
                                                progress_bar.progress(progress, f"进度: {int(progress * 100)}%")
                                                
                                                error_msg = str(e)
                                                errors.append(f"{file_name}: {error_msg}")
                                                status_text.markdown(f"❌ 失败: **{file_name}** - {error_msg}")
                                                logger.error(f"处理文件 {file_name} 时出错: {error_msg}")
                                    
                                    # 显示错误信息（如果有）
                                    if errors:
                                        error_text = "\n".join(errors)
                                        error_container.error(f"转换过程中出现以下错误：\n{error_text}")
                                    
                                    # 如果有成功转换的文件，创建下载链接
                                    if converted_files:
                                        try:
                                            # 创建ZIP文件
                                            zip_buffer = io.BytesIO()
                                            with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
                                                for file_path in converted_files:
                                                    zip_file.write(
                                                        file_path,
                                                        os.path.basename(file_path)
                                                    )
                                            
                                            # 更新状态并提供下载链接
                                            status_text.markdown("### ✅ 转换完成！")
                                            st.success(f"成功转换 {len(converted_files)} 个文件！")
                                            
                                            # 显示成功率
                                            success_rate = (len(converted_files) / total_files) * 100
                                            st.markdown(f"转换成功率: **{success_rate:.1f}%**")
                                            
                                            st.download_button(
                                                label="📥 下载转换后的文件",
                                                data=zip_buffer.getvalue(),
                                                file_name=f"converted_files_{output_format}.zip",
                                                mime="application/zip",
                                                use_container_width=True
                                            )
                                        except Exception as e:
                                            error_msg = str(e)
                                            st.error(f"创建下载文件时出错: {error_msg}")
                                            logger.error(f"创建下载文件时出错: {error_msg}")
                        except Exception as e:
                            error_msg = str(e)
                            st.error(f"转换过程中出现错误: {error_msg}")
                            logger.error(f"转换过程中出现错误: {error_msg}")
                else:
                    st.error(f"不支持 {input_format.upper()} 格式的转换")

if __name__ == "__main__":
    main() 
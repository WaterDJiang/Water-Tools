import json
import markdown
from fpdf import FPDF
from docx import Document
import tempfile
import os
from pathlib import Path
import logging
import re
from typing import Any, Union, Dict, List

# 设置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class PDF(FPDF):
    def __init__(self):
        super().__init__()
        self.font_path = None
        
    def set_chinese_font(self):
        """设置中文字体"""
        font_paths = [
            '/System/Library/Fonts/PingFang.ttc',  # macOS 系统字体
            '/System/Library/Fonts/STHeiti Light.ttc',  # macOS 系统字体
            '/System/Library/Fonts/Hiragino Sans GB.ttc',  # macOS 系统字体
            os.path.join(os.path.dirname(__file__), 'fonts', 'SimSun.ttf'),  # 相对路径
            'C:\\Windows\\Fonts\\SimSun.ttf',  # Windows 系统字体
            '/usr/share/fonts/truetype/droid/DroidSansFallbackFull.ttf',  # Linux 系统字体
        ]
        
        for font_path in font_paths:
            if os.path.exists(font_path):
                try:
                    logger.info(f"尝试加载字体: {font_path}")
                    # 使用 add_font 的新语法
                    self.font_path = font_path
                    self.add_font("CustomFont", fname=font_path)
                    logger.info("字体加载成功")
                    return True
                except Exception as e:
                    logger.error(f"加载字体失败: {str(e)}")
                    continue
        
        logger.error("未找到可用的中文字体")
        return False

    def footer(self):
        """添加页脚"""
        self.set_y(-15)
        self.set_font('CustomFont', size=8)
        self.cell(0, 10, f'第 {self.page_no()} 页', align='C')

class FormatConverter:
    """格式转换器类，处理不同格式之间的转换"""
    
    @staticmethod
    def sanitize_json_value(value: Any) -> Union[str, int, float, bool, None, Dict, List]:
        """
        清理和标准化 JSON 值，确保所有值都是可序列化的基本类型
        """
        if isinstance(value, (str, int, float, bool)) or value is None:
            return value
        elif isinstance(value, dict):
            return {str(k): FormatConverter.sanitize_json_value(v) for k, v in value.items()}
        elif isinstance(value, list):
            return [FormatConverter.sanitize_json_value(item) for item in value]
        elif callable(value):
            # 处理方法/函数类型
            return str(value.__name__ if hasattr(value, '__name__') else value)
        elif hasattr(value, '__dict__'):
            # 处理对象类型，转换为字典
            return FormatConverter.sanitize_json_value(value.__dict__)
        else:
            # 其他类型转换为字符串
            return str(value)

    @staticmethod
    def sanitize_json_data(data: Any) -> Any:
        """
        清理整个 JSON 数据结构，确保所有值都是可序列化的
        """
        try:
            # 如果输入是字符串，尝试解析它
            if isinstance(data, str):
                try:
                    data = json.loads(data)
                except json.JSONDecodeError:
                    return data

            return FormatConverter.sanitize_json_value(data)
        except Exception as e:
            logger.error(f"清理 JSON 数据时出错: {str(e)}")
            return str(data)

    @staticmethod
    def format_json_for_pdf(obj: Any, indent: int = 0) -> str:
        """格式化 JSON 对象为易读的文本形式"""
        try:
            # 首先清理和标准化数据
            obj = FormatConverter.sanitize_json_value(obj)
            
            lines = []
            indent_str = "    " * indent
            
            if isinstance(obj, dict):
                if not obj:  # 处理空字典
                    return "{}"
                lines.append("{")
                items = list(obj.items())
                for i, (key, value) in enumerate(items):
                    # 确保 key 是字符串类型
                    key_str = str(key)
                    formatted_value = FormatConverter.format_json_for_pdf(value, indent + 1)
                    comma = "," if i < len(items) - 1 else ""
                    lines.append(f'{indent_str}    "{key_str}": {formatted_value}{comma}')
                lines.append(indent_str + "}")
                return "\n".join(lines)
            elif isinstance(obj, list):
                if not obj:  # 处理空列表
                    return "[]"
                lines.append("[")
                for i, item in enumerate(obj):
                    formatted_item = FormatConverter.format_json_for_pdf(item, indent + 1)
                    comma = "," if i < len(obj) - 1 else ""
                    lines.append(f"{indent_str}    {formatted_item}{comma}")
                lines.append(indent_str + "]")
                return "\n".join(lines)
            elif isinstance(obj, str):
                # 处理多行字符串，移除不可打印字符
                clean_str = ''.join(char for char in obj if char.isprintable() or char in ['\n', '\t'])
                if "\n" in clean_str:
                    escaped = clean_str.replace('"', '\\"').replace("\n", "\\n")
                    return f'"{escaped}"'
                return f'"{clean_str}"'
            elif isinstance(obj, (int, float)):
                return str(obj)
            elif obj is None:
                return "null"
            elif isinstance(obj, bool):
                return str(obj).lower()
            else:
                # 处理其他类型
                return f'"{str(obj)}"'
        except Exception as e:
            logger.error(f"格式化 JSON 时出错: {str(e)}")
            return f'"[Error: {str(e)}]"'

    @staticmethod
    def json_to_pdf(content: Union[str, bytes]) -> str:
        """将JSON内容转换为PDF格式，保持原始格式"""
        try:
            # 解析 JSON 内容
            try:
                if isinstance(content, bytes):
                    content = content.decode('utf-8')
                    logger.info("成功将字节内容转换为字符串")
                
                # 尝试解析 JSON 并打印内容的前100个字符（用于调试）
                logger.info(f"尝试解析的JSON内容（前100个字符）: {content[:100]}")
                
                # 首先解析 JSON
                data = json.loads(content)
                logger.info("JSON解析成功")
                
                # 清理和标准化数据
                data = FormatConverter.sanitize_json_data(data)
                logger.info("JSON数据清理完成")
                
            except json.JSONDecodeError as e:
                error_msg = f"JSON解析错误（位置 {e.pos}）: {str(e)}"
                logger.error(error_msg)
                return error_msg
            except Exception as e:
                error_msg = f"处理JSON内容时出错: {str(e)}"
                logger.error(error_msg)
                return error_msg

            # 创建临时目录
            temp_dir = tempfile.mkdtemp()
            output_filename = 'output.pdf'
            output_path = os.path.join(temp_dir, output_filename)
            
            try:
                # 创建 PDF 对象
                pdf = PDF()
                pdf.set_margin(10)  # 设置较小的边距
                
                # 设置中文字体
                if not pdf.set_chinese_font():
                    return "错误：未找到合适的中文字体，请确保已安装中文字体"
                
                # 添加页面
                pdf.add_page()
                pdf.set_font('CustomFont', size=9)  # 使用更小的字号
                pdf.set_auto_page_break(auto=True, margin=15)
                
                # 格式化 JSON 并写入 PDF
                formatted_json = FormatConverter.format_json_for_pdf(data)
                
                # 按行写入，保持缩进
                for line in formatted_json.split('\n'):
                    # 移除不可打印字符
                    clean_line = ''.join(char for char in line if char.isprintable() or char in ['\n', '\t', ' '])
                    if clean_line.strip():  # 只写入非空行
                        pdf.cell(0, 6, txt=clean_line, new_x="LMARGIN", new_y="NEXT")
                
                # 保存 PDF
                try:
                    pdf.output(output_path)
                    
                    # 验证生成的文件
                    if os.path.exists(output_path) and os.path.getsize(output_path) > 0:
                        logger.info(f"PDF生成成功: {output_path}")
                        return output_path
                    else:
                        logger.error("生成的PDF文件为空")
                        return "错误：生成的PDF文件为空"
                except Exception as e:
                    logger.error(f"保存PDF时出错: {str(e)}")
                    return f"保存PDF时出错: {str(e)}"
                
            except Exception as e:
                logger.error(f"创建PDF时出错: {str(e)}")
                return f"创建PDF时出错: {str(e)}"
                
        except Exception as e:
            logger.error(f"转换过程中出错: {str(e)}")
            return f"转换错误: {str(e)}"

    @staticmethod
    def json_to_md(content):
        """将JSON内容转换为Markdown格式"""
        try:
            data = json.loads(content)
            md_content = []
            
            def process_dict(d, level=0):
                for key, value in d.items():
                    prefix = "#" * (level + 1) if level < 6 else "######"
                    md_content.append(f"{prefix} {key}\n")
                    
                    if isinstance(value, dict):
                        process_dict(value, level + 1)
                    elif isinstance(value, list):
                        for item in value:
                            if isinstance(item, dict):
                                process_dict(item, level + 1)
                            else:
                                md_content.append(f"- {item}\n")
                    else:
                        md_content.append(f"{value}\n")
                    
                    md_content.append("\n")
            
            if isinstance(data, dict):
                process_dict(data)
            elif isinstance(data, list):
                for item in data:
                    if isinstance(item, dict):
                        process_dict(item)
                    else:
                        md_content.append(f"- {item}\n")
            
            return "".join(md_content)
        except Exception as e:
            return f"转换错误: {str(e)}"

    @staticmethod
    def md_to_json(content):
        """将Markdown内容转换为JSON格式"""
        try:
            lines = content.split('\n')
            result = {}
            current_section = result
            section_stack = []
            
            for line in lines:
                if line.strip():
                    if line.startswith('#'):
                        # 计算标题级别
                        level = len(line.split()[0])
                        title = ' '.join(line.split()[1:])
                        
                        # 根据级别调整当前节点
                        while len(section_stack) >= level:
                            section_stack.pop()
                        
                        current_section = result
                        for section in section_stack:
                            current_section = current_section[section]
                        
                        current_section[title] = {}
                        section_stack.append(title)
                        current_section = current_section[title]
                    elif line.startswith('- '):
                        content = line[2:].strip()
                        if isinstance(current_section, dict):
                            current_section['items'] = current_section.get('items', [])
                            current_section['items'].append(content)
                    else:
                        if isinstance(current_section, dict):
                            current_section['content'] = line.strip()
            
            return json.dumps(result, ensure_ascii=False, indent=2)
        except Exception as e:
            return f"转换错误: {str(e)}"

    @staticmethod
    def text_to_json(content):
        """将纯文本转换为JSON格式"""
        try:
            paragraphs = content.split('\n\n')
            result = {
                "content": {
                    "paragraphs": [p.strip() for p in paragraphs if p.strip()]
                }
            }
            return json.dumps(result, ensure_ascii=False, indent=2)
        except Exception as e:
            return f"转换错误: {str(e)}"

    @staticmethod
    def convert_file(file_content, input_format, output_format):
        """
        转换文件格式
        :param file_content: 文件内容
        :param input_format: 输入格式
        :param output_format: 输出格式
        :return: 转换后的内容
        """
        try:
            # 确保输入内容是字符串类型
            if isinstance(file_content, bytes):
                file_content = file_content.decode('utf-8')
            
            # JSON 转换
            if input_format == 'json':
                if output_format == 'md':
                    return FormatConverter.json_to_md(file_content)
                elif output_format == 'pdf':
                    return FormatConverter.json_to_pdf(file_content)
                elif output_format == 'txt':
                    # 直接使用格式化的 JSON 作为文本
                    try:
                        data = json.loads(file_content)
                        return json.dumps(data, ensure_ascii=False, indent=2)
                    except Exception as e:
                        return f"JSON格式化错误: {str(e)}"
            
            # Markdown 转换
            elif input_format == 'md':
                if output_format == 'json':
                    return FormatConverter.md_to_json(file_content)
                elif output_format == 'pdf':
                    html = markdown.markdown(file_content)
                    return FormatConverter.html_to_pdf(html)
                elif output_format == 'txt':
                    return file_content
            
            # 文本转换
            elif input_format == 'txt':
                if output_format == 'json':
                    return FormatConverter.text_to_json(file_content)
                elif output_format == 'md':
                    # 简单的文本到 Markdown 转换
                    return file_content
                elif output_format == 'pdf':
                    return FormatConverter.text_to_pdf(file_content)
            
            # PDF 转换（如果支持）
            elif input_format == 'pdf':
                return "错误：暂不支持 PDF 作为输入格式"
            
            return f"错误：不支持从 {input_format} 转换到 {output_format}"
            
        except Exception as e:
            logger.error(f"转换过程中出错: {str(e)}")
            return f"转换错误: {str(e)}"

    @staticmethod
    def get_supported_formats():
        """获取支持的格式转换映射"""
        return {
            'json': ['md', 'pdf', 'txt'],
            'md': ['json', 'pdf', 'txt'],
            'txt': ['json', 'md', 'pdf'],
            'pdf': []  # PDF 暂时只支持作为输出格式
        }

    @staticmethod
    def html_to_pdf(html_content: str) -> str:
        """将HTML内容转换为PDF格式"""
        try:
            # 创建临时目录
            temp_dir = tempfile.mkdtemp()
            output_filename = 'output.pdf'
            output_path = os.path.join(temp_dir, output_filename)
            
            try:
                # 创建 PDF 对象
                pdf = PDF()
                pdf.set_margin(10)
                
                # 设置中文字体
                if not pdf.set_chinese_font():
                    return "错误：未找到合适的中文字体，请确保已安装中文字体"
                
                # 添加页面
                pdf.add_page()
                pdf.set_font('CustomFont', size=10)
                pdf.set_auto_page_break(auto=True, margin=15)
                
                # 移除HTML标签，保留文本内容
                text_content = re.sub('<[^<]+?>', '', html_content)
                text_content = text_content.replace('&nbsp;', ' ')
                text_content = text_content.replace('&lt;', '<')
                text_content = text_content.replace('&gt;', '>')
                text_content = text_content.replace('&amp;', '&')
                
                # 按行写入文本
                for line in text_content.split('\n'):
                    if line.strip():
                        pdf.multi_cell(0, 6, txt=line.strip())
                    else:
                        pdf.ln(3)  # 空行
                
                # 保存 PDF
                pdf.output(output_path)
                
                if os.path.exists(output_path) and os.path.getsize(output_path) > 0:
                    logger.info(f"PDF生成成功: {output_path}")
                    return output_path
                else:
                    logger.error("生成的PDF文件为空")
                    return "错误：生成的PDF文件为空"
                    
            except Exception as e:
                logger.error(f"生成PDF时出错: {str(e)}")
                return f"生成PDF时出错: {str(e)}"
                
        except Exception as e:
            logger.error(f"创建临时目录时出错: {str(e)}")
            return f"创建临时目录时出错: {str(e)}"

    @staticmethod
    def text_to_pdf(text_content: str) -> str:
        """将纯文本内容转换为PDF格式"""
        try:
            # 创建临时目录
            temp_dir = tempfile.mkdtemp()
            output_filename = 'output.pdf'
            output_path = os.path.join(temp_dir, output_filename)
            
            try:
                # 创建 PDF 对象
                pdf = PDF()
                pdf.set_margin(10)
                
                # 设置中文字体
                if not pdf.set_chinese_font():
                    return "错误：未找到合适的中文字体，请确保已安装中文字体"
                
                # 添加页面
                pdf.add_page()
                pdf.set_font('CustomFont', size=10)
                pdf.set_auto_page_break(auto=True, margin=15)
                
                # 按行写入文本
                for line in text_content.split('\n'):
                    if line.strip():
                        pdf.multi_cell(0, 6, txt=line)
                    else:
                        pdf.ln(3)  # 空行
                
                # 保存 PDF
                pdf.output(output_path)
                
                if os.path.exists(output_path) and os.path.getsize(output_path) > 0:
                    logger.info(f"PDF生成成功: {output_path}")
                    return output_path
                else:
                    logger.error("生成的PDF文件为空")
                    return "错误：生成的PDF文件为空"
                    
            except Exception as e:
                logger.error(f"生成PDF时出错: {str(e)}")
                return f"生成PDF时出错: {str(e)}"
                
        except Exception as e:
            logger.error(f"创建临时目录时出错: {str(e)}")
            return f"创建临时目录时出错: {str(e)}" 
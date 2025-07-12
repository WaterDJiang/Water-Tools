# 文件格式转换工具集

这是一个基于 Streamlit 和 Python 开发的文件格式转换工具集网站。支持多种格式文件的相互转换。

## 功能特点

- 支持多种格式文件的批量上传
- 支持格式：JSON、Markdown、TXT、PDF
- 实时转换进度显示
- 批量下载转换后的文件（ZIP 格式）
- 美观的用户界面
- 模块化设计，易于扩展新功能

## 安装要求

```bash
Python 3.7+
```

## 安装步骤

1. 克隆项目到本地
2. 安装依赖包：
```bash
pip install -r requirements.txt
```
3. 设置中文字体（用于生成 PDF）：
   - 在项目根目录下创建 `fonts` 文件夹
   - 下载宋体字体文件 (SimSun.ttf)
   - 将字体文件重命名为 `SimSun.ttf` 并放入 `fonts` 文件夹

## 运行方法

在项目目录下运行：
```bash
streamlit run app.py
```

## 使用说明

1. 启动应用后，在左侧边栏选择要使用的工具
2. 在主界面上传一个或多个文件
3. 选择期望的输出格式
4. 点击"开始转换"按钮
5. 等待转换完成后，点击下载按钮获取转换后的文件

## 支持的转换格式

目前支持的格式：
- JSON (.json)
- Markdown (.md)
- Text (.txt)
- PDF (.pdf)

支持的转换路径：
- JSON -> Markdown, PDF, TXT
- Markdown -> JSON, PDF, TXT
- TXT -> JSON, PDF, Markdown
- PDF -> TXT, Markdown

## 注意事项

- 上传的文件需要是有效的格式
- 建议单次批量转换的文件数量不要过多
- 转换完成前请勿刷新页面
- 生成 PDF 需要正确设置中文字体

## 后续开发计划

- [ ] 添加更多输出格式支持（Word、Excel 等）
- [ ] 添加更多文件格式之间的互转功能
- [ ] 优化转换算法和性能
- [ ] 添加文件预览功能
- [ ] 支持更多字体选择 
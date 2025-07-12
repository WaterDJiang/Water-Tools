import os
import requests
from pathlib import Path

def download_font():
    """下载中文字体"""
    fonts_dir = Path('fonts')
    fonts_dir.mkdir(exist_ok=True)
    
    simsun_path = fonts_dir / 'SimSun.ttf'
    
    if not simsun_path.exists():
        # 从清华大学镜像站下载宋体
        url = 'https://mirrors.tuna.tsinghua.edu.cn/adobe-fonts/source-han-serif/SubsetOTF/CN/SourceHanSerifCN-Regular.otf'
        
        try:
            response = requests.get(url, stream=True)
            response.raise_for_status()
            
            with open(simsun_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
            
            print("字体下载完成！")
        except Exception as e:
            print(f"下载字体时出错: {str(e)}")
            print("请手动下载宋体字体文件并放置在 fonts/SimSun.ttf")
    else:
        print("字体文件已存在")

if __name__ == "__main__":
    download_font() 
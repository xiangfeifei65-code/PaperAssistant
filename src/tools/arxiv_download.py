import os
import re
import requests
from src.utils.logger import logger


def sanitize_filename(title: str) -> str:
    """清理标题中不适合作为文件名的字符"""
    # 删除非法字符
    title = re.sub(r'[\\/*?:"<>|]', '', title)
    # 空格替换为下划线
    title = re.sub(r'\s+', '_', title)
    # 限制长度
    if len(title) > 200:
        title = title[:200]
    return title


def download_pdf(arxiv_id: str, title: str,topic: str = "", output_dir: str = "data/pdfs") -> str:
    """
    通过 arXiv 的 PDF 直链下载论文，保存为标题.pdf
    """

    # 如果提供了 topic，则在 output_dir 下创建 topic 子目录
    if topic:
        output_dir = os.path.join(output_dir, topic)
    os.makedirs(output_dir, exist_ok=True)

    os.makedirs(output_dir, exist_ok=True)

    # 关键：去掉末尾的版本号（如 v1, v2, v3），只保留基础 ID
    # 例如：2508.08733v3 -> 2508.08733
    base_id = re.sub(r'v\d+$', '', arxiv_id)
    pdf_url = f"https://arxiv.org/pdf/{base_id}.pdf"

    safe_title = sanitize_filename(title)
    filename = f"{safe_title}.pdf"
    filepath = os.path.join(output_dir, filename)

    try:
        logger.info(f"正在下载: {pdf_url}")
        # 增加超时时间，并模拟浏览器头，防止部分网络拦截
        headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
        }
        response = requests.get(pdf_url, timeout=30, headers=headers)
        response.raise_for_status()  # 检查 HTTP 状态码

        with open(filepath, 'wb') as f:
            f.write(response.content)

        logger.info(f"PDF 下载成功: {filepath}")
        return filepath

    except requests.exceptions.RequestException as e:
        logger.error(f"下载失败 ({arxiv_id}): {e}")
    except Exception as e:
        logger.error(f"保存文件失败 ({arxiv_id}): {e}")

    return None
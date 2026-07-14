import os
import json
import glob
from src.utils.logger import logger

def load_existing_results(topic: str):
    """从 outputs/{topic}/ 下读取最新的 JSON 结果文件，返回论文列表（可能为空）"""
    topic_dir = f"outputs/{topic}"
    if not os.path.exists(topic_dir):
        logger.info(f"目录不存在: {topic_dir}")
        return []

    # 1. 优先读取固定文件名 {topic}.json（新格式）
    fixed_json = os.path.join(topic_dir, f"{topic}.json")
    if os.path.exists(fixed_json):
        try:
            with open(fixed_json, 'r', encoding='utf-8') as f:
                data = json.load(f)
                if isinstance(data, list):
                    logger.info(f"从固定文件加载成功: {fixed_json}，共 {len(data)} 篇")
                    return data
                else:
                    logger.warning(f"固定文件内容不是列表，类型: {type(data)}，尝试其他文件")
        except Exception as e:
            logger.warning(f"读取固定文件失败: {e}")

    # 2. 回退：查找所有 JSON 文件，取最新的
    json_files = glob.glob(os.path.join(topic_dir, "*.json"))
    if not json_files:
        logger.info(f"没有找到任何 JSON 文件: {topic_dir}")
        return []
    latest_file = max(json_files, key=os.path.getmtime)
    logger.info(f"回退读取最新文件: {latest_file}")
    try:
        with open(latest_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
            logger.info(f"文件内容类型: {type(data)}")
            if isinstance(data, list):
                logger.info(f"从旧格式文件加载成功，共 {len(data)} 篇")
                return data
            else:
                logger.warning(f"文件内容不是列表，类型: {type(data)}")
                return []
    except Exception as e:
        logger.error(f"读取 JSON 失败: {e}")
        return []

def merge_and_deduplicate(existing, new):
    """合并两个论文列表，按标题去重（新结果替换旧结果）"""
    seen_titles = set()
    merged = []
    for item in existing:
        title = item.get("paper", "")
        if title not in seen_titles:
            seen_titles.add(title)
            merged.append(item)
    for item in new:
        title = item.get("paper", "")
        if title in seen_titles:
            for i, old in enumerate(merged):
                if old.get("paper") == title:
                    merged[i] = item
                    break
        else:
            seen_titles.add(title)
            merged.append(item)
    return merged
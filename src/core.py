from typing import List, Dict
from tqdm import tqdm
from src.tools.arxiv_search import search_papers, Paper
from src.agents.summary_agent import summary_agent
from src.agents.citation_agent import citation_agent
from src.utils.retry import retry_on_exception
from src.utils.logger import logger
from src.utils.config import config
import json
import os
import time
import glob
from datetime import datetime
from src.utils.cache import get_cache_key, get_cached, save_cache

@retry_on_exception()
def run_summary(paper_text: str) -> str:
    key = get_cache_key(paper_text, "summary")
    cached = get_cached(key)
    if cached is not None:
        logger.info("使用缓存的摘要结果")
        return cached
    result = summary_agent.run(f"请总结论文：\n\n{paper_text}")
    result = result.strip()
    save_cache(key, result)
    return result

@retry_on_exception()
def run_citation(paper_text: str) -> str:
    key = get_cache_key(paper_text, "citation")
    cached = get_cached(key)
    if cached is not None:
        logger.info("使用缓存的引用结果")
        return cached
    result = citation_agent.run(paper_text)
    result = result.strip()
    save_cache(key, result)
    return result

def process_paper(paper: Paper) -> Dict[str, str]:
    paper_text = paper.to_text()
    logger.info(f"Processing paper: {paper.title}")
    summary = run_summary(paper_text)
    citation = run_citation(paper_text)
    return {
        "paper": paper.title,
        "summary": summary,
        "citation": citation,
        "arxiv_id": paper.arxiv_id
    }

def paper_assistant(
    topic: str,
    max_results: int = None,
    category: str = None,
    year_from: int = None,
    sort_by: str = "Relevance",
    exclude_ids: list = None
) -> List[Dict[str, str]]:
    # 如果用户输入的是中文，自动翻译成英文
    if any('\u4e00' <= char <= '\u9fff' for char in topic):
        translated_topic = None
        max_retries = 3
        for attempt in range(max_retries):
            try:
                from deep_translator import GoogleTranslator
                translator = GoogleTranslator(source='auto', target='en')
                translated_topic = translator.translate(topic)
                if translated_topic:
                    logger.info(f"关键词已翻译: '{topic}' -> '{translated_topic}'")
                    topic = translated_topic
                    break  # 成功则退出循环
                else:
                    logger.warning("翻译结果为空，将尝试重试")
            except Exception as e:
                logger.warning(f"翻译尝试 {attempt + 1}/{max_retries} 失败: {e}")
                if attempt < max_retries - 1:
                    time.sleep(2)  # 等待2秒后重试
                else:
                    logger.warning("所有翻译尝试均失败，将使用原始关键词")
        if not translated_topic:
            # 如果最终没有成功翻译，使用原始关键词
            pass
    else:
        logger.info("关键词已为英文，无需翻译")

    if max_results is None:
        max_results = config.DEFAULT_MAX_RESULTS

    logger.info(f"Paper assistant started for topic '{topic}'")
    papers = search_papers(
        keyword=topic,
        max_results=max_results,
        category=category,
        year_from=year_from,
        sort_by=sort_by,
        exclude_ids = exclude_ids
    )
    results = []

    for paper in tqdm(papers, desc="Processing papers", unit="paper"):
        try:
            result = process_paper(paper)
            results.append(result)
        except Exception as e:
            logger.error(f"Failed to process '{paper.title}': {e}")
            results.append({
                "paper": paper.title,
                "summary": f"ERROR: {e}",
                "citation": "ERROR: citation generation failed",
            })

    logger.info(f"Assistant finished, processed {len(results)} papers")
    return results

def save_results(results: list, topic: str, output_dir: str = "outputs"):
    """
    将结果保存为 JSON 和 Markdown 文件，固定文件名，合并已有结果（按标题去重）。
    """
    topic_dir = os.path.join(output_dir, topic)
    os.makedirs(topic_dir, exist_ok=True)

    json_path = os.path.join(topic_dir, f"{topic}.json")
    md_path = os.path.join(topic_dir, f"{topic}.md")

    # 1. 如果已有 JSON，读取并合并（按标题去重，新数据覆盖旧数据）
    existing_data = []
    if os.path.exists(json_path):
        try:
            with open(json_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                if isinstance(data, list):
                    existing_data = data
        except Exception as e:
            logger.warning(f"读取已有 JSON 失败，将覆盖: {e}")

    # ===== 调试日志：读取已有数据长度 =====
    logger.info(f"读取已有数据: {len(existing_data)} 篇")

    # 构建标题索引
    title_to_item = {item.get("paper"): item for item in existing_data if item.get("paper")}
    for new_item in results:
        title = new_item.get("paper")
        if title:
            title_to_item[title] = new_item
    merged = list(title_to_item.values())

    # ===== 调试日志：合并后长度 =====
    logger.info(f"合并后: {len(merged)} 篇")

    # 2. 写入 JSON（覆盖）
    with open(json_path, 'w', encoding='utf-8') as f:
        json.dump(merged, f, ensure_ascii=False, indent=2)

    # 3. 写入 Markdown（覆盖） - 增加分隔线
    with open(md_path, 'w', encoding='utf-8') as f:
        f.write(f"# Paper Assistant Report: {topic}\n\n")
        for idx, item in enumerate(merged):
            if idx > 0:
                f.write("\n---\n\n")   # 条目间分隔线
            f.write(f"## {item['paper']}\n\n")
            f.write(f"**Summary:**\n\n{item.get('summary', '无摘要')}\n\n")
            f.write(f"**Citation (BibTeX):**\n```bibtex\n{item.get('citation', '无引用')}\n```\n")

    logger.info(f"Results saved to {json_path} and {md_path}")
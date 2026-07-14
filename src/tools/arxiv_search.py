import arxiv
import hashlib
import json
import os
from dataclasses import dataclass, asdict
from typing import List

from src.utils.logger import logger
from src.utils.config import config


@dataclass
class Paper:
    title: str
    author: str
    summary: str
    year: int
    arxiv_id: str

    def to_text(self) -> str:
        return (
            f"Title: {self.title}\n"
            f"Author: {self.author}\n"
            f"Year: {self.year}\n"
            f"Summary: {self.summary}"
        )

    @classmethod
    def from_arxiv_result(cls, result) -> "Paper":
        arxiv_id = result.get_short_id()

        return cls(
            title=result.title,
            author=result.authors[0].name if result.authors else "Unknown",
            summary=result.summary,
            year=result.published.year,
            arxiv_id=arxiv_id,
        )


def search_papers(
    keyword: str,
    max_results: int = None,
    category: str = None,
    year_from: int = None,
    year_to: int = None,
    sort_by: str = "Relevance",
    exclude_ids: list = None
) -> List[Paper]:

    if exclude_ids is None:
        exclude_ids = []

    if max_results is None:
        max_results = config.DEFAULT_MAX_RESULTS

    if not keyword or not keyword.strip():
        raise ValueError("Keyword cannot be empty")

    if max_results <= 0:
        raise ValueError("max_results must be positive")

    # =====================================================
    # 缓存逻辑（始终启用）
    # =====================================================

    use_cache = True

    cache_key_parts = [
        keyword.strip().lower(),
        str(max_results),
        category or "",
        str(year_from or ""),
        str(year_to or ""),
        sort_by,
        ",".join(sorted(exclude_ids)) if exclude_ids else "none"
    ]

    cache_key_str = "_".join(cache_key_parts)

    cache_key = hashlib.md5(
        cache_key_str.encode()
    ).hexdigest()

    cache_dir = "data/search_cache"

    cache_path = os.path.join(
        cache_dir,
        f"{cache_key}.json"
    )

    if os.path.exists(cache_path):
        try:
            with open(cache_path, "r", encoding="utf-8") as f:
                data = json.load(f)

            papers = [
                Paper(**item)
                for item in data
            ]

            logger.info(
                f"从搜索缓存加载了 {len(papers)} 篇论文（关键词: {keyword}）"
            )

            return papers[:max_results]

        except Exception as e:
            logger.warning(
                f"读取搜索缓存失败，将重新搜索: {e}"
            )

            try:
                os.remove(cache_path)
            except Exception:
                pass
    # =====================================================
    # 搜索逻辑
    # =====================================================

    logger.info(
        f"Searching arXiv for '{keyword}', "
        f"max_results={max_results}, "
        f"exclude_ids={len(exclude_ids)}"
    )

    client = arxiv.Client(
        page_size=50,
        delay_seconds=3,
        num_retries=3
    )

    # 为缓存多获取一些结果
    cache_fetch_size = max(
        100,
        max_results + len(exclude_ids) * 2
    )

    search_kwargs = {
        "query": keyword,
        "max_results": cache_fetch_size
    }

    # 排序
    if sort_by.lower() == "submitteddate":
        search_kwargs["sort_by"] = arxiv.SortCriterion.SubmittedDate
    elif sort_by.lower() == "lastupdateddate":
        search_kwargs["sort_by"] = arxiv.SortCriterion.LastUpdatedDate
    else:
        search_kwargs["sort_by"] = arxiv.SortCriterion.Relevance

    search = arxiv.Search(**search_kwargs)

    # 返回给业务逻辑的论文
    papers = []

    # 写入缓存的全部论文
    all_fetched_papers = []

    try:
        for result in client.results(search):

            paper = Paper.from_arxiv_result(result)

            # 所有抓到的论文都记录下来
            all_fetched_papers.append(paper)

            # 排除已经使用过的论文
            if paper.arxiv_id in exclude_ids:
                continue

            # 分类过滤
            if category:
                if category not in result.categories:
                    continue

            # 年份过滤
            if year_from:
                if result.published.year < year_from:
                    continue

            if year_to:
                if result.published.year > year_to:
                    continue

            # 返回结果达到上限就不再继续加入返回列表
            if len(papers) < max_results:
                papers.append(paper)

        logger.info(
            f"Fetched {len(all_fetched_papers)} papers from arXiv"
        )

    except Exception as e:
        logger.error(f"搜索 arXiv 失败: {e}")
        raise

    logger.info(
        f"Found {len(papers)} papers after filtering"
    )

    # =====================================================
    # 保存缓存
    # =====================================================

    if use_cache and papers and cache_path:
        try:
            os.makedirs(
                os.path.dirname(cache_path),
                exist_ok=True
            )

            paper_dicts = [
                asdict(p)
                for p in papers
            ]

            with open(
                cache_path,
                "w",
                encoding="utf-8"
            ) as f:
                json.dump(
                    paper_dicts,
                    f,
                    ensure_ascii=False,
                    indent=2
                )

            logger.info(
                f"搜索缓存已保存，共保存 {len(papers)} 篇论文: {cache_path}"
            )

        except Exception as e:
            logger.warning(
                f"保存搜索缓存失败（不影响使用）: {e}"
            )

    return papers
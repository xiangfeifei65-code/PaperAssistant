#!/usr/bin/env python
import time
from src.core import paper_assistant
from src.utils.logger import logger
import os
import json
import glob
from src.utils.batch_helpers import load_existing_results, merge_and_deduplicate

try:
    from src.core import save_results
except ImportError:
    save_results = None

try:
    from src.tools.arxiv_download import download_pdf
except ImportError:
    download_pdf = None

def main():
    print("=" * 50)
    print("📚 欢迎使用论文助手")
    print("=" * 50)

    # 1. 输入主题列表（逗号分隔）
    topics_input = input("请输入要处理的论文主题，用英文逗号分隔：\n").strip()
    if not topics_input:
        print("未输入任何主题，程序退出。")
        return

    topics = [t.strip() for t in topics_input.split(",") if t.strip()]
    if not topics:
        print("未解析到有效主题，程序退出。")
        return

    print(f"\n✅ 共解析到 {len(topics)} 个主题：")
    for idx, t in enumerate(topics, 1):
        print(f"  {idx}. {t}")

    print("\n" + "=" * 50)
    print("开始处理，每个主题将分别询问配置。")
    print("=" * 50)

    total = len(topics)
    for idx, topic in enumerate(topics, 1):
        # ---------- 智能增量检查 ----------
        existing_papers = load_existing_results(topic)
        existing_count = len(existing_papers)

        if existing_count > 0:
            print(f"\n📂 主题 '{topic}' 已有 {existing_count} 篇论文的结果。")
        else:
            print(f"\n📂 主题 '{topic}' 尚未处理过。")

        # 询问期望论文数量
        max_input = input(f"  请输入该主题期望的论文数量（当前已有 {existing_count} 篇，默认 3）：").strip()
        desired_count = int(max_input) if max_input.isdigit() else 3
        if desired_count <= 0:
            print("  数量必须为正数，跳过此主题。")
            continue

        # 判断是否需要补充
        if existing_count >= desired_count:
            print(f"\n⏭️ 主题 [{idx}/{total}]：{topic} 已有数量 ({existing_count}) 已达到期望 ({desired_count})，无需重新搜索。")
            # 仍然询问是否下载 PDF（补充下载）
            download_input = input("  是否下载这些论文的 PDF？(y/n，默认 n)：").strip().lower()
            download_flag = download_input in ("y", "yes")
            if download_flag and download_pdf is not None:
                print(f"  开始下载 {existing_count} 篇论文的 PDF...")
                for paper_info in existing_papers:
                    arxiv_id = paper_info.get("arxiv_id")
                    title = paper_info.get("paper")
                    if arxiv_id:
                        try:
                            pdf_path = download_pdf(arxiv_id, title, topic=topic)
                            if pdf_path:
                                print(f"    ✓ {title} -> {pdf_path}")
                            else:
                                print(f"    ✗ {title} 下载失败")
                        except Exception as e:
                            logger.error(f"下载 PDF 失败 ({title}): {e}")
                    else:
                        print(f"    ✗ {title} 没有 arxiv_id，跳过")
                print("  PDF 下载完成。")
            else:
                print("  跳过 PDF 下载。")
            # 主题间休息
            if idx < total:
                time.sleep(1)
            continue  # 跳过后续处理

        # 需要补充：计算需要新搜索的数量
        need = desired_count - existing_count
        print(f"\n🔄 主题 [{idx}/{total}]：{topic} 需要补充 {need} 篇论文。")

        # 询问是否保存结果（默认 y）
        save_input = input("  是否将结果保存到 outputs/ 目录？(y/n，默认 y)：").strip().lower()
        save_global = save_input in ("y", "yes", "")

        # 询问是否下载新论文的 PDF
        download_input = input("  是否下载补充论文的 PDF？(y/n，默认 n)：").strip().lower()
        download_global = download_input in ("y", "yes")

        # ---------- 关键修改：提取已有论文的 arxiv_id 用于排除 ----------
        exclude_ids = [p.get("arxiv_id") for p in existing_papers if p.get("arxiv_id")]
        if exclude_ids:
            logger.info(f"排除已有论文 ID: {exclude_ids}")
        else:
            logger.info("没有已有论文，无需排除")

        logger.info(f"========== 开始处理 [{idx}/{total}]：{topic}，搜索 {need} 篇 ==========")
        print(f"\n>>> 正在处理 [{idx}/{total}]：{topic}（补充 {need} 篇）")

        try:
            # 传入 exclude_ids 确保新论文与已有不同
            new_results = paper_assistant(topic, need, exclude_ids=exclude_ids)
            # ===== 新增调试打印 =====
            print(f"新论文数量: {len(new_results)}")
            for p in new_results:
                print(f"  - {p.get('paper')}")
            # ===== 调试结束 =====
            logger.info(f"搜索完成，获得 {len(new_results)} 篇新论文。")
        except Exception as e:
            logger.error(f"处理主题 '{topic}' 时出错: {e}")
            continue

        if not new_results:
            print("  未获得任何新论文，可能搜索不到或出错。保留旧结果。")
            results = existing_papers
        else:
            # 合并旧结果和新结果，去重
            results = merge_and_deduplicate(existing_papers, new_results)
            print(f"  合并后共有 {len(results)} 篇论文。")

            # 保存合并后的结果（如果启用）
            if save_global and save_results is not None:
                try:
                    save_results(results, topic)
                    logger.info(f"结果已保存到 outputs/{topic}/")
                except Exception as e:
                    logger.error(f"保存结果失败 ({topic}): {e}")
            elif save_global and save_results is None:
                logger.warning("save_results 函数未实现，请先在 src/core.py 中定义。")

            # 下载新论文的 PDF（如果启用）
            if download_global and download_pdf is not None:
                print(f"  正在下载 {len(new_results)} 篇新论文的 PDF...")
                for paper_info in new_results:
                    arxiv_id = paper_info.get("arxiv_id")
                    title = paper_info.get("paper")
                    if arxiv_id:
                        try:
                            pdf_path = download_pdf(arxiv_id, title, topic=topic)
                            if pdf_path:
                                print(f"    ✓ {title} -> {pdf_path}")
                            else:
                                print(f"    ✗ {title} 下载失败")
                        except Exception as e:
                            logger.error(f"下载 PDF 失败 ({title}): {e}")
                    else:
                        print(f"    ✗ {title} 没有 arxiv_id，跳过")
                print("  PDF 下载完成。")
            elif download_global and download_pdf is None:
                logger.warning("download_pdf 函数未实现，请先在 src/tools/arxiv_download.py 中定义。")

        # 主题间休息
        if idx < total:
            time.sleep(1)

    # 在批量处理循环结束后，生成批量索引
    try:
        from src.report import generate_index
        generate_index("outputs")
        logger.info("批量索引已生成")
    except Exception as e:
        logger.error(f"生成批量索引失败: {e}")

    print("\n" + "=" * 50)
    print("✅ 所有主题处理完成！按回车键退出。")
    input()


if __name__ == "__main__":
    main()
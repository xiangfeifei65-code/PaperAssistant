import os
import glob
from datetime import datetime
from src.utils.logger import logger

def generate_index(output_dir="outputs"):
    """
    遍历 outputs/ 下所有按主题分类的子目录，生成一个汇总索引页面。
    索引文件保存在 outputs/index.md。
    """
    if not os.path.exists(output_dir):
        logger.warning(f"目录 {output_dir} 不存在，无法生成索引。")
        return

    # 获取所有主题子目录（排除可能存在的索引文件本身）
    subdirs = [d for d in os.listdir(output_dir)
               if os.path.isdir(os.path.join(output_dir, d))]

    if not subdirs:
        logger.info("没有找到任何主题文件夹，跳过索引生成。")
        return

    # 准备 Markdown 表格内容
    lines = [
        "# 📚 论文助手 - 结果汇总索引",
        "",
        "以下是所有已处理主题的汇总列表，按主题分类存放：",
        "",
        "| 主题 | 结果文件（点击查看） | 最后修改时间 |",
        "|------|-------------------|--------------|"
    ]

    for topic in sorted(subdirs):
        topic_path = os.path.join(output_dir, topic)
        json_files = glob.glob(os.path.join(topic_path, "*.json"))

        if json_files:
            latest_file = max(json_files, key=os.path.getmtime)
            file_name = os.path.basename(latest_file)
            # 链接使用相对路径，因为 index.md 在 outputs/ 下，主题文件夹在同级
            rel_path = os.path.join(topic, file_name)
            mod_time = datetime.fromtimestamp(os.path.getmtime(latest_file)).strftime("%Y-%m-%d %H:%M")
            lines.append(f"| {topic} | [{file_name}]({rel_path}) | {mod_time} |")
        else:
            lines.append(f"| {topic} | （暂无 JSON 结果） | - |")

    # 写入索引文件
    index_path = os.path.join(output_dir, "index.md")
    with open(index_path, 'w', encoding='utf-8') as f:
        f.write("\n".join(lines))

    logger.info(f"索引汇总已生成: {index_path}")
    print(f"✅ 索引已生成: {index_path}")
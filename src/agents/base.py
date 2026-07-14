from hello_agents import HelloAgentsLLM, SimpleAgent
from src.utils.config import config
from src.utils.logger import logger

def load_prompt(file_path: str) -> str:
    # 这里的路径是相对于项目根目录的
    with open(file_path, 'r', encoding='utf-8') as f:
        return f.read().strip()

def create_llm():
    return HelloAgentsLLM(
        model=config.MODEL,
        api_key=config.API_KEY,
        base_url=config.BASE_URL if config.BASE_URL else None,
    )

def create_agent(name: str, system_prompt: str) -> SimpleAgent:
    llm = create_llm()
    logger.info(f"Creating agent: {name}")
    return SimpleAgent(
        llm=llm,
        name=name,
        system_prompt=system_prompt,
    )
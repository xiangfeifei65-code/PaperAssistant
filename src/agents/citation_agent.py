from src.agents.base import create_agent
from src.agents.base import load_prompt

CITATION_PROMPT = load_prompt("skills/citation_prompt.txt")

citation_agent = create_agent("CitationAgent", CITATION_PROMPT)
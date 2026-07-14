from src.agents.base import create_agent
from src.agents.base import load_prompt

SUMMARY_PROMPT = load_prompt("skills/summary_prompt.txt")

summary_agent = create_agent("PaperSummaryAgent", SUMMARY_PROMPT)
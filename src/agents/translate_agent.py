from src.agents.base import create_agent
from src.agents.base import load_prompt

TRANSLATE_PROMPT = load_prompt("skills/translate_prompt.txt")

translate_agent = create_agent("TranslateAgent", TRANSLATE_PROMPT)
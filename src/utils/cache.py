import hashlib
import json
import os

CACHE_DIR = "data/cache"

def get_cache_key(text: str, agent_name: str) -> str:
    content = f"{agent_name}:{text}"
    return hashlib.md5(content.encode()).hexdigest()

def get_cached(key: str) -> str | None:
    path = os.path.join(CACHE_DIR, f"{key}.json")
    if os.path.exists(path):
        with open(path, 'r') as f:
            return json.load(f).get("result")
    return None

def save_cache(key: str, value: str):
    os.makedirs(CACHE_DIR, exist_ok=True)
    with open(os.path.join(CACHE_DIR, f"{key}.json"), 'w') as f:
        json.dump({"result": value}, f)
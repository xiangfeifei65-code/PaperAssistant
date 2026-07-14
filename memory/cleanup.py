import time
from pathlib import Path

def clean_old_traces(days=7):
    traces_dir = Path(__file__).parent / "traces"
    if not traces_dir.exists():
        return
    now = time.time()
    for f in traces_dir.glob("*"):
        if f.is_file() and (now - f.stat().st_mtime) > days * 86400:
            f.unlink()
            print(f"Deleted old trace: {f.name}")

if __name__ == "__main__":
    clean_old_traces()
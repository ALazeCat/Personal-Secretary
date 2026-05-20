import json
from datetime import datetime
from pathlib import Path


DATA_DIR = Path(__file__).parent / "data"
HISTORY_FILE = DATA_DIR / "history.json"


def _ensure_history_file():
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    if not HISTORY_FILE.exists():
        HISTORY_FILE.write_text(json.dumps({"records": []}, indent=2), encoding="utf-8")


def get_history():
    _ensure_history_file()
    try:
        return json.loads(HISTORY_FILE.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {"records": []}


def save_record(record_type: str, data: dict):
    history = get_history()
    records = history.get("records", [])
    records.append(
        {
            "type": record_type,
            "timestamp": datetime.now().isoformat(timespec="seconds"),
            "data": data,
        }
    )
    history["records"] = records
    HISTORY_FILE.write_text(json.dumps(history, ensure_ascii=False, indent=2), encoding="utf-8")
    return history["records"][-1]

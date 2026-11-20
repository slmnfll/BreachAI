import json
from pathlib import Path

def load():
    return json.loads((Path(__file__).with_name("catalog.json")).read_text(encoding="utf-8"))

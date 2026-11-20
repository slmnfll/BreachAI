import json
from pathlib import Path

def load():
    return json.loads(Path(__file__).with_name("paired.json").read_text(encoding="utf-8"))

def load_legacy():
    """Corpus initial conservé pour la reproductibilité des anciens essais."""
    return json.loads(Path(__file__).with_name("catalog.json").read_text(encoding="utf-8"))

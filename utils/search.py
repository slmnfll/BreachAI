"""Recherche locale : mots partiels, identifiants espacés et suggestions tolérantes."""
import re
import unicodedata
from difflib import SequenceMatcher

def normalize(text):
    text = "".join(c for c in unicodedata.normalize("NFD", str(text).casefold()) if not unicodedata.combining(c))
    return re.sub(r"\b([at])\s+(\d+)\b", r"\1\2", text)

def search_results(results, query):
    tokens = normalize(query).split()
    if not tokens:
        return results, False
    def fields(r):
        return normalize(" ".join(str(r.get(k, "")) for k in ("scenario_id", "titre", "identité", "date_utc", "mode", "campagne")))
    exact = [r for r in results if all(t in fields(r) for t in tokens)]
    if exact:
        return exact, False
    # Pas de correction approximative des dates ni des identifiants.
    def score(r):
        words = fields(r).split()
        scores = [max((1 if t in w else SequenceMatcher(None, t, w).ratio() if len(t) >= 4 and t.isalpha() else 0 for w in words), default=0) for t in tokens]
        return min(scores)
    near = [(score(r), i, r) for i, r in enumerate(results)]
    return [r for value, _, r in sorted(near, key=lambda x: (-x[0], x[1])) if value >= .76], True

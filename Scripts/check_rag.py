import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from lib.rag import retrieve, _get_collection

print("chunks in corpus:", _get_collection().count())
for c in retrieve("What is first-line pharmacotherapy for type 2 diabetes?", k=5) or []:
    print(round(c["score"], 3), "|", c["source"], "|", c["section"], "|", c["text"][:80])
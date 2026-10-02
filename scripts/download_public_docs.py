"""Download the public strategy documents used in the examples into data/library/.

These are published documents. Check each publisher's reuse terms before redistributing them;
this script downloads them to your own machine rather than storing them in the repository.
"""
from pathlib import Path
from urllib.request import Request, urlopen

DOCS = {
    "HIQA_Corporate_Plan_2025-2027.pdf": "https://www.hiqa.ie/sites/default/files/2025-05/HIQA-Corporate-Plan-25-27.pdf",
    "Skillnet_Ireland_Empowering_Enterprise_2026-2028.pdf": "https://www.skillnetireland.ie/images/uploads/annual-report/Skillnet_Ireland_Empowering_Enterprise_2026-2028.pdf",
}

target = Path(__file__).resolve().parent.parent / "data" / "library"
target.mkdir(parents=True, exist_ok=True)
for name, url in DOCS.items():
    dest = target / name
    if dest.exists():
        print(f"Already have {name}")
        continue
    print(f"Downloading {name} ...")
    req = Request(url, headers={"User-Agent": "strategy-ai-toolkit/0.1"})
    dest.write_bytes(urlopen(req, timeout=60).read())
print(f"Done. Files are in {target}")

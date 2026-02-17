import os
from datetime import datetime
import requests
import pandas as pd

OUT_DIR = "data"
API_URL = "https://www.cse.lk/api/tradeSummary"

def main():
    os.makedirs(OUT_DIR, exist_ok=True)

    # Try POST then GET (CSE endpoints often accept POST)
    r = requests.post(API_URL, data={}, timeout=30)
    if r.status_code != 200:
        r = requests.get(API_URL, timeout=30)
    r.raise_for_status()

    data = r.json()

    # Response is usually list OR dict containing a list
    if isinstance(data, list):
        rows = data
    elif isinstance(data, dict):
        rows = next((v for v in data.values() if isinstance(v, list)), None)
    else:
        rows = None

    if not rows:
        raise RuntimeError("CSE API returned no rows (empty response).")

    df = pd.DataFrame(rows)
    today = datetime.utcnow().strftime("%Y-%m-%d")
    out_path = os.path.join(OUT_DIR, f"cse_trade_summary_{today}.csv")
    df.to_csv(out_path, index=False, encoding="utf-8-sig")
    print("Saved:", out_path, "rows:", len(df))

if __name__ == "__main__":
    main()

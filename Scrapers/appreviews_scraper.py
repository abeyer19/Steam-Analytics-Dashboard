import os
import time
import random
from datetime import datetime, timezone
import requests
import pandas as pd
from dotenv import load_dotenv

load_dotenv("config.env")

API_KEY = os.getenv("API_KEY")
APP_ID_LIST_ENDPOINT = os.getenv("APP_ID_LIST_ENDPOINT")      
APP_DETAILS_ENDPOINT = os.getenv("APP_DETAILS_ENDPOINT")      
APP_REVIEWS_ENDPOINT = os.getenv("APP_REVIEWS_ENDPOINT")     

OUT_DIR = "Scrapers/steam_data"
GAMES_LIST_CACHE = "Scrapers/games-list.csv"
REVIEWS_SUMMARY_CSV = os.path.join(OUT_DIR, "reviews_summary_games.csv")
FAILED_LOG = os.path.join(OUT_DIR, "failed_requests.log")

REQUEST_TIMEOUT = 30
SLEEP_SECONDS = 2.0
JITTER_SECONDS = 0.5

HEADERS = {
    "User-Agent": "steam-reviews-summary-scraper/1.1 (macOS; summary-only)"
}

def log_fail(msg: str):
    os.makedirs(OUT_DIR, exist_ok=True)
    with open(FAILED_LOG, "a", encoding="utf-8") as f:
        f.write(f"{datetime.now(timezone.utc).isoformat()}Z\t{msg}\n")

def safe_get(url, params=None):
    try:
        r = requests.get(url, params=params, headers=HEADERS, timeout=REQUEST_TIMEOUT)
        r.raise_for_status()
        return r
    except Exception as e:
        log_fail(f"GET failed url={url} params={params} err={repr(e)}")
        return None

def fetch_all_app_list(api_key: str, max_results: int = 50000) -> pd.DataFrame:
    """
    Pages through IStoreService/GetAppList using last_appid.
    Returns a DataFrame with at least: appid, name, last_modified, price_change_number.
    """
    if not APP_ID_LIST_ENDPOINT:
        raise ValueError("APP_ID_LIST_ENDPOINT missing in config.env")
    if not api_key:
        raise ValueError("API_KEY missing in config.env")

    rows = []
    last_appid = 0

    while True:
        params = {
            "key": api_key,
            "last_appid": last_appid,
            "max_results": max_results,
        }
        resp = safe_get(APP_ID_LIST_ENDPOINT, params=params)
        if resp is None:
            break

        data = resp.json()
        apps = (data.get("response") or {}).get("apps") or []
        if not apps:
            break

        for a in apps:
            rows.append({
                "appid": a.get("appid"),
                "name": a.get("name"),
                "last_modified": a.get("last_modified"),
                "price_change_number": a.get("price_change_number"),
            })

        last_appid = apps[-1].get("appid", last_appid)
        time.sleep(0.2)

    df = pd.DataFrame(rows).dropna(subset=["appid"])
    df["appid"] = df["appid"].astype(int)
    return df

def load_or_build_app_list() -> pd.DataFrame:
    if os.path.exists(GAMES_LIST_CACHE):
        try:
            df = pd.read_csv(GAMES_LIST_CACHE)
            if "appid" in df.columns:
                df["appid"] = df["appid"].astype(int)
                return df
        except Exception as e:
            log_fail(f"Failed to read cache {GAMES_LIST_CACHE}: {repr(e)}")

    df = fetch_all_app_list(API_KEY)
    os.makedirs(os.path.dirname(GAMES_LIST_CACHE), exist_ok=True)
    df.to_csv(GAMES_LIST_CACHE, index=False)
    return df

def is_game_app(appid: int, cc: str = "us") -> bool:
    """
    Uses store appdetails to determine type == 'game' (filters out DLC/software/etc).
    """
    if not APP_DETAILS_ENDPOINT:
        raise ValueError("APP_DETAILS_ENDPOINT missing in config.env")

    params = {"appids": str(appid), "cc": cc}
    resp = safe_get(APP_DETAILS_ENDPOINT, params=params)
    if resp is None:
        return False

    try:
        payload = resp.json()
        entry = payload.get(str(appid), {})
        if not entry.get("success"):
            return False
        data = entry.get("data") or {}
        return data.get("type") == "game"
    except Exception as e:
        log_fail(f"appdetails parse failed appid={appid} err={repr(e)}")
        return False

def fetch_review_summary(appid: int, name: str = None, language: str = "all"):
    """
    Calls store appreviews with filter=summary and num_per_page=0, reads query_summary.
    """
    if not APP_REVIEWS_ENDPOINT:
        raise ValueError("APP_REVIEWS_ENDPOINT missing in config.env")

    url = APP_REVIEWS_ENDPOINT.format(appid)
    params = {
        "json": 1,
        "filter": "summary",
        "language": language,
        "num_per_page": 0,
    }
    resp = safe_get(url, params=params)
    if resp is None:
        return None

    try:
        data = resp.json()
        if not data.get("success"):
            return None
        qs = data.get("query_summary") or {}
        return {
            "steam_appid": appid,
            "name": name,
            "num_reviews": qs.get("num_reviews"),
            "review_score": qs.get("review_score"),
            "review_score_desc": qs.get("review_score_desc"),
            "total_positive": qs.get("total_positive"),
            "total_negative": qs.get("total_negative"),
            "total_reviews": qs.get("total_reviews"),
            "collection_date_utc": datetime.now(timezone.utc).isoformat(),
        }
    except Exception as e:
        log_fail(f"appreviews parse failed appid={appid} err={repr(e)}")
        return None

def load_processed_appids(csv_path: str):
    """
    Resumes by skipping any steam_appid already written to REVIEWS_SUMMARY_CSV.
    """
    if not os.path.exists(csv_path):
        return set()
    try:
        df = pd.read_csv(csv_path, usecols=["steam_appid"])
        return set(df["steam_appid"].astype(int).tolist())
    except Exception as e:
        log_fail(f"Failed to read processed set from {csv_path}: {repr(e)}")
        return set()

def append_row(csv_path: str, row: dict):
    os.makedirs(os.path.dirname(csv_path), exist_ok=True)
    df = pd.DataFrame([row])
    write_header = not os.path.exists(csv_path)
    df.to_csv(csv_path, mode="a", header=write_header, index=False)

def main():
    apps = load_or_build_app_list()
    apps["appid"] = apps["appid"].astype(int)

    # AppID -> name mapping
    appid_to_name = dict(zip(apps["appid"], apps.get("name", pd.Series([None] * len(apps)))))

    appids = apps["appid"].dropna().astype(int).tolist()
    processed = load_processed_appids(REVIEWS_SUMMARY_CSV)
    remaining = [a for a in appids if a not in processed]

    print(f"Total appids: {len(appids)} | Already processed: {len(processed)} | Remaining: {len(remaining)}")

    for idx, appid in enumerate(remaining, start=1):
        time.sleep(SLEEP_SECONDS + random.random() * JITTER_SECONDS)

        # Only keep actual games
        if not is_game_app(appid):
            continue

        summary = fetch_review_summary(appid, name=appid_to_name.get(appid))
        if summary is None:
            continue

        append_row(REVIEWS_SUMMARY_CSV, summary)
        print(f"WROTE {appid} {summary.get('name')} total_reviews={summary.get('total_reviews')}")

        if idx % 250 == 0:
            print(f"Progress: looped {idx}/{len(remaining)} remaining appids")

    print("Done. Output:", REVIEWS_SUMMARY_CSV)

if __name__ == "__main__":
    main()

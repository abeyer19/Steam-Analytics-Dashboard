import os
import time
import random
from datetime import datetime, timezone
import requests
import pandas as pd
from dotenv import load_dotenv
import csv
import sys
from typing import Dict, List, Optional


load_dotenv("config.env")

API_KEY = os.getenv("API_KEY")
APP_ACHIEVEMENTS_ENDPOINT = os.getenv("APP_ACHIEVEMENTS_ENDPOINT")  
ACHIEVEMENT_GLOBAL_PCT_ENDPOINT = os.getenv("ACHIEVEMENT_GLOBAL_PCT_ENDPOINT") 


OUT_DIR = "Scrapers/steam_data"
ACHIEVEMENTS_CSV = os.path.join(OUT_DIR, "achievements.csv")
GAMES_LIST_CACHE = "Scrapers/games-list.csv"
FAILED_LOG = os.path.join(OUT_DIR, "failed_requests.log")


REQUEST_TIMEOUT = 30
SLEEP_SECONDS = 1.5
JITTER_SECONDS = 0.5


HEADERS = {
    "User-Agent": "steam-achievements-scraper/1.1 (macOS; schema+global)"
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


def get_schema(appid: int) -> Optional[Dict]:
    if not API_KEY or not APP_ACHIEVEMENTS_ENDPOINT:
        log_fail(f"Missing API_KEY or APP_ACHIEVEMENTS_ENDPOINT for {appid}")
        return None
    
    url = APP_ACHIEVEMENTS_ENDPOINT.format(API_KEY, appid)
    resp = safe_get(url)
    if resp is None:
        return None
    
    try:
        data = resp.json()
        return data.get('game', {})
    except Exception as e:
        log_fail(f"Schema parse failed appid={appid} err={repr(e)}")
        return None


def get_global_stats(appid: int) -> Dict[str, float]:
    """Get global achievement percentages"""
    if not ACHIEVEMENT_GLOBAL_PCT_ENDPOINT:
        return {}
    
    params = {'gameid': appid}
    resp = safe_get(ACHIEVEMENT_GLOBAL_PCT_ENDPOINT, params=params)
    if resp is None:
        return {}
    
    try:
        data = resp.json()
        pct_map = {}
        for stat in data.get('achievement_percentages', {}).get('achievements', []):
            pct_map[stat['name']] = stat['percent']
        return pct_map
    except Exception as e:
        log_fail(f"Global stats parse failed appid={appid} err={repr(e)}")
        return {}


def load_appids_from_cache() -> List[int]:
    if not os.path.exists(GAMES_LIST_CACHE):
        log_fail(f"Missing {GAMES_LIST_CACHE}")
        return []
    
    try:
        df = pd.read_csv(GAMES_LIST_CACHE)
        appids = df["appid"].dropna().astype(int).unique().tolist()
        print(f"Loaded {len(appids)} appids from {GAMES_LIST_CACHE}")
        return appids
    except Exception as e:
        log_fail(f"Failed to read {GAMES_LIST_CACHE}: {repr(e)}")
        return []


def load_processed_appids(csv_path: str) -> set:
    """Skip appids already processed."""
    if not os.path.exists(csv_path):
        return set()
    
    try:
        df = pd.read_csv(csv_path, usecols=["appid"])
        return set(df["appid"].astype(int).tolist())
    except Exception as e:
        log_fail(f"Failed to read processed set from {csv_path}: {repr(e)}")
        return set()


def append_achievement_rows(csv_path: str, rows: List[dict]):
    """Append achievement rows to CSV."""
    os.makedirs(os.path.dirname(csv_path), exist_ok=True)
    write_header = not os.path.exists(csv_path)
    
    with open(csv_path, 'a', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=[
            'appid', 'game_name', 'achievement_apiname', 'display_name', 
            'description', 'is_hidden', 'default_value', 'global_unlock_pct'
        ])
        if write_header:
            writer.writeheader()
        writer.writerows(rows)


def scrape_achievements_for_appid(appid: int) -> List[dict]:
    """Scrape schema + global % for one appid."""
    print(f"  → Scraping achievements for {appid}...")
    
    schema = get_schema(appid)
    if not schema or 'availableGameStats' not in schema:
        print(f"    No schema data")
        return []
    
    game_name = schema.get('gameName', f'App_{appid}')
    achievements = schema['availableGameStats'].get('achievements', [])
    if not achievements:
        print(f"    No achievements")
        return []
    
    # Get global percentages
    pct_map = get_global_stats(appid)
    
    # Build rows
    rows = []
    for ach in achievements:
        row = {
            'appid': appid,
            'game_name': game_name,
            'achievement_apiname': ach.get('name', ''),
            'display_name': ach.get('displayName', ''),
            'description': ach.get('description', ''),
            'is_hidden': ach.get('hidden', 0),
            'default_value': ach.get('defaultvalue', 0),
            'global_unlock_pct': pct_map.get(ach.get('name'), '')
        }
        rows.append(row)
    
    print(f"    Wrote {len(rows)} achievements")
    return rows


def main():
    # Load appids from your existing cache
    appids = load_appids_from_cache()
    if not appids:
        print("No appids found. Run your main scraper first.")
        return
    
    processed_appids = load_processed_appids(ACHIEVEMENTS_CSV)
    remaining = [appid for appid in appids if appid not in processed_appids]
    
    print(f"Total appids: {len(appids)} | Already processed: {len(processed_appids)} | Remaining: {len(remaining)}")
    
    total_rows = 0
    for idx, appid in enumerate(remaining, start=1):
        rows = scrape_achievements_for_appid(appid)
        if rows:
            append_achievement_rows(ACHIEVEMENTS_CSV, rows)
            total_rows += len(rows)
        
        # Rate limiting
        time.sleep(SLEEP_SECONDS + random.random() * JITTER_SECONDS)
        
        if idx % 50 == 0:
            print(f"Progress: {idx}/{len(remaining)} appids | {total_rows} total rows")
    
    print(f"Complete! Wrote {total_rows} achievement rows to {ACHIEVEMENTS_CSV}")


if __name__ == "__main__":
    main()

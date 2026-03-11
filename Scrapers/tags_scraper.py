# Used to get all specified data from the details endpoint -> https://store.steampowered.com/app/{}

# Import packages
import os
import time
from datetime import datetime
from dataclasses import dataclass
from typing import Optional
import requests
import pandas as pd
from dotenv import load_dotenv
from pydantic import BaseModel, ConfigDict
from bs4 import BeautifulSoup


# Insert API key and endpoint for game list, and endpoint for game details
load_dotenv("config.env")
API_KEY = os.getenv("API_KEY")
GAME_LIST_ENDPOINT = os.getenv("APP_ID_LIST_ENDPOINT")
APP_TAGS_ENDPOINT = os.getenv("APP_TAGS_ENDPOINT")

# --------------------------------------------------------------------------- Helpers ---------------------------------------------------------------------------
# In-memory cache for fetched app JSON responses, limiting repeats for each get function
_app_json_cache = {}

def fetch_app_json(endpoint: str, app_id: str):
    key = endpoint.format(app_id)
    if key in _app_json_cache:
        return _app_json_cache[key]
    try:
        response = requests.get(key)
        response.raise_for_status()
        soup = BeautifulSoup(response.content, "html.parser")
        _app_json_cache[key] = soup
        return soup
    except requests.exceptions.RequestException as e:
        print(f"Request failed: {e}")
        return None

# --------------------------------------------------------------------------- Game List ---------------------------------------------------------------------------

# Used to get the steam game list from the API connection
def get_steam_game_list(api_key: str, cache_file: str = "Scrapers/games-list.csv"):
    # Check cache file first
    if os.path.exists(cache_file):
        try:
            return pd.read_csv(cache_file)
        except Exception as e:
            print(f"Failed to read cache file {cache_file}: {e}")
    
    # Cache miss or unreadable; fetch from API
    params = {"key": api_key}
    try:
        response = requests.get(GAME_LIST_ENDPOINT, params=params)
        response.raise_for_status()
        data = response.json()
        appids, names, last_mods, price_changes = [], [], [], []
        for i in data["response"]["apps"]:
            appids.append(i["appid"])
            names.append(i["name"])
            last_mods.append(i["last_modified"])
            price_changes.append(i["price_change_number"])
        df = pd.DataFrame({
            "appid": appids,
            "name": names,
            "last_modified": last_mods,
            "price_change_number": price_changes,
        })
        # Save to cache for future runs
        os.makedirs(os.path.dirname(cache_file), exist_ok=True)
        df.to_csv(cache_file, index=False)
        return df
    except requests.exceptions.RequestException as e:
        print(f"Request failed: {e}")
        return None

# --------------------------------------------------------------------------- Game Tags ---------------------------------------------------------------------------

# Create Tags class
@dataclass
class Tags(BaseModel):
    model_config = ConfigDict(extra="ignore")

    tag_name: Optional[str] = "None"
    collection_date: datetime = datetime.now()

def get_tags(endpoint: str, app_id: str):
    try:
        tag_data = fetch_app_json(endpoint, app_id)
        if tag_data is None:
            return None
        raw = tag_data.find_all("a", class_="app_tag")
        if raw is None:
            return None
        entries = raw if isinstance(raw, list) else [raw]
        rows = []
        for entry in entries:
            tags = Tags.model_validate({
                "tag_name": str(entry.get_text().strip()),
                "collection_date": datetime.now(),
                })
            rows.append({
                "steam_appid": app_id,
                "tag_name":tags.tag_name,
                "collection_date":tags.collection_date
                })
        return pd.DataFrame(rows)
    except Exception as e:
        print(f"Error parsing genres for {app_id}: {e}")
        return None


def main():
    # Get game list (reads from cache if exists, fetches API only on cache miss)
    games_list = get_steam_game_list(API_KEY, "Scrapers/games-list.csv")
    if games_list is not None:
        appids = games_list["appid"].tolist()
    else:
        print("Unable to obtain app IDs")
        return

    # For each app id, run each scraper once (in tandem)
    scrapers = [
        ("tags", get_tags, "Scrapers/steam_data_tags/tags_data.csv")
    ]

    # Prepare processed-id sets per scraper for resumability
    processed = {}
    for name, _func, out_file in scrapers:
        os.makedirs(os.path.dirname(out_file), exist_ok=True)
        if os.path.exists(out_file):
            try:
                existing = pd.read_csv(out_file)
                processed[name] = set(existing["steam_appid"].astype(str))
            except Exception:
                processed[name] = set()
        else:
            processed[name] = set()

    # Get set of already-processed app IDs from the first scraper (details)
    first_scraper_name = scrapers[0][0] if scrapers else None
    already_processed = processed.get(first_scraper_name, set())
    
    # Filter appids to only those not yet processed; resume where scraper left off
    unprocessed_appids = [str(app_id) for app_id in appids if str(app_id) not in already_processed]
    print(f"Resuming from app ID index (already processed: {len(already_processed)}, remaining: {len(unprocessed_appids)})")

    # For each app id, call each scraper once (skip if already processed)
    for sid in unprocessed_appids:
        # Rate limiting
        time.sleep(1.5)
        for name, _func, out_file in scrapers:
            if sid in processed.get(name, set()):
                continue

            try:
                df = _func(APP_TAGS_ENDPOINT, sid)
            except Exception as e:
                print(f"Error running {name} for {sid}: {e}")
                df = None

            if df is not None and not df.empty:
                df.to_csv(out_file, mode="a", header=not os.path.exists(out_file), index=False)
                processed[name].add(sid)
                print(f"{sid} {name} processed")

    print("All scrapers finished.")

if __name__ == "__main__":
    main()

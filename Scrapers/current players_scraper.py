# Used to get all specified data from the details endpoint -> https://api.steampowered.com/ISteamUserStats/GetNumberOfCurrentPlayers/v1/?appid={}

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

# Insert API key and endpoint for game list, and endpoint for game details
load_dotenv("config.env")
API_KEY = os.getenv("API_KEY")
GAME_LIST_ENDPOINT = os.getenv("APP_ID_LIST_ENDPOINT")
PlAYER_COUNT_ENDPOINT = os.getenv("PLAYER_COUNT_ENDPOINT")

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
        data = response.json()
        _app_json_cache[key] = data
        return data
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

# --------------------------------------------------------------------------- Player Count ---------------------------------------------------------------------------

# Create Players class
@dataclass
class Players(BaseModel):
    model_config = ConfigDict(extra="ignore")

    steam_appid: int
    player_count: Optional[int] = 0
    collection_date: datetime = datetime.now()

# Used to get current game players at time of collection
def get_players(endpoint, app_id: str):
    try:
        data = fetch_app_json(endpoint, app_id)
        if not data or "response" not in data:
            print(f"No data found for app_id {app_id}")
            return None
        players = Players.model_validate(data["response"])
        return pd.DataFrame([{
            "steam_appid": app_id,
            "player_count": players.player_count,
            "collection_date": players.collection_date,
        }])
    except Exception as e:
        print(f"Error parsing players for {app_id}: {e}")
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
        ("players", get_players, "Scrapers/steam_data_players/player_count_data.csv"),
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
                df = _func(DETAIL_ENDPOINT, sid)
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

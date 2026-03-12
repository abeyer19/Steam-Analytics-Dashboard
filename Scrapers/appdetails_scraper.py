# Used to get all specified data from the details endpoint -> https://store.steampowered.com/api/appdetails?appids={}&cc=us

# Import packages
import os
import time
from datetime import datetime
from dataclasses import dataclass
from typing import Optional
import requests
import pandas as pd
from dotenv import load_dotenv
from pydantic import BaseModel, ConfigDict, Field

# Insert API key and endpoint for game list, and endpoint for game details
load_dotenv("config.env")
API_KEY = os.getenv("API_KEY")
GAME_LIST_ENDPOINT = os.getenv("APP_ID_LIST_ENDPOINT")
DETAIL_ENDPOINT = os.getenv("APP_DETAIL_ENDPOINT")

# --------------------------------------------------------------------------- Helpers ---------------------------------------------------------------------------
# In-memory cache for fetched app JSON responses, limiting repeats for each get function
_app_json_cache = {}

def fetch_app_json(endpoint: str, app_id: str):
    key = endpoint.format(app_id)
    if app_id in _app_json_cache:
        return _app_json_cache[app_id]
    try:
        response = requests.get(key)
        response.raise_for_status()
        data = response.json()
        _app_json_cache[app_id] = data
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

# --------------------------------------------------------------------------- Game Details ---------------------------------------------------------------------------

# Create Details class
@dataclass
class Details(BaseModel):
    model_config = ConfigDict(extra="ignore")

    steam_appid: int
    name: str = "Unknown"
    app_type: str = Field(default="Unknown", alias="type")
    is_free: bool = False
    controller_support: str = "Unknown"
    about_the_game: str = ""
    short_description: str = ""
    supported_languages: str = ""
    website: Optional[str] = None
    collection_date: datetime = datetime.now()

# Used to get game metadata details
def get_details(endpoint, app_id: str):
    try:
        details_data = fetch_app_json(endpoint, app_id)
        if details_data is None:
            return None
        app_data = details_data.get(str(app_id))
        if app_data and app_data.get("success") and "data" in app_data:
            details = Details.model_validate(app_data["data"])
        else:
            print(f"No data found for app_id {app_id}")
            return None
        return pd.DataFrame([{
            "steam_appid": details.steam_appid,
            "name": details.name,
            "type": details.app_type,
            "is_free": details.is_free,
            "controller_support": details.controller_support,
            "about_the_game": details.about_the_game,
            "short_description": details.short_description,
            "supported_languages": details.supported_languages,
            "website": details.website,
            "collection_date": details.collection_date,
        }])
    except Exception as e:
        print(f"Error parsing details for {app_id}: {e}")
        return None

# --------------------------------------------------------------------------- price overview section ---------------------------------------------------------------------------

# Create Price Overview class
@dataclass
class PriceOverview(BaseModel):
    model_config = ConfigDict(extra="ignore")

    currency: str
    initial: int
    final: int
    discount_percent: int
    final_formatted: str
    collection_date: datetime = datetime.now()

# Used to get the prices of each game
def get_price_overview(endpoint, app_id: str):
    try:
        details_data = fetch_app_json(endpoint, app_id)
        if details_data is None:
            return None
        raw = details_data[str(app_id)]["data"].get("price_overview")
        if raw is None:
            return pd.DataFrame()
        entries = raw if isinstance(raw, list) else [raw]
        rows = []
        for entry in entries:
            details = PriceOverview.model_validate(entry)
            rows.append({
                "steam_appid": app_id,
                "currency": details.currency,
                "initial": details.initial,
                "final": details.final,
                "discount_percent": details.discount_percent,
                "final_formatted": details.final_formatted,
                "collection_date": details.collection_date,
            })
        return pd.DataFrame(rows)
    except Exception as e:
        print(f"Error parsing price overview for {app_id}: {e}")
        return None

# --------------------------------------------------------------------------- developers/publishers section ---------------------------------------------------------------------------

# Create Developers class
@dataclass
class Devs(BaseModel):
    model_config = ConfigDict(extra="ignore")

    developers: Optional[str] = None
    collection_date: datetime = datetime.now()

# Used to get data about the developers of the games
def get_devs(endpoint, app_id: str):
    try:
        details_data = fetch_app_json(endpoint, app_id)
        if details_data is None:
            return None
        raw = details_data[str(app_id)]["data"]
        devs = raw.get("developers") or []
        devs = devs if isinstance(devs, list) else [devs]
        rows = []
        for d in devs:
                validated = Devs.model_validate({
                    "developers": d,
                    "collection_date": datetime.now(),
                })
                rows.append({
                    "steam_appid": app_id,
                    "developers": validated.developers,
                    "collection_date": validated.collection_date,
                })
        return pd.DataFrame(rows)
    except Exception as e:
        print(f"Error parsing developers for {app_id}: {e}")
        return None

# Create Publishers class
class Pubs(BaseModel):
    model_config = ConfigDict(extra="ignore")

    publishers: Optional[str] = None
    collection_date: datetime = datetime.now()

# Used to get data about the publishers of the games
def get_pubs(endpoint, app_id: str):
    try:
        details_data = fetch_app_json(endpoint, app_id)
        if details_data is None:
            return None
        raw = details_data[str(app_id)]["data"]
        pubs = raw.get("publishers") or []
        pubs = pubs if isinstance(pubs, list) else [pubs]
        rows = []
        for p in pubs:
            validated = Pubs.model_validate({
                "publishers": p,
                "collection_date": datetime.now(),
            })
            rows.append({
                "steam_appid": app_id,
                "publishers": validated.publishers,
                "collection_date": validated.collection_date,
            })
        return pd.DataFrame(rows)
    except Exception as e:
        print(f"Error parsing publishers for {app_id}: {e}")
        return None

# --------------------------------------------------------------------------- categories section ---------------------------------------------------------------------------
# Create Category class
@dataclass
class Category(BaseModel):
    model_config = ConfigDict(extra="ignore")

    id: int
    description: str
    collection_date: datetime = datetime.now()

# Used to get categories for each game
def get_categories(endpoint, app_id: str):
    try:
        details_data = fetch_app_json(endpoint, app_id)
        if details_data is None:
            return None
        raw = details_data[str(app_id)]["data"].get("categories")
        if raw is None:
            return pd.DataFrame()
        entries = raw if isinstance(raw, list) else [raw]
        rows = []
        for entry in entries:
            details = Category.model_validate(entry)
            rows.append({
                "steam_appid": app_id,
                "id": details.id,
                "description": details.description,
                "collection_date": details.collection_date,
            })
        return pd.DataFrame(rows)
    except Exception as e:
        print(f"Error parsing categories for {app_id}: {e}")
        return None

# --------------------------------------------------------------------------- DLC section ---------------------------------------------------------------------------

# Create DLC class
@dataclass
class DLC(BaseModel):
    model_config = ConfigDict(extra="ignore")

    dlc: Optional[int] = None
    collection_date: datetime = datetime.now()

# Used to get DLCs from each game
# Stored as a list, need to process out
def get_dlcs(endpoint, app_id: str):
    try:
        details_data = fetch_app_json(endpoint, app_id)
        if details_data is None:
            return None
        raw = details_data[str(app_id)]["data"].get("dlc")
        if not raw:
            return pd.DataFrame()
        ids = raw if isinstance(raw, list) else [raw]
        rows = []
        for dlc_id in ids:
            validated = DLC.model_validate({
                "dlc": dlc_id,
                "collection_date": datetime.now(),
            })
            rows.append({
                "steam_appid": app_id,
                "dlc": validated.dlc,
                "collection_date": validated.collection_date,
            })
        return pd.DataFrame(rows)
    except Exception as e:
        print(f"Error parsing dlcs for {app_id}: {e}")
        return None

# --------------------------------------------------------------------------- genres section ---------------------------------------------------------------------------

# Create Genre class
@dataclass
class Genre(BaseModel):
    model_config = ConfigDict(extra="ignore")

    id: str
    description: str
    collection_date: datetime = datetime.now()

# Get genres of each game
# Stored as a list of dicts, need to process out
def get_genres(endpoint, app_id: str):
    try:
        details_data = fetch_app_json(endpoint, app_id)
        if details_data is None:
            return None
        raw = details_data[str(app_id)]["data"].get("genres")
        if raw is None:
            return pd.DataFrame()
        entries = raw if isinstance(raw, list) else [raw]
        rows = []
        for entry in entries:
            details = Genre.model_validate(entry)
            rows.append({
                "steam_appid": app_id,
                "id": details.id,
                "description": details.description,
                "collection_date": details.collection_date,
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
        ("details", get_details, "Scrapers/steam_data_details/details_data.csv"),
        ("price", get_price_overview, "Scrapers/team_data_details/price_data.csv"),
        ("devs", get_devs, "Scrapers/team_data_details/devs_data.csv"),
        ("pubs", get_pubs, "Scrapers/team_data_details/pubs_data.csv"),
        ("categories", get_categories, "Scrapers/team_data_details/categories_data.csv"),
        ("dlc", get_dlcs, "Scrapers/team_data_details/dlc_data.csv"),
        ("genres", get_genres, "Scrapers/team_data_details/genres_data.csv"),
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

        if sid in _app_json_cache:
            _app_json_cache.pop(sid)

    print("All scrapers finished.")


if __name__ == "__main__":
    main()

# Used to get all specified data from the reviews endpoint -> https://store.steampowered.com/appreviews/{}?json=1&filter=summary

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
REVIEWS_ENDPOINT = os.getenv("APP_REVIEWS_ENDPOINT")

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


# --------------------------------------------------------------------------- Reviews Summary data ---------------------------------------------------------------------------

# Create Tags class
@dataclass
class ReviewSummary(BaseModel):
    model_config = ConfigDict(extra="ignore")
    
    num_reviews: int = 0
    review_score: int = 0
    review_score_desc: str
    total_positive: int
    total_negative: int
    total_reviews: int
    collection_date: datetime = datetime.now()

# Function to get a review summary of each app ID
def get_reviews_summary(endpoint, app_id: str):
    try:
        reviews_sum_data = fetch_app_json(endpoint, app_id)
        if reviews_sum_data is None:
            return None
        # Reviews endpoint returns flat JSON
        reviews_data = reviews_sum_data
        if reviews_data and reviews_data.get("success") and "query_summary" in reviews_data:
            summary = reviews_data["query_summary"]
            reviews = ReviewSummary.model_validate(summary)
        else:
            print(f"No data found for app_id {app_id}")
            return None
        return pd.DataFrame([{
            "steam_appid": app_id,
            "num_reviews": reviews.num_reviews,
            "review_score": reviews.review_score,
            "review_score_desc": reviews.review_score_desc,
            "total_positive": reviews.total_positive,
            "total_negative": reviews.total_negative,
            "total_reviews": reviews.total_reviews,
            "collection_date": datetime.now(),
        }])
    except Exception as e:
        print(f"Error parsing reviews for {app_id}: {e}")
        return None

# --------------------------------------------------------------------------- Top Reviews data ---------------------------------------------------------------------------

# Create Top Reviews dataclass
@dataclass
class TopReviews(BaseModel):
    model_config = ConfigDict(extra="ignore")

    steam_appid: int
    recommendationid: str
    num_games_owned: Optional[int] = 0
    num_reviews: Optional[int] = 0
    playtime_forever: Optional[int] = 0
    playtime_last_two_weeks: Optional[int] = 0
    playtime_at_review: Optional[int] = 0
    last_played: Optional[int] = 0
    language: Optional[str] = None
    review: Optional[str] = None
    voted_up: Optional[bool] = None
    votes_up: Optional[int] = 0
    votes_funny: Optional[int] = 0
    weighted_vote_score: Optional[float] = 0.0
    comment_count: Optional[int] = 0
    steam_purchase: Optional[bool] = None
    received_for_free: Optional[bool] = None
    refunded: Optional[bool] = None
    written_during_early_access: Optional[bool] = None
    app_release_date: Optional[str] = None
    collection_date: datetime = datetime.now()

# Used to get the top reviews on the summary page of each app ID
def get_top_reviews(endpoint, app_id: str):
    try:
        reviews_data = fetch_app_json(endpoint, app_id)
        if reviews_data is None:
            return None
        reviews_list = reviews_data.get("reviews", [])
        if not reviews_list:
            return pd.DataFrame()
        rows = []
        for review in reviews_list:
            try:
                author = review.get("author", {})
                top_review = TopReviews.model_validate({
                    "steam_appid": app_id,
                    "recommendationid": review.get("recommendationid"),
                    "num_games_owned": author.get("num_games_owned"),
                    "num_reviews": author.get("num_reviews"),
                    "playtime_forever": author.get("playtime_forever"),
                    "playtime_last_two_weeks": author.get("playtime_last_two_weeks"),
                    "playtime_at_review": author.get("playtime_at_review"),
                    "last_played": author.get("last_played"),
                    "language": review.get("language"),
                    "review": review.get("review"),
                    "voted_up": review.get("voted_up"),
                    "votes_up": review.get("votes_up"),
                    "votes_funny": review.get("votes_funny"),
                    "weighted_vote_score": review.get("weighted_vote_score"),
                    "comment_count": review.get("comment_count"),
                    "steam_purchase": review.get("steam_purchase"),
                    "received_for_free": review.get("received_for_free"),
                    "refunded": review.get("refunded"),
                    "written_during_early_access": review.get("written_during_early_access"),
                    "app_release_date": review.get("app_release_date"),
                    "collection_date": datetime.now(),
                })
                rows.append({
                    "steam_appid": top_review.steam_appid,
                    "recommendationid": top_review.recommendationid,
                    "num_games_owned": top_review.num_games_owned,
                    "num_reviews": top_review.num_reviews,
                    "playtime_forever": top_review.playtime_forever,
                    "playtime_last_two_weeks": top_review.playtime_last_two_weeks,
                    "playtime_at_review": top_review.playtime_at_review,
                    "last_played": top_review.last_played,
                    "language": top_review.language,
                    "review": top_review.review,
                    "voted_up": top_review.voted_up,
                    "votes_up": top_review.votes_up,
                    "votes_funny": top_review.votes_funny,
                    "weighted_vote_score": top_review.weighted_vote_score,
                    "comment_count": top_review.comment_count,
                    "steam_purchase": top_review.steam_purchase,
                    "received_for_free": top_review.received_for_free,
                    "refunded": top_review.refunded,
                    "written_during_early_access": top_review.written_during_early_access,
                    "app_release_date": top_review.app_release_date,
                    "collection_date": top_review.collection_date,
                })
            except Exception as e:
                print(f"Error parsing review {review.get('recommendationid')}: {e}")
                continue
        return pd.DataFrame(rows) if rows else pd.DataFrame()
    except Exception as e:
        print(f"Error parsing top reviews for {app_id}: {e}")
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
        ("reviews_sum", get_reviews_summary, "Scrapers/steam_data_reviews/reviews_summary_data.csv"),
        ("reviews_top", get_top_reviews, "Scrapers/steam_data_reviews/top_reviews_data.csv")
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
                df = _func(REVIEWS_ENDPOINT, sid)
            except Exception as e:
                print(f"Error running {name} for {sid}: {e}")
                df = None

            if df is not None and not df.empty:
                df.to_csv(out_file, mode="a", header=not os.path.exists(out_file), index=False)
                processed[name].add(sid)
                print(f"{sid} {name} processed")

        if sid in _app_json_cache:
            _app_json_cache.pop(sid)
            print(_app_json_cache)

    print("All scrapers finished.")


if __name__ == "__main__":
    main()

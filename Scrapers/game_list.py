# Used to get the JSON file for all games listed on Steam into a table format and CSV output

# Import packages
import requests # 2.32.5
import pandas as pd #2.4.2

# Insert API key
API_KEY = "YOUR API KEY HERE"

# Function to get and return games list
def get_steam_game_list(api_key: str):
    endpoint = "https://api.steampowered.com/IStoreService/GetAppList/v1/"
    params = {
        "key": api_key
    }

    # Try to connect to the endpoint
    try:
        response = requests.get(endpoint, params=params)
        response.raise_for_status()
        data = response.json()
    
        # Create column buckets
        appids = []
        names = []
        last_modifieds = []
        price_change_numbers = []

        # Iterate through JSON output and store each element in the column buckets above
        for i in data["response"]["apps"]:
            appids.append(i["appid"])
            names.append(i["name"])
            last_modifieds.append(i["last_modified"])
            price_change_numbers.append(i["price_change_number"])

        # Create a pandas DF to view data
        output = pd.DataFrame({
            'appid': appids,
            'name': names,
            'last_modified': last_modifieds,
            'price_change_number': price_change_numbers
        })

        return output
    
    # Error exception output
    except requests.exceptions.RequestException as e:
        print(f"Request failed: {e}")
        return None

if __name__ == "__main__":
    games_list = get_steam_game_list(API_KEY)
    print(games_list.head())

    # Export to CSV
    #games_list.to_csv('games-list.csv', index=False, encoding='utf-8-sig')
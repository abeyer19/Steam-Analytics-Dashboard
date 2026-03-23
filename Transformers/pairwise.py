import os
import pandas as pd
from itertools import combinations
from collections import Counter

devs_data = pd.read_csv('Scrapers/steam_data_details/devs_data.csv', header=0)
pubs_data = pd.read_csv('Scrapers/steam_data_details/pubs_data.csv', header=0)
categories_data = pd.read_csv('Scrapers/steam_data_details/categories_data.csv', header=0)
genres_data = pd.read_csv('Scrapers/steam_data_details/genres_data.csv', header=0)

# Pairwise counts of each developers and publisher
def devs_pubs_pairwise(devs: pd.DataFrame, pubs: pd.DataFrame) -> pd.DataFrame:
    devs = devs[['steam_appid', 'developers']]
    pubs = pubs[['steam_appid', 'publishers']]

    merged_data = devs.merge(pubs, how='inner', on='steam_appid')
    merged_data = merged_data.dropna(subset=['developers', 'publishers'])

    pair_list = list(zip(merged_data['developers'], merged_data['publishers']))
    pair_sort = [tuple(sorted(x)) for x in pair_list]

    pair_counts = Counter(pair_sort)

    df = pd.DataFrame(pd.Series(pair_counts), columns=['pair_count']).reset_index()
    df = df.rename(columns={'level_0': 'developers', 'level_1': 'publishers'})

    return df

# Pairwise counts of categories and genres
def categories_genres_pairwise(categories: pd.DataFrame, genres: pd.DataFrame) -> pd.DataFrame:
    categories = categories[['steam_appid', 'description']]
    genres = genres[['steam_appid', 'description']]

    merged_data = categories.merge(genres, how='inner', on='steam_appid')
    merged_data = merged_data.rename(columns={'steam_appid': 'steam_appid', 'description_x': 'categories_description', 'description_y': 'genres_description'})
    merged_data = merged_data.dropna(subset=['categories_description', 'genres_description'])

    pair_list = list(zip(merged_data['categories_description'], merged_data['genres_description']))
    pair_sort = [tuple(sorted(x)) for x in pair_list]

    pair_counts = Counter(pair_sort)

    df = pd.DataFrame(pd.Series(pair_counts), columns=['pair_count']).reset_index()
    df = df.rename(columns={'level_0': 'categories_description', 'level_1': 'genres_description'})

    return df

if __name__ == '__main__':
    devspubs_counts = devs_pubs_pairwise(devs_data, pubs_data)
    os.makedirs(os.path.dirname('Transformers/tables/devspubs_pairwise.csv'), exist_ok=True)
    devspubs_counts.to_csv('Transformers/tables/devspubs_pairwise.csv', index=False)

    catsgenres_counts = categories_genres_pairwise(categories_data, genres_data)
    os.makedirs(os.path.dirname('Transformers/tables/catsgenres_pairwise.csv'), exist_ok=True)
    catsgenres_counts.to_csv('Transformers/tables/catsgenres_pairwise.csv', index=False)
    

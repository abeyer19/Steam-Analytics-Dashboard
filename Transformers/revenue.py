import os
import pandas as pd

# Base calculation parameters
BASE_MULTIPLIER = 30
BOUND_TOLERANCE = 15

# Read CSV files
reviews_data = pd.read_csv("Scrapers/steam_data_reviews/reviews_summary_games.csv", header=0)
details_data = pd.read_csv("Scrapers/steam_data_details/details_data.csv", header=0)
price_data = pd.read_csv("Scrapers/steam_data_details/price_data.csv", header=0)

def calc_units(multiplier:int, tolerance:int, reviews:pd.DataFrame, details:pd.DataFrame) -> pd.DataFrame:
    games_only = details[details['type'] == 'game'][['steam_appid']]
    
    df = reviews.merge(games_only, on='steam_appid')

    low = multiplier - tolerance
    high = multiplier + tolerance

    df = df.assign(
        units_sold_lowerbound = df['total_reviews'] * low,
        units_sold = df['total_reviews'] * multiplier,
        units_sold_upperbound = df['total_reviews'] * high
    )
    return df

def calc_revenue(units:pd.DataFrame, prices:pd.DataFrame) -> pd.DataFrame:
    prices = prices[['steam_appid', 'initial']].copy()
    prices['initial_price'] = prices['initial'] / 100.0
    
    df = units.merge(prices[['steam_appid', 'initial_price']], on='steam_appid', how='left')

    for col in ['units_sold_lowerbound', 'units_sold', 'units_sold_upperbound']:
        rev_col = col.replace('units_sold', 'revenue')
        df[rev_col] = df[col] * df['initial_price']
        
    return df


if __name__ == "__main__":
    units_sold = calc_units(BASE_MULTIPLIER, BOUND_TOLERANCE, reviews_data, details_data)
    revenue_table = calc_revenue(units_sold, price_data)
    
    os.makedirs(os.path.dirname('Transformers/tables/revenue_table.csv'), exist_ok=True)
    revenue_table.to_csv('Transformers/tables/revenue_table.csv', index=False)

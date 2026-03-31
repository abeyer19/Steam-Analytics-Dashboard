import os
import pandas as pd

details_data = pd.read_csv('Scrapers/steam_data_details/details_data.csv')
reviews_data = pd.read_csv('Scrapers/steam_data_reviews/reviews_summary_games.csv')
dlc_data = pd.read_csv('Scrapers/steam_data_details/dlc_data.csv')
genres_data = pd.read_csv('Scrapers/steam_data_details/genres_data.csv')
tags_data = pd.read_csv('Scrapers/steam_data_tags/tags_data.csv')
cats_data = pd.read_csv('Scrapers/steam_data_details/categories_data.csv')

revenue_data = pd.read_csv('Transformers/tables/revenue_table.csv')

### Column Count => 94
# 1. Details - App, Name, Type, Is Free?, Controller Support? => 3
# filter details_data for relevant columns
details_cols = ['steam_appid', 'name', 'type', 'is_free', 'controller_support']
details_data = details_data[details_cols]
details_data = details_data[details_data['type'] == 'game'].drop_duplicates('steam_appid')


# 2. Reviews - Total and Score => 2
reviews_cols = ['steam_appid', 'review_score', 'total_reviews']
reviews_data = reviews_data[reviews_cols]


# 3. DLC Counts => 1
dlc_cols = ['steam_appid', 'dlc']
dlc_data = dlc_data[dlc_cols]
dlc_data = dlc_data.groupby('steam_appid').size().reset_index(name='dlc_count')


# 4. Genres Unique - limited (33 unique, top 10 + Others) => 11
genres_cols = ['steam_appid', 'description']
genres_data = genres_data[genres_cols]


# 5. Tags Unique - limited (446 unique, top 50? + Others) => 51
tags_cols = ['steam_appid', 'tag_name']
tags_data = tags_data[tags_cols]


# 6. Categories Counts - limited (58 unique, top 25 + Others)=> 26
cats_cols = ['steam_appid', 'description']
cats_data = cats_data[cats_cols]


# 8. Rename the duplicated column names and filter Units table columns
genres_data = genres_data.rename(columns={'description': 'genres_description'})
cats_data = cats_data.rename(columns={'description': 'cats_description'})

revenue_cols = ['steam_appid', 'units_sold_lowerbound', 'units_sold', 'units_sold_upperbound']
revenue_data = revenue_data[revenue_cols]


def limit_and_pivot(df: pd.DataFrame, col_name, top_n, prefix) -> pd.DataFrame:
    # Get the top N most frequent values
    top_v = df[col_name].value_counts().nlargest(top_n).index
    df_filtered = df.copy()
    df_filtered[col_name] = df_filtered[col_name].where(df_filtered[col_name].isin(top_v), 'Other')
    
    # 2. Create dummies
    dummies = pd.get_dummies(df_filtered, columns=[col_name], prefix=prefix)
    
    # 3. Group by appid so each game is exactly ONE row
    return dummies.groupby('steam_appid').max()

genres_final = limit_and_pivot(genres_data, 'genres_description', 10, 'genre')
tags_final = limit_and_pivot(tags_data, 'tag_name', 50, 'tag')
cats_final = limit_and_pivot(cats_data, 'cats_description', 25, 'cat')


# 9. Merge all to Details table, then add Units table
master_data = details_data.merge(reviews_data, how='left', on='steam_appid') \
    .merge(dlc_data, how='left', on='steam_appid') \
    .merge(genres_final, how='left', on='steam_appid') \
    .merge(tags_final, how='left', on='steam_appid') \
    .merge(cats_final, how='left', on='steam_appid') \
    .merge(revenue_data, how='left', on='steam_appid')


if __name__ == "__main__":
    master_data = master_data.fillna(0)
    master_data = pd.get_dummies(master_data, columns=['is_free', 'controller_support', 'review_score'])

    # Reorder columns to have units sold at the end
    cols_to_move = ['units_sold_lowerbound', 'units_sold', 'units_sold_upperbound']
    new_column_order = [col for col in master_data.columns if col not in cols_to_move] + cols_to_move
    master_data = master_data[new_column_order]
    
    os.makedirs(os.path.dirname('Transformers/tables/master_table.csv'), exist_ok=True)
    master_data.to_csv('Transformers/tables/master_table.csv', index=False)

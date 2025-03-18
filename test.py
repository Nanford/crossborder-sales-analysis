import pandas as pd

# 读取Excel数据
def load_data(filepath):
    df = pd.read_excel(filepath)
    return df

# 数据清洗和整理
def preprocess_data(df):
    current_week_data = df[df['周'] == '本周']
    previous_week_data = df[df['周'] == '上周']

    current_summary = current_week_data.groupby('平台').agg({
        '销售额': 'sum',
        '销量': 'sum',
        '销售毛利额': 'sum',
        '毛利率': 'mean'
    }).rename(columns=lambda x: f'本周{x}')

    previous_summary = previous_week_data.groupby('平台').agg({
        '销售额': 'sum',
        '销量': 'sum',
        '销售毛利额': 'sum',
        '毛利率': 'mean'
    }).rename(columns=lambda x: f'上周{x}')

    summary_comparison = current_summary.join(previous_summary, how='outer').fillna(0)
    for metric in ['销售额', '销量', '销售毛利额']:
        summary_comparison[f'{metric}环比'] = (summary_comparison[f'本周{metric}'] - summary_comparison[f'上周{metric}']) / summary_comparison[f'上周{metric}'].replace({0: None})

    return summary_comparison.reset_index()

# Top销售额和销量的产品环比分析
def top_product_analysis(df, top_n=5):
    current_week = df[df['周'] == '本周']
    previous_week = df[df['周'] == '上周']

    top_sales = current_week.groupby('SKU&仓库')['销售额'].sum().nlargest(top_n).reset_index()
    top_volume = current_week.groupby('SKU&仓库')['销量'].sum().nlargest(top_n).reset_index()

    top_sales_comparison = pd.merge(top_sales, previous_week.groupby('SKU&仓库')['销售额'].sum().reset_index(), on='SKU&仓库', how='left', suffixes=('本周', '上周')).fillna(0)
    top_volume_comparison = pd.merge(top_volume, previous_week.groupby('SKU&仓库')['销量'].sum().reset_index(), on='SKU&仓库', how='left', suffixes=('本周', '上周')).fillna(0)

    top_sales_comparison['销售额环比'] = top_sales_comparison.apply(lambda row: (row['销售额本周'] - row['销售额上周']) / row['销售额上周'] if row['销售额上周'] != 0 else None, axis=1)
    top_volume_comparison['销量环比'] = top_volume_comparison.apply(lambda row: (row['销量本周'] - row['销量上周']) / row['销量上周'] if row['销量上周'] != 0 else None, axis=1)

    return top_sales_comparison, top_volume_comparison

# 国家销售额占比和环比情况分析
def country_sales_analysis(df):
    current_week_country = df[df['周'] == '本周'].groupby('买家国家')['销售额'].sum().reset_index()
    previous_week_country = df[df['周'] == '上周'].groupby('买家国家')['销售额'].sum().reset_index()

    country_comparison = pd.merge(current_week_country, previous_week_country, on='买家国家', how='outer', suffixes=('本周', '上周')).fillna(0)
    country_comparison['销售额环比'] = country_comparison.apply(lambda row: (row['销售额本周'] - row['销售额上周']) / row['销售额上周'] if row['销售额上周'] != 0 else None, axis=1)
    country_comparison['销售额占比'] = country_comparison['销售额本周'] / country_comparison['销售额本周'].sum()

    return country_comparison

# 主函数
def main():
    filepath = 'salesdata.xlsx'
    df = load_data(filepath)

    summary = preprocess_data(df)
    top_sales, top_volume = top_product_analysis(df)
    country_sales = country_sales_analysis(df)

    print("销售数据环比分析：")
    print(summary)
    print("\nTop销售额产品环比分析：")
    print(top_sales)
    print("\nTop销量产品环比分析：")
    print(top_volume)
    print("\n国家销售额占比与环比分析：")
    print(country_sales)

if __name__ == '__main__':
    main()

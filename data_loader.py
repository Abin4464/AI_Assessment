import pandas as pd
from config import DATA_PATH

def load_tickets():
    # handling dates
    df = pd.read_csv(DATA_PATH, parse_dates=["created_at"])

    # handling time 
    df["resolution_time_hrs"] = pd.to_numeric(
        df["resolution_time_hrs"], errors="coerce"
    )

    # handling customer ratings
    df["customer_rating"] = pd.to_numeric(
        df["customer_rating"], errors="coerce"
    )

    text_columns = df.select_dtypes(include="object").columns
    for col in text_columns:
        df[col] = df[col].str.strip()
 
    return df

# to confirm weather data loaded correctly or not.
def get_summary(df):
    return {
        "total_tickets": len(df),
        "date_range": (df["created_at"].min(), df["created_at"].max()),
        "status_counts": df["status"].value_counts().to_dict(),
        "priority_counts": df["priority"].value_counts().to_dict(),
        "unresolved_count": df["resolution_time_hrs"].isna().sum(),
    }

if __name__ == "__main__":
    tickets_df = load_tickets()
    print(tickets_df.head())
    print()
    print("Summary:")
    for key, value in get_summary(tickets_df).items():
        print(f"  {key}: {value}")


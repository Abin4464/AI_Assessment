import pandas as pd

HOURS_THRESHOLD = 24


def detect_stale_high_priority(df: pd.DataFrame, now: pd.Timestamp = None) -> pd.DataFrame:
    if now is None:
        now = df["created_at"].max()

    age_hours = (now - df["created_at"]).dt.total_seconds() / 3600

    is_stale = (
        (df["status"] == "Open")
        & (df["priority"].isin(["High", "Critical"]))
        & (age_hours > HOURS_THRESHOLD)
    )

    result = df[is_stale].copy()
    result["age_hours"] = age_hours[is_stale].round(1)
    return result[["ticket_id", "priority", "agent_id", "created_at", "age_hours", "issue_summary"]]


def detect_resolution_time_outliers(df: pd.DataFrame) -> pd.DataFrame:
    resolved = df[df["resolution_time_hrs"].notna()]

    q1 = resolved["resolution_time_hrs"].quantile(0.25)
    q3 = resolved["resolution_time_hrs"].quantile(0.75)
    iqr = q3 - q1
    upper_bound = q3 + 1.5 * iqr

    outliers = resolved[resolved["resolution_time_hrs"] > upper_bound].copy()
    outliers = outliers.sort_values("resolution_time_hrs", ascending=False)

    return outliers[["ticket_id", "priority", "agent_id", "resolution_time_hrs", "issue_summary"]], upper_bound


def get_all_anomalies(df: pd.DataFrame) -> dict:
    stale = detect_stale_high_priority(df)
    outliers, threshold_used = detect_resolution_time_outliers(df)

    return {
        "stale_high_priority": {
            "count": len(stale),
            "threshold_hours": HOURS_THRESHOLD,
            "tickets": stale.to_dict(orient="records"),
        },
        "resolution_time_outliers": {
            "count": len(outliers),
            "threshold_hours_used": round(threshold_used, 1),
            "tickets": outliers.to_dict(orient="records"),
        },
    }


# Quick manual verification, independent of any API/UI.
if __name__ == "__main__":
    from data_loader import load_tickets

    df = load_tickets()
    anomalies = get_all_anomalies(df)

    print(f"Stale High/Critical tickets (>{HOURS_THRESHOLD}h open): "
          f"{anomalies['stale_high_priority']['count']}")
    print(f"Resolution time outliers (IQR method, threshold="
          f"{anomalies['resolution_time_outliers']['threshold_hours_used']}h): "
          f"{anomalies['resolution_time_outliers']['count']}")
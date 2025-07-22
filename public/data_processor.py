# data_processor.py
import pandas as pd
from collections import defaultdict
import requests
from io import StringIO
import re

# Configuration
BASE_URL = "https://raw.githubusercontent.com/{owner}/{repo}/main/{path}/"
VERSION = "3.4.1"  # Update this for each new version


def download_csv(url):
    """Download CSV file from GitHub"""
    print(f"Downloading: {url}")
    response = requests.get(url)
    response.raise_for_status()
    return StringIO(response.text)


def normalize_name(name):
    """Normalize character names to standard format"""
    # Skip NaN values
    if pd.isna(name):
        return None

    # Convert to string if it's a float
    if isinstance(name, float):
        name = str(int(name)) if name.is_integer() else str(name)

    # Remove extra spaces and special characters
    name = re.sub(r"\s+", " ", str(name).strip())

    # Handle known aliases
    aliases = {"nan": None}
    return aliases.get(name, name)


def process_moc_data(df):
    """Process Memory of Chaos data"""
    print(f"Processing MoC data ({len(df)} rows)")

    # Convert character columns to string
    char_cols = ["ch1", "ch2", "ch3", "ch4"]
    for col in char_cols:
        df[col] = df[col].astype(str)

    # Convert to numeric and filter
    df["floor"] = pd.to_numeric(df["floor"], errors="coerce")
    df["star_num"] = pd.to_numeric(df["star_num"], errors="coerce")
    df["round_num"] = pd.to_numeric(df["round_num"], errors="coerce")

    # Filter for Floor 12 and 3-star clears
    filtered = df[(df["floor"] == 12) & (df["star_num"] == 3)]
    print(f"After filtering: {len(filtered)} rows")

    # Group by UID and floor to find complete stages
    stage_groups = filtered.groupby(["uid", "floor"])
    complete_stages = stage_groups.filter(
        lambda x: len(x) == 2
    )  # Only stages with both nodes

    # Calculate statistics
    total_stages = len(complete_stages) / 2
    print(f"Total complete stages: {total_stages}")

    if total_stages == 0:
        print("Warning: No complete stages found!")
        return {}

    char_stats = defaultdict(lambda: {"cycle_sum": 0, "count": 0})

    for _, row in complete_stages.iterrows():
        cycles = row["round_num"]
        for char_col in char_cols:
            char_name = normalize_name(row[char_col])
            if not char_name:  # Skip None values
                continue
            char_stats[char_name]["cycle_sum"] += cycles
            char_stats[char_name]["count"] += 1

    # Calculate averages
    results = {}
    for char, stats in char_stats.items():
        avg_cycles = stats["cycle_sum"] / stats["count"]
        usage_rate = stats["count"] / total_stages * 100
        results[char] = {"cycles": avg_cycles, "usage": usage_rate}

    print(f"Processed {len(results)} characters for MoC")
    return results


def process_score_data(df, mode):
    """Process Pure Fiction or Apocalyptic Shadow data"""
    print(f"Processing {mode} data ({len(df)} rows)")

    # Convert character columns to string
    char_cols = ["ch1", "ch2", "ch3", "ch4"]
    for col in char_cols:
        df[col] = df[col].astype(str)

    # Convert to numeric and filter
    df["floor"] = pd.to_numeric(df["floor"], errors="coerce")
    df["star_num"] = pd.to_numeric(df["star_num"], errors="coerce")
    df["round_num"] = pd.to_numeric(df["round_num"], errors="coerce")

    # Filter for Floor 4 and 3-star clears
    filtered = df[(df["floor"] == 4) & (df["star_num"] == 3)]
    print(f"After filtering: {len(filtered)} rows")

    # Group by UID and floor to find complete stages
    stage_groups = filtered.groupby(["uid", "floor"])
    complete_stages = stage_groups.filter(
        lambda x: len(x) == 2
    )  # Only stages with both nodes

    # Calculate statistics
    total_stages = len(complete_stages) / 2
    print(f"Total complete stages: {total_stages}")

    if total_stages == 0:
        print("Warning: No complete stages found!")
        return {}

    char_stats = defaultdict(lambda: {"score_sum": 0, "count": 0})

    for _, row in complete_stages.iterrows():
        score = row["round_num"]
        for char_col in char_cols:
            char_name = normalize_name(row[char_col])
            if not char_name:  # Skip None values
                continue
            char_stats[char_name]["score_sum"] += score
            char_stats[char_name]["count"] += 1

    # Calculate averages
    results = {}
    for char, stats in char_stats.items():
        avg_score = stats["score_sum"] / stats["count"]
        usage_rate = stats["count"] / total_stages * 100
        results[char] = {"score": avg_score, "usage": usage_rate}

    print(f"Processed {len(results)} characters for {mode}")
    return results


def get_processed_data(version=VERSION, owner="owner", repo="repo", path="path"):
    """Get all processed data from GitHub CSVs"""
    # Download and process MOC data
    moc_url = f"{BASE_URL.format(owner=owner, repo=repo, path=path)}{version}.csv"
    try:
        moc_df = pd.read_csv(download_csv(moc_url))
        moc_data = process_moc_data(moc_df)
    except Exception as e:
        print(f"Error processing MoC data: {str(e)}")
        moc_data = {}

    # Download and process Pure Fiction data
    pf_url = f"{BASE_URL.format(owner=owner, repo=repo, path=path)}{version}_pf.csv"
    try:
        pf_df = pd.read_csv(download_csv(pf_url))
        pf_data = process_score_data(pf_df, "pf")
    except Exception as e:
        print(f"Error processing PF data: {str(e)}")
        pf_data = {}

    # Download and process Apocalyptic Shadow data
    as_url = f"{BASE_URL.format(owner=owner, repo=repo, path=path)}{version}_as.csv"
    try:
        as_df = pd.read_csv(download_csv(as_url))
        as_data = process_score_data(as_df, "as")
    except Exception as e:
        print(f"Error processing AS data: {str(e)}")
        as_data = {}

    # Combine all data
    all_chars = set(moc_data.keys()) | set(pf_data.keys()) | set(as_data.keys())
    combined = {}

    for char in all_chars:
        char_data = {}
        if char in moc_data:
            char_data["moc"] = moc_data[char]
        if char in pf_data:
            char_data["pf"] = pf_data[char]
        if char in as_data:
            char_data["as"] = as_data[char]
        combined[char] = char_data

    print(f"Final dataset has {len(combined)} characters")
    return combined


if __name__ == "__main__":
    # Example usage - will run when script is executed directly
    print("Running data processor test...")
    data = get_processed_data(
        version="3.4.1", owner="LvlUrArti", repo="MocStats", path="data/raw_csvs"
    )

    if data:
        print("Processed data for characters:", list(data.keys()))
        print("Example character data:")
        for char, stats in list(data.items())[:3]:
            print(f"{char}: {stats}")
    else:
        print("No data processed")

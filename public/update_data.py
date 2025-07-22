# update_data.py
import json
import os
from datetime import datetime
import pandas as pd
from tierlist import DATASET_PATH
from data_processor import get_processed_data  # Import the processor

ARCHIVE_DIR = "dataset_archive/"


def clean_dataset(data):
    """Remove NaN characters and invalid entries"""
    cleaned = {}
    for char, stats in data.items():
        # Skip NaN characters
        if pd.isna(char) or char == "nan":
            continue

        # Create a clean entry
        clean_stats = {}
        for mode, mode_stats in stats.items():
            if mode == "moc":
                clean_stats["moc"] = {
                    "cycles": float(mode_stats.get("cycles", 10)),
                    "usage": float(mode_stats.get("usage", 0)),
                }
            elif mode in ["pf", "as"]:
                clean_stats[mode] = {
                    "score": float(mode_stats.get("score", 0)),
                    "usage": float(mode_stats.get("usage", 0)),
                }
        cleaned[char] = clean_stats
    return cleaned


def update_dataset(new_data):
    """Update dataset with versioning"""
    # Archive current dataset if exists
    if os.path.exists(DATASET_PATH):
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        os.makedirs(ARCHIVE_DIR, exist_ok=True)
        os.rename(DATASET_PATH, f"{ARCHIVE_DIR}dataset_{timestamp}.json")

    # Save new dataset
    with open(DATASET_PATH, "w") as f:
        json.dump(new_data, f, indent=2)


def validate_data(data):
    """Ensure data has required structure"""
    for char, stats in data.items():
        for mode in ["moc", "pf", "as"]:
            if mode in stats:
                if mode == "moc":
                    if "cycles" not in stats[mode] or "usage" not in stats[mode]:
                        raise ValueError(f"Missing data in MoC for {char}")
                else:
                    if "score" not in stats[mode] or "usage" not in stats[mode]:
                        raise ValueError(f"Missing data in {mode.upper()} for {char}")


if __name__ == "__main__":
    try:
        # Fetch and process data from GitHub
        print("Fetching and processing data from GitHub...")
        new_data = get_processed_data(
            version="3.4.1",  # Update version as needed
            owner="LvlUrArti",  # GitHub owner
            repo="MocStats",  # Repository name
            path="data/raw_csvs",  # Path to CSV files
        )

        # Clean the dataset
        new_data = clean_dataset(new_data)

        # Validate before updating
        validate_data(new_data)

        # Perform update
        update_dataset(new_data)
        print(f"Dataset updated successfully! Processed {len(new_data)} characters.")

        # Print archive info
        if os.path.exists(ARCHIVE_DIR):
            archives = os.listdir(ARCHIVE_DIR)
            if archives:
                print(f"Previous version archived as: {archives[-1]}")
    except ValueError as e:
        print(f"Validation Error: {e}")
        print("Update aborted. Please fix data format.")
    except Exception as e:
        print(f"Unexpected Error: {e}")
        print("Update failed. Check the GitHub URL or data format.")

import json
import os
from datetime import datetime

# Configuration
TIER_RATIOS = {"S": 0.1, "A": 0.2, "B": 0.3, "C": 0.3}  # D-tier gets remainder
WEIGHTS = {"performance": 0.7, "usage": 0.3}
DATASET_PATH = "hsr_dataset.json"
ROLES_PATH = "character_roles.json"
ROLE_TYPES = ["DPS", "Sub DPS", "Amplifier", "Sustain"]

MIN_USAGE = 0.5
USAGE_CAP = 95


def calculate_scores(data):
    scores = {"moc": {}, "pf": {}, "as": {}, "general": {}}

    for char, stats in data.items():
        # Process MoC
        if "moc" in stats:
            moc_stats = stats["moc"]
            cycles = min(moc_stats["cycles"], 10)
            perf_moc = (10 - cycles) / 10

            # Apply usage threshold and cap
            usage = max(min(moc_stats["usage"], USAGE_CAP), MIN_USAGE)
            usage_moc = usage / 100

            scores["moc"][char] = (WEIGHTS["performance"] * perf_moc) + (
                WEIGHTS["usage"] * usage_moc
            )

        # Process Pure Fiction
        if "pf" in stats:
            pf_stats = stats["pf"]
            score_val = max(23000, min(pf_stats["score"], 40000))
            perf_pf = score_val / 40000

            # Apply usage threshold and cap
            usage = max(min(pf_stats["usage"], USAGE_CAP), MIN_USAGE)
            usage_pf = usage / 100

            scores["pf"][char] = (WEIGHTS["performance"] * perf_pf) + (
                WEIGHTS["usage"] * usage_pf
            )

        # Process Apocalyptic Shadow
        if "as" in stats:
            as_stats = stats["as"]
            score_val = max(3100, min(as_stats["score"], 4000))
            perf_as = score_val / 4000

            # Apply usage threshold and cap
            usage = max(min(as_stats["usage"], USAGE_CAP), MIN_USAGE)
            usage_as = usage / 100

            scores["as"][char] = (WEIGHTS["performance"] * perf_as) + (
                WEIGHTS["usage"] * usage_as
            )

        # General Score Calculation
        mode_scores = []
        for mode in ["moc", "pf", "as"]:
            if mode in scores and char in scores[mode]:
                mode_scores.append(scores[mode][char])

        if mode_scores:
            scores["general"][char] = sum(mode_scores) / len(mode_scores)

    return scores


def assign_tiers(score_dict, data=None):
    """Assign tiers based on score distribution"""
    # If data is provided, filter out non-viable characters
    if data is not None:
        viable_chars = {
            char: score
            for char, score in score_dict.items()
            if any(
                mode in data.get(char, {})
                and data[char][mode].get("usage", 0) >= MIN_USAGE
                for mode in ["moc", "pf", "as"]
            )
        }
    else:
        viable_chars = score_dict

    sorted_chars = sorted(viable_chars.items(), key=lambda x: x[1], reverse=True)
    n_chars = len(sorted_chars)

    # Calculate tier counts
    counts = {}
    cumulative = 0
    for tier, ratio in TIER_RATIOS.items():
        count = max(1, round(n_chars * ratio))
        cumulative += count
        counts[tier] = count

    # Handle remainder for D-tier
    counts["D"] = n_chars - cumulative

    # Assign tiers
    tiers = {t: [] for t in ["S", "A", "B", "C", "D"]}
    index = 0
    for tier, count in counts.items():
        for i in range(count):
            if index < n_chars:
                tiers[tier].append(sorted_chars[index][0])
                index += 1
    non_viable = set(score_dict.keys()) - set(viable_chars.keys())
    tiers["D"].extend(non_viable)
    return tiers


def generate_role_based_tier_lists(data, scores):
    """Generate tier lists for each role and game mode"""
    try:
        with open(ROLES_PATH) as f:
            role_data = json.load(f)
    except FileNotFoundError:
        print(f"Error: Role file {ROLES_PATH} not found!")
        return {}

    # Create the tier list structure
    tier_lists = {
        "Memory of Chaos": {role: {} for role in ROLE_TYPES},
        "Pure Fiction": {role: {} for role in ROLE_TYPES},
        "Apocalyptic Shadow": {role: {} for role in ROLE_TYPES},
        "General Tier List": {role: {} for role in ROLE_TYPES},
    }

    # Map internal names to display names
    mode_mapping = {
        "moc": "Memory of Chaos",
        "pf": "Pure Fiction",
        "as": "Apocalyptic Shadow",
        "general": "General Tier List",
    }

    # Process each game mode and role
    for mode_key, mode_name in mode_mapping.items():
        if mode_key not in scores:
            continue

        for role in ROLE_TYPES:
            role_scores = {}
            for char in scores[mode_key]:
                # Only include characters with this role
                if char in role_data and role in role_data[char]:
                    role_scores[char] = scores[mode_key][char]

            # Only create tier list if there are characters in this role
            if role_scores:
                tier_lists[mode_name][role] = assign_tiers(role_scores, data)

    return tier_lists


# Example Usage
if __name__ == "__main__":
    # Load dataset (example structure shown below)
    try:
        with open(DATASET_PATH) as f:
            data = json.load(f)
    except FileNotFoundError:
        print(f"Error: Dataset file {DATASET_PATH} not found!")
        print("Please run update_data.py first to create a dataset.")
        exit(1)

    # Calculate scores
    scores = calculate_scores(data)

    # Generate role-based tier lists
    tier_lists = generate_role_based_tier_lists(data, scores)

    # Print results
    for mode, role_data in tier_lists.items():
        print(f"\n{mode.upper():^40}")
        print("=" * 40)
        for role, tiers in role_data.items():
            print(f"\n{role}:")
            for tier, chars in tiers.items():
                if chars:  # Only print if there are characters
                    print(f"  {tier}-tier: {', '.join(chars)}")

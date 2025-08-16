import json
import numpy as np
import os
import datetime

# Tier value mapping with finer granularity
TIER_VALUES = {
    "T0": 10.0,
    "T0.5": 9.7,
    "T1": 9.3,
    "T1.5": 8.7,
    "T2": 8.0,
    "T3": 7.0,
    "T4": 6.0,
    "T5": 5.0,
}


def calculate_score(ratings):
    """Calculate aggregated score with bonuses for consistency and top placements"""
    if not ratings:
        return 0.0

    values = [TIER_VALUES[r["tier"]] for r in ratings]

    # Weighted average (higher weight for better ratings)
    weights = np.linspace(1.5, 0.5, len(values))
    base_score = np.average(sorted(values, reverse=True), weights=weights)

    # Consistency bonus (1 - std_dev)
    std_dev = np.std(values)
    consistency_bonus = (1 - min(std_dev, 1.0)) * 0.3

    # Top tier bonus (count of T0/T0.5)
    top_count = sum(1 for v in values if v >= 9.7)
    top_bonus = min(top_count * 0.15, 0.45)

    # Missing data penalty
    missing_penalty = (3 - len(values)) * 0.2

    return base_score + consistency_bonus + top_bonus - missing_penalty


def generate_tierlist(data):
    aggregated = {}
    role_stats = {}

    # First pass: calculate raw scores and collect role statistics
    for char, char_data in data["characters"].items():
        for role, ratings in char_data["roles"].items():
            if not ratings:
                continue

            score = calculate_score(ratings)
            entry = {
                "character": char,
                "raw_score": score,
                "details": {
                    "modes": [r["mode"] for r in ratings],
                    "tiers": [r["tier"] for r in ratings],
                },
            }

            # Collect for normalization
            aggregated.setdefault(role, []).append(entry)
            role_stats.setdefault(role, {"min": float("inf"), "max": float("-inf")})

            # Update role min/max
            if score < role_stats[role]["min"]:
                role_stats[role]["min"] = score
            if score > role_stats[role]["max"]:
                role_stats[role]["max"] = score

    # Normalize scores per role (0-1 scale)
    for role, entries in aggregated.items():
        min_score = role_stats[role]["min"]
        max_score = role_stats[role]["max"]
        score_range = max_score - min_score if max_score > min_score else 1.0

        for entry in entries:
            entry["norm_score"] = (entry["raw_score"] - min_score) / score_range

    # Final tier assignment with 0-1 boundaries
    TIER_BOUNDARIES = [
        (0.95, "T0"),
        (0.85, "T0.5"),
        (0.75, "T1"),
        (0.65, "T1.5"),
        (0.55, "T2"),
        (0.35, "T3"),
        (0.10, "T4"),
        (0.00, "T5"),
    ]

    tierlist = {}
    for role, chars in aggregated.items():
        # Sort characters by normalized score
        sorted_chars = sorted(chars, key=lambda x: x["norm_score"], reverse=True)

        # Assign tiers
        tier_groups = {tier: [] for _, tier in TIER_BOUNDARIES}
        for char in sorted_chars:
            for boundary, tier in TIER_BOUNDARIES:
                if char["norm_score"] >= boundary:
                    tier_groups[tier].append(char)
                    break

        tierlist[role] = tier_groups

    return tierlist


def generate_html_tierlist(tierlist_data, output_file="../public/index.html"):
    """Generate an HTML tier list page from the tierlist data"""
    # Define tier colors with more vibrant palette
    TIER_COLORS = {
        "T0": "#FF6B6B",  # Coral red
        "T0.5": "#FF9E6B",  # Peach
        "T1": "#FFD166",  # Pastel yellow
        "T1.5": "#A3C586",  # Sage green
        "T2": "#4ECDC4",  # Turquoise
        "T3": "#6A7FDB",  # Periwinkle
        "T4": "#9B59B6",  # Lavender
        "T5": "#95A5A6",  # Cool gray
    }

    # Role display names
    ROLE_NAMES = {
        "DPS": "DPS",
        "Support DPS": "Sub-DPS",
        "Amplifier": "Amplifier",
        "Sustain": "Sustain",
    }

    def get_icon_filename(character_name):
        """Convert character name to icon filename format"""
        return (
            character_name.lower()
            .replace(" ", "_")
            .replace("'", "")
            .replace("\u2022", "_")
            + "_icon.png"
        )

    # Collect all roles and tiers
    roles = list(tierlist_data.keys())
    tiers = list(TIER_COLORS.keys())

    # Generate HTML with enhanced design
    html = f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Honkai: Star Rail Tier List</title>
        <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap" rel="stylesheet">
        <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
        <link rel="icon" href="favicon.png" type="image/png">
        <style>
            :root {{
                --background-dark: #0f0f1d;
                --background-card: #1a182d;
                --text-primary: #f0f0ff;
                --text-secondary: #a0a0c0;
                --accent-color: #6a7fdb;
                --transition-speed: 0.3s;
                --card-shadow: 0 4px 20px rgba(0, 0, 0, 0.3);
                --card-radius: 12px;
            }}
            
            * {{
                margin: 0;
                padding: 0;
                box-sizing: border-box;
            }}
            
            body {{
                font-family: 'Inter', sans-serif;
                background: var(--background-dark);
                color: var(--text-primary);
                line-height: 1.6;
                padding: 20px;
                min-height: 100vh;
                background-attachment: fixed;
                overflow-x: hidden;
            }}
            
            .container {{
                max-width: 1400px;
                margin: 0 auto;
            }}
            
            header {{
                text-align: center;
                margin-bottom: 40px;
                padding: 40px 20px;
                background: var(--background-card);
                border-radius: var(--card-radius);
                box-shadow: var(--card-shadow);
                backdrop-filter: blur(10px);
                border: 1px solid rgba(255, 255, 255, 0.05);
                position: relative;
                overflow: hidden;
                z-index: 2;
            }}
            
            h1 {{
                font-size: 2.8rem;
                margin-bottom: 15px;
                font-weight: 700;
                letter-spacing: -0.5px;
                background: linear-gradient(to right, #f0f0ff, #a0a0c0);
                -webkit-background-clip: text;
                -webkit-text-fill-color: transparent;
            }}
            
            .subtitle {{
                font-size: 1.1rem;
                color: var(--text-secondary);
                max-width: 700px;
                margin: 0 auto 25px;
                font-weight: 300;
            }}
            
            .legend {{
                display: flex;
                justify-content: center;
                flex-wrap: wrap;
                gap: 10px;
                margin-top: 30px;
            }}
            
            .legend-item {{
                display: flex;
                align-items: center;
                background: rgba(40, 37, 60, 0.3);
                padding: 8px 16px;
                border-radius: 30px;
                font-size: 0.9rem;
                border: 1px solid rgba(255, 255, 255, 0.08);
                transition: all 0.3s ease;
            }}
            
            .legend-item:hover {{
                transform: translateY(-3px);
                background: rgba(50, 47, 70, 0.5);
            }}
            
            .legend-color {{
                width: 16px;
                height: 16px;
                border-radius: 50%;
                margin-right: 8px;
                box-shadow: 0 0 8px currentColor;
            }}
            
            .tier-list {{
                background: var(--background-card);
                border-radius: var(--card-radius);
                box-shadow: var(--card-shadow);
                backdrop-filter: blur(10px);
                border: 1px solid rgba(255, 255, 255, 0.05);
                overflow: hidden;
                padding: 25px;
                margin-bottom: 40px;
                position: relative;
            }}
            
            table {{
                width: 100%;
                border-collapse: separate;
                border-spacing: 0;
                background-color: transparent;
                position: relative;
                z-index: 1;
            }}
            
            th, td {{
                padding: 16px 20px;
                text-align: left;
                border-bottom: 1px solid rgba(255, 255, 255, 0.05);
            }}
            
            thead th {{
                background: rgba(30, 28, 50, 0.9);
                font-weight: 600;
                text-transform: uppercase;
                letter-spacing: 1px;
                text-align: center;
                position: sticky;
                top: 0;
                z-index: 10;
                backdrop-filter: blur(8px);
                color: #ffffff;
                font-size: 1.1rem;
                border-top: 1px solid rgba(255, 255, 255, 0.05);
                border-bottom: 1px solid rgba(255, 255, 255, 0.1);
            }}
            
            .tier-header {{
                font-weight: 700;
                text-align: center;
                width: 100px;
                position: sticky;
                left: 0;
                z-index: 5;
                font-size: 1.1rem;
                background: rgba(20, 18, 35, 0.9);
                backdrop-filter: blur(5px);
                border-right: 1px solid rgba(255, 255, 255, 0.05);
            }}
            
            .character-cell {{
                min-width: 250px;
            }}
            
            .character {{
                display: inline-flex;
                align-items: center;
                background: rgba(30, 28, 45, 0.7);
                padding: 10px 18px;
                margin: 6px;
                border-radius: 10px;
                transition: all var(--transition-speed) ease;
                cursor: default;
                animation: fadeIn 0.5s ease-out;
                border: 1px solid rgba(255, 255, 255, 0.05);
                position: relative;
                overflow: hidden;
                z-index: 1;
                backdrop-filter: blur(4px);
            }}
            
            .character:hover {{
                transform: translateY(-5px);
                box-shadow: 0 8px 20px rgba(0, 0, 0, 0.3);
                z-index: 2;
                border-color: rgba(255, 255, 255, 0.15);
            }}
            
            .character-icon {{
                width: 36px;
                height: 36px;
                border-radius: 50%;
                margin-right: 12px;
                flex-shrink: 0;
                object-fit: cover;
                border: 1px solid rgba(255, 255, 255, 0.15);
                background: rgba(0, 0, 0, 0.3);
                transition: all 0.3s ease;
            }}
            
            .character:hover .character-icon {{
                transform: scale(1.1);
                box-shadow: 0 0 12px rgba(255, 255, 255, 0.1);
            }}
            
            .character-name {{
                position: relative;
                z-index: 1;
                font-weight: 500;
                font-size: 0.95rem;
            }}
            
            .role-column {{
                vertical-align: top;
                background: rgba(25, 23, 40, 0.4);
                transition: background-color 0.3s;
                backdrop-filter: blur(3px);
            }}
            
            .role-column:hover {{
                background: rgba(35, 33, 50, 0.6);
            }}
            
            footer {{
                text-align: center;
                margin-top: 20px;
                color: var(--text-secondary);
                font-size: 0.9rem;
                padding: 20px;
                background: var(--background-card);
                border-radius: var(--card-radius);
                border: 1px solid rgba(255, 255, 255, 0.05);
                box-shadow: var(--card-shadow);
                backdrop-filter: blur(5px);
            }}
            
            .footer-content {{
                display: flex;
                justify-content: center;
                align-items: center;
                gap: 15px;
                flex-wrap: wrap;
            }}
            
            .update-time {{
                display: flex;
                align-items: center;
                gap: 8px;
            }}
            
            @keyframes fadeIn {{
                from {{ opacity: 0; transform: translateY(10px); }}
                to {{ opacity: 1; transform: translateY(0); }}
            }}
            
            /* Mobile styles */
            @media (max-width: 768px) {{
                .tier-header {{
                    position: static;
                }}
                
                table {{
                    display: block;
                    overflow-x: auto;
                }}
                
                header {{
                    padding: 30px 15px;
                }}
                
                h1 {{
                    font-size: 2.2rem;
                }}
                
                .character {{
                    padding: 8px 14px;
                }}
            }}
            
            .tier-list-mobile {{
                display: none;
                flex-direction: column;
                gap: 25px;
                margin-bottom: 40px;
            }}
            
            .tier-section {{
                background: var(--background-card);
                border-radius: var(--card-radius);
                overflow: hidden;
                box-shadow: var(--card-shadow);
                position: relative;
                z-index: 1;
            }}
            
            .tier-header-mobile {{
                padding: 20px;
                font-weight: 700;
                font-size: 1.4rem;
                text-align: center;
                background: rgba(20, 18, 35, 0.9);
                letter-spacing: 0.5px;
                box-shadow: 0 4px 10px rgba(0, 0, 0, 0.2);
                position: relative;
                z-index: 2;
            }}
            
            .role-row {{
                padding: 16px;
                border-bottom: 1px solid rgba(255, 255, 255, 0.05);
                background: rgba(30, 28, 45, 0.5);
                backdrop-filter: blur(5px);
            }}
            
            .role-row:last-child {{
                border-bottom: none;
            }}
            
            .role-header {{
                font-weight: 600;
                font-size: 1.1rem;
                margin-bottom: 12px;
                color: var(--text-primary);
                display: flex;
                align-items: center;
                gap: 10px;
            }}
            
            .role-header::after {{
                content: '';
                flex-grow: 1;
                height: 1px;
                background: rgba(255, 255, 255, 0.1);
                border-radius: 2px;
            }}
            
            .characters-row {{
                display: flex;
                flex-wrap: wrap;
                gap: 8px;
            }}
            
            /* Responsive switching */
            @media (max-width: 768px) {{
                .desktop-tier-list {{
                    display: none;
                }}
                
                .tier-list-mobile {{
                    display: flex;
                }}
                
                .tier-header {{
                    position: static;
                    border: none;
                    margin-bottom: 5px;
                }}
            }}
            
            @media (min-width: 769px) {{
                .tier-list-mobile {{
                    display: none;
                }}
            }}
            
            /* Glow effect for tiers */
            .tier-glow {{
                position: absolute;
                width: 100%;
                height: 100%;
                top: 0;
                left: 0;
                background: radial-gradient(circle at center, currentColor 0%, transparent 70%);
                opacity: 0.1;
                pointer-events: none;
                z-index: -1;
            }}
        </style>
    </head>
    <body>
        <div class="container">
            <header>
                <h1>Honkai: Star Rail Tier List</h1>
                
                <div class="legend">
                    {"".join(
                        f'<div class="legend-item" style="color: {TIER_COLORS[tier]}">'
                        f'<div class="legend-color" style="background: {TIER_COLORS[tier]}"></div>'
                        f'{tier}'
                        '</div>'
                        for tier in tiers
                    )}
                </div>
            </header>
            
            <!-- Desktop Tier List -->
            <main class="desktop-tier-list tier-list">
                <table>
                    <thead>
                        <tr>
                            <th>Tier</th>
                            {"".join(f'<th>{ROLE_NAMES.get(role, role)}</th>' for role in roles)}
                        </tr>
                    </thead>
                    <tbody>
    """

    # Generate table rows (tiers)
    for tier in tiers:
        tier_empty = True
        for role in roles:
            if tier in tierlist_data[role] and tierlist_data[role][tier]:
                tier_empty = False
                break

        if tier_empty:
            continue

        html += f"<tr>"
        html += (
            f'<td class="tier-header" style="color: {TIER_COLORS[tier]}">{tier}</td>'
        )

        for role in roles:
            html += '<td class="role-column character-cell">'
            if tier in tierlist_data[role] and tierlist_data[role][tier]:
                for char in tierlist_data[role][tier]:
                    icon_filename = get_icon_filename(char["character"])
                    html += f"""
                    <div class="character">
                        <div class="tier-glow" style="color: {TIER_COLORS[tier]}"></div>
                        <img class="character-icon" src="icons/{icon_filename}" alt="{char['character']}">
                        <span class="character-name">{char["character"]}</span>
                    </div>
                    """
            html += "</td>"

        html += "</tr>"

    html += """
                    </tbody>
                </table>
            </main>
            
            <!-- Mobile Tier List -->
            <div class="tier-list-mobile">
    """

    # Generate mobile tier sections
    for tier in tiers:
        tier_empty = True
        for role in roles:
            if tier in tierlist_data[role] and tierlist_data[role][tier]:
                tier_empty = False
                break
        if tier_empty:
            continue

        html += f"""
        <div class="tier-section">
            <div class="tier-header-mobile" style="color: {TIER_COLORS[tier]};">
                {tier}
            </div>
        """

        for role in roles:
            if tier in tierlist_data[role] and tierlist_data[role][tier]:
                html += f"""
                <div class="role-row">
                    <div class="role-header">
                        {ROLE_NAMES.get(role, role)}
                    </div>
                    <div class="characters-row">
                """

                for char in tierlist_data[role][tier]:
                    icon_filename = get_icon_filename(char["character"])
                    html += f"""
                    <div class="character">
                        <div class="tier-glow" style="color: {TIER_COLORS[tier]}"></div>
                        <img class="character-icon" src="icons/{icon_filename}" alt="{char['character']}">
                        <span class="character-name">{char["character"]}</span>
                    </div>
                    """

                html += """
                    </div>
                </div>
                """

        html += "</div>"

    html += "</div>"

    # Enhanced footer
    html += f"""
            <footer>
                <div class="footer-content">
                    <div class="update-time">
                        <i class="fas fa-sync-alt"></i>
                        <span>Last updated: {datetime.datetime.now().strftime("%Y-%m-%d %H:%M")}</span>
                    </div>
                </div>
            </footer>
        </div>
        
        <script>
            // Initialize the page with animations
            document.addEventListener('DOMContentLoaded', function() {{
                // Staggered character animations
                document.querySelectorAll('.character').forEach((char, index) => {{
                    char.style.animationDelay = `${{index * 0.03}}s`;
                    
                    // Add tier-specific glow on hover
                    char.addEventListener('mouseenter', function() {{
                        const glow = this.querySelector('.tier-glow');
                        if (glow) {{
                            glow.style.opacity = '0.2';
                        }}
                    }});
                    
                    char.addEventListener('mouseleave', function() {{
                        const glow = this.querySelector('.tier-glow');
                        if (glow) {{
                            glow.style.opacity = '0.1';
                        }}
                    }});
                }});
            }});
        </script>
    </body>
    </html>
    """

    # Save to file
    with open(output_file, "w", encoding="utf-8") as f:
        f.write(html)

    return os.path.abspath(output_file)


if __name__ == "__main__":
    # Load character data
    with open("tier_data.json") as f:
        data = json.load(f)

    # Generate tier list data
    tierlist_data = generate_tierlist(data)

    # Create HTML tier list
    output_path = generate_html_tierlist(tierlist_data)
    print(f"Successfully generated HTML tier list at: {output_path}")

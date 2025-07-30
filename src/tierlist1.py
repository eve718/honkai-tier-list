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
    # Updated vibrant tier colors with better contrast
    TIER_COLORS = {
        "T0": "#ff3366",  # Vibrant pink-red
        "T0.5": "#ff7733",  # Bright orange
        "T1": "#ffcc00",  # Golden yellow
        "T1.5": "#aadd55",  # Lime green
        "T2": "#44cc99",  # Turquoise
        "T3": "#44aaff",  # Vibrant blue
        "T4": "#aa66ff",  # Purple
        "T5": "#cc88ee",  # Light purple
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
        <link href="https://fonts.googleapis.com/css2?family=Montserrat:wght@400;600;700;800&family=Roboto:wght@300;400;500&display=swap" rel="stylesheet">
        <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
        <link rel="icon" href="favicon.png" type="image/png">
        <style>
            :root {{
                --background-dark: #0f0c1d;
                --background-card: #1a1730;
                --text-primary: #f0f0ff;
                --text-secondary: #a0a0c0;
                --accent-color: #ffcc00;
                --transition-speed: 0.3s;
                --card-shadow: 0 6px 16px rgba(0, 0, 0, 0.4);
            }}
            
            * {{
                margin: 0;
                padding: 0;
                box-sizing: border-box;
            }}
            
            body {{
                font-family: 'Roboto', sans-serif;
                background: radial-gradient(circle at top, #1a1a2e 0%, #0f0c1d 70%);
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
                background: rgba(26, 23, 48, 0.85);
                border-radius: 20px;
                box-shadow: var(--card-shadow);
                backdrop-filter: blur(10px);
                border: 1px solid rgba(255, 255, 255, 0.08);
                position: relative;
                overflow: hidden;
                z-index: 2;
            }}
            
            header::before {{
                content: '';
                position: absolute;
                top: 0;
                left: 0;
                right: 0;
                height: 4px;
                background: linear-gradient(90deg, 
                    #ff3366, #ff7733, #ffcc00, #aadd55, 
                    #44cc99, #44aaff, #aa66ff, #cc88ee);
                animation: gradientFlow 8s ease infinite;
                background-size: 300% 300%;
            }}
            
            .header-content {{
                position: relative;
                z-index: 3;
            }}
            
            h1 {{
                font-family: 'Montserrat', sans-serif;
                font-size: 3rem;
                margin-bottom: 15px;
                color: #ffffff;
                text-shadow: 0 0 15px rgba(255, 204, 0, 0.5);
                letter-spacing: 1.5px;
                font-weight: 800;
                background: linear-gradient(to right, #ffcc00, #ff7733, #ff3366);
                -webkit-background-clip: text;
                -webkit-text-fill-color: transparent;
            }}
            
            .subtitle {{
                font-size: 1.2rem;
                color: var(--text-secondary);
                max-width: 800px;
                margin: 0 auto 25px;
            }}
            
            .controls {{
                display: flex;
                justify-content: center;
                gap: 15px;
                margin-top: 20px;
                flex-wrap: wrap;
            }}
            
            .view-toggle {{
                background: rgba(40, 37, 60, 0.8);
                border: 1px solid rgba(255, 255, 255, 0.1);
                color: var(--text-primary);
                padding: 8px 20px;
                border-radius: 30px;
                cursor: pointer;
                transition: all 0.3s ease;
                display: flex;
                align-items: center;
                gap: 8px;
            }}
            
            .view-toggle:hover {{
                background: rgba(60, 55, 90, 0.9);
                transform: translateY(-2px);
                box-shadow: 0 4px 8px rgba(0, 0, 0, 0.3);
            }}
            
            .view-toggle.active {{
                background: var(--accent-color);
                color: #121212;
                font-weight: 600;
            }}
            
            .legend {{
                display: flex;
                justify-content: center;
                flex-wrap: wrap;
                gap: 15px;
                margin-top: 30px;
            }}
            
            .legend-item {{
                display: flex;
                align-items: center;
                background: rgba(40, 37, 60, 0.9);
                padding: 8px 16px;
                border-radius: 30px;
                font-size: 0.95rem;
                border: 1px solid rgba(255, 255, 255, 0.15);
                box-shadow: 0 4px 8px rgba(0, 0, 0, 0.2);
                transition: transform 0.3s ease;
            }}
            
            .legend-item:hover {{
                transform: translateY(-3px);
            }}
            
            .legend-color {{
                width: 18px;
                height: 18px;
                border-radius: 50%;
                margin-right: 10px;
                box-shadow: 0 0 8px currentColor;
            }}
            
            .tier-list {{
                background: rgba(26, 23, 48, 0.8);
                border-radius: 20px;
                box-shadow: var(--card-shadow);
                backdrop-filter: blur(10px);
                border: 1px solid rgba(255, 255, 255, 0.1);
                overflow: hidden;
                padding: 25px;
                margin-bottom: 40px;
                position: relative;
            }}
            
            .tier-list::before {{
                content: '';
                position: absolute;
                top: 0;
                left: 0;
                right: 0;
                bottom: 0;
                background: radial-gradient(circle at center, rgba(255,255,255,0.03) 0%, transparent 70%);
                pointer-events: none;
                z-index: 0;
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
                padding: 18px 22px;
                text-align: left;
                border-bottom: 1px solid rgba(255, 255, 255, 0.1);
            }}
            
            thead th {{
                background: rgba(50, 45, 80, 0.9);
                font-family: 'Montserrat', sans-serif;
                font-weight: 700;
                text-transform: uppercase;
                letter-spacing: 1.5px;
                text-align: center;
                position: sticky;
                top: 0;
                z-index: 10;
                backdrop-filter: blur(8px);
                color: #ffffff;
                font-size: 1.2rem;
                border-top: 1px solid rgba(255, 255, 255, 0.1);
                box-shadow: 0 4px 10px rgba(0, 0, 0, 0.3);
            }}
            
            .tier-header {{
                font-family: 'Montserrat', sans-serif;
                font-weight: 800;
                text-align: center;
                width: 100px;
                position: sticky;
                left: 0;
                z-index: 5;
                font-size: 1.3rem;
                text-shadow: 0 2px 4px rgba(0, 0, 0, 0.4);
                border: 1px solid rgba(255, 255, 255, 0.15);
                box-shadow: 4px 0 8px rgba(0, 0, 0, 0.3);
            }}
            
            .character-cell {{
                min-width: 250px;
            }}
            
            .character {{
                display: inline-flex;
                align-items: center;
                background: linear-gradient(to right, rgba(40, 37, 60, 0.7), rgba(30, 27, 50, 0.9));
                padding: 12px 20px;
                margin: 8px;
                border-radius: 15px;
                transition: all var(--transition-speed) ease;
                cursor: default;
                box-shadow: var(--card-shadow);
                animation: fadeIn 0.5s ease-out;
                border: 1px solid rgba(255, 255, 255, 0.1);
                position: relative;
                overflow: hidden;
                z-index: 1;
                backdrop-filter: blur(4px);
            }}
            
            .character::before {{
                content: '';
                position: absolute;
                top: 0;
                left: 0;
                width: 100%;
                height: 100%;
                background: linear-gradient(120deg, rgba(255,255,255,0.15) 0%, rgba(255,255,255,0) 100%);
                z-index: -1;
                opacity: 0;
                transition: opacity var(--transition-speed);
            }}
            
            .character:hover::before {{
                opacity: 0.6;
            }}
            
            .character:hover {{
                transform: translateY(-8px);
                box-shadow: 0 12px 20px rgba(0, 0, 0, 0.4);
                z-index: 2;
            }}
            
            .character-icon {{
                width: 36px;
                height: 36px;
                border-radius: 50%;
                margin-right: 14px;
                flex-shrink: 0;
                object-fit: cover;
                border: 1px solid rgba(255, 255, 255, 0.25);
                background: rgba(0, 0, 0, 0.3);
                box-shadow: 0 0 10px rgba(0, 0, 0, 0.3);
                transition: all 0.3s ease;
            }}
            
            .character:hover .character-icon {{
                transform: scale(1.1);
                box-shadow: 0 0 15px rgba(255, 255, 255, 0.2);
            }}
            
            .character-name {{
                position: relative;
                z-index: 1;
                font-weight: 500;
                letter-spacing: 0.5px;
            }}
            
            .role-column {{
                vertical-align: top;
                background: rgba(30, 27, 50, 0.4);
                transition: background-color 0.3s;
                backdrop-filter: blur(3px);
            }}
            
            .role-column:hover {{
                background: rgba(40, 37, 70, 0.6);
            }}
            
            footer {{
                text-align: center;
                margin-top: 20px;
                color: var(--text-secondary);
                font-size: 0.95rem;
                padding: 25px;
                background: rgba(26, 23, 48, 0.8);
                border-radius: 15px;
                border: 1px solid rgba(255, 255, 255, 0.1);
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
                from {{ opacity: 0; transform: translateY(15px); }}
                to {{ opacity: 1; transform: translateY(0); }}
            }}
            
            @keyframes gradientFlow {{
                0% {{ background-position: 0% 50%; }}
                50% {{ background-position: 100% 50%; }}
                100% {{ background-position: 0% 50%; }}
            }}
            
            @keyframes float {{
                0% {{ transform: translateY(0px); }}
                50% {{ transform: translateY(-10px); }}
                100% {{ transform: translateY(0px); }}
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
                    font-size: 2.4rem;
                }}
                
                .character {{
                    padding: 10px 16px;
                }}
            }}
            
            .tier-list-mobile {{
                display: none;
                flex-direction: column;
                gap: 30px;
                margin-bottom: 40px;
            }}
            
            .tier-section {{
                background: rgba(40, 37, 60, 0.7);
                border-radius: 20px;
                overflow: hidden;
                box-shadow: var(--card-shadow);
                position: relative;
                z-index: 1;
            }}
            
            .tier-section::before {{
                content: '';
                position: absolute;
                top: 0;
                left: 0;
                right: 0;
                bottom: 0;
                background: radial-gradient(circle at top left, rgba(255,255,255,0.05) 0%, transparent 40%);
                pointer-events: none;
                z-index: -1;
            }}
            
            .tier-header-mobile {{
                padding: 22px 20px;
                font-family: 'Montserrat', sans-serif;
                font-weight: 800;
                font-size: 1.6rem;
                text-align: center;
                color: #121212;
                text-shadow: 0 2px 4px rgba(0, 0, 0, 0.3);
                letter-spacing: 1px;
                box-shadow: 0 4px 10px rgba(0, 0, 0, 0.2);
                position: relative;
                z-index: 2;
            }}
            
            .role-row {{
                padding: 18px;
                border-bottom: 1px solid rgba(255, 255, 255, 0.1);
                background: rgba(30, 27, 50, 0.5);
                backdrop-filter: blur(5px);
            }}
            
            .role-row:last-child {{
                border-bottom: none;
            }}
            
            .role-header {{
                font-family: 'Montserrat', sans-serif;
                font-weight: 700;
                font-size: 1.3rem;
                margin-bottom: 15px;
                color: var(--accent-color);
                display: flex;
                align-items: center;
                gap: 12px;
                letter-spacing: 0.5px;
            }}
            
            .role-header::after {{
                content: '';
                flex-grow: 1;
                height: 2px;
                background: linear-gradient(90deg, var(--accent-color), transparent);
                border-radius: 2px;
            }}
            
            .characters-row {{
                display: flex;
                flex-wrap: wrap;
                gap: 10px;
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
        </style>
    </head>
    <body>
        <div class="container">
            <header>
                <div class="header-content">
                    <h1>Honkai: Star Rail Tier List</h1>
                    <p class="subtitle">Comprehensive character rankings based on community analysis</p>
                    
                    <div class="legend">
                        {"".join(
                            f'<div class="legend-item" style="color: {TIER_COLORS[tier]}">'
                            f'<div class="legend-color" style="background: {TIER_COLORS[tier]}"></div>'
                            f'{tier}'
                            '</div>'
                            for tier in tiers
                        )}
                    </div>
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

        html += f'<tr style="background: linear-gradient(90deg, {TIER_COLORS[tier]}22, transparent);">'
        html += f'<td class="tier-header" style="background: linear-gradient(135deg, {TIER_COLORS[tier]}, {TIER_COLORS[tier]}dd); color: #121212;">{tier}</td>'

        for role in roles:
            html += '<td class="role-column character-cell">'
            if tier in tierlist_data[role] and tierlist_data[role][tier]:
                for char in tierlist_data[role][tier]:
                    icon_filename = get_icon_filename(char["character"])
                    html += f"""
                    <div class="character">
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
            <div class="tier-header-mobile" style="background: linear-gradient(135deg, {TIER_COLORS[tier]}, {TIER_COLORS[tier]}dd);">
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
                    <div class="credits">
                        <i class="fas fa-code"></i>
                        <span>Community-Driven Rankings</span>
                    </div>
                </div>
            </footer>
        </div>
        
        <script>
            // Initialize the page with animations
            document.addEventListener('DOMContentLoaded', function() {{
                // Staggered character animations
                document.querySelectorAll('.character').forEach((char, index) => {{
                    char.style.animationDelay = `${{index * 0.05}}s`;
                    
                    // Add tier-specific glow on hover
                    char.addEventListener('mouseenter', function() {{
                        const tier = this.closest('tr') ? this.closest('tr').querySelector('.tier-header').textContent.trim() : 
                                   this.closest('.tier-section') ? this.closest('.tier-section').querySelector('.tier-header-mobile').textContent.trim() : '';
                        if (tier && TIER_COLORS[tier]) {{
                            this.style.boxShadow = `0 8px 25px ${{TIER_COLORS[tier]}}80`;
                        }}
                    }});
                    
                    char.addEventListener('mouseleave', function() {{
                        this.style.boxShadow = 'var(--card-shadow)';
                    }});
                }});
                
                // Floating animation for legend items
                const legendItems = document.querySelectorAll('.legend-item');
                legendItems.forEach((item, index) => {{
                    item.style.animation = `float 3s ease-in-out ${{index * 0.2}}s infinite`;
                }});
                
                // Add parallax effect
                window.addEventListener('scroll', function() {{
                    const scrollY = window.scrollY;
                    document.querySelector('header').style.backgroundPosition = `center ${{scrollY * 0.4}}px`;
                    document.querySelector('.tier-list').style.backgroundPosition = `center ${{scrollY * 0.3}}px`;
                }});
            }});
            
            // Tier colors for JavaScript
            const TIER_COLORS = {json.dumps(TIER_COLORS)};
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

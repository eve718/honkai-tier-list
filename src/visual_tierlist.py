import json
import os
from datetime import datetime
import shutil

# Configuration
DATASET_PATH = "hsr_dataset.json"
ROLES_PATH = "character_roles.json"
OUTPUT_FILE = "../public/index.html"
COLORS = {
    "S": "#ff7f7f",  # Red
    "A": "#ffbf7f",  # Orange
    "B": "#ffdf7f",  # Yellow
    "C": "#7fff7f",  # Green
    "D": "#7fbfff",  # Blue
}
ROLE_TYPES = ["DPS", "Sub DPS", "Amplifier", "Sustain"]  # Define role types
GITHUB_REPO_URL = "https://github.com/eve718/honkai-tier-list/tree/main"


def sanitize_filename(name):
    """Convert character names to safe filenames"""
    replacements = {
        "•": "_",  # Bullet to underscore
        ":": "-",  # Colon to dash
        "/": "-",  # Slash to dash
        "\\": "-",  # Backslash to dash
        "?": "",  # Remove question marks
        "*": "",  # Remove asterisks
        '"': "",  # Remove quotes
        "<": "",  # Remove less-than
        ">": "",  # Remove greater-than
        "|": "-",  # Pipe to dash
    }
    for char, replacement in replacements.items():
        name = name.replace(char, replacement)
    return name.strip().lower().replace(" ", "_")


def generate_html(tier_lists, game_version, characters_data):
    """Generate a visually appealing HTML tier list with tabbed interface and horizontal roles"""

    # Helper function to generate tooltip content
    def generate_tooltip(char, mode_name):
        char_data = characters_data.get(char, {})
        mode_data = char_data.get(mode_name, {})

        # Extract stats with default values
        usage = mode_data.get("usage", "N/A")
        cycles = mode_data.get("cycles", "N/A")
        score = mode_data.get("score", "N/A")

        # Format stats display based on mode
        if cycles == "Pure Fiction" or "Apocalyptic Shadow":
            stats_display = f"Avg Score: {score}"
        else:
            stats_display = f"Avg Cycles: {cycles}"

        # Format usage percentage
        usage_display = f"Usage: {usage}%" if usage != "N/A" else "Usage: N/A"

        # Escape special characters
        char_escaped = html.escape(char)
        stats_escaped = html.escape(stats_display)
        usage_escaped = html.escape(usage_display)
        version_escaped = html.escape(game_version)

        return f"""
        <div class="tooltip-content">
            <div class="tooltip-header">{char_escaped}</div>
            <div class="tooltip-stats">
                <div>{usage_escaped}</div>
                <div>{stats_escaped}</div>
            </div>
            <div class="tooltip-footer">Version: {version_escaped}</div>
        </div>
        """

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <!-- Add SEO tags -->
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Honkai: Star Rail Tier List {game_version}</title>
    <meta name="description" content="Comprehensive Honkai: Star Rail tier list for {game_version}. Rankings for Memory of Chaos, Pure Fiction, and Apocalyptic Shadow based on community data. Updated weekly.">
    <meta name="keywords" content="honkai star rail, tier list, hsr tier list, memory of chaos, pure fiction, apocalyptic shadow, {game_version}, character rankings">
    
    <!-- Open Graph/Facebook -->
    <meta property="og:title" content="Honkai Star Rail Tier List {game_version}">
    <meta property="og:description" content="Updated tier list rankings for Honkai: Star Rail {game_version}">
    <meta property="og:type" content="website">
    <meta property="og:url" content="https://my-hsr-tierlist.netlify.app">
    <meta property="og:image" content="https://my-hsr-tierlist.netlify.app/images/og-image.jpg">
    
    <!-- Twitter -->
    <meta name="twitter:card" content="summary_large_image">
    <meta name="twitter:title" content="Honkai Star Rail Tier List {game_version}">
    <meta name="twitter:description" content="Updated rankings for Memory of Chaos, Pure Fiction and Apocalyptic Shadow">
    <meta name="twitter:image" content="https://my-hsr-tierlist.netlify.app/images/twitter-card.jpg">
    
    <!-- Favicon links -->
    <link rel="icon" href="favicon.png" type="image/png">
    <link rel="apple-touch-icon" href="favicon.png">
    <!-- Existing stylesheet -->
    <link href="https://fonts.googleapis.com/css2?family=Segoe+UI:wght@400;600&display=swap" rel="stylesheet">
    <style>
        :root {{
            --s-color: {COLORS['S']};
            --a-color: {COLORS['A']};
            --b-color: {COLORS['B']};
            --c-color: {COLORS['C']};
            --d-color: {COLORS['D']};
            --tab-active: #4cc9f0;
            --tab-inactive: #2a2a4e;
            --role-bg: rgba(30, 30, 46, 0.8);
        }}
        * {{
            box-sizing: border-box;
            margin: 0;
            padding: 0;
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
        }}
        body {{
            background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
            color: #e6e6e6;
            padding: 20px;
            line-height: 1.6;
            font-family: 'Segoe UI', sans-serif;
        }}
        .container {{
            max-width: 1400px;
            margin: 0 auto;
        }}
        header {{
            text-align: center;
            padding: 20px 0;
            margin-bottom: 20px;
            border-bottom: 2px solid #4cc9f0;
        }}
        h1 {{
            font-size: 2.5rem;
            color: #4cc9f0;
            margin-bottom: 10px;
            text-shadow: 0 0 10px rgba(76, 201, 240, 0.5);
            font-family: 'Segoe UI', sans-serif;
        }}
        .timestamp {{
            color: #a9a9a9;
            font-size: 0.9rem;
            font-family: 'Segoe UI', sans-serif;
        }}
        
        /* Tab navigation */
        .tabs {{
            display: flex;
            justify-content: center;
            margin-bottom: 20px;
            flex-wrap: wrap;
        }}
        .tab-button {{
            background: var(--tab-inactive);
            border: none;
            color: #e6e6e6;
            padding: 12px 24px;
            margin: 0 5px;
            border-radius: 5px 5px 0 0;
            font-size: 1.1rem;
            cursor: pointer;
            transition: all 0.3s ease;
            font-family: 'Segoe UI', sans-serif;
            font-weight: 400;
        }}
        .tab-button:hover {{
            background: #3a3a6e;
        }}
        .tab-button.active {{
            background: var(--tab-active);
            color: #16213e;
            font-weight: 700;
        }}
        
        /* Tab content */
        .tab-content {{
            display: none;
            background: rgba(30, 30, 46, 0.8);
            border-radius: 10px;
            padding: 20px;
            margin-bottom: 30px;
            box-shadow: 0 4px 20px rgba(0, 0, 0, 0.5);
            width: 95%;
            margin: 0 auto 30px;
        }}
        .tab-content.active {{
            display: block;
        }}
        
        /* Main tier list layout */
        .tier-list-layout {{
            display: flex;
            flex-direction: column;
            gap: 20px;
        }}
        
        /* Header alignment wrapper */
        .headers-wrapper {{
            display: flex;
            gap: 20px;
        }}
        
        /* Spacer for tier labels */
        .label-spacer {{
            width: 60px;
            flex-shrink: 0;
        }}
        
        /* Role headers container */
        .role-headers {{
            flex: 1;
            display: flex;
            gap: 20px;
            margin-bottom: 15px;
        }}
        
        /* Individual role header */
        .role-header {{
            flex: 1;
            text-align: center;
            font-size: 1.4rem;
            color: #4cc9f0;
            padding: 10px;
            border-bottom: 2px solid #4361ee;
            font-family: 'Segoe UI', sans-serif;
            font-weight: 600;
        }}
        
        /* Tier row container */
        .tier-row-container {{
            display: flex;
            gap: 20px;
            min-height: 100px;
            align-items: stretch;
        }}
        
        /* Tier label styling */
        .tier-label {{
            width: 60px;
            display: flex;
            justify-content: center;
            align-items: center;
            font-weight: bold;
            font-size: 2rem;
            text-shadow: 1px 1px 2px rgba(0,0,0,0.5);
            border-radius: 5px;
            font-family: 'Segoe UI', sans-serif;
        }}
        .tier-label-S {{ background-color: var(--s-color); }}
        .tier-label-A {{ background-color: var(--a-color); }}
        .tier-label-B {{ background-color: var(--b-color); }}
        .tier-label-C {{ background-color: var(--c-color); }}
        .tier-label-D {{ background-color: var(--d-color); }}
        
        /* Role containers */
        .role-containers {{
            flex: 1;
            display: flex;
            gap: 20px;
        }}
        
        /* Role container styling */
        .role-container {{
            flex: 1;
            background: var(--role-bg);
            border-radius: 8px;
            padding: 15px;
            box-shadow: 0 3px 10px rgba(0, 0, 0, 0.3);
            display: flex;
            flex-wrap: wrap;
            align-content: flex-start;
            gap: 10px;
        }}
        
        /* Character styling */
        .character {{
            display: flex;
            flex-direction: column;
            align-items: center;
            width: 100px;
            text-align: center;
            position: relative;
        }}
        .character img {{
            width: 60px;
            height: 60px;
            border-radius: 50%;
            object-fit: cover;
            border: 2px solid #4cc9f0;
            background: #2a2a4e;
            transition: transform 0.3s ease;
        }}
        .character:hover img {{
            transform: scale(1.1);
        }}
        .character span {{
            font-size: 0.9rem;
            overflow: hidden;
            text-overflow: ellipsis;
            white-space: nowrap;
            display: block;
            width: 100%;
            font-family: 'Segoe UI', sans-serif;
            margin-top: 5px;
        }}
        
        /* Character tooltip */
        .character .tooltip {{
            max-width: 220px; /* Slightly wider for stats */
            padding: 8px;
            text-align: left;
        }}
        .tooltip-content {{
            display: flex;
            flex-direction: column;
            gap: 4px;
        }}
        .tooltip-header {{
            font-weight: bold;
            font-size: 1.1rem;
            border-bottom: 1px solid #4cc9f0;
            padding-bottom: 4px;
            margin-bottom: 4px;
        }}
        .tooltip-stats {{
            font-size: 0.9rem;
            line-height: 1.4;
        }}
        .tooltip-footer {{
            font-size: 0.8rem;
            color: #a9a9a9;
            font-style: italic;
            margin-top: 4px;
        }}
        .character:hover .tooltip {{
            visibility: visible;
            opacity: 1;
        }}
        .character .tooltip::after {{
            content: "";
            position: absolute;
            top: 100%;
            left: 50%;
            margin-left: -5px;
            border-width: 5px;
            border-style: solid;
            border-color: rgba(0, 0, 0, 0.85) transparent transparent transparent;
        }}
        
        footer {{
            text-align: center;
            margin-top: 20px;
            padding: 20px;
            color: #a9a9a9;
            font-size: 0.9rem;
            border-top: 1px solid #4cc9f0;
            font-family: 'Segoe UI', sans-serif;
        }}
        
        @media (max-width: 1200px) {{
            .tier-row-container {{
                flex-direction: column;
            }}
            .tier-label {{
                width: 100%;
                height: 50px;
            }}
            .role-containers {{
                flex-direction: column;
            }}
            .headers-wrapper {{
                flex-direction: column;
            }}
            .label-spacer {{
                display: none;
            }}
            .role-headers {{
                flex-wrap: wrap;
                justify-content: center;
            }}
            .role-header {{
                flex: none;
                width: calc(50% - 10px);
            }}
        }}
        @media (max-width: 768px) {{
            .tabs {{
                flex-direction: column;
                align-items: center;
            }}
            .tab-button {{
                width: 100%;
                margin: 5px 0;
                border-radius: 5px;
            }}
            .character {{
                max-width: 100px;
            }}
            .character span {{
                font-size: 0.8rem;
            }}
            .role-header {{
                width: 100%;
                font-size: 1.2rem;
            }}
        }}
    </style>
</head>
<body>
    <div class="container">
        <header>
            <h1>Honkai: Star Rail Tier List</h1>
            <div class="timestamp">
                Based on game version {game_version} | Generated on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
            </div>
        </header>
        
        <div class="tabs">
            <button class="tab-button active" data-tab="moc">Memory of Chaos</button>
            <button class="tab-button" data-tab="pf">Pure Fiction</button>
            <button class="tab-button" data-tab="as">Apocalyptic Shadow</button>
            <button class="tab-button" data-tab="general">General Tier List</button>
        </div>
"""

    # Add tier lists for each game mode as tab content
    tab_ids = {
        "Memory of Chaos": "moc",
        "Pure Fiction": "pf",
        "Apocalyptic Shadow": "as",
        "General Tier List": "general",
    }

    for mode, role_data in tier_lists.items():
        tab_id = tab_ids.get(mode)
        if not tab_id:
            continue

        html += f"""
        <div id="{tab_id}" class="tab-content{' active' if tab_id == 'moc' else ''}">
            <h2 class="mode-header" style="text-align: center; margin-bottom: 20px;">{mode}</h2>
            
            <div class="tier-list-layout">
                <!-- Role headers with proper alignment -->
                <div class="headers-wrapper">
                    <div class="label-spacer"></div>
                    <div class="role-headers">
                        {"".join([f'<div class="role-header">{role}</div>' for role in ROLE_TYPES])}
                    </div>
                </div>
                
                <!-- S Tier -->
                <div class="tier-row-container">
                    <div class="tier-label tier-label-S">S</div>
                    <div class="role-containers">
                        {"".join([f'<div class="role-container">' + 
                            ''.join([f'<div class="character">' +
                            f'<img src="images/{sanitize_filename(char)}_icon.png" alt="{char} Honkai Star Rail character - Tier S">' +
                            f'<span class="tooltip">{generate_tooltip(char, mode)}</span>' +
                            f'<span>{char}</span></div>' 
                            for char in role_data.get(role, {}).get('S', [])]) + 
                            '</div>' 
                        for role in ROLE_TYPES])}
                    </div>
                </div>
                
                <!-- A Tier -->
                <div class="tier-row-container">
                    <div class="tier-label tier-label-A">A</div>
                    <div class="role-containers">
                        {"".join([f'<div class="role-container">' + 
                            ''.join([f'<div class="character">' +
                            f'<img src="images/{sanitize_filename(char)}_icon.png" alt="{char} Honkai Star Rail character - Tier A">' +
                            f'<span class="tooltip">{generate_tooltip(char, mode)}</span>' +
                            f'<span>{char}</span></div>' 
                            for char in role_data.get(role, {}).get('A', [])]) + 
                            '</div>' 
                        for role in ROLE_TYPES])}
                    </div>
                </div>
                
                <!-- B Tier -->
                <div class="tier-row-container">
                    <div class="tier-label tier-label-B">B</div>
                    <div class="role-containers">
                        {"".join([f'<div class="role-container">' + 
                            ''.join([f'<div class="character">' +
                            f'<img src="images/{sanitize_filename(char)}_icon.png" alt="{char} Honkai Star Rail character - Tier B">' +
                            f'<span class="tooltip">{generate_tooltip(char, mode)}</span>' +
                            f'<span>{char}</span></div>' 
                            for char in role_data.get(role, {}).get('B', [])]) + 
                            '</div>' 
                        for role in ROLE_TYPES])}
                    </div>
                </div>
                
                <!-- C Tier -->
                <div class="tier-row-container">
                    <div class="tier-label tier-label-C">C</div>
                    <div class="role-containers">
                        {"".join([f'<div class="role-container">' + 
                            ''.join([f'<div class="character">' +
                            f'<img src="images/{sanitize_filename(char)}_icon.png" alt="{char} Honkai Star Rail character - Tier C">' +
                            f'<span class="tooltip">{generate_tooltip(char, mode)}</span>' +
                            f'<span>{char}</span></div>' 
                            for char in role_data.get(role, {}).get('C', [])]) + 
                            '</div>' 
                        for role in ROLE_TYPES])}
                    </div>
                </div>
                
                <!-- D Tier -->
                <div class="tier-row-container">
                    <div class="tier-label tier-label-D">D</div>
                    <div class="role-containers">
                        {"".join([f'<div class="role-container">' + 
                            ''.join([f'<div class="character">' +
                            f'<img src="images/{sanitize_filename(char)}_icon.png" alt="{char} Honkai Star Rail character - Tier D">' +
                            f'<span class="tooltip">{generate_tooltip(char, mode)}</span>' +
                            f'<span>{char}</span></div>' 
                            for char in role_data.get(role, {}).get('D', [])]) + 
                            '</div>' 
                        for role in ROLE_TYPES])}
                    </div>
                </div>
            </div>
        </div>
"""

    html += f"""
            <footer>
                <p>Created with Honkai Star Rail Tier List Generator | Data updated weekly</p>
                <p>
                    <a href="{GITHUB_REPO_URL}" target="_blank" style="color: #4cc9f0; text-decoration: none; display: inline-flex; align-items: center; gap: 5px;">
                        <svg width="20" height="20" viewBox="0 0 24 24" fill="currentColor">
                            <path d="M12 .297c-6.63 0-12 5.373-12 12 0 5.303 3.438 9.8 8.205 11.385.6.113.82-.258.82-.577 0-.285-.01-1.04-.015-2.04-3.338.724-4.042-1.61-4.042-1.61C4.422 18.07 3.633 17.7 3.633 17.7c-1.087-.744.084-.729.084-.729 1.205.084 1.838 1.236 1.838 1.236 1.07 1.835 2.809 1.305 3.495.998.108-.776.417-1.305.76-1.605-2.665-.3-5.466-1.332-5.466-5.93 0-1.31.465-2.38 1.235-3.22-.135-.303-.54-1.523.105-3.176 0 0 1.005-.322 3.3 1.23.96-.267 1.98-.399 3-.405 1.02.006 2.04.138 3 .405 2.28-1.552 3.285-1.23 3.285-1.23.645 1.653.24 2.873.12 3.176.765.84 1.23 1.91 1.23 3.22 0 4.61-2.805 5.625-5.475 5.92.42.36.81 1.096.81 2.22 0 1.606-.015 2.896-.015 3.286 0 .315.21.69.825.57C20.565 22.092 24 17.592 24 12.297c0-6.627-5.373-12-12-12"/>
                        </svg>
                        View on GitHub
                    </a>
                </p>
            </footer>
    </div>
    
    <script>
        // Tab switching functionality
        document.querySelectorAll('.tab-button').forEach(button => {{
            button.addEventListener('click', () => {{
                // Remove active class from all buttons and content
                document.querySelectorAll('.tab-button').forEach(btn => btn.classList.remove('active'));
                document.querySelectorAll('.tab-content').forEach(content => content.classList.remove('active'));
                
                // Add active class to clicked button
                button.classList.add('active');
                
                // Show corresponding content
                const tabId = button.getAttribute('data-tab');
                document.getElementById(tabId).classList.add('active');
            }});
        }});
        document.querySelectorAll('img').forEach(img => {{
            img.onerror = () => {{
            img.alt = "Image missing!";
            img.style.border = "2px dashed red";
            }};
        }});
    </script>
</body>
</html>
"""

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        f.write(html)
    print(f"Visual tier list saved to {OUTPUT_FILE}")


if __name__ == "__main__":
    # Load dataset
    try:
        with open(DATASET_PATH) as f:
            data = json.load(f)
    except FileNotFoundError:
        print(f"Error: Dataset file {DATASET_PATH} not found!")
        print("Please run update_data.py first to create a dataset.")
        exit(1)

    # Extract game version
    game_version = data.get("version", "Unknown")
    characters_data = data.get("characters", {})

    # Load role definitions
    try:
        with open(ROLES_PATH) as f:
            role_data = json.load(f)
    except FileNotFoundError:
        print(f"Error: Role file {ROLES_PATH} not found!")
        exit(1)

    # Calculate scores (using your existing function from tierlist.py)
    from tierlist import calculate_scores, generate_role_based_tier_lists

    scores = calculate_scores(characters_data)
    tier_lists = generate_role_based_tier_lists(characters_data, scores)

    # Generate the visual tier list
    generate_html(tier_lists, game_version, characters_data)

    # Copy favicon to public directory
    script_dir = os.path.dirname(os.path.abspath(__file__))
    favicon_src = os.path.join(script_dir, "favicon.png")
    favicon_dest = os.path.join(script_dir, "../public/favicon.png")

    if os.path.exists(favicon_src):
        shutil.copy2(favicon_src, favicon_dest)
        print(f"Copied favicon.png to public directory")
    else:
        print(f"Warning: favicon.png not found at {favicon_src}")

    # Add this after generating HTML in visual_tierlist.py
    SITEMAP = """<?xml version="1.0" encoding="UTF-8"?>
    <urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
        <url>
            <loc>https://my-hsr-tierlist.netlify.app/</loc>
            <lastmod>{date}</lastmod>
            <changefreq>weekly</changefreq>
            <priority>1.0</priority>
        </url>
    </urlset>
    """.format(
        date=datetime.now().strftime("%Y-%m-%d")
    )

    with open("../public/sitemap.xml", "w") as f:
        f.write(SITEMAP)

    # Add this to your script
    with open("../public/robots.txt", "w") as f:
        f.write(
            "User-agent: *\nAllow: /\n\nSitemap: https://my-hsr-tierlist.netlify.app/sitemap.xml"
        )

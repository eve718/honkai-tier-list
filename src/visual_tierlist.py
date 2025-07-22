import json
import os
from datetime import datetime

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
GITHUB_REPO_URL = "https://github.com/eve718/honkai-tier-list/tree/main/src"


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


def generate_html(tier_lists):
    """Generate a visually appealing HTML tier list with tabbed interface and horizontal roles"""
    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Honkai: Star Rail Tier List</title>
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
            visibility: hidden;
            position: absolute;
            bottom: calc(100% + 8px);
            left: 50%;
            transform: translateX(-50%);
            background-color: rgba(0, 0, 0, 0.85);
            color: #fff;
            text-align: center;
            padding: 6px 12px;
            border-radius: 4px;
            z-index: 100;
            /* Remove text constraints to show full name */
            white-space: normal;
            max-width: 200px;
            word-wrap: break-word;
            opacity: 0;
            transition: opacity 0.3s ease;
            pointer-events: none;
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
            <div class="timestamp">Generated on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</div>
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
                            f'<img src="images/{sanitize_filename(char)}_icon.png" alt="{char}">' +
                            f'<span class="tooltip">{char}</span>' +
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
                            f'<img src="images/{sanitize_filename(char)}_icon.png" alt="{char}">' +
                            f'<span class="tooltip">{char}</span>' +
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
                            f'<img src="images/{sanitize_filename(char)}_icon.png" alt="{char}">' +
                            f'<span class="tooltip">{char}</span>' +
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
                            f'<img src="images/{sanitize_filename(char)}_icon.png" alt="{char}">' +
                            f'<span class="tooltip">{char}</span>' +
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
                            f'<img src="images/{sanitize_filename(char)}_icon.png" alt="{char}">' +
                            f'<span class="tooltip">{char}</span>' +
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
            <p>View source on <a href="{GITHUB_REPO_URL}" target="_blank" style="color: #4cc9f0; text-decoration: none;">GitHub</a></p>
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

    # Load role definitions
    try:
        with open(ROLES_PATH) as f:
            role_data = json.load(f)
    except FileNotFoundError:
        print(f"Error: Role file {ROLES_PATH} not found!")
        exit(1)

    # Calculate scores (using your existing function from tierlist.py)
    from tierlist import calculate_scores, generate_role_based_tier_lists

    scores = calculate_scores(data)
    tier_lists = generate_role_based_tier_lists(data, scores)

    # Generate the visual tier list
    generate_html(tier_lists)

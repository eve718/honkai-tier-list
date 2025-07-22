#!/bin/sh

# Install dependencies
pip install -r requirements.txt

# Run scripts
cd src
python update_data.py
python visual_tierlist.py

# Move files to public directory
cp index.html ../public/
cp -r images ../public/

echo "Build complete!"
#!/bin/sh

# Install dependencies
pip install -r requirements.txt

# Run scripts
cd src
python tierlist.py

# Move files to public directory
cp index.html ../public/
cp -r icons ../public/

echo "Build complete!"
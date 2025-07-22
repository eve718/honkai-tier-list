#!/bin/bash

# Install Python dependencies
pip install -r requirements.txt

# Run update and generation scripts
cd src
python update_data.py
python visual_tierlist.py

# Move generated files to public directory
mv index.html ../public/
cp -r images ../public/
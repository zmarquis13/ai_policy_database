#!/bin/bash
set -e

# Change to the correct directory
cd /webapps/project_dir/ai_policy_database/private/govinfo

# Activate virtual environment
source /webapps/project_dir/env/bin/activate

# Run the Python script
python update_list_and_download.py

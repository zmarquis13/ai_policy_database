#!/bin/bash
set -e

source /webapps/project_dir/env/bin/activate
cd /webapps/project_dir/ai_policy_database/private/govinfo
python get_text.py

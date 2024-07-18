#!/bin/bash
set -e

source /webapps/project_dir/env/bin/activate
cd /webapps/project_dir/ai_policy_database/private/site/billscraper
python manage.py llm_analysis
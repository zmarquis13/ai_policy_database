#uses an llm (gpt4o-mini) to analyze bills and classify them into categories and sectors

import os
import json
import io
import re

from tqdm import tqdm

from django.core.management.base import BaseCommand, CommandError
from search.models import Bill

import openai

from dotenv import load_dotenv

load_dotenv()

client = openai.OpenAI(api_key = os.environ.get('OPENAI_API_KEY'))

SUMMARY_PROMPT = """Please summarize the following bill in 20-30 words based on its text. Summarize what the bill does generally and what the point of the bil is.
"""

#current directory: private/site/billscraper/search/management/commands

def summarize_all_items():
    #filters on time
    content_list = Bill.objects.filter(status_date__gte='2024-07-01')
    #content_list = content_list.filter(status_date__gte='2024-05-01')

    items_classified = 0

    #private/site/billscraper/search/management/analyses
    #summaries_directory_path = 'summaries'

    #if not os.path.exists(summaries_directory_path):
    #    os.makedirs(summaries_directory_path)

    for bill in tqdm(content_list):
        #check to see if it's already been analyzed
        if bill.summary == 'N/A':

            summary = gpt_summary(bill)

            bill.summary = summary

            bill.save()

            items_classified += 1

    return items_classified

def gpt_summary(bill):
    #feed title, description, and first 20,000 chars of text
    if bill.summary != "N/A":
        bill_content = f"Title: {bill.title}\n Description: {bill.description}\n Text: {bill.text[:20000]}"
    else:
        bill_content = f"Title: {bill.title}\n Text: {bill.text[:20000]}"

    response = client.chat.completions.create(
    model="gpt-4o-mini",
    #response_format={ "type": "json_object" },
    messages=[
        {"role": "system", "content": SUMMARY_PROMPT},
        {"role": "user", "content": bill_content}
    ]
    )
    summary = response.choices[0].message.content
    return summary


class Command(BaseCommand):
    help = "Uses chatgpt to summarize items"

    def handle(self, *args, **options):

        items_summarized = summarize_all_items()

        self.stdout.write(self.style.SUCCESS(f'Database updated successfully ({items_summarized} items summarized)'))

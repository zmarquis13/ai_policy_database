# for each item, gets all points in the text where a keyword shows up and adds it to the keyword_instances list for that item

import re
from tqdm import tqdm

from django.core.management.base import BaseCommand, CommandError
from search.models import Bill

#list of keywords, need to change here if modified
KEYWORDS = [
    "artificial intelligence", 
    "machine learning", 
    "neural network", 
    "deep learning",
    "automated",
    "deepfake",
    "deep fake",
    "synthetic media",
    "large language model",
    "foundation model",
    "chatbot",
    "recommendation system",
    "autonomous vehicle",
    "algorithm"
]

#adds counts and total
def add_keyword_contexts():

    all_bills = Bill.objects.all()

    for bill in tqdm(all_bills):
        #check to see if instances have already been added
        if (not bill.keyword_instances):

            contexts = []
            text = bill.text

            for keyword in KEYWORDS:
                # Use regular expressions to find keyword occurrences
                keyword_pattern = r'\b{}\b'.format(re.escape(keyword))
                matches = re.finditer(keyword_pattern, text)

                for match in matches:
                    #show up to 100 chars before and 200 chars after
                    start_index = max(0, match.start() - 100)
                    end_index = min(len(text), match.end() + 200)
                    context = text[start_index:end_index]

                    # Split into words to ensure maximum 75 words
                    words = context.split()
                    if len(words) > 75:
                        context = ' '.join(words[:75])
                
                    contexts.append(context)

            bill.keyword_instances = contexts
            bill.save()
        
    items_updated = all_bills.count()
    return items_updated


#actual command itself (called with python manage.py add_keyword_instances)
class Command(BaseCommand):
    help = "Updates the keyword listings for all items in the database"

    def handle(self, *args, **options):

        #remove items to database and count total
        items_updated = add_keyword_contexts()

        #print out the number of items added
        self.stdout.write(self.style.SUCCESS(f'Database keyword listings updated successfully ({items_updated} items updated)'))

       

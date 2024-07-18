# re-counts the keywords for every item in the database
# (useful if keywords are added/removed)

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

#count the specific keywords and the total number
def count_keywords(text):
    keyword_counts = {keyword: 0 for keyword in KEYWORDS}
    total_keywords = 0

    for keyword in KEYWORDS:
        pattern = r'\b' + re.escape(keyword) + r'\b'
        count = len(re.findall(pattern, text.lower()))
        total_keywords += count
        keyword_counts[keyword] = count
    
    return keyword_counts, total_keywords

#adds counts and total
def add_keywords():

    all_bills = Bill.objects.all()

    for bill in tqdm(all_bills):
        keyword_counts, total_keywords = count_keywords(bill.text)
        bill.keyword_artificial_intelligence = keyword_counts['artificial intelligence']
        bill.keyword_machine_learning = keyword_counts['machine learning']
        bill.keyword_algorithm = keyword_counts['algorithm']
        bill.keyword_neural_network = keyword_counts['neural network']
        bill.keyword_deep_learning = keyword_counts['deep learning']
        bill.keyword_automated = keyword_counts['automated']
        bill.keyword_deepfake = keyword_counts['deepfake'] + keyword_counts['deep fake']
        bill.keyword_synthetic_media = keyword_counts['synthetic media']
        bill.keyword_large_language_model = keyword_counts['large language model']
        bill.keyword_foundation_model = keyword_counts['foundation model']
        bill.keyword_chatbot = keyword_counts['chatbot']
        bill.keyword_recommendation_system = keyword_counts['recommendation system']
        bill.keyword_autonomous_vehicle = keyword_counts['autonomous vehicle']
        bill.total_keywords = total_keywords
        bill.save()

    
    items_updated = all_bills.count()
    return items_updated


#actual command itself (called with python manage.py populate_db)
class Command(BaseCommand):
    help = "Updates the keyword counts for all items in the database"

    def handle(self, *args, **options):

        #remove items to database and count total
        items_updated = add_keywords()

        #print out the number of items added
        self.stdout.write(self.style.SUCCESS(f'Database keywords updated successfully ({items_updated} items updated)'))

       

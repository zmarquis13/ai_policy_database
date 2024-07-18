# removes all items with no keywords from the database

import os
import json
import io
import re

from tqdm import tqdm

from django.core.management.base import BaseCommand, CommandError
from search.models import Bill


#adds all content from legiscan
def remove_irrelevant_items():

    irrelevant_items = Bill.objects.filter(total_keywords=0)
    items_removed = irrelevant_items.count()

    for bill in tqdm(irrelevant_items):
        bill.delete()
    
    return items_removed


#actual command itself (called with python manage.py remove_irrelevant)
class Command(BaseCommand):
    help = "Removes all irrelevant from the database"

    def handle(self, *args, **options):

        user_input = input("Are you sure you want to remove all items with no keywords from the database? (y/n) ")

        if (user_input == 'y'):

            #remove items to database and count total
            items_removed = remove_irrelevant_items()

            #print out the number of items added
            self.stdout.write(self.style.SUCCESS(f'Database updated successfully ({items_removed} items removed)'))

        else:
            self.stdout.write('Operation canceled')

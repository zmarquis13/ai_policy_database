#removes all legislation from the database

import os
import json
import io
import re

from tqdm import tqdm

from django.core.management.base import BaseCommand, CommandError
from search.models import Bill


#adds all content from legiscan
def remove_all_legislation():

    legislation = Bill.objects.filter(content_collection='Legislation')
    items_removed = legislation.count()

    for bill in tqdm(legislation):
        bill.delete()
    
    return items_removed


#actual command itself (called with python manage.py populate_db)
class Command(BaseCommand):
    help = "Removes all legislation from the database"

    def handle(self, *args, **options):

        user_input = input("Are you sure you want to remove all legislation from the database? (y/n) ")

        if (user_input == 'y'):

            #remove items to database and count total
            items_removed = remove_all_legislation()

            #print out the number of items added
            self.stdout.write(self.style.SUCCESS(f'Database updated successfully ({items_removed} items removed)'))

        else:
            self.stdout.write('Operation canceled')

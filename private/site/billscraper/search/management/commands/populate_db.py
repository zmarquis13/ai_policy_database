# adds legislation and federal documents from legiscan and govinfo to the database

import os
import json
import io
import re

from django.core.management.base import BaseCommand, CommandError
from psycopg.errors import UniqueViolation
from django.db import IntegrityError
from search.models import Bill

from tqdm import tqdm

import base64
from bs4 import BeautifulSoup

import PyPDF2
from PyPDF2 import PdfReader
from PyPDF2.errors import PdfReadError

from django.db.utils import DataError

#govinfo returns collection codes, used to convert to full name
COLLECTION_CODES = {
    'BILLS': 'Congressional Bills',
    'BILLSTATUS': 'Congressional Bill Status',
    'BILLSUM': 'Congressional Bill Summaries',
    'BUDGET': 'United States Budget',
    'CCAL': 'Congressional Calendars',
    'CDIR': 'Congressional Directory',
    'CDOC': 'Congressional Documents',
    'CFR': 'Code of Federal Regulations',
    'CHRG': 'Congressional Hearings',
    'CMR': 'Congressionally Mandated Reports',
    'COMPS': 'Statutes Compilations',
    'CPD': 'Compilation of Presidential Documents',
    'CPRT': 'Congressional Committee Prints',
    'CREC': 'Congressional Record',
    'CRECB': 'Congressional Record (Bound Edition)',
    'CRI': 'Congressional Record Index',
    'CRPT': 'Congressional Reports',
    'CZIC': 'Coastal Zone Information Center',
    'ECFR': 'Electronic Code of Federal Regulations',
    'ECONI': 'Economic Indicators',
    'ERIC': 'Education Reports from ERIC',
    'ERP': 'Economic Report of the President',
    'FR': 'Federal Register',
    'GAOREPORTS': 'Government Accountability Office Reports and Comptroller General Decisions',
    'GOVMAN': 'United States Government Manual',
    'GOVPUB': 'Bulk Submission',
    'GPO': 'Additional Government Publications',
    'HJOURNAL': 'Journal of the House of Representatives',
    'HMAN': 'House Rules and Manual',
    'HOB': 'History of Bills',
    'LSA': 'List of CFR Sections Affected',
    'PAI': 'Privacy Act Issuances',
    'PLAW': 'Public and Private Laws',
    'PPP': 'Public Papers of the Presidents of the United States',
    'SERIALSET': 'Congressional Serial Set',
    'SJOURNAL': 'Journal of the Senate',
    'SMAN': 'Senate Manual',
    'STATUTE': 'Statutes at Large',
    'USCODE': 'United States Code',
    'USCOURTS': 'United States Courts Opinions'
}

#legiscan returns state codes, used to convert to full name
STATES = {
    'US': "Federal",
    'AL': "Alabama",
    'AK': "Alaska",
    'AZ': "Arizona",
    'AR': "Arkansas",
    'CA': "California",
    'CO': "Colorado",
    'CT': "Connecticut",
    'DE': "Delaware",
    'DC': "District of Columbia",
    'FL': "Florida",
    'GA': "Georgia",
    'HI': "Hawaii",
    'ID': "Idaho",
    'IL': "Illinois",
    'IN': "Indiana",
    'IA': "Iowa",
    'KS': "Kansas",
    'KY': "Kentucky",
    'LA': "Louisiana",
    'ME': "Maine",
    'MD': "Maryland",   
    'MA': "Massachusetts",
    'MI': "Michigan",
    'MN': "Minnesota",
    'MS': "Mississippi",
    'MO': "Missouri",
    'MT': "Montana",
    'NE': "Nebraska",
    'NV': "Nevada",
    'NH': "New Hampshire",
    'NJ': "New Jersey",
    'NM': "New Mexico",
    'NY': "New York",
    'NC': "North Carolina",
    'ND': "North Dakota",
    'OH': "Ohio",
    'OK': "Oklahoma",
    'OR': "Oregon",
    'PA': "Pennsylvania",
    'RI': "Rhode Island",
    'SC': "South Carolina",
    'SD': "South Dakota",
    'TN': "Tennessee",
    'TX': "Texas",
    'UT': "Utah",
    'VT': "Vermont",
    'VA': "Virginia",
    'WA': "Washington",
    'WV': "West Virginia",
    'WI': "Wisconsin",
    'WY': "Wyoming",
}

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

#processes and returns given text after base64 decoding (used with legiscan docs)
def extract_text_from_html(html_content):
    soup = BeautifulSoup(html_content, 'html.parser')
    
    # Kill all script and style elements
    for script in soup(["script", "style"]):
        script.extract()  # Remove these tags from the soup
    
    # Get text
    text = soup.get_text()
    
    # Break into lines and remove leading and trailing spaces
    lines = (line.strip() for line in text.splitlines())
    
    # Break multi-headlines into a line each
    chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
    
    # Drop blank lines
    text = '\n'.join(chunk for chunk in chunks if chunk)
    
    return text

#returns text from a pdf
def extract_text_from_pdf_bytes(pdf_bytes):
    # Use an in-memory binary stream to interface with PyPDF2
    buffer = io.BytesIO(pdf_bytes)
    
    # Create a PDF reader object
    pdf_reader = PyPDF2.PdfReader(buffer)
    
    # Check if the PDF is encrypted
    if pdf_reader.is_encrypted:
        # If the PDF is encrypted, then try decrypting it (with no password)
        try:
            pdf_reader.decrypt('')
        except:
            return "The PDF is encrypted and couldn't be decrypted."
    
    # Extract text from each page
    text = ""
    for page_num in range(len(pdf_reader.pages)):
        page = pdf_reader.pages[page_num]
        text += page.extract_text()
        
    return text

#decode base64 encoding in a json file (used with legiscan text files)
def extract_zip_from_json(json_file):
    # 1. Load the JSON file
    with open(json_file, 'r') as f:
        data = json.load(f)

    # 2. Extract the "zip" key from the JSON data
    zip_base64 = data.get('text', {}).get('doc')
    if not zip_base64:
        print("No 'zip' key found in the JSON file.")
        return

    # 3. Decode the Base64 string
    zip_bytes = base64.b64decode(zip_base64)

    return extract_text_from_html(zip_bytes)

#gets the keyword counts for a given piece of text
def keywords_from_bill_text(bill_text):
    keyword_counts = {keyword: 0 for keyword in KEYWORDS}
    total_keywords = 0

    for keyword in KEYWORDS:
        pattern = r'\b' + re.escape(keyword) + r'\b'
        count = len(re.findall(pattern, bill_text.lower()))
        total_keywords += count
        keyword_counts[keyword] = count
    
    return keyword_counts, total_keywords

#gets the text snippets for each keyword occurrence in a given text and returns them as a list of strings
def get_keyword_instances(bill_text):

    contexts = []

    for keyword in KEYWORDS:
                # Use regular expressions to find keyword occurrences
                keyword_pattern = r'\b{}\b'.format(re.escape(keyword))
                matches = re.finditer(keyword_pattern, bill_text)

                for match in matches:
                    #show up to 100 chars before and 200 chars after
                    start_index = max(0, match.start() - 100)
                    end_index = min(len(bill_text), match.end() + 200)
                    context = bill_text[start_index:end_index]

                    # Split into words to ensure maximum 75 words
                    words = context.split()
                    if len(words) > 75:
                        context = ' '.join(words[:75])
                
                    contexts.append(context)

    return contexts

#adds all content downloaded from govinfo 
def add_federal_documents():
    #count number of items added
    items_added = 0
    items_not_added = 0

    #path to govinfo directory
    abs_file_path = os.path.join(os.path.abspath(''), '..', '..', 'govinfo')

    #list of content
    bill_file = open(abs_file_path + '/content_list.json')

    data = json.load(bill_file)

    # Keep track of items to remove
    items_to_remove = []

    print("Adding federal documents")

    #process each item in content_list (stored as a 'results' list in the file)
    for item in tqdm(data.get('results', [])):
        
        #get the last collection listed
        collection_string = item['collectionCode']
        parts = collection_string.split(';')
        type_code = parts[-1]

        #check to see if something already exists in the same collection with the same title and issue date (avoids duplicates)
        if not Bill.objects.filter(content_collection=COLLECTION_CODES[type_code], title=item.get('title'), status_date=item['dateIssued']).exists():
            #find associated txt or pdf file
            if item.get('download', {}).get('txtLink'):
                if item['granuleId']:
                    text_file_path = os.path.join(abs_file_path, 'txt_files', (item['granuleId'] + '.txt'))
                elif item['packageId']:
                    text_file_path = os.path.join(abs_file_path, 'txt_files', (item['packageId'] + '.txt'))
            elif item.get('download', {}).get('pdfLink'):
                if item['granuleId']:
                    text_file_path = os.path.join(abs_file_path, 'pdf_files', (item['granuleId'] + '.pdf'))
                elif item['packageId']:
                    text_file_path = os.path.join(abs_file_path, 'pdf_files', (item['packageId'] + '.pdf'))
            else:
                bill_text = "No text available"
            
            try:
                if text_file_path.endswith('.txt'):
                    #open txt file
                    with open(text_file_path, 'r', encoding='utf-8') as file:
                        bill_text = file.read()
                elif text_file_path.endswith('.pdf'):
                    #try to open pdf
                    try:
                        reader = PdfReader(text_file_path)
                        bill_text = ""
                        for page in reader.pages:
                           bill_text += page.extract_text()
                    except PdfReadError:
                        print("Error reading pdf file")
                        bill_text = "Text file not found"
                else:
                    bill_text = "No text available"
            #remove item if its file can't be found
            #note: makes running get_text first very important
            except FileNotFoundError:
                #data['results'].remove(item)
                continue

            #gets map of keyword:count pairs and the total number
            keyword_counts, keyword_total = keywords_from_bill_text(bill_text)
            
            #check to make sure the bill actually has keywords
            if keyword_total > 0:

                #url is related to packageId and granuleId if one exists
                bill_url = 'https://govinfo.gov/app/details/'
                bill_url += item['packageId']
                if item['granuleId']: bill_url += '/' + item['granuleId']
                bill_url += '/summary'

                #create object
                b = Bill(
                    title = item.get('title'),
                    status_date = item.get('dateIssued'),
                    status = 'Issued',
                    state = 'Federal',
                    url = bill_url,
                    text = bill_text,
                    content_collection = COLLECTION_CODES[type_code],
                    source = item['governmentAuthor'][-1],

                    keyword_artificial_intelligence = keyword_counts['artificial intelligence'],
                    keyword_machine_learning = keyword_counts['machine learning'],
                    keyword_algorithm = keyword_counts['algorithm'],
                    keyword_neural_network = keyword_counts['neural network'],
                    keyword_deep_learning = keyword_counts['deep learning'],
                    keyword_automated = keyword_counts['automated'],
                    keyword_deepfake = keyword_counts['deepfake'] + keyword_counts['deep fake'],
                    keyword_synthetic_media = keyword_counts['synthetic media'],
                    keyword_large_language_model = keyword_counts['large language model'],
                    keyword_foundation_model = keyword_counts['foundation model'],
                    keyword_chatbot = keyword_counts['chatbot'],
                    keyword_recommendation_system = keyword_counts['recommendation system'],
                    keyword_autonomous_vehicle = keyword_counts['autonomous vehicle'],
                    total_keywords = keyword_total,
                    keyword_instances = get_keyword_instances(bill_text)
                )
                
                #try to add bill, catch DataErrors (one item had a null error so this avoids that)
                try:
                    b.save()
                    items_added += 1
                except DataError:
                    pass
            #if bill doesn't have any keywords, remove it from the list and delete its text file to avoid repeated checking of the same thing
            else:
                items_not_added += 1
                '''
                # Add the item to the removal list
                items_to_remove.append(item)

                # Delete the associated text file
                if os.path.exists(text_file_path):
                    os.remove(text_file_path)

    # After the loop, remove the invalid items from the original data
    for item in items_to_remove:
        data['results'].remove(item)

    # Save the updated data back to the JSON file
    with open(abs_file_path + '/content_list.json', 'w') as bill_file:
        json.dump(data, bill_file, indent=4)
    '''

    #return the number of items added
    return items_added, items_not_added


def add_bill(data):

    state_string = data.get('bill', {}).get('state')

    #cut title to 300 chars if longer
    bill_title = data.get('bill', {}).get('title')
    if len(bill_title) > 300:
        bill_title = bill_title[:297] + '...'

    #cut description to 500 chars if longer
    bill_description = data.get('bill', {}).get('description')
    if len(bill_description) > 500:
        bill_description = bill_description[:497] + '...'

    bill_status_date = data.get('bill', {}).get('status_date')

    action_date = data.get('bill', {}).get('history', {})[-1].get('date')
    
    action = data.get('bill', {}).get('history', {})[-1].get('action')

    bill_text = get_bill_text(data)

    #gets map of keyword:count pairs and the total number
    keyword_counts, keyword_total = keywords_from_bill_text(bill_text)

    #check to make sure the bill actually has keywords
    if keyword_total > 0:

        statuses = ["Other", "Introduced", "Engrossed", "Enrolled", "Passed", "Vetoed"]

        bill_status = "N/A"

        if data.get('bill', {}).get('status') > 5 or data.get('bill', {}).get('status') < 1:
            bill_status = "Other"
        else: 
            bill_status = statuses[data.get('bill', {}).get('status')]
        
        num_sponsors = len(data.get('bill', {}).get('sponsors', {}))
        
        main_sponsor = "N/A"

        if num_sponsors != 0:
            main_sponsor = data.get('bill', {}).get('sponsors', {})[0].get('name')


        b = Bill(
            title = bill_title,
            description = bill_description,
            status_date = bill_status_date,
            status = bill_status,
            state = STATES[data.get('bill', {}).get('state')],
            url = data.get('bill', {}).get('url'),
            bill_number = data.get('bill', {}).get('bill_number'),
            bill_type = data.get('bill', {}).get('bill_type_id'),
            total_sponsors = num_sponsors,
            primary_sponsor = main_sponsor,
            text = bill_text,
            content_collection = "Legislation",
            last_action = action,
            last_action_date = action_date,

            keyword_artificial_intelligence = keyword_counts['artificial intelligence'],
            keyword_machine_learning = keyword_counts['machine learning'],
            keyword_algorithm = keyword_counts['algorithm'],
            keyword_neural_network = keyword_counts['neural network'],
            keyword_deep_learning = keyword_counts['deep learning'],
            keyword_automated = keyword_counts['automated'],
            keyword_deepfake = keyword_counts['deepfake'] + keyword_counts['deep fake'],
            keyword_synthetic_media = keyword_counts['synthetic media'],
            keyword_large_language_model = keyword_counts['large language model'],
            keyword_foundation_model = keyword_counts['foundation model'],
            keyword_chatbot = keyword_counts['chatbot'],
            keyword_recommendation_system = keyword_counts['recommendation system'],
            keyword_autonomous_vehicle = keyword_counts['autonomous vehicle'],
            total_keywords = keyword_total,
            keyword_instances = get_keyword_instances(bill_text)
        )

        b.save()
        #return true if the bill was added, false if not
        return True
    else:
        return False

def get_bill_text(data):
    num_texts = len(data.get('bill', {}).get('texts', {}))
    if (num_texts > 0):
        #look for the text file, set text if not found
        text_file_id = data.get('bill', {}).get('texts', {})[num_texts - 1].get('doc_id')

        text_file_name = str(text_file_id) + '.json'

        text_file_path = os.path.join(os.path.abspath(''), '..', '..', 'legiscan', 'cache', 'api', 'text', text_file_name)

        try:
            text_file = open(text_file_path)
            data = json.load(text_file)

            text_file_type = data.get('text', {}).get('mime_id')

            doc = data.get('text', {}).get('doc')
            bill_bytes = base64.b64decode(doc)

            #something for down the line: the current text files have line numbers incorporated into the text which may disrupt search and makes snippets look weird, could do some kind of processing to remove them
            bill_text = extract_text_from_html(bill_bytes) if text_file_type == 1 else extract_text_from_pdf_bytes(bill_bytes)

        except FileNotFoundError:

            try:
                text_file_id = data.get('bill', {}).get('texts', {})[0].get('doc_id')

                text_file_name = str(text_file_id) + '.json'

                text_file_path = os.path.join(os.path.abspath(''), '..', '..', 'legiscan', 'cache', 'api', 'text', text_file_name)

                text_file = open(text_file_path)
                data = json.load(text_file)

                text_file_type = data.get('text', {}).get('mime_id')

                doc = data.get('text', {}).get('doc')
                bill_bytes = base64.b64decode(doc)

                #something for down the line: the current text files have line numbers incorporated into the text which may disrupt search and makes snippets look weird, could do some kind of processing to remove them
                bill_text = extract_text_from_html(bill_bytes) if text_file_type == 1 else extract_text_from_pdf_bytes(bill_bytes)

            except FileNotFoundError:
                bill_text = "Text file not found"
            except PdfReadError:
                print("Error reading pdf file")
                bill_text = "Text file not found"

    else:
        bill_text = "No text available"

    return bill_text

#adds all content from legiscan
def add_legislation():
    #track the number of items added
    items_added = 0
    items_not_added = 0

    #print ("Adding legislation")

    #path to legiscan directory
    abs_file_path = os.path.join(os.path.abspath(''), '..', '..', 'legiscan', 'cache', 'api', 'bill')

    for filename in tqdm(os.listdir(abs_file_path)):
        #make sure only actual bill files are processed
        if filename.endswith('.json'):
            
            bill_file = open(os.path.join(abs_file_path, filename))
            data = json.load(bill_file)

            bill_file.close()

            state_string = data.get('bill', {}).get('state')

            #cut title to 300 chars if longer
            bill_title = data.get('bill', {}).get('title')
            if len(bill_title) > 300:
                bill_title = bill_title[:297] + '...'

            #cut description to 500 chars if longer
            bill_description = data.get('bill', {}).get('description')
            if len(bill_description) > 500:
                bill_description = bill_description[:497] + '...'

            #also need to add gpt analysis to this and the federal documents

            #check to see if the bill is already in the database
            if not Bill.objects.filter(state=STATES[state_string], title=bill_title).exists():
                
                if add_bill(data):
                    items_added += 1
                    #print(bill_title, state_string)
                else:
                    items_not_added += 1

            '''
            #if a bill exists with the same title and state
            else:

                bill_status_date = data.get('bill', {}).get('status_date')

                action_date = data.get('bill', {}).get('history', {})[-1].get('date')
                
                action = data.get('bill', {}).get('history', {})[-1].get('action')

                copies = Bill.objects.filter(state=STATES[data.get('bill', {}).get('state')], title=bill_title)
                if copies.count() == 1:
                    #check if it has the same status date, last action date, and last action. If not, delete it and replace it
                    if not copies.filter(status_date=bill_status_date, last_action_date=action_date, last_action=action).exists():
                        
                        copies.delete()

                        #why is this returning values when run repeatedly?
                        #shouldn't be replacing the same thing over and over again

                        #389 items being added here and 12 the other way

                        #also all changes here are unpushed
                        if add_bill(data):
                            items_added += 1
                        else:
                            items_not_added += 1
            '''
                        
        #else:
            #print(f"{filename} not json file")
            #.DS_Store and .ipynb_checkpoints returned
    return items_added, items_not_added

#something to add here: should check if there exists a bill in the database with the same relevant features (name, state, bill number) but a different recent action date and/or status. If so, should replace that one with the new version to update status, text, and/or recent action. Basically, remove that bill and save the new version in its place

            # what that would look like:
            # copies = bill.objects.filter(state, bill number, title)
            # -if copies.count() == 1
            # if not copies.filter(status, last action date, last action).exists()
            # remove copies
            # add current bill
            # alternatively, copies[0].status = status, copies[0].last action = last action, etc.
            # copies[0].save
            # may be more efficient but text may have changed so probably easier just removing and replacing

#actual command itself (called with python manage.py populate_db)
class Command(BaseCommand):
    help = "Fills the database with items"

    def handle(self, *args, **options):

        #add items to database and count total
        items_added, items_not_added = add_legislation()
        more_items_added, more_items_not_added = add_federal_documents()
        #items_added += more_items_added
        #items_not_added += more_items_not_added

        #print out the number of items added
        self.stdout.write(self.style.SUCCESS(f'Database updated successfully ({items_added} legislation items added, {items_not_added} legislation items not added, {more_items_added} federal items added, {more_items_not_added} federal items not added)'))

        

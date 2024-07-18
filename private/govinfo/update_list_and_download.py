#updates content_list.json and downloads associated text files

import requests
import json
import os
from datetime import datetime, timedelta
from tqdm import tqdm

from dotenv import load_dotenv

load_dotenv()

#govinfo api key
API_KEY = os.environ.get('GOVINFO_API_KEY')
url = 'https://api.govinfo.gov/search?api_key=' + API_KEY

headers = {
    'accept': 'application/json',
    'Content-Type': 'application/json'
}

collection_list = [
    "CFR",
    "CHRG",
    "CREC"
    #"FR"
]

def remove_duplicates(original_list):
    unique_list = []
    for d in original_list:
        if d not in unique_list:
            unique_list.append(d)
    return unique_list

#get all content from after 10 days ago
#note: will have overlaps, currently just a workaround for them taking a while to upload some items
now = datetime.now()
start_date = now - timedelta(days=30)

formatted_date = start_date.strftime('%Y-%m-%d')

#see govinfo.gov api page for info on query syntax
for collection in collection_list:
    data = {
      "query": f"collection:({collection}) AND publishdate:range({formatted_date},) AND (content:(artificial intelligence) OR content:(machine learning) OR content:(neural network) OR content:(deep learning) OR content:(automated) OR content:(deepfake) OR content:(synthetic media) OR content:(large language model) OR content:(foundation model) OR content:(chatbot) OR content:(recommendation system) OR content:(autonomous vehicle) OR content:(algorithm))",
      "pageSize": 1000,
      "offsetMark": "*",
      "sorts": [
        {
          "field": "relevancy",
          "sortOrder": "DESC"
        }
      ],
      "historical": True,
      "resultLevel": "default"
    }
    
    #get response from govinfo
    response = requests.post(url, headers=headers, data=json.dumps(data))
    
    #200 is success
    if response.status_code == 200:
        # Parse the JSON response
        response_data = response.json()
        

        #get current list
        content_file = 'content_list.json'

        #max page size is 1000 so larger returns would get cut off
        if (response_data['count'] > 1000):
          count = response_data['count']
          print(f'Tried to get {count} results, max is 1000 at a time')
        else:
          #if there's already a content file, add to it
          if os.path.exists(content_file):
            with open(content_file, 'r') as existing_file:
                existing_list = json.load(existing_file)
    
            
            starting_size = len(existing_list['results'])

            num_items_added = len(response_data['results'])

            #combine existing and returned list
            combined_list = existing_list['results'] + response_data['results']
      
            #remove duplicate items
            combined_list = remove_duplicates(combined_list)

            num_items_added = len(combined_list) - starting_size

            combined_data = {
                'results': combined_list
            }

            #put combined list back into content_list.json
            with open(content_file, 'w') as existing_file:
              json.dump(combined_data, existing_file, indent=4)
              print(f"content_list.json updated with {num_items_added} new items")
          else:
            with open(content_file, 'w') as destination_file:
              num_items_added = len(response_data['results'])
              json.dump(response_data, destination_file, indent=4)
              print(f"content_list.json populated with {num_items_added} items")
    
    #if status code is not 200, print the error
    else:
        print(f"Request failed with status code: {response.status_code}")
        print(response.text)


# Path to your JSON file
json_file_path = 'content_list.json'

# Directories to save the downloaded files
txt_directory = ('txt_files')
pdf_directory = ('pdf_files')

# Ensure the download directory exists
os.makedirs(txt_directory, exist_ok=True)
os.makedirs(pdf_directory, exist_ok=True)

with open(json_file_path, 'r') as file:
    data = json.load(file)

# Extract PDF links and download them
for item in tqdm(data.get('results', [])):

    txt_link = ""
    pdf_link = ""

    #check if there's an associated txt file. If not, check for a pdf
    if item.get('download', {}).get('txtLink'):
        txt_link = item.get('download', {}).get('txtLink')
    elif item.get('download', {}).get('pdfLink'):
        pdf_link = item.get('download', {}).get('pdfLink')


    if txt_link:
        #save as Id.txt
        if item['granuleId']:
            file_name = item['granuleId'] + '.txt'
        elif item['packageId']:
            file_name = item['packageId'] + '.txt'
        else:
            file_name = 'no_source_found.txt'

        file_path = os.path.join(txt_directory, file_name)

        #check to see if the text has already been downloaded
        if not os.path.isfile(file_path):
        
            response = requests.get(txt_link + '?api_key=' + API_KEY)
            
            if response.status_code == 200:
                with open(file_path, 'wb') as txt_file:
                    txt_file.write(response.content)
            else:
                print(f"Failed to download {txt_link} (status code: {response.status_code})")

    elif pdf_link:
        #save as Id.pdf
        if item['granuleId']:
            file_name = item['granuleId'] + '.pdf'
        elif item['packageId']:
            file_name = item['packageId'] + '.pdf'
        else:
            file_name = 'no_source_found.pdf'
        
        # Full path to save the PDF file
        file_path = os.path.join(pdf_directory, file_name)

        #check to see if the pdf has already been downloaded
        if not os.path.isfile(file_path):
            
            # Download the PDF
            response = requests.get(pdf_link + '?api_key=' + API_KEY)
            
            if response.status_code == 200:
                with open(file_path, 'wb') as pdf_file:
                    pdf_file.write(response.content)
                #print(f"Downloaded: {file_name}")
            else:
                print(f"Failed to download {pdf_link} (status code: {response.status_code})")

    else:
        print('No txt or pdf file available')

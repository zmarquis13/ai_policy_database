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

CLASSIFICATION_PROMPT = """You are tasked with categorizing AI-related legislation and government documents (herein referred to as texts) based on their relevance to a set of four predefined categories.
Follow these steps for each text:
Identify portions of the text which explicitly pertain to AI. Focus on portions of the text where the following keywords appear: Artificial Intelligence/AI, Algorithm/Algorithmic, Machine Learning, Neural Network, Deep Learning, Automated Decision, Automation/Automated, Deepfake/Deep Fake, Synthetic Media, Large Language Model/LLM, Foundation Model, Chatbot, Recommender System.
For each category, generate reasoning regarding its relevance to the AI-related portions of the text. Be prepared to interpret the category descriptions broadly. This means considering related terminology, concepts, and examples that may not be explicitly mentioned in the category description but are still relevant.
Based on your reasoning, assign a score between 1 and 5 for each category, where:
1: Not relevant
2: Slightly relevant
3: Moderately relevant
4: Very relevant
5: Extremely relevant

Repeat this scoring process three times, independently evaluating and scoring each category on each pass.
Average the three scores assigned to each category to produce a final score for each category.
Any category that receives a final score of 4 or 5 will be assigned to the bill, so make sure it is truly relevant.
Ensure that your reasoning is thorough and precedes the scoring. This is a crucial step. The reasoning should clearly and comprehensively explain why a category is not relevant, slightly relevant, moderately relevant, very relevant, or extremely relevant to the AI-related portions of the text. The quality and depth of your reasoning will directly inform the accuracy of the score you assign.
The provided category descriptions may not be exhaustive. You must use your extensive training data to intuitively bridge any gaps. Apply deductive reasoning to align the text with the most fitting category or categories. Recognize that while the text may touch upon multiple categories, not all connections warrant categorization. Avoid marginal associations.
Here are the four categories:
Social Impact: encompasses legislation that specifically addresses the impact of AI on society and individuals, including but not limited to; reducing the carbon footprint of AI systems, holding system developers accountable for the outputs of these systems, the establishment of new fairness and bias metrics to guard against AI-driven discrimination, the use of AI by minors, consumer protections for AI products, regulations that address psychological, physical, or material harm caused by interactions with AI systems, and the role of AI in misinformation, public discourse, and the erosion of trust in public institutions.
Data Governance: encompasses legislation that specifically addresses the secure and accurate collection and management of data within AI systems, including but not limited to; mandates for rectifying inaccuracies in AI data sets, mandates for ensuring AI data sets are free from biases, regulations that address intellectual property concerns with the unauthorized use of protected material in AI data sets, and requirements for data encryption, data anonymization, controlled access, and compliance with consumer privacy laws. 
System Integrity: encompasses legislation that specifically addresses the inherent security, transparency, and control of AI systems, including but not limited to; mandates for human intervention and oversight in AI processes, standards for the interoperability of AI systems in essential services, and the implementation of security measures such as threat modeling, penetration testing, and incident response.
Robustness: encompasses legislation that specifically addresses the development and adoption of new benchmarks for AI performance, including but not limited to; the certification of AI systems against new benchmarks, ensuring compliance with international standards, requirements for auditing and transparent reporting to verify continuous regulatory compliance, and the creation of specialized oversight bodies.

You are also tasked with categorizing texts based on their relevance to a set of nine predefined sectors.
Follow the same steps for each text with the sectors instead:
For each sector, generate reasoning regarding its relevance to the text and use the previously described 1-5 scale. 
Ensure that your reasoning is thorough and precedes the scoring.
The provided sector descriptions may not be exhaustive. Avoid marginal associations.
Here are the nine sectors:
Politics and Elections: encompasses legislation that specifically addresses the use and regulation of AI in political campaigns, electoral processes, and related legislative activities.
Government Agencies and Public Services: encompasses legislation that specifically addresses the use and regulation of AI by state and federal government agencies, as well as AI applications in the delivery of public services and enhancing government operations.
Judicial System: encompasses legislation that specifically addresses the use and regulation of AI by judicial and legal systems, including but not limited to the use of AI in case management and legal decision making.
Healthcare: encompasses legislation that specifically addresses the use and regulation of AI in healthcare settings, including but not limited to AI applications within hospitals and clinics, the development of AI-enabled diagnostic tools and related medical technologies, and the management of medical data. 
Private Enterprises, Labor, and Employment: encompasses legislation that specifically addresses the use and regulation of AI in business environments, ensuring fair competition, and the effects of AI on labor markets, employment practices, and corporate governance. 
Academic and Research Institutions: encompasses legislation that specifically addresses the use and regulation of AI in educational and research contexts. 
International Cooperation and Standards: encompasses laws and agreements that address international cooperation on AI development, use, and regulation, including but not limited to multinational standards, cross-border data practices, and global ethical guidelines for AI.
Nonprofits and NGOs: encompasses legislation that specifically addresses the use and regulation of AI by nonprofits and non-governmental organizations and institutions.
Hybrid, Emerging, and Unclassified: encompasses legislation that doesn’t neatly fit into other categories, as well as the application of AI in hybrid or emerging sectors.


Answer in the form of a json object with the following fields:
{
    "Category reasoning": "Reasoning about the category decisions",
    "Social impact": int,
    "Data governance": int,
    "System integrity": int,
    "Robustness": int,
    "Sector reasoning": "Reasoning about the sector decisions",
    "Politics and Elections": int,
    "Government Agencies and Public Services": int,
    "Judicial System": int,
    "Healthcare": int,
    "Private Enterprises, Labor, and Employment": int,
    "Academic and Research Institutions": int,
    "International Cooperation and Standards": int,
    "Nonprofits and NGOs": int,
    "Hybrid, Emerging, and Unclassified": int
}

"""

#current directory: private/site/billscraper/search/management/commands
#need to decide where analyses are being stored
#could make a management/analyses folder

def analyze_all_items():
    #filters on time
    content_list = Bill.objects.filter(status_date__gte='2023-01-01')
    #content_list = content_list.filter(status_date__gte='2024-05-01')

    items_classified = 0

    #private/site/billscraper/search/management/analyses
    analysis_directory_path = 'analyses'

    if not os.path.exists(analysis_directory_path):
        os.makedirs(analysis_directory_path)

    for bill in tqdm(content_list):
        #check to see if it's already been analyzed
        if bill.societal_impact == 0:

            #unique identifier
            bill_url = bill.url
            cleaned_id = bill_url.replace('https://', '').replace('/', '')
            filename = cleaned_id + '.json'

            path_to_file = os.path.join(analysis_directory_path, filename)

            analysis_json = {}

            if os.path.exists(path_to_file):
                # File exists, load and return its JSON content
                with open(path_to_file, 'r') as file:
                    try:
                        analysis_json = json.load(file)
                    except json.JSONDecodeError:
                        print("Error: The retrieved file is not a valid JSON file.")
            else:
                analysis_json = gpt_analysis(bill)

                # Write the result to the file
                with open(path_to_file, 'w') as file:
                    try:
                        json.dump(analysis_json, file, indent=4)  # Write JSON with indentation
                    except TypeError as e:
                        print(f"Error writing JSON to file: {e}")


            if analysis_json:
                bill.category_reasoning = analysis_json['Category reasoning']
                bill.societal_impact = analysis_json['Social impact']
                bill.data_governance = analysis_json['Data governance']
                bill.system_integrity = analysis_json['System integrity']
                bill.robustness = analysis_json['Robustness']
                bill.sector_reasoning = analysis_json['Sector reasoning']
                bill.politics_elections = analysis_json['Politics and Elections']
                bill.government_public = analysis_json['Government Agencies and Public Services']
                bill.judicial = analysis_json['Judicial System']
                bill.healthcare = analysis_json['Healthcare']
                bill.private = analysis_json['Private Enterprises, Labor, and Employment']
                bill.academic = analysis_json['Academic and Research Institutions']
                bill.international = analysis_json['International Cooperation and Standards']
                bill.nonprofits = analysis_json['Nonprofits and NGOs']
                bill.other_sector = analysis_json['Hybrid, Emerging, and Unclassified']

                #important step, need to save
                bill.save()

                items_classified += 1

            else:
                print("Error: could not get analysis")
        else:
            pass    
    return items_classified

def gpt_analysis(bill):
    #feed title, description, and first 20,000 chars of text
    if bill.description != "N/A":
        bill_content = f"Title: {bill.title}\n Description: {bill.description}\n Text: {bill.text[:20000]}"
    else:
        bill_content = f"Title: {bill.title}\n Text: {bill.text[:20000]}"

    response = client.chat.completions.create(
    model="gpt-4o-mini",
    response_format={ "type": "json_object" },
    messages=[
        {"role": "system", "content": CLASSIFICATION_PROMPT},
        {"role": "user", "content": bill_content}
    ]
    )
    content = response.choices[0].message.content
    #print(content)
    json_response = json.loads(content)
    return json_response


class Command(BaseCommand):
    help = "Uses chatgpt to categorize items"

    def handle(self, *args, **options):

        items_classified = analyze_all_items()

        self.stdout.write(self.style.SUCCESS(f'Database updated successfully ({items_classified} items classified)'))

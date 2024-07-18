#Definition of the bill model (the underlying unit of storage for all content in the database)


from django.db import models
from django.contrib.postgres.fields import ArrayField

from django.contrib.postgres.indexes import GinIndex

from django.contrib.postgres.search import SearchVector
import django.contrib.postgres.search as pg_search

# Create your models here.
class Bill(models.Model):
    title = models.CharField(default="N/A")
    description = models.CharField(default="N/A")
    text = models.CharField(default="N/A")

    #link to item in its source database
    url = models.CharField(default="legiscan.com")

    #for legislation, whether it passed, etc.
    status = models.CharField(default="N/A")
    status_date = models.DateField(default="1970-1-1")

    #really jurisdicition
    state = models.CharField(default="N/A")

    #bill id code
    bill_number = models.CharField(default="N/A")

    #legiscan categorization (HB, SB, etc.)
    bill_type = models.CharField(default="N/A")

    #for legislation, who sponsored it
    primary_sponsor = models.CharField(default="N/A")
    total_sponsors = models.IntegerField(default=0)

    #department/agency publishing bill
    source = models.CharField(default="N/A")

    #where this bill comes from (ex. code of federal regulations)
    content_collection = models.CharField(default="N/A")

    #llm's explanation for which categories it chose
    category_reasoning = models.CharField(default="N/A")

    #1-5 scores of category relevance (5 = most relevant)
    societal_impact = models.IntegerField(default=0)
    data_governance = models.IntegerField(default=0)
    system_integrity = models.IntegerField(default=0)
    robustness = models.IntegerField(default=0)

    #llm's explanation for which sectors it chose
    sector_reasoning = models.CharField(default="N/A")

    #1-5 scores of sector relevance (5 = most relevant)
    politics_elections = models.IntegerField(default=0)
    government_public = models.IntegerField(default=0)
    judicial = models.IntegerField(default=0)
    healthcare = models.IntegerField(default=0)
    private = models.IntegerField(default=0)
    academic = models.IntegerField(default=0)
    international = models.IntegerField(default=0)
    nonprofits = models.IntegerField(default=0)
    other_sector = models.IntegerField(default=0)


    last_action = models.CharField(default="N/A")
    last_action_date = models.DateField(default="1970-1-1")

    #total number of keywords
    total_keywords = models.IntegerField(default=0)

    #occurrance of specific keywords in the item's text
    #note: must update when adding new keywords
    keyword_artificial_intelligence = models.IntegerField(default=0)
    keyword_machine_learning = models.IntegerField(default=0)
    keyword_neural_network = models.IntegerField(default=0)
    keyword_deep_learning = models.IntegerField(default=0)
    keyword_automated = models.IntegerField(default=0)
    keyword_deepfake = models.IntegerField(default=0)
    keyword_synthetic_media = models.IntegerField(default=0)
    keyword_large_language_model = models.IntegerField(default=0)
    keyword_foundation_model = models.IntegerField(default=0)
    keyword_chatbot = models.IntegerField(default=0)
    keyword_recommendation_system = models.IntegerField(default=0)
    keyword_algorithm = models.IntegerField(default=0)
    keyword_autonomous_vehicle = models.IntegerField(default=0)

    #list of keywords in context
    keyword_instances = ArrayField(models.CharField(max_length=None), blank=True, default=list)

    #display for the admin page
    def __str__(self):
        return self.title

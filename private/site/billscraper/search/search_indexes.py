#definition of the index that enables fast searching and filtering

import datetime
from haystack import indexes
from search.models import Bill

# fields that are stored in the index (fields must be stored here to be
# filtered through the sidebar)
class BillIndex(indexes.SearchIndex, indexes.Indexable):
    #document=True field is indexed more heavily and is searchable through text search
    #field configured in templates/search/indexes/search/bill_text.txt
    text = indexes.CharField(document=True, use_template=True)

    #add boost to make title matches show up more prominently
    title = indexes.CharField(model_attr='title', boost=10.0)

    last_action_date = indexes.DateField(model_attr='last_action_date')
    status_date = indexes.DateField(model_attr='status_date')
    state = indexes.CharField(model_attr='state')
    status = indexes.CharField(model_attr='status')
    content_collection = indexes.CharField(model_attr='content_collection')
    total_keywords = indexes.IntegerField(model_attr='total_keywords')
    societal_impact = indexes.IntegerField(model_attr='societal_impact')
    data_governance = indexes.IntegerField(model_attr='data_governance')
    system_integrity = indexes.IntegerField(model_attr='system_integrity')
    robustness = indexes.IntegerField(model_attr='robustness')
    politics_elections = indexes.IntegerField(model_attr='politics_elections')
    government_public = indexes.IntegerField(model_attr='government_public')
    judicial = indexes.IntegerField(model_attr='judicial')
    healthcare = indexes.IntegerField(model_attr='healthcare')
    private = indexes.IntegerField(model_attr='private')
    academic = indexes.IntegerField(model_attr='academic')
    international = indexes.IntegerField(model_attr='international')
    nonprofits = indexes.IntegerField(model_attr='nonprofits')
    other_sector = indexes.IntegerField(model_attr='other_sector')


    def get_model(self):
        return Bill

    def index_queryset(self, using=None):
            return self.get_model().objects.all()

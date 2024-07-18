#loads the different pages of the site

from django.shortcuts import render

from django.http import HttpResponse

from .models import Bill

from django.urls import reverse
from urllib.parse import urlencode

from django.contrib.postgres.search import SearchQuery, SearchRank, SearchVector, SearchHeadline

from django.utils.safestring import SafeString
from django.core.paginator import Paginator
from django.template import Context
from django.db.models import Q

from haystack.query import SearchQuerySet
from haystack.utils.highlighting import Highlighter
from haystack.inputs import Exact
from haystack.query import SQ
from haystack.inputs import Raw
from haystack.inputs import AutoQuery

import datetime

from whoosh.qparser import QueryParserError
from whoosh.qparser import QueryParser
from whoosh.fields import Schema, TEXT

from haystack.backends.whoosh_backend import WhooshSearchBackend
from haystack import connections

from whoosh.highlight import ContextFragmenter

from haystack.utils import Highlighter

import re

# Create your views here.

#loads the about page
def about(request):
    return render(request, 'search/about.html', {})

#homepage
def home(request):
    return render(request, 'search/home.html', 
    {'num_bills': Bill.objects.count() + 1})

#show results from search filters
def results(request):

    if request.method == "POST":
        searched = request.POST.get('searched', '')  
    else:
        searched = request.GET.get('q', '')

    #get url based on query
    base_url = reverse('results') 
    query_params = request.GET.copy()

    #handles search through POST instead of GET
    if searched:
        query_params['q'] = searched
    
    #removes the page number (leaves it to the pagination operation)
    if 'page' in query_params:
        del query_params['page']

    #removes csrf token from url
    if 'csrfmiddlewaretoken' in query_params:
        del query_params['csrfmiddlewaretoken']

    #check to see if any search filters have been applied, if not
    #return a message to search
    if ((not searched) and (not request.GET.copy()) or (query_params.urlencode()=='q=&start_date=&end_date=')):
        return render(request, 'search/results.html', {'no_search': True})
    else:
        no_search = False

    sqs = SearchQuerySet()

    results = sqs.all()

    if searched:
        try:    
            #uses raw search, ordering is by relevance by default
            #whoosh only gets highlights from the first 100000 chars
            #could experiment with haystack bsoost to incorporate some
            #relevance or make title count more
            results = results.filter(content=Raw(searched)).highlight(highlight_query=Exact(searched))

        except QueryParserError:
            # Handle invalid query
            results = SearchQuerySet().none()
            error_message = "Invalid search query. Please check your syntax."

    #filter start and end dates based on input
    start_date = request.GET.get('start_date')
    if start_date:
        results = results.filter(status_date__gte=start_date)

    end_date = request.GET.get('end_date')
    if end_date:
        results = results.filter(status_date__lte=end_date)
    else:
        #this makes queries with sort but no filters 10x faster for some reason
        results = results.filter(status_date__lte=datetime.date.today())

    #filter jurisdiction if selected
    selected_states = request.GET.getlist('jurisdiction')
    if selected_states:
        results = results.filter(state__exact__in=selected_states)
        #selecting virginia was also displaying west virginia
        if (not 'West Virginia' in selected_states):
            results = results.exclude(state='West Virginia')

    #filter status if selected
    selected_status = request.GET.getlist('status')
    if selected_status:
        results = results.filter(status__in=selected_status)

    #filter collections if selected
    selected_collections = request.GET.getlist('collection')
    if selected_collections:
        results = results.filter(content_collection__in=selected_collections)

    selected_categories = request.GET.getlist('category')
    if selected_categories:
        filters = Q()
        for category in selected_categories:
            filters |= Q(**{f"{category}__gte": 3})
        results = results.filter(filters)

    selected_sectors = request.GET.getlist('sector')
    if selected_sectors:
        filters = Q()
        for sector in selected_sectors:
            filters |= Q(**{f"{sector}__gte": 3})
        results = results.filter(filters)

    #make relevance the default if a search term has been entered,
    #recency otherwise
    ordering = request.GET.get('sort')
    if not ordering:
        if searched:
            ordering = 'relevance'
        else:
            ordering = 'newest'

    #ordering is relevance by default so no need to order by it
    if ordering == 'oldest_status':
        results = results.order_by('status_date')
    elif ordering == 'newest_status':
        results = results.order_by('-status_date')
    elif ordering == 'oldest_action':
        results = results.filter(content_collection='Legislation')
        results = results.order_by('last_action_date')
    elif ordering == 'newest_action':
        results = results.filter(content_collection='Legislation')
        results = results.filter(last_action_date__lte=datetime.date.today())
        results = results.order_by('-last_action_date')
    elif ordering == 'keyword':
        results = results.order_by('-total_keywords')

    num_results = results.count()

    #pages of 20 items
    p = Paginator(results, 20)
    page = request.GET.get('page')
    shown_bills = p.get_page(page)

    #relevant information for the displaying html page
    context = {
        'searched': searched,
        'shown_bills': shown_bills,
        'num_results': num_results,
        'sort': ordering,
        'sidebar_search': searched,
        'selected_status': selected_status,
        'selected_collections': selected_collections,
        'jurisdiction': selected_states,
        'start_date': start_date,
        'end_date': end_date,
        'no_search': no_search,
        'selected_categories': selected_categories,
        'selected_sectors': selected_sectors
    }

    #information encoded in the url
    params = {
        'searched': searched,
        'selected_states[]': [selected_states],
        'sort': ordering,
        'selected_status[]': [selected_status],
        'jurisdiction[]': selected_states,
        'start_date': start_date,
        'end_date': end_date
    }

    #encode the query in the url
    context['query_string'] = query_params.urlencode()

    #load the results page with the relevant information
    return render(request, 'search/results.html', context)


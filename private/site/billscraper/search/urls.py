from django.urls import path

from . import views

#urls used in the site (aipolicydatabase/search/url)
urlpatterns = [
    path("results", views.results, name="results"),
    path("home", views.home, name="home"),
    path("about", views.about, name="about"),
]

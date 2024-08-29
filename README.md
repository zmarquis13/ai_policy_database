# AI Policy Database
A comprehensive database of artificial intelligence policy in all 50 states, DC, and the federal government since the start of 2023, and all federal regulation and U.S. congressional proceedings related to artificial intelligence in the same time period.

# General Overview of Tools Used:
- digitalocean: hosting site, program runs on a droplet (virtual machine)
- namecheap: service that domain (aipolicydatabase.com) is registered to
- django: web framework used for site implementation
- postgresql: database used to store content
- haystack + whoosh: indexing tools for search + filter functionality
- gunicorn: runs django implementation
- nginx: web server
- supervisor: gets gunicorn running automatically
- cron: schedules updates with new content (currently daily)
- legiscan: database containing legislation from all 50 states + DC + federal
- govinfo: database containing U.S. federal government documents

# Program structure:
main directory:
- .gitignore: files to ignore
- LICENSE: software license
- README.md: this file
- requirements.txt: System requirements in order to run the site successfully
- private: directory containing implementation

private directory:
- eu_corpus_compiler-master: directory containing a program that could be used to add EU legislation in the future
- govinfo: directory containing programs that interface with the govinfo.gov API to get search results and text files. See https://api.govinfo.gov/docs/ for more info.
- legiscan: directory containing legiscan config, API interaction, and legislative info. See https://api.legiscan.com/dl/ for more info.
- site/billscraper: directory containing django implementation of the site

private/site/billscraper directory:
- billscraper: directory containing settings, root urls, and static files
- search: directory containing implementation of database search features
- manage.py: django program called to execute commands like populate_db and rebuild_index (comes with django, only edit if you know what you're doing)

private/site/billscraper/billscraper directory:
- settingsprod.py: actual settings for the program in production
- settings.py: used for testing + development, not used in production (see manage.py for the settings file being used)
- urls.py: redirects aipolicydatabase.com to aipolicydatabase.com/search/home
- search/static: static files for site implementation

private/site/billscraper/search directory:
- management/commands/populate_db.py: implementation of the python manage.py populate_db command
- migrations: directory listing changes to the bill module
- static/search: css for views in this directory
- templates/search: html files for different components and the file indexes/search/bill_text.txt which specifies which fields should be text-searchable in the whoosh index (what can be found from the search bar)
- admin.py: configuration for the django admin page for the site
- apps.py: search app declaration
- models.py: structure of the bill model
- search_indexes.py: specifies which fields of the model are part of the index (fields must be added here to be filtered with the sidebar filter)
- urls.py: instructs what view to load for each url
- views.py: gets information, filters, and loads html pages with content (results view is particularly important)

private/site/billscraper/search/templates/search:
- base.html: website title and contains navbar
- home.html: homepage of the site
- navbar.html: site header with navigation options
- results.html: displays content, called in views.py
- sidebar.html: clickable search filters on a form that shows up as a sidebar

# Most Important Programs:
There are a lot of files, but the main action of the site can be captured in 4 files
- private/site/billscraper/search/management/commands/populate_db.py: adds content to the database
- private/site/billscraper/search/models.py: structure of the bill model (the object that stores content for the site)
- private/site/billscraper/search/templates/search/sidebar.html: filter boxes and search field
- private/site/billscraper/search/views.py: takes the form submitted from sidebar.html, filters the bills, then returns the resulting list


# Useful Commands
in private/site/billscraper:

`python manage.py populate_db`: Adds all legislation and regulation to the database that isn't already there, pulling from the legiscan api cache and private/govinfo/content_list.json (getting regulation text from private/govinfo/txt_files and pdf_files)

`python manage.py llm_analysis`: Uses ChatGPT to classify all unclassified items into category and sector, as well as adding the reasoning

`python manage.py update_legislation`: Compares all legislation (but not other documents) in the database to their associated data files to check for changes to text, status, and/or action 

`python manage.py rebuild_index`: Rebuilds the whoosh index that enables reasonable search times (useful to do if searches are taking more than a couple of seconds)

In private/govinfo:

`python update_list_and_download.py`: Updates the content list and, for each item in the resulting list, downloads its associated text file if not already downloaded

In private/legiscan:

`php legiscand.php`: looks for all relevant bills that aren't already in the legiscan_api postgresql database and adds them to the database and downloads their information and text files. Configurable in private/legiscan/config.php (omitted in this repo since it contains sensitive information)

These commands are all executed automatically with cron jobs running the scripts in the private/cron_scripts directory



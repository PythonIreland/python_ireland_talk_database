# python_ireland_talk_database
An application capable of creating a historical database for all Python Ireland talks. PyCon Ireland, Limerick and monthly meetups.

# Python Ireland talks database:

## Project ideas:
1. Create a searchable database of past Meetups.
2. Create a searchable database of all PyCon talks & videos.
3. Create a web application to display Meetup & PyCon meta data

## Introduction:
For Python Ireland, we would like to create a historical database of each of the presentations given, at both our monthly meetups and PyCon Ireland and Limerick conferences.
This data can then be used to help us make informed decisions about upcoming events, for example:

### Meetups:
1. If we can find a venue who used to host us in the past - we can reach out and ask them to host us again.
2. If we have had speakers for a given topic we would like to reach out to.
3. See when was the last time we presented a given topic - when was the last "Python for beginners" type talk given?

### PyCons:
1. See all talks by a given speaker.
2. See all talks for a given subject.
3. Decide to we have enough scope to split rooms into dedicated tracks, data science, AI, web dev, etc.

## Application structure:
This will be discussed and agred with the Python Ireland development team and updated. A suggested structure is: https://github.com/cookiecutter-flask/cookiecutter-flask

The required application will need to be capable of 3 things:
1. Scraping the Meetup API.
2. Scraping PyCon Ireland data (Sessionize API?, Sessionize csv file?).
3. Presenting the data in an easily digestible format.

For the above application we will use a templated web application (Flask or other framework) to house the main application #3, above. For items #1 and #2, above we will store the code in a relevant class object that can be called, standalone, from their own main.py type file.

An example 

## Technology Stack:
This will be discussed and agred with the Python Ireland development team and updated. A suggested stack is:

1. Flask / FastAPI
2. React JS frontend
3. SQLAlchemy ORM
4. SQLite DB
5. Python typing
6. pytest
7. pylint
8. GitHub Actions

## Project development constraints:
In order to proceed with the collaborative development, on GitHub, the app structure must be completed first. A suggestion would be to create a fresh cookiecutter-flask instance, and begin from there.
Once the app structure is in place, 2 files can be created, meetup_scraper.py and py_con_scraper.py, which will allow parallel development on the 3 main project tracks.

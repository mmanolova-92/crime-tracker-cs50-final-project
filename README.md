# Crime Tracker

Crime Tracker is a web application that provides a graphical mapping of criminal activity across Berlin, one of the largest and most criminal cities in Europe.

## Table of contents
* [Information](#info)
* [Project structure](#projectstructure)
* [Technologies](#technologies)
* [Setup](#setup)
* [Contributors](#contributors)

## Information
The application collects the latest police reports which are listed on the website https://www.berlin.de/polizei/polizeimeldungen and visualizes these on an interactive map based on their location. Furthermore, the users also has the option to report any crime activity they have witnessed by choosing the location on the map and providing the date, time, and a short description. The Mapbox API is used for integrating the web map in the application.

The landing page prompts for user login details. If visiting for the first time, the user can opt in to register from the "Register" button in the top-right corner of the web application. The registration form requires more data from the user than expected, because the ...

The home page shows the interactive map with markers on the locations where a crime activity was reported in the news. When the user clicks on a marker on the map, a popup appears and provides more infromation such as date, time, location and title of the crime report. On the right side of the map there is a log of all the crime reports listed on the aforementioned website for a better overview.

There is an animation button on the map which allows the user to report a crime and add this to the log of crime reports. After the user clicks the button, an alert appears asking the user to select the location of the witnessed crime actitivy. This can be achieved by clicking on the chosen place on the map. This action provides the geographic coordinates of the place in Mapbox and the exact address can be obtained by using reverse geocoding of the Mapbox API.

In addition to the web map visualizing the location of the crime reports, there is a data analytics section with several diagrams. The first diagram shows the total amount of reports and the second one - the dates of the reported cases. The third chart illustrates the amount of reports for each crime type and the last one represents the crime cases in the different neighbourhoods. The diagrams are created by using Chart.js.

In case the user has reported any crime activity in the web application, an overview table with their reports can be viewed in a separate page.

## Project structure
[final_project](./final_project)
   * [application.py](./final_project/application.py)
   * [crimes.json](./final_project/crimes.json)
   * [database.db](./final_project/database.db)
   * [helpers.py](./final_project/helpers.py)
   * [README.md](./final_project/README.md)
   * [requirements.txt](./final_project/requirements.txt)
 * [crimeAnalysis](./crimeAnalysis)
    * [__init__.py](./crimeAnalysis/__init__.py)
    * [scrapy.cfg](./crimeAnalysis/scrapy.cfg)
    * [crimeAnalysis](./crimeAnalysis/crimeAnalysis)
        * [__init__.py](./crimeAnalysis/crimeAnalysis/__init__.py)
        * [items.py](./crimeAnalysis/crimeAnalysis/items.py)
        * [middlewares.py](./crimeAnalysis/crimeAnalysis/middlewares.py)
        * [pipelines.py](./crimeAnalysis/crimeAnalysis/pipelines.py)
        * [settings.py](./crimeAnalysis/crimeAnalysis/settings.py)
        * [spiders](./crimeAnalysis/crimeAnalysis/spiders)
            * [__init__.py](./crimeAnalysis/crimeAnalysis/spiders/__init__.py)
            * [articles-spider.py](./crimeAnalysis/crimeAnalysis/spiders/articles-spider.py)
            * [crimes.json](./crimeAnalysis/crimeAnalysis/spiders/crimes.json)
 * [static](./static)
    * [cop.gif](./static/cop.gif)
    * [crime-tracker-logo.png](./static/crime-tracker-logo.png)
    * [favicon.ico](./static/favicon.ico)
    * [Light_1.gif](./static/Light_1.gif)
    * [marker-user.png](./static/marker-user.png)
    * [marker.png](./static/marker.png)
    * [news.png](./static/news.png)
    * [street.jpg](./static/street.jpg)
    * [styles.css](./static/styles.css)
    * [thief.gif](./static/thief.gif)
    * [user.png](./static/user.png)
 * [templates](./templates)
    * [apology.html](./templates/apology.html)
    * [history.html](./templates/history.html)
    * [index.html](./templates/index.html)
    * [layout.html](./templates/layout.html)
    * [login.html](./templates/login.html)
    * [register.html](./templates/register.html)

## Technologies
The project is created by using the following frameworks:
* HTML
* CSS
* JavaScript
* Flask
* Python
* Scrapy
* Mapbox GL
* Chart.js
* SQLite

## Setup
Ther CS50 IDE was used for developing and testing the web application. Before running the project, the Python libraries specified in the "requirements.txt" file should be installed:

```bash
$ cd project
$ pip install -r requirements.txt
```

Then follow the instructions to set up and run the project:

```bash
$ set FLASK_APPLICATION=application.py
$ set DEBUG=1
$ flask run
```

## Contributors
Alex Sakakushev - alexsak <br/>
Manuela Manolova - mmanolova-92

import os, sys, json, geocoder, sqlite3, subprocess
import pandas as pd
from cs50 import SQL
from flask import Flask, flash, jsonify, redirect, render_template, request, session, make_response
from flask_session import Session
from tempfile import mkdtemp
from werkzeug.exceptions import default_exceptions, HTTPException, InternalServerError
from werkzeug.security import check_password_hash, generate_password_hash
from helpers import apology, login_required

from crimeAnalysis.crimeAnalysis.spiders.articles_spider import crimeSpider
import datetime
import schedule
import time


# Configure application
app = Flask(__name__)

# Ensure templates are auto-reloaded
app.config["TEMPLATES_AUTO_RELOAD"] = True

# Ensure responses aren't cached
@app.after_request
def after_request(response):
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"
    return response

# Configure session to use filesystem (instead of signed cookies)
app.config["SESSION_FILE_DIR"] = mkdtemp()
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Configure CS50 Library to use SQLite database
db = SQL("sqlite:///database.db")

@app.route("/register", methods=["GET", "POST"])
def register():

    """Register user"""
    if request.method == "GET":
        return render_template("register.html")

    else:
        username = request.form.get("username")
        password = request.form.get("password")
        firstname = request.form.get("firstname")
        lastname = request.form.get("lastname")
        streetname = request.form.get("streetname")
        city = request.form.get("city")
        plz = request.form.get("plz")
        confirmation = request.form.get("confirmation")

        if (username == "" or password == "" or confirmation == ""):
            return apology("please enter a valid username and password", 400)
        if password != confirmation :
            return apology("your passwords do not match", 400)

        existing_users_raw = db.execute("SELECT distinct username FROM users")
        existing_users = [d['username'] for d in existing_users_raw if 'username' in d]
        if username in existing_users:
            return apology("this user already exists", 400)

        hash_password = generate_password_hash(password, method='pbkdf2:sha256', salt_length=len(password))

        db.execute("INSERT INTO users (userName, password, firstName, lastName, streetName, city, PLZ) VALUES (%s, %s, %s, %s, %s, %s, %s)", (username, hash_password, firstname, lastname, streetname, city, plz))

        return redirect("/login")


@app.route("/login", methods=["GET", "POST"])
def login():
    """Log user in"""

    # Forget any user_id
    session.clear()

    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":

        # Ensure username was submitted
        if not request.form.get("username"):
            return apology("must provide username", 403)

        # Ensure password was submitted
        elif not request.form.get("password"):
            return apology("must provide password", 403)

        # Query database for username
        rows = db.execute("SELECT * FROM users WHERE userName = :username",
                          username=request.form.get("username"))

        # Ensure username exists and password is correct
        if len(rows) != 1 or not check_password_hash(rows[0]["password"], request.form.get("password")):
            return apology("invalid username and/or password", 403)

        # Remember which user has logged in
        session["user_id"] = rows[0]["id"]

        # Redirect user to home page
        return redirect("/")

    # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("login.html")


@app.route("/logout")
def logout():
    """Log user out"""

    # Forget any user_id
    session.clear()

    # Redirect user to login form
    return redirect("/")


@app.route("/check", methods=["GET"])
def check():
    """Return true if username available, else false, in JSON format"""
    username = session['userName']
    # username = g.user.username

    existing_users_raw = db.execute("SELECT distinct userName FROM users")
    existing_users = [d['userName'] for d in existing_users_raw if 'userName' in d]
    
    if username not in existing_users:
        return jsonify({'status': "true"}), 400
    else:
        return jsonify({'status': "false"}), 200


@app.route("/", methods=["GET", "POST"])
@login_required
def index():

    # cmdline.execute("scrapy crawl crimes -o crimes.json -t json".split())

    # return render_template("index.html", portfolio=portfolio.to_html(classes=["table table-striped"],index=False))
    if request.method == "POST":
        username = session["user_id"]
        crimeType_input = request.form.get("typeCrime")

        dateTime = request.form.get("crimeTime")
        dateTime_read = datetime.datetime.strptime(dateTime, '%Y-%m-%dT%H:%M')
        dateTime_formatted = dateTime_read.strftime('%d.%m.%Y %H:%M')

        crimeDate_input = dateTime_formatted.split(' ')[0]
        crimeTime_input = dateTime_formatted.split(' ')[1]

        crimeLocation_input = request.form.get('crimeDistrict')
        crimeLatLong_input = request.form.get('crimeLatLng')
        crimeDescription_input = request.form.get("crimeDescription")

        db.execute("INSERT INTO crimeReports_news (date, time, crimeType, location, latLong, title, username, source) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)", (crimeDate_input.replace('.','/'), crimeTime_input, crimeType_input, crimeLocation_input, crimeLatLong_input, crimeDescription_input, username, "user"))
        return redirect("/")

    else:
        username = session["user_id"]

        crimeSpider().run()

        with open('crimes.json') as json_file:

            data = json.load(json_file)

            for entry in data:

                date = entry['date']
                time = entry['time']

                if entry['location'] is None:
                    location = "berlinweit"
                    latLong = '52.520008, 13.404954'
                elif entry['location'] == 'berlinweit' or entry['location'] == 'bezirksübergreifend':
                    location = entry['location']
                    latLong = '52.520008, 13.404954'
                else:
                    location = entry['location']
                    latLong = ', '.join(map(str, entry['latLong']))

                title = entry['title']
                crimeType = ', '.join(entry['crimeType'])
                source = "Polizeipräsident"

                db.execute("INSERT INTO crimeReports_news (date, time, location, latLong, title, crimeType, source) VALUES (%s, %s, %s, %s, %s, %s, %s)", (date.replace('.','/'), time, location, latLong, title, crimeType, source))
                db.execute("DELETE FROM crimeReports_news WHERE id IN (SELECT t.id FROM crimeReports_news t GROUP BY t.date, t.time, t.title HAVING COUNT(*) > 1);")

        #update()

        reports_news = db.execute("SELECT title, location, latLong, source, date, time, crimeType FROM crimeReports_news ORDER BY date DESC, time DESC")

        # reports_news.extend(reports_users)

        reports_news_df = pd.DataFrame(reports_news)

        #reports_news_df = reports_news_df[['title','location','latLong','date','time','crimeType']]    
        

        #reports_news_count = reports_news_df.shape[0]

        # tot_crimeType = db.execute("SELECT a.crimeType, a.crimeN, ifnull(b.crimeU,0) FROM (SELECT crimeType, count(id) as crimeN FROM crimeReports_news GROUP BY crimeType) as a LEFT JOIN (SELECT crimeType, count(id) as crimeU FROM crimeReports_users GROUP BY crimeType) as b ON a.crimeType = b.crimeType")

        # tot_date = db.execute("SELECT a.date, a.crimeN, ifnull(b.crimeU,0) FROM (SELECT date, count(id) as crimeN FROM crimeReports_news GROUP BY date) as a LEFT JOIN (SELECT date, count(id) as crimeU FROM crimeReports_users GROUP BY date) as b ON a.date = b.date")

        # tot_location = db.execute("SELECT a.location, a.crimeN, ifnull(b.crimeU,0) FROM (SELECT location, count(id) as crimeN FROM crimeReports_news GROUP BY location) as a LEFT JOIN (SELECT location, count(id) as crimeU FROM crimeReports_users GROUP BY location) as b ON a.location = b.location")

        tot_crimeType = db.execute("SELECT crimeType, sum(case when source = 'Polizeipräsident' then 1 else 0 end) as crimeN, sum(case when source = 'user' then 1 else 0 end) as crimeU FROM crimeReports_news GROUP BY crimeType")

        tot_date = db.execute("SELECT date, sum(case when source = 'Polizeipräsident' then 1 else 0 end) as crimeN, sum(case when source = 'user' then 1 else 0 end) as crimeU FROM crimeReports_news GROUP BY date")

        tot_location = db.execute("SELECT location, sum(case when source = 'Polizeipräsident' then 1 else 0 end) as crimeN, sum(case when source = 'user' then 1 else 0 end) as crimeU FROM crimeReports_news GROUP BY location")

        all_latLng = db.execute("SELECT title, date, time, crimeType, location, latLong FROM crimeReports_news")

        return render_template("index.html", reports_news = reports_news, tot_crimeType = tot_crimeType, tot_date = tot_date, tot_location = tot_location, all_latLng = all_latLng)

    # else:
    #     return render_template("buy.html")

@app.route("/signalsLog")
@login_required
def signalsLog():
    """Show history of user-submitted signals"""

    username = session["user_id"]
    signals_list = db.execute("SELECT date, time, location, crimeType, title FROM crimeReports_news WHERE username = %s",
                          (username))
    signals_df = pd.DataFrame(signals_list)

    signals_df = signals_df[['date','time','location','crimeType','title']]
    signals_df.columns = ['Report date', 'Time of report', 'District', 'Type of crime', 'Description']
    # signals_df.rename(columns={"date": "Report date", "time": "Time of report", "location": "District", "crimeType": "Type of crime", "title": "Description"})

    return render_template("history.html", signals_df=signals_df.to_html(classes='historyTable',index=False))



def errorhandler(e):
    """Handle error"""
    if not isinstance(e, HTTPException):
        e = InternalServerError()
    return apology(e.name, e.code)


# Listen for errors
for code in default_exceptions:
    app.errorhandler(code)(errorhandler)

# def my_maps():

#     mapbox_access_token = 'pk.eyJ1IjoiYXNha2FrdXNoZXYiLCJhIjoiY2tmd25uZW9uMDFobTJxcndkdGNkYmwyZSJ9.Lm3qs2XtCG34WVXNOhWHgw'

#     return render_template('index.html', mapbox_access_token=mapbox_access_token)



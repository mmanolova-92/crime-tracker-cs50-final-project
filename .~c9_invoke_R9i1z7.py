import os, sys
import pandas as pd
from cs50 import SQL
from flask import Flask, flash, jsonify, redirect, render_template, request, session, make_response
from flask_session import Session
from tempfile import mkdtemp
from werkzeug.exceptions import default_exceptions, HTTPException, InternalServerError
from werkzeug.security import check_password_hash, generate_password_hash
from helpers import apology, login_required, lookup, usd
from scrapy import cmdline
import db_update

sys.path.insert(0, 'crimeAnalysis/crimeAnalysis/spiders/')

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

# Custom filter
app.jinja_env.filters["usd"] = usd

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

    # db_update.update()


    # return render_template("index.html", portfolio=portfolio.to_html(classes=["table table-striped"],index=False))
    if request.method == "POST":
        username = session["user_id"]
        crimeType_input = request.form.get("typeCrime")
        print(crimeType_input)
        crimeDate_input = request.form.get("crimeTime")
        print(crimeDate_input)
        # crimeTime_input = request.form.get("crimeTime").split()[1]
        # print(crimeTime_input)
        # # crimeLocation_input = request.form.get('crimeLocation')
        # crimeLatLong_input = request.form.get('crimeLatLong')
        # crimeTitle_input = request.form.get('crimeTitle')
        crimeDescription_input = request.form.get("crimeDescription")
        print(crimeDescription_input)

        db.execute("INSERT INTO crimeReports_users (date, crimeType, description, username) VALUES (%s, %s, %s, %s)", (crimeDate_input, crimeType_input, crimeDescription_input, username))
        return redirect("/")

    else:
        username = session["user_id"]

        reports_news = db.execute("SELECT title, location, latLong, date, time, crimeType FROM crimeReports_news")

        reports_users = db.execute("SELECT description, location, latLong, date, time, crimeType FROM crimeReports_users")

        reports_total = reports_news.append(reports_users)
        print(reports_total)

        # reports_news_df = pd.DataFrame(reports_news)

        #reports_news_df = reports_news_df[['title','location','latLong','date','time','crimeType']]

        #reports_news_count = reports_news_df.shape[0]

        tot_crimeType = db.execute("SELECT a.crimeType, a.crimeN, ifnull(b.crimeU,0) FROM (SELECT crimeType, count(id) as crimeN FROM crimeReports_news GROUP BY crimeType) as a LEFT JOIN (SELECT crimeType, count(id) as crimeU FROM crimeReports_users GROUP BY crimeType) as b ON a.crimeType = b.crimeType")

        tot_date = db.execute("SELECT a.date, a.crimeN, ifnull(b.crimeU,0) FROM (SELECT date, count(id) as crimeN FROM crimeReports_news GROUP BY date) as a LEFT JOIN (SELECT date, count(id) as crimeU FROM crimeReports_users GROUP BY date) as b ON a.date = b.date")

        tot_location = db.execute("SELECT a.location, a.crimeN, ifnull(b.crimeU,0) FROM (SELECT location, count(id) as crimeN FROM crimeReports_news GROUP BY location) as a LEFT JOIN (SELECT location, count(id) as crimeU FROM crimeReports_users GROUP BY location) as b ON a.location = b.location")

        return render_template("index.html", reports_news = reports_news, tot_crimeType = tot_crimeType, tot_date = tot_date, tot_location = tot_location, reports_users = reports_users, reports_total = reports_total)


    # else:
    #     return render_template("buy.html")

@app.route("/signalsLog")
@login_required
def signalsLog():
    """Show history of user-submitted signals"""

    username = session["user_id"]
    signals_list = db.execute("SELECT date, time, location, crimeType FROM crimeReports_users WHERE user_id = %s",
                          (username))
    signals_df = pd.DataFrame(signals_list)

    signals_df = signals_df[['date','time','location','crimeType']]

    return render_template("history.html", signals_df=signals_df.to_html(classes=["table table-striped"],index=False))



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



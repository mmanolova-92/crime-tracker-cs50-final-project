import os

from cs50 import SQL
from flask import Flask, flash, jsonify, redirect, render_template, request, session
from flask_session import Session
from tempfile import mkdtemp
from werkzeug.exceptions import default_exceptions, HTTPException, InternalServerError
from werkzeug.security import check_password_hash, generate_password_hash
import pandas as pd
from helpers import apology, login_required, lookup, usd

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

# Make sure API key is set
if not os.environ.get("API_KEY"):
    raise RuntimeError("API_KEY not set")


@app.route("/")
@login_required
def index():
    """Show portfolio of stocks"""

    username = session["user_id"]

    # portfolio_raw = db.execute("SELECT symbol, sum(n_shares) as shares FROM (SELECT distinct symbol, n_shares from transactions WHERE user_id = %s) group by symbol HAVING sum(n_shares) > 0",
    #                       (username))
    portfolio_raw = db.execute("SELECT symbol, sum(n_shares) as shares FROM transactions WHERE user_id = %s group by symbol HAVING sum(n_shares) > 0",
                          (username))
    current_balance_raw = db.execute("SELECT cash FROM users WHERE id = %s",
                          (username))
    current_balance = float(current_balance_raw[0]["cash"])


    if not portfolio_raw:
        # portfolio = pd.DataFrame([['Cash','','','',current_balance]], columns=['symbol','name','shares','price','total'])
        # portfolio = portfolio.append([{'symbol':'Total','name':'','shares':'','price':'','total':portfolio['total'].sum()}], ignore_index=True, sort=False)

        flash("You haven't bought any shares yet!")
        total_assets = current_balance
        return render_template("index.html", portfolio_raw=portfolio_raw, current_balance=current_balance, total_assets=float(total_assets))

    else:
        total_shares = 0

        for d in portfolio_raw:
            quote = lookup(d["symbol"])
            price = quote["price"]
            name = quote["name"]
            total = d["shares"] * price
            d.update({"name":name, "price":price, "total":total})
            total_shares = total_shares + float(price)

        total_assets = total_shares + current_balance
        print(portfolio_raw)
    #   portfolio = pd.DataFrame(portfolio_raw)

#         portfolio = portfolio[['symbol','name','shares','price','total']]
#         portfolio = portfolio.append([{'symbol':'CASH','name':'','shares':'','price':'','total':usd(current_balance)}], ignore_index=True, sort=False)
#         portfolio = portfolio.append([{'symbol':'Total','name':'','shares':'','price':'','total':usd(total_assets)}], ignore_index=True, sort=False)
#
        return render_template("index.html", portfolio_raw=portfolio_raw, current_balance=current_balance, total_assets=float(total_assets))

    # return render_template("index.html", portfolio=portfolio.to_html(classes=["table table-striped"],index=False))

@app.route("/buy", methods=["GET", "POST"])
@login_required
def buy():

    """Buy shares of stock"""

    if request.method == "POST":

        symbol = request.form.get("symbol")
        n_shares = request.form.get("shares")

        if (not symbol or not n_shares):
            return apology("Invalid entries", 400)

        if not n_shares.isdigit():
            return apology("invalid ticker", 400)

        n_shares = int(n_shares)

        stock_quote = lookup(symbol)

        if not stock_quote:
            return apology("ticker is invalid", 400)

        value_raw = float(stock_quote["price"])
        stock_name = stock_quote['name']

        if not value_raw:
            return apology("ticker is invalid", 400)

        total = n_shares * value_raw
        username = session["user_id"]
        value = usd(value_raw)

        current_balance_raw = db.execute("SELECT cash FROM users WHERE id = %s",
                          (username))
        current_balance = current_balance_raw[0]["cash"]

        if current_balance < total:
            return apology("Insufficient account balance")

        remaining_balance = current_balance - total

        db.execute("INSERT INTO transactions (user_id,current_balance,symbol,price,n_shares,total,remaining_balance, operation_type) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)", (username, current_balance, symbol, value, n_shares, total, remaining_balance, "buy"))
        db.execute("UPDATE users SET cash = %s where id = %s", (remaining_balance, username))

        flash("Bought! Congratulations, you bought %s shares of %s at a price of %s" % (n_shares, stock_name, value))

        return redirect("/")

    else:
        return render_template("buy.html")


@app.route("/check", methods=["GET"])
def check():
    """Return true if username available, else false, in JSON format"""
    username = session['username']
    # username = g.user.username

    existing_users_raw = db.execute("SELECT distinct username FROM users")
    existing_users = [d['username'] for d in existing_users_raw if 'username' in d]
    if username not in existing_users:
        return jsonify({'status': "true"}), 400
    else:
        return jsonify({'status': "false"}), 200

@app.route("/history")
@login_required
def history():
    """Show history of transactions"""

    username = session["user_id"]
    share_list = db.execute("SELECT datetime, symbol, price, n_shares FROM transactions WHERE user_id = %s",
                          (username))
    stocks_df = pd.DataFrame(share_list)

    stocks_df = stocks_df[['datetime','symbol','n_shares','price']]

    return render_template("history.html", stocks_df=stocks_df.to_html(classes=["table table-striped"],index=False))

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
        rows = db.execute("SELECT * FROM users WHERE username = :username",
                          username=request.form.get("username"))

        # Ensure username exists and password is correct
        if len(rows) != 1 or not check_password_hash(rows[0]["hash"], request.form.get("password")):
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


@app.route("/quote", methods=["GET", "POST"])
@login_required
def quote():
    """Get stock quote."""

    if request.method == "POST":

        # get symbol value

        symbol = request.form.get("symbol")

        if (not symbol):
            return apology("Invalid entries", 400)

        stock_quote = lookup(symbol)

        if not stock_quote:
            return apology("ticker is invalid", 400)

        print(stock_quote)
        value_raw = float(stock_quote["price"])
        value = usd(value_raw)


        # redirect user to quoted.html

        return render_template("quoted.html", value=value)

    else:
        return render_template("quote.html")




@app.route("/register", methods=["GET", "POST"])
def register():

    """Register user"""
    if request.method == "GET":
        return render_template("register.html")

    else:
        username = request.form.get("username")
        password = request.form.get("password")
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

        db.execute("INSERT INTO users (username,hash) VALUES (%s, %s)", (username, hash_password))

        return redirect("/login")

@app.route("/sell", methods=["GET", "POST"])
@login_required
def sell():
    """Sell shares of stock"""
    if request.method == "POST":

        username = session["user_id"]
        symbol = request.form.get("symbol")
        available_shares_raw = db.execute("SELECT distinct symbol, sum(total) as sum_total FROM transactions WHERE symbol = %s", symbol)
        available_shares = available_shares_raw[0]['sum_total']
        n_shares = int(request.form.get("shares"))
        stock_quote = lookup(symbol)
        value = stock_quote["price"]
        total = n_shares * value

        current_balance_raw = db.execute("SELECT cash FROM users WHERE id = %s",
                          (username))
        current_balance = current_balance_raw[0]["cash"]

        if (not symbol or not n_shares):
            return apology("Please enter a valid stock and number of shares")

        if (available_shares < n_shares):
            return apology("You do not have enough shares")

        remaining_balance = current_balance + total

        db.execute("INSERT INTO transactions (user_id,current_balance,symbol,price,n_shares,total,remaining_balance,operation_type) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)", (username, current_balance, symbol, value, -n_shares, total, remaining_balance, "sell"))
        db.execute("UPDATE users SET cash = %s where id = %s", (remaining_balance, username))

        return redirect("/")
    else:
        username = session["user_id"]
        share_list = db.execute("SELECT symbol FROM (SELECT symbol, sum(total) as sum_total FROM (SELECT distinct symbol, total from transactions WHERE user_id = %s) group by symbol) WHERE sum_total > 0",
                          (username))
        stocks = [d['symbol'] for d in share_list if 'symbol' in d]
        return render_template("sell.html", stocks = stocks)


def errorhandler(e):
    """Handle error"""
    if not isinstance(e, HTTPException):
        e = InternalServerError()
    return apology(e.name, e.code)


# Listen for errors
for code in default_exceptions:
    app.errorhandler(code)(errorhandler)

from cs50 import SQL
from flask import Flask, flash, redirect, render_template, request, session, url_for
from flask_session import Session
from passlib.apps import custom_app_context as pwd_context
from tempfile import mkdtemp

from helpers import *
import datetime

# configure application
app = Flask(__name__)

# ensure responses aren't cached
if app.config["DEBUG"]:
    @app.after_request
    def after_request(response):
        response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
        response.headers["Expires"] = 0
        response.headers["Pragma"] = "no-cache"
        return response

# custom filter
app.jinja_env.filters["usd"] = usd

# configure session to use filesystem (instead of signed cookies)
app.config["SESSION_FILE_DIR"] = mkdtemp()
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# configure CS50 Library to use SQLite database
db = SQL("sqlite:///finance.db")

@app.route("/")
@login_required
def index():
    portfolio_symbols = db.execute("SELECT shares_count, symbol,total_cost \
                                    FROM portfolio WHERE id = :id", \
                                    id=session["user_id"])
    
    # create a temporary variable to store TOTAL worth ( cash + share)
    total_cash = 0
    
    # update each symbol prices and total
    for portfolio_symbol in portfolio_symbols:
        symbol = portfolio_symbol["symbol"]
        shares = portfolio_symbol["shares_count"]
        stock = lookup(symbol)
        total = stock["price"]*shares
        total_cash += total
        db.execute("UPDATE portfolio SET unit_cost=:price, \
                    total_cost=:total WHERE id=:id AND symbol=:symbol", \
                    price=usd(stock["price"]), \
                    total=usd(total), id=session["user_id"], symbol=symbol)
    
    # update user's cash in portfolio
    updated_cash = db.execute("SELECT usercash FROM users \
                               WHERE userid=:id", id=session["user_id"])
    
    # update total cash -> cash + shares worth
    total_cash += updated_cash[0]["usercash"]
    
    # print portfolio in index homepage
    updated_portfolio = db.execute("SELECT * from portfolio \
                                    WHERE id=:id", id=session["user_id"])
                                    
    return render_template("index.html", stocks=updated_portfolio, \
                            cash=usd(updated_cash[0]["usercash"]), total= usd(total_cash) )
    

@app.route("/buy", methods=["GET", "POST"])
@login_required
def buy():
    """Buy shares of stock."""
    if request.method=="GET":
        return render_template("buy.html")
    else:
        # ensure proper symbol
        stock = lookup(request.form.get("symbol"))
        if not stock:
            return apology("Invalid Symbol")
        
        # ensure proper number of shares
        try:
            shares = int(request.form.get("share"))
            if shares < 0:
                return apology("Shares must be positive integer")
        except:
            return apology("Shares must be positive integer")
        
        # select user's cash
        balance = db.execute("SELECT usercash FROM users WHERE userid = :id", \
                            id=session["user_id"])
        
        # check if enough money to buy
        if not balance or float(balance[0]["usercash"]) < stock["price"] * shares:
            return apology("Not enough money")
        
        # update history
        db.execute("INSERT INTO transactions (symbol, shares_count, cost, userid) \
                    VALUES(:symbol, :shares, :price, :id)", \
                    symbol=stock["symbol"], shares=shares, \
                    price=usd(stock["price"]), id=session["user_id"])
                       
        # update user cash               
        db.execute("UPDATE users SET usercash = usercash - :purchase WHERE userid = :id", \
                    id=session["user_id"], \
                    purchase=stock["price"] * float(shares))
                        
        # Select user shares of that symbol
        user_shares = db.execute("SELECT shares_count FROM portfolio \
                           WHERE id = :id AND symbol=:symbol", \
                           id=session["user_id"], symbol=stock["symbol"])
                           
        # if user doesn't has shares of that symbol, create new stock object
        if not user_shares:
            db.execute("INSERT INTO portfolio (pname, shares_count, unit_cost, total_cost, symbol, id) \
                        VALUES(:name, :shares, :price, :total, :symbol, :id)", \
                        name=stock["name"], shares=shares, price=usd(stock["price"]), \
                        total=usd(shares * stock["price"]), \
                        symbol=stock["symbol"], id=session["user_id"])
                        
        # Else increment the shares count
        else:
            shares_total = user_shares[0]["shares_count"] + shares
            db.execute("UPDATE portfolio SET shares_count=:shares \
                        WHERE id=:id AND symbol=:symbol", \
                        shares=shares_total, id=session["user_id"], \
                        symbol=stock["symbol"])
        
        # return to index
        return redirect(url_for("index"))
        
        
       

@app.route("/history")
@login_required
def history():
    """Show history of transactions."""
    histories = db.execute("SELECT * from transactions WHERE userid=:id", id=session["user_id"])
    
    return render_template("history.html", histories=histories)
@app.route("/login", methods=["GET", "POST"])
def login():
    """Log user in."""

    # forget any user_id
    session.clear()

    # if user reached route via POST (as by submitting a form via POST)
    if request.method == "POST":

        # ensure username was submitted
        if not request.form.get("username"):
            return apology("must provide username")

        # ensure password was submitted
        elif not request.form.get("password"):
            return apology("must provide password")

        # query database for username
        rows = db.execute("SELECT * FROM users WHERE username = :username", username=request.form.get("username"))

        # ensure username exists and password is correct
        if len(rows) != 1 or not pwd_context.verify(request.form.get("password"), rows[0]["userhash"]):
            return apology("invalid username and/or password")

        # remember which user has logged in
        session["user_id"] = rows[0]["userid"]

        # redirect user to home page
        return redirect(url_for("index"))

    # else if user reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("login.html")

@app.route("/logout")
def logout():
    """Log user out."""

    # forget any user_id
    session.clear()

    # redirect user to login form
    return redirect(url_for("login"))

@app.route("/quote", methods=["GET", "POST"])
@login_required
def quote():
    """Get stock quote."""
    if request.method == "POST":
        rows = lookup(request.form.get("symbol"))
        
        if not rows:
            return apology("Invalid Symbol")
            
        return render_template("Quoted.html", stock=rows)
    
    else:
        return render_template("quote.html")

@app.route("/register", methods=["GET", "POST"])
def register():
    """Register user."""
    if request.method == "POST":
        
        # ensure username was submitted
        if not request.form.get("username"):
            return apology("Must provide username")
            
        # ensure password was submitted    
        elif not request.form.get("password"):
            return apology("Must provide password")
        
        # ensure password and verified password is the same
        elif request.form.get("password") != request.form.get("conformpassword"):
            return apology("password doesn't match")
        
        # insert the new user into users, storing the hash of the user's password
        result = db.execute("INSERT INTO users (username, userhash) \
                             VALUES(:username, :hash)", \
                             username=request.form.get("username"), \
                             hash=pwd_context.encrypt(request.form.get("password")))
                 
        if not result:
            return apology("Username already exist")
        
        # remember which user has logged in
        session["user_id"] = result

        # redirect user to home page
        return redirect(url_for("index"))
    
    else:
        return render_template("register.html")            

@app.route("/sell", methods=["GET", "POST"])
@login_required
def sell():
    """Sell shares of stock."""
    if request.method=="GET":
        return render_template("sell.html")
    else:
        # ensure proper symbol
        stock = lookup(request.form.get("symbol"))
        if not stock:
            return apology("Invalid Symbol")
        
        # ensure proper number of shares
        try:
            shares = int(request.form.get("share"))
            if shares < 0:
                return apology("Shares must be positive integer")
        except:
            return apology("Shares must be positive integer")
        
        # select user's cash
        balance = db.execute("SELECT shares_count FROM portfolio WHERE id = :id and symbol=:symbol", \
                         id=session["user_id"],symbol=stock["symbol"])
        #share=shares-balance
        # check if enough money to buy
        if not balance or int(balance[0]["shares_count"]) <  shares:
           return apology("Not enough Shares")
        
        # update history
        
        db.execute("INSERT INTO transactions (symbol, shares_count, cost, userid) \
                    VALUES(:symbol, :shares, :price, :id)", \
                    symbol=stock["symbol"], shares=-shares, \
                    price=usd(stock["price"]), id=session["user_id"])
                       
        # update user cash               
        db.execute("UPDATE users SET usercash = usercash + :purchase WHERE userid = :id", \
                    id=session["user_id"], \
                    purchase=stock["price"] * float(shares))
                        
        # Select user shares of that symbol
        user_shares = db.execute("SELECT shares_count FROM portfolio \
                           WHERE id = :id AND symbol=:symbol", \
                           id=session["user_id"], symbol=stock["symbol"])
                           
        # if user doesn't has shares of that symbol, create new stock object
        shares_count=balance[0]["shares_count"]-shares
        
        if shares_count<=0:
             db.execute("DELETE FROM portfolio \
                        WHERE id=:id AND symbol=:symbol", \
                        id=session["user_id"], \
                        symbol=stock["symbol"])
        else:
            db.execute("UPDATE portfolio SET shares_count=:shares \
                    WHERE id=:id AND symbol=:symbol", \
                    shares=shares_count, id=session["user_id"], \
                    symbol=stock["symbol"])
            
       
        
        # return to index
        return redirect(url_for("index"))
        
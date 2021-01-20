import os
import requests
import json
import string
import random
import config

from cs50 import SQL
from newsapi import NewsApiClient
from flask import Flask, flash, redirect, render_template, request, session
from flask_session import Session
from datetime import date

from tempfile import mkdtemp
from werkzeug.exceptions import default_exceptions, HTTPException, InternalServerError
from werkzeug.security import check_password_hash, generate_password_hash
from functools import wraps


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





def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if session.get("user_id") is None:
            return redirect("/login")
        return f(*args, **kwargs)
    return decorated_function


db = SQL("sqlite:///compress.db")


@app.route("/")

def index():
    return render_template("index.html")

@app.route("/news", methods=["GET", "POST"])
@login_required
def news():
    print(request.method)
    if request.method == "GET":
        today = date.today()
        d = today.strftime("%Y-%m-%d")
        key = config.api_key
        newsapi = NewsApiClient(api_key='{0}'.format(key))
        keyword = 'security'
        url = ('http://newsapi.org/v2/everything?'
        'q={0}&'
        'from={1}&'
        'sortBy=popularity&'
        'apiKey={2}'.format(keyword, d, key))
        data_response = requests.get(url)
        response_json = data_response.json()
        articles = response_json['articles']

        with open('request.json', 'w') as outfile:
            json.dump(articles, outfile, ensure_ascii = False)
        return render_template("news.html", articles=articles, keyword = keyword)
    else:
        with open('request.json') as json_file:
            articles = json.load(json_file)
        return render_template("news.html", articles = articles)

@app.route("/passwords")
@login_required
def passwords():
    query_passwords = db.execute("SELECT * FROM passwords WHERE user_id = ?", session["user_id"])
    session['passwords'] = query_passwords
    return render_template("passwords.html", query_passwords = query_passwords)


@app.route("/generate_password")
@login_required
def generate_password():
    password = f'{string.ascii_letters}{string.digits}{string.punctuation}'
    password = list(password)
    random.shuffle(password)
    random_password = random.choices(password, k=12)
    random_password = ''.join(random_password)
    print(random_password)
    return render_template("passwords.html")

@app.route("/create", methods=["GET", "POST"])
@login_required
def create():
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")
        service = request.form.get("service")
        url = request.form.get("url")
        category = request.form.get("category")
        if 'generate' in request.form:
            password = f'{string.ascii_letters}{string.digits}{string.punctuation}'
            password = list(password)
            random.shuffle(password)
            random_password = random.choices(password, k=12)
            random_password = ''.join(random_password)
            return render_template("create.html", password = random_password, username = username, service = service, url = url, category = category)
        if not request.form.get("username"):
            print("username is missing")
        if not request.form.get("password"):
            print("password is missing")
        if not request.form.get("password") == request.form.get("confirmation"):
            print("password not equal to confirmation")

        db.execute("INSERT INTO passwords (user_id, username, password, service, url, category) VALUES(?, ?, ?, ?, ?, ?)", session["user_id"], username, password, service, url, category)
        return render_template("passwords.html")
    else:
        return render_template("create.html")

@app.route("/edit", methods=["GET", "POST"])
@login_required
def edit():
    if request.method == "POST":
        if not request.form.get("username"):
            print("username fehlt")
        if not request.form.get("password"):
            print("password fehlt")
        if not request.form.get("password") == request.form.get("confirmation"):
            print("password not equal to confirmation")
        username = request.form.get("username")
        password = request.form.get("password")
        service = request.form.get("service")
        url = request.form.get("url")
        category = request.form.get("category")
        confirmation = request.form.get("confirmation")
        return render_template("edit.html", username = username, password = password, service = service, url = url, category = category, confirmation = confirmation)
    else:
        return render_template("edit.html")

@app.route("/change", methods=["GET", "POST"])
@login_required
def change():
    if request.method == "POST":
        if 'delete' in request.form:
            service = request.form.get("service")
            db.execute("DELETE FROM passwords where user_id = ? AND service = ?", session["user_id"], service)
            return render_template("passwords.html")
        else:
            if not request.form.get("username"):
                print("username fehlt")
            if not request.form.get("password"):
                print("password fehlt")
            if not request.form.get("password") == request.form.get("confirmation"):
                print("password not equal to confirmation")
            username = request.form.get("username")
            password = request.form.get("password")
            service = request.form.get("service")
            url = request.form.get("url")
            category = request.form.get("category")
            confirmation = request.form.get("confirmation")
            db.execute("UPDATE passwords set username = ?, password = ?, url = ?, category = ? where user_id = ? AND service = ?", username, password, url, category, session["user_id"], service)
            return render_template("passwords.html")
    else:
        return render_template("passwords.html")

@app.route("/items", methods=["GET", "POST"])
@login_required
def items():
    selected_item = request.args.get('type')
    if selected_item == "all":
        query_passwords = db.execute("SELECT * FROM passwords WHERE user_id = ?", session["user_id"])
        session['passwords'] = query_passwords
    if selected_item == "socialmedia":
        query_passwords = db.execute("SELECT * FROM passwords WHERE user_id = ? AND category = ?", session["user_id"], "Social Media")
        session['passwords'] = query_passwords
    if selected_item == "finance":
        query_passwords = db.execute("SELECT * FROM passwords WHERE user_id = ? AND category = ?", session["user_id"], "Finance")
        session['passwords'] = query_passwords
    if selected_item == "education":
        query_passwords = db.execute("SELECT * FROM passwords WHERE user_id = ? AND category = ?", session["user_id"], "Education")
        session['passwords'] = query_passwords
    if selected_item == "newspaper":
        query_passwords = db.execute("SELECT * FROM passwords WHERE user_id = ? AND category = ?", session["user_id"], "Newspaper")
        session['passwords'] = query_passwords
    if not query_passwords:
        return render_template("passwords.html", selected_item = selected_item)
    return render_template("passwords.html", selected_item = selected_item, query_passwords = query_passwords)

@app.route("/details", methods=["GET", "POST"])
@login_required
def details():
    service = request.args.get('type')
    query_services = db.execute("SELECT * FROM passwords WHERE user_id = ? AND service = ?", session["user_id"], service)
    if not query_services:
        return render_template("passwords.html", service = service)
    return render_template("passwords.html", service = service, query_services = query_services, session_passwords = session['passwords'])



@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
# Ensure username was submitted
        if not request.form.get("username"):
           error = "Missing username. Please try again!"
           return render_template("register.html", error = error)
        # Ensure password was submitted
        if not request.form.get("password"):
           error = "Missing password. Please try again!"
           return render_template("register.html", error = error)
        if not request.form.get("password") == request.form.get("confirmation"):
           error = "Password and Username did not match. Please try again!"
           return render_template("register.html", error = error)
        username = request.form.get("username")
        password = generate_password_hash(request.form.get("password"))
        existing_user = db.execute("SELECT * FROM users WHERE username = ?", username)
        if not existing_user:
           # Query database for username
           db.execute("INSERT INTO users (username, hash) VALUES(?, ?)", username, password)
           users = db.execute("SELECT * FROM users")
           return redirect("/")
        error = "Username already exists. Please try again!"
        return render_template("register.html", error = error)
     # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("register.html")

@app.route("/login", methods=["GET", "POST"])
def login():
    # Forget any user_id
    session.clear()

    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":

        # Ensure username was submitted
        if not request.form.get("username"):
            error = "Missing username. Please try again!"
            return render_template("login.html", error = error)

        # Ensure password was submitted
        elif not request.form.get("password"):
            error = "Missing password. Please try again!"
            return render_template("login.html", error = error)

        # Query database for username
        rows = db.execute("SELECT * FROM users WHERE username = ?", request.form.get("username"))

        # Ensure username exists and password is correct
        if len(rows) != 1 or not check_password_hash(rows[0]["hash"], request.form.get("password")):
            error = "Invalid username or password. Please try again!"
            return render_template("login.html", error = error)

        # Remember which user has logged in
        session["user_id"] = rows[0]["id"]
        session["username"] = rows[0]["username"]

        with open('request2.json') as json_file:
            articles = json.load(json_file)

        # Redirect user to home page
        return render_template("index.html", articles = articles)

    # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("login.html")

@app.route("/logout")
def logout():
    # Forget any user_id
    session.clear()

    # Redirect user to login form
    return redirect("/")

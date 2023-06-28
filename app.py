# In-built imports
from datetime import datetime
import os
import json
import webbrowser

# External imports
from flask import Flask, flash, render_template, url_for, request, redirect, session
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import current_user, login_user, logout_user, login_required, LoginManager, UserMixin
import pyrebase


app = Flask(__name__)
app.secret_key = 'super secret key'

# Firebase config
with open('firebase_config.json') as config_file:
    firebase_config = dict(json.load(config_file))
firebase = pyrebase.initialize_app(firebase_config)
auth = firebase.auth()

# login_manager = LoginManager(app)

# @login_manager.user_loader
# def user_loader(username):
#     if os.path.exists(f"users/{username}"):
#         with open(f"users/{username}", 'r') as f:
#             user_data = json.load(f)
#         return user_data

@app.route('/')
def home():
    json_files = os.listdir("articles")
    articles = {}
    for file in json_files:
        file_path = os.path.join("articles", file)
        with open(file_path, 'r') as f:
            json_data = json.load(f)
            articles[file] = json_data
    return render_template('home.html', articles=articles)

@app.route('/about')
def about():
    return render_template('about.html')

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')

        # {kind, idToken, email, refreshToken, expiresIn, localId}
        signup_user = auth.create_user_with_email_and_password(email, password)
        
        flash("User created", category='message')
        return redirect(url_for("home"))
    return render_template('signup.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if 'user' in session:
        return flash(f"{session['user']} is already logged in!")
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        try:
            login_user = auth.sign_in_with_email_and_password(email, password)
            auth.send_email_verification(login_user['idToken'])
            session['user'] = email
        except:
            flash("Invalid username or password")
            return redirect(url_for("login"))
        flash("User logged in")
        return redirect(url_for("home"))
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.pop('user')
    return redirect(url_for('home'))

@app.route("/contact", methods=['GET', 'POST'])
def contact():
    if request.method == "POST":
        form_data = dict(request.form)
        sender = request.form.get('name')
        email = request.form.get('email')
        title = request.form.get('title')
        message = request.form.get('message')
        priority = request.form.get('priority')
        
        if not os.path.exists(f"feedback/{sender}"):
            os.makedirs(f"feedback/{sender}")
        with open(f"feedback/{sender}/{datetime.now().timestamp()}.json", 'w') as f:
            json.dump(form_data, f)
        flash("Feedback recorded. Thanks for reaching out!")
        return redirect(url_for('index'))
    
    return render_template("contact.html")

@app.route('/contribute', methods=['GET', 'POST'])
def contribute():
    if request.method == 'POST':
        form_data = dict(request.form)
        Author = request.form.get('Author').replace(" ","_")
        Title = request.form.get('Title')
        Message = request.form.get('Message')
        
        form_data = {
            "Author": Author,
            "Title": Title,
            "Date_created": str(datetime.now().today()),
            "Message": Message,
        }

        with open(f"articles/{Author}_{datetime.now().timestamp()}.json", 'w') as f:
            json.dump(form_data, f)
        flash("Thank you for contributing!")
        return redirect(url_for("index"))
    return render_template('contribute.html')

@app.route('/article/<string:file_name>', methods=['GET', 'POST'])
def article(file_name):
    if request.method == 'GET':
        file_path = os.path.join("articles", file_name)
        if os.path.exists(file_path):
            with open(file_path, 'r') as f:
                file_data = json.load(f)
        else:
            flash("ERROR")
            return redirect(url_for('index'))
    return render_template("article.html", file_data=file_data)

if __name__ == "__main__":
    app.run(debug=True)
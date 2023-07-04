# In-built imports
from datetime import datetime
import os
import json

# External imports
from flask import Flask, flash, render_template, url_for, request, redirect, session
import pyrebase
from pymongo.mongo_client import MongoClient
from pymongo.server_api import ServerApi


app = Flask(__name__)
app.secret_key = 'super secret key'

# Firebase config
with open('firebase_config.json') as config_file:
    firebase_config = dict(json.load(config_file))
firebase = pyrebase.initialize_app(firebase_config)
auth = firebase.auth()

# DB connection
db_client = MongoClient(os.environ.get('MONGODB_URI'), server_api=ServerApi('1'))
db = db_client['blog_site']
db_collection = db['blog_data']


@app.route('/')
def home():
    # Get some random articles and pass them in a dict
    random_users = db_collection.aggregate([
        { "$sample": { "size": 7 } }
    ])
    authors = []
    for document in random_users:
        authors.append(document)
    
    return render_template('home.html', authors=authors)

@app.route('/about')
def about():
    return render_template('about.html')

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        username = request.form.get('username')
        full_name = request.form.get('full_name')
        email = request.form.get('email')
        password = request.form.get('password')
        try:
            # {kind, idToken, email, refreshToken, expiresIn, localId}
            signup_user = auth.create_user_with_email_and_password(email, password)
            auth.send_email_verification(signup_user['idToken'])
            
            # Adding user in db
            user_data = {
                "username": username,
                "full_name": full_name,
                "email": email,
                "blogs":[]
            }
            inserted_data = db_collection.insert_one(user_data)
        except:
            flash("User already exists!")
            return redirect(url_for("home"))
        
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
            user_data = db_collection.find({"email": email})
            for document in user_data:
                session['user'] = document.get('username')
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
        return redirect(url_for('home'))
    
    return render_template("contact.html")

@app.route('/contribute', methods=['GET', 'POST'])
def contribute():
    if request.method == 'POST':
        user_data = db_collection.find_one({"username": session['user']})
        form_data = {
            "title": request.form.get('title'),
            "author_name": user_data.full_name,
            "author_username": session['user'],
            "date_created": str(datetime.now().today()),
            "content": request.form.get('content'),
        }

        db_collection.update_one(
            {"username": session['user']},
            {"$push": {"blogs": form_data}},
            upsert=True
        )
        flash("Thank you for contributing!")
        return redirect(url_for("home"))
    return render_template('contribute.html')

@app.route('/article', methods=['GET', 'POST'])
def article():
    if request.method == 'GET':
        try:
            blog_title = request.args.get('blog_title')
            author_username = request.args.get('author_username')
            blog = db_collection.find_one({
                "username": author_username,
                "blogs.title": blog_title
            }, {
                "blogs.$": 1
            })
            if blog:
                blog_data = blog["blogs"][0]
        except:
            flash("Error retrieving the document")
            return redirect(url_for("home"))

    return render_template("article.html", blog_data=blog_data)

if __name__ == "__main__":
    app.run(debug=True)
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
user_collection = db['user_data']
blog_collection = db['blog_data']


@app.route('/')
def home():
    if 'user' in session:
        # Recommend articles to user, unfinished yet so will do the same as else

        # Get some random articles and pass them in a dict
        random_blogs = blog_collection.aggregate([
            { "$sample": { "size": 7 } }
        ])
        blogs = []
        for document in random_blogs:
            blogs.append(document)
    else:
        # Get some random articles and pass them in a dict
        random_blogs = blog_collection.aggregate([
            { "$sample": { "size": 7 } }
        ])
        blogs = []
        for document in random_blogs:
            blogs.append(document)
    
    return render_template('home.html', blogs=blogs)

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
                "blogs":[],
                "view_history": []
            }
            inserted_data = user_collection.insert_one(user_data)
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
            user_document = user_collection.find({"email": email})
            for document in user_document:
                session['user'] = document.get('username')
        except Exception as e:
            flash("Invalid username or password")
            return redirect(url_for("login"))
        flash("User logged in")
        return redirect(url_for("home"))
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.pop('user')
    return redirect(url_for('home'))

@app.route('/contribute', methods=['GET', 'POST'])
def contribute():
    if request.method == 'POST':
        user_data = user_collection.find_one({"username": session['user']})
        
        # Create a new blog document
        blog_data = {
            "title": request.form.get('title'),
            "author_name": user_data['full_name'],
            "author_username": session['user'],
            "date_created": str(datetime.now().today()),
            "content": request.form.get('content'),
        }

        # Insert the blog document into the blog_data collection
        result = blog_collection.insert_one(blog_data)
        
        # Retrieve the inserted blog's _id
        inserted_blog_id = result.inserted_id

        # Update the user_data document with the reference to the inserted blog's _id
        user_collection.update_one(
            {"username": session['user']},
            {"$push": {"blogs": {"$oid":inserted_blog_id}}},
            upsert=True
        )

        flash("Thank you for contributing!")
        return redirect(url_for("home"))
    return render_template('contribute.html')

@app.route('/author', methods=['GET', 'POST'])
def author():
    if request.method == 'GET':
        author_username = request.args.get('author_username')
        author_data =  user_collection.find_one({"username": author_username})
        blog_data = []
        blog_objects = blog_collection.find({"_id": {"$in": author_data['blogs']}})
        for blog in blog_objects:
            blog_data.append(blog)
    return render_template("author.html", author_data=author_data, blog_data=blog_data)

@app.route('/article', methods=['GET', 'POST'])
def article():
    if request.method == 'GET':
        try:
            blog_title = request.args.get('blog_title')
            author_username = request.args.get('author_username')
            blog = blog_collection.find_one({
                "title": blog_title,
                "author_username": author_username,
            })
        except:
            flash("Error retrieving the document")
            return redirect(url_for("home"))
        if 'user' in session:
            # Add article to view history
            user_collection.update_one(
                {"username": session['user']},
                {"$push": {"view_history":{"title": blog_title, "author_username": author_username, "date_viewed": str(datetime.now().today())},}})

    return render_template("article.html", blog_data=blog)

if __name__ == "__main__":
    app.run(debug=True)
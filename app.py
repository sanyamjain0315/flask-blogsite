from flask import Flask, flash, render_template, url_for, request, redirect
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import current_user, login_user, logout_user, login_required, LoginManager, UserMixin
from datetime import datetime
import os
import json
app = Flask(__name__)
app.secret_key = 'super secret key'
login_manager = LoginManager(app)

@login_manager.user_loader
def user_loader(username):
    if os.path.exists(f"users/{username}"):
        with open(f"users/{username}", 'r') as f:
            user_data = json.load(f)
        return user_data

@app.route('/')
def index():
    json_files = os.listdir("articles")
    articles = {}
    for file in json_files:
        file_path = os.path.join("articles", file)
        with open(file_path, 'r') as f:
            json_data = json.load(f)
            articles[file] = json_data
    return render_template('index.html', articles=articles)

@app.route('/about')
def about():
    return render_template('about.html')

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
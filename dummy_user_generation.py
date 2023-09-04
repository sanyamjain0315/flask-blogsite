import random
import faker
from datetime import datetime
import pymongo
import os

fake = faker.Faker()

# Function to generate a random blog entry
def generate_blog_entry():
    title = fake.sentence(nb_words=6, variable_nb_words=True)
    author_name = fake.name()
    author_username = fake.user_name()
    date_created = fake.date_time_this_decade()
    content = fake.paragraphs(nb=5)
    return {
        "title": title,
        "author_name": author_name,
        "author_username": author_username,
        "date_created": date_created,
        "content": content,
    }

# Function to generate view history for a user
def generate_view_history(blogs):
    num_viewed = random.randint(0, min(len(blogs), 5))
    blogs_corpus = []
    for n_user in blogs:
        for blog in n_user['blogs']:
            blogs_corpus.append(blog)
    viewed_blogs = random.sample(blogs_corpus, num_viewed)
    return [{"title":blog["title"], "author_username":blog["author_username"]} for blog in viewed_blogs]

# Establish a connection to MongoDB
client = pymongo.MongoClient(os.environ.get('MONGODB_URI'))
db = client["blog_site"]
collection = db["blog_data"]

# Generate dummy data for multiple users
users = []
for _ in range(100):
    user = {
        "username": fake.user_name(),
        "full_name": fake.name(),
        "email": fake.email(),
        "blogs": [generate_blog_entry() for _ in range(random.randint(0, 5))],
        "view_history": []
    }
    users.append(user)

# Populate view_history for each user
for user in users:
    user["view_history"] = generate_view_history(users)

# Insert the generated data into MongoDB
collection.insert_many(users)


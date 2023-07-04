# Script to generate dummy data for mongodb database

from pymongo import MongoClient
from faker import Faker
from datetime import datetime
import os


# Set up the MongoDB client
client = MongoClient(os.environ.get('MONGODB_URI'))
db = client['blog_site']
db_collection = db['blog_data']

# Create a Faker instance for generating fake data
fake = Faker()

# Generate 100 sample blogs
for _ in range(100):
    # Generate random user details
    username = fake.user_name()
    full_name = fake.name()
    email = fake.email()

    # Generate a random number of blogs for each user
    num_blogs = fake.random_int(min=1, max=5)

    # Generate blogs for the user
    blogs = []
    for _ in range(num_blogs):
        blog = {
            "title": fake.sentence(nb_words=5),
            "author_name": full_name,
            "author_username": username,
            "date_created": str(datetime.now().today()),
            "content": fake.paragraph(nb_sentences=5),
        }
        blogs.append(blog)

    # Create the user document with blogs
    user_data = {
        "username": username,
        "full_name": full_name,
        "email": email,
        "blogs": blogs
    }

    # Insert the user document into the collection
    db_collection.insert_one(user_data)

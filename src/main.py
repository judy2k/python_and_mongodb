from datetime import datetime
import os

# Import the `pprint` function to print nested data:
from pprint import pprint

from dotenv import load_dotenv

import bson
import pymongo
from pymongo import MongoClient


def print_title(title, underline_char="="):
    """
    Utility function to print a title with an underline.
    """
    print()  # Print a blank line
    print(title)
    print(underline_char * len(title))  # Print an underline made of `underline_char`


# Load config from a .env file:
load_dotenv(verbose=True)
MONGODB_URI = os.environ["MONGODB_URI"]

# Connect to your MongoDB cluster:
client = MongoClient(MONGODB_URI)

# Get a reference to the "recipes" collection:
db = client.get_database("cocktails")
recipes = db.get_collection("recipes")

# recipes.insert_one(
#     {
#         "name": "Dodgy Cocktail",
#         "ingredients": [
#             {
#                 "name": "Water",
#                 "quantity": {"unit": "ml", "amount": 30},
#             }
#         ],
#         "instructions": [
#             "Pour yourself some water from the tap.",
#         ],
#     }
# )

print_title("All Documents")
cursor = recipes.find(
    sort=[
        ("name", pymongo.ASCENDING),
    ],
)
for recipe in cursor:
    print("Cocktail:", recipe["name"])

print_title("Negroni Sbagliato")
query = {"name": "Negroni Sbagliato"}
cursor = recipes.find(query)
for recipe in cursor:
    pprint(recipe)

"""
{'_id': ObjectId('5f7b4b6204799f5cf837b1e1'),
 'garnish': 'Orange Twist',
 'ingredients': [{'name': 'Campari', 'quantity': {'unit': 'ml', 'value': 30}},
                 {'name': 'Sweet Vermouth',
                  'quantity': {'unit': 'ml', 'value': 30}},
                 {'name': 'Prosecco', 'quantity': {'unit': 'ml', 'value': 30}}],
 'instructions': ['Stir Campari & vermouth with ice',
                  'Pour into a champagne flute',
                  'Add wine & gently combine',
                  'Serve with orange twist'],
 'name': 'Negroni Sbagliato',
"""

print_title("Vodka Cocktails")
query = {"ingredients": {"$elemMatch": {"name": "Vodka"}}}
project = {"reviews": 0}
cursor = recipes.find(query, projection=project)
for recipe in cursor:
    print(" *", recipe["name"])


print_title("Empty Aggregation Pipeline")
query = []
cursor = recipes.aggregate(query)
for recipe in cursor:
    print(" *", recipe["name"])

print_title("Vodka Cocktail Reviews")
query = [
    {"$match": {"ingredients": {"$elemMatch": {"name": "Vodka"}}}},
    {
        "$lookup": {
            "from": "reviews",
            "localField": "_id",
            "foreignField": "recipe_id",
            "as": "reviews",
        }
    },
]
cursor = recipes.aggregate(query)
for recipe in cursor:
    pprint(recipe)


print_title("Cocktail Ratings")
query = [
    {
        "$lookup": {
            "from": "reviews",
            "localField": "_id",
            "foreignField": "recipe_id",
            "as": "reviews",
        },
    },
    {"$sort": {"rating": -1}},
    {
        "$project": {
            "name": 1,
            "rating": 1,
            "exact_rating": 1,
            "rating_count": 1,
            "ratings": {
                "$map": {
                    "input": "$reviews",
                    "as": "review",
                    "in": "$$review.rating",
                }
            },
            "exact_rating": {"$avg": "$reviews.rating"},
            "rating": {
                "$divide": [
                    {"$round": {"$multiply": [{"$avg": "$reviews.rating"}, 2]}},
                    2,
                ],
            },
            "rating_count": {"$size": "$reviews.rating"},
        },
    },
]

cursor = recipes.aggregate(query)
for recipe in cursor:
    pprint(recipe)


try:
    print_title("Watch for Changes")
    print("Waiting for updates ... Ctrl-C to move on.")
    for update in recipes.watch():
        pprint(update)

    """
    {'_id': {'_data': '825FA81A1D000000022B022C0100296E5A100457432E8F24D941BF9A9D4EDAD5FD837646645F696400645F7DAA018EC9DFB536781AFA0004'},
    'clusterTime': Timestamp(1604852253, 2),
    'documentKey': {'_id': ObjectId('5f7daa018ec9dfb536781afa')},
    'fullDocument': {'_id': ObjectId('5f7daa018ec9dfb536781afa'),
                    'ingredients': [{'name': 'Dark rum',
                                    'quantity': {'quantity': '45',
                                                    'unit': 'ml'}},
                                    {'name': 'Peach nectar',
                                    'quantity': {'quantity': '2', 'unit': 'oz'}},
                                    {'name': 'Orange juice',
                                    'quantity': {'quantity': '3',
                                                    'unit': 'oz'}}],
                    'instructions': ['Pour all of the ingredients into a '
                                    'highball glass almost filled with ice '
                                    'cubes',
                                    'Stir well.'],
                    'name': 'Abilene'},
    'ns': {'coll': 'recipes', 'db': 'cocktails'},
    'operationType': 'replace'}
    """
except KeyboardInterrupt:
    print()  # Print a line break


print_title("Transaction test")
from pymongo import WriteConcern, ReadPreference
from pymongo.read_concern import ReadConcern
import random

try:
    with client.start_session() as session:

        def transactional_function(session):
            db = session.client.get_database("cocktails")
            recipes = db.get_collection("recipes")
            reviews = db.get_collection("reviews")

            # Important:: You must pass the session to the operations.
            recipe_id = recipes.insert_one(
                {"name": "The Ghost"}, session=session
            ).inserted_id
            for i in range(5):
                reviews.insert_one(
                    {"recipe_id": recipe_id, "rating": random.randint(1, 5)},
                    session=session,
                )
                if i == 2:
                    raise Exception(
                        "Oops, failed transaction after the third review insertion"
                    )

        wc_majority = WriteConcern("majority", wtimeout=1000)
        session.with_transaction(
            transactional_function,
            read_concern=ReadConcern("local"),
            write_concern=wc_majority,
            read_preference=ReadPreference.PRIMARY,
        )
except Exception as e:
    print(e)

print("Is there a recipe in the database?", end=" ")
if recipes.find_one({"name": "The Ghost"}) is None:
    print("Nope!")
else:
    print("Oh dear, yes.")

print_title("Updating Part of a Document")
recipes.update_one(
    {"name": "Negroni Sbagliato"},
    {
        "$push": {
            "reviews": {"rating": 4, "when": datetime.now()},
        },
    },
)
pprint(
    recipes.find_one(
        {"name": "Negroni Sbagliato"},
    )
)


"""
{'_id': ObjectId('5f7b4b6204799f5cf837b1e1'),
 'garnish': 'Orange Twist',
 'ingredients': [{'name': 'Campari', 'quantity': {'unit': 'ml', 'value': 30}},
                 {'name': 'Sweet Vermouth',
                  'quantity': {'unit': 'ml', 'value': 30}},
                 {'name': 'Prosecco', 'quantity': {'unit': 'ml', 'value': 30}}],
 'instructions': ['Stir Campari & vermouth with ice',
                  'Pour into a champagne flute',
                  'Add wine & gently combine',
                  'Serve with orange twist'],
 'name': 'Negroni Sbagliato',
 'reviews': [{'rating': 4,
              'when': datetime.datetime(2020, 11, 8, 16, 53, 25, 905000)},
             {'rating': 4,
              'when': datetime.datetime(2020, 11, 8, 16, 54, 15, 279000)},
             {'rating': 4,
              'when': datetime.datetime(2020, 11, 8, 16, 54, 23, 818000)},
             {'rating': 4,
              'when': datetime.datetime(2020, 11, 8, 16, 54, 26, 744000)},
             {'rating': 4,
              'when': datetime.datetime(2020, 11, 8, 17, 40, 26, 656000)},
             {'rating': 4,
              'when': datetime.datetime(2020, 11, 8, 17, 51, 2, 903000)}]}
"""
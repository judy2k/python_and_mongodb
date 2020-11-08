# Getting Started with MongoDB and Python

## Abstract

MongoDB is probably the world's most popular document database, and it has not one, but TWO, fully supported Python drivers.

This talk will cover core database operations and then move into some of MongoDB's more advanced features (because CRUD is a bit boring!)
I will give an overview of the features of MongoDB, including some features that many think MongoDB doesn't support, including transactions and joins. I'll cover: 

* What MongoDB is (and isn't)
* How to effectively use the document model
* Transactions
* Aggregation queries, including joins!

You'll leave with a good idea of how to integrate MongoDB with your next project, and whether you might want to!

## Agenda

* Overview of MongoDB
  * Clustered document database
  * What is a document?
    * Extra BSON types
  * Documents are stored in collections
    * No requirement for documents to have same structure
    * But you should, because indexing
    * JSONSchema validation
  * Lesser-known features: Transactions, Joins, Schema, Sharding, GIS types, Watch!
* MongoDB & Python
  * There are drivers for most languages
  * There are _two_ Python drivers
    * PyMongo (which is blocking)
    * Motor (which is _kinda_ asyncio)
      * Motor is a wrapper around PyMongo, which runs in a thread.
  * I'm going to cover PyMongo
  * FARM stack, FastAPI, React, MongoDB
* Quick overview of cocktail document
* Connecting to the server
* Insert a document
* Retrieve a document
* Find cocktails by ingredient
* Boring!
* Aggregation pipelines
  * Group cocktails by ingredient
  * Join with comments collection
* Transactions
  * Example
  * Indication your schema is wrong
* Documents -> Pandas
* Twitch Stream on Friday, 6pm!

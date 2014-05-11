__author__ = 'Stephen'

import pyodbc, re, copy, math
import numpy as np
import random

# define connection to local database
connection = pyodbc.connect("DSN=LocalSQL")

# read in the vocab from the wordlist.csv, assign an index to each word and store these mapping in a dictionary
i = 0
iMap = dict()
with open('wordlist.csv', 'r') as my_file:
    for line in my_file:
        w = line.strip()
        iMap[w] = i
        i += 1

def getTrainingDocs():

    ### retrieve the training data from the database

    # get the text data from the database
    cursor = connection.cursor()

    # first get the row count
    cursor.execute("""SELECT count(*) FROM [Forums].[dbo].[Threads] t WHERE LEFT(t.ID,1) NOT LIKE '[a-z]%'""")
    num_train_docs = cursor.fetchone()[0]

    cursor.execute("""
        SELECT left(t.Title + ' ' + t.Question, 8000) As MyText
        FROM [Forums].[dbo].[Threads] t
        WHERE LEFT(t.ID,1) NOT LIKE '[a-z]%'
        ORDER BY t.ID
        """)

    ### record which words appear in which documents

    global doc_vocab_counts, vocab_idfs, doc_text

    doc_text = list()

    # initialize a zeros matrix for word counts by word by document
    # each row represents a document
    # each column represents a distinct word in the vocabulary
    doc_vocab_counts = np.zeros((num_train_docs, len(iMap)))

    # go document by document
    d = 0  # to keep track of the doc index
    doc = cursor.fetchone()
    while doc is not None:

        # remember the original text of the thread
        doc_text.append(doc.MyText)

        # do a little bit of text clean up
        text = doc.MyText.lower()  # make it all lower case
        text = re.sub(r'[^a-z ]', ' ', text)  # remove non-alphabetical characters
        text = re.sub(r' +', ' ', text)  # replace multiple spaces with a single space
        words = str.split(text)  # separate string into individual words

        # iterate through each of the words in the text
        for w in words:

            # if the word is in the vocabulary, mark it down
            if w in iMap:
                doc_vocab_counts[d, iMap[w]] = 1  # turn the switch on

        # move on to the next document
        doc = cursor.fetchone()
        d += 1

    # calculate idfs
    # num_words = doc_vocab_counts.shape[1]
    # vocab_idfs = np.log((np.ones(num_words) * num_train_docs)/(sum(doc_vocab_counts) + np.ones(num_words)).flatten())

def getTestDoc():

    # pick a random document
    j = random.randint(1, 1000)
    for k in range(0, j):
        doc = cursor.fetchone()

    print("--------------------------------------\n")
    print("looking for documents similar to this one:\n")
    print(doc.MyText)

    # do a little bit of text clean up
    text = doc.MyText.lower()  # make it all lower case
    text = re.sub(r'[^a-z ]', ' ', text)  # remove non-alphabetical characters
    text = re.sub(r' +', ' ', text)  # replace multiple spaces with a single space
    words = str.split(text)  # separate string into individual words

    word_counts = np.zeros((1, len(iMap)))

    # iterate through each of the words in the text
    for w in words:

        # if the word is in our vocabulary increment word count
        if w in iMap:
            word_counts[0, iMap[w]] = 1  # mark that this word was in this doc

    return word_counts

def findTopThreeMatches(words):

    global doc_text

    # create a list that will be used to keeping the k nearest neighbors found so far
    best_docs = list()
    # initialize with some easily beatable negative scores
    for m in range(0, 3):
        best_docs.append([-m - 1, ''])

    # get a score for each doc
    for r in range(0, doc_vocab_counts.shape[0]):
        score = sum(sum(doc_vocab_counts[r] * words)) / (np.linalg.norm(doc_vocab_counts[r]) * np.linalg.norm(words) + 1)
        # track best category/score
        for j in range(0, len(best_docs)):
            if score > best_docs[j][0]:
                best_docs.insert(j, [score, doc_text[r]])
                best_docs.pop(len(best_docs)-1)
                break

    return best_docs

# load and process data from training set
getTrainingDocs()

# load data from the test set
cursor = connection.cursor()
cursor.execute("""
    SELECT left(t.Title + ' ' + t.Question, 8000) As MyText
    FROM [Forums].[dbo].[Threads] t
    WHERE LEFT(t.ID,1) LIKE '[a-z]%'
    ORDER BY t.ID""")

# let's do some trials to see what the results look like
for y in range(0, 3):
    matches = findTopThreeMatches(getTestDoc())
    for m in matches:
        print ("\n---------------\n")
        print (m[1])
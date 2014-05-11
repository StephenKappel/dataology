__author__ = 'Stephen Kappel'

# This script create a wordlist.csv file listing all the words in the vocabulary.
# This is accomplished by identifying all the unique words in the corpus, removing the
# stop words, and excluding words that occur less than 10 times.
# In the wordlist.csv, the words are listed in descending order by frequency of appearance.

import pyodbc, re

# define connection to local database
connection = pyodbc.connect("DSN=LocalSQL")

# fetch text from database
# text over 8000 characters long is truncated because pyodbc complains if it is left in
cursor = connection.cursor()
cursor.execute("""
    SELECT left(Title + ' ' + Question, 8000) As MyText
    FROM [Forums].[dbo].[Threads]
    """)

# create new dict
vocab = dict()

# go through text row by row and update vocab
row = cursor.fetchone()
while row is not None:
    text = row.MyText.lower()  # make it all lower case
    text = re.sub(r'[^a-z ]', ' ', text)  # remove non-alphabetical characters
    text = re.sub(r' +', ' ', text)  # replace multiple spaces with a single space
    words = str.split(text)  # separate string into individual words

    #remove last word if it was truncated (so we're not left with half words)
    if len(row.MyText) == 8000:
        del words[-1]

    for word in words:
        if word in vocab:  # if the word is already in the dict
            vocab[word] += 1  # just increment the count
        else:  # if not
            vocab[word] = 1  # add the entry to the dict

    row = cursor.fetchone()

# sort the vocab from high frequency to low frequency
sorted_vocab = sorted(vocab.items(), key=lambda vocab: vocab[1], reverse=True)

# get list of stop words to exclude
stops = list()
with open('stopwords.csv', 'r') as myfile:
    for line in myfile:
        stops.append(line.strip())

# save the findings to a csv
with open('wordlist.csv', 'r+') as myfile:
    for v in sorted_vocab:
        # exclude stop words and words that appeared less than 10 times in the corpus
        if v[0] not in stops and v[1] >= 10:
            myfile.write(v[0] + "\n")
            #myfile.write(str(v[1]) + "," + v[0] + "\n")  # if we want to see the frequency with the word
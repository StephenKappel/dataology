__author__ = 'Stephen'

import pyodbc, re, copy, math
import numpy as np
import matplotlib.pyplot as plt

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

# define a function to get training examples from the database and create a word/doc frequency matrix
# takes as input:
#   size - the max number of examples desired
#   binary - if True, each entry in the matrix will be 1/0 indicating whether the word is in the doc,
#            if False, each entry will be the count of the number of time the word appears in the doc
# returns the number of training examples fetched
# sets these variables in the global environment:
#   doc_vocab_counts - matrix with counts for each word in each doc; row are docs; cols are word
#   doc_categories - vector with category id for each doc in the row corresponding the doc in doc_vocab_counts
#   doc_forums - vector with forum id for each doc in the row corresponding to the doc in doc_vocab_counts
#   category_id_map - dict of category name keys to category id values
#   forum_id_map - dict of forum name keys to forum id values
#   id_category_map - dict of category id keys to category name values
#   id_forum_map - dict of forum id keys to forum name values
def getTrainingData(size, binary=False):

    ### retrieve the training data from the database

    # get the text data from the database
    cursor = connection.cursor()
    # first get the row count
    cursor.execute("""SELECT count(*) FROM [Forums].[dbo].[Threads] t WHERE LEFT(t.ID,1) NOT LIKE '[a-z]%'""")
    num_train_docs = min(cursor.fetchone()[0], size)

    cursor.execute("""
        SELECT TOP """ + str(size) + """ left(t.Title + ' ' + t.Question, 8000) As MyText
            , replace(replace(replace(replace(replace(f.Display_Name,
	    	'SharePoint 2010 - ', 'SharePoint - '),
			'SharePoint 2013 - ', 'SharePoint - '),
			'SharePoint Legacy Versions - ', 'SharePoint - '),
			'Other Programming', 'Programming'),
			'-  Setup', '- Setup') As Forum
            , c.Display_Name As Category
        FROM [Forums].[dbo].[Threads] t
            INNER JOIN [Forums].[dbo].[Forums] f ON t.Forum_ID = f.ID
            INNER JOIN [Forums].[dbo].[Categories] c ON f.Category_ID = c.ID
        WHERE LEFT(t.ID,1) NOT LIKE '[a-z]%'
        ORDER BY t.ID
        """)

    #print("num_train_docs:", num_train_docs, "words:", len(iMap))

    ### count how many times each word is found in each document
    ### and keep track of which docs are in which categories/forums
    #print("building doc_vocab_counts matrix")

    global doc_vocab_counts, doc_categories, doc_forums
    global category_id_map, forum_id_map, id_category_map, id_forum_map
    global vocab_idfs

    # initialize a zeros matrix for word counts by word by document
    # each row represents a document
    # each column represents a distinct word in the vocabulary
    doc_vocab_counts = np.zeros((num_train_docs, len(iMap)))

    # initialize a vector to store the category id of each doc
    doc_categories = np.zeros((num_train_docs, 1))

    # initialize a vector to store the forum id of each doc
    doc_forums = np.zeros((num_train_docs, 1))

    # set up framework for mapping category names to int ids
    category_id_map = dict()
    global cat_id_count
    cat_id_count = 0
    def get_category_id(cat):
        global cat_id_count
        if cat not in category_id_map:
            category_id_map[cat] = cat_id_count
            cat_id_count += 1
        return category_id_map[cat]

    # set up framework for mapping forum names to int ids
    forum_id_map = dict()
    global forum_id_count
    forum_id_count = 0
    def get_forum_id(forum):
        global forum_id_count
        if forum not in forum_id_map:
            forum_id_map[forum] = forum_id_count
            forum_id_count += 1
        return forum_id_map[forum]

    # go document by document
    d = 0  # to keep track of the doc index
    doc = cursor.fetchone()
    while doc is not None:

        # do a little bit of text clean up
        text = doc.MyText.lower()  # make it all lower case
        text = re.sub(r'[^a-z ]', ' ', text)  # remove non-alphabetical characters
        text = re.sub(r' +', ' ', text)  # replace multiple spaces with a single space
        words = str.split(text)  # separate string into individual words

        # remember the forum ID and the category ID for the doc
        doc_categories[d, 0] = get_category_id(doc.Category)
        doc_forums[d, 0] = get_forum_id(doc.Forum)

        # iterate through each of the words in the text
        for w in words:

            # if the word is in our vocabulary increment word count
            if w in iMap:
                if binary:
                    doc_vocab_counts[d, iMap[w]] = 1  # turn the switch on
                else:
                    doc_vocab_counts[d, iMap[w]] += 1  # increment the count of this word in this doc

        # move on to the next document
        doc = cursor.fetchone()
        d += 1

    # build a dictionary for lookup of category/forum based on id
    id_category_map = dict((v, k) for (k, v) in category_id_map.items())
    id_forum_map = dict((v, k) for (k, v) in forum_id_map.items())

    # calculate idfs
    if binary:
        num_words = doc_vocab_counts.shape[1]
        vocab_idfs = np.log((np.ones(num_words) * num_train_docs)/(sum(doc_vocab_counts) + np.ones(num_words)).flatten())

    # return the number of training examples used
    return num_train_docs

# finds the best matching class using cosine similarity and with weighting of words based on inverse document frequency
# uses majority voting of k nearest neighbors to assign the class
# takes as input:
#   k - the number of nearest neighbors to consider
#   words -  vector or word frequencies for example to be classified
#   topic_words_map - dict of topic ids mapped to vectors with word counts for each word in topic
#   id_topic_map - dict of topic ids to topic names
def knn_cosine_sim(min_k, max_k, words, doc_topic, id_topic_map):

    # create a list that will be used to keeping the k nearest neighbors found so far
    best_classes = list()
    # initialize with some easily beatable negative scores
    for m in range(0, max_k):
        best_classes.append([-m - 1, ''])

    # get a score for each doc
    for r in range(0, doc_vocab_counts.shape[0]):
        score = sum(sum(doc_vocab_counts[r] * words)) / (np.linalg.norm(doc_vocab_counts[r]) * np.linalg.norm(words) + 1)
        # track best category/score
        for j in range(0, len(best_classes)):
            if score > best_classes[j][0]:
                best_classes.insert(j, [score, id_topic_map[doc_topic[r][0]]])
                best_classes.pop(len(best_classes)-1)
                break

    # create dict that maps k to class prediction
    best_class_map = dict()

    # find best class based on each k
    for k in range(min_k, max_k+1):

        # count the votes for each class
        votes = dict()
        for n in range(0, k):
            # print(n)
            # print(len(best_classes))
            bc = best_classes[n]
            cat = bc[1]
            if cat not in votes:
                votes[cat] = 0
            votes[cat] += 1

        # return the class with most votes
        best_class = ''
        most_votes = -1
        for v in votes:
            if votes[v] > most_votes:
                best_class = v
                most_votes = votes[v]

        best_class_map[k] = best_class

    return best_class_map

# a variable to make sure each figure id is unique
plot_counter = 0

# create a line graph showing the performance of the algorithm by number of training examples
def plotPerformanceVsSize(performance_by_size, num_val_examples):
    global plot_counter

    for k in performance_by_size:

        plot_counter += 1

        title = "KNN Algorithm Accuracy when k="+str(k)

        # create the figure on which to plot lines
        fig = plt.figure(plot_counter, facecolor="white")

        # add lines showing performance by sample size
        for pbs in sorted(performance_by_size[k].keys()):
            plt.plot(performance_by_size[k][pbs][0], performance_by_size[k][pbs][1], label=pbs)

        fig.canvas.set_window_title(title)
        plt.title(title)
        plt.xlabel("Number of Training Examples")
        plt.ylabel("Accuracy (over " + str(num_val_examples) + " validation examples)")
        plt.legend(loc=2)
        plt.grid(True)
        plt.savefig("C:\\Users\\Stephen\\SkyDrive\\Columbia\\ML\\Project\\Figures\\" + title + ".png")
        #plt.show()

# add a data to performance_by_size dict for later plotting or printing
# takes as input
#   size - the number of training examples used to get this performance
#   performance - a dict of topic to array of success and failure counts
def recordResults(size, performance):
    for k in performance:
        if k not in performance_by_size:
            performance_by_size[k] = dict()
        for p in performance[k]:
            if p not in performance_by_size[k]:
                performance_by_size[k][p] = [[], []]
            performance_by_size[k][p][0].append(size)
            accuracy = performance[k][p][0] / (performance[k][p][0] + performance[k][p][1])
            performance_by_size[k][p][1].append(accuracy)

# for a given size k, test the knn algorithm against each training size within the range specified by
# the global variables min_examples, max_examples, and resolution
def doTestAgainstTrainingSize(k_min, k_max, test=False):

    global performance_by_size
    performance_by_size = dict()

    def recordPerformance (k, topic, success):
        if k not in performance:
            performance[k] = dict()
            performance[k]["Overall"] = [0, 0]
        if topic not in performance[k]:
            performance[k][topic] = [0, 0]
        performance[k][topic][0 if success else 1] += 1
        performance[k]["Overall"][0 if success else 1] += 1

    for size in range(min_examples, max_examples, resolution):

        print("using", size, "training examples")

        performance = dict()

        # read in data from database and prepare word frequency matrix
        training_examples = getTrainingData(size, binary=True)

        # for testing, use threads with ids starting with A, B, or C. for validation, use D, E, F.
        char_set = "('A','B','C')" if test else "('D','E','F')"

        # get the text data from the database
        cursor = connection.cursor()
        # first get the row count
        cursor.execute("""SELECT count(*) FROM [Forums].[dbo].[Threads] t WHERE LEFT(t.ID,1) IN """ + char_set)
        num_test_docs = cursor.fetchone()[0]

        # note that similar SharePoint forums are grouped together in this query
        cursor.execute("""
            SELECT TOP """ + str(validation_examples) + """left(t.Title + ' ' + t.Question, 8000) As MyText
                , replace(replace(replace(replace(replace(f.Display_Name,
                    'SharePoint 2010 - ', 'SharePoint - '),
                    'SharePoint 2013 - ', 'SharePoint - '),
                    'SharePoint Legacy Versions - ', 'SharePoint - '),
                    'Other Programming', 'Programming'),
                    '-  Setup', '- Setup') As Forum
                , c.Display_Name As Category
            FROM [Forums].[dbo].[Threads] t
                INNER JOIN [Forums].[dbo].[Forums] f ON t.Forum_ID = f.ID
                INNER JOIN [Forums].[dbo].[Categories] c ON f.Category_ID = c.ID
            WHERE LEFT(t.ID,1) IN """ + char_set + """ ORDER BY t.ID""")

        ### classify each document and track performance

        doc = cursor.fetchone()
        count=0
        while doc is not None:

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
                    word_counts[0, iMap[w]] = 1  # mark down that this word appeared in this doc

            # classify the example and see if the results match reality
            predictions = knn_cosine_sim(k_min, k_max, word_counts, doc_forums, id_forum_map)
            actual = doc.Forum

            for k in predictions:
                recordPerformance(k, doc.Category, actual == predictions[k])

            # move on to the next document
            doc = cursor.fetchone()

            count += 1
            if count%5 == 0:
                print("classified", count, "documents")

        if test:
            return performance

        recordResults(size, performance)

    # plot results
    plotPerformanceVsSize(performance_by_size, num_val_examples=validation_examples)

# set a constant to determine how many validation examples will be used in each test
validation_examples = 300

# set some constant variables that will be used to determine the range and resolution of # of training examples at
# which to test the algorithm
min_examples = 250
max_examples = 2501
resolution = 750

# creates a set of plots for k=1 to k=15
doTestAgainstTrainingSize(1, 15, False)

# using k=7, test the performance of the algorithm using the test data set
# use 3,000 training examples and 1000 test docs
print("doing test against the test data set")
validation_examples = 1000
min_examples = 3000
max_examples = 3001
resolution = 1
print(doTestAgainstTrainingSize(9, 9, test=True))
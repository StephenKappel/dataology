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
    #print("getting training data from the database")

    # get the text data from the database
    cursor = connection.cursor()
    # first get the row count
    cursor.execute("""SELECT count(*) FROM [Forums].[dbo].[Threads] t WHERE LEFT(t.ID,1) NOT LIKE '[a-z]%'""")
    num_train_docs = min(cursor.fetchone()[0], size)

    #### original query
    # cursor.execute("""
    #     SELECT TOP """ + str(size) + """ left(t.Title + ' ' + t.Question, 8000) As MyText
    #         , f.Display_Name As Forum
    #         , c.Display_Name As Category
    #     FROM [Forums].[dbo].[Threads] t
    #         INNER JOIN [Forums].[dbo].[Forums] f ON t.Forum_ID = f.ID
    #         INNER JOIN [Forums].[dbo].[Categories] c ON f.Category_ID = c.ID
    #     WHERE LEFT(t.ID,1) NOT LIKE '[a-z]%'
    #     ORDER BY t.ID
    #     """)

    #### changed query to group some sharepoint forums together
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

    ### count how many times each word is found in each document
    ### and keep track of which docs are in which categories/forums

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

# create category_prior_map and forum_prior_map which give the prior probability of a thread belonging to a
# category or forum, respectively, based only the % of total threads belonging to those forums
# EDIT: the raw probability drowns out the signal of the individual documents, so a sqrt or log transform on this
# probability is used
def preparePriors():

    cursor = connection.cursor()

    #### original query
    # cursor.execute("""
    #     SELECT count(*) As Threads
    #         , f.Display_Name As Forum
    #         , c.Display_Name As Category
    #     FROM [Forums].[dbo].[Threads] t
    #         INNER JOIN [Forums].[dbo].[Forums] f ON t.Forum_ID = f.ID
    #         INNER JOIN [Forums].[dbo].[Categories] c ON f.Category_ID = c.ID
    #     WHERE LEFT(t.ID,1) NOT LIKE '[a-z]%'
    #     GROUP BY
    #         f.Display_Name
    #         , c.Display_Name
    #     """)

    #### changed query ot group together certain sharepoint forums
    cursor.execute("""
        SELECT count(*) As Threads
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
        GROUP BY
            f.Display_Name
            , c.Display_Name
        """)

    global category_prior_map, forum_prior_map
    category_prior_map = dict()
    forum_prior_map = dict()

    threads = 0
    row = cursor.fetchone()
    while row is not None:

        threads += row.Threads
        if row.Category in category_prior_map:
            category_prior_map[row.Category] += row.Threads
        else:
            category_prior_map[row.Category] = row.Threads
        forum_prior_map[row.Forum] = row.Threads

        row = cursor.fetchone()

    for k in category_prior_map:
        category_prior_map[k] = math.log(category_prior_map[k], 3)  # math.sqrt(category_prior_map[k])

    for k in forum_prior_map:
        forum_prior_map[k] = math.log(forum_prior_map[k], 3)  # math.sqrt(forum_prior_map[k])

# define a function that used the doc_vocab_counts to get the count of each word in a forum or category
# takes as inputs:
#   id_name_map - a dict of topic id to topic name
#   doc_topic - a vector with the topic id for each document
# I use "topic" to refer to either category or forum
# returns a dict that maps the topic id to a vector that has the word counts for each word
def getWordCountsByTopic(id_name_map, doc_topic):

    global doc_vocab_counts

    num_docs = doc_vocab_counts.shape[0]

    # start by creating binary vectors to identify which docs belong to each category

    # create a dict in which store store all the vectors I build
    topic_docs_map = dict()

    # for each topic
    for topic_id in id_name_map:

        # create vector
        v = np.zeros((num_docs, 1))

        # add vector to map
        topic_docs_map[topic_id] = v

    # for each doc, set value to 1 if doc is this category
    for i in range(0, num_docs):
        topic_docs_map[doc_topic[i, 0]][i, 0] = 1

    # now do element-wise multiplication and sum to get the count for each word in each topic

    # create a dict in which store store all the vectors I build
    topic_words_map = dict()

    # for each topic
    for topic_id in topic_docs_map:
        topic_words_map[topic_id] = sum(doc_vocab_counts * topic_docs_map[topic_id])

    return topic_words_map

# define a method to test the performance of a categorization method
# takes as input:
#   topic_words_map - a dict of topic id to vectors of word metric
#   example_transform - a function that  transforms a word frequency vector in preparation to be passed to classifier
#   classifier - a function that takes a vector word counts for one doc and returns a predicted category or forum
#   id_topic_map - a dict that maps topic id to topic name
#   forums - true if we are testing classifier for forums classification; false for categories
#   test - true to use test set; false to use validation set
#   size - the number of test/validation examples to check
#   priors -  None if no priors are to be used, or a dict of topic to prior value if priors are to be used
def testPerformance(topic_words_map, example_transform, classifier, id_topic_map, forums, test, size, priors):

    ### retrieve the test data from the database

    # for testing, use threads with ids starting with A, B, or C. for validation, use D, E, F.
    char_set = "('A','B','C')" if test else "('D','E','F')"

    # get the text data from the database
    cursor = connection.cursor()
    # first get the row count
    cursor.execute("""SELECT count(*) FROM [Forums].[dbo].[Threads] t WHERE LEFT(t.ID,1) IN """ + char_set)
    num_test_docs = cursor.fetchone()[0]

    #### original query
    # cursor.execute("""
    #     SELECT TOP """ + str(size) + """left(t.Title + ' ' + t.Question, 8000) As MyText
    #         , f.Display_Name As Forum
    #         , c.Display_Name As Category
    #     FROM [Forums].[dbo].[Threads] t
    #         INNER JOIN [Forums].[dbo].[Forums] f ON t.Forum_ID = f.ID
    #         INNER JOIN [Forums].[dbo].[Categories] c ON f.Category_ID = c.ID
    #     WHERE LEFT(t.ID,1) IN """ + char_set + """ ORDER BY t.ID""")

    #### query with sharepoint forums grouped
    cursor.execute("""
        SELECT TOP """ + str(size) + """left(t.Title + ' ' + t.Question, 8000) As MyText
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

    # create a dict that maps a topic (or "overall") to a list of counts of successes and failures
    performance = dict()
    performance["Overall"] = [0, 0]
    def recordPerformance (topic, success):
        if topic not in performance:
            performance[topic] = [0, 0]
        performance[topic][0 if success else 1] += 1
        performance["Overall"][0 if success else 1] += 1

    doc = cursor.fetchone()
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
                word_counts[0, iMap[w]] += 1  # increment the count of this word in this doc

        # classify the example and see if the results match reality
        prediction = classifier(example_transform(word_counts), topic_words_map, id_topic_map, priors)
        actual = doc.Forum if forums else doc.Category
        #print("prediction:", prediction, "actual:", actual)
        successfulness = (prediction == actual)

        recordPerformance(doc.Category, successfulness)

        # move on to the next document
        doc = cursor.fetchone()

    return performance


### create some classification algorithms

# finds the best matching class using the numerator of the cosine similarity
# takes as input:
#   words -  vector or word frequencies for example to be classified
#   topic_words_map - dict of topic ids mapped to vectors with word counts for each word in topic
#   id_topic_map - dict of topic ids to topic names
#   priors - a dict of topic to prior value, if priors are to be factored into classification
def class_cosine_sim_num(words, topic_words_map, id_topic_map, priors=None):
    best_class = ""
    best_score = -1
    # get a score for each topic
    for topic_id in topic_words_map:
        score = sum(sum(topic_words_map[topic_id] * words))
        if priors is not None:
            score *= priors[id_topic_map[topic_id]]
        # track best category/score
        if score > best_score:
            best_score = score
            best_class = id_topic_map[topic_id]
    # return the category that had the highest score
    return best_class

# finds the best matching class using cosine similarity
# takes as input:
#   words -  vector or word frequencies for example to be classified
#   topic_words_map - dict of topic ids mapped to vectors with word counts for each word in topic
#   id_topic_map - dict of topic ids to topic names
#   priors - a dict of topic to prior value, if priors are to be factored into classification
def class_cosine_sim(words, topic_words_map, id_topic_map, priors=None):
    best_class = ""
    best_score = -1
    # get a score for each topic
    for topic_id in topic_words_map:
        score = sum(sum(topic_words_map[topic_id] * words)) / (np.linalg.norm(topic_words_map[topic_id]) * np.linalg.norm(words))
        if priors is not None:
            score *= priors[id_topic_map[topic_id]]
        # track best category/score
        if score > best_score:
            best_score = score
            best_class = id_topic_map[topic_id]
    # return the category that had the highest score
    return best_class

# finds the best matching class using numerator of cosine similarity and with weighting of words based on inverse document frequency
# takes as input:
#   words -  vector or word frequencies for example to be classified
#   topic_words_map - dict of topic ids mapped to vectors with word counts for each word in topic
#   id_topic_map - dict of topic ids to topic names
#   priors - a dict of topic to prior value, if priors are to be factored into classification
def class_log_idf_cosine_sim_num(words, topic_words_map, id_topic_map, priors=None):
    best_class = ""
    best_score = -1
    # get a score for each topic
    for topic_id in topic_words_map:
        score = sum(sum(topic_words_map[topic_id].flatten() * (words * vocab_idfs)))
        if priors is not None:
            score *= priors[id_topic_map[topic_id]]
        # track best category/score
        if score > best_score:
            best_score = score
            best_class = id_topic_map[topic_id]
    # return the category that had the highest score
    return best_class

# finds the best matching class using cosine similarity and with weighting of words based on inverse document frequency
# takes as input:
#   words -  vector or word frequencies for example to be classified
#   topic_words_map - dict of topic ids mapped to vectors with word counts for each word in topic
#   id_topic_map - dict of topic ids to topic names
#   priors - a dict of topic to prior value, if priors are to be factored into classification
def class_log_idf_cosine_sim(words, topic_words_map, id_topic_map, priors=None):
    best_class = ""
    best_score = -1
    # get a score for each topic
    for topic_id in topic_words_map:
        score = sum(sum(topic_words_map[topic_id].flatten() * (words * vocab_idfs))) / \
                (np.linalg.norm(topic_words_map[topic_id].flatten()) * np.linalg.norm(words * vocab_idfs))
        if priors is not None:
            score *= priors[id_topic_map[topic_id]]
        # track best category/score
        if score > best_score:
            best_score = score
            best_class = id_topic_map[topic_id]
    # return the category that had the highest score
    return best_class


### create some transformation algorithms

# takes as an input a matrix with word frequencies; each column is a word; each row is a doc or a topic
# change non-zero entries to 1s, so we have a matrix of only 0s and 1s
def binary_transform(word_freqs):

    if type(word_freqs) == np.ndarray:
        new_matrix = np.copy(word_freqs)
        if len(new_matrix.shape) > 1:
            (rs, cs) = np.nonzero(new_matrix)
            for k in range(0, len(rs)):
                new_matrix[rs[k], cs[k]] = 1
        else:
            rs = np.nonzero(new_matrix)
            for k in range(0, len(rs)):
                new_matrix[rs[k]] = 1
        return new_matrix

    if type(word_freqs) == dict:
        new_dict = copy.deepcopy(word_freqs)
        for k in new_dict:
            new_dict[k] = binary_transform(new_dict[k])
        return new_dict

# just a place holder, does not transformation on the data
def no_transform(word_freq_matrix):
    return word_freq_matrix

# scale rows to have a sum of 100
def normalize_transform(word_freqs):

    if type(word_freqs) == np.ndarray:
        wc = sum(word_freqs) + 1  # make sure we don't divide by zero
        return (100/wc)*word_freqs

    if type(word_freqs) == dict:
        new_dict = copy.deepcopy(word_freqs)
        for k in new_dict:
            new_dict[k] = normalize_transform(new_dict[k])
        return new_dict

# add a data to performance_by_size dict for later plotting or printing
# takes as input
#   size - the number of training examples used to get this performance
#   performance - a dict of topic to array of success and failure counts
def recordResults(size, performance):
    for p in performance:
        if p not in performance_by_size:
            performance_by_size[p] = [[], []]
        performance_by_size[p][0].append(size)
        accuracy = performance[p][0] / (performance[p][0] + performance[p][1])
        performance_by_size[p][1].append(accuracy)

# a variable to make sure each figure id is unique
plot_counter = 0

# create a line graph showing the performance of the algorithm by number of training examples
def plotPerformanceVsSize(performance_by_size, title, num_val_examples):
    global plot_counter
    plot_counter += 1

    # create the figure on which to plot lines
    fig = plt.figure(plot_counter, facecolor="white")

    # add lines showing performance by sample size
    for pbs in sorted(performance_by_size.keys()):
        plt.plot(performance_by_size[pbs][0], performance_by_size[pbs][1], label=pbs)

    fig.canvas.set_window_title(title)
    plt.title(title)
    plt.xlabel("Number of Training Examples")
    plt.ylabel("Accuracy (over " + str(num_val_examples) + " validation examples)")
    plt.legend(loc=2)
    plt.grid(True)
    plt.savefig("C:\\Users\\Stephen\\SkyDrive\\Columbia\\ML\\Project\\Figures\\" + title + ".png")
    #plt.show()

# for each of the training set sizes specified by the min_examples, max_examples, and resolution global variables,
# test performance of the algorithm with the given properties and plot it
# takes as input:
#  title - the title to be used on the plot and as the plot's file name
#  forum_level - True for forums, False for forum categories
#  binary_training - True to read in training data as 0/1 matrix, False to read in frequencies
#  example_transformation - a function used to transform example vectors
#  classfication_function - a function to do comparisons and assign a class to an examples based on its similarity to
#      training data
#  normalize - True to scale training data to common scale
#  use_priors - True to incorporate priors into classification_function's choicev
def doTestAgainstTrainingSize(title, forum_level, binary_training, example_transform, classification_function,
                              normalize, use_priors):

    # start with unscaled word frequency with cosine similarity
    print("\n---- " + title + " ----\n")

    global performance_by_size, category_prior_map, forum_prior_map
    performance_by_size = dict()
    for size in range(min_examples, max_examples, resolution):

        print("-- using", size, "training examples")
        print("training...")

        # read in data from database and prepare word frequency matrix
        training_examples = getTrainingData(size, binary=binary_training)
        if use_priors:
            preparePriors()

        doc_topic = doc_categories if not forum_level else doc_forums
        id_topic_map = id_category_map if not forum_level else id_forum_map

        # aggregate frequencies by topic
        topic_words_map = getWordCountsByTopic(id_topic_map, doc_topic)
        if normalize:
            topic_words_map = normalize_transform(topic_words_map)

        # test classification
        print("testing...")
        performance = testPerformance(topic_words_map, example_transform, classification_function,
                                      id_topic_map, forums=forum_level, test=False, size=validation_examples,
                                      priors= None if not use_priors else (category_prior_map if not forum_level else forum_prior_map))
        recordResults(size, performance)

    plotPerformanceVsSize(performance_by_size, title, validation_examples)

# set a constant to determine how many validation examples will be used in each test
validation_examples = 2500

# set some constant variables that will be used to determine the range and resolution of # of training examples at
# which to test the algorithm
min_examples = 500
max_examples = 5001
resolution = 750

## and now for the magic.... let's try a bunch of variants of the algorithm on our validation data


## first, category level with no priors

# word frequencies

doTestAgainstTrainingSize("Categories - Word Frequency", forum_level=False, binary_training=False,
                          example_transform=no_transform, classification_function=class_cosine_sim_num, normalize=False,
                          use_priors=False)

doTestAgainstTrainingSize("Categories - Cosine Word Frequency", forum_level=False, binary_training=False,
                          example_transform=no_transform, classification_function=class_cosine_sim, normalize=False,
                          use_priors=False)

doTestAgainstTrainingSize("Categories - Normalized Word Frequency", forum_level=False, binary_training=False,
                          example_transform=no_transform, classification_function=class_cosine_sim_num, normalize=True,
                          use_priors=False)

# binaries

doTestAgainstTrainingSize("Categories - Cosine Binary Word Counts", forum_level=False, binary_training=True,
                          example_transform=binary_transform, classification_function=class_cosine_sim, normalize=False,
                          use_priors=False)

doTestAgainstTrainingSize("Categories - Binary Word Counts", forum_level=False, binary_training=True,
                          example_transform=binary_transform, classification_function=class_cosine_sim_num, normalize=False,
                          use_priors=False)

doTestAgainstTrainingSize("Categories - Normalized Binary Word Counts", forum_level=False, binary_training=True,
                          example_transform=binary_transform, classification_function=class_cosine_sim_num, normalize=True,
                          use_priors=False)

# tf-idf

doTestAgainstTrainingSize("Categories - Cosine tf-idf", forum_level=False, binary_training=True,
                          example_transform=no_transform, classification_function=class_log_idf_cosine_sim,
                          normalize=False, use_priors=False)

doTestAgainstTrainingSize("Categories - tf-idf ", forum_level=False, binary_training=True,
                          example_transform=no_transform, classification_function=class_log_idf_cosine_sim_num,
                          normalize=False, use_priors=False)

doTestAgainstTrainingSize("Categories - Normalized tf-idf", forum_level=False, binary_training=True,
                          example_transform=no_transform, classification_function=class_log_idf_cosine_sim_num,
                          normalize=True, use_priors=False)

# second, category level with priors

# word frequencies

doTestAgainstTrainingSize("Categories - Word Frequency with Log3 Priors", forum_level=False, binary_training=False,
                          example_transform=no_transform, classification_function=class_cosine_sim_num, normalize=False,
                          use_priors=True)

doTestAgainstTrainingSize("Categories - Cosine Word Frequency with Log3 Priors", forum_level=False, binary_training=False,
                          example_transform=no_transform, classification_function=class_cosine_sim, normalize=False,
                          use_priors=True)

doTestAgainstTrainingSize("Categories - Normalized Word Frequency with Log3 Priors", forum_level=False, binary_training=False,
                          example_transform=no_transform, classification_function=class_cosine_sim_num, normalize=True,
                          use_priors=True)

# binaries

doTestAgainstTrainingSize("Categories - Cosine Binary Word Counts with Log3 Priors", forum_level=False, binary_training=True,
                          example_transform=binary_transform, classification_function=class_cosine_sim, normalize=False,
                          use_priors=True)

doTestAgainstTrainingSize("Categories - Binary Word Counts with Log3 Priors", forum_level=False, binary_training=True,
                          example_transform=binary_transform, classification_function=class_cosine_sim_num, normalize=False,
                          use_priors=True)

doTestAgainstTrainingSize("Categories - Normalized Binary Word Counts with Log3 Priors", forum_level=False, binary_training=True,
                          example_transform=binary_transform, classification_function=class_cosine_sim_num, normalize=True,
                          use_priors=True)

# tf-idf

doTestAgainstTrainingSize("Categories - Cosine tf-idf with Log3 Priors", forum_level=False, binary_training=True,
                          example_transform=no_transform, classification_function=class_log_idf_cosine_sim,
                          normalize=False, use_priors=True)

doTestAgainstTrainingSize("Categories - tf-idf with Log3 Priors", forum_level=False, binary_training=True,
                          example_transform=no_transform, classification_function=class_log_idf_cosine_sim_num,
                          normalize=False, use_priors=True)

doTestAgainstTrainingSize("Categories - Normalized tf-idf with Log3 Priors", forum_level=False, binary_training=True,
                          example_transform=no_transform, classification_function=class_log_idf_cosine_sim_num,
                          normalize=True, use_priors=True)


### test the final algorithm against the test set for forum category classification

print("-- testing against test set")
print("training...")

# read in data from database and prepare word frequency matrix
training_examples = getTrainingData(100000, binary=True)

# aggregate frequencies by topic
topic_words_map = getWordCountsByTopic(id_category_map, doc_categories)
topic_words_map = normalize_transform(topic_words_map)

# test classification
print("testing...")
performance = testPerformance(topic_words_map, no_transform, class_log_idf_cosine_sim,
                              id_category_map, forums=False, test=True, size=100000, priors=None)
print(performance)


# set a constant to determine how many validation examples will be used in each test
validation_examples = 2000

# set some constant variables that will be used to determine the range and resolution of # of training examples at
# which to test the algorithm
min_examples = 1000
max_examples = 9001
resolution = 1000

## third, forum level with no priors

# word frequencies

doTestAgainstTrainingSize("Forums - Word Frequency", forum_level=True, binary_training=False,
                          example_transform=no_transform, classification_function=class_cosine_sim_num, normalize=False,
                          use_priors=False)

doTestAgainstTrainingSize("Forums - Cosine Word Frequency", forum_level=True, binary_training=False,
                          example_transform=no_transform, classification_function=class_cosine_sim, normalize=False,
                          use_priors=False)

doTestAgainstTrainingSize("Forums - Normalized Word Frequency", forum_level=True, binary_training=False,
                          example_transform=no_transform, classification_function=class_cosine_sim_num, normalize=True,
                          use_priors=False)

# binaries

doTestAgainstTrainingSize("Forums - Cosine Binary Word Counts", forum_level=True, binary_training=True,
                          example_transform=binary_transform, classification_function=class_cosine_sim, normalize=False,
                          use_priors=False)

doTestAgainstTrainingSize("Forums - Binary Word Counts", forum_level=True, binary_training=True,
                          example_transform=binary_transform, classification_function=class_cosine_sim_num, normalize=False,
                          use_priors=False)

doTestAgainstTrainingSize("Forums - Normalized Binary Word Counts", forum_level=True, binary_training=True,
                          example_transform=binary_transform, classification_function=class_cosine_sim_num, normalize=True,
                          use_priors=False)

# tf-idf

doTestAgainstTrainingSize("Forums - Cosine tf-idf", forum_level=True, binary_training=True,
                          example_transform=no_transform, classification_function=class_log_idf_cosine_sim,
                          normalize=False, use_priors=False)

doTestAgainstTrainingSize("Forums - tf-idf ", forum_level=True, binary_training=True,
                          example_transform=no_transform, classification_function=class_log_idf_cosine_sim_num,
                          normalize=False, use_priors=False)

doTestAgainstTrainingSize("Forums - Normalized tf-idf", forum_level=True, binary_training=True,
                          example_transform=no_transform, classification_function=class_log_idf_cosine_sim_num,
                          normalize=True, use_priors=False)

# fourth, forum level with priors

# word frequencies

doTestAgainstTrainingSize("Forums - Word Frequency with Log3 Priors", forum_level=True, binary_training=False,
                          example_transform=no_transform, classification_function=class_cosine_sim_num, normalize=False,
                          use_priors=True)

doTestAgainstTrainingSize("Forums - Cosine Word Frequency with Log3 Priors", forum_level=True, binary_training=False,
                          example_transform=no_transform, classification_function=class_cosine_sim, normalize=False,
                          use_priors=True)

doTestAgainstTrainingSize("Forums - Normalized Word Frequency with Log3 Priors", forum_level=True, binary_training=False,
                          example_transform=no_transform, classification_function=class_cosine_sim_num, normalize=True,
                          use_priors=True)

# binaries

doTestAgainstTrainingSize("Forums - Cosine Binary Word Counts with Log3 Priors", forum_level=True, binary_training=True,
                          example_transform=binary_transform, classification_function=class_cosine_sim, normalize=False,
                          use_priors=True)

doTestAgainstTrainingSize("Forums - Binary Word Counts with Log3 Priors", forum_level=True, binary_training=True,
                          example_transform=binary_transform, classification_function=class_cosine_sim_num, normalize=False,
                          use_priors=True)

doTestAgainstTrainingSize("Forums - Normalized Binary Word Counts with Log3 Priors", forum_level=True, binary_training=True,
                          example_transform=binary_transform, classification_function=class_cosine_sim_num, normalize=True,
                          use_priors=True)

# tf-idf

doTestAgainstTrainingSize("Forums - Cosine tf-idf with Log3 Priors", forum_level=True, binary_training=True,
                          example_transform=no_transform, classification_function=class_log_idf_cosine_sim,
                          normalize=False, use_priors=True)

doTestAgainstTrainingSize("Forums - tf-idf with Log3 Priors", forum_level=True, binary_training=True,
                          example_transform=no_transform, classification_function=class_log_idf_cosine_sim_num,
                          normalize=False, use_priors=True)

doTestAgainstTrainingSize("Forums - Normalized tf-idf with Log3 Priors", forum_level=True, binary_training=True,
                          example_transform=no_transform, classification_function=class_log_idf_cosine_sim_num,
                          normalize=True, use_priors=True)


### test the final algorithm against the test set for forum classification

print("-- testing forums algorithm against test set")
print("training...")

# read in data from database and prepare word frequency matrix
training_examples = getTrainingData(100000, binary=True)

# aggregate frequencies by topic
topic_words_map = getWordCountsByTopic(id_forum_map, doc_forums)

# test classification
print("testing...")
performance = testPerformance(topic_words_map, binary_transform, class_cosine_sim,
                              id_forum_map, forums=True, test=True, size=100000, priors=None)
print (performance)
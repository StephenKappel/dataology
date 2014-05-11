#!/usr/bin/python

# ORIGINAL COMMENTS:

# onlinewikipedia.py: Demonstrates the use of online VB for LDA to
# analyze a bunch of random Wikipedia articles.
#
# Copyright (C) 2010  Matthew D. Hoffman
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

# THIS CODE HAS BEEN ADAPTED BY STEPHEN KAPPEL
# THE CODE HAS BEEN UPDATED TO RUN ON PYTHON 3.3
# INSTEAD OF READING FROM WIKIPEDIA, THIS NOT READS IN FORUM TEXT FROM A DATABASE
#

import numpy, sys, onlineldavb, pyodbc

#constants
CONNECTION_STRING = "DSN=LocalSQL"

# define connection string to local database
connection = pyodbc.connect(CONNECTION_STRING)

# The number of documents to analyze each iteration
BATCHSIZE = 1000
# The total number of documents in database
D = 73822
# The number of topics
K = 7

# How many documents to look at
if (len(sys.argv) < 2):
    documentstoanalyze = int(D/BATCHSIZE)
else:
    documentstoanalyze = int(sys.argv[1])

print (documentstoanalyze)

# Our vocabulary
vocab = open('./forums_dict.txt').readlines()
W = len(vocab)

# Initialize the algorithm with alpha=1/K, eta=1/K, tau_0=1024, kappa=0.7
olda = onlineldavb.OnlineLDA(vocab, K, D, 1./K, 1./K, 1024., 0.7)
# Run until we've seen D documents. (Feel free to interrupt *much*
# sooner than this.)

def scanAllDocs(cursor):
    n = 0
    row = cursor.fetchone()
    for iteration in range(0, documentstoanalyze + 1):
        # Download some articles
        docset = list()
        i = 0
        while row is not None and i < BATCHSIZE:
            docset.append(row.MyText)
            row = cursor.fetchone()
            i += 1
        n += i
        print ("Docs analyzed: ", n)
        # Give them to online LDA
        (gamma, bound) = olda.update_lambda(docset)
        # Compute an estimate of held-out perplexity
        (wordids, wordcts) = onlineldavb.parse_doc_list(docset, olda._vocab)
        perwordbound = bound * len(docset) / (D * sum(map(sum, wordcts)))
        print ('%d:  rho_t = %f,  held-out perplexity estimate = %f' % \
            (iteration, olda._rhot, numpy.exp(-perwordbound)))

        # Save lambda, the parameters to the variational distributions
        # over topics, and gamma, the parameters to the variational
        # distributions over topic weights for the articles analyzed in
        # the last iteration.
        if (iteration % 100 == 0):
            numpy.savetxt('lambda_{0}-{1}.dat'.format(K, iteration), olda._lambda)
            numpy.savetxt('gamma_{0}-{1}.dat'.format(K, iteration), gamma)

        if n >= D-1:
            numpy.savetxt('lambda_{0}-final.dat'.format(K), olda._lambda)
            numpy.savetxt('gamma_{0}-final.dat'.format(K), gamma)
            break

# fetch text from database, and iterate through all threads three times with different orderings

for y in range(0, 3):

    myCursor = connection.cursor()
    myCursor.execute("""
        SELECT left(Title + ' ' + Question, 8000) As MyText
        FROM [Forums].[dbo].[Threads]
        ORDER BY Title
    """)
    scanAllDocs(myCursor)

    myCursor = connection.cursor()
    myCursor.execute("""
        SELECT left(Title + ' ' + Question, 8000) As MyText
        FROM [Forums].[dbo].[Threads]
        ORDER BY Title
    """)
    scanAllDocs(myCursor)

    myCursor = connection.cursor()
    myCursor.execute("""
        SELECT left(Title + ' ' + Question, 8000) As MyText
        FROM [Forums].[dbo].[Threads]
        ORDER BY Created_On
    """)
    scanAllDocs(myCursor)

vocab = str.split(open('forums_dict.txt').read())
testlambda = numpy.loadtxt('lambda_{0}-final.dat'.format(K))

for k in range(0, len(testlambda)):
    lambdak = list(testlambda[k, :])
    lambdak = lambdak / sum(lambdak)
    temp = zip(lambdak, range(0, len(lambdak)))
    temp = sorted(temp, key = lambda x: x[0], reverse=True)
    print ('topic %d:' % (k))
    for i in range(0, 53):
        print ('%20s  \t---\t  %.4f' % (vocab[temp[i][1]], temp[i][0]))
    print()


__author__ = 'Stephen'

from Contributor import Contributor
from datetime import datetime, tzinfo, timedelta

class Thread:

    # constructor
    def __init__(self, id, title, question, views, subscribers, createdOn, firstPostHasCode, type, scrapedOn):
        self.id = id
        self.contributors = dict()
        self.title = title
        self.question = question
        self.views = views
        self.subscribers = subscribers
        self.createdOn = createdOn
        self.firstPostHasCode = firstPostHasCode
        self.answeredOn = datetime(3000, 1, 1, 0, 0, 0, tzinfo=GMT())
        self.lastPostOn = datetime(1900, 1, 1, 0, 0, 0, tzinfo=GMT())
        self.answerHasCode = False
        self.type = type
        self.scrapedOn = scrapedOn
        self.firstReplyOn = datetime(3000, 1, 1, 0, 0, 0, tzinfo=GMT())

    #  returns a contributor object with the given userId
    #  if a contributor with that id alread exists use it, if not create a new one
    def getContributor(self, userId):
        if(not userId in self.contributors):
            self.contributors[userId] = Contributor(userId)
        return self.contributors[userId]

    # this will be called for the post date of each message marked as an answer
    # determine which answer is the first one
    def setAnsweredOn(self, answeredOn):
        if (answeredOn < self.answeredOn):
            self.answeredOn = answeredOn

    # this will be called for the post date of each message in the thread
    # determine which is the most recent post and which is the first reply
    def addPostDate(self, postDate):
        if (postDate > self.lastPostOn):
            self.lastPostOn = postDate
        if (postDate > self.createdOn and postDate < self.firstReplyOn):
            self.firstReplyOn = postDate

    # called if a post marked as an answer contains code
    def setAnswerHasCode(self):
        self.answerHasCode = True

class GMT(tzinfo):
     def utcoffset(self, dt):
         return timedelta(hours=0)
     def dst(self, dt):
         return timedelta(0)
     def tzname(self,dt):
          return "GMT"




__author__ = 'Stephen'

from Contributor import Contributor
from datetime import datetime, tzinfo, timedelta

class Thread:

    def __init__(self, id, title, question, views, subscribers, createdOn, firstPostHasCode):
        self.id = id
        self.contributors = dict()
        self.title = title
        self.question = question
        self.views = views
        self.subscribers = subscribers
        self.createdOn = createdOn
        self.firstPostHasCode = firstPostHasCode
        self.answeredOn = datetime(3000, 1, 1, 0, 0, 0, tzinfo = GMT())
        self.lastPostOn = datetime(1900, 1, 1, 0, 0, 0, tzinfo = GMT())
        self.answerHasCode = False

    def getContributor(self, userId):
        if(not userId in self.contributors):
            self.contributors[userId] = Contributor(userId)
        return self.contributors[userId]

    def setAnsweredOn(self, answeredOn):
        if (answeredOn < self.answeredOn):
            self.answeredOn = answeredOn

    def setLastPostOn(self, lastPostOn):
        if (lastPostOn > self.lastPostOn):
            self.lastPostOn = lastPostOn

    def setAnswerHasCode(self):
        self.answerHasCode = True

class GMT(tzinfo):
     def utcoffset(self, dt):
         return timedelta(hours=0)
     def dst(self, dt):
         return timedelta(0)
     def tzname(self,dt):
          return "GMT"




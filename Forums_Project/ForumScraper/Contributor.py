__author__ = 'Stephen'

class Contributor:

    def __init__(self, user):
        self.posts = 0
        self.answers = 0
        self.votes = 0
        self.code = 0
        self.userId = user
        self.firstPosts = 0

    def addFirstPost(self):
        self.firstPosts = 1

    def addPost(self):
        self.posts += 1

    def addAnswer(self):
        self.answers += 1

    def addVotes(self, votes):
        self.votes += votes

    def addCode(self):
        self.code += 1

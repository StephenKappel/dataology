__author__ = 'Stephen'

from bs4 import BeautifulSoup
import urllib.request
import urllib.parse
import json
from DAL import DAL
import parsedatetime
import datetime
from Thread import Thread
from User import User
from  Contributor import Contributor
import iso8601

class MsdnScraper():

    # the contents of this html file were attained by going to http://social.msdn.microsoft.com/Forums/en-US/home
    # selecting the [ View All ] link, inspecting the element of the dialog box, and saving the exposed DOM
    FORUM_CATALOG_PATH = "C:\\Users\\Stephen\\Documents\\GitHub\\dataology\\Forums_Project\\ForumScraper\\Sample_Markup\\MsdnForumsCatalog.html"
    FORUM_DETAILS_API_STUB = "http://social.msdn.microsoft.com/Forums/api/category/getforumdetails?category="
    THREAD_LIST_URL_STUB = "http://social.msdn.microsoft.com/Forums/en-US/home?filter=alltypes&sort=firstpostdesc"
    THREAD_URL_STUB = "http://social.msdn.microsoft.com/Forums/en-US/###?outputAs=xml"


    def __init__(self):
        self.myDal = DAL()

    def scrapeForumsList(self):

        count = 0

        # use Beautiful soup to get category names from html file
        soup = BeautifulSoup(open(self.FORUM_CATALOG_PATH))
        container = soup.find(id="allCategoryListContainer")
        categories = container.find_all(class_="categoryArea")

        for cat in categories:

            #save category information to categories table in database
            catID = cat.get("data-categoryid")
            catName = cat.get("data-categoryname")
            catTitle = cat.find(class_="categoryHeaderText").get("title")
            self.myDal.addCategory(catName, "MS", catID, catTitle)

            #use category names to make api requests and get details of specific forums
            with urllib.request.urlopen(self.FORUM_DETAILS_API_STUB + catName) as rawJson:
                data = rawJson.read().decode("utf8")
            data = json.loads(data)

            #save forums details to Forums table in database
            for i in range(len(data)):
                self.myDal.addForum(data[i]["Name"], "MS", data[i]["ForumId"], data[i]["Description"], catID, data[i]["DisplayName"])
                count += 1

            print (i, " forums added or updated, for ", catName)

        print (count, " forums added or updated, in total")

    def scrapeThreadsList(self):

        forums = self.myDal.getForumsList()
        for forumKey in forums.keys():
            print("getting threads for " + forumKey)
            forumId = forums[forumKey]
            for i in range(1,26):
                gotSome = False
                url = self.THREAD_LIST_URL_STUB + "&forum=" + forumKey + "&page=" + str(i)
                soup = BeautifulSoup(urllib.request.urlopen(url))
                threads = soup.find_all(class_="threadblock")
                for thread in threads:
                    gotSome = True
                    id = thread.get("data-threadid")
                    self.myDal.addThread(id, forumId)
                if gotSome == False:
                    break

    def scrapeThreadDetail(self):

        i = 1
        cal = parsedatetime.Calendar()

        myThreads = list()
        myUsers = dict()

        threads = self.myDal.getThreadsList()

        for threadId in threads:

            i += 1
            if (i > 10):
                break

            url = self.THREAD_URL_STUB.replace("###", threadId)
            print (url)
            soup = BeautifulSoup(urllib.request.urlopen(url))

            t = soup.find("thread")

            tt = t.get("threadtype")
            if tt == "question" or tt == "answer" or tt == "propose":

                messages = soup.find("messages")
                firstMess = messages.find("message")
                myThread = Thread(t.get("id"), t.find("topic").text, firstMess.find("body").text, t.get("views"),
                                  t.get("subscribers"), self.makeDateTime(cal.parseDateTime(t.find("createdon").text)), firstMess.get("hascode") == "true")

                myThread.getContributor(t.get("authorid")).addFirstPost()

                # update list of users
                for user in soup.find("users").findAll("user"):
                    userId = user.get("id")
                    if not userId in myUsers:
                        myUsers[userId] = User(userId, user.find("displayname").text, user.find("msft").text == "true"
                            , user.find("mscs").text == "true", user.find("mvp").text == "true"
                            , user.find("partner").text == "true", user.find("mcc").text == "true"
                            , self.makeDateTime(cal.parseDateTime(user.find("lastactive").text))
                            , int(user.find("points").text), int(user.find("posts").text)
                            , int(user.find("answers").text), int(user.find("stars").text))
                            #, user.find("role").text)

                # iterate through each message to get data not explicitly called out in attributes
                for message in messages.findAll("message"):

                    #print (message)

                    # keep track of newest post
                    myThread.setLastPostOn(self.makeDateTime(cal.parseDateTime(message.find("createdon").text)))

                    # update contributor stats
                    con = myThread.getContributor(message.get("authorid"))
                    con.addPost()
                    if message.get("hasCode") == "true":
                        con.addCode()
                    con.addVotes(int(message.get("helpfulvotes")))

                    # if this is marked as an answer
                    ans = message.find("answer")
                    if (not ans is None) and ans.text == "true":

                        # give contributor credit
                        con.addAnswer()

                        # track if any answer contains code
                        if (message.get("hascode") == "true"):
                            myThread.setAnswerHasCode()

                        # find when this was marked as an answer
                        hists = message.findAll("history")
                        for hist in hists:
                            if hist.find("type").text == "MarkAnswer":
                                myThread.setAnsweredOn(self.makeDateTime(cal.parseDateTime(hist.find("date").text)))
                                break

                myThreads.append(myThread)

            else:
                print ("Thread of type " + t.get("threadtype") + " ignored. " + t.get("id"))

        # submit users to the database
        self.myDal.addUsers(myUsers)

        # submit threads to the database
        self.myDal.addThreadDetails(myThreads)

    def makeDateTime(self, input):
        input = input[0]
        print (input, " ", input[0])
        return datetime.datetime(input[0], input[1], input[2], input[3], input[4],input[5])

#myScraper = MsdnScraper()
#myScraper.scrapeForumsList()
#myScraper.scrapeThreadsList()
#myScraper.scrapeThreadDetail()




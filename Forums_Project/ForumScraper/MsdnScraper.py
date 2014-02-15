__author__ = 'Stephen'

from bs4 import BeautifulSoup
import urllib.request
import urllib.parse
import json
from DAL import DAL
import parsedatetime
from Thread import Thread
from User import User
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

        cal = parsedatetime.Calendar()

        threads = self.myDal.getThreadsList()

        while len(threads) > 0:

            myThreads = list()
            myUsers = dict()

            for threadId in threads:

                url = self.THREAD_URL_STUB.replace("###", threadId)
                print (url)
                soup = BeautifulSoup(urllib.request.urlopen(url))

                t = soup.find("thread")

                messages = soup.find("messages")
                firstMess = messages.find("message")

                myThread = Thread(t.get("id"), t.find("topic").text, clean_html_markup(firstMess.find("body").text), t.get("views"),
                                  t.get("subscribers"), iso8601.parse_date(t.find("createdon").text), firstMess.get("hascode") == "true", t.get("threadtype"))

                myThread.getContributor(t.get("authorid")).addFirstPost()

                # update list of users
                for user in soup.find("users").findAll("user"):
                    userId = user.get("id")
                    if not userId in myUsers:
                        role = user.find("role")
                        if role is None:
                            role = ""
                        else:
                            role = role.text

                        points = user.find("points")
                        if points is None:
                            points = 0
                        else:
                            points = int(points.text)

                        posts = user.find("posts")
                        if posts is None:
                            posts = 0
                        else:
                            posts = int(posts.text)

                        answers = user.find("answers")
                        if answers is None:
                            answers = 0
                        else:
                            answers = int(answers.text)

                        stars = user.find("stars")
                        if stars is None:
                            stars = 0
                        else:
                            stars = int(stars.text)

                        myUsers[userId] = User(userId, user.find("displayname").text, user.find("msft").text == "true"
                            , user.find("mscs").text == "true", user.find("mvp").text == "true"
                            , user.find("partner").text == "true", user.find("mcc").text == "true"
                            , iso8601.parse_date(user.find("lastactive").text)
                            , points, posts, answers, stars, role)

                # iterate through each message to get data not explicitly called out in attributes
                for message in messages.findAll("message"):

                    # keep track of newest post
                    myThread.setLastPostOn(iso8601.parse_date(message.find("createdon").text))

                    # update contributor stats
                    con = myThread.getContributor(message.get("authorid"))
                    con.addPost()
                    if message.get("hascode") == "true":
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
                                myThread.setAnsweredOn(iso8601.parse_date(hist.find("date").text))
                                break

                myThreads.append(myThread)


            # submit users to the database
            self.myDal.addUsers(myUsers)

            # submit threads to the database
            self.myDal.addThreadDetails(myThreads)

            threads = self.myDal.getThreadsList()

def clean_html_markup(s):
    tag = False
    quote = False
    out = ""

    for c in s:
            if c == '<' and not quote:
                tag = True
            elif c == '>' and not quote:
                tag = False
            elif (c == '"' or c == "'") and tag:
                quote = not quote
            elif not tag:
                out = out + c

    return out.replace("&gt;",">").replace("&lt;", "<").replace("&apos;","'").replace("&quot;", "\"")\
        .replace("&nbsp;"," ").replace("&amp;", "&").strip()

myScraper = MsdnScraper()
#myScraper.scrapeForumsList()
#myScraper.scrapeThreadsList()
myScraper.scrapeThreadDetail()


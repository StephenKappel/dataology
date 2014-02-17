__author__ = 'Stephen'

# import libraries for making web requests and parsing responses
from bs4 import BeautifulSoup
import urllib.request
import urllib.parse
import json
import iso8601
import parsedatetime
from datetime import datetime, tzinfo, timedelta

# import my own modules
from DAL import DAL
from Thread import Thread
from User import User
from GMT import GMT

# a class for gathering a data about categories, forums, threads, contributors, and users from MSDN
class MsdnScraper():

    # the contents of this html file were attained by going to http://social.msdn.microsoft.com/Forums/en-US/home
    # selecting the [ View All ] link, inspecting the element of the dialog box, and saving the exposed DOM
    FORUM_CATALOG_PATH = "C:\\Users\\Stephen\\Documents\\GitHub\\dataology\\Forums_Project\\ForumScraper\\Sample_Markup\\MsdnForumsCatalog.html"

    # api url to get list of all forums in the category
    FORUM_DETAILS_API_STUB = "http://social.msdn.microsoft.com/Forums/api/category/getforumdetails?category="

    # page that lists all threads in a given forum
    THREAD_LIST_URL_STUB = "http://social.msdn.microsoft.com/Forums/en-US/home?filter=alltypes&sort=firstpostdesc"

    # url for getting xml document with a single thread's details
    THREAD_URL_STUB = "http://social.msdn.microsoft.com/Forums/en-US/###?outputAs=xml"

    # define the date range of thread start dates for which we want to get data
    MIN_DATE = datetime(2013, 1, 1, 0, 0, 0, 0, tzinfo = GMT())
    MAX_DATE = datetime(2014, 1, 1, 0, 0, 0, 0, tzinfo = GMT())

    # constructor
    # creates an instance of the data access layer module
    def __init__(self):
        self.myDal = DAL()

    # from html page saved locally, get a list of all the categories,
    # and use these categories to get forums from api
    def scrapeForumsList(self):

        count = 0

        # use Beautiful soup to get category names from html file
        soup = BeautifulSoup(open(self.FORUM_CATALOG_PATH))
        container = soup.find(id="allCategoryListContainer")
        categories = container.find_all(class_="categoryArea")

        # iterate through the categories to make one api call per category
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

    # get threads based on forum names, then for each thread get the thread details
    def scrapeThreadsComplete(self):

        # initialize calendar for parsing dates
        cal = parsedatetime.Calendar()

        # get forums from the database
        forums = self.myDal.getForumsList()

        # forum by forum...
        for forumKey in forums.keys():
            print("scraping this forum: " + forumKey)
            forumId = forums[forumKey]

            # create data structures for storing data for this forum before committing to database
            myThreads = list()
            myUsers = dict()

            # keep on looping through pages until I'm not getting anything new
            gotSome = True
            i = 0
            while gotSome:

                gotSome = False
                i += 1

                # use beautiful soup to parse thread id from the html
                url = self.THREAD_LIST_URL_STUB + "&forum=" + forumKey + "&page=" + str(i)
                listSoup = BeautifulSoup(urllib.request.urlopen(url))
                threads = listSoup.find_all(class_="threadblock")
                for thread in threads:

                    # parse thread id from the page
                    threadId = thread.get("data-threadid")

                    # create request url by using the threadId
                    url = self.THREAD_URL_STUB.replace("###", threadId)
                    #print (url)

                    # make request for xml
                    try:
                        scrapeTime = datetime.now()
                        soup = BeautifulSoup(urllib.request.urlopen(url))
                    except urllib.error.HTTPError:
                        # this occurs in the case that a thread has been deleted since the time when the thread id was scraped
                        continue

                    # start parsing thread
                    t = soup.find("thread")
                    messages = soup.find("messages")
                    firstMess = messages.find("message")

                    # check if the date is in the desired time range
                    createdOn = iso8601.parse_date(t.find("createdon").text)
                    if createdOn < self.MIN_DATE:
                        gotSome = False
                        break
                    gotSome = True
                    if createdOn >= self.MAX_DATE:
                        continue

                    # create thread object with top-level attributes initialized
                    myThread = Thread(t.get("id"), t.find("topic").text, clean_html_markup(firstMess.find("body").text), t.get("views"),
                                      t.get("subscribers"), createdOn, firstMess.get("hascode") == "true", t.get("threadtype"), scrapeTime)

                    # add in thread author
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

                        # keep track of newest post and first reply dates
                        myThread.addPostDate(iso8601.parse_date(message.find("createdon").text))

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

                print("scraped " + str(len(myThreads)) + " threads so far.")

            # after getting all threads for a given forum, make database submissions:
            # for users
            self.myDal.addUsers(myUsers)
            # for threads (including contributors)
            self.myDal.addThreads(myThreads,forumId)

# a function for removing ugly markup from message text
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
#myScraper.scrapeThreadDetail()
myScraper.scrapeThreadsComplete()


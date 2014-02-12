__author__ = 'Stephen'

from bs4 import BeautifulSoup
import urllib.request
import urllib.parse
import json
from pprint import pprint
from DAL import DAL

class MsdnScraper():

    # the contents of this html file were attained by going to http://social.msdn.microsoft.com/Forums/en-US/home
    # selecting the [ View All ] link, inspecting the element of the dialog box, and saving the exposed DOM
    FORUM_CATALOG_PATH = "C:\\Users\\Stephen\\Documents\\GitHub\\dataology\\Forums_Project\\ForumScraper\\MsdnForumsCatalog.html"
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
            catName = cat.get("data-categoryname")
            catTitle = cat.find(class_="categoryHeaderText").get("title")
            self.myDal.addCategory(catName, "MS", cat.get("data-categoryid"), catTitle)

            #use category names to make api requests and get details of specific forums
            with urllib.request.urlopen(self.FORUM_DETAILS_API_STUB + catName) as rawJson:
                data = rawJson.read().decode("utf8")
            data = json.loads(data)

            #save forums details to Forums table in database
            for i in range(len(data)):
                self.myDal.addForum(data[i]["Name"], "MS", data[i]["ForumId"], data[i]["Description"], catName, data[i]["DisplayName"])
                count += 1

            print (i, " forums added or updated, for ", catName)

            '''
            forums = cat.find_all(class_="forumItem")
            for f in forums:
                if f.has_attr("data-forumid"):
                    forumName = f.get("data-forumname")
                    self.page = urllib.request.urlopen(url)
            '''

        print (count, " forums added or updated, in total")

    def scrapeThreadsList(self):

        forums = self.myDal.getForumsList()
        for forumKey in forums.keys():
            print("getting threads for " + forumKey)
            forumId = forums[forumKey]
            for i in range(25):
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

        threads = self.myDal.getThreadList()
        for threadKey in threads.keys():
            threadId = threads[threadKey]
            url = self.THREAD_URL_STUB.replace("###", threadKey)
            soup = BeautifulSoup(urllib.request.urlopen(url))
            ## TODO: scrape thread details and write to database

myScraper = MsdnScraper()
#myScraper.scrapeForumsList()
#myScraper.scrapeThreadsList()


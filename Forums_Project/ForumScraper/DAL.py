__author__ = 'Stephen Kappel'

import pyodbc

class DAL:

    CONNECTION_STRING = "DSN=DataHogDB"
    FORUMS_LIST = "('sqlexpress','sqldataaccess','sharepointdevelopmentprevious','sharepointadminprevious','sharepointdevelopment'," \
                  "'sqlce','sharepointdevelopmentlegacy','sharepointgeneralprevious','sqlsmoanddmo','sharepointcustomizationprevious'," \
                  "'sqlreplication','sharepointgeneral','sqlservicebroker','sharepointadmin','sqlintegrationservices'," \
                  "'sqlreportingservices','sqlxml','sqlgetstarted','sqlsetupandupgrade','sqldisasterrecovery','sqldatawarehousing'," \
                  "'sqlkjpowerpointforsharepoint','sqldatamining','sqlmds','sqldatabaseengine','sqlspatial','sqlnotificationservices'," \
                  "'sqlsearch','sqldriverforphp','sharepointsearchlegacy','sharepointcustomization','sharepointsearch'," \
                  "'sqlkjpowerpivotforexcel','sqlnetfx','sqlsecurity','sharepointgenerallegacy','sqlanalysisservices'," \
                  "'sqldocumentation','sqldatabasemirroring','sqlkjmanageability','sharepointadminlegacy','sharepointcustomizationlegacy'," \
                  "'sqlservermigration','sharepointsearchprevious','sqlserversamples','sqlkjappmsmgmt','sqltools','sqldataqualityservices','sqlazurelabssupport')"

    def __init__(self):
        self.connection = pyodbc.connect(self.CONNECTION_STRING)

    # use to add or refresh record in the Forums table
    def addForum (self, name, company, nativeId, description, categoryID, dispName):
        cursor = self.connection.cursor()
        cursor.execute("""
              MERGE
	            [Forums].[dbo].[Forums] AS target
                USING (select ?,?,?,?,?,?) AS source ([Name],[Company],[ID],[Description],[Category_ID],[Display_Name])
                ON (target.[ID] = source.[ID])
              WHEN MATCHED THEN
                UPDATE SET target.Name = source.Name, target.Description = source.Description,
                    target.Category_ID = source.Category_ID, target.Display_Name = source.Display_Name
	        WHEN NOT MATCHED THEN
	            INSERT
                   ([Name]
                   ,[Company]
                   ,[ID]
                   ,[Description]
                   ,[Category_ID]
                   ,[Display_Name])
                VALUES
                   (?,?,?,?,?,?);
            """, name, company, nativeId, description, categoryID, dispName, name, company, nativeId, description, categoryID, dispName)
        self.connection.commit()

    # use to add or refresh record in the Categories table
    def addCategory (self, category, company, nativeId, dispName):
        cursor = self.connection.cursor()
        cursor.execute("""
              MERGE
	            [Forums].[dbo].[Categories] AS target
                USING (select ?,?,?,?) AS source ([Category],[Company],[ID],[Display_Name])
                ON (target.[ID] = source.[ID] and
                    target.[Display_Name] = source.[Display_Name])
              WHEN MATCHED THEN
                UPDATE SET target.Category = source.Category, target.Display_Name = source.Display_Name
	        WHEN NOT MATCHED THEN
	            INSERT
                   ([Category]
                   ,[Company]
                   ,[ID]
                   ,[Display_Name])
                VALUES
                   (?,?,?,?);
            """, category, company, nativeId, dispName, category, company, nativeId, dispName)
        self.connection.commit()

    def getForumsList (self):
        cursor = self.connection.cursor()
        cursor.execute("""
            SELECT distinct f.[ID]
                ,f.[Name]
            FROM [Forums].[dbo].[Forums] f
            WHERE f.[Name] IN """ + self.FORUMS_LIST)
        rows = cursor.fetchall()
        forums = dict()
        for row in rows:
            forums[row.Name] = row.ID
        return forums

    def addThread (self, threadId, forumId):
        cursor = self.connection.cursor()
        cursor.execute("""
            MERGE
	            [Forums].[dbo].[Threads] AS target
                USING (select ?,?) AS source ([Forum_ID],[ID])
                ON (target.[ID] = source.[ID])
	        WHEN NOT MATCHED THEN
	            INSERT
                   ([Forum_ID]
                   ,[ID])
                VALUES
                   (?,?);
            """,  forumId, threadId, forumId, threadId)
        self.connection.commit()

    def getThreadsList (self):
        cursor = self.connection.cursor()
        cursor.execute("""
            SELECT TOP 10 [ID]
            FROM [Forums].[dbo].[Threads]
            WHERE Scraped_On IS NULL
            """)
        rows = cursor.fetchall()
        threads = list()
        for row in rows:
            threads.append(row.ID)
        return threads

    def addThreads(self, threads, forumId):
        for thr in threads:
            cursor = self.connection.cursor()
            cursor.execute("""
            MERGE
	            [Forums].[dbo].[Threads] AS target
                USING (select ?,?) AS source ([Forum_ID],[ID])
                ON (target.[ID] = source.[ID])
	        WHEN NOT MATCHED THEN
	            INSERT
                   ([Forum_ID]
                   ,[ID]
                   ,[Title]
                   ,[Question]
                   ,[Views]
                   ,[Subscribers]
                   ,[Created_On]
                   ,[Answered_On]
                   ,[Last_Post_On]
                   ,[Answer_Has_Code]
                   ,[First_Post_Has_Code]
                   ,[Type]
                   ,[Scraped_On]
                   ,[First_Reply_On])
                VALUES
                   (?,?,?,?,?,?,?,?,?,?,?,?,?,?)
            WHEN MATCHED THEN
                UPDATE SET
                      [Title] = ?
                      ,[Question] = ?
                      ,[Views] = ?
                      ,[Subscribers] = ?
                      ,[Created_On] = ?
                      ,[Answered_On] = ?
                      ,[Last_Post_On] = ?
                      ,[Answer_Has_Code] = ?
                      ,[First_Post_Has_Code] = ?
                      ,[Type] = ?
                      ,[Scraped_On] = ?
                      ,[First_Reply_On] = ?
            ;
            """, forumId, thr.id, forumId, thr.id, thr.title, thr.question, thr.views, thr.subscribers, thr.createdOn,
                thr.answeredOn, thr.lastPostOn, thr.answerHasCode, thr.firstPostHasCode, thr.type, thr.scrapedOn,
                thr.firstReplyOn, thr.title, thr.question, thr.views, thr.subscribers, thr.createdOn, thr.answeredOn,
                thr.lastPostOn, thr.answerHasCode, thr.firstPostHasCode, thr.type, thr.scrapedOn, thr.firstReplyOn)
            self.connection.commit()

            for conKey in thr.contributors.keys():
                con = thr.contributors[conKey]
                cursor = self.connection.cursor()
                cursor.execute("""
                    MERGE
                        [Forums].[dbo].[Contributors] AS target
                        USING (select ?,?) AS source ([User_ID],[Thread_ID])
                        ON (target.[User_ID] = source.[User_ID] AND target.[Thread_ID] = source.[Thread_ID])
                    WHEN NOT MATCHED THEN
                        INSERT
                            ([User_ID]
                            ,[Thread_ID]
                            ,[First_Posts]
                            ,[Posts]
                            ,[Answers]
                            ,[Votes]
                            ,[Code_Posts])
                        VALUES
                           (?,?,?,?,?,?,?)
                    WHEN MATCHED THEN
                        UPDATE SET
                            [First_Posts] = ?
                            ,[Posts] = ?
                            ,[Answers] = ?
                            ,[Votes] = ?
                            ,[Code_Posts] = ?
                    ;
                """, con.userId, thr.id, con.userId, thr.id, con.firstPosts, con.posts, con.answers,
                               con.votes, con.code,  con.firstPosts, con.posts, con.answers,
                               con.votes, con.code)
                self.connection.commit()

    def addUsers (self, users):
        for userId in users.keys():
            u = users[userId]
            cursor = self.connection.cursor()
            cursor.execute("""
                MERGE
                    [Forums].[dbo].[Users] AS target
                    USING (select ?) AS source ([ID])
                    ON (target.[ID] = source.[ID])
                WHEN NOT MATCHED THEN
                    INSERT
                       ([ID]
                          ,[Display_Name]
                          ,[MSFT]
                          ,[MSCS]
                          ,[MVP]
                          ,[Partner]
                          ,[MCC]
                          ,[LastActive]
                          ,[Points]
                          ,[Posts]
                          ,[Answers]
                          ,[Stars]
                          ,[Role])
                    VALUES
                       (?,?,?,?,?,?,?,?,?,?,?,?,?);
                """,  userId, userId, u.displayName, u.msft, u.mscs, u.mvp, u.partner, u.mcc,
                           u.lastActive, u.points, u.posts, u.answers, u.stars, u.role)
            self.connection.commit()

    def deleteThread(self, threadId):
        cursor = self.connection.cursor()
        cursor.execute("""
            DELETE FROM [Forums].[dbo].[Threads] WHERE ID = ?
            """,  threadId)
        self.connection.commit()






__author__ = 'Stephen Kappel'

import pyodbc

class DAL:

    CONNECTION_STRING = "DSN=DataHogDB"

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
            SELECT [ID]
                ,[Name]
            FROM [Forums].[dbo].[Forums]
            WHERE [Name] LIKE 'sql%' or [Name] LIKE 'sharepoint%'
            """)
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
            """)
        rows = cursor.fetchall()
        threads = list()
        for row in rows:
            threads.append(row.ID)
        return threads

    def addThreadDetails(self, threadId, title, views, subscribers, question, hasCode, createdOn, answeredOn, replies,
                         contributors, authorId, answererId, lastReplyOn):
        cursor = self.connection.cursor()
        cursor.execute("""
            MERGE
	            [Forums].[dbo].[Threads] AS target
                USING (select ?,?,?,?,?,?,?,?,?,?,?,?,?) AS source  ([ID]
           ,[Title]
           ,[Views]
           ,[Subscribers]
           ,[Question]
           ,[Has_Code]
           ,[Created_On]
           ,[Answered_On]
           ,[Replies]
           ,[Contributors]
           ,[Author_ID]
           ,[Answerer_ID]
           ,[Last_Reply_On])
                ON (target.[ID] = source.[ID])
	        WHEN NOT MATCHED THEN
	            INSERT INTO [dbo].[Threads]
                   ([Title]
           ,[Views]
           ,[Subscribers]
           ,[Question]
           ,[Has_Code]
           ,[Created_On]
           ,[Answered_On]
           ,[Replies]
           ,[Contributors]
           ,[Author_ID]
           ,[Answerer_ID]
           ,[Last_Reply_On])
                VALUES
                   (?,?,?,?,?,?,?,?,?,?,?,?)

            INSERT INTO [dbo].[Threads]
        """, threadId, title, views, subscribers, question, hasCode, createdOn, answeredOn, replies,
                         contributors, authorId, answererId, lastReplyOn, title, views, subscribers, question, hasCode,
                         createdOn, answeredOn, replies, contributors, authorId, answererId, lastReplyOn)
        self.connection.commit()



__author__ = 'Stephen Kappel'

import pyodbc

class DAL:

    CONNECTION_STRING = "DSN=DataHogDB"

    def __init__(self):
        self.connection = pyodbc.connect(self.CONNECTION_STRING)

    # use to add or refresh record in the Forums table
    def addForum (self, name, company, nativeId, description, category, dispName):
        cursor = self.connection.cursor()
        cursor.execute("""
              MERGE
	            [Forums].[dbo].[Forums] AS target
                USING (select ?,?,?,?,?,?) AS source ([Name],[Company],[Native_Identifier],[Description],[Category],[Display_Name])
                ON (target.[Native_Identifier] = source.[Native_Identifier])
              WHEN MATCHED THEN
                UPDATE SET target.Name = source.Name, target.Description = source.Description,
                    target.Category = source.Category, target.Display_Name = source.Display_Name
	        WHEN NOT MATCHED THEN
	            INSERT
                   ([Name]
                   ,[Company]
                   ,[Native_Identifier]
                   ,[Description]
                   ,[Category]
                   ,[Display_Name])
                VALUES
                   (?,?,?,?,?,?);
            """, name, company, nativeId, description, category, dispName, name, company, nativeId, description, category, dispName)
        self.connection.commit()

    # use to add or refresh record in the Categories table
    def addCategory (self, category, company, nativeId, dispName):
        cursor = self.connection.cursor()
        cursor.execute("""
              MERGE
	            [Forums].[dbo].[Categories] AS target
                USING (select ?,?,?,?) AS source ([Category],[Company],[Native_Identifier],[Display_Name])
                ON (target.[Native_Identifier] = source.[Native_Identifier] and
                    target.[Display_Name] = source.[Display_Name])
              WHEN MATCHED THEN
                UPDATE SET target.Category = source.Category, target.Display_Name = source.Display_Name
	        WHEN NOT MATCHED THEN
	            INSERT
                   ([Category]
                   ,[Company]
                   ,[Native_Identifier]
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
                USING (select ?,?) AS source ([Forum_ID],[Native_Identifier])
                ON (target.[Native_Identifier] = source.[Native_Identifier])
	        WHEN NOT MATCHED THEN
	            INSERT
                   ([Forum_ID]
                   ,[Native_Identifier])
                VALUES
                   (?,?);
            """,  forumId, threadId, forumId, threadId)
        self.connection.commit()

    def getThreadsList (self):
        cursor = self.connection.cursor()
        cursor.execute("""
            SELECT TOP 10 [ID]
              ,[Native_Identifier]
            FROM [Forums].[dbo].[Threads]
            """)
        rows = cursor.fetchall()
        threads = dict()
        for row in rows:
            threads[row.Native_Identifier] = row.ID
        return threads



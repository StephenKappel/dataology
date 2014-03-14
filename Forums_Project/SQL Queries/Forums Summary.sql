SELECT top 100
	Forum_ID = f.ID
	, Forum_Name = f.Name
	, Forum_Display_Name = f.Display_Name
	, Forum_Category = cat.Display_Name
	, Num_Threads = count(*)
	, Num_Unique_Contributors = (select count(distinct c.User_ID) from Forums.dbo.Threads t INNER JOIN Forums.dbo.Contributors c on c.Thread_ID = t.ID where t.Forum_ID = f.ID)
	, Avg_Thread_Contributors = AVG(ts.Num_Contributors * 1.0)
	, Avg_Contributor_Points = (select AVG(u.Points * 1.0) from Forums.dbo.Threads t INNER JOIN Forums.dbo.Contributors c on c.Thread_ID = t.ID INNER JOIN Forums.dbo.Users u on u.ID = c.User_ID where t.Forum_ID = f.ID)
	, Avg_Contributors_Stars = (select AVG(u.Stars * 1.0) from Forums.dbo.Threads t INNER JOIN Forums.dbo.Contributors c on c.Thread_ID = t.ID INNER JOIN Forums.dbo.Users u on u.ID = c.User_ID where t.Forum_ID = f.ID)
	, Avg_Num_Posts = AVG(ts.Num_Posts * 1.0)
	, Num_Answered_Threads = sum(case when ts.Answered = 1 then 1 else 0 end)
	, Avg_Answers = AVG(ts.Num_Answers * 1.0)
	, Mean_Time_To_Answer = AVG(ts.Time_To_Answer * 1.0)
	, Mean_Time_To_Response = AVG(ts.Time_To_First_Reply * 1.0)
	, Avg_Num_Subscribers = AVG(ts.Num_Subscribers * 1.0)
	, Avg_Num_Views = AVG(ts.Num_Views * 1.0)
	, Avg_Num_Votes = AVG(ts.Num_Votes * 1.0)
	, Avg_Title_Length = AVG(ts.Title_Length * 1.0)
	, Avg_Question_Length = AVG(ts.Question_Length * 1.0)
	, Num_Threads_With_Code = sum(case when ts.Num_Code_Posts > 0 then 1 else 0 end)
	, Avg_Code_Posts = AVG(ts.Num_Code_Posts * 1.0)
	, Num_Questions_With_Code = sum(case when ts.Question_Has_Code = 1 then 1 else 0 end)
	, Num_Threads_With_MSFT = sum(case when ts.Num_MSFT_Posts > 0 then 1 else 0 end)
	, Num_Threads_With_MVP = sum(case when ts.Num_MVP_Posts > 0 then 1 else 0 end)
	, Num_Threads_With_Partner = sum(case when ts.Num_Partner_Posts > 0 then 1 else 0 end)

FROM  Forums.dbo.Forums f INNER JOIN
    Forums.dbo.Categories cat ON cat.ID = f.Category_ID
	INNER JOIN Forums.dbo.Thread_Summary ts ON f.ID = ts.Forum_ID

GROUP BY
	f.ID
	, f.Name
	, f.Display_Name
	, cat.Display_Name
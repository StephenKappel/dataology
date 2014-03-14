SELECT top 100
	Thread_ID = t.ID
	, Forum_ID = t.Forum_ID
	, Title = t.Title
	, Title_Length = Len(ltrim(rtrim(t.Title)))
	, Thread_Type = t.Type
	, Question = t.Question
	, Question_Length = Len(ltrim(rtrim(t.Question)))
	, Question_Has_Code = t.First_Post_Has_Code
	, Num_Subscribers = t.Subscribers
	, Num_Views = t.Views	

	, Answered = CAST(case when t.Answered_On = '1-jan-3000' then 0 else 1 end As bit)
	, Answered_On = t.Answered_On
	, Answer_Has_Code = t.Answer_Has_Code
	, Time_To_Answer = case when t.Answered_On = '1-jan-3000' then NULL else DATEDIFF(MINUTE, t.Created_On, t.Answered_On) end
	, Time_To_First_Reply = case when t.First_Reply_On = '1-jan-3000' then NULL else DATEDIFF(MINUTE, t.Created_On, t.First_Reply_On) end

	, Num_Contributors = count(distinct c.User_ID)
	, Num_Posts = sum(c.Posts)
	, Num_Answers = sum(c.Answers)
	, Num_Code_Posts = SUM(c.Code_Posts)
	, Num_Votes = sum(c.Votes)	

	, Num_MSFT_Contributors = sum(cast(u.MSFT as int))
	, Num_MSFT_Posts = sum(case when u.MSFT = 1 then c.Posts else 0 end)
	, Num_MSFT_Answers = sum(case when u.MSFT = 1 then c.Answers else 0 end)
	, Num_MSFT_Code_Posts = sum(case when u.MSFT = 1 then c.Posts else 0 end)
	, Num_MSFT_Votes = sum(case when u.MSFT = 1 then c.Votes else 0 end)

	, Num_MVP_Contributors = sum(cast(u.MVP as int))
	, Num_MVP_Posts = sum(case when u.MVP = 1 then c.Posts else 0 end)
	, Num_MVP_Answers = sum(case when u.MVP = 1 then c.Answers else 0 end)
	, Num_MVP_Code_Posts = sum(case when u.MVP = 1 then c.Posts else 0 end)
	, Num_MVP_Votes = sum(case when u.MVP = 1 then c.Votes else 0 end)

	, Num_Partner_Contributors = sum(cast(u.Partner as int))
	, Num_Partner_Posts = sum(case when u.Partner = 1 then c.Posts else 0 end)
	, Num_Partner_Answers = sum(case when u.Partner = 1 then c.Answers else 0 end)
	, Num_Partner_Code_Posts = sum(case when u.Partner = 1 then c.Posts else 0 end)
	, Num_Partner_Votes = sum(case when u.Partner = 1 then c.Votes else 0 end)

	, Avg_Contributor_Points = AVG(u.Points)
	, Avg_Contributor_Stars = AVG(u.Stars)

	, Created_On = t.Created_On
	, Created_Month = DATEPART(MONTH, t.Created_On)
	, Created_Week_Day = DATEPART(WEEKDAY, t.Created_On)
	, Created_Hour = DATEPART(HOUR, t.Created_On)

FROM  Forums.dbo.Threads t 
	Inner Join Forums.dbo.Contributors c on t.ID = c.Thread_ID
	Inner Join Forums.dbo.Users u on u.ID = c.User_ID

GROUP BY
	t.ID
	, t.Forum_ID
	, t.Title
	, t.Question
	, t.Type
	, t.Subscribers
	, t.Views
	, t.Answered_On
	, t.Created_On
	, t.Answer_Has_Code
	, t.First_Post_Has_Code
	, t.First_Reply_On
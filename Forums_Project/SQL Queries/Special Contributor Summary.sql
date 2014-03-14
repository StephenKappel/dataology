select

	Thread_ID = c.Thread_ID

	, MSFT_Posts = sum(case when u.MSFT = 1 then c.Posts else 0 end)
	, MSFT_Answers = sum(case when u.MSFT = 1 then c.Answers else 0 end)
	, MSFT_Code_Posts = sum(case when u.MSFT = 1 then c.Posts else 0 end)
	, MSFT_Votes = sum(case when u.MSFT = 1 then c.Votes else 0 end)

	, Avg_Points = AVG(u.Points)
	, Avg_Stars = AVG(u.Stars)

	, Num_Contributors = Count(*)

From Forums.dbo.Users u
	Inner Join Forums.dbo.Contributors c on u.ID = c.User_ID

Group By c.Thread_ID
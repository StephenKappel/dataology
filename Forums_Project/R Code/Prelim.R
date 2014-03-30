library(RODBC)
library(ggplot2)
library(ggthemes)

#create connection to database
myDB = odbcConnect("LocalSQL")

#query the database and put results in a dataframe
forums = sqlQuery(myDB, "SELECT * FROM Forums.dbo.Forum_Summary", stringsAsFactors=FALSE)

#make sure data is loaded as expected
head(forums)

#plot MTTR vs. num contributors
plot(forums$Num_Unique_Contributors, forums$Mean_Time_To_Answer, main="MTTR vs. Unique Contributors", xlab="Unique Contributors in 2013", ylab="Mean Time to Resolution (days)")
#plot MTTR vs. num contributors for forums with more than 100 threads
with(forums[forums$Num_Threads >= 100 & forums$Mean_Time_To_Answer < 30 & forums$Forum_Category=='SQL Server',], plot(Num_Unique_Contributors, Mean_Time_To_Answer, main="MTTR vs. Unique Contributors for Forums with >= 100 Threads", xlab="Unique Contributors in 2013", ylab="Mean Time to Resolution (days)"))
reg = with(forums[forums$Num_Threads >= 100 & forums$Mean_Time_To_Answer < 30,],lm(Mean_Time_To_Answer~Num_Unique_Contributors))
abline(reg)

# plot scatter with regression line for time to answer vs. contributors
forums.50.answers = forums[forums$Num_Answered_Threads >= 50 ,]
g = ggplot(forums.50.answers, aes(x=Num_Unique_Contributors, y=Mean_Time_To_Answer))
g = g + geom_point(aes(color=Forum_Category))
g = g + labs(title="MTTA vs. Unique Contributors", x="Unique Contributors in 2013", y="Mean Time to Answer (days)")
g = g + theme_tufte() + scale_colour_excel()
g = g + geom_smooth(method="lm", aes(color=Forum_Category))
g = g + coord_cartesian(ylim=c(0,max(forums.50.answers$Mean_Time_To_Answer) + 2))
g

# plot scatter with regression for time to response vs. contributors
# observation 1: with same number of contributors, SharePoint MTTR appears slower than SQL forums
# observation 2: more contributors seems to correlate with quicker responses (especially for SharePoint)
forums.50.threads = forums[forums$Num_Threads >= 50 ,]
g = ggplot(forums.50.threads, aes(x=Num_Unique_Contributors, y=Mean_Time_To_Response))
g = g + geom_point(aes(color=Forum_Category))
g = g + labs(title="MTTR vs. Unique Contributors", x="Unique Contributors in 2013", y="Mean Time to Response (days)")
g = g + theme_tufte() + scale_colour_excel()
#g = g + geom_smooth(method="lm", aes(color=Forum_Category))
g = g + coord_cartesian(ylim=c(0,max(forums.50.threads$Mean_Time_To_Response) + 2))
g

# plot scatter  with regression for time to response vs. % with MSFT
# observation: more MSFT involvement and quicker response times for SQL Server vs. SharePoint
forums.50.threads = forums[forums$Num_Threads >= 50 ,]
g = ggplot(forums.50.threads, aes(x=Num_Threads_With_MSFT/Num_Threads, y=Mean_Time_To_Response))
g = g + geom_point(aes(color=Forum_Category))
g = g + labs(title="MTTR vs. MSFT Involvement", x="Portion of Threads with MSFT involvement", y="Mean Time to Response (days)")
g = g + theme_tufte() + scale_colour_excel()
g = g + geom_smooth(method="lm", color=black)
g = g + coord_cartesian(ylim=c(0,max(forums.50.threads$Mean_Time_To_Response) + 2))
g

# plot scatter  with regression for time to answer vs. % with MSFT
# observeration: more MSFT involvement and quicker response times for SQL Server vs. SharePoint
forums.50.threads = forums[forums$Num_Threads >= 50 ,]
g = ggplot(forums.50.threads, aes(x=Num_Threads_With_MSFT/Num_Threads, y=Mean_Time_To_Answer))
g = g + geom_point(aes(color=Forum_Category))
g = g + labs(title="MTTA vs. MSFT Involvement", x="Portion of Threads with MSFT involvement", y="Mean Time to Answer (days)")
g = g + theme_tufte() + scale_colour_excel()
#g = g + geom_smooth(method="lm")
g = g + coord_cartesian(ylim=c(0,max(forums.50.threads$Mean_Time_To_Answer) + 2))
g

# plot scatter  with regression for time to answer vs. % with MVPs
forums.50.threads = forums[forums$Num_Threads >= 50 ,]
g = ggplot(forums.50.threads, aes(x=Num_Threads_With_MVP/Num_Threads, y=Mean_Time_To_Answer))
g = g + geom_point(aes(color=Forum_Category))
g = g + labs(title="MTTA vs. MVP Involvement", x="Portion of Threads with MVP involvement", y="Mean Time to Answer (days)")
g = g + theme_tufte() + scale_colour_excel()
g = g + geom_smooth(method="lm")
g = g + coord_cartesian(ylim=c(0,max(forums.50.threads$Mean_Time_To_Answer) + 2))
g

# plot scatter  with regression for time to answer vs. % with Partners
# a lot more partner involvement in SharePoint, but no correlation with MTTA
forums.50.threads = forums[forums$Num_Threads >= 50 ,]
g = ggplot(forums.50.threads, aes(x=Num_Threads_With_Partner/Num_Threads, y=Mean_Time_To_Answer))
g = g + geom_point(aes(color=Forum_Category))
g = g + labs(title="MTTA vs. Partner Involvement", x="Portion of Threads with Partner involvement", y="Mean Time to Answer (days)")
g = g + theme_tufte() + scale_colour_excel()
g = g + geom_smooth(method="lm")
g = g + coord_cartesian(ylim=c(0,max(forums.50.threads$Mean_Time_To_Answer) + 2))
g

# plot scatter with regression for time to answer vs. avg. views per thread
# observeration: SharePoint forums are less viewed, but there is not strong correlation with MTTA
forums.50.threads = forums[forums$Num_Threads >= 50 ,]
g = ggplot(forums.50.threads, aes(x=Avg_Num_Views, y=Mean_Time_To_Answer))
g = g + geom_point(aes(color=Forum_Category))
g = g + labs(title="MTTA vs. Views/Thread", x="Average Views per Thread", y="Mean Time to Answer (days)")
g = g + theme_tufte() + scale_colour_excel()
g = g + geom_smooth(method="lm")
g = g + coord_cartesian(ylim=c(0,max(forums.50.threads$Mean_Time_To_Answer) + 2))
g

# plot scatter with regression for time to answer vs. avg. contributors per thread
# observeration: 
forums.50.threads = forums[forums$Num_Threads >= 50 & forums$Mean_Time_To_Answer < 30 ,]
g = ggplot(forums.50.threads, aes(x=Avg_Thread_Contributors, y=Mean_Time_To_Answer))
g = g + geom_point(aes(color=Forum_Category))
g = g + labs(title="MTTA vs. Views/Thread", x="Average Contributors per Thread", y="Mean Time to Answer (days)")
g = g + theme_tufte() + scale_colour_excel()
g = g + geom_smooth(method="lm")
g = g + coord_cartesian(ylim=c(0,max(forums.50.threads$Mean_Time_To_Answer) + 2))
g

# plot scatter with regression for avg. views vs. avg. contributors per thread
# observeration: SharePoint forums are low contributors and views/thread; SQL server is in every other quadrant
forums.50.threads = forums[forums$Num_Threads >= 50,]
g = ggplot(forums.50.threads, aes(x=Avg_Thread_Contributors, y=Avg_Num_Views))
g = g + geom_point(aes(color=Forum_Category))
g = g + labs(title="Contributors/Thread vs. Views/Thread", x="Average Contributors per Thread", y="Average Views per Thread")
g = g + theme_tufte() + scale_colour_excel()
#g = g + geom_smooth(method="lm")
#g = g + coord_cartesian(ylim=c(0,max(forums.50.threads$Mean_Time_To_Answer) + 2))
g

# plot scatter with regression for avg. views vs. avg. contributors per thread
# observeration: SharePoint forums are low contributors and views/thread; SQL server is in every other quadrant
forums.50.threads = forums[forums$Num_Threads >= 50,]
g = ggplot(forums.50.threads, aes(x=Avg_Num_Votes, y=Avg_Num_Views))
g = g + geom_point(aes(color=Forum_Category))
g = g + labs(title="Views vs. Votes", x="Average Votes per Thread", y="Average Views per Thread")
g = g + theme_tufte() + scale_colour_excel()
#g = g + geom_smooth(method="lm")
#g = g + coord_cartesian(ylim=c(0,max(forums.50.threads$Mean_Time_To_Answer) + 2))
g

# plot scatter  with regression for % threads answered vs. % with MSFT
# observeration: 
forums.50.threads = forums[forums$Num_Threads >= 50 ,]
g = ggplot(forums.50.threads, aes(x=Num_Threads_With_MSFT/Num_Threads, y=Num_Answered_Threads/Num_Threads))
g = g + geom_point(aes(color=Forum_Category))
g = g + labs(title="Theads Answered vs. MSFT Involvement", x="Portion of Threads with MSFT involvement", y="Portion of Threads Answered")
g = g + theme_tufte() + scale_colour_excel()
#g = g + geom_smooth(method="lm")
g = g + coord_cartesian(ylim=c(0,1), xlim=c(0,1))
g
                   
# create small multiples
# did not turn out to be very helpful
f2 = subset(forums, select=c(Mean_Time_To_Answer, Mean_Time_To_Response, Avg_Num_Votes, Votes_Per_View, Percent_Threads_Answered, Avg_Answers, Num_Threads_With_MSFT, Num_Threads_With_MVP, Num_Unique_Contributors, Avg_Contributor_Points))
GGally::ggpairs(f2)

# plot scatter
# observeration: 
forums.100.threads.20.MTTA = forums[forums$Num_Threads >= 100 & forums$Mean_Time_To_Answer <= 20,]
g = ggplot(forums.100.threads.20.MTTA, aes(x=Num_Answered_Threads/Num_Threads, y=Mean_Time_To_Answer))
g = g + geom_point(aes(color=Forum_Category, size=Num_Unique_Contributors))
g = g + labs(x="Portion of Threads Answered", y="Mean Time to Answer (days)")
g = g + theme_tufte() + scale_colour_excel()
#g = g + geom_smooth(method="lm")
g = g + coord_cartesian(xlim=c(0,1))
g

#histogram - unique contributors/num thread
hist(forums$Num_Unique_Contributors / forums$Num_Threads, breaks=5)

# #get summary data about creation dates
# summary(threads$Created_On)
# summary(as.POSIXlt(threads$Created_On)$mon)
# 
# #create a histogram to see # of threads created each day of the week
# #observation: as expected, lowest volume on weekends, highest volume on Wednedsay
# wbins=seq(0,7,by=1)
# hist(as.POSIXlt(threads$Created_On)$wday + 1, main = "Threads by Week Day", xlab = "Day of Week", breaks=wbins, labels = TRUE)
# 
# ##create a histogram to see # of threads created each month of year
# #observation: sudden drop off in volume in 3rd quarter
# mbins=seq(0,12,by=1)
# hist(as.POSIXlt(threads$Created_On)$mon + 1, main = "Threads by Month", xlab = "Month", breaks=mbins, labels = TRUE)
# 
# ##plot a scatter of views vs. day of week posted
# #observation: nothing particularly interesting; there are a few posts that really stand out from the pack
# plot(jitter(as.POSIXlt(threads$Created_On)$wday + 1),  threads$Views, xlab = "Day of Week", ylab = "Views",main = "Views by Creation Day", log="y")
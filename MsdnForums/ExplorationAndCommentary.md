Exploring MSDN Forum Data
========================================================




Introduction
-------------------------
Working in a technical support organization, I have come to appreciate the value of forums in deflecting issues before they reach support queues. Smaller volumes of issues that support engineers need to work on translates to lowers costs and generally happier customers. In this project, I want to ask: What factors make a forum successful (or unsuccessful)? Through data exploration, I hope to gain actionable insights into the things an organization can do (or avoid doing) to accelerate the successful-ness of forums and the deflection of support issues.

The notion of *success* in a forum is not easy to directly quantify. In a perfect world, we would want to measure the number of support issues *not* opened, which is obviously not possible in our reality. Therefore, we must use indirect measures to give us a directionally-correct understanding of our successfulness. Based on experience, I have chosen to quantify success in the following ways:

* For a forum as a whole:
  * Percent of threads answered (higher is better)
  * Mean time to first answer (faster is better)
  * Mean number of answers per thread (more is better)
  * Mean number of votes per thread (more is better)
  * Mean number of votes per view (more is better)
* For a single thread:
  * Number of answers (more is better; zero is particularly bad)
  * Time to first answer, if applicable (faster is better)
  * Number of votes (more is better)
  * Mean number of votes per view (more is better)

In order to limit this project to publicly available information and use forums with which I had some prior experience, I decided to focus the project around the SharePoint and SQL Server [forums on MSDN (Microsoft Developer Network)](http://social.msdn.microsoft.com/Forums/en-US/home).

DISCLAIMER: The work that follows is not intended to be a finely-proofed and edited report on the effectiveness of forums. It is an exploration, with notes on my thoughts as I explored this data for the first time. My graphics leave much to be desired and are intended more for my understanding of the data than for publication or general circulation to a broader audience. There will be plenty of time later for having some fun with D3 :-).

Gathering and Preparing the Data
----------------------------------------
All the data that I am interested in for an initial analysis is easily accessible by surfing the forums in a web browser. However, no API exists for getting a consolidated and nicely-formatted data export of the forums' content. Therefore, I used Python to scrape the desired data from MSDN web pages. As a repository for the scraped data, I created a SQL Server Express database.

My scraping procedure followed these high-level steps:
* __Get a list of all the MSDN forum categories.__ I did this by parsing the source for the forum selection dialog box on MSDN. That much was easy.
* __Get a list of all the MSDN forums.__ Using the forum categories, I was able to make requests in the following format to get the forums belonging to each category: social.msdn.microsoft.com/Forums/api/category/getforumdetails?category=[category name]
* __For each forum, get a list of thread IDs.__ This was accomplished with a Python script that set the forum filter and iterated through the pages of the listed threads, scraping the thread IDs from the page source.
* __Use each thread ID to get an XML version of the thread.__ Conveniently, a web request like the following returns all the thread details in XML: social.msdn.microsoft.com/Forums/en-US/[thread id]?outputAs=xml
* __Parse the XML and save the results to the database.__ From the XML, I selectively parsed characteristics of interest to me, and I calculated some derived values based on what was given. 

To keep my initial exploration to a managable level while giving me enough to make it interesting, I scraped all the SharePoint and SQL (well, actually, only the ones in English) and all the threads in calendar year 2013.

To make my life easier, I created two views in my database that would make things cleaner when it was time to start playing with the data in R:
* Forum_Summary aggregates data at the forum level. That is, the view has one row for each forum, and the metrics reflect the attributes of the forum as a whole.
* Thread_Summmary aggregates data at the thread level. That is, the view has one row for each thread, and the metrics reflect only the attributes of only a single thread.

Note that my script scraped threads of all types from MSDN. This includes *comment* threads, which are either general discussion threads (which cannot be answered) or locked threads. To avoid these from muddying my results, the Forum_Summary and Thread_Summary views exclude *comment* threads (of which I scraped 1,498).

Looking at Forums
----------------------------
I started my analysis in R at the forum level, using the data from my Forum_Summary database view.


```r
# use RODBC to connect to the database
library(RODBC)

# create connection to database (assuming local odbc connection LocalSQL is already 
# configured)
myDB <- odbcConnect("LocalSQL")
# query the database and put results in a dataframe
forums <- sqlQuery(myDB, "SELECT * FROM Forums.dbo.Forum_Summary", stringsAsFactors=FALSE)

# make sure data is loaded as expected
# we should have 48 forums (15 for SharePoint and 33 for SQL Server)
nrow(forums)
```

```
## [1] 48
```

```r
# let's see the column names
colnames(forums)
```

```
##  [1] "Forum_ID"                      "Forum_Display_Name"           
##  [3] "Forum_Category"                "Percent_Threads_Answered"     
##  [5] "Mean_Time_To_First_Answer"     "Avg_Answers"                  
##  [7] "Avg_Num_Votes"                 "Avg_Votes_Per_View"           
##  [9] "Num_Threads"                   "Num_Unique_Contributors"      
## [11] "Mean_Time_To_First_Response"   "Avg_Num_Posts"                
## [13] "Avg_Num_Subscribers"           "Avg_Num_Views"                
## [15] "Avg_Question_Length"           "Percent_Threads_With_Code"    
## [17] "Avg_Thread_Contributors"       "Avg_Thread_Contributor_Points"
## [19] "Avg_Thread_Contributors_Stars" "Percent_Threads_With_MSFT"    
## [21] "Percent_Threads_With_MVP"      "Percent_Threads_With_Partner"
```


Note that we have 22 columns. The first 3 are non-numeric and identify the column and its category (SQL Server or SharePoint). The next 5 columns are the success metrics. The remaining 14 are numeric attributes that could help us explain differences in the observed success metrics.

### Distributions

As a start, I want to see how my success metrics are distributed. Is there a wide enough spread among forums for these to be meaningful metrics? Anything that jumps out? Let's create a histogram for each of them.


```r
# get ready to use ggplot2
library(ggplot2)
library(ggthemes)

# create ggplot2 object
ggf <- ggplot(data = forums) + labs(title = "SQL & SharePoint Forums")

# how many bins should be used in each graph?
nbins <- 10

# for each success metric
for (ind in 4:8){
  # plot a histogram
  print(ggf + geom_histogram(aes_string(x = colnames(forums)[ind]), binwidth = diff(range(forums[,ind]))/nbins))
}

rm(ggf)
```

![plot of chunk forums.hist](figure/forums_hist1.png) ![plot of chunk forums.hist](figure/forums_hist2.png) ![plot of chunk forums.hist](figure/forums_hist3.png) ![plot of chunk forums.hist](figure/forums_hist4.png) ![plot of chunk forums.hist](figure/forums_hist5.png) 


The results look normal-ish, but the small sample size gives us only a rough picture. The vote-related graphs are skewed by some outliers, so let's remove the outliers and replot.

```r
forums.sub <- subset(forums, Avg_Votes_Per_View < 0.001)
gg2 <- ggplot(data = forums.sub) + labs(title = "SQL & SharePoint Forums")
gg2 + geom_histogram(aes(x = Avg_Votes_Per_View), binwidth = 0.0001)

forums.sub <- subset(forums, Avg_Num_Votes < 0.75)
gg2 <- ggplot(data = forums.sub) + labs(title = "SQL & SharePoint Forums")
gg2 + geom_histogram(aes(x = Avg_Num_Votes), binwidth = 0.05)

rm(forums.sub, gg2)
```

![plot of chunk forums.hist2](figure/forums_hist21.png) ![plot of chunk forums.hist2](figure/forums_hist22.png) 


What happens if we break these each into two graph -- once for each forum category? How do the two forums compare?


```r
# create ggplot2 objects for each category
forums.sp <- subset(forums, Forum_Category == "SharePoint")
ggsp <- ggplot(data = forums.sp) + 
  labs(y="Number of Forums", title = "SharePoint Forums")
forums.sql <- subset(forums, Forum_Category == "SQL Server")
ggsql <- ggplot(data = forums.sql) +
  labs(y="Number of Forums", title = "SQL Forums")

# for each success metric
for (ind in 4:8){
  # plot a histogram for SQL server
  print(ggsql + geom_histogram(aes_string(x = colnames(forums)[ind]),
    binwidth = diff(range(forums.sql[,ind]))/nbins))
  # plot a histogram for SharePoint server
  print(ggsp + geom_histogram(aes_string(x = colnames(forums)[ind]),
    binwidth = diff(range(forums.sp[,ind]))/nbins))
}
rm(ggsp, ggsql, nbins)
```

![plot of chunk forums.hist3](figure/forums_hist31.png) ![plot of chunk forums.hist3](figure/forums_hist32.png) ![plot of chunk forums.hist3](figure/forums_hist33.png) ![plot of chunk forums.hist3](figure/forums_hist34.png) ![plot of chunk forums.hist3](figure/forums_hist35.png) ![plot of chunk forums.hist3](figure/forums_hist36.png) ![plot of chunk forums.hist3](figure/forums_hist37.png) ![plot of chunk forums.hist3](figure/forums_hist38.png) ![plot of chunk forums.hist3](figure/forums_hist39.png) ![plot of chunk forums.hist3](figure/forums_hist310.png) 


### Correlation

Next, let's calculate the correlations between each of the metrics. Let's look at these for all 48 forums, plus for the SQL Server and SharePoint forums separately to see if we get more clear results.


```r
# load reshape so we can "melt"
library(reshape)

# create some stuff that I can reuse between plots
fill.grad <- scale_fill_gradient2(low="red", mid="white", high="green", midpoint=0, 
  space="rgb", guide="colourbar")
axis.theme <- theme(axis.text.y = element_text(size=10), 
  axis.text.x = element_text(size=10, angle=90))

# across all forums
cor.all <- cor(forums[,4:22])
ggplot(melt(cor.all), aes(X1, X2, fill=value)) + geom_tile() + 
  fill.grad + axis.theme + labs(y="", x="", title = "All Forums")  

# limit to SharePoint forums
cor.sp <- cor(forums.sp[,4:22])
ggplot(melt(cor.sp), aes(X1, X2, fill=value)) + geom_tile() + 
  fill.grad + axis.theme + labs(y="", x="", title = "SharePoint Forums")

# limit to SQL Server forums
cor.sql <- cor(forums.sql[,4:22])
ggplot(melt(cor.sql), aes(X1, X2, fill=value)) + geom_tile() + 
  fill.grad + axis.theme + labs(y="", x="", title = "SQL Forums")

rm(fill_grad, cor.all, cor.sql, cor.sp)
```

![plot of chunk forums.cor](figure/forums_cor1.png) ![plot of chunk forums.cor](figure/forums_cor2.png) ![plot of chunk forums.cor](figure/forums_cor3.png) 


That was a bad idea. Not very helpful, and most of the things that jump out are intuitively obvious. Perhaps some scatter plots (primarily with a success metric on the y-axis) and the data points color-coded by forum category will help.


```r
# scatter plot of percent threads answered vs. average number of answers per thread
ggplot(forums, aes(y=Percent_Threads_Answered, x=Avg_Answers)) +
  geom_point(aes(color=Forum_Category)) +
  scale_colour_excel()

# scatter plot of percent threads answered vs. average number of conributors per thread
ggplot(forums, aes(y=Percent_Threads_Answered, x=Avg_Thread_Contributors)) +
  geom_point(aes(color=Forum_Category)) +
  scale_colour_excel()

# scatter plot of percent threads answered vs. average number of posts per thread
ggplot(forums, aes(y=Percent_Threads_Answered, x=Avg_Num_Posts)) +
  geom_point(aes(color=Forum_Category)) +
  scale_colour_excel()

# scatter plot of mean time to first answer vs. mean time to first response
ggplot(forums, aes(y=Mean_Time_To_First_Answer, x=Mean_Time_To_First_Response)) +
  geom_point(aes(color=Forum_Category)) +
  scale_colour_excel() + 
  coord_cartesian(ylim=c(0,20), xlim=c(0,12)) # ignore a couple far outliers

# scatter plot of mean time to first answer vs. number of unique contributors
ggplot(forums, aes(y=Mean_Time_To_First_Answer, x=Num_Unique_Contributors)) +
  geom_point(aes(color=Forum_Category)) +
  scale_colour_excel() +
  coord_cartesian(ylim=c(0,20)) # ignore a couple far outliers

# scatter plot of average number of answers per thread vs. average number of thread contributors
ggplot(forums, aes(y=Avg_Answers, x=Avg_Thread_Contributors)) +
  geom_point(aes(color=Forum_Category)) +
  scale_colour_excel()

# scatter plot of mean time to first answer vs. percent thread with MSFT involvement
ggplot(forums, aes(y=Mean_Time_To_First_Answer, x=Percent_Threads_With_MSFT)) +
  geom_point(aes(color=Forum_Category)) +
  scale_colour_excel() +
  coord_cartesian(ylim=c(0,20), xlim=c(0,0.20)) # ignore a couple far outliers

# scatter plot of mean time to first answer vs. percent thread with MVP involvement
ggplot(forums, aes(y=Mean_Time_To_First_Answer, x=Percent_Threads_With_MVP)) +
  geom_point(aes(color=Forum_Category)) +
  scale_colour_excel() +
  coord_cartesian(ylim=c(0,20), xlim=c(0,0.80)) # ignore a couple far outliers

# scatter plot of average number of votes per thread vs. percent thread with MSFT involvement
ggplot(forums, aes(y=Avg_Num_Votes, x=Percent_Threads_With_MSFT)) +
  geom_point(aes(color=Forum_Category)) +
  scale_colour_excel() +
  coord_cartesian(ylim=c(0,0.75), xlim=c(0,0.30)) # ignore a couple far outliers

# scatter plot of average number of votes per thread vs. average number of views per thread
ggplot(forums, aes(y=Avg_Num_Votes, x=Avg_Num_Views)) +
  geom_point(aes(color=Forum_Category)) +
  scale_colour_excel() +
  coord_cartesian(ylim=c(0,0.75), xlim=c(500,1500)) # ignore a couple far outliers

# scatter plot of number of threads vs. mean time to first answer
ggplot(forums, aes(y=Mean_Time_To_First_Answer, x=Num_Threads)) +
  geom_point(aes(color=Forum_Category)) +
  scale_colour_excel() +
  coord_cartesian(ylim=c(0,20)) # ignore a couple far outliers

# scatter plot of number of threads vs. mean time to first answer
ggplot(forums, aes(y=Mean_Time_To_First_Response, x=Num_Threads)) +
  geom_point(aes(color=Forum_Category)) +
  scale_colour_excel() +
  coord_cartesian(ylim=c(0,15)) # ignore a couple far outliers

# scatter plot of number of threads vs. mean time to first answer
ggplot(forums, aes(y=Mean_Time_To_First_Response, x=Avg_Question_Length)) +
  geom_point(aes(color=Forum_Category)) +
  scale_colour_excel() +
  coord_cartesian(ylim=c(0,15)) # ignore a couple far outliers

# scatter plot of number of threads vs. mean time to first answer
ggplot(forums, aes(y=Avg_Answers, x=Num_Threads)) +
  geom_point(aes(color=Forum_Category)) +
  scale_colour_excel()

rm(forums, forums.sp, forums.sql)
```

![plot of chunk forums.scatter](figure/forums_scatter1.png) ![plot of chunk forums.scatter](figure/forums_scatter2.png) ![plot of chunk forums.scatter](figure/forums_scatter3.png) ![plot of chunk forums.scatter](figure/forums_scatter4.png) ![plot of chunk forums.scatter](figure/forums_scatter5.png) ![plot of chunk forums.scatter](figure/forums_scatter6.png) ![plot of chunk forums.scatter](figure/forums_scatter7.png) ![plot of chunk forums.scatter](figure/forums_scatter8.png) ![plot of chunk forums.scatter](figure/forums_scatter9.png) ![plot of chunk forums.scatter](figure/forums_scatter10.png) ![plot of chunk forums.scatter](figure/forums_scatter11.png) ![plot of chunk forums.scatter](figure/forums_scatter12.png) ![plot of chunk forums.scatter](figure/forums_scatter13.png) ![plot of chunk forums.scatter](figure/forums_scatter14.png) 


My observations from looking at the above scatter plots follow. These do not reflect causation, only apparent patterns of correlation:

* Approximately 2.5 contributors per thread seems to be an activity-level turning point, below which 75% or less of the questions posted will be answered, and above which 75% or more of the questions posted will be answered.
* When it comes to answerings a higher percentage of questions posted, SQL tend to do better than SharePoint forums.
* More posts per thread generally translates into more threads being answered. No surprise here.
* Average first response times for the majority of SQL Server forums is are below 1.5 days. On the flip side, the majority of SharePoint forums have an average initial response time of over 3 days.
* Even when we compare SharePoint and SQL forums of relatively the same size (in terms of the number of unique contributors during 2013), SharePoint forums are on average slower in providing an answer than are SQL forums. Maybe product complexity is a factor here?
* SQL Server forums benefit from a higher rate of Microsoft involvement than does ShaerPoint.
* Forums with MVPs contributing to over 40% of the threads have relatively quick average times to first answer.
* Based on average thread views, SQL forums tend to get more traffic than SharePoint forums.
* Based on number of threads created, seven of the top-ten largest forums are SharePoint forums.

Looking at Threads
---------------------------
Now that we got a high-level look at the forum level, I want to drill down a little deeper and look at thread-level data. 

I'll start by loading the data from my database.


```r
# query the database and put results in a dataframe
threads <- sqlQuery(myDB, "SELECT * FROM Forums.dbo.Thread_Summary",
  stringsAsFactors=FALSE) 
# we can close the odbc connection now
odbcClose(myDB) 
rm(myDB)

# make sure data is loaded as expected
# we should have 72,324 threads
nrow(threads)
```

```
## [1] 72324
```

```r
# let's see the column names
colnames(threads)
```

```
##  [1] "Thread_ID"                "Title"                    "Question"                
##  [4] "Answered"                 "Num_Contributors"         "Asker_Type"              
##  [7] "Created_On"               "Answered_On"              "Answer_Has_Code"         
## [10] "Question_Has_Code"        "Forum_ID"                 "Forum_Name"              
## [13] "Forum_Category"           "Num_Answers"              "Time_To_First_Answer"    
## [16] "Num_Votes"                "Num_Votes_Per_View"       "Title_Length"            
## [19] "Question_Length"          "Num_Subscribers"          "Num_Views"               
## [22] "Time_To_First_Reply"      "Num_Posts"                "Num_Code_Posts"          
## [25] "Percent_Code_Posts"       "Num_MSFT_Contributors"    "Num_MSFT_Posts"          
## [28] "Num_MSFT_Answers"         "Num_MSFT_Code_Posts"      "Num_MSFT_Votes"          
## [31] "Num_MVP_Contributors"     "Num_MVP_Posts"            "Num_MVP_Answers"         
## [34] "Num_MVP_Code_Posts"       "Num_MVP_Votes"            "Num_Partner_Contributors"
## [37] "Num_Partner_Posts"        "Num_Partner_Answers"      "Num_Partner_Code_Posts"  
## [40] "Num_Partner_Votes"        "Avg_Contributor_Points"   "Avg_Contributor_Stars"   
## [43] "Created_Month"            "Created_Week_Day"         "Created_Hour"            
## [46] "Asker_Stars"              "Asker_Points"
```


The first 13 columns are identifiers and data types that will not work well doing math (i.e. string, dates, and booleans). Columns 14-17 are our success metrics. The remaining columns are attributes which might give us some interesting insight into what drives the success metrics.

I will append a few columns to *threads* with engineered features that will make my life a little easier later on.


```r
# group title lengths into groups, with one group per 10 characters of length
threads$Title_Length_Group <- floor(threads$Title_Length/10) * 10 + 5

# group question lengths into groups, with one group per 40 characters of length
threads$Question_Length_Group <- floor(threads$Question_Length/40) * 40 + 20

# round time to first reply to the nearest day
threads$TTFR_Group <- floor(threads$Time_To_First_Reply + 0.5)
```


### Success Factor Distributions

Let's see how the success metrics are distributed at the thread level.


```r
# create ggplot2 object
ggt <- ggplot(data = threads) + labs(title = "SQL & SharePoint Threads")

# Num_Answers histogram
ggt + geom_bar(aes(x = as.factor(Num_Answers)), binwidth=1) + coord_cartesian(xlim=c(0,8))

# Time_To_First_Answer histogram
ggt + geom_density(aes(x = Time_To_First_Answer), na.rm = TRUE) + coord_cartesian(xlim=c(0,30))

# Num_Votes histogram
ggt + geom_bar(aes(x = as.factor(Num_Votes)), binwidth=1) + coord_cartesian(xlim=c(0,10))

# Num_Votes_Per_View histogram
ggt + geom_density(aes(x = Num_Votes_Per_View), na.rm = TRUE) + coord_cartesian(xlim=c(0,0.005))
```

![plot of chunk threads.hist.success](figure/threads_hist_success1.png) ![plot of chunk threads.hist.success](figure/threads_hist_success2.png) ![plot of chunk threads.hist.success](figure/threads_hist_success3.png) ![plot of chunk threads.hist.success](figure/threads_hist_success4.png) 


That's an interesting double-peak in Time_To_First_Answer. Is that because we're mixing SQL and SharePoint? Let's take a look both forum categories side-by-side.


```r
# create ggplot2 objects
ggt.sql <- ggplot(data = subset(threads, Forum_Category == "SQL Server")) + labs(title = "SQL Forums")
ggt.sp <- ggplot(data = subset(threads, Forum_Category == "SharePoint")) + labs(title = "SharePoint Forums")

# Num_Answers histograms
ggt.sql + geom_bar(aes(x = as.factor(Num_Answers)), binwidth=1) + coord_cartesian(xlim=c(0,8))
ggt.sp + geom_bar(aes(x = as.factor(Num_Answers)), binwidth=1) + coord_cartesian(xlim=c(0,8))

# Time_To_First_Answer histogram
ggt.sql + geom_density(aes(x = Time_To_First_Answer), na.rm = TRUE) + coord_cartesian(xlim=c(0,30))
ggt.sp + geom_density(aes(x = Time_To_First_Answer), na.rm = TRUE) + coord_cartesian(xlim=c(0,30))

# Num_Votes histogram
ggt.sql + geom_bar(aes(x = as.factor(Num_Votes)), binwidth=1) + coord_cartesian(xlim=c(0,10))
ggt.sp + geom_bar(aes(x = as.factor(Num_Votes)), binwidth=1) + coord_cartesian(xlim=c(0,10))

# Num_Votes_Per_View histogram
ggt.sql + geom_density(aes(x = Num_Votes_Per_View), na.rm = TRUE) + coord_cartesian(xlim=c(0,0.005))
ggt.sp + geom_density(aes(x = Num_Votes_Per_View), na.rm = TRUE) + coord_cartesian(xlim=c(0,0.005))
```

![plot of chunk threads.hist.success.sql.sp](figure/threads_hist_success_sql_sp1.png) ![plot of chunk threads.hist.success.sql.sp](figure/threads_hist_success_sql_sp2.png) ![plot of chunk threads.hist.success.sql.sp](figure/threads_hist_success_sql_sp3.png) ![plot of chunk threads.hist.success.sql.sp](figure/threads_hist_success_sql_sp4.png) ![plot of chunk threads.hist.success.sql.sp](figure/threads_hist_success_sql_sp5.png) ![plot of chunk threads.hist.success.sql.sp](figure/threads_hist_success_sql_sp6.png) ![plot of chunk threads.hist.success.sql.sp](figure/threads_hist_success_sql_sp7.png) ![plot of chunk threads.hist.success.sql.sp](figure/threads_hist_success_sql_sp8.png) 


That doesn't answer the double-peak question, but I do have a couple quick observations:
* Noticably more questions go unanswered in SharePoint forums as compared to SQL forums.
* Both forums seems to have the highest Time_To_First_Answer frequency at about 7 days and the second highest frequency at about 1 day.

If the double-peak isn't caused by the different types of forums, could it be influenced by where the weekend falls? Let's look at the days of the week individually and see if it becomes any clearer.


```r
for (day in 1:7)
{
  print(ggplot(data = subset(threads, Created_Week_Day == day)) + labs(title = paste("Day ", as.character(day))) + 
  geom_density(aes(x = Time_To_First_Answer), na.rm = TRUE) + coord_cartesian(xlim=c(0,6)))
}
```

![plot of chunk threads.ttfa.day](figure/threads_ttfa_day1.png) ![plot of chunk threads.ttfa.day](figure/threads_ttfa_day2.png) ![plot of chunk threads.ttfa.day](figure/threads_ttfa_day3.png) ![plot of chunk threads.ttfa.day](figure/threads_ttfa_day4.png) ![plot of chunk threads.ttfa.day](figure/threads_ttfa_day5.png) ![plot of chunk threads.ttfa.day](figure/threads_ttfa_day6.png) ![plot of chunk threads.ttfa.day](figure/threads_ttfa_day7.png) 


Ah, yes. That's it. The days with the highest volume (Monday through Thursday) all have a significant trough when the weekend comes around (somewhere between 2 and 5 days), leading to a trough in the overall graph in that 2-5 day range.

### Other Distributions

Out of curiousity, I'd also like to see the distribution of the question/title length attributes and the time of the post attributes. These are things that are known immediately when a thread is posted, so they could be good inputs for a prediction model.


```r
# Title_Length density plot
ggt + geom_density(aes(x = Title_Length)) + coord_cartesian(xlim=c(0,250))

# Question_Length density plot
ggt + geom_density(aes(x = Question_Length)) + coord_cartesian(xlim=c(0,5000))

# Created_Week_Day bar chart
ggt + geom_bar(aes(x = as.factor(Created_Week_Day)), binwidth=1)

# Created_Month bar chart 
ggt + geom_bar(aes(x = as.factor(Created_Month)), binwidth=1)

# Created_Hour bar chart
ggt + geom_bar(aes(x = as.factor(Created_Hour)), binwidth=1)
```

![plot of chunk threads.hist.other](figure/threads_hist_other1.png) ![plot of chunk threads.hist.other](figure/threads_hist_other2.png) ![plot of chunk threads.hist.other](figure/threads_hist_other3.png) ![plot of chunk threads.hist.other](figure/threads_hist_other4.png) ![plot of chunk threads.hist.other](figure/threads_hist_other5.png) 


And, let's see the distributions of threads based on the number of posts made by Microsft, MVPs, and partners.


```r
# MSFT histogram
ggt + geom_bar(aes(x = as.factor(Num_MSFT_Posts)), binwidth=1)

# MSFT histogram without zero
ggt + geom_bar(aes(x = as.factor(Num_MSFT_Posts)), binwidth=1) + coord_cartesian(xlim=c(1.5,10), ylim=c(0,3000))

# MVP histogram
ggt + geom_bar(aes(x = as.factor(Num_MVP_Posts)), binwidth=1) + coord_cartesian(xlim=c(0,11.5))

# MVP histogram without zero
ggt + geom_bar(aes(x = as.factor(Num_MVP_Posts)), binwidth=1) + coord_cartesian(xlim=c(1.5,11.5), ylim=c(0,15000))

# Partner histogram
ggt + geom_bar(aes(x = as.factor(Num_Partner_Posts)), binwidth=1) + coord_cartesian(xlim=c(0,11.5))

# Partner histogram without zero
ggt + geom_bar(aes(x = as.factor(Num_Partner_Posts)), binwidth=1) + coord_cartesian(xlim=c(1.5,11.5), ylim=c(0,25000))
```

![plot of chunk threads.hist.part](figure/threads_hist_part1.png) ![plot of chunk threads.hist.part](figure/threads_hist_part2.png) ![plot of chunk threads.hist.part](figure/threads_hist_part3.png) ![plot of chunk threads.hist.part](figure/threads_hist_part4.png) ![plot of chunk threads.hist.part](figure/threads_hist_part5.png) ![plot of chunk threads.hist.part](figure/threads_hist_part6.png) 


Almost there... Here are the distributions of a few remaining, potentially interesting attributes.


```r
# asker points
ggt + geom_density(aes(x = Asker_Points)) + coord_cartesian(xlim=c(0,2000))

# subscribers
ggt + geom_bar(aes(x = as.factor(Num_Subscribers)), binwidth=1) + coord_cartesian(xlim=c(0,8.5))

# views
ggt + geom_density(aes(x = Num_Views)) + coord_cartesian(xlim=c(0,4000))

# TTFR
ggt + geom_density(aes(x = Time_To_First_Reply), na.rm = TRUE) + coord_cartesian(xlim=c(0,10))
```

![plot of chunk threads.hist.other2](figure/threads_hist_other21.png) ![plot of chunk threads.hist.other2](figure/threads_hist_other22.png) ![plot of chunk threads.hist.other2](figure/threads_hist_other23.png) ![plot of chunk threads.hist.other2](figure/threads_hist_other24.png) 


### Microsoft Involvement

If I worked at Microsoft, I'd want to know how when employees are getting involved in threads and what impact it is having. So, I'm going to plot some distributions for those threads that Microsoft got involved in vs. those threads that Microsoft did not get involved in to see if there are any distinct differences.


```r

# create ggplot2 object for only MSFT-involved threads
ggt.msft <- ggplot(data = subset(threads, Num_MSFT_Posts > 0)) + labs(title = "Threads with MSFT Engagement")
ggt.not.msft <- ggplot(data = subset(threads, Num_MSFT_Posts == 0)) + labs(title = "Threads without MSFT Engagement")

# Num_Answers histogram
ggt.msft + geom_bar(aes(x = as.factor(Num_Answers)), binwidth=1) + coord_cartesian(xlim=c(0,8))
ggt.not.msft + geom_bar(aes(x = as.factor(Num_Answers)), binwidth=1) + coord_cartesian(xlim=c(0,8))

# Time_To_First_Answer histogram
ggt.msft + geom_density(aes(x = Time_To_First_Answer), na.rm = TRUE) + coord_cartesian(xlim=c(0,30))
ggt.not.msft + geom_density(aes(x = Time_To_First_Answer), na.rm = TRUE) + coord_cartesian(xlim=c(0,30))

# Num_Votes histogram
ggt.msft + geom_bar(aes(x = as.factor(Num_Votes)), binwidth=1) + coord_cartesian(xlim=c(0,10))
ggt.not.msft + geom_bar(aes(x = as.factor(Num_Votes)), binwidth=1) + coord_cartesian(xlim=c(0,10))

# Title_Length density plot
ggt.msft + geom_density(aes(x = Title_Length)) + coord_cartesian(xlim=c(0,250))
ggt.not.msft + geom_density(aes(x = Title_Length)) + coord_cartesian(xlim=c(0,250))

# Question_Length density plot
ggt.msft + geom_density(aes(x = Question_Length)) + coord_cartesian(xlim=c(0,5000))
ggt.not.msft + geom_density(aes(x = Question_Length)) + coord_cartesian(xlim=c(0,5000))

# Created_Week_Day bar chart
ggt.msft + geom_bar(aes(x = as.factor(Created_Week_Day)), binwidth=1)
ggt.not.msft + geom_bar(aes(x = as.factor(Created_Week_Day)), binwidth=1)

# Created_Month bar chart 
ggt.msft + geom_bar(aes(x = as.factor(Created_Month)), binwidth=1)
ggt.not.msft + geom_bar(aes(x = as.factor(Created_Month)), binwidth=1)

# Created_Hour bar chart
ggt.msft + geom_bar(aes(x = as.factor(Created_Hour)), binwidth=1)
ggt.not.msft + geom_bar(aes(x = as.factor(Created_Hour)), binwidth=1)

# Num_Votes_Per_View histogram
ggt.msft + geom_density(aes(x = Num_Votes_Per_View), na.rm = TRUE) + coord_cartesian(xlim=c(0,0.005))
ggt.not.msft + geom_density(aes(x = Num_Votes_Per_View), na.rm = TRUE) + coord_cartesian(xlim=c(0,0.005))

# asker points
ggt.msft + geom_density(aes(x = Asker_Points)) + coord_cartesian(xlim=c(0,2000))
ggt.not.msft + geom_density(aes(x = Asker_Points)) + coord_cartesian(xlim=c(0,2000))

# subscribers
ggt.msft + geom_bar(aes(x = as.factor(Num_Subscribers)), binwidth=1) + coord_cartesian(xlim=c(0,8.5))
ggt.not.msft + geom_bar(aes(x = as.factor(Num_Subscribers)), binwidth=1) + coord_cartesian(xlim=c(0,8.5))

# views
ggt.msft + geom_density(aes(x = Num_Views)) + coord_cartesian(xlim=c(0,4000))
ggt.not.msft + geom_density(aes(x = Num_Views)) + coord_cartesian(xlim=c(0,4000))

# TTFR
ggt.msft + geom_density(aes(x = Time_To_First_Reply), na.rm = TRUE) + coord_cartesian(xlim=c(0,10))
ggt.not.msft + geom_density(aes(x = Time_To_First_Reply), na.rm = TRUE) + coord_cartesian(xlim=c(0,10))

rm(ggt.msft, ggt.not.msft)
```

![plot of chunk threads.msft](figure/threads_msft1.png) ![plot of chunk threads.msft](figure/threads_msft2.png) ![plot of chunk threads.msft](figure/threads_msft3.png) ![plot of chunk threads.msft](figure/threads_msft4.png) ![plot of chunk threads.msft](figure/threads_msft5.png) ![plot of chunk threads.msft](figure/threads_msft6.png) ![plot of chunk threads.msft](figure/threads_msft7.png) ![plot of chunk threads.msft](figure/threads_msft8.png) ![plot of chunk threads.msft](figure/threads_msft9.png) ![plot of chunk threads.msft](figure/threads_msft10.png) ![plot of chunk threads.msft](figure/threads_msft11.png) ![plot of chunk threads.msft](figure/threads_msft12.png) ![plot of chunk threads.msft](figure/threads_msft13.png) ![plot of chunk threads.msft](figure/threads_msft14.png) ![plot of chunk threads.msft](figure/threads_msft15.png) ![plot of chunk threads.msft](figure/threads_msft16.png) ![plot of chunk threads.msft](figure/threads_msft17.png) ![plot of chunk threads.msft](figure/threads_msft18.png) ![plot of chunk threads.msft](figure/threads_msft19.png) ![plot of chunk threads.msft](figure/threads_msft20.png) ![plot of chunk threads.msft](figure/threads_msft21.png) ![plot of chunk threads.msft](figure/threads_msft22.png) ![plot of chunk threads.msft](figure/threads_msft23.png) ![plot of chunk threads.msft](figure/threads_msft24.png) ![plot of chunk threads.msft](figure/threads_msft25.png) ![plot of chunk threads.msft](figure/threads_msft26.png) 


The most obvious differences between Microsoft-involved threads and the rest of the population:

* Microsoft involvement is skewed toward threads started by users with very few reputation points.
* Threads where Microsoft is involved tend to have more views and more subscribers than other threads.
* Microsoft is involved in a disproportionately few threads that are answered in the first one or two days.

### Correlations


```r
# across all threads
cor.all <- cor(threads[,14:47], use="pairwise.complete.obs")
ggplot(melt(cor.all), aes(X1, X2, fill=value)) + geom_tile() + 
  fill.grad + axis.theme + labs(y="", x="", title = "All Threads")  

rm(cor.all, axis.theme)
```

![plot of chunk threads.corr](figure/threads_corr.png) 


This is useless. On to something else...

### Responsiveness

Is there some relationship between the length of the title/question and time to first reply/first answer?


```r
# scatter plot of TTFR vs. the title's length

ggt + aes(y=Time_To_First_Reply, x=Title_Length_Group) +
  coord_cartesian(xlim=c(0,125), ylim=c(0,4)) +
  stat_summary(fun.y = 'mean', fun.ymin = mean, fun.ymax = mean)

# scatter plot of TTFA vs. the title's length
ggt + aes(y=Time_To_First_Answer, x=Title_Length_Group) +
  coord_cartesian(xlim=c(0,125), ylim=c(0,15)) +
  stat_summary(fun.y = 'mean', fun.ymin = mean, fun.ymax = mean)

# scatter plot of TTFR vs. the question's length
ggt + aes(y=Time_To_First_Reply, x=Question_Length_Group) +
  coord_cartesian(xlim=c(0,2000), ylim=c(0,4)) +
  stat_summary(fun.y = 'mean', fun.ymin = mean, fun.ymax = mean)

# scatter plot of TTFA vs. the question's length
ggt + aes(y=Time_To_First_Answer, x=Question_Length_Group) +
  coord_cartesian(xlim=c(0,2000), ylim=c(0,15)) +
  stat_summary(fun.y = 'mean', fun.ymin = mean, fun.ymax = mean)
```

![plot of chunk thread.length](figure/thread_length1.png) ![plot of chunk thread.length](figure/thread_length2.png) ![plot of chunk thread.length](figure/thread_length3.png) ![plot of chunk thread.length](figure/thread_length4.png) 


It appears that shorter titles and short questions lead to faster first replies and first answers. This could be that shorter questions are easier/simpler questions. Or, perhaps longer questions could discourage people from reading them.

Does the time the post was made affect the speed at which it is replied to and answered?


```r

# scatter plot of TTFR vs. the hour
ggt + aes(y=Time_To_First_Reply, x=as.factor(Created_Hour)) +
  coord_cartesian(xlim=c(0,25), ylim=c(0,3)) +
  stat_summary(fun.y = 'mean', fun.ymin = mean, fun.ymax = mean)

# scatter plot of TTFA vs. the hour
ggt + aes(y=Time_To_First_Answer, x=as.factor(Created_Hour)) +
  coord_cartesian(xlim=c(0,25), ylim=c(0,15)) +
  stat_summary(fun.y = 'mean', fun.ymin = mean, fun.ymax = mean)

# scatter plot of TTFR vs. the day
ggt + aes(y=Time_To_First_Reply, x=as.factor(Created_Week_Day)) +
  coord_cartesian(xlim=c(0,8), ylim=c(0,3)) +
  stat_summary(fun.y = 'mean', fun.ymin = mean, fun.ymax = mean)

# scatter plot of TTFA vs. the day
ggt + aes(y=Time_To_First_Answer, x=as.factor(Created_Week_Day)) +
  coord_cartesian(xlim=c(0,8), ylim=c(0,15)) +
  stat_summary(fun.y = 'mean', fun.ymin = mean, fun.ymax = mean)

# scatter plot of TTFR vs. the month
ggt + aes(y=Time_To_First_Reply, x=as.factor(Created_Month)) +
  coord_cartesian(xlim=c(0,13), ylim=c(0,3)) +
  stat_summary(fun.y = 'mean', fun.ymin = mean, fun.ymax = mean)

# scatter plot of TTFA vs. the month
ggt + aes(y=Time_To_First_Answer, x=as.factor(Created_Month)) +
  coord_cartesian(xlim=c(0,13), ylim=c(0,15)) +
  stat_summary(fun.y = 'mean', fun.ymin = mean, fun.ymax = mean)
```

![plot of chunk thead.created](figure/thead_created1.png) ![plot of chunk thead.created](figure/thead_created2.png) ![plot of chunk thead.created](figure/thead_created3.png) ![plot of chunk thead.created](figure/thead_created4.png) ![plot of chunk thead.created](figure/thead_created5.png) ![plot of chunk thead.created](figure/thead_created6.png) 


While a question posted on a weekend will get a faster initial reply, there isn't any evidence of the question actually being resolved any faster than any other day of the week.

Posting a question later in the year did, however, seem to yield both faster initial responses and answers. We saw earlier that the total number of questions asked decreased as the year progressed, so perhaps this trend shows that fewer questions posted allow the questions that are posted to gain more attention and be resolved more quickly. This hypothesis would also make sense with the observation that the weekends (with the lowest number of new issues) give the fastest initial responses.

Is it possible that other factors played a role in the responsiveness improvement over the course of the year? For example, SharePoint 2013 went GA on 2/28/13. Maybe procedural changes lead to heaver involvment from experts as the year progressed. Let's take a look...



```r

# MSFTs

msft.ply <- ddply(threads, "Created_Month", summarise, Total_MSFT_Posts = sum(Num_MSFT_Posts), 
  Total_Posts = sum(Num_Posts))

gg.msft <- ggplot(msft.ply, aes(x = factor(Created_Month))) + 
  labs(title="SQL & SharePoint Threads", x="Thread Created Month") + 
  geom_bar(stat = "identity")

gg.msft + aes(y = Total_MSFT_Posts) + labs(y="Number of MSFT Posts") 
gg.msft + aes(y = Total_MSFT_Posts/Total_Posts) + labs(y="MSFT Posts as Percent of Total Posts")

# MVPs

mvp.ply <- ddply(threads, "Created_Month", summarise, Total_MVP_Posts = sum(Num_MVP_Posts), 
  Total_Posts = sum(Num_Posts))

gg.mvp <- ggplot(mvp.ply, aes(x = factor(Created_Month))) + 
  labs(title="SQL & SharePoint Threads", x="Thread Created Month") + 
  geom_bar(stat = "identity")

gg.mvp + aes(y = Total_MVP_Posts) + labs(y="Number of MVP Posts")
gg.mvp + aes(y = Total_MVP_Posts/Total_Posts) + labs(y="MVP Posts as Percent of Total Posts")

# Partners

part.ply <- ddply(threads, "Created_Month", summarise, Total_Partner_Posts = sum(Num_Partner_Posts), 
  Total_Posts = sum(Num_Posts))

gg.part <- ggplot(part.ply, aes(x = factor(Created_Month))) + 
  labs(title="SQL & SharePoint Threads", x="Thread Created Month") + 
  geom_bar(stat = "identity")

gg.part + aes(y = Total_Partner_Posts) + labs(y="Number of Partner Posts")
gg.part + aes(y = Total_Partner_Posts/Total_Posts) + labs(y="Partner Posts as Percent of Total Posts")

rm(ggt, msft.ply, gg.msft, mvp.ply, gg.mvp, part.ply, gg.part)
```

![plot of chunk thead.msft](figure/thead_msft1.png) ![plot of chunk thead.msft](figure/thead_msft2.png) ![plot of chunk thead.msft](figure/thead_msft3.png) ![plot of chunk thead.msft](figure/thead_msft4.png) ![plot of chunk thead.msft](figure/thead_msft5.png) ![plot of chunk thead.msft](figure/thead_msft6.png) 


It looks like MSFT employees took a break (just like everyone else) at the end of the year. There was an uptick in the relative level of MVP and partner activity, but I'm doubtful this made any significant difference. However, I did find it surprising to see the level of partner activity is greater than 25%. 

To look at the posibility of seasonality, we could scrape another year of data from the website, but I'll leave that for a follow up analysis...

### Success Rate

The ultimate question of a thread's success is really whether or not it ever got answered. Of course we'd like to see it happen as fast as possible, but the more important thing is to see whether it was resolved at all. Let's look at the "success rate" (the ratio of threads that received an answer to the total number of threads created) in a few different slices.


```r
# By month
succ.ply <- ddply(threads, "Created_Month", summarise, Total_Questions = length(Num_Answers), Successes = sum(Answered))
ggplot(succ.ply, aes(x = factor(Created_Month), y = Successes/Total_Questions)) + 
  labs(title="SQL & SharePoint Threads", x="Thread Created Month", y="Success Rate") + geom_point()

# By week day
succ.ply <- ddply(threads, "Created_Week_Day", summarise, Total_Questions = length(Num_Answers), Successes = sum(Answered))
ggplot(succ.ply, aes(x = factor(Created_Week_Day), y = Successes/Total_Questions)) + 
  labs(title="SQL & SharePoint Threads", x="Thread Created Week Day", y="Success Rate") + geom_point()

# By time of day
succ.ply <- ddply(threads, "Created_Hour", summarise, Total_Questions = length(Num_Answers), Successes = sum(Answered))
ggplot(succ.ply, aes(x = factor(Created_Hour), y = Successes/Total_Questions)) + 
  labs(title="SQL & SharePoint Threads", x="Thread Created Hour", y="Success Rate") + geom_point()

# By title length
succ.ply <- ddply(threads, "Title_Length_Group", summarise, Total_Questions = length(Num_Answers), Successes = sum(Answered))
ggplot(succ.ply, aes(x = Title_Length_Group, y = Successes/Total_Questions)) + 
  labs(title="SQL & SharePoint Threads", y="Success Rate") + geom_point() + coord_cartesian(xlim=c(0,130), ylim=c(0.5, 1))

# By question length
succ.ply <- ddply(threads, "Question_Length_Group", summarise, Total_Questions = length(Num_Answers), Successes = sum(Answered))
ggplot(succ.ply, aes(x = Question_Length_Group, y = Successes/Total_Questions)) + 
  labs(title="SQL & SharePoint Threads", y="Success Rate") + geom_point() + coord_cartesian(xlim=c(0,2100), ylim=c(0.5, 1))

# By TTFR
succ.ply <- ddply(threads, "TTFR_Group", summarise, Total_Questions = length(Num_Answers), Successes = sum(Answered))
ggplot(succ.ply, aes(x = TTFR_Group, y = Successes/Total_Questions)) + 
  labs(title="SQL & SharePoint Threads", y="Success Rate") + geom_point() + coord_cartesian(xlim=c(-0.5,20.5), ylim=c(0, 1))

# By MSFT posts
succ.ply <- ddply(threads, "Num_MSFT_Posts", summarise, Total_Questions = length(Num_Answers), Successes = sum(Answered))
ggplot(succ.ply, aes(x = factor(Num_MSFT_Posts), y = Successes/Total_Questions)) + 
  labs(title="SQL & SharePoint Threads", y="Success Rate") + geom_point() + coord_cartesian(xlim=c(0.5,5.5), ylim=c(0, 1))

rm(succ.ply)
```

![plot of chunk thread.length.succ](figure/thread_length_succ1.png) ![plot of chunk thread.length.succ](figure/thread_length_succ2.png) ![plot of chunk thread.length.succ](figure/thread_length_succ3.png) ![plot of chunk thread.length.succ](figure/thread_length_succ4.png) ![plot of chunk thread.length.succ](figure/thread_length_succ5.png) ![plot of chunk thread.length.succ](figure/thread_length_succ6.png) ![plot of chunk thread.length.succ](figure/thread_length_succ7.png) 


These graphs reveal much the same as our earlier graphs. More success is seen for questions posted later in the year and on weekends. Shorter title and questions get better results than longer ones. Here is one last insightful morsel, though: If an issue gets an initial reply during the first five days, it is about 75% likely to eventually get resolved successfully. But, as each day after the 5-day mark passes, the question gets less and less likely to receive a successful answer. By day 10, the likelihood of a successful resolution is only about 50%. 

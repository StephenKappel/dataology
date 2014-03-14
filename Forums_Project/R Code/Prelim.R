library(RODBC)
library(ggplot2)

#create connection to database
myDB = odbcConnect("LocalSQL")

#query the database and put results in a dataframe
forums = sqlQuery(myDB, "SELECT * FROM Forums.dbo.Forum_Summary", stringsAsFactors=FALSE)

leng#make sure data is loaded as expected
head(forums)

#plot MTTR vs. num contributors
plot(forums$Num_Unique_Contributors, forums$Mean_Time_To_Answer, main="MTTR vs. Unique Contributors", xlab="Unique Contributors in 2013", ylab="Mean Time to Resolution (days)")
#plot MTTR vs. num contributors for forums with more than 100 threads
with(forums[forums$Num_Threads >= 100,], plot(Num_Unique_Contributors, Mean_Time_To_Answer, main="MTTR vs. Unique Contributors for Forums with >= 100 Threads", xlab="Unique Contributors in 2013", ylab="Mean Time to Resolution (days)"))
reg = with(forums[forums$Num_Threads >= 100,],lm(Mean_Time_To_Answer~Num_Unique_Contributors))
abline(reg)


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
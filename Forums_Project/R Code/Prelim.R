library(RODBC)

#create connection to database
myDB = odbcConnect("DataHogDB")

#query the database and put results in a dataframe
threads = sqlQuery(myDB, "SELECT * FROM Thread_Basics WHERE Display_Name = 'SQL Server Express'", stringsAsFactors=FALSE)

#make sure data is loaded as expected
head(threads)

#get summary data about creation dates
summary(threads$Created_On)
summary(as.POSIXlt(threads$Created_On)$mon)

#create a histogram to see # of threads created each day of the week
#observation: as expected, lowest volume on weekends, highest volume on Wednedsay
wbins=seq(0,7,by=1)
hist(as.POSIXlt(threads$Created_On)$wday + 1, main = "Threads by Week Day", xlab = "Day of Week", breaks=wbins, labels = TRUE)

##create a histogram to see # of threads created each month of year
#observation: sudden drop off in volume in 3rd quarter
mbins=seq(0,12,by=1)
hist(as.POSIXlt(threads$Created_On)$mon + 1, main = "Threads by Month", xlab = "Month", breaks=mbins, labels = TRUE)

##plot a scatter of views vs. day of week posted
#observation: nothing particularly interesting; there are a few posts that really stand out from the pack
plot(jitter(as.POSIXlt(threads$Created_On)$wday + 1),  threads$Views, xlab = "Day of Week", ylab = "Views",main = "Views by Creation Day", log="y")


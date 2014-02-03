require(XML)

dataUrl = "http://www.peakbagger.com/pbgeog/histmetropop.aspx"
html = htmlTreeParse(dataUrl, useInternalNodes = T)
myTables = getNodeSet(html, "//table[@bordercolor]")[7:29]

year = c()
city = c()
rank = c()
pop = c()

for (myTab in myTables)
{
  currYear = xmlValue(xmlChildren(xmlChildren(xmlChildren(myTab)[[1]])[[1]])[[1]])
  rowNum = 1
  for (myRow in xmlChildren(myTab))
  {
    if(rowNum > 2)
    {
      myCols = xmlChildren(myRow)
    
      year = c(year, currYear)
      rankText = xmlValue(myCols[[1]])
      rank = c(rank, substr(rankText, 1, nchar(rankText)-1))
      city = c(city, xmlValue(myCols[[3]]))
      pop = c(pop, xmlValue(myCols[[5]]))
    }
    rowNum = rowNum + 1
  }
}

write.csv(data.frame(year, rank, city, pop), file="citypop.csv", row.names=FALSE)

rm(dataUrl, html,myTables, myTab,myRow, rankText, year, rank, city, pop, currYear, myCols, rowNum, df)
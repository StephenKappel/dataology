# MSDN Forums Data Exploration Project #

This is my final project for *Exploratory Data Analysis and Visualization* -- a course at Columbia University during he sprint semester of 2014.

My goal during this project was to better understand the factors that make technical support forums successful (or not successful) by collecting and analyzing data from Microsoft's Developer Network's forums.

Hopefully, you will find my work in this repository to be a good first foray into this area. And, ideas and contributions are, of course, welcome.

## The Structure of This Repo ##

Here's a brief outline of the files/folders in this project:

* **ForumScraper** - This folder contains my PyCharm project with the Python code I used to scrape my data from MSDN.
* **ForumExplorer** - This folder contains a d3/crossfilter visualization of the data. For the time being, this must be downloaded and hosted locally to see it in action. I highly recommend checking this out before diving into any of my R code.
* **TextAnalysis** - This folder contains my final project submission for my Machine Learning course, in which I played around with text analysis, making use of the text from the MSDN forums.
* **ForumsDb.zip** - This zip contains the SQL required to completely replicate my SQL Server Express database (including schema and data) on your machine.
* **DatabaseDiagram.PNG** - A quick screenshot of my database's structure (in case you don't want to recreate it yourself).
* **ExplorationAndCommentary.md** - A very comprehensive brain dump of my exploration of the data in R, along with some notes about how I scraped the data.
* **ExplorationAndCommentary.rmd** - Exactly what you'd expect... ExplorationAndCommentary.md before it was knitr'd.
* **figure**  - This folder has the images for the graphs that appear when you are viewing the ExplorationAndCommentary.md file.

## Possibilities for Future Exploration ##
Being that I have just scratched the surface of understanding the underlying structure and dynamics of forums, here are some thoughts as to areas that can be further explored.

Forums are subject to social dynamics. That is, the personalities, habits, and relationships of a forum's participants play important roles in the successful-ness of the forum. In future analysis, it would be interesting to dig into these relationships and ask questions like: are users more likely to answer a question if the asker helped them in the past? Does getting answers generally drive participants to 'pass it on' and give someone else an answer? Are there certain individuals who can single-handedly have a significant impact on a forum's dynamics?

Being that we see significant differences between SQL Server forums and SharePoint forums, it would be insightful to better understand what's being done differently in these spaces. Talking to experts on these forums might be helpful. Also, adding other forum categories to the analysis to see how they compare would add more color. Perhaps every forum category has it's own unique profile, or perhaps most forums are like SQL Server forums and SharePoint forums are outliers (or vice versa).

The ForumExplorer d3 visualization is a solid start, but this can definitely be improved upon, and it scope can be broadened to included other data points from the database.

While I have started to play around with text analysis, I have not yet really dug deep enough to provide meaningful insight. With some text analytics basics now in place, it should be possible to start focusing this analysis on real use cases with actionable results.
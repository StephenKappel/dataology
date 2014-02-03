from bs4 import BeautifulSoup
import urllib.request #UPDATED URLLIB2 REFERENCE FOR PYTHON 3.3
import urllib.parse
import csv

class PopulationTableGrabber(object):
    def __init__(self, url):
        self.page = urllib.request.urlopen(url)
        self.soup = BeautifulSoup(self.page)

    def find_all_tabs(self):
        def table_has_enough_rows(elm):
            # tables of interest have a border AND enough rows.
            return elm.name == 'table' and \
              elm.has_attr('bordercolor') and \
              len(elm.find_all('tr')) > 20
        return self.soup.find_all(table_has_enough_rows)

    def parse_one_table(self, tab):
        # munge the table rows
        yearElement = tab.find(colspan='3')
        year = int(yearElement.get_text())
        rows = tab.find_all('tr')
        out = []
        rowNum = 1 #ADDED THIS VARIABLE TO LET US IGNORE FIRST TWO ROWS IN TABLES
        for row in rows:
            if rowNum > 2:
                if row.find('td').has_attr('colspan'):
                    continue
                tds = row.find_all('td')
                rowdata = {
                    'year': year,
                    'rank': tds[0].get_text().replace('.', ''), # REMOVED PERIODS FROM RANK DATA
                    'city': tds[1].get_text(),
                    'pop': float(tds[2].get_text())
                }
                out.append(rowdata)
            rowNum += 1
        return out

    def reshape_city_data(self, all_tabs):
        ''' list of lists'''
        return [self.parse_one_table(tab) for tab in all_tabs]

    def write_csv(self, dicts, filename="citypop.csv"):
        ''' could do without ceremony, but this preserves key order'''
        print(dicts) # ADDED PARENTHESIS SO THAT CODE WORKS IN PYTHON 3.3
        keys = ['year', 'rank', 'city', 'pop']
        f = open(filename, 'w') # CHANGED FROM WB TO W BECAUSE I'M RUNNING IN WINDOWS
        dict_writer = csv.DictWriter(f, fieldnames=keys, lineterminator='\n') # ADDED LINETERMINATOR ARGUMENT TO PREVENT EXTRA CARRIAGE RETURNS BEING ADDED IN WINDOWS
        dict_writer.writer.writerow(keys)
        for di in dicts: # ADDED FOR LOOP TO STOP ERRORS AND HAVE ALL DATA PRITNED OUT
            dict_writer.writerows(di)
        f.close()

pop = PopulationTableGrabber('http://www.peakbagger.com/pbgeog/histmetropop.aspx')
pop.write_csv(pop.reshape_city_data(pop.find_all_tabs()))

## I transcribed total population in millions:
## https://docs.google.com/spreadsheet/pub?key=0AruyJI76uB8RdFBySUhzRldyalJGTXZtY1NxT0E2Z1E&output=csv
## source: http://www.census.gov/population/censusdata/table-4.pdf
## and census factfinder2 tables for 2000, 2010.
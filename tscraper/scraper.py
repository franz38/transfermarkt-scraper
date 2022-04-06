import requests
from bs4 import BeautifulSoup
import pandas as pd
import re

from .parser import parse_generic, parse_player, parse_value, parse_date, parse_image
from .settings import *

date_keywords = ["date", "from", "until"]


class Column:
    nameSet = None
    type = None
    colspan = 1

    def __init__(self, label):
        self.label = label

        for kw in date_keywords:
            if kw in label:
                self.type = "date"
                break


class TScraper:

    columns_types = []

    scraped = {}
    """ url: {"table1_title":table1, "table2_title":table2, ..}
    """

    columns = []
    soup = None

    def __init__(self, url=None, **kwargs):

        if kwargs and "columns_types" in kwargs:
            self.columns_types = kwargs["columns_types"]

        # scrape
        if url is not None:
            soup = self.__scrape(url)
            print(self)



    def __scrape(self, url):
        # return table dict
        if url in self.scraped:
            # page already scraped
            return self.scraped[url]
        else:
            page = requests.get(url, headers=REQUEST_HEADERS)
            soup = BeautifulSoup(page.content, "html.parser")
            tables = self.__get_boxes(soup)
            self.scraped[url] = tables
            return tables


    def __str__(self):
        tmp = ""
        tmp += str(len(self.scraped.keys())) + " url scraped:\n"

        for k in self.scraped.keys():
            tables_dict = self.scraped[k]
            tmp += "## url: " + str(k) + " [ " + str(len(tables_dict.keys())) + " tables found ] :"
            tmp += '\n - ' + '\n - '.join(tables_dict.keys()) + "\n"

        return tmp


    def __get_boxes(self, soup):
        boxes_dict = {}
        boxes = soup.find_all("div", {"class": "box"})

        for i, box in enumerate(boxes):

            if box.find("table", {"class": "items"}) and box.find("table", {"class": "items"}).find(
                    "thead") and box.find("table", {"class": "items"}).find("tbody"):
                table = box.find("table", {"class": "items"})
            else:
                potential_tables = box.find_all("table")
                for pot_table in potential_tables:
                    if not pot_table.find("thead") or not pot_table.find("tbody"):
                        pot_table.clear()

                if box.find("table") and box.find("thead") and box.find("tbody"):
                    table = box.find("table")
                else:
                    continue

            if box.find("div", {"class": ["table-header", "subkategorie-header"]}, recursive=False):
                title = box.find("div", {"class": ["table-header", "subkategorie-header"]}, recursive=False).text
            elif box.find(["h1", "h2", "h3", "h4", "h5"], recursive=False):
                title = box.find(["h1", "h2", "h3", "h4", "h5"], recursive=False).text
            else:
                title = str(i)
            boxes_dict[title.strip().lower()] = table

        return boxes_dict

    def extract_chart(self, url, chart_title):
        pass

    def extract_tables(self, **kwargs):

        url = []
        tables_titles = []

        if kwargs and "url" in kwargs:
            url = kwargs["url"]
        if kwargs and "table" in kwargs:
            tables_titles = [ x.lower() for x in kwargs["table"] ]


        if len(url) == 1:
            # 1 page, n tables
            tables_dict = self.__scrape(url[0])
            dataframes = []
            for t_title in tables_titles:
                table = tables_dict[t_title]
                df = self.__extract_dataframe(table)
                dataframes.append(df)
            print("Found " + str(len(dataframes)) + " tables in " + str(len(url)) + " urls")
            return dataframes


        elif len(tables_titles) == 1:
            # same table in multiple pages
            dataframes = []
            for u in url:
                tables_dict = self.__scrape(u)
                table = tables_dict[tables_titles[0]]
                df = self.__extract_dataframe(table)
                dataframes.append(df)
            print("Found " + str(len(dataframes)) + " tables in " + str(len(url)) + " urls")
            return dataframes


        elif len(url) == len(tables_titles):
            # 1to1 between urls and tables
            dataframes = []
            for i in range(len(url)):
                u = url[i]
                t_title = tables_titles[i]
                tables_dict = self.__scrape(u)
                table = tables_dict[t_title]
                df = self.__extract_dataframe(table)
                dataframes.append(df)
            print("Found " + str(len(dataframes)) + " tables in " + str(len(url)) + " urls")
            return dataframes

        else:
            print("Table or url format incorrect, must be..")


    def __extract_dataframe(self, table):

        # header
        theader = table.find("thead")
        columns = self.__parse_header(theader)

        # rows
        tbody = table.find("tbody")
        rows = tbody.find_all("tr", recursive=False)

        if len(rows) == 0 and tbody.find_all("td", recursive=False):
            td_s = tbody.find_all("td", recursive=False)
            tmp = []
            row = []
            for i, td in enumerate(td_s):
                row.append(td)
                if len(row) == len(columns):
                    tmp.append(row)
                    row = []
            rows = tmp

        else:
            tmp = []
            for row in rows:
                tmp.append(row.find_all("td", recursive=False))
            rows = tmp

        # parse rows
        row_values_list = []
        for row in rows:
            values = self.parse_row(row, columns)
            if values is not None:
                row_values_list.append(values)

        # make df
        df = pd.DataFrame(row_values_list, columns=[x.label for x in columns])
        for col in columns:
            if col.type == "date":
                df = df.astype({col.label: 'datetime64'})
            elif col.type == "int":
                df = df.astype({col.label: 'int64'})
            elif col.type == "float":
                df = df.astype({col.label: 'float64'})

        return df


    def __parse_header(self, theader):

        th_s = theader.find_all("th")
        cols = []
        for i, th in enumerate(th_s):
            if (th.has_attr('class')) and ("hide" in th['class']):
                pass
            else:
                txt = th.text.strip()
                if txt == "" and th.find("span", {"class": "icons_sprite"}):
                    if th.find("span", {"class": "icons_sprite"}).has_attr("title"):
                        txt = th.find("span", {"class": "icons_sprite"})["title"]

                col = Column(txt)
                if i < len(self.columns_types) and self.columns_types[i]:
                    col.type = self.columns_types[i]
                cols.append(col)

                if th.has_attr("colspan"):
                    col.colspan = int(th["colspan"])
                    for j in range(int(th["colspan"]) - 1):
                        cols.append(col)

        return cols

    def parse_row(self, td_arr, columns):

        values = []

        for i, td in enumerate(td_arr):

            header = columns[i].label
            col = columns[i]

            if (td.has_attr('class')) and ("hide" in td['class']):
                pass

            elif td.has_attr('colspan'):
                colspan = int(td["colspan"])

                for j in range(colspan):
                    if len(values) == len(columns):
                        break
                    values.append(None)

            else:

                if col and col.type == "date":
                    values.append(parse_date(td))
                # elif (col and col.type=="value"):
                #     tmp.append(self.parse_value(td))
                elif header == "player":
                    values.append(parse_player(td))
                elif header == "Nat.":
                    values.append(parse_image(td))
                else:
                    values.append(parse_generic(td))

        if len(values) != len(columns):
            return None

        # print(values)
        return values

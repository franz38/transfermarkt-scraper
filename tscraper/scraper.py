import requests
from bs4 import BeautifulSoup
import pandas as pd
import re

from .parser import parse_generic, parse_int, parse_player, parse_value, parse_date, parse_image
from .settings import *



class Column:

    nameSet = None
    type = None
    colspan = 1

    def __init__(self, label):
        self.label = label

    def guess_type(self):

        for kw in DATE_COLUMN_KEYWORDS:
            if kw in self.label.lower():
                self.type = TScraper.DATETIME64
                break
        for kw in INTEGER_COLUMN_KEYWORDS:
            if kw in self.label.lower():
                self.type = TScraper.INT64
                break

    def set_type(self, column_type):
        self.type = column_type


class TScraper:

    INT64 = 1
    FLOAT64 = 2
    DATETIME64 = 3


    __columns_types = []

    __scraped = {}
    """ url: {"table1_title":table1, "table2_title":table2, ..}
    """

    def __init__(self, url=None, **kwargs):

        if kwargs and "columns_types" in kwargs:
            self.__columns_types = kwargs["columns_types"]

        # scrape
        if url is not None:
            soup = self.__scrape(url)
            print(self)



    def __scrape(self, url):
        # return table dict
        if url in self.__scraped:
            # page already scraped
            return self.__scraped[url]
        else:
            page = requests.get(url, headers=REQUEST_HEADERS)
            soup = BeautifulSoup(page.content, "html.parser")
            tables = self.__get_boxes(soup)
            self.__scraped[url] = tables
            return tables


    def __str__(self):
        tmp = ""
        tmp += str(len(self.__scraped.keys())) + " url scraped:\n"

        for k in self.__scraped.keys():
            tables_dict = self.__scraped[k]
            tmp += "## url: " + str(k) + "\n[ " + str(len(tables_dict.keys())) + " tables found ] :"
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

            if box.find("div", {"class": TM_BOX_HEADER_CLASS}, recursive=False):
                title = box.find("div", {"class": TM_BOX_HEADER_CLASS}, recursive=False).text
            elif box.find(HTML_HEADERS, recursive=False):
                title = box.find(HTML_HEADERS, recursive=False).text
            else:
                title = str(i)
            boxes_dict[title.strip().lower()] = table

        return boxes_dict

    def extract_chart(self, url, chart_title):
        pass

    def extract_tables(self, **kwargs):

        url = []
        tables_titles = []
        dtypes = None

        if kwargs and "url" in kwargs:
            url = kwargs["url"]
        if kwargs and "table" in kwargs:
            tables_titles = [ x.lower() for x in kwargs["table"] ]
        if kwargs and "guess_types" in kwargs:
            guess_types = kwargs["guess_types"]
        else:
            guess_types = False
        if kwargs and "dtypes" in kwargs:
            dtypes = kwargs["dtypes"]


        if len(url) == 1:
            # 1 page, n tables
            tables_dict = self.__scrape(url[0])
            dataframes = []
            for t_title in tables_titles:
                table = tables_dict[t_title]
                df = self.__extract_dataframe(table, guess_types, dtypes)
                dataframes.append(df)
            print("Found " + str(len(dataframes)) + " tables in " + str(len(url)) + " urls")
            return dataframes


        elif len(tables_titles) == 1:
            # same table in multiple pages
            dataframes = []
            for u in url:
                tables_dict = self.__scrape(u)
                table = tables_dict[tables_titles[0]]
                df = self.__extract_dataframe(table, guess_types, dtypes)
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
                df = self.__extract_dataframe(table, guess_types, dtypes)
                dataframes.append(df)
            print("Found " + str(len(dataframes)) + " tables in " + str(len(url)) + " urls")
            return dataframes

        else:
            print("Table or url format incorrect, must be..")


    def __extract_dataframe(self, table_soup, guess_types=False, dtypes=None):

        # header
        theader = table_soup.find("thead")
        columns = self.__parse_header(theader, guess_types)

        if dtypes is not None:
            for column in columns:
                if column.label in dtypes:
                    dtype = dtypes[column.label]
                    column.set_type(dtype)


        # rows
        tbody = table_soup.find("tbody")
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
            values = self.__parse_row(row, columns, guess_types)
            if values is not None:
                row_values_list.append(values)

        # make df
        df = pd.DataFrame(row_values_list, columns=[x.label for x in columns])

        # change dtypes
        for col in columns:
            if col.type == TScraper.DATETIME64:
                df = df.astype({col.label: 'datetime64'})
            elif col.type == TScraper.INT64:
                df[col.label] = df[col.label].fillna(0)
                df = df.astype({col.label: 'int64'})
            elif col.type == TScraper.FLOAT64:
                df = df.astype({col.label: 'float64'})

        return df


    def __parse_header(self, theader, guess_types=False):

        th_s = theader.find_all("th")
        cols = []
        for i, th in enumerate(th_s):
            if (th.has_attr('class')) and ("hide" in th['class']):
                pass
            else:
                txt = th.text.strip()
                if txt == "" and th.find("span", {"class": TABLE_HEADER_ICON_CLASS}):
                    if th.find("span", {"class": TABLE_HEADER_ICON_CLASS}).has_attr("title"):
                        txt = th.find("span", {"class": TABLE_HEADER_ICON_CLASS})["title"]

                col = Column(txt)
                if guess_types:
                    col.guess_type()

                if i < len(self.__columns_types) and self.__columns_types[i]:
                    col.type = self.__columns_types[i]
                cols.append(col)

                if th.has_attr("colspan"):
                    col.colspan = int(th["colspan"])
                    for j in range(int(th["colspan"]) - 1):
                        cols.append(col)

        return cols

    def __parse_row(self, td_arr, columns, guess_types=False):

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

                if guess_types and col.type is not None:
                    #print(col.type)
                    if col.type == TScraper.DATETIME64:
                        values.append(parse_date(td))
                    elif col.type == TScraper.INT64:
                        values.append(parse_int(td))
                    else:
                        values.append(parse_generic(td))
                else:
                    values.append(parse_generic(td))

                # if col and col.type == TScraper.DATETIME64:
                #     values.append(parse_date(td))
                # # elif (col and col.type=="value"):
                # #     tmp.append(self.parse_value(td))
                # elif header == "player":
                #     values.append(parse_player(td))
                # elif header == "Nat.":
                #     values.append(parse_image(td))
                # else:


        if len(values) != len(columns):
            return None

        # print(values)
        return values

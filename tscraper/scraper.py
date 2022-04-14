import requests
from bs4 import BeautifulSoup
import pandas as pd

from .settings import *
from .column_manager import VirtualTable, Column, PlayerColumn, NumericColumn, TeamColumn, DateColumn


class TScraper:
    DEFAULT = DEFAULT
    NUMERIC = NUMERIC
    DATETIME = DATETIME
    TEAM = TEAM
    PLAYER = PLAYER

    __scraped = {}
    """ url: {"table1_title":table1, "table2_title":table2, ..}
    """

    def __init__(self, url=None, **kwargs):

        # scrape
        if url is not None:
            soup = self.__scrape(url)

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

    # def extract_chart(self, url, chart_title):
    #     pass

    def extract_tables(self, **kwargs):

        url = []
        tables_titles = []
        dtypes = {}

        if kwargs and "url" in kwargs:
            url = kwargs["url"]
            if isinstance(url, str):
                tmp = url
                url = [tmp]

        if kwargs and "table" in kwargs:
            tables_titles = kwargs["table"]
            if isinstance(tables_titles, str):
                tmp = tables_titles
                tables_titles = [tmp]
            tables_titles = [x.lower() for x in tables_titles]

        if kwargs and "guess_types" in kwargs:
            guess_types = kwargs["guess_types"]
        else:
            guess_types = False

        if kwargs and "dtypes" in kwargs:
            dtypes = kwargs["dtypes"]

        """
        
        """
        pairs = []
        if len(url) == 1:
            for t_title in tables_titles:
                pairs.append((url[0], t_title))

        elif len(tables_titles) == 1:
            for u in url:
                pairs.append((u, tables_titles[0]))

        elif len(url) == len(tables_titles):
            for i in range(len(url)):
                u = url[i]
                t_title = tables_titles[i]
                pairs.append((u, t_title))

        else:
            print("Table or url format incorrect, must be..")

        dataframes = []
        ttt = None
        for url, table_name in pairs:
            tables_dict = self.__scrape(url)
            table = tables_dict[table_name]

            table = self.__extract_dataframe(table, guess_types, dtypes)
            if ttt is None:
                ttt = table
            elif ttt == table:
                ttt.add(table)
            # table_dict = table.get()
            # print(table_dict)
            # df = pd.DataFrame(table_dict)
            # print(df)

            # change dtypes
            # for col in columns:
            #     if isinstance(col, NumericColumn):
            #         df = df.astype({col.label: 'float64'})

            # dataframes.append(df)

        dicttt = ttt.get()
        df = pd.DataFrame(dicttt)
        return df

    def __extract_dataframe(self, table_soup, guess_types=False, dtypes={}):

        # header
        theader = table_soup.find("thead")
        # columns = self.__parse_header(theader, guess_types, dtypes)

        table = VirtualTable(theader, guess_types, dtypes)

        # rows
        tbody = table_soup.find("tbody")
        rows = tbody.find_all("tr", recursive=False)

        if len(rows) == 0 and tbody.find_all("td", recursive=False):
            td_s = tbody.find_all("td", recursive=False)
            tmp = []
            row = []
            for i, td in enumerate(td_s):
                row.append(td)
                if len(row) == len(table.columns):
                    tmp.append(row)
                    row = []
            rows = tmp

        else:
            tmp = []
            for row in rows:
                tmp.append(row.find_all("td", recursive=False))
            rows = tmp

        # parse rows
        for row in rows:
            table.parse_row(row)
            # self.__parse_row(row, columns)

        # make dict
        # columns_dict = {}
        # for column in columns:
        #     column.parse()
        #     for col_h, col_vals in column.get():
        #         columns_dict[col_h] = col_vals
        #         print(col_h + " : " + str(len(col_vals)))
        #
        #         if col_h == "Pos.":
        #             print(col_vals)

        return table

        # make df
        # df = pd.DataFrame(columns_dict)
        #
        # # change dtypes
        # for col in columns:
        #     if isinstance(col, NumericColumn):
        #         df = df.astype({col.label: 'float64'})
        #
        # return df

    def __parse_header(self, theader, guess_types, dtypes):

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

                if txt in dtypes:
                    datatype = dtypes[txt]
                    if datatype == PLAYER:
                        col = PlayerColumn(txt)
                    elif datatype == TEAM:
                        col = TeamColumn(txt)
                    elif datatype == NUMERIC:
                        col = NumericColumn(txt)
                    elif datatype == DATETIME:
                        col = DateColumn(txt)

                elif guess_types:
                    for kw in PLAYER_COLUMN_KEYWORDS:
                        if kw in txt.lower():
                            col = PlayerColumn(txt)
                            break
                    for kw in INTEGER_COLUMN_KEYWORDS:
                        if kw in txt.lower():
                            col = NumericColumn(txt)
                            break

                cols.append(col)

                if th.has_attr("colspan"):
                    col.colspan = int(th["colspan"])
                    for j in range(int(th["colspan"]) - 1):
                        newcol = Column(txt + "_" + str(j + 1))
                        cols.append(newcol)

        return cols

    def __parse_row(self, td_arr, columns):

        values = []

        filtered = list(filter(lambda x: not (x.has_attr('class') and "hide" in x['class']), td_arr))

        for z, col in enumerate(columns):

            if not len(td_arr) > z:
                col.add(None)
            else:
                td = filtered[z]
                col.add(td)

        return values

import requests
from bs4 import BeautifulSoup
import pandas as pd
import re

from .settings import *
from .parser import parse_generic, parse_numeric, parse_player, parse_date

""" Boolean

"""
def is_column_meaningful(mylist):
    return len(list(filter(lambda val: val is not None, mylist))) > 0



class VirtualTable:

    def __init__(self, theader, guess_types, dtypes):
        self.columns = {}
        self.parse_header(theader, guess_types, dtypes)
        # for c_name in self.columns_names:
        #     self.columns[c_name] = []

    def __eq__(self, other):
        if len(self.columns) == len(other.columns):
            for c_name in self.columns:
                if c_name not in other.columns:
                    return False
            return True
        return False

    def add(self, other):
        if self == other:
            for k in self.columns:
                self.columns[k].td_s.extend(other.columns[k].td_s)


    def parse_header(self, theader, guess_types, dtypes):

        th_s = theader.find_all("th")

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

                self.columns[txt] = col

                if th.has_attr("colspan"):
                    col.colspan = int(th["colspan"])
                    for j in range(int(th["colspan"]) - 1):
                        newcol = Column(txt + "_" + str(j + 1))
                        self.columns[txt + "_" + str(j + 1)] = newcol

    def parse_row(self, td_arr):
        values = []
        filtered = list(filter(lambda x: not (x.has_attr('class') and "hide" in x['class']), td_arr))

        for z, col_key in enumerate(self.columns):
            col = self.columns[col_key]
            if not len(td_arr) > z:
                col.add(None)
            else:
                td = filtered[z]
                col.add(td)

        return values

    def get(self):
        tmp = {}
        for k in self.columns:
            column = self.columns[k]
            column.parse()
            for col_h, col_vals in column.get():
                tmp[col_h] = col_vals
        return tmp

class Column:
    nameSet = None
    type = None
    colspan = 1

    def __init__(self, label):
        self.label = label
        self.td_s = []
        self.values = []

    def add(self, td):
        self.td_s.append(td)

    def parse(self):

        for td in self.td_s:
            value = parse_generic(td)
            self.values.append(value)

    """ Return a list of tuples with one element, first element of the tuple 
        is the column label, the second element is the list of values
    """
    def get(self):

        tmp = []
        tmp.append((self.label, self.values))
        return tmp

    """
    """
    def __str__(self):
        tmp = ""
        for val in self.values:
            tmp += str(val) + "\n"
        return tmp


class PlayerColumn(Column):

    def __init__(self, label):
        super().__init__(label)
        self.positions = []

    def parse(self):

        for td in self.td_s:
            value, position = parse_player(td)
            self.values.append(value)
            self.positions.append(position)

    """ Return a list of tuples, first element is the column label, 
        the second element is the list of values.
        The optional tuple contains the roles extracted from player column (if any)
    """
    def get(self):
        tmp = []
        tmp.append((self.label, self.values))
        if is_column_meaningful(self.positions):
            tmp.append((self.label + "__position", self.positions))
        return tmp


class TeamColumn(Column):

    def __init__(self, label):
        super().__init__(label)
        self.leagues = []

    def parse(self):

        for td in self.td_s:
            value, league = parse_player(td)
            self.values.append(value)
            self.leagues.append(league)

    """ Return a list of tuples, first element is the column label, 
        the second element is the list of values.
        The optional tuple contains the leagues of the teams (if any)
    """
    def get(self):
        tmp = []
        tmp.append((self.label, self.values))
        if is_column_meaningful(self.leagues):
            tmp.append((self.label + "__league", self.leagues))
        return tmp


class DateColumn(Column):

    def __init__(self, label):
        super().__init__(label)
        self.ages = []

    def parse(self):

        for td in self.td_s:
            value, age = parse_date(td)
            self.values.append(value)
            self.ages.append(age)

    """ Return a list of tuples, first element is the column label, 
        the second element is the list of values.
        The optional tuple contains the ages of the players (if any)
    """
    def get(self):
        tmp = []
        tmp.append((self.label, self.values))
        if is_column_meaningful(self.ages):
            tmp.append((self.label + "__age", self.ages))
        return tmp


class NumericColumn(Column):

    def __init__(self, label):
        super().__init__(label)
        self.units = []
        self.multiples = []
        self.notes = []

    def parse(self):
        for td in self.td_s:
            value, unit, multiple, note = parse_numeric(td)
            self.values.append(value)
            self.units.append(unit)
            self.multiples.append(multiple)
            self.notes.append(note)

    def __get_coefficent(self, from_mult, to_mult):

        if from_mult is None or to_mult is None:
            return 1

        multiples = {
            'B': 9,
            'm': 6,
            'Th.': 3,
        }
        pow_ = multiples[from_mult] - multiples[to_mult]
        return pow(10, pow_)

    """ Return a list of tuples, first element is the column label, 
        the second element is the list of values.
        The optional tuple contains non numeric comments 
        extracted from the column (if any)
    """
    def get(self):
        tmp = []

        tmp_multiples = []
        for prefix in self.multiples:
            if prefix is not None:
                tmp_multiples.append(prefix)

        if len(tmp_multiples) > 0:
            base_mult = self.__most_frequent(tmp_multiples)
            for i in range(len(self.values)):
                value = self.values[i]
                prefix = self.multiples[i]
                if value is not None and value != 0:
                    coeff = self.__get_coefficent(prefix, base_mult)
                    self.values[i] = float(value) * coeff

        tmp.append((self.label, self.values))
        if len(list(filter(lambda x: x is not None, self.notes))) > 0:
            tmp.append((self.label + "__note", self.notes))
        return tmp

    def __most_frequent(self, list):
        return max(set(list), key=list.count)

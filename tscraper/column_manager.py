import requests
from bs4 import BeautifulSoup
import pandas as pd
import re

from .parser import parse_generic, parse_numeric, parse_player, parse_date, parse_image


def is_column_meaningful(mylist):
    return len(list(filter(lambda val: val is not None, mylist))) > 0


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

    def get(self):

        tmp = []
        tmp.append((self.label, self.values))
        return tmp

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

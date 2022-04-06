import re
from .settings import *

def parse_generic(td):
    txt = td.text.strip()

    if (not td.has_attr('class') or "no-border-links" in td['class']) and td.find("a", recursive=False ):
        link = td.find("a", recursive=False )
        if (link.find("span", {"class": VALUE_HIDE_SMALL_CLASS})) and (link.find("span", {"class": VALUE_SHOW_SMALL_CLASS})):
            txt = link.find("span", {"class": VALUE_HIDE_SMALL_CLASS}).text.strip()
        else:
            txt = link.text.strip()

    if txt=="":
        if td.find("span"):
            txt = td.find("span")["title"]
        elif td.find("img"):
            txt = td.find("img")["alt"] or td.find("img")["title"]
    return txt.strip()


def parse_player(td):

    name = td.text
    position = ""
    if (td.find("table")):
        tr_s = td.find("table").find_all("tr", recursive=False)
        name_item, position_item = tr_s
        if (name_item.find("span", {"class": VALUE_HIDE_SMALL_CLASS})) and (name_item.find("span", {"class": VALUE_SHOW_SMALL_CLASS})):
            name = name_item.find("span", {"class": VALUE_HIDE_SMALL_CLASS}).text
        else:
            name = name_item.text

    return name.strip()


def parse_image(td):
    return td.find("img")["alt"].strip()


def parse_value(td):

    currencies = ['$', '€']
    currency = None
    txt = td.text
    for tmp_currency in currencies:
        if tmp_currency in txt:
            currency = tmp_currency
            break
    txt = txt.replace(currency, '')


    multiples = {
        'Th.':1000,
        'm':1000000
    }
    mult=1
    for k in multiples:
        if k in txt:
            mult = multiples[k]
            txt=txt.replace(k, '')
            break
    return txt


def parse_date(td):

    txt = td.text
    if re.search('\(..\)', td.text):
        age = re.search('\(..\)', td.text).group(0)
        txt = txt.replace(age, '')
        age = age.replace('(','').replace(')','')

    txt = txt.replace(',', '')
    return txt.strip()
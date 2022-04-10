import re
from .settings import *

def parse_generic(td):

    if td is None:
        return None

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
    position = None

    if td.find("table"):
        tr_s = td.find("table").find_all("tr", recursive=False)
        name_item, position_item = tr_s
        if (name_item.find("span", {"class": VALUE_HIDE_SMALL_CLASS})) and (name_item.find("span", {"class": VALUE_SHOW_SMALL_CLASS})):
            name = name_item.find("span", {"class": VALUE_HIDE_SMALL_CLASS}).text
        else:
            name = name_item.text
        position = position_item.text.strip()

    return name.strip(), position


def parse_team(td):

    return parse_player(td)



def parse_image(td):
    return td.find("img")["alt"].strip()




def extract_value(txt):

    search = re.search("[$€\']?[0-9.,]+(m|Th.)?", txt)
    if len(re.findall("[$€\']?[0-9.,]+(m|Th.)?", txt)) != 1:
        return None

    if search is not None:

        value = search.group(0)
        unit = re.search("[$€\']", value)
        prefix = re.search("(m|Th.)", value)

        if unit is not None:
            unit = unit.group(0)
            value = value.replace(unit, '')

        if prefix is not None:
            prefix = prefix.group(0)
            value = value.replace(prefix, '')

        return value, unit, prefix
    return None


def parse_numeric(td):
    
    txt = td.text
    sub_text = None

    if td.find("a") and td.find("a").find("i"):
        sub_element = td.find("a").find("i")
        sub_text = sub_element.text
        txt = txt.replace(sub_text, '')

    value = 0
    unit = prefix = other = None

    if txt is not None and extract_value(txt) is not None:
        value, unit, prefix = extract_value(txt)
        other = sub_text

    elif sub_text is not None and extract_value(sub_text) is not None:
        value, unit, prefix = extract_value(sub_text)
        other = txt

    else:
        if txt is not None and txt != "" and txt != "-":
            other = str(txt)
        if sub_text is not None and sub_text != "" and sub_text != "-":
            other += str(sub_text)

    return value, unit, prefix, other


def parse_date(td):

    txt = td.text
    age = None
    if re.search('\([0-9]{1,2}\)', td.text):
        age = re.search('\(..\)', td.text).group(0)
        txt = txt.replace(age, '')
        age = age.replace('(','').replace(')','')

    txt = txt.replace(',', '')
    return txt.strip(), age



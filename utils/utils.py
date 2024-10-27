import pickle
import re
import pytz

def load_model(path):
    with open(path, "rb") as fin:
        tree_loaded = pickle.load(fin)

    return tree_loaded

def is_number(s):
    pattern = r'^\s*-?\d+(\.\d+)?\s*$'

    return bool(re.match(pattern, s))

def is_only_latin_letters(s):
    pattern = r'^[a-zA-Z]+$'

    return bool(re.match(pattern, s))

def utc_to_moscow(utc_datetime):
    tz_moscow = pytz.timezone('Europe/Moscow')

    utc_datetime = utc_datetime.replace(tzinfo=pytz.utc)
    moscow_datetime = utc_datetime.astimezone(tz_moscow)
    return moscow_datetime
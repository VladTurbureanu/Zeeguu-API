import re

def split_words_from_text(text):
    words = []
    words = re.findall(r'(?u)\w+', text)
    return words
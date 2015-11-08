import re
import threading
import multiprocessing
from goose import Goose


def split_words_from_text(text):
    words = []
    words = re.findall(r'(?u)\w+', text)
    return words


class PageExtractor:
    goose = Goose()

    def __init__(self, url):
        self.article = PageExtractor.goose.extract(url=url)

    def get_content(self):
        return self.article.cleaned_text

    def get_image(self):
        if self.article.top_image is not None:
            return self.article.top_image.src
        else:
            return ""

    @classmethod
    def worker(cls, url, id, result):
        article = cls(url)
        result.put(dict(content=article.get_content(), image=article.get_image(), id=id))
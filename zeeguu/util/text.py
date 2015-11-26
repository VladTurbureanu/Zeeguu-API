import regex
from goose import Goose


def split_words_from_text(text):
    words = regex.findall(ur'(\b\p{L}+\b)', text)
    return words


def generate_histogram(words_difficulty):
    histogram_groups = dict()

    for difficulty in words_difficulty:
        group = int(difficulty*10)/10.0 # round down
        # print str(difficulty) + " -> " + str(group)
        if group in histogram_groups:
            histogram_groups[group] += 1
        else:
            histogram_groups[group] = 1

    current_group = 0.0
    csv_groups = ""
    for i in xrange(10):
        if i is not 9:
            if current_group in histogram_groups:
                csv_groups += str(histogram_groups[current_group]) + "; "
            else:
                csv_groups += "0; "
        else:
            if current_group in histogram_groups:
                csv_groups += str((histogram_groups[current_group]+histogram_groups[1.0])) + ";"
            else:
                csv_groups += str(histogram_groups[1.0]) + ";"
        current_group += 0.1
        current_group = round(current_group, 1)

    print csv_groups


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
__author__ = 'mircea'


import zeeguu_testcase

class TranslationTests(zeeguu_testcase.ZeeguuTestCase):

    def test_get_url_for_dicts_taht_do_nasty_urls(self):
        dictionaries = [
            'http://pda.leo.org/#/search=fantastisch',
        ]

        for d in dictionaries:
            formData = dict(url=d)
            rv = self.app.post(self.in_session('/get_page'), data=formData)
            if 'fantastic' in rv.data:
                print "OK for " + d
            else:
                print "Fail for " + d
                print rv.data


if __name__ == '__main__':
    unittest.main()

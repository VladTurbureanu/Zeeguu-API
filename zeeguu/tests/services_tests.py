# coding=utf-8
import zeeguu_testcase
# Always must be imported first
# it sets the test DB

import unittest


class ServicesTests(zeeguu_testcase.ZeeguuTestCase):

    def setUp(self):
        # Superclass does prepare the DB before each of the tests
        super(ServicesTests, self).setUp()

    def tearDown(self):
        pass

    def test_collins_translation(self):
        from zeeguu.translation.german.german_translator \
            import get_all_possible_translations_from_the_collins_api

        print get_all_possible_translations_from_the_collins_api("tor")
        assert len(get_all_possible_translations_from_the_collins_api("haus")) > 0

if __name__ == '__main__':
    # unittest.main()
    suite = unittest.TestLoader().loadTestsFromTestCase(ServicesTests)
    unittest.TextTestRunner(verbosity=3).run(suite)

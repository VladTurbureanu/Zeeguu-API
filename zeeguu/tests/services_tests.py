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
        from zeeguu.api.translation_service import translate_using_collins_dictionary
        assert translate_using_collins_dictionary("entspricht") is not None

if __name__ == '__main__':
    # unittest.main()
    suite = unittest.TestLoader().loadTestsFromTestCase(ServicesTests)
    unittest.TextTestRunner(verbosity=3).run(suite)

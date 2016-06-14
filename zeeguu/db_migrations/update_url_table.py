# -*- coding: utf8 -*-

"""
Used on Jan 15, 2015 to prepare the DB for commit
8d597c30cc9906baf5dde36bd54d5e33704858ea
"""

import zeeguu
from zeeguu.model.domain_name import DomainName
from zeeguu.model.url import Url


def set_default_exercise_based_prob():
    zeeguu.app.test_request_context().push()
    zeeguu.db.session.commit()

    urls = Url.query.all()

    for url in urls:
        url.path = Url.get_path(url.url)
        d = DomainName.find(Url.get_domain(url.url))
        url.domain = d

        zeeguu.db.session.add(url)
        zeeguu.db.session.add(d)
        zeeguu.db.session.commit()


if __name__ == "__main__":
    try:
        set_default_exercise_based_prob()
        print ("Migration OK")
    except Exception:
        print ("Ooops")

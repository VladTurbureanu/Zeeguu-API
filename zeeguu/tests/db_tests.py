__author__ = 'ada'
import zeeguu_testcase
import unittest
from zeeguu.model import User
from sqlalchemy import Column, ForeignKey, Integer, String, Binary
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy import create_engine

Base = declarative_base()

class DB_Tests(zeeguu_testcase.ZeeguuTestCase):

    # def setUp(self):
    #     con_string = 'mysql://{}:{}@{}'.format("zeeguu", "sla2012", "localhost/zeeguu")
    #     engine = create_engine(con_string)
    #
    #     from sqlalchemy.orm import sessionmaker
    #
    #     Base.metadata.bind = engine # bind-uim informatiile metadata din Base la engine
    #     DBSession = sessionmaker(engine) # cream o clasa DBsession
    #
    #     # cream un obiect sesiune de tip clasa DBSession/ deschidem o noua sesiune in baza de date
    #     self.session = DBSession()

    def test1(self):

        users = self.session.query(User).all()
        for u in users:
            print u.name + ":" + u.name + ":" + u.email



if __name__ == '__main__':
    unittest.main()

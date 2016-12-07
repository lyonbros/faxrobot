import os
from models import db
from models.account import Account
from datetime import datetime
from sqlalchemy import func, Column, BigInteger, SmallInteger, Integer, \
    String, Float, DateTime, ForeignKey, Text
from sqlalchemy.orm.session import Session
from sqlalchemy.exc import SQLAlchemyError
from library.grab_bag import random_hash, o
from library.errors import ValidationError

class IncomingFax(db.Model):
    __tablename__ = 'incoming_fax'

    id              = Column(BigInteger, primary_key=True)
    account_id      = Column(BigInteger, ForeignKey('account.id'))
    external_id     = Column(BigInteger)
    account         = db.relationship('Account', 
                        backref=db.backref('incoming_faxes',order_by=id))
    access_key      = Column(String(64), unique=True, index=True)
    num_pages       = Column(Integer)
    cost            = Column(Float)
    from_number     = Column(String(32))
    to_number       = Column(String(32))
    hosted_url      = Column(String(255))
    data_deleted    = Column(SmallInteger, default=0)
    create_date     = Column(DateTime)
    mod_date        = Column(DateTime)

    def __init__(self, account_id, external_id, num_pages, cost, from_number,
        to_number):

        self.create_date        = datetime.now()
        self.account_id         = account_id
        self.external_id        = external_id
        self.num_pages          = num_pages
        self.cost               = cost
        self.from_number        = from_number
        self.to_number          = to_number
        self.access_key         = random_hash("%s%s%s%s%s" % (from_number,
                                    to_number, cost, num_pages, account_id))

 
    def public_data(self):
        """
        Returns a dictionary of fields that are safe to display to the end user.
        """

        data = {
            'id':               self.id,
            'access_key':       self.access_key,
            'num_pages':        self.num_pages,
            'cost':             self.cost,
            'from_number':      self.from_number,
            'to_number':        self.to_number,
            'data_deleted':     self.data_deleted,
            'create_date':      self.create_date,
            'mod_date':         self.mod_date
        }

        return data;

    def __repr__(self):
        return "<IncomingFax(id='%s', account_id='%s', from_number='%s')>" % \
            (self.id, self.account_id, self.from_number)
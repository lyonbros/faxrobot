from models import db
from datetime import datetime
from sqlalchemy import func, Column, BigInteger, SmallInteger, Integer, \
    String, Float, DateTime, ForeignKey, Text
from sqlalchemy.orm.session import Session
from sqlalchemy.exc import SQLAlchemyError

class Transaction(db.Model):
    __tablename__ = 'transaction'

    id              = Column(BigInteger, primary_key=True)
    account_id      = Column(Integer, ForeignKey('account.id'))
    account         = db.relationship('Account', 
                        backref=db.backref('transactions',order_by=id))
    amount          = Column(Float)
    initial_balance = Column(Float)
    job_id          = Column(BigInteger, index=True)
    job_destination = Column(String(32))
    source          = Column(String(10))
    source_id       = Column(String(64))
    ip_address      = Column(String(255))
    note            = Column(String(255))
    trans_type      = Column(String(64))
    create_date     = Column(DateTime)
    mod_date        = Column(DateTime)

    def __init__(self, account_id, amount, job_id=None, job_destination=None,
            source=None, source_id=None, ip_address=None, initial_balance=None,
            note=None, trans_type=None):

        self.create_date        = datetime.now()
        self.account_id         = account_id
        self.amount             = amount
        self.job_id             = job_id
        self.job_destination    = job_destination
        self.source             = source
        self.source_id          = source_id
        self.ip_address         = ip_address
        self.initial_balance    = initial_balance
        self.note               = note
        self.trans_type         = trans_type

    def public_data(self):
        """
        Returns a dictionary of fields that are safe to display to the client.
        """

        return {
            'id': self.id,
            'amount': self.amount,
            'initial_balance': self.initial_balance,
            'job_id': self.job_id,
            'job_destination': self.job_destination,
            'source': self.source,
            'source_id': self.source_id,
            'ip_address': self.ip_address,
            'trans_type': self.trans_type,
            'create_date': self.create_date
        };

    def __repr__(self):
        return "<Transaction(id=%s, account_id=%s, amount=%s, source='%s')>" % \
            (self.id, self.account_id, self.amount, self.source)
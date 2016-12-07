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

class Job(db.Model):
    __tablename__ = 'job'

    id              = Column(BigInteger, primary_key=True)
    account_id      = Column(BigInteger, ForeignKey('account.id'))
    external_id     = Column(BigInteger, index=True)
    account         = db.relationship('Account', 
                        backref=db.backref('jobs',order_by=id))
    filename        = Column(String(255))
    body            = Column(Text)
    destination     = Column(String(32))
    attempts        = Column(Integer, default=0)
    num_pages       = Column(Integer)
    cost            = Column(Float)
    cover_cost      = Column(Float)
    international   = Column(SmallInteger, default=0)
    device          = Column(String(64))
    failed          = Column(SmallInteger, default=0)
    fail_code       = Column(Integer, default=0)
    status          = Column(String(255), index=True)
    debug           = Column(Text)
    access_key      = Column(String(64), unique=True, index=True)
    ip_address      = Column(String(64))
    send_authorized = Column(SmallInteger, default=0)
    data_deleted    = Column(SmallInteger, default=0)

    cover           = Column(SmallInteger, default=0)
    cover_name      = Column(String(64))
    cover_address   = Column(String(128))
    cover_city      = Column(String(64))
    cover_state     = Column(String(64))
    cover_zip       = Column(String(64))
    cover_country   = Column(String(64))
    cover_phone     = Column(String(64))
    cover_email     = Column(String(128))
    cover_company   = Column(String(128))
    cover_to_name   = Column(String(64))
    cover_cc        = Column(String(64))
    cover_subject   = Column(String(64))
    cover_status    = Column(String(64))
    cover_comments  = Column(Text)

    callback_url    = Column(String(255))
    callback_fail   = Column(Integer, default=0, index=True)
    callback_date   = Column(DateTime)

    create_date     = Column(DateTime)
    mod_date        = Column(DateTime)
    start_date      = Column(DateTime)
    fail_date       = Column(DateTime)
    end_date        = Column(DateTime)

    def __init__(self, account_id, ip_address, filename=None, destination=None,
            send_authorized=0, cover=0, cover_name=None, cover_address=None,
            cover_city=None, cover_state=None, cover_zip=None,
            cover_country=None, cover_phone=None, cover_email=None,
            cover_company=None, cover_to_name=None, cover_cc=None,
            cover_subject=None, cover_status=None, cover_comments=None,
            body=None, callback_url=None):

        if destination != None:
            self.validate_destination(destination)
            self.destination = destination

        self.create_date        = datetime.now()
        self.account_id         = account_id
        self.filename           = filename
        self.ip_address         = ip_address
        self.send_authorized    = send_authorized
        self.access_key         = random_hash("%s%s" % (account_id, filename))
        self.status             = 'new'

        self.cover              = cover
        self.cover_name         = cover_name
        self.cover_address      = cover_address
        self.cover_city         = cover_city
        self.cover_state        = cover_state
        self.cover_zip          = cover_zip
        self.cover_country      = cover_country
        self.cover_phone        = cover_phone
        self.cover_email        = cover_email
        self.cover_company      = cover_company
        self.cover_to_name      = cover_to_name
        self.cover_cc           = cover_cc
        self.cover_subject      = cover_subject
        self.cover_status       = cover_status
        self.cover_comments     = cover_comments
        self.body               = body
        self.callback_url       = callback_url

    def validate_destination(self, destination):
        if len(destination) < 10:
            raise ValidationError('JOBS_BAD_DESTINATION')
        if not destination.isdigit():
            raise ValidationError('JOBS_BAD_DESTINATION')
        return True

    def determine_international(self):
        if not self.destination:
            return

        destination = self.destination

        if len(destination) == 10:
            self.destination = u"1%s" % destination
            self.international = 0

        elif len(destination) > 11 or \
            (len(destination) == 11 and not destination.startswith(u"1")):
            self.international = 1

        else:
            self.international = 0

    def compute_cost(self):
        if self.account.base_rate:
            page_cost = self.account.base_rate
        else:
            page_cost = float(os.environ.get('DEFAULT_COST_PER_PAGE', '0.10'))

        international_multiplier = self.international + 1

        self.cost = page_cost * self.num_pages * international_multiplier
        self.cover_cost = page_cost * international_multiplier

    def delete_data(self, session=None):
        """
        Removes job data from the server (including optionally Amazon S3).
        """
        import shutil
        import os
        from boto.s3.connection import S3Connection
        from boto.s3.key import Key

        if not session:
            session = db.session

        self.data_deleted   = 1
        self.cover_name     = None
        self.cover_address  = None
        self.cover_city     = None
        self.cover_state    = None
        self.cover_zip      = None
        self.cover_country  = None
        self.cover_phone    = None
        self.cover_email    = None
        self.cover_company  = None
        self.cover_to_name  = None
        self.cover_cc       = None
        self.cover_subject  = None
        self.cover_status   = None
        self.cover_comments = None
        self.body           = None
        self.mod_date       = datetime.now()

        session.commit()

        if os.path.isdir('./tmp/' + self.access_key):
            shutil.rmtree('./tmp/' + self.access_key)

        if os.environ.get('AWS_STORAGE') == "on":
            try:
                conn = S3Connection(os.environ.get('AWS_ACCESS_KEY'),
                                    os.environ.get('AWS_SECRET_KEY'))
                bucket = conn.get_bucket(os.environ.get('AWS_S3_BUCKET'))
            except:
                o("COULD NOT CONNECT TO S3 WTF WTF WTF WTF")
                return

            try:
                for i in range(0, self.num_pages):

                    n = ("0%s" % i) if i < 10 else "%s" % i
                    k = Key(bucket)
                    k.key ='fax/%s/%s.%s.tiff'%(self.access_key,self.filename,n)
                    k.delete()

            except:
                o("COULD NOT DELETE FILES FROM LOCAL OMG SHIT")

        return True

    def validate(self):
        """
        I had as much fun writing this as you'll probably have reading it.
        """

        if self.destination:
            self.validate_destination(self.destination)

        if self.cover and self.cover != 0 and self.cover != 1 and \
            self.cover != "0" and self.cover != "1":
            raise ValidationError('JOBS_BAD_COVER')

        if self.send_authorized and self.send_authorized != 0 and \
                self.send_authorized != 1 and self.send_authorized != "0" and \
                self.send_authorized != "1":
            raise ValidationError('JOBS_BAD_SEND_AUTHORIZED')

        if self.send_authorized and not self.destination:
            raise ValidationError('JOBS_MISSING_DESTINATION')

        if self.filename and len(self.filename) > 255:
            raise ValidationError('JOBS_BAD_FILENAME')

        if self.cover_name and len(self.cover_name) > 64:
            raise ValidationError('JOBS_BAD_COVER_NAME')

        if self.cover_address and len(self.cover_address) > 128:
            raise ValidationError('JOBS_BAD_COVER_ADDRESS')

        if self.cover_city and len(self.cover_city) > 64:
            raise ValidationError('JOBS_BAD_COVER_CITY')

        if self.cover_state and len(self.cover_state) > 64:
            raise ValidationError('JOBS_BAD_COVER_STATE')

        if self.cover_zip and len(self.cover_zip) > 64:
            raise ValidationError('JOBS_BAD_COVER_ZIP')

        if self.cover_country and len(self.cover_country) > 64:
            raise ValidationError('JOBS_BAD_COVER_COUNTRY')

        if self.cover_phone and len(self.cover_phone) > 64:
            raise ValidationError('JOBS_BAD_COVER_PHONE')

        if self.cover_email and len(self.cover_email) > 128:
            raise ValidationError('JOBS_BAD_COVER_EMAIL')

        if self.cover_company and len(self.cover_company) > 128:
            raise ValidationError('JOBS_BAD_COVER_COMPANY')

        if self.cover_to_name and len(self.cover_to_name) > 64:
            raise ValidationError('JOBS_BAD_COVER_TO_NAME')

        if self.cover_cc and len(self.cover_cc) > 64:
            raise ValidationError('JOBS_BAD_COVER_CC')

        if self.cover_subject and len(self.cover_subject) > 64:
            raise ValidationError('JOBS_BAD_COVER_SUBJECT')

        if self.cover_status and len(self.cover_status) > 64:
            raise ValidationError('JOBS_BAD_COVER_STATUS')

        if self.callback_url and len(self.callback_url) > 255:
            raise ValidationError('JOBS_BAD_CALLBACK_URL')

        return True

    def public_data(self):
        """
        Returns a dictionary of fields that are safe to display to the end user.
        """
        if self.cost and self.cover_cost:
            total = self.cost if not self.cover else self.cost+self.cover_cost
        else:
            total = "0"

        data = {
            'id':               self.id,
            'status':           self.status,
            'access_key':       self.access_key,
            'ip_address':       self.ip_address,
            'filename':         self.filename if self.filename else "(text)",
            'destination':      self.destination,
            'attempts':         self.attempts,
            'num_pages':        self.num_pages,
            'cover':            self.cover,
            'cost':             self.cost,
            'cover_cost':       self.cover_cost,
            'international':    self.international,
            'total_cost':       total,
            'send_authorized':  self.send_authorized,
            'data_deleted':     self.data_deleted,
            'create_date':      self.create_date,
            'mod_date':         self.mod_date,
            'start_date':       self.start_date,
            'end_date':         self.end_date,
            'failed':           self.failed,
            'fail_code':        self.fail_code,
            'fail_date':        self.fail_date
        }
        if self.status == 'new' or self.status == 'uploading':
            note = ('We have not yet computed the \'cost\', '
                    '\'cover_cost\', \'total_cost\', or \'num_pages\' fields. '
                    'Do not rely on them yet.')
            data.pop("cost", None)
            data.pop("cover_cost", None)
            data.pop("total_cost", None)
            data.pop("num_pages", None)
            data['NOTE'] = note

        return data;

    def __repr__(self):
        return "<Job(id='%s', account_id='%s', filename='%s')>" % (self.id, \
            self.account_id, self.filename)
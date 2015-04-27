Fax Robot API
=============
#### A Python API to send faxes

Introduction
------------
Fax Robot is an easy-to-use API for sending faxes through your own faxmodem(s).
It's based on a Flask web API and one or more worker processes. Faxes are sent
into a queue (based on [rq][1]), so you can send tons of them in, and they'll be
processed one by one. Or, if you have a bunch of faxmodems and phone lines, you
can run multiple workers and power through them really quickly.

Sending faxes to long distance numbers is not free, so Fax Robot can optionally
collect payments from API users via [Stripe][2]. Users purchase stored credit,
and faxes are charged against this credit based on a fixed cost per page. Or, if
you're feeling generous, you can make it free for anyone with network access.

Fax Robot was designed to be easy to set up and configure by anyone with basic
Python devops skills. It's licensed under
[the GNU General Public License, Version 3][3].

**There is a separate project called [faxrobot-www][7] which is a frontend
webapp for the Fax Robot API.**

Dependencies
------------
* One or more physical faxmodems hooked up to land lines
* Python 2.7
* PostgreSQL
* Redis
* ImageMagick (particularly the `convert` and `composite` commands)
* (Optional) [Stripe API][2], only needed if you're collecting payments.
* (Optional) [Mandrill API][5], for sending account-related emails to
  API users.
* (Optional) [Amazon S3 storage][4]. Only needed if you have multiple servers
  for your workers (basically stores your temp files in the cloud)

Installation
------------
There are two pieces to Fax Robot: a Python Flask API and the worker process
that actually runs through the queue and sends the faxes. How you run the API in
production will vary depending on your hosting infrastructure. This section will
explain how to test the API on your local machine (production is left as an
exercise to the reader). Setting up the worker process is a bit easier, and
always the same whether you're testing or in production.

#### Set up your Virtualenv and packages

You should use [Virtualenv] to isolate Fax Robot's required package dependencies
away from your system Python installation. You don't have to, but come on.
Assuming you have `virtualenv` installed, do the following commands from within
your Fax Robot project directory to install Fax Robot's required packages:

```
virtualenv venv
source venv/bin/activate
pip install -r requirements.txt
```

#### Set up your environment variables

Fax Robot's configuration is stored in system environment variables. You should
create a file called `.env` in your Fax Robot project directory (or wherever you
like). The file should look something like this:

```
export DEBUG=true
export SECRET_KEY=asdf1234
export DATABASE_URI=postgres://username:password@localhost/faxrobot
export REDIS_URI=redis://127.0.0.1:6379?db=1
export REQUIRE_PAYMENTS=on
export AWS_STORAGE=off
export AWS_ACCESS_KEY=AKSPLGHLOL
export AWS_SECRET_KEY='trolol'
export AWS_S3_BUCKET='s3.faxrobot.io'
export FAXROBOT_DIR=/htdocs/faxrobot
export GLOBAL_SALT=omgtrolol
export STRIPE_SECRET_KEY=sk_test_12345678
export SERVEOFFICE2PDF_URL=http://convert.dev/convert
export MANDRILL_API_KEY=asdf
export EMAIL_FROM='support@faxrobot.io'
export EMAIL_FROM_NAME='Fax Robot'
export EMAIL_SUPPORT='support@faxrobot.io'
export EMAIL_FEEDBACK='human@faxrobot.io'
export FAXROBOT_URL='https://faxrobot.io'
```

Here are the specific environment variables, and what they do:

* **`DEBUG`**: Whether to run the API in debug mode. Useful for local testing.

* **`SECRET_KEY`**: Secret key used by Flask for sessions. It's probably not
  used for anything, but good practice to have it just in case.

* **`DATABASE_URI` (required)**: A PostgreSQL connection string to use for
  database access. Database tables are created automatically with SQLAlchemy, so
  you don't have to set the schema up manually.

* **`REDIS_URI` (required)**: A Redis connection string. Required for the
  [rq][1] worker to operate.

* **`REQUIRE_PAYMENTS`**: If set to "on" then API users will need to purchase
  credit via [Stripe][2] API endpoints in order to send faxes. This also means
  you will need a valid `STRIPE_SECRET_KEY` in the configuration.

* **`AWS_STORAGE`**: If set to "on" then temporary data for jobs will be
  uploaded to Amazon S3. This is only useful if you have more than one physical
  server running the Fax Robot worker process. Turning this on also means you'll
  have to set up the other `AWS_` prefixed configuration variables.

* **`AWS_ACCESS_KEY`**: Your Amazon AWS Access Key ID.

* **`AWS_SECRET_KEY`**: Your Amazon AWS Secret Key.

* **`AWS_S3_BUCKET`**: The Amazon S3 bucket to use for data storage.

* **`FAXROBOT_DIR` (required)**: The directory you have the Fax Robot project
  stored in.

* **`GLOBAL_SALT` (required)**: A global salt value used for hashing passwords
  and other secret values. This should be an arbitrary string (longer is better)

* **`STRIPE_SECRET_KEY`**: Only required if `REQUIRE_PAYMENTS` is turned on.
  This is your Stripe secret key used for processing payments.

* **`SERVEOFFICE2PDF_URL`**: ServeOffice2PDF is a separate web application that
  converts Microsoft Office file formats (like .doc and .docx) to PDF. This is
  optional, and only used to support faxing these formats via the Fax Robot API.
  By default Microsoft Office formats are unsupported by Fax Robot.

* **`MANDRILL_API_KEY`**: Used for sending transactional emails to Fax Robot API
  accounts. If not present, then emails are disabled.

* **`EMAIL_FROM`**: The from email address for transactional emails.

* **`EMAIL_FROM_NAME`**: The from email name for transactional emails.

* **`EMAIL_SUPPORT`**: A support email address to include in relevent
  transactional emails.

* **`EMAIL_FEEDBACK`**: A feedback email address to include in relevent
  transactional emails.

* **`FAXROBOT_URL`**: The URL to a front-end client webapp for your Fax Robot
  instance.

Once your environment variables are configured, load them into your shell using
the `source` command:

```
source .env
```

#### Running the Fax Robot API

The API listens for incoming fax jobs (and other CRUD type API requests) and
pushes faxes onto the worker's queue. To start it, you'll simply run
`python api.py` after following the steps above. To recap:

```
source venv/bin/activate
source .env
python api.py
```

When running in Debug mode, the API will listen on `localhost:9001`.

#### Running the Worker

The worker listens for fax jobs on the [rq][1] queue and processes them.
After loading your environment up, you'll run `python worker.py` with your
faxmodem device specified as an argument. For example:

```
source venv/bin/activate
source .env
python worker.py --device /dev/ttyUSB0
```

**NOTE:** The device for your faxmodem must be accessible by the user account
you're running the `worker.py` process under.

If you have more than one faxmodem hooked up, you can run multiple instances of
`worker.py` for maximum pwnage.

API Documentation
-----------------
Read the full API documentation at https://faxrobot.io/api

[1]: http://python-rq.org/
[2]: https://stripe.com
[3]: https://www.gnu.org/copyleft/gpl.html
[4]: http://aws.amazon.com/s3/
[5]: http://mandrill.com
[6]: https://virtualenv.pypa.io/en/latest/
[7]: https://github.com/lyonbros/faxrobot-www
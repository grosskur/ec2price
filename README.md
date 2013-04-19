# EC2 Price Tracker

This application collects and displays prices for EC2 spot instances
over time. It's written in [Python](http://www.python.org/) using the
[Tornado](http://www.tornadoweb.org/) web framework. A periodic task
(`ec2price collector`) grabs spot price data from the EC2 API using
[botocore](https://github.com/boto/botocore) and stores it in a
[postgres](http://www.postgresql.org/) database. The web interface
(`ec2price web`) displays graphs of the data using
[nvd3](http://nvd3.org/).

## Instructions

```bash
$ git clone https://github.com/grosskur/ec2price.git
$ cd ec2price
$ heroku create your-ec2price
$ heroku addons:add heroku-postgresql:dev
$ heroku pg:promote $(heroku config -s | awk -F= '$1 ~ /^HEROKU_POSTGRESQL_[A-Z]+_URL$/ {print $1}')
$ heroku config set SECRET_KEY=$(python -c "import base64, uuid; print base64.b64encode(uuid.uuid4().bytes + uuid.uuid4().bytes)")
$ heroku config set AWS_ACCESS_KEY_ID=... AWS_SECRET_ACCESS_KEY=...
$ heroku run psql -f ec2price/sql/schema.sql
$ heroku run psql -f ec2price/sql/initial.sql
$ git push heroku master
```

## To do

* Experiment with Rickshaw for graph drawing
 * Use D3 option `interpolation: 'step-after'` for staircase lines

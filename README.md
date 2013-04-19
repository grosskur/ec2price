# EC2 Price Tracker

This application collects and displays prices for EC2 spot instances
over time. It's written in [Python](http://www.python.org/) using the
[Tornado](http://www.tornadoweb.org/) web framework. A periodic task
`ec2price collector` grabs spot price data from the EC2 API using
[botocore](https://github.com/boto/botocore) and stores it in a
[Postgres](http://www.postgresql.org/) database. The web interface
`ec2price web` displays graphs of the data using
[NVD3.js](http://nvd3.org/).

## Instructions for running on Heroku

```bash
$ git clone https://github.com/grosskur/ec2price.git
$ cd ec2price
$ heroku create your-ec2price
$ heroku addons:add heroku-postgresql:dev
$ heroku pg:promote $(heroku config -s | awk -F= '$1 ~ /^HEROKU_POSTGRESQL_[A-Z]+_URL$/ {print $1}')
$ heroku config:set COOKIE_SECRET=$(python -c "import base64, uuid; print base64.b64encode(uuid.uuid4().bytes + uuid.uuid4().bytes)")
$ heroku config:set AWS_ACCESS_KEY_ID=...
$ heroku config:set AWS_SECRET_ACCESS_KEY=...
$ heroku pg:psql < ec2price/sql/schema.sql
$ heroku pg:psql < ec2price/sql/initial.sql
$ git push heroku master
$ heroku run env HOURS=24 scripts/ec2price collector
$ heroku addons:add scheduler:standard
```

Then go to the Heroku dashboard and add a scheduled job to run
`scripts/ec2price collector` every 10 minutes.

## To do

* Experiment with Rickshaw for graph drawing
 * Use D3 option `interpolation: 'step-after'` for staircase lines

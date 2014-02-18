# EC2 Price Tracker

This application collects and displays prices for EC2 spot instances
over time. It's written in [Python](http://www.python.org/) using the
[Tornado](http://www.tornadoweb.org/) web framework.

* The daemon `ec2price collector` grabs spot price data from the EC2
  API using [botocore](https://github.com/boto/botocore) and stores it
  in [DynamoDB](http://aws.amazon.com/dynamodb/).

* The web interface `ec2price web` displays graphs of the data using
  [NVD3.js](http://nvd3.org/).

## Instructions for running on Heroku

```bash
$ git clone https://github.com/grosskur/ec2price.git
$ cd ec2price
$ heroku create your-ec2price
$ heroku config:set TABLE_PREFIX=$(uuidgen | cut -c 1-8 | tr 'A-Z' 'a-z')
$ heroku config:set COOKIE_SECRET=$(head /dev/urandom | base64 | cut -c 1-40)
$ heroku config:set AWS_ACCESS_KEY_ID=...
$ heroku config:set AWS_SECRET_ACCESS_KEY=...
$ git push heroku master
$ heroku ps:scale web=1
$ heroku addons:add scheduler
$ heroku addons:open scheduler  # Add hourly job to run "scripts/ec2price collector"
```

## To do

* Experiment with Rickshaw for graph drawing
 * Use D3 option `interpolation: 'step-after'` for staircase lines

## See also

* [cloud exchange](http://cloudexchange.org/)
* [EC2Instances.info](http://ec2instances.info/)

"""
App
"""
import argparse
import logging
import os
import re
import time

import tornado.ioloop
import tornado.web
import webassets.loaders

from .web import MainHandler, HealthCheckHandler
from .collector import collect
from .model import Model


PROG = 'ec2price'
TEMPLATE_PATH = os.path.join(os.path.dirname(__file__), 'templates')
STATIC_PATH = os.path.join(os.path.dirname(__file__), 'static')
DATABASE_URL_REGEX = re.compile(
    'postgres://'
    '(?P<user>.*)'
    ':(?P<password>.*)'
    '@(?P<host>[-a-z\d.]+)'
    ':(?P<port>\d+)'
    '/(?P<dbname>.+)'
)
_HOURS = 1
_COLLECTOR_SLEEP_TIME = 600


class ArgumentParser(argparse.ArgumentParser):
    def error(self, message):
        self.exit(2, '%s: error: %s\n' % (self.prog, message))


def main(args):
    # setup logging
    fmt = PROG + ': %(levelname)s%(message)s'
    logging.basicConfig(level=logging.DEBUG, format=fmt)
    logging.addLevelName(logging.DEBUG, 'debug: ')
    logging.addLevelName(logging.INFO, '')
    logging.addLevelName(logging.WARNING, 'warning: ')
    logging.addLevelName(logging.ERROR, 'error: ')
    logging.addLevelName(logging.CRITICAL, 'critical: ')

    # parse command line
    parser = ArgumentParser(
        prog=PROG,
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    subparsers = parser.add_subparsers(help='commands')

    p_web = subparsers.add_parser('web', help='web app')
    p_web.set_defaults(cmd='web')

    p_collector = subparsers.add_parser('collector', help='collector')
    p_collector.set_defaults(cmd='collector')
    p_collector.add_argument('--once', action='store_true',
                             help='run once instead of indefinitely')

    opts = parser.parse_args(args)

    if opts.cmd == 'web':
        debug = bool(_consume_env('DEBUG', False))
        port = int(_consume_env('PORT', 8080))
        address = _consume_env('ADDRESS', '')
        cookie_secret = _consume_env('COOKIE_SECRET')
        table_prefix = _consume_env('TABLE_PREFIX')
        gauges_site_id = _consume_env('GAUGES_SITE_ID')
        ga_tracking_id = _consume_env('GA_TRACKING_ID')
        ga_domain = _consume_env('GA_DOMAIN')
        google_site_verification_id = _consume_env(
            'GOOGLE_SITE_VERIFICATION_ID')
        static_host = _consume_env('STATIC_HOST')

        if not table_prefix:
            parser.error('TABLE_PREFIX is required')
        if not cookie_secret:
            parser.error('COOKIE_SECRET is required')

        asset_loader = webassets.loaders.YAMLLoader('webassets.yml')
        asset_env = asset_loader.load_environment()
        asset_env.debug = debug

        params = {
            'model': Model(table_prefix),
            'asset_env': asset_env,
            'gauges_site_id': gauges_site_id,
            'ga_tracking_id': ga_tracking_id,
            'ga_domain': ga_domain,
            'google_site_verification_id': google_site_verification_id,
            'static_host': static_host,
        }
        handlers = [
            (r'/', MainHandler, params),
            (r'/healthcheck', HealthCheckHandler, params),
        ]
        _start_tornado_app(debug, cookie_secret, port, address, handlers)
    elif opts.cmd == 'collector':
        table_prefix = _consume_env('TABLE_PREFIX')
        hours = _consume_env('HOURS', _HOURS)
        collector_sleep_time = _consume_env('COLLECTOR_SLEEP_TIME',
                                            _COLLECTOR_SLEEP_TIME)

        if not table_prefix:
            parser.error('TABLE_PREFIX is required')

        try:
            hours = int(hours)
        except ValueError:
            parser.error('HOURS must be an integer')

        try:
            collector_sleep_time = int(collector_sleep_time)
        except ValueError:
            parser.error('COLLECTOR_SLEEP_TIME must be an integer')

        model = Model(table_prefix)
        while True:
            collect(model, hours)
            if opts.once:
                break
            logging.debug('sleeping %d seconds', collector_sleep_time)
            time.sleep(collector_sleep_time)
    return 0


def _start_tornado_app(debug, cookie_secret, port, address, handlers):
    settings = dict(
        cookie_secret=cookie_secret,
        template_path=TEMPLATE_PATH,
        static_path=STATIC_PATH,
        xsrf_cookies=False,
        autoescape='xhtml_escape',
        debug=debug,
        gzip=not debug,
    )
    app = tornado.web.Application(handlers, **settings)
    logging.info('listening on port: %d', port)
    app.listen(port, address)
    tornado.ioloop.IOLoop.instance().start()


def _consume_env(name, default=None):
    value = os.getenv(name, default)
    os.unsetenv(name)
    if name in os.environ:
        del os.environ[name]
    return value

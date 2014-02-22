"""
App
"""
import argparse
import logging
import os
import re

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

    opts = parser.parse_args(args)

    if opts.cmd == 'web':
        debug = bool(os.getenv('DEBUG', False))
        port = int(os.getenv('PORT', 8080))
        address = os.getenv('ADDRESS', '')
        cookie_secret = os.getenv('COOKIE_SECRET')
        table_prefix = os.getenv('TABLE_PREFIX')
        gauges_site_id = os.getenv('GAUGES_SITE_ID')
        ga_tracking_id = os.getenv('GA_TRACKING_ID')
        ga_domain = os.getenv('GA_DOMAIN')
        google_site_verification_id = os.getenv('GOOGLE_SITE_VERIFICATION_ID')

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
        }
        handlers = [
            (r'/', MainHandler, params),
            (r'/healthcheck', HealthCheckHandler, params),
        ]
        _start_tornado_app(debug, cookie_secret, port, address, handlers)
    elif opts.cmd == 'collector':
        table_prefix = os.getenv('TABLE_PREFIX')
        hours = os.getenv('HOURS')

        if not table_prefix:
            parser.error('TABLE_PREFIX is required')

        if not hours:
            hours = _HOURS
        try:
            hours = int(hours)
        except ValueError:
            parser.error('HOURS must be an integer')

        model = Model(table_prefix)
        collect(model, hours)
    return 0


def _start_tornado_app(debug, cookie_secret, port, address, handlers):
    settings = dict(
        cookie_secret=cookie_secret,
        template_path=TEMPLATE_PATH,
        static_path=STATIC_PATH,
        xsrf_cookies=False,
        autoescape='xhtml_escape',
        debug=debug,
    )
    app = tornado.web.Application(handlers, **settings)
    logging.info('listening on port: %d', port)
    app.listen(port, address)
    tornado.ioloop.IOLoop.instance().start()

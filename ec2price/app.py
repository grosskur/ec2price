"""
App
"""
import argparse
import logging
import os
import re

import psycopg2
import psycopg2.extras
import tornado.ioloop
import tornado.web

from .web import MainHandler
from .collector import collect


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
DATABASE_URL_EXAMPLE = 'postgres://username:password@host:port/dbname'
_HOURS = 8


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

    p_api = subparsers.add_parser('api', help='web API')
    p_api.set_defaults(cmd='api')

    p_collector = subparsers.add_parser('collector', help='collector')
    p_collector.set_defaults(cmd='collector')

    opts = parser.parse_args(args)

    if opts.cmd == 'web':
        debug = bool(os.getenv('DEBUG', False))
        port = int(os.getenv('PORT', 8080))
        address = os.getenv('ADDRESS', '')
        cookie_secret = os.getenv('COOKIE_SECRET')
        database_url = os.getenv('DATABASE_URL')

        database_dsn = None
        if database_url:
            m = DATABASE_URL_REGEX.match(database_url)
            if not m:
                parser.error('must be of form %s' % DATABASE_URL_EXAMPLE)
            database_dsn = ' '.join('%s=%s' % (k, v)
                                    for k, v in m.groupdict().items())

        if not database_url:
            parser.error('DATABASE_URL is required')
        if not cookie_secret:
            parser.error('COOKIE_SECRET is required')

        db_conn = _get_db_conn(database_dsn)

        params = {'db_conn': db_conn}
        handlers = [
            (r'/', MainHandler, params),
        ]
        _start_tornado_app(debug, cookie_secret, port, address, handlers)
    elif opts.cmd == 'api':
        debug = bool(os.getenv('DEBUG', False))
        port = int(os.getenv('PORT', 8080))
        address = os.getenv('ADDRESS', '')
        cookie_secret = os.getenv('COOKIE_SECRET')
        database_url = os.getenv('DATABASE_URL')

        database_dsn = None
        if database_url:
            m = DATABASE_URL_REGEX.match(database_url)
            if not m:
                parser.error('must be of form %s' % DATABASE_URL_EXAMPLE)
            database_dsn = ' '.join('%s=%s' % (k, v)
                                    for k, v in m.groupdict().items())

        if not database_url:
            parser.error('DATABASE_URL is required')
        if not cookie_secret:
            parser.error('COOKIE_SECRET is required')

        db_conn = _get_db_conn(database_dsn)

        params = {'db_conn': db_conn}
        handlers = [
            (r'/', MainHandler, params),
        ]
        _start_tornado_app(debug, cookie_secret, port, address, handlers)
    elif opts.cmd == 'collector':
        database_url = os.getenv('DATABASE_URL')
        hours = os.getenv('HOURS')

        database_dsn = None
        if database_url:
            m = DATABASE_URL_REGEX.match(database_url)
            if not m:
                parser.error('must be of form %s' % DATABASE_URL_EXAMPLE)
            database_dsn = ' '.join('%s=%s' % (k, v)
                                    for k, v in m.groupdict().items())

        if not database_url:
            parser.error('DATABASE_URL is required')

        if not hours:
            hours = _HOURS
        try:
            hours = int(hours)
        except ValueError:
            parser.error('HOURS must be an integer')

        db_conn = _get_db_conn(database_dsn)

        collect(db_conn, hours)
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


def _get_db_conn(database_dsn):
    psycopg2.extras.register_uuid()
    return psycopg2.connect(
        database_dsn,
        connection_factory=psycopg2.extras.RealDictConnection,
    )

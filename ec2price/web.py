"""
Web handlers
"""
import logging

import arrow
import tornado.web


_FMT = 'YYYY-MM-DDTHH:mm:ssZ'


logging.getLogger('boto').setLevel(logging.CRITICAL)


class BaseHandler(tornado.web.RequestHandler):
    def initialize(self, model, asset_env, gauges_site_id, ga_tracking_id,
                   ga_domain, google_verification_id):
        self._model = model
        self._asset_env = asset_env
        self._gauges_site_id = gauges_site_id
        self._ga_tracking_id = ga_tracking_id
        self._ga_domain = ga_domain
        self._google_verification_id = google_verification_id


class GoogleVerificationHandler(BaseHandler):
    def get(self):
        self.write('google-site-verification: google{}.html'.format(
            self._google_verification_id))


class HealthCheckHandler(BaseHandler):
    def get(self):
        self.write('OK')


class MainHandler(BaseHandler):
    def get(self):
        product_description = self.get_argument('product', 'Linux/UNIX')
        instance_type = self.get_argument('type', 't1.micro')
        region = self.get_argument('region', 'us-east-1')
        window = int(self.get_argument('window', 3))

        logging.debug('window: past %s days', window)
        timestamp = arrow.utcnow().replace(days=-window).timestamp
        logging.debug('timestamp: %s', timestamp)

        rows = self._model.instance_zones.query(
            instance_id__eq=':'.join([
                product_description,
                instance_type,
            ]),
            zone__beginswith=region,
        )
        zones = [str(row['zone']) for row in rows]

        data = {}
        for zone in zones:
            rows = self._model.spot_prices.query(
                instance_zone_id__eq=':'.join([
                    product_description,
                    instance_type,
                    zone,
                ]),
                timestamp__gte=timestamp,
            )
            data[zone] = []
            for row in rows:
                data[zone].append([
                    arrow.get(row['timestamp']).format(_FMT),
                    float(row['price']),
                ])

        rows = self._model.instance_types.scan()
        instance_types = sorted([row['instance_type'] for row in rows])

        rows = self._model.regions.scan()
        regions = sorted([row['region'] for row in rows])

        rows = self._model.product_descriptions.scan()
        product_descriptions = sorted([row['product_description']
                                       for row in rows])

        windows = [1, 3, 8, 15, 30, 60]

        self.render('main.html',
                    asset_env=self._asset_env,
                    gauges_site_id=self._gauges_site_id,
                    ga_tracking_id=self._ga_tracking_id,
                    ga_domain=self._ga_domain,
                    data=data,
                    product_description=product_description,
                    product_descriptions=product_descriptions,
                    instance_type=instance_type,
                    instance_types=instance_types,
                    region=region,
                    regions=regions,
                    window=window,
                    windows=windows)

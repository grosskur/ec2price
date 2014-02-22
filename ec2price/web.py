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
                   ga_domain, google_site_verification_id, static_host):
        self._model = model
        self._asset_env = asset_env
        self._gauges_site_id = gauges_site_id
        self._ga_tracking_id = ga_tracking_id
        self._ga_domain = ga_domain
        self._google_site_verification_id = google_site_verification_id
        self.static_host = static_host

    def static_url(self, path, include_host=None, **kwargs):
        self.require_setting('static_path', 'static_url')
        get_url = self.settings.get(
            'static_handler_class',
            tornado.web.StaticFileHandler,
        ).make_static_url

        if include_host is None:
            include_host = getattr(self, 'include_host', False)

        static_host = getattr(self, 'static_host', None)

        if static_host:
            base = self.request.protocol + "://" + static_host
        elif include_host:
            base = self.request.protocol + "://" + self.request.host
        else:
            base = ""

        return base + get_url(self.settings, path, **kwargs)


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

        self.render(
            'main.html',
            asset_env=self._asset_env,
            gauges_site_id=self._gauges_site_id,
            ga_tracking_id=self._ga_tracking_id,
            ga_domain=self._ga_domain,
            google_site_verification_id=self._google_site_verification_id,
            data=data,
            product_description=product_description,
            product_descriptions=product_descriptions,
            instance_type=instance_type,
            instance_types=instance_types,
            region=region,
            regions=regions,
            window=window,
            windows=windows,
        )

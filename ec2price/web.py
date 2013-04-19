"""
Web handlers
"""
import contextlib

import tornado.web


_FMT = '%Y-%m-%dT%H:%M:%SZ'
_SELECT_PRICES = """
select spot_prices.price, spot_prices.ts, availability_zones.api_name
from spot_prices, availability_zones, instance_types
where spot_prices.availability_zone_id = availability_zones.id
  and availability_zones.api_name like %s
  and spot_prices.instance_type_id = instance_types.id
  and instance_types.api_name = %s
  and spot_prices.ts > now() - interval %s
order by ts;
"""
_SELECT_INSTANCE_TYPES = """
select api_name
from instance_types
order by api_name
"""
_SELECT_AVAILABILITY_ZONES = """
select api_name
from availability_zones
order by api_name
"""


class BaseHandler(tornado.web.RequestHandler):
    def initialize(self, db_conn, gauges_site_id):
        self._conn = db_conn
        self._gauges_site_id = gauges_site_id


class MainHandler(BaseHandler):
    def get(self):
        instance_type = self.get_argument('type', 't1.micro')
        region = self.get_argument('region', 'us-east-1')
        window = int(self.get_argument('window', 3))

        with contextlib.closing(self._conn.cursor()) as cursor:
            cursor.execute(_SELECT_PRICES, [region + '%', instance_type,
                                            '{} days'.format(window)])
            rows = cursor.fetchall()

        data = {}
        for row in rows:
            api_name = row['api_name']
            if api_name not in data:
                data[api_name] = []
            data[api_name].append([
                row['ts'].strftime(_FMT),
                float(row['price']),
            ])

        with contextlib.closing(self._conn.cursor()) as cursor:
            cursor.execute(_SELECT_INSTANCE_TYPES)
            rows = cursor.fetchall()
        instance_types = [r['api_name'] for r in rows]

        with contextlib.closing(self._conn.cursor()) as cursor:
            cursor.execute(_SELECT_AVAILABILITY_ZONES)
            rows = cursor.fetchall()
        availability_zones = [r['api_name'] for r in rows]
        regions = sorted(list(set([i[:-1] for i in availability_zones])))
        windows = [1, 3, 8, 15, 30, 60]

        self.render('main.html',
                    gauges_site_id=self._gauges_site_id,
                    data=data,
                    instance_type=instance_type,
                    instance_types=instance_types,
                    availability_zones=availability_zones,
                    region=region,
                    regions=regions,
                    window=window,
                    windows=windows)

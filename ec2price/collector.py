"""
Data collector
"""
import botocore.session

import contextlib
import datetime
import logging
import uuid


_HOURS = 8
_FMT = '%Y-%m-%dT%H:%M:%S.000Z'

_SELECT_SPOT_PRICE = """
select price
from spot_prices, availability_zones, instance_types
where spot_prices.availability_zone_id = availability_zones.id
  and availability_zones.api_name = %s
  and spot_prices.instance_type_id = instance_types.id
  and instance_types.api_name = %s
  and spot_prices.ts = %s
limit 1
"""
_INSERT_SPOT_PRICE = """
with a as (select id from availability_zones where api_name = %s),
     i as (select id from instance_types where api_name = %s)
insert into spot_prices (id, availability_zone_id, instance_type_id, ts, price)
select %s, a.id, i.id, %s, %s
from a, i
"""
_SELECT_INSTANCE_TYPES = """
select api_name
from instance_types
order by api_name
"""

logging.getLogger('botocore').setLevel(logging.WARN)
logging.getLogger('requests.packages.urllib3').setLevel(logging.WARN)


def collect(db_conn):
    session = botocore.session.get_session()
    ec2 = session.get_service('ec2')
    operation = ec2.get_operation('DescribeSpotPriceHistory')

    d = datetime.datetime.utcnow() - datetime.timedelta(hours=_HOURS)
    start_time = d.strftime(_FMT)

    with contextlib.closing(db_conn.cursor()) as cursor:
        cursor.execute(_SELECT_INSTANCE_TYPES)
        rows = cursor.fetchall()
    instance_types = [r['api_name'] for r in rows]

    for region in ec2.region_names:
        logging.debug('collecting spot prices from region: %s', region)
        endpoint = ec2.get_endpoint(region)
        response, data = operation.call(
            endpoint,
            instance_types=instance_types,
            product_descriptions=['Linux/UNIX'],
            start_time=start_time,
        )
        for i in data.get('spotPriceHistorySet', []):
            with contextlib.closing(db_conn.cursor()) as cursor:
                cursor.execute(_SELECT_SPOT_PRICE, [
                    i['availabilityZone'],
                    i['instanceType'],
                    i['timestamp'],
                ])
                row = cursor.fetchone()
                if not row:
                    logging.debug('inserting spot price: %s', i)
                    cursor.execute(_INSERT_SPOT_PRICE, [
                        i['availabilityZone'],
                        i['instanceType'],
                        uuid.uuid4(),
                        i['timestamp'],
                        i['spotPrice'],
                    ])
                    db_conn.commit()

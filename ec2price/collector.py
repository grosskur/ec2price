"""
Data collector
"""
import decimal
import logging

import arrow
import botocore.session


_EXCLUDED_REGION_PREFIXES = ['cn-', 'us-gov-']
_FMT = 'YYYY-MM-DDTHH:mm:ss.000Z'


logging.getLogger('boto').setLevel(logging.WARN)
logging.getLogger('botocore').setLevel(logging.WARN)
logging.getLogger('requests.packages.urllib3').setLevel(logging.WARN)


def collect(model, hours):
    row = model.progress.get_item(name='end_time')
    if row['timestamp'] is None:
        logging.debug('using initial window of -%d hours', hours)
        start_time = arrow.utcnow().replace(hours=-hours)
    else:
        start_time = arrow.get(row['timestamp'])
    logging.debug('start time: %s', start_time)

    end_time = arrow.utcnow()
    logging.debug('end time: %s', end_time)

    all_regions = set()
    all_product_descriptions = set()
    all_instance_types = set()
    all_instance_zones = set()

    session = botocore.session.get_session()
    ec2 = session.get_service('ec2')
    operation = ec2.get_operation('DescribeSpotPriceHistory')

    for region in ec2.region_names:
        if any(region.startswith(x) for x in _EXCLUDED_REGION_PREFIXES):
            continue
        all_regions.add(region)

        next_token = None
        while True:
            logging.debug('collecting spot prices from region: %s', region)
            endpoint = ec2.get_endpoint(region)
            if next_token:
                response, data = operation.call(
                    endpoint,
                    start_time=start_time.format(_FMT),
                    end_time=end_time.format(_FMT),
                    next_token=next_token,
                )
            else:
                response, data = operation.call(
                    endpoint,
                    start_time=start_time.format(_FMT),
                )
            next_token = data.get('NextToken')
            logging.debug('next_token: %s', next_token)
            spot_data = data.get('SpotPriceHistory', [])

            #conn = boto.ec2.connect_to_region(r.name)
            #logging.debug('getting spot prices for region: %s', r.name)
            #data = conn.get_spot_price_history(start_time=start_time)

            logging.debug('saving %d spot prices for region: %s',
                          len(spot_data), region)
            with model.spot_prices.batch_write() as batch:
                for d in spot_data:
                    all_product_descriptions.add(d['ProductDescription'])
                    all_instance_types.add(d['InstanceType'])
                    all_instance_zones.add((
                        d['ProductDescription'],
                        d['InstanceType'],
                        d['AvailabilityZone'],
                    ))
                    batch.put_item(data={
                        'instance_zone_id': ':'.join([
                            d['ProductDescription'],
                            d['InstanceType'],
                            d['AvailabilityZone'],
                        ]),
                        'timestamp': arrow.get(d['Timestamp']).timestamp,
                        'price': decimal.Decimal(str(d['SpotPrice'])),
                    })
            if not next_token:
                break

    logging.debug('saving %d regions', len(all_regions))
    with model.regions.batch_write() as batch:
        for i in all_regions:
            batch.put_item(data={'region': i})

    logging.debug('saving %d product_descriptions',
                  len(all_product_descriptions))
    with model.product_descriptions.batch_write() as batch:
        for i in all_product_descriptions:
            batch.put_item(data={'product_description': i})

    logging.debug('saving %d instance_types', len(all_instance_types))
    with model.instance_types.batch_write() as batch:
        for i in all_instance_types:
            batch.put_item(data={'instance_type': i})

    logging.debug('saving %d instance_zones', len(all_instance_zones))
    with model.instance_zones.batch_write() as batch:
        for i in all_instance_zones:
            batch.put_item(data={
                'instance_id': ':'.join([i[0], i[1]]),
                'zone': i[2],
            })

    logging.debug('saving end_time')
    with model.progress.batch_write() as batch:
        batch.put_item(data={
            'name': 'end_time',
            'timestamp': end_time.timestamp,
        })

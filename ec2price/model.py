"""
Model
"""
import logging

from boto.exception import JSONResponseError
from boto.dynamodb2.fields import HashKey, RangeKey
from boto.dynamodb2.table import Table
from boto.dynamodb2.types import NUMBER


class Model(object):
    def __init__(self, table_prefix):
        self.spot_prices = _create_table(
            '_'.join([table_prefix, 'spot_price']),
            schema=[
                HashKey('instance_zone_id'),
                RangeKey('timestamp', data_type=NUMBER),
            ],
            throughput={'read': 5, 'write': 5},
        )
        self.instance_zones = _create_table(
            '_'.join([table_prefix, 'instance_zone']),
            schema=[
                HashKey('instance_id'),
                RangeKey('zone'),
            ],
            throughput={'read': 1, 'write': 1},
        )
        self.regions = _create_table(
            '_'.join([table_prefix, 'region']),
            schema=[
                HashKey('region'),
            ],
            throughput={'read': 1, 'write': 1},
        )
        self.product_descriptions = _create_table(
            '_'.join([table_prefix, 'product_description']),
            schema=[
                HashKey('product_description'),
            ],
            throughput={'read': 1, 'write': 1},
        )
        self.instance_types = _create_table(
            '_'.join([table_prefix, 'instance_type']),
            schema=[
                HashKey('instance_type'),
            ],
            throughput={'read': 1, 'write': 1},
        )
        self.progress = _create_table(
            '_'.join([table_prefix, 'progress']),
            schema=[
                HashKey('name'),
            ],
            throughput={'read': 1, 'write': 1},
        )


def _create_table(table_name, schema, throughput):
    if _table_exists(table_name):
        logging.debug('using existing table: %s', table_name)
        return Table(table_name, schema=schema)
    else:
        logging.debug('creating table: %s', table_name)
        return Table.create(table_name, schema=schema, throughput=throughput)


def _table_exists(table_name):
    table = Table(table_name)
    try:
        table.describe()
    except JSONResponseError as exc:
        if exc.error_code == 'ResourceNotFoundException':
            return False
    return True

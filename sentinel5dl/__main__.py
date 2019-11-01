# -*- coding: utf-8 -*-
'''
Sentinel-5p Downloader
~~~~~~~~~~~~~~~~~~~~~~

:copyright: 2019, The Emissions API Developers
:url: https://emissions-api.org
:license: MIT
'''
import argparse
import iso8601
import logging
import textwrap

import sentinel5dl
from sentinel5dl import search, download

PRODUCTS = (
    'L1B_IR_SIR',
    'L1B_IR_UVN',
    'L1B_RA_BD1',
    'L1B_RA_BD2',
    'L1B_RA_BD3',
    'L1B_RA_BD4',
    'L1B_RA_BD5',
    'L1B_RA_BD6',
    'L1B_RA_BD7',
    'L1B_RA_BD8',
    'L2__AER_AI',
    'L2__AER_LH',
    'L2__CH4___',
    'L2__CLOUD_',
    'L2__CO___',
    'L2__HCHO__',
    'L2__NO2__',
    'L2__NP_BD3',
    'L2__NP_BD6',
    'L2__NP_BD7',
    'L2__O3_TCL',
    'L2__O3___',
    'L2__SO2__',
)

PRODUCTS_STR = textwrap.fill(', '.join(PRODUCTS),
                             subsequent_indent='  ',
                             initial_indent='  ')

PROCESSING_LEVELS = (
    'L1B',
    'L2'
)


def is_polygon(polygon):
    '''Validate if the supplied polygon string is in the necessary format to be
    used as part of a WKT polygon string.

    :param polygon: Polygon string in the form of lon1 lat1, lon2 lat2, ...
    :return: WKT polygon
    '''
    values = [value.strip() for value in polygon.split(',')]

    # Polygon must be at least a triangle
    if len(values) < 4:
        raise ValueError('Polygon must be at least a triangle')

    # Check if we got float pairs
    for value in values:
        if len([float(x) for x in value.split()]) != 2:
            raise ValueError('Polygon values must be pairs of numbers')

    # Check if we got a closed polygon
    if values[0] != values[-1]:
        raise ValueError('Polygon is not closed')

    return f'POLYGON(({polygon}))'


def validate_date_string(date_string):
    '''Validate that the supplied argument is a valid iso8601 date-time string.

    :param date_string: Date string to validate
    :return: Supplied date string
    '''
    try:
        iso8601.parse_date(date_string)
    except iso8601.iso8601.ParseError:
        raise ValueError('Unable to parse date')
    return date_string


def main():
    # Confgure logging in the library
    logging.basicConfig()
    logger = logging.getLogger(sentinel5dl.__name__)
    logger.setLevel(logging.INFO)

    parser = argparse.ArgumentParser(
        description='Search for and download Sentinel-5P data files',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=f'AVAILABLE PRODUCTS\n{PRODUCTS_STR}'
    )

    # type= can use a callable, use that for most of this
    parser.add_argument(
        '--polygon',
        type=is_polygon,
        default='7.88 49.34,13.45 49.34,13.45 52.87,7.88 52.87,7.88 49.34',
        help='''Polygon defining an area by a set of coordinates.
            Example: 30.1 10.0, 40.0 40.1, 20 40, 10 20, 30.1 10.0'''
    )

    parser.add_argument(
        '--product',
        choices=PRODUCTS,
        metavar='PRODUCT',
        default='L2__CO____',
        help='Type of product to search for'
    )

    parser.add_argument(
        '--level',
        choices=PROCESSING_LEVELS,
        default='L2',
        help='Data processing level'
    )

    parser.add_argument(
        '--begin_ts',
        default='2019-09-01T00:00:00.000Z',
        type=validate_date_string,
        help='''ISO-8601 timestamp specifying the earliest sensing date.
            Example: 2019-09-01T00:00:00.000Z'''
    )

    parser.add_argument(
        '--end_ts',
        default='2019-09-17T23:59:59.999Z',
        type=validate_date_string,
        help='''ISO-8601 timestamp specifying the latest sensing date.
            Example: 2019-09-17T23:59:59.999Z'''
    )

    args = parser.parse_args()

    result = search(
        polygon=args.polygon,
        begin_ts=args.begin_ts,
        end_ts=args.end_ts,
        product=args.product,
        processing_level=args.level
    )

    # Download found products to the local folder
    download(result.get('products'))


if __name__ == '__main__':
    main()

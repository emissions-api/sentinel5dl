# -*- coding: utf-8 -*-
'''
Sentinel-5p Downloader
~~~~~~~~~~~~~~~~~~~~~~

:copyright: 2019, The Emissions API Developers
:url: https://emissions-api.org
:license: MIT
'''

import argparse
import dateutil.parser
import certifi
import logging
import multiprocessing
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
    'L2__CO____',
    'L2__HCHO__',
    'L2__NO2___',
    'L2__NP_BD3',
    'L2__NP_BD6',
    'L2__NP_BD7',
    'L2__O3_TCL',
    'L2__O3____',
    'L2__SO2___',
)

PRODUCTS_STR = textwrap.fill(', '.join(PRODUCTS),
                             subsequent_indent='  ',
                             initial_indent='  ')

PROCESSING_LEVELS = (
    'L1B',
    'L2'
)

PROCESSING_MODES = (
    'Offline',
    'Near real time',
    'Reprocessing'
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


def main():
    # Configure logging in the library
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
        '--mode',
        choices=PROCESSING_MODES,
        help='Data processing mode'
    )

    parser.add_argument(
        '--begin-ts',
        default='2019-09-01T00:00:00.000Z',
        type=dateutil.parser.parse,
        help='''Timestamp specifying the earliest sensing date.
            Example: 2019-09-01T00:00:00.000Z'''
    )

    parser.add_argument(
        '--end-ts',
        default='2019-09-17T23:59:59.999Z',
        type=dateutil.parser.parse,
        help='''Timestamp specifying the latest sensing date.
            Example: 2019-09-17T23:59:59.999Z'''
    )

    parser.add_argument(
        '--use-certifi',
        action='store_true',
        help='''If a Certificate Authority (CA) bundle is not already supplied
            by your operating system, certifi provides an easy way of
            providing a cabundle.'''
    )

    parser.add_argument(
        '--worker',
        type=int,
        default=1,
        help='Number of parallel downloads',
    )

    parser.add_argument(
        'download_dir',
        metavar='download-dir',
        help='Download directory'
    )

    args = parser.parse_args()

    # Provide a Certificate Authority (CA) bundle
    if args.use_certifi:
        sentinel5dl.ca_info = certifi.where()

    # Search for Sentinel-5 products
    result = search(
        polygon=args.polygon,
        begin_ts=args.begin_ts,
        end_ts=args.end_ts,
        product=args.product,
        processing_level=args.level,
        processing_mode=args.mode
    )

    # Download found products to the download directory with number of workers
    with multiprocessing.Pool(args.worker) as p:
        p.starmap(download, map(
            lambda product: ((product,), args.download_dir),
            result.get('products')))


if __name__ == '__main__':
    main()

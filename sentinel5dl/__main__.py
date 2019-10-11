# -*- coding: utf-8 -*-
'''
Sentinel-5p Downloader
~~~~~~~~~~~~~~~~~~~~~~

:copyright: 2019, The Emissions API Developers
:url: https://emissions-api.org
:license: MIT
'''

import logging

import sentinel5dl
from sentinel5dl import search, download


def main():
    # Confgure logging in the library
    logging.basicConfig()
    logger = logging.getLogger(sentinel5dl.__name__)
    logger.setLevel(logging.INFO)

    # Search for Sentinel-5 products
    result = search(
            polygon='POLYGON((7.88574278354645 49.347193400927495,'
                    '13.452152609825136 49.347193400927495,'
                    '13.452152609825136 52.870418902802214,'
                    '7.88574278354645 52.870418902802214,'
                    '7.88574278354645 49.347193400927495))',
            begin_ts='2019-09-01T00:00:00.000Z',
            end_ts='2019-09-17T23:59:59.999Z',
            product='L2__CO____',
            processing_level='L2')

    # Download found products to the local folder
    download(result.get('products'))


if __name__ == '__main__':
    main()

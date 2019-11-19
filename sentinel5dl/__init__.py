# -*- coding: utf-8 -*-
# Copyright 2019, The Emissions API Developers
# https://emissions-api.org
# This software is available under the terms of an MIT license.
# See LICENSE fore more information.
'''Sentinel-5P Downloader
'''

import hashlib
import io
import json
import os.path
import pycurl
import urllib.parse
import logging

# Data publicly provided by ESA:
API = 'https://s5phub.copernicus.eu/dhus/'
USER = 's5pguest'
PASS = 's5pguest'

logger = logging.getLogger(__name__)
'''Logger used by ``sentinel5dl``. Use this to specifically modify the
libraries log level like this::

    sentinel5dl.logger.setLevel(logging.DEBUG)
'''

ca_info = None
'''Path to Certificate Authority (CA) bundle. If this is set,
the value is passed to CURLOPT_CAINFO. If not set,
this option is by default set to the system path
where libcurl's cacert bundle is assumed to be stored,
as established at build time. If this is not already supplied
by your operating system, certifi provides an easy way of
providing a cabundle.
'''


def __md5(filename):
    '''Generate the md5 sum of a file

    :param filename: input filename for which the md5 sum is generated.
    :type filename: str
    :returns: hex representation of the md5 sum with uppercase characters.
    :rtype: str
    '''
    hash_md5 = hashlib.md5()
    with open(filename, 'rb') as f:
        for chunk in iter(lambda: f.read(4096), b''):
            hash_md5.update(chunk)
    return hash_md5.hexdigest().upper()


def __check_md5(filename, base_path):
    '''Check the md5 sum of a given file against the ESA API.

    :param filename: Path of local file to check
    :param base_path: Base API path to for this product
    :returns: If the local file matches the md5 checksum
    :rtype: bool
    '''
    md5file = f'{filename}.md5sum'
    try:
        with open(md5file, 'r') as f:
            md5sum = f.read()
    except FileNotFoundError:
        md5sum = __http_request(f'{base_path}/Checksum/Value/$value')
        md5sum = md5sum.decode('ascii')
        with open(md5file, 'w') as f:
            f.write(md5sum)

    # Compare md5 sum
    return __md5(filename) == md5sum


def __http_request(path, filename=None):
    '''Make an HTTP request to the API via HTTP, optionally downloading the
    response.

    :param path: Request path relative to the base API.
    :param filename: Optional output file name. Note that this file will be
                     overwritten if it already exists. If no filename is
                     provided, the response will be returned.
    :returns: The response body or None if a filename is provided.
    '''

    url = API + path.lstrip('/')
    logger.debug(f'Requesting {url}')
    with open(filename, 'wb') if filename else io.BytesIO() as f:
        curl = pycurl.Curl()
        curl.setopt(curl.URL, url.encode('ascii', 'ignore'))

        curl.setopt(curl.USERPWD, f'{USER}:{PASS}')
        curl.setopt(curl.WRITEDATA, f)
        curl.setopt(curl.FAILONERROR, True)

        if ca_info:
            curl.setopt(pycurl.CAINFO, ca_info)

        curl.perform()
        curl.close()
        if not filename:
            return f.getvalue()


def _search(polygon, begin_ts, end_ts, product, processing_level, offset,
            limit):
    '''Make a single search request for products to the API.

    :param polygon: WKT polygon specifying an area the data should intersect
    :param begin_ts: ISO-8601 timestamp specifying the earliest sensing date
    :param end_ts: ISO-8601 timestamp specifying the latest sensing date
    :param product: Type of product to request
    :param processing_level: Data processing level (`L1B` or `L2`)
    :param offset: Offset for the results to return
    :param limit: Limit number of results
    :returns: Dictionary containing information about found products
    '''
    filter_query = ['platformname:Sentinel-5']
    if polygon:
        filter_query.append(f'footprint:"Intersects({polygon})"')
    if begin_ts:
        filter_query.append(f'beginPosition:[{begin_ts} TO {end_ts}]')
    if end_ts:
        filter_query.append(f'endPosition:[{begin_ts} TO {end_ts}]',)
    if product:
        filter_query.append(f'producttype:{product}')
    if processing_level:
        filter_query.append(f'processinglevel:{processing_level}')
    filter_query = ' AND '.join(filter_query)
    query = {'filter': filter_query, 'offset': offset, 'limit': limit,
             'sortedby': 'ingestiondate', 'order': 'desc'}
    query = urllib.parse.urlencode(query, safe='():,\\[]',
                                   quote_via=urllib.parse.quote)
    path = '/api/stub/products?' + query
    body = __http_request(path)
    return json.loads(body.decode('utf8'))


def search(polygon=None, begin_ts=None, end_ts=None, product=None,
           processing_level='L2', per_request_limit=25):
    '''Search for products via API.

    :param polygon: WKT polygon specifying an area the data should intersect
    :param begin_ts: ISO-8601 timestamp specifying the earliest sensing date
    :param end_ts: ISO-8601 timestamp specifying the latest sensing date
    :param product: Type of product to request
    :param processing_level: Data processing level (`L1B` or `L2`)
    :param per_request_limit: Limit number of results per request
    :returns: Dictionary containing information about found products
    '''

    count = 0
    total = 1
    data = None
    logger.info('Searching for Sentinel-5 products')
    while count < total:
        s = _search(polygon, begin_ts, end_ts, product, processing_level,
                    count, per_request_limit)
        total = s.get('totalresults', 0)
        if data:
            data['products'].extend(s['products'])
            data['totalresults'] = total
        else:
            data = s
        count = len(data['products'])
        logger.debug(f'Received {count} of {total} data sets')
    logger.info('Found {0} products'.format(len(data.get('products', []))))
    return data


def download(products, output_dir='.'):
    '''Download a set of products via API.

    :param products: List with product information (e.g. retrieved via search).
                     The list needs to contain dictionaries which must at least
                     have the fields `uuid` and `identifier`.
    :param output_dir: Directory to which the files will be downloaded.
    '''
    for product in products:
        uuid = product['uuid']
        filename = os.path.join(output_dir, product['identifier'] + '.nc')
        logger.info(f'Downloading {uuid} to {filename}')
        base_path = f"/odata/v1/Products('{uuid}')"

        # Check if file exist
        if os.path.exists(filename):
            # Skip download if checksum matches
            if __check_md5(filename, base_path):
                logger.info(f'Skipping {filename} since it already exist.')
                continue
            logger.info(f'Overriding {filename} since md5 hash differs.')

        # Download file
        __http_request(f'{base_path}/$value', filename)

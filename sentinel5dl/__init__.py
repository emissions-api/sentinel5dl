# -*- coding: utf-8 -*-
'''
Sentinel-5p Downloader
~~~~~~~~~~~~~~~~~~~~~~

:copyright: 2019, The Emissions API Developers
:url: https://emissions-api.org
:license: MIT
'''

import hashlib
import io
import json
import os.path
import pycurl
import urllib.parse
import logging


# Data publically provided by ESA:
API = 'https://s5phub.copernicus.eu/dhus/'
USER = 's5pguest'
PASS = 's5pguest'

logger = logging.getLogger(__name__)


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


def __http_request(path, headers=[], **post_data):
    '''Make an HTTP request to a given URL with optional parameters.

    :param path: Request path relative to the base API
    :param headers: Request headers to send (e.g. cookies)
    :param post_data: Data to send as HTTP POST request
    :returns: Tuple containing response body and list of response headers
    '''
    buf = io.BytesIO()
    response_headers = []
    curl = pycurl.Curl()
    url = API + path.lstrip('/')
    curl.setopt(curl.URL, url.encode('ascii', 'ignore'))

    if headers:
        curl.setopt(curl.HTTPHEADER, headers)
    if post_data:
        post_fields = urllib.parse.urlencode(post_data)
        curl.setopt(curl.POSTFIELDS, post_fields)
    curl.setopt(curl.USERPWD, f'{USER}:{PASS}')
    curl.setopt(curl.WRITEFUNCTION, buf.write)
    curl.setopt(curl.HEADERFUNCTION, response_headers.append)
    curl.setopt(curl.FAILONERROR, True)
    curl.perform()
    curl.close()
    result = buf.getvalue()
    buf.close()
    return result, response_headers


def __http_download(path, filename, headers=[]):
    '''Download a file from the API via HTTP.

    :param path: Request path relative to the base API
    :param filename: Output file name. Note that this file will be overwritten
                     if it already exists.
    :param headers: Request headers to send (e.g. cookies)
    '''
    with open(filename, 'wb') as f:
        curl = pycurl.Curl()
        url = API + path.lstrip('/')
        curl.setopt(curl.URL, url.encode('ascii', 'ignore'))

        if headers:
            curl.setopt(curl.HTTPHEADER, headers)
        curl.setopt(curl.USERPWD, f'{USER}:{PASS}')
        curl.setopt(curl.WRITEDATA, f)
        curl.setopt(curl.FAILONERROR, True)
        curl.perform()
        curl.close()


def _login():
    '''Login to retrieve a session cookie.

    :returns: Session cookie.
    '''
    _, headers = __http_request('/login', login_username=USER,
                                login_password=PASS)
    cookies = []
    for header in headers:
        header_line = header.decode('ascii', 'ignore')
        if header_line.lower().startswith('set-cookie:'):
            value = header_line.split(':', 1)[1]
            cookies.extend([c.strip() for c in value.split(';')])
    return 'Cookie: ' + '; '.join(set(cookies))


def _user(cookies):
    '''Request user information.

    :param cookies: Session cookie to use for request.
    :returns: Dictionary containing user information.
    '''
    path = f'/odata/v1/Users(\'{USER}\')?$format=json&$expand=SystemRoles'
    body, _ = __http_request(path, [cookies])
    return json.loads(body.decode('utf8')).get('d')


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
    logger.debug(f'Requesting {path}')
    body, _ = __http_request(path)
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
        path = f'/odata/v1/Products(\'{uuid}\')/$value'

        # Check if file exist
        if os.path.exists(filename):
            # Get md5 sum
            md5um_path = \
                f'/odata/v1/Products(\'{uuid}\')/Checksum/Value/$value'
            md5sum, _ = __http_request(md5um_path)
            md5sum = md5sum.decode()

            # Compare md5 sum
            if __md5(filename) == md5sum:
                logger.info(f'Skipping {filename} since it already exist.')
                continue
            logger.info(f'Overriding {filename} since md5 hash differs.')

        # Download file
        __http_download(path, filename)

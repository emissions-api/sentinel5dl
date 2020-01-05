import os
import logging
import datetime
import tempfile
import unittest
from unittest.mock import patch
import sentinel5dl


testpath = os.path.dirname(os.path.abspath(__file__))


def mock_http_request(path, filename=None, resume=False):
    """Mock HTTP requests to the ESA API"""
    # download
    if filename is not None:
        with open(filename, 'wb') as f:
            f.write(b'123')
        return

    # search request
    if path.startswith('/api/stub/products?'):
        with open(os.path.join(testpath, 'products.json'), 'rb') as f:
            return f.read()

    # checksum request
    if path.endswith('/Checksum/Value/$value'):
        # MD5 checksum for string `123`
        return b'202CB962AC59075B964B07152D234B70'


class TestSentinel5dl(unittest.TestCase):

    def setUp(self):
        """Patch cURL based operation in sentinel5dl so that we do not really
        make any HTTP requests and reset the request counters."""
        logging.getLogger(sentinel5dl.__name__).setLevel(logging.WARNING)

    @patch('sentinel5dl.__http_request')
    def test_search_and_download(self, mock_request):
        mock_request.side_effect = mock_http_request
        result = sentinel5dl.search(
            polygon='POLYGON((7 49,13 49,13 52,7 52,7 49))',
            begin_ts=datetime.datetime.fromtimestamp(0),
            end_ts=datetime.datetime.now(),
            product='L2__CO____')

        # The result returned by the mock contains four products but claims a
        # total of eight products, making sentinel5dl request resources twice.
        self.assertEqual(mock_request.call_count, 2)
        self.assertEqual(result['totalresults'], 8)
        self.assertEqual(result['totalresults'], len(result['products']))

        products = result['products']
        with tempfile.TemporaryDirectory() as temp_dir:

            # prepare a file which is half-downloaded
            file_one = os.path.join(temp_dir, products[0]['identifier'] + '.nc')
            with open(file_one, 'wb') as f:
                f.write(b'12')

            sentinel5dl.download(products, worker_num=1, output_dir=temp_dir)

            # test files
            for product in products:
                filename = os.path.join(temp_dir, product['identifier'] + '.nc')
                with open(filename, 'rb') as f:
                    self.assertEqual(f.read(), b'123')

            # We should have downloaded four files and have an additional four
            # files storing md5 checksums
            self.assertEqual(len(os.listdir(temp_dir)), 8)

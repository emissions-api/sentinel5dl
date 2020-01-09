import datetime
import os
import sentinel5dl
import sentinel5dl.__main__ as executable
import tempfile
import unittest
from unittest.mock import patch
import logging
import sys


test_dir = os.path.dirname(os.path.realpath(__file__))


def _mock_http_request(path, filename=None, resume=False):
    """Mock HTTP requests to the ESA API.
    """
    # download
    if filename is not None:
        with open(filename, 'wb') as f:
            f.write(b'123')
        return

    # search request
    if path.startswith('/api/stub/products?'):
        with open(os.path.join(test_dir, 'products.json'), 'rb') as f:
            return f.read()

    # checksum request
    if path.endswith('/Checksum/Value/$value'):
        # MD5 checksum for string `123`
        return b'202CB962AC59075B964B07152D234B70'


class TestSentinel5dl(unittest.TestCase):

    def setUp(self):
        """Patch cURL based operation in sentinel5dl so that we do not really
        make any HTTP requests and reset the request counters.
        """
        logging.getLogger(sentinel5dl.__name__).setLevel(logging.WARNING)

    @patch('sentinel5dl.__http_request', side_effect=_mock_http_request)
    def test_search_and_download(self, mock_request):
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
            # We should have four checksum requests. One for each file
            self.assertEqual(len([s for s in os.listdir(temp_dir)
                                  if s.endswith('.md5sum')]), 4)
            # We should have downloaded four unique files
            self.assertEqual(len([s for s in os.listdir(temp_dir)
                                  if s.endswith('.nc')]), 4)


def _mock_download(products, *args):
    assert products == []


class TestExecutable(unittest.TestCase):

    @patch.object(sys, 'argv', sys.argv[0:1] + ['.'])
    @patch.object(executable, 'search', return_value={'products': []})
    @patch.object(executable, 'download', side_effect=_mock_download)
    def test_executable(self, mock_search, mock_download):
        executable.main()

        self.assertTrue(mock_search.assert_called_once)
        self.assertTrue(mock_download.assert_called_once)


if __name__ == '__main__':
    unittest.main()

import datetime
import os
import pycurl
import sentinel5dl
import sentinel5dl.__main__ as executable
import tempfile
import unittest
import logging
import sys


testpath = os.path.dirname(os.path.abspath(__file__))


class TestSentinel5dl(unittest.TestCase):

    def _mock_http_request(self, path, filename=None, headers=[]):
        '''Mock HTTP requests to the ESA API
        '''
        # download
        if filename is not None:
            self._count_download += 1
            with open(filename, 'wb') as f:
                f.write(b'123')
            return

        # search request
        if path.startswith('/api/stub/products?'):
            self._count_search_request += 1
            with open(os.path.join(testpath, 'products.json'), 'rb') as f:
                return f.read()

        # checksum request
        if path.endswith('/Checksum/Value/$value'):
            self._count_checksum_request += 1
            # MD5 checksum for string `123`
            return b'202CB962AC59075B964B07152D234B70'

    def setUp(self):
        '''Patch cURL based operation in sentinel5dl so that we do not really
        make any HTTP requests and reset the request counters.
        '''
        if not getattr(sentinel5dl, '__original_http_request', None):
            # save the original one
            setattr(sentinel5dl, '__original_http_request',
                    getattr(sentinel5dl, '__http_request'))
        setattr(sentinel5dl, '__http_request', self._mock_http_request)
        self._count_search_request = 0
        self._count_checksum_request = 0
        self._count_download = 0
        logging.getLogger(sentinel5dl.__name__).setLevel(logging.WARNING)

    def test(self):
        '''Test search and download.
        '''
        result = sentinel5dl.search(
            polygon='POLYGON((7 49,13 49,13 52,7 52,7 49))',
            begin_ts=datetime.datetime.fromtimestamp(0),
            end_ts=datetime.datetime.now(),
            product='L2__CO____')

        # The result returned by the mock contains four products but claims a
        # total of eight products, making sentinel5dl request resources twice.
        self.assertEqual(self._count_search_request, 2)
        self.assertEqual(result['totalresults'], 8)
        self.assertEqual(result['totalresults'], len(result['products']))

        products = result['products']
        with tempfile.TemporaryDirectory() as tmpdir:

            # prepare a file which is half-downloaded
            file_one = os.path.join(tmpdir, products[0]['identifier'] + '.nc')
            with open(file_one, 'wb') as f:
                f.write(b'12')

            sentinel5dl.download(products, tmpdir)

            # test files
            for product in products:
                filename = os.path.join(tmpdir, product['identifier'] + '.nc')
                with open(filename, 'rb') as f:
                    self.assertEqual(f.read(), b'123')

            # We should have downloaded four files and have an additional four
            # files storing md5 checksums
            self.assertEqual(len(os.listdir(tmpdir)), 8)

        # We should have four checksum requests. One for each file
        self.assertEqual(self._count_checksum_request, 4)
        # We should have downloaded four unique files
        self.assertEqual(self._count_download, 4)

    def testFailedRequest(self):
        sentinel5dl.API = 'http://127.0.0.1:9'
        request = getattr(sentinel5dl, '__original_http_request')
        # nothing may use port 9. This should always fail
        with self.assertRaises(pycurl.error):
            request('/', retries=0)


class TestExecutable(unittest.TestCase):

    def _mock_search(self, *args, **kwargs):
        return {'products': []}

    def _mock_download(self, products, _):
        self.assertEqual(products, [])

    def setUp(self):
        # Mock library calls
        setattr(executable, 'search', self._mock_search)
        setattr(executable, 'download', self._mock_download)
        logging.getLogger(sentinel5dl.__name__).setLevel(logging.WARNING)
        # override sys.argv. Otherwise argparse is trying to parse it.
        sys.argv = sys.argv[0:1] + ['.']

    def testNoArguments(self):
        '''Test the executable.
        '''
        executable.main()

    def testPolygon(self):
        '''Test with an invalid polygon.
        '''
        sys.argv = [sys.argv[0], '--polygon', '3 1, 4 4, 2 4, 1 2, 3 1', '.']
        executable.main()

    def testInvalidPolygons(self):
        '''Tests with invalid polygons.
        '''
        invalid_polygons = (
            '3 1 4 4, 2 4 1',      # coordinates must be pairs
            '3 1, 4 4, 2 4, 1 2',  # polygon must be closed
            'a s, d f, a s, d f',  # coordinates must be numbers
        )

        for invalid_polygon in invalid_polygons:
            sys.argv = [sys.argv[0], '--polygon', invalid_polygon, '.']

            error_msg = 'Expecting SystemExit error when providing the '\
                f'invalid polygon "{invalid_polygon}"'
            with self.assertRaises(SystemExit, msg=error_msg) as e:
                executable.main()

            error_msg = 'Expecting return code != 0 error when providing '\
                f'the invalid polygon "{invalid_polygon}"'
            self.assertNotEqual(e.exception.code, 0, msg=error_msg)


if __name__ == '__main__':
    unittest.main()

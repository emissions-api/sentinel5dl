import os
import sentinel5dl
import tempfile
import unittest


testpath = os.path.dirname(os.path.abspath(__file__))


class TestSentinel5dl(unittest.TestCase):

    def _mock_http_request(self, path, filename=None):
        '''Mock HTTP requests to the ESA API
        '''
        if filename is not None:
            self._count_download += 1
            with open(filename, 'wb') as f:
                f.write(b'123')
            return

        # no nownload
        self._count_request += 1
        if path.startswith('/api/stub/products?'):
            with open(os.path.join(testpath, 'products.json'), 'rb') as f:
                return f.read()
        if path.endswith('/Checksum/Value/$value'):
            # MD5 checksum for string `123`
            return b'202CB962AC59075B964B07152D234B70'

    def setUp(self):
        '''Patch cURL based operation in sentinel5dl so that we do not really
        make any HTTP requests and reset the request counters.
        '''
        setattr(sentinel5dl, '__http_request', self._mock_http_request)
        self._count_request = 0
        self._count_download = 0

    def test(self):
        '''Test search and download.
        '''
        result = sentinel5dl.search(
            polygon='POLYGON((7 49,13 49,13 52,7 52,7 49))',
            begin_ts='2019-09-01T00:00:00.000Z',
            end_ts='2019-09-17T23:59:59.999Z',
            product='L2__CO____')

        # The result returned by the mock contains four products but claims a
        # total of eight products, making sentinel5dl request resources twice.
        self.assertEqual(self._count_request, 2)
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

        # We should have made an additional five requests for checksums:
        # - one for the file we created manually
        # - four for the duplicated entries in the loaded test data
        self.assertEqual(self._count_request, 7)
        # We should have downloaded four unique files
        self.assertEqual(self._count_download, 4)


if __name__ == '__main__':
    unittest.main()

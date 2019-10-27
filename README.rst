Sentinel-5P Downloader
======================

.. image:: https://travis-ci.com/emissions-api/sentinel5dl.svg?branch=master
    :target: https://travis-ci.com/emissions-api/sentinel5dl
    :alt: CI Builds
.. image:: https://coveralls.io/repos/github/emissions-api/sentinel5dl/badge.svg?branch=master
    :target: https://coveralls.io/github/emissions-api/sentinel5dl?branch=master
    :alt: Test Coverage
.. image:: https://img.shields.io/github/issues-raw/emissions-api/sentinel5dl?color=blue
    :target: https://github.com/emissions-api/sentinel5dl/issues
    :alt: GitHub issues
.. image:: https://img.shields.io/github/license/emissions-api/sentinel5dl
    :target: https://github.com/emissions-api/sentinel5dl/blob/master/LICENSE
    :alt: MIT license

This library provides easy access to data from the European Space Agency's
Sentinel 5P satellite.

- `Sentinel5dl on PyPI <https://pypi.org/project/sentinel5dl/>`_
- `Online documentation <https://sentinel5dl.emissions-api.org>`_
- `Issue tracker <https://github.com/emissions-api/sentinel5dl/issues>`_


Installation
------------

Install this library using::

    %> pip install sentinel5dl


Quick Example
-------------

.. code-block:: python


    from sentinel5dl import search, download

    # Search for Sentinel-5 products
    result = search(
            polygon='POLYGON((7.8 49.3,13.4 49.3,13.4 52.8,7.8 52.8,7.8 49.3))',
            begin_ts='2019-09-01T00:00:00.000Z',
            end_ts='2019-09-17T23:59:59.999Z',
            product='L2__CO____',
            processing_level='L2')

    # Download found products to the local folder
    download(result.get('products'))

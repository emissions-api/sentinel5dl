from setuptools import setup, find_packages

setup(
    name='sentinel5dl',
    version='0.4',
    description='Sentinel-5p Downloader',
    author='Emissions API Developers',
    license='MIT',
    url='https://github.com/emissions-api/sentinel5dl',
    packages=find_packages(),
    classifiers=[
        'Development Status :: 4 - Beta',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Operating System :: OS Independent',
        'Topic :: Scientific/Engineering :: GIS',
    ],
    install_requires=['pycurl>=7.43.0'],
    long_description='This library provides easy access to data from the '
                     'European Space Agency\'s Sentinel 5P sattellite.',
    entry_points={
        'console_scripts': [
            'sentinel5dl = sentinel5dl.__main__:main'
        ]
    }
)

from setuptools import setup, find_packages
import os

path = os.path.abspath(os.path.dirname(__file__))


def read(filename):
    with open(os.path.join(path, filename), encoding='utf-8') as f:
        return f.read()


setup(
    name='sentinel5dl',
    version='1.2',
    description='Sentinel-5p Downloader',
    author='Emissions API Developers',
    license='MIT',
    url='https://github.com/emissions-api/sentinel5dl',
    packages=find_packages(),
    classifiers=[
        'Development Status :: 5 - Production/Stable',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
        'Programming Language :: Python :: 3.10',
        'Operating System :: OS Independent',
        'Topic :: Scientific/Engineering :: GIS',
    ],
    install_requires=read('requirements.txt').split(),
    long_description=read('README.rst'),
    long_description_content_type='text/x-rst',
    entry_points={
        'console_scripts': [
            'sentinel5dl = sentinel5dl.__main__:main'
        ]
    }
)

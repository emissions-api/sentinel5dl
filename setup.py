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
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
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

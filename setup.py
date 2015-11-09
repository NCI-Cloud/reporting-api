import os

from setuptools import setup, find_packages


def read(*paths):
    """Build a file path from *paths* and return the contents."""
    with open(os.path.join(*paths), 'r') as f:
        return f.read()

setup(
    name='reporting-api',
    version='0.1.0',
    description='OpenStack Reporting API',
    long_description=(read('README.md')),
    url='https://github.com/NCI-Cloud/reporting-api',
    license='Apache 2.0',
    author='NCI Cloud Team',
    author_email='cloud.team@nci.org.au',
    packages=find_packages(),
    install_requires=open('REQUIREMENTS.txt').read().splitlines(),
    include_package_data=True,
    scripts=['bin/reporting-api.py'],
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Environment :: Web Environment',
        'Framework :: Paste',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: Apache Software License',
        'Natural Language :: English',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.3',
        'Topic :: Software Development :: Libraries :: Python Modules',
        'Topic :: Database :: Front-Ends',
        'Topic :: Internet :: WWW/HTTP :: WSGI :: Application',
        'Topic :: Internet :: WWW/HTTP :: WSGI :: Middleware',
        'Topic :: Internet :: WWW/HTTP :: WSGI :: Server',
    ],
)

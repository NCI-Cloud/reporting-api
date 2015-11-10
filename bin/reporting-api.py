#!/usr/bin/python

"""
Start the Reporting API application using Paste Deploy.
"""

import sys
import os
from paste.deploy import loadapp, loadserver
import logging
import argparse

def parse_args():
    REALFILE = os.path.realpath(__file__)
    REALDIR = os.path.dirname(REALFILE)
    PARDIR = os.path.realpath(os.path.join(REALDIR, os.pardir))
    CONFDIR = os.path.join(PARDIR, 'reporting_api', 'conf')
    parser = argparse.ArgumentParser()
    parser.add_argument(
        '-c',
        '--confdir',
        action='store',
        required=False,
        default=CONFDIR,
        help="Specify config directory"
    )
    parser.add_argument(
        '-l',
        '--logfile',
        action='store',
        required=False,
        default='/var/log/reporting-api.log',
        help="Specify the file to log to"
    )
    return parser.parse_args()

if __name__ == '__main__':
    args = parse_args()
    logging.basicConfig(
        filename=args.logfile, level=logging.INFO
    )
    PASTE_CONFIG = os.path.join(args.confdir, 'paste.config')
    REPORTING_APP = loadapp('config:' + PASTE_CONFIG)
    SERVER = loadserver('config:' + PASTE_CONFIG)
    SERVER(REPORTING_APP)


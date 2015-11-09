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
    parser = argparse.ArgumentParser()
    parser.add_argument('-c', '--confdir', action='store', required=True, help="Specify config directory")
    parser.add_argument('--logfile', action='store', required=False, default='/var/log/reporting-api.log',
                        help="Specify the file to log to")
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


#!/usr/bin/python

"""
Start the Reporting API application using Paste Deploy.
"""

import os
from paste.deploy import loadapp, loadserver
import logging
import argparse


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('-c', '--confdir', action='store', required=True,
                        help="Specify config directory")
    parser.add_argument('--logfile', action='store', required=False,
                        default='/var/log/reporting-api.log',
                        help="Specify the file to log to")
    parser.add_argument('--pidfile', action='store', required=False,
                        default='/var/run/reporting-api.pid')
    return parser.parse_args()


def create_pidfile(pidfile="/var/run/reporting-api.pid"):
    with open(pidfile, 'rw') as pf:
        pf.write("%d" % (os.getpid()))

if __name__ == '__main__':
    args = parse_args()
    logging.basicConfig(
        filename=args.logfile, level=logging.INFO
    )
    PASTE_CONFIG = os.path.join(args.confdir, 'paste.config')
    REPORTING_APP = loadapp('config:' + PASTE_CONFIG)
    SERVER = loadserver('config:' + PASTE_CONFIG)
    create_pidfile(args.pidfile)
    SERVER(REPORTING_APP)

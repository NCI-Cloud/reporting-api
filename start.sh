#!/bin/sh

PYTHONPATH=. paster serve paste.config --reload >> /var/log/reporting-api.log 2>&1

#!/bin/sh

script=$(readlink -f "$0")
bindir=$(dirname "$script")
pardir=$(readlink -f "$bindir/..")
confdir="${pardir}/conf"
log=/var/log/reporting-api.log

PYTHONPATH="$pardir" paster serve "$confdir/paste.config" --reload >> "$log" 2>&1

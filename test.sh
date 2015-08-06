#!/bin/sh

urls="\
http://10.0.7.117:9494/v1/reports/projects/resultset/ \
http://10.0.7.117:9494/v1/reports/projects/resultset \
http://10.0.7.117:9494/v1/reports/projects/ \
http://10.0.7.117:9494/v1/reports/projects \
http://10.0.7.117:9494/v1/reports/ \
http://10.0.7.117:9494/v1/reports \
http://10.0.7.117:9494/v1/ \
http://10.0.7.117:9494/v1 \
http://10.0.7.117:9494/ \
http://10.0.7.117:9494 \
"

for url in $urls ; do
	echo "$url"
	curl "$url"
	ret=$?
	echo
	if [ $ret -ne 0 ] ; then
		break
	fi
done

#!/bin/sh

ip=$(cat conf/paste.config | egrep '^ *host *= *([^ ]+) *$' | sed -r -e 's/^ *host *= *([^ ]+) *$/\1/')
if test -z "$ip" ; then
       ip=$(ip a|egrep 'inet[^6]'|fgrep -v 127.0.0.1|sed -r -e 's/.*inet ([0-9.]+).*/\1/g'|head -1)
fi

urls="\
http://${ip}:9494/v1/reports/projects/resultset/ \
http://${ip}:9494/v1/reports/projects/resultset \
http://${ip}:9494/v1/reports/ \
http://${ip}:9494/v1/reports \
http://${ip}:9494/v1/ \
http://${ip}:9494/v1 \
http://${ip}:9494/ \
http://${ip}:9494 \
"

for url in $urls ; do
	echo "OPTIONS $url"
	curl -X OPTIONS "$url"
	ret=$?
	echo
	if [ $ret -ne 0 ] ; then
		echo "Error on OPTIONS of URL '$url'" 1>&2
		exit $?
	fi
	echo "GET $url"
	curl "$url"
	ret=$?
	echo
	if [ $ret -ne 0 ] ; then
		echo "Error on GET of URL '$url'" 1>&2
		exit $?
	fi
done

echo "All tests successful"
exit 0

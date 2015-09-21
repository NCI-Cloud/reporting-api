#!/bin/sh

# Attempt to use the IP address in the Paste configuration file
ip=$(cat conf/paste.config | egrep '^ *host *= *([^ ]+) *$' | sed -r -e 's/^ *host *= *([^ ]+) *$/\1/')
if test -z "$ip" ; then
	# Fall back to the IPv4 address of the first found network interface
       ip=$(ip a|egrep 'inet[^6]'|fgrep -v 127.0.0.1|sed -r -e 's/.*inet ([0-9.]+).*/\1/g'|head -1)
fi

methods="\
OPTIONS \
GET \
"

special_urls="\
http://${ip}:9494/v1/reports/instance/?name=test \
http://${ip}:9494/v1/reports/instance?name=test \
"

urls="\
http://${ip}:9494/v1/reports/project \
http://${ip}:9494/v1/reports \
http://${ip}:9494/v1 \
http://${ip}:9494 \
"

test_url() {
	method="$1"
	url="$2"
	echo "${method} $url"
	curl -X "$method" "$url"
	ret=$?
	echo
	if [ $ret -ne 0 ] ; then
		echo "Error on ${method} of URL '$url'" 1>&2
		exit $?
	fi
}

for base_url in $urls ; do
	for suffix in '' '/' ; do
		url="${base_url}${suffix}"
		for method in $methods ; do
			test_url "$method" "$url"
		done
	done
done
for url in $special_urls ; do
	for method in $methods ; do
		test_url "$method" "$url"
	done
done

echo "All tests successful"
exit 0

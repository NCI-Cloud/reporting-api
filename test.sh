#!/bin/sh

# Attempt to use the IP address in the Paste configuration file
ip=$(cat conf/paste.config | egrep '^ *host *= *([^ ]+) *$' | sed -r -e 's/^ *host *= *([^ ]+) *$/\1/')
if test -z "$ip" ; then
	# Fall back to the IPv4 address of the first found network interface
       ip=$(ip a|egrep 'inet[^6]'|fgrep -v 127.0.0.1|sed -r -e 's/.*inet ([0-9.]+).*/\1/g'|head -1)
fi

port=9494
verbose=
# verbose=--verbose

token=$(keystone token-get | egrep '^\|[ ]*id' | sed -r -e 's/^\|[ ]*id[ ]*\|[ ]*//g' | sed -r -e 's/[ ]*\|$//g')
ret=$?
if [ $ret -ne 0 ] ; then
	echo "Failed to get Keystone token" 1>&2
	exit $?
fi

auth="X-Auth-Token: $token"

methods="\
OPTIONS \
GET \
"

special_urls="\
http://${ip}:${port}/v1/reports/instance/?name=test \
http://${ip}:${port}/v1/reports/instance?name=test \
"

urls="\
http://${ip}:${port}/v1/reports/project \
http://${ip}:${port}/v1/reports \
http://${ip}:${port}/v1 \
http://${ip}:${port} \
"

test_url() {
	method="$1"
	url="$2"
	echo "${method} $url"
	curl $verbose -X "$method" -H "$auth" "$url"
	ret=$?
	echo
	if [ $ret -ne 0 ] ; then
		echo "Error on ${method} of URL '$url'" 1>&2
		exit $?
	fi
	# exit $?
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

#!/bin/sh

# Attempt to use the IP address in the Paste configuration file
ip=$(cat reporting/conf/paste.config | egrep '^ *host *= *([^ ]+) *$' | sed -r -e 's/^ *host *= *([^ ]+) *$/\1/')
if test -z "$ip" ; then
	# Fall back to the IPv4 address of the first found network interface
       ip=$(ip a|egrep 'inet[^6]'|fgrep -v 127.0.0.1|sed -r -e 's/.*inet ([0-9.]+).*/\1/g'|head -1)
fi

port=9494

verbose=
# verbose=--verbose

# This requests HTTP Transfer Encoding, which the server doesn't support,
# because browsers don't support it. It would be strictly correct, however.
# compressed=--tr-encoding

# This requests HTTP Content Encoding, which the server supports.
# Curl then automatically decompresses the response, which is incorrect,
# as that should only happen when using Transfer Encoding.
# Nevertheless, such auto-de-compression is the desired behaviour,
# so we do it even though it's not strictly correct.
compressed=--compressed

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
http://${ip}:${port}/v1/reports/flavour \
http://${ip}:${port}/v1/reports \
http://${ip}:${port}/v1 \
http://${ip}:${port} \
"

test_url_method() {
	url="$1"
	method="$2"
	echo "${method} $url"
	curl $verbose $compressed -X "$method" -H "$auth" "$url"
	ret=$?
	echo
	if [ $ret -ne 0 ] ; then
		echo "Error on ${method} of URL '$url'" 1>&2
		exit $ret
	fi
	# exit $ret
}

test_url_methods() {
	url="$1"
	shift
	for method in "$@" ; do
		test_url_method "$url" "$method"
	done
}

for base_url in $urls ; do
	for suffix in '' '/' ; do
		url="${base_url}${suffix}"
		test_url_methods "$url" $methods
	done
done
for url in $special_urls ; do
	test_url_methods "$url" $methods
done

echo "All tests successful"
exit 0

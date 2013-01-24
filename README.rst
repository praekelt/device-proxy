device-proxy
============

Inspects incoming HTTP requests adds some HTTP headers and proxies upstream.
Has ability to add extra cookies for HTTP responses being sent back to the
client.

Installation
------------

Installation is pegged to the latest GPL version of Wurfl.

Assuming you're living in a virtualenv::

    $ pip install -r requirements.pip
    $ ./get-wurfl-2.1-db.sh

Running
-------

Run with `twistd`::

    $ twistd -n devproxy --config config.yaml


Configuration
-------------

This is what the processing chain looks like::

           +------------------+
           |                  |
           |           Header & Cookie set
           v                  |
    (1) HAProxy -> (2) *n* DeviceProxies
           |
          (3)
           | (if Cookie or Header set)
           +--------------------------------> (4) *n* Backend Apps

1. Haproxy receives incoming traffic from Nginx
2. Request is passed to *n* number of Device Proxies running.
   HTTP headers are inserted (possibly from cached WURFL or OpenDDR lookups).
   Device Proxy has the option of inserting Cookies into the HTTP response
   which can cache the Device Lookup (for subsequent requests HAProxy (1)
   could use these cookie values to skip DeviceProxy completely for the
   lifetime of the Cookie.)
   DeviceProxy reverse proxies back to HAProxy with HTTP headers inserted.
3. HAProxy inspects the HTTP headers & cookies received and selects appropriate
   backend application for the request. HAProxy can have a default fallback
   backend. If the Cookie is already set then the DeviceProxies are skipped.
4. The Backend application renders the request with a template set suitable for
   the given HTTP request.

--------------------------------------------------------------------------------

    **NOTE:**
    By default DeviceProxy only caches the lookup in Memcache, not in the Cookie.

--------------------------------------------------------------------------------
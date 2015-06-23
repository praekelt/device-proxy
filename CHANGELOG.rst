Changelog
=========

next
----
#. Pass user agent as header so Wurfl API call works correctly.

0.4.2
-----
#. The Wurfl cloud handler can now go through an authenticated proxy.

0.4.1
-----
#. Ensure `EchoResource` properly encodes the headers.

0.4
---
#. Introduce `EchoResource` resource which does not proxy but returns to the
client. `ReverseProxyResource` constructor signature has changed so update any
subclasses you may have.


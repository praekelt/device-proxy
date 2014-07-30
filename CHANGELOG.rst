Changelog
=========

next
----
#. Ensure `EchoResource` properly encodes the headers.

0.4
---
#. Introduce `EchoResource` resource which does not proxy but returns to the
client. `ReverseProxyResource` constructor signature has changed so update any
subclasses you may have.


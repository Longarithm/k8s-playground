## Querying the app

On the node itself:

```bash
exec 3<>/dev/tcp/127.0.0.1/8080; printf 'GET /is-even?value=42 HTTP/1.1\r\nHost: localhost\r\n\r\n' >&3; cat <&3; exec 3>&- 3<&-
```

Externally:

```bash
curl 'http://EXTERNAL_IP:30080/is-even?value=41'
```

---
card: system-design
gi: 34
slug: reverse-proxy-vs-forward-proxy
title: Reverse proxy vs forward proxy
---

## 1. What it is

A **proxy** is a server that sits between a client and a destination, forwarding traffic on someone's behalf. A **forward proxy** sits in front of *clients*, forwarding their outgoing requests to the internet on the clients' behalf — the destination server sees the proxy, not the real client. A **reverse proxy** sits in front of *servers*, forwarding incoming requests to the right backend server on the servers' behalf — the client sees the proxy, not the real backend.

## 2. Why & when

The distinction is about *whose identity is hidden and whose interests the proxy serves*. A forward proxy protects and represents clients (common in corporate networks, filtering or anonymizing outgoing employee traffic). A reverse proxy protects and represents servers (extremely common in system design: it is what a load balancer, an API gateway, or a CDN edge node typically is, from the client's point of view). You bring this distinction up to be precise about which side of a connection a given proxy component sits on, especially since a load balancer is, structurally, a specific kind of reverse proxy.

## 3. Core concept

**Forward proxy:**
- Sits in front of a group of *clients* (e.g. all employees on a company network).
- The client is configured to send its requests *through* the proxy.
- The destination server only ever sees the proxy's IP address, not the real client's.
- Common uses: content filtering, anonymizing client identity, caching frequently requested external content for many internal clients.

**Reverse proxy:**
- Sits in front of a group of *servers* (your backend infrastructure).
- Clients connect to the reverse proxy's address, believing it *is* the server; they never connect directly to any real backend instance.
- The proxy decides which actual backend server handles each request, and the client never sees which one it was.
- Common uses: load balancing, SSL/TLS termination, caching, hiding internal architecture and server details from the outside world.

**The direction of "whose side it's on" is the entire distinction:** a forward proxy answers "who is this client talking to?" on the client's behalf. A reverse proxy answers "which of my servers should handle this?" on the server's behalf. The same physical proxy software (like Nginx) can be configured to act as either, depending only on which side it is deployed for.

## 4. Diagram

```
 FORWARD PROXY (represents CLIENTS)          REVERSE PROXY (represents SERVERS)
 Client1 -\                                   Client1 -\
 Client2 --> [Forward Proxy] --> Internet      Client2 --> [Reverse Proxy] -+-> Server1
 Client3 -/    (destination sees                          (client sees      +-> Server2
                the proxy, not                             the proxy, not   +-> Server3
                the real client)                            which real
                                                              server answered)
```
*Caption: a forward proxy hides the client from the destination; a reverse proxy hides the destination server from the client.*

## 5. Runnable example

### Artifact: a Java simulation modeling which identity each proxy type exposes to the other side

```java
import java.util.*;

public class ProxyDirectionSim {

    static String forwardProxyRequest(String realClientId, String destination) {
        String proxyIdentity = "forward-proxy-01";
        System.out.println(realClientId + " sends request through forward proxy to " + destination);
        System.out.println("  " + destination + " sees the request as coming from: " + proxyIdentity);
        return proxyIdentity;
    }

    static String reverseProxyRequest(String realClient, List<String> backendPool) {
        String chosenBackend = backendPool.get(new Random(42).nextInt(backendPool.size()));
        String proxyIdentity = "reverse-proxy-01";
        System.out.println(realClient + " sends request to " + proxyIdentity);
        System.out.println("  " + realClient + " never learns which backend handled it (actually: " + chosenBackend + ")");
        return chosenBackend;
    }

    public static void main(String[] args) {
        System.out.println("=== Forward proxy scenario ===");
        forwardProxyRequest("employee-laptop-17", "external-website.com");

        System.out.println("=== Reverse proxy scenario ===");
        reverseProxyRequest("public-browser-client", List.of("server1", "server2", "server3"));
    }
}
```

**How to run:** save as `ProxyDirectionSim.java`, run `java ProxyDirectionSim.java` (JDK 17+).

## 6. Walkthrough

1. `forwardProxyRequest` simulates a client's outbound request being relayed by a forward proxy; the print statements make explicit that the *destination* only ever learns the proxy's identity, never the real client's.
2. `reverseProxyRequest` simulates an inbound client request being relayed by a reverse proxy to one of several backend servers; the print statements make explicit that the *client* only ever knows about the reverse proxy, never which specific backend actually served the request.
3. `main` runs both scenarios back to back so the directional difference is visible side by side.
4. Output:
```
=== Forward proxy scenario ===
employee-laptop-17 sends request through forward proxy to external-website.com
  external-website.com sees the request as coming from: forward-proxy-01
=== Reverse proxy scenario ===
public-browser-client sends request to reverse-proxy-01
  public-browser-client never learns which backend handled it (actually: server2)
```
5. In the forward proxy case, the *destination's* view is obscured (it cannot see the real client). In the reverse proxy case, the *client's* view is obscured (it cannot see the real backend). This is the whole distinction, demonstrated concretely: each proxy type hides a different side of the connection from the other.

## 7. Gotchas & takeaways

> **Gotcha:** describing a load balancer or API gateway as "just a proxy" without specifying which kind. In a system design interview, precisely calling it a reverse proxy (representing your servers to the outside world) signals you understand the architectural role it plays, not just that traffic passes through it.

- Forward proxy: represents clients to the outside world; the destination sees the proxy, not the real client.
- Reverse proxy: represents servers to the outside world; the client sees the proxy, not the real backend server.
- Load balancers, API gateways, and CDN edge nodes are all, structurally, reverse proxies — this vocabulary connects several system design components under one concept.

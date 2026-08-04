---
card: system-design
gi: 33
slug: l4-transport-vs-l7-application-load-balancing
title: "L4 (transport) vs L7 (application) load balancing"
---

## 1. What it is

Load balancers are classified by which layer of the network stack they operate at, using the OSI model's numbering. An **L4 (Layer 4, transport-layer) load balancer** makes routing decisions using only network-level information — IP addresses and TCP/UDP ports — without looking at the actual content of the request. An **L7 (Layer 7, application-layer) load balancer** reads the actual application content, like the HTTP request's URL path, headers, or cookies, and routes based on that.

## 2. Why & when

Which layer your load balancer operates at determines how smart its routing can be, and how much overhead it adds. You bring this distinction up whenever a design needs routing decisions based on request *content* (like sending `/api/*` to one service and `/images/*` to another) — that requires L7. If you only need to spread raw connections across identical servers with no content-based logic, L4 is simpler and faster.

## 3. Core concept

**L4 load balancing:**
- Looks only at IP address and port; it does not parse or understand HTTP, or any application protocol, at all.
- Very fast, since there is minimal processing per packet — it essentially just forwards packets to a chosen backend based on connection information.
- Cannot make routing decisions based on URL path, headers, or cookies, because it never looks that deep into the request.
- Good fit when all backend servers are interchangeable and no content-based routing is needed.

**L7 load balancing:**
- Terminates the connection and actually reads the HTTP request — the method, URL path, headers, cookies, even the body if configured to.
- Can route based on content: `/api/*` to the API service, `/static/*` to a static file server, or route based on a specific header or cookie value.
- Can also perform application-aware features L4 cannot: SSL/TLS termination (decrypting HTTPS so backend servers receive plain HTTP), request/response modification, and detailed application-level health checks.
- Costs more processing per request, since it must parse and understand the application protocol.

**A concrete example of the difference:** an L4 load balancer sees a TCP connection to port 443 and picks a backend server based on a simple algorithm (like round-robin, covered later in this section) — it has no idea if the request is for `/checkout` or `/images/logo.png`. An L7 load balancer, having actually read the HTTP request, can send `/checkout` requests to a specially provisioned "checkout" service pool, and `/images/*` requests to a separate, cheaper static-asset pool.

## 4. Diagram

```
 L4 LOAD BALANCER (sees only IP:port)         L7 LOAD BALANCER (reads HTTP content)
 Client -> [TCP conn to :443] -> LB           Client -> [GET /checkout HTTP/1.1] -> LB
              |                                              |
      picks a backend by IP/port only            reads path "/checkout" -----> Checkout Pool
      (no idea what's inside the request)        reads path "/images/*" -----> Static Asset Pool
              v                                              |
         Any Backend Server                         (routes DIFFERENTLY based on content)
```
*Caption: L4 forwards based on connection info alone; L7 reads the actual request content to make smarter routing decisions.*

## 5. Runnable example

### Artifact: a Java simulation contrasting L4's blind round-robin routing with L7's content-aware routing

```java
import java.util.*;

public class L4VsL7Sim {

    record Request(String path) {}

    // L4: knows nothing about the request content, just cycles through all backends.
    static String l4Route(int requestIndex, List<String> allBackends) {
        return allBackends.get(requestIndex % allBackends.size());
    }

    // L7: reads the request path and routes to a specific pool based on content.
    static String l7Route(Request request, Map<String, String> pathToPool) {
        for (Map.Entry<String, String> rule : pathToPool.entrySet()) {
            if (request.path().startsWith(rule.getKey())) {
                return rule.getValue();
            }
        }
        return "default-pool";
    }

    public static void main(String[] args) {
        List<String> allBackends = List.of("server1", "server2", "server3");
        List<Request> requests = List.of(
            new Request("/checkout"),
            new Request("/images/logo.png"),
            new Request("/checkout"),
            new Request("/api/users")
        );

        System.out.println("L4 routing (blind to content, just cycles backends):");
        for (int i = 0; i < requests.size(); i++) {
            System.out.println("  " + requests.get(i).path() + " -> " + l4Route(i, allBackends));
        }

        Map<String, String> pathToPool = new LinkedHashMap<>();
        pathToPool.put("/checkout", "checkout-pool");
        pathToPool.put("/images", "static-asset-pool");
        pathToPool.put("/api", "api-pool");

        System.out.println("L7 routing (content-aware):");
        for (Request r : requests) {
            System.out.println("  " + r.path() + " -> " + l7Route(r, pathToPool));
        }
    }
}
```

**How to run:** save as `L4VsL7Sim.java`, run `java L4VsL7Sim.java` (JDK 17+).

## 6. Walkthrough

1. `l4Route` never even looks at `request.path()` — it only uses the request's *position in the sequence* to pick a backend in round-robin order, mirroring how L4 has no visibility into application content.
2. `l7Route` checks the request's actual path against a set of routing rules, and returns the specific pool that rule maps to — mirroring how L7 parses and acts on the real HTTP content.
3. `main` sends the same four requests through both routing functions, so the difference in behavior is directly visible on identical input.
4. Output:
```
L4 routing (blind to content, just cycles backends):
  /checkout -> server1
  /images/logo.png -> server2
  /checkout -> server3
  /api/users -> server1
L7 routing (content-aware):
  /checkout -> checkout-pool
  /images/logo.png -> static-asset-pool
  /checkout -> checkout-pool
  /api/users -> api-pool
```
5. Notice L4 sends the two `/checkout` requests to two *different* servers (`server1`, then `server3`), purely based on their position in the sequence — it has no concept of "checkout" as a category. L7 correctly sends both `/checkout` requests to the same `checkout-pool`, because it actually read and understood the request path.

## 7. Gotchas & takeaways

> **Gotcha:** assuming L7's extra capability is always worth its extra cost. If your backend servers are truly interchangeable and no content-based routing or SSL termination is needed, L4's lower overhead and simplicity make it the better, faster choice — added intelligence you do not use is added cost you did not need to pay.

- L4 routes based on IP/port only — fast, simple, no content awareness.
- L7 routes based on actual request content (path, headers, cookies) — enables smart routing and SSL termination, at higher processing cost.
- Choose L7 when you need content-based routing or SSL termination at the load balancer; choose L4 when backends are interchangeable and speed matters most.

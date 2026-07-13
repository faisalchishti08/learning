---
card: microservices
gi: 277
slug: client-side-vs-server-side-rate-limiting
title: "Client-side vs server-side rate limiting"
---

## 1. What it is

Rate limiting can be enforced on either side of a call: client-side rate limiting has the *caller* voluntarily throttle its own outgoing request rate (e.g., a client-side [token bucket](0274-token-bucket-algorithm.md) wrapping an HTTP client), while server-side rate limiting has the *callee* enforce a limit on incoming requests and reject or delay anything over it, regardless of what the caller intended. They solve related but distinct problems and are commonly used together, not as substitutes for each other.

## 2. Why & when

Server-side rate limiting is the authoritative, security-relevant control: it is the only place a service can truly *guarantee* protection, because it doesn't depend on every caller behaving well — a malicious, buggy, or simply uncooperative client cannot bypass it. But server-side limiting alone means every rejected request has already consumed network round-trip time and server-side connection resources before being turned away, and the caller only finds out it was over budget after the fact (typically via a 429 response).

Client-side rate limiting is a courtesy and an efficiency optimization: a well-behaved client that knows it is about to exceed a downstream service's published limit can throttle itself *before* sending, avoiding wasted round trips, avoiding contributing to the 429 flood, and often spacing out its own retries more gracefully. It requires no coordination and takes effect immediately, but it only works if the caller actually implements it — it provides no protection against callers who don't.

Use both together in a well-designed microservices system: server-side limiting as the non-negotiable backstop that protects the service under all circumstances, and client-side limiting in your own service's outbound HTTP clients as a courtesy to downstream dependencies and to reduce wasted calls that would just get rejected anyway.

## 3. Core concept

Server-side: a limiter sits in front of (or inside) the service handling incoming requests — a filter, interceptor, or API gateway — and rejects requests exceeding the configured limit for that caller/route.

Client-side: a limiter wraps the outgoing call in the calling code itself, blocking or rejecting the call locally *before* it ever leaves the process.

```java
// SERVER-SIDE: enforced regardless of caller intent, inside the callee.
class ServerSideLimiterFilter {
    boolean allowIncoming(String clientId) { /* checked on EVERY inbound request */ return true; }
}

// CLIENT-SIDE: caller voluntarily self-throttles BEFORE the call leaves.
class ClientSideLimitingHttpClient {
    boolean allowOutgoing() { /* checked BEFORE sending, avoids a wasted round trip */ return true; }
    Object call() {
        if (!allowOutgoing()) throw new IllegalStateException("self-throttled, not sent");
        return null; // would actually perform the HTTP call
    }
}
```

## 4. Diagram

<svg viewBox="0 0 640 190" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Client-side limiting happens inside the caller before the network call leaves; server-side limiting happens inside the callee after the request has already traveled across the network, rejecting it there instead">
  <rect x="30" y="30" width="150" height="60" rx="6" fill="#1c2430" stroke="#79c0ff"/>
  <text x="105" y="55" fill="#e6edf3" font-size="8" text-anchor="middle" font-family="sans-serif">Client</text>
  <text x="105" y="72" fill="#8b949e" font-size="7" text-anchor="middle" font-family="sans-serif">self-throttle BEFORE send</text>

  <line x1="180" y1="60" x2="300" y2="60" stroke="#6db33f" stroke-width="1.5" marker-end="url(#arr277)"/>
  <text x="240" y="50" fill="#8b949e" font-size="7" text-anchor="middle" font-family="sans-serif">network</text>

  <rect x="300" y="30" width="150" height="60" rx="6" fill="#1c2430" stroke="#79c0ff"/>
  <text x="375" y="55" fill="#e6edf3" font-size="8" text-anchor="middle" font-family="sans-serif">Server</text>
  <text x="375" y="72" fill="#8b949e" font-size="7" text-anchor="middle" font-family="sans-serif">enforce limit AFTER arrival</text>

  <text x="240" y="120" fill="#8b949e" font-size="7.5" text-anchor="middle" font-family="sans-serif">Client-side: cheap, voluntary, saves a wasted round trip</text>
  <text x="240" y="140" fill="#8b949e" font-size="7.5" text-anchor="middle" font-family="sans-serif">Server-side: authoritative, mandatory, the real backstop</text>
</svg>

Client-side throttling avoids the round trip; server-side enforcement is the guarantee that actually holds.

## 5. Runnable example

Scenario: a client that calls a rate-limited server with no client-side throttling (wasting round trips on rejections), extended with client-side self-throttling to avoid those wasted calls, and finally combining both with the client backing off based on the server's rejection hints for a realistic, resilient interaction.

### Level 1 — Basic

```java
// File: ServerOnlyLimiting.java -- server enforces a limit; client sends
// blindly with no self-throttling, wasting calls on rejections.
public class ServerOnlyLimiting {
    static class Server {
        int callsThisWindow = 0;
        final int limit = 3;
        String handle(int requestId) {
            if (callsThisWindow < limit) { callsThisWindow++; return "200 OK (request " + requestId + ")"; }
            return "429 Too Many Requests (request " + requestId + ")";
        }
    }

    public static void main(String[] args) {
        Server server = new Server();
        for (int i = 1; i <= 6; i++) {
            System.out.println("Client sends request " + i + " blindly -> " + server.handle(i));
        }
    }
}
```

How to run: `java ServerOnlyLimiting.java`

The client fires six requests with no awareness of the server's limit of 3 per window. The first three succeed; the last three each make a full round trip only to be rejected with a 429. Every rejected call still cost the client a network round trip and cost the server a connection accept and rejection response — pure waste that client-side throttling could have avoided.

### Level 2 — Intermediate

```java
// File: ClientSideThrottling.java -- client tracks its own budget and
// stops sending once it estimates it would be rejected, avoiding wasted
// round trips to the same server-side limiter.
public class ClientSideThrottling {
    static class Server {
        int callsThisWindow = 0;
        final int limit = 3;
        String handle(int requestId) {
            if (callsThisWindow < limit) { callsThisWindow++; return "200 OK (request " + requestId + ")"; }
            return "429 Too Many Requests (request " + requestId + ")";
        }
    }

    static class SelfThrottlingClient {
        int sentThisWindow = 0;
        final int knownServerLimit = 3; // published/discovered limit
        boolean shouldSend() { return sentThisWindow < knownServerLimit; }
        void recordSent() { sentThisWindow++; }
    }

    public static void main(String[] args) {
        Server server = new Server();
        SelfThrottlingClient client = new SelfThrottlingClient();
        for (int i = 1; i <= 6; i++) {
            if (client.shouldSend()) {
                client.recordSent();
                System.out.println("Client sends request " + i + " -> " + server.handle(i));
            } else {
                System.out.println("Client SKIPS request " + i + " locally (self-throttled, no round trip made)");
            }
        }
    }
}
```

How to run: `java ClientSideThrottling.java`

Same server and same six attempted requests, but now the client tracks `sentThisWindow` against the server's known limit of 3 and stops sending once it would exceed it. Requests 4-6 are skipped entirely on the client — no network call is made, no server-side rejection is generated. This is strictly more efficient: the client learns it is over budget without paying for a round trip, and the server never has to process and reject those calls.

### Level 3 — Advanced

```java
// File: CombinedLimitingWithBackoff.java -- client self-throttles using
// its own estimate, AND still handles the case where the server rejects
// anyway (its estimate was stale or wrong), backing off using the
// server's Retry-After hint -- the realistic, resilient combination.
public class CombinedLimitingWithBackoff {
    static class Server {
        int callsThisWindow = 0;
        final int limit = 3;
        final long retryAfterMillis = 1000;
        record Response(int status, String body, Long retryAfterMillis) {}
        Response handle(int requestId) {
            if (callsThisWindow < limit) {
                callsThisWindow++;
                return new Response(200, "ok(" + requestId + ")", null);
            }
            return new Response(429, "rejected(" + requestId + ")", retryAfterMillis);
        }
    }

    static class SelfThrottlingClient {
        int sentThisWindow = 0;
        int estimatedServerLimit = 3; // client's OWN estimate -- may be stale
        boolean shouldSend() { return sentThisWindow < estimatedServerLimit; }
        void recordSent() { sentThisWindow++; }
        void onRejected(long retryAfterMillis) {
            // Server disagreed with our estimate -- correct it and back off.
            estimatedServerLimit = sentThisWindow - 1;
            System.out.println("  Client corrects its estimate to " + estimatedServerLimit
                    + " and will wait " + retryAfterMillis + "ms before trying again");
        }
    }

    public static void main(String[] args) {
        Server server = new Server();
        // Client's estimate starts stale/optimistic at 5, though server's true limit is 3.
        SelfThrottlingClient client = new SelfThrottlingClient();
        client.estimatedServerLimit = 5;

        for (int i = 1; i <= 6; i++) {
            if (!client.shouldSend()) {
                System.out.println("Request " + i + ": SKIPPED locally (self-throttled)");
                continue;
            }
            client.recordSent();
            Server.Response r = server.handle(i);
            if (r.status() == 200) {
                System.out.println("Request " + i + ": sent -> 200 " + r.body());
            } else {
                System.out.println("Request " + i + ": sent -> 429 " + r.body());
                client.onRejected(r.retryAfterMillis());
            }
        }
    }
}
```

How to run: `java CombinedLimitingWithBackoff.java`

The client starts with a stale, overly optimistic estimate of the server's limit (5, when the true limit is 3). Requests 1-3 succeed and consume the server's real budget. Request 4 is sent (client's stale estimate still allows it) but the server rejects it with a 429 and a `retryAfterMillis` hint; the client's `onRejected` callback corrects its internal estimate down to match reality and logs the backoff wait. Request 5 is then skipped locally because the corrected estimate now matches the exhausted budget. This models the realistic production pattern: client-side throttling reduces load optimistically, but the client still must handle and learn from server-side rejections, since its own estimate can be wrong or stale (e.g., the server's limit changed, or the window reset differently than the client assumed).

## 6. Walkthrough

Trace `CombinedLimitingWithBackoff.main` in order. **First**, `server` is created with `limit=3`, and `client` is created with a deliberately wrong `estimatedServerLimit=5`.

**For requests 1-3**, `client.shouldSend()` returns `true` (sentThisWindow 0,1,2 all under 5), so each is sent. On the server, `handle` checks `callsThisWindow < limit` (3) — true for all three — so each increments `callsThisWindow` and returns a `Response(200, ...)`. The data at this stage: request enters the client layer, passes the client's local check, crosses to the server layer as a plain call, the server's counter state mutates from 0→1→2→3, and a 200 response returns to the client layer.

**At request 4**, the client's local check still passes (`sentThisWindow=3 < estimatedServerLimit=5`), so it is sent. On the server, `callsThisWindow` is now 3, which is not less than `limit=3`, so `handle` returns `Response(429, "rejected(4)", 1000)` instead. This response crosses back to the client layer, where the `if (r.status() == 200)` branch fails and the `else` branch fires, printing the rejection and calling `client.onRejected(1000)`.

**Inside `onRejected`**, the client corrects `estimatedServerLimit` to `sentThisWindow - 1`, i.e., `4 - 1 = 3` — now matching the server's true limit — and logs that it will wait before retrying.

**At request 5**, `client.shouldSend()` now evaluates `sentThisWindow(4) < estimatedServerLimit(3)`, which is false, so the request is skipped locally with no network call at all — the client has learned from the one rejection and stopped wasting round trips for the rest of the window.

**Request/response shape** for the rejected call, expressed as an HTTP-style exchange:
```
POST /work HTTP/1.1
X-Request-Id: 4

HTTP/1.1 429 Too Many Requests
Retry-After: 1000

{"body":"rejected(4)"}
```

```
client.shouldSend()? --yes--> server.handle() --429+Retry-After--> client.onRejected() corrects estimate --> next request re-checks locally
```

## 7. Gotchas & takeaways

> Client-side rate limiting is never a substitute for server-side enforcement — a client you don't control (or one with a bug) can always ignore its own throttle, so the server must still be the authoritative backstop.

- Server-side limiting is mandatory for protection; client-side limiting is an optimization that reduces wasted round trips and courtesy load on downstream services.
- A client's estimate of the server's limit can go stale (limits change, windows don't align) — always handle actual server rejections gracefully rather than trusting the local estimate blindly.
- Use the server's `Retry-After` (or equivalent) hint to correct the client's estimate and pace retries, rather than hammering immediately after a rejection.
- In a microservices system, apply client-side throttling in your own outbound HTTP clients toward every downstream dependency you call, and rely on server-side limiting (often at an API gateway) to protect every service you expose.

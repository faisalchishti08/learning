---
card: microservices
gi: 281
slug: connect-vs-read-timeouts
title: "Connect vs read timeouts"
---

## 1. What it is

An HTTP client call actually involves two distinct waiting phases, each of which needs its own timeout. The *connect timeout* bounds how long the client waits to establish the underlying TCP connection (and, for HTTPS, complete the TLS handshake) with the server. The *read timeout* (sometimes called socket timeout) bounds how long the client waits for data to arrive *after* the connection is already established — typically, the time between sending the request and receiving the first byte of the response, or between successive bytes/chunks of a streamed response.

## 2. Why & when

These two phases fail for completely different reasons and call for different timeout durations. A connection can fail to establish because the host is unreachable, a firewall silently drops packets, or the server's connection queue is full — these are usually near-instant failures at the network level, so the connect timeout can typically be set quite short (a few seconds at most; connecting either works fast or is essentially not going to work at all).

A read can be slow because the server is legitimately doing real, possibly heavy work before it has a response ready — a report generation endpoint might legitimately take 10+ seconds. The read timeout needs to be tuned to the *specific* endpoint's expected processing time, which varies wildly between a fast cache lookup and a slow batch job.

Using a single combined timeout for both phases forces an awkward compromise: set it short enough to fail fast on unreachable hosts, and it will falsely time out legitimately slow-but-working endpoints; set it long enough to tolerate slow endpoints, and a genuinely unreachable host will hang far longer than necessary before failing. Configuring them separately lets each be tuned to what it actually measures.

## 3. Core concept

Most production HTTP clients expose both settings independently.

```java
import java.net.http.HttpClient;
import java.time.Duration;
import java.net.http.HttpRequest;
import java.net.http.HttpResponse;

HttpClient client = HttpClient.newBuilder()
    .connectTimeout(Duration.ofSeconds(2))  // bounds TCP connect + TLS handshake
    .build();

HttpRequest request = HttpRequest.newBuilder()
    .uri(java.net.URI.create("https://api.example.com/report"))
    .timeout(Duration.ofSeconds(15))        // bounds waiting for the RESPONSE after connecting
    .build();

HttpResponse<String> response = client.send(request, HttpResponse.BodyHandlers.ofString());
```

## 4. Diagram

<svg viewBox="0 0 640 160" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="A timeline shows the connect phase, bounded by a short connect timeout, followed by the request being sent and the server processing, bounded by a separate, typically longer read timeout that governs waiting for the response after the connection already exists">
  <line x1="30" y1="80" x2="610" y2="80" stroke="#8b949e" stroke-width="1"/>

  <rect x="30" y="65" width="120" height="30" fill="#1c2430" stroke="#79c0ff"/>
  <text x="90" y="85" fill="#e6edf3" font-size="7.5" text-anchor="middle" font-family="sans-serif">TCP connect + TLS</text>
  <text x="90" y="55" fill="#8b949e" font-size="7" text-anchor="middle" font-family="sans-serif">connect timeout (short, ~2s)</text>

  <rect x="160" y="65" width="60" height="30" fill="#1c2430" stroke="#6db33f"/>
  <text x="190" y="85" fill="#e6edf3" font-size="7" text-anchor="middle" font-family="sans-serif">send req</text>

  <rect x="230" y="65" width="300" height="30" fill="#1c2430" stroke="#6db33f"/>
  <text x="380" y="85" fill="#e6edf3" font-size="7.5" text-anchor="middle" font-family="sans-serif">server processing / waiting for bytes</text>
  <text x="380" y="55" fill="#8b949e" font-size="7" text-anchor="middle" font-family="sans-serif">read timeout (endpoint-dependent, e.g. 15s)</text>

  <rect x="540" y="65" width="60" height="30" fill="#1c2430" stroke="#6db33f"/>
  <text x="570" y="85" fill="#e6edf3" font-size="7" text-anchor="middle" font-family="sans-serif">response</text>
</svg>

Connect timeout bounds establishing the pipe; read timeout bounds waiting for data once the pipe exists.

## 5. Runnable example

Scenario: a client using Java's `HttpClient` against an unreachable host to observe a connect-phase failure, extended to hit a real (slow-responding) endpoint to observe a read-phase failure with separately tuned timeouts, and finally combining both timeouts with retry logic that treats the two failure kinds differently, since a connect failure is often safely retryable while a read timeout on a non-idempotent write is not.

### Level 1 — Basic

```java
// File: ConnectTimeoutDemo.java -- a short connect timeout against an
// address that will not accept a TCP connection (a non-routable IP),
// failing fast instead of hanging.
import java.net.http.HttpClient;
import java.net.http.HttpRequest;
import java.net.http.HttpResponse;
import java.net.URI;
import java.time.Duration;
import java.net.http.HttpConnectTimeoutException;

public class ConnectTimeoutDemo {
    public static void main(String[] args) {
        HttpClient client = HttpClient.newBuilder()
                .connectTimeout(Duration.ofSeconds(2)) // fails fast if the TCP handshake doesn't complete
                .build();

        // 10.255.255.1 is a non-routable address in most environments -- connect will hang, then time out.
        HttpRequest request = HttpRequest.newBuilder()
                .uri(URI.create("http://10.255.255.1/"))
                .build();

        long start = System.currentTimeMillis();
        try {
            client.send(request, HttpResponse.BodyHandlers.ofString());
        } catch (HttpConnectTimeoutException e) {
            System.out.println("Connect timed out after " + (System.currentTimeMillis() - start)
                    + "ms -- server never accepted the TCP connection");
        } catch (Exception e) {
            System.out.println("Failed after " + (System.currentTimeMillis() - start) + "ms: " + e);
        }
    }
}
```

How to run: `java ConnectTimeoutDemo.java`

The client attempts to connect to a non-routable address. Because `connectTimeout` is set to 2 seconds, the client gives up on establishing the TCP connection after roughly 2 seconds and throws `HttpConnectTimeoutException`, rather than hanging for the OS-level TCP timeout (which can be 30-120+ seconds depending on platform). This is a pure connect-phase failure — no bytes of an HTTP request were ever sent.

### Level 2 — Intermediate

```java
// File: ReadTimeoutDemo.java -- connects successfully but the SERVER is
// slow to respond; a separate, longer read timeout governs this phase,
// tuned differently from the connect timeout.
import java.net.http.HttpClient;
import java.net.http.HttpRequest;
import java.net.http.HttpResponse;
import java.net.URI;
import java.time.Duration;
import java.net.http.HttpTimeoutException;

public class ReadTimeoutDemo {
    public static void main(String[] args) {
        HttpClient client = HttpClient.newBuilder()
                .connectTimeout(Duration.ofSeconds(2)) // still short -- this endpoint DOES accept connections fast
                .build();

        // httpbin's /delay/{n} endpoint accepts the connection immediately
        // but deliberately delays the response body by n seconds.
        HttpRequest request = HttpRequest.newBuilder()
                .uri(URI.create("https://httpbin.org/delay/10"))
                .timeout(Duration.ofSeconds(3)) // READ timeout: much shorter than the 10s the server will take
                .build();

        long start = System.currentTimeMillis();
        try {
            client.send(request, HttpResponse.BodyHandlers.ofString());
        } catch (HttpTimeoutException e) {
            System.out.println("Read timed out after " + (System.currentTimeMillis() - start)
                    + "ms -- connection was established, but the response never arrived in time");
        } catch (Exception e) {
            System.out.println("Failed after " + (System.currentTimeMillis() - start) + "ms: " + e);
        }
    }
}
```

How to run: `java ReadTimeoutDemo.java` (requires network access to httpbin.org)

The TCP connection to `httpbin.org` succeeds almost immediately (well within the 2-second connect timeout), so no `HttpConnectTimeoutException` occurs. But the endpoint `/delay/10` deliberately waits 10 seconds before sending any response body. Because the request-level `timeout` (the read timeout) is set to 3 seconds, the client gives up waiting for the response after roughly 3 seconds and throws `HttpTimeoutException` — a distinctly different failure from the connect-phase one in Level 1, even though both ultimately show up as "the call failed."

### Level 3 — Advanced

```java
// File: DifferentiatedRetryOnTimeoutType.java -- a real client wraps
// both timeouts AND treats a connect-phase failure and a read-phase
// failure differently on retry: a connect failure (nothing was sent) is
// safe to retry blindly, but a read timeout on a NON-idempotent POST
// might mean the server already processed it, so retry only if the
// operation is known to be idempotent.
import java.net.http.HttpClient;
import java.net.http.HttpRequest;
import java.net.http.HttpResponse;
import java.net.URI;
import java.time.Duration;
import java.net.http.HttpConnectTimeoutException;
import java.net.http.HttpTimeoutException;

public class DifferentiatedRetryOnTimeoutType {
    static HttpClient client = HttpClient.newBuilder()
            .connectTimeout(Duration.ofSeconds(2))
            .build();

    static String callWithDifferentiatedRetry(String url, boolean isIdempotent, int maxAttempts) {
        for (int attempt = 1; attempt <= maxAttempts; attempt++) {
            try {
                HttpRequest request = HttpRequest.newBuilder()
                        .uri(URI.create(url))
                        .timeout(Duration.ofSeconds(3))
                        .build();
                HttpResponse<String> response = client.send(request, HttpResponse.BodyHandlers.ofString());
                return "SUCCESS on attempt " + attempt + ": status=" + response.statusCode();
            } catch (HttpConnectTimeoutException e) {
                // Connect failure -- NOTHING was sent to the server. Always safe to retry.
                System.out.println("Attempt " + attempt + ": connect timeout, nothing sent -- retrying (safe)");
            } catch (HttpTimeoutException e) {
                // Read timeout -- the request MAY have already been processed server-side.
                if (!isIdempotent) {
                    return "GIVING UP after attempt " + attempt
                            + ": read timeout on a NON-idempotent call -- retrying could double-process it";
                }
                System.out.println("Attempt " + attempt + ": read timeout on an idempotent call -- retrying (safe)");
            } catch (Exception e) {
                return "FAILED on attempt " + attempt + ": " + e;
            }
        }
        return "GIVING UP after " + maxAttempts + " attempts";
    }

    public static void main(String[] args) {
        System.out.println(callWithDifferentiatedRetry("https://httpbin.org/delay/10", false, 3));
    }
}
```

How to run: `java DifferentiatedRetryOnTimeoutType.java` (requires network access to httpbin.org)

This models a production-realistic client calling a non-idempotent endpoint (`isIdempotent=false`, e.g., a "charge credit card" style call). The connect succeeds, but the request-level read timeout of 3 seconds is hit against the 10-second-delay endpoint. Because a read timeout means the client cannot be sure whether the server already received and started processing the request, and the operation is marked non-idempotent, the method gives up immediately after the first read timeout rather than retrying — retrying here risks double-processing (e.g., double-charging). Had `isIdempotent` been `true` (a safe GET, or a write designed to be idempotent), the same read timeout would instead trigger a retry, since re-sending an idempotent operation is safe regardless of whether the first attempt actually succeeded server-side.

## 6. Walkthrough

Trace `DifferentiatedRetryOnTimeoutType.main` in order for the `isIdempotent=false` call. **First**, `callWithDifferentiatedRetry` enters its loop with `attempt=1`, builds an `HttpRequest` with a 3-second read timeout, and calls `client.send(...)`.

**Internally**, `client.send` first performs the connect phase (TCP + TLS), bounded by the client-level `connectTimeout` of 2 seconds — this succeeds quickly since `httpbin.org` accepts connections immediately. **Next**, the client sends the HTTP request bytes over the now-established connection and begins waiting for a response, bounded by the request-level `timeout` of 3 seconds.

**At the 3-second mark**, the server still hasn't sent a response (it's programmed to wait 10 seconds), so the client throws `HttpTimeoutException` from `client.send`.

**Back in `callWithDifferentiatedRetry`**, this lands in the `catch (HttpTimeoutException e)` block. The code checks `isIdempotent`, which is `false` for this call — so instead of looping to `attempt=2`, it immediately returns a "GIVING UP" message explaining the reasoning: since a read timeout means the request bytes were already sent and possibly processed server-side, blindly retrying a non-idempotent operation could cause it to be executed twice.

**Contrast with a connect-phase failure** (as in Level 1): had the exception instead been `HttpConnectTimeoutException`, the code would print a message and loop to the next attempt regardless of idempotency, because a connect failure guarantees the server never received any request bytes — there is nothing to double-process.

```
send() -> [connect phase: 2s budget] -> [read phase: 3s budget]
              |                              |
       fails: HttpConnectTimeoutException   fails: HttpTimeoutException
              |                              |
       safe to retry (nothing sent)    retry ONLY if operation is idempotent
```

## 7. Gotchas & takeaways

> A read timeout does not tell you whether the server processed the request before timing out — from the client's perspective, the request may have been fully executed server-side, partially executed, or never received at all. Never blindly retry a non-idempotent operation after a read timeout without additional safeguards like an idempotency key.

- Connect timeouts should generally be short (a few seconds) since a healthy connection either establishes almost immediately or is not going to establish at all.
- Read timeouts should be tuned per endpoint based on that endpoint's actual expected processing time — a single global read timeout across every call in a service is usually wrong for at least some of those calls.
- A `HttpConnectTimeoutException` guarantees nothing was sent to the server and is generally always safe to retry; a read/request timeout carries no such guarantee.
- Many HTTP client libraries (Java's `HttpClient`, Apache HttpClient, OkHttp, Spring's `RestClient`/`WebClient`) expose connect and read/response timeouts as separate configuration — always set both explicitly rather than relying on library defaults, which are sometimes unbounded.

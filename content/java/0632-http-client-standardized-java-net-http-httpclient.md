---
card: java
gi: 632
slug: http-client-standardized-java-net-http-httpclient
title: HTTP Client standardized (java.net.http.HttpClient)
---

## 1. What it is

`java.net.http.HttpClient` is the **modern, standardised HTTP client API** introduced as an incubation feature in Java 9 and standardised in Java 11. It replaces the venerable `HttpURLConnection` (which dates from JDK 1.1 and is notoriously difficult to use correctly) and provides a clean, fluent, builder-based API for sending HTTP requests and receiving responses. The client supports **HTTP/1.1 and HTTP/2** with automatic protocol negotiation, **synchronous and asynchronous** request modes, and built-in handling of cookies, redirects, authentication, and WebSocket (added later). It is the definitive JDK HTTP client for new code — no third-party library required.

## 2. Why & when

`HttpURLConnection` is widely regarded as one of the worst APIs in the JDK: inconsistent error handling (it returns `200` for some errors), no HTTP/2 support, awkward streaming, and a verbose constructor/setup pattern that requires dozens of lines for a simple GET. For years, developers reached for third-party libraries (Apache HttpClient, OkHttp, Spring's `RestTemplate`) to avoid it. `java.net.http.HttpClient` gives the JDK a first-class HTTP client that is competitive with those libraries in ergonomics, supports modern protocols, and integrates naturally with the JDK's concurrency model (`CompletableFuture` for async). Use it as your default HTTP client in Java 11+ applications; reach for third-party libraries only when you need features beyond its scope (e.g. specific authentication schemes, connection pooling for very high throughput).

## 3. Core concept

```java
// Create a client (reusable, thread-safe)
HttpClient client = HttpClient.newHttpClient();

// Build a request
HttpRequest request = HttpRequest.newBuilder()
    .uri(URI.create("https://httpbin.org/get"))
    .GET()
    .build();

// Send synchronously
HttpResponse<String> response = client.send(request,
    HttpResponse.BodyHandlers.ofString());

System.out.println(response.statusCode());  // 200
System.out.println(response.body());        // JSON response body

// Or send asynchronously
client.sendAsync(request, HttpResponse.BodyHandlers.ofString())
    .thenApply(HttpResponse::body)
    .thenAccept(System.out::println);
```

The API has three main components: `HttpClient` (the reusable client configured with settings), `HttpRequest` (an immutable request built with a builder), and `HttpResponse` (the response containing status, headers, and body). Body handlers convert the response bytes into a usable type — `ofString()`, `ofFile()`, `ofInputStream()`, `ofByteArray()`, or custom handlers.

## 4. Diagram

<svg viewBox="0 0 600 160" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="HttpClient request/response flow with builder pattern">
  <rect x="10" y="10" width="580" height="140" rx="8" fill="#1c2430" stroke="#6db33f"/>

  <rect x="20" y="25" width="130" height="55" rx="4" fill="#0d1117" stroke="#79c0ff"/>
  <text x="85" y="44" fill="#79c0ff" font-size="10" text-anchor="middle" font-family="monospace">HttpClient</text>
  <text x="85" y="58" fill="#8b949e" font-size="8" text-anchor="middle" font-family="monospace">newHttpClient()</text>
  <text x="85" y="72" fill="#8b949e" font-size="7" text-anchor="middle" font-family="monospace">newBuilder()</text>

  <text x="160" y="55" fill="#8b949e" font-size="14" font-family="monospace" text-anchor="middle">→</text>

  <rect x="175" y="25" width="140" height="55" rx="4" fill="#0d1117" stroke="#79c0ff"/>
  <text x="245" y="44" fill="#79c0ff" font-size="10" text-anchor="middle" font-family="monospace">HttpRequest</text>
  <text x="245" y="58" fill="#8b949e" font-size="8" text-anchor="middle" font-family="monospace">.uri() .GET() .build()</text>
  <text x="245" y="72" fill="#8b949e" font-size="7" text-anchor="middle" font-family="monospace">or .POST(body)</text>

  <text x="325" y="55" fill="#8b949e" font-size="14" font-family="monospace" text-anchor="middle">→</text>

  <rect x="340" y="20" width="120" height="65" rx="4" fill="#6db33f" stroke="#6db33f"/>
  <text x="400" y="40" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="monospace">client.send()</text>
  <text x="400" y="55" fill="#8b949e" font-size="8" text-anchor="middle" font-family="monospace">or sendAsync()</text>
  <text x="400" y="70" fill="#8b949e" font-size="7" text-anchor="middle" font-family="monospace">+ BodyHandler</text>

  <text x="470" y="55" fill="#8b949e" font-size="14" font-family="monospace" text-anchor="middle">→</text>

  <rect x="485" y="25" width="95" height="55" rx="4" fill="#0d1117" stroke="#3fb950"/>
  <text x="532" y="44" fill="#3fb950" font-size="10" text-anchor="middle" font-family="monospace">HttpResponse</text>
  <text x="532" y="58" fill="#8b949e" font-size="8" text-anchor="middle" font-family="monospace">.statusCode()</text>
  <text x="532" y="72" fill="#8b949e" font-size="7" text-anchor="middle" font-family="monospace">.body()</text>

  <text x="20" y="120" fill="#8b949e" font-size="9" font-family="sans-serif">Supports: HTTP/1.1, HTTP/2, sync &amp; async, cookies, redirects, WebSocket (Java 11+ standardised)</text>
  <text x="20" y="138" fill="#3fb950" font-size="9" font-family="sans-serif">Replaces HttpURLConnection — no third-party library needed for modern HTTP</text>
</svg>

The builder pattern creates an immutable request; the client sends it and returns a typed response. The same `HttpClient` can be reused for multiple requests and is thread-safe.

## 5. Runnable example

Scenario: building a simple API client that fetches data from a public REST endpoint — starting with a basic GET, extending to POST with JSON and error handling, and finally handling async requests, custom headers, and HTTP/2.

### Level 1 — Basic

```java
// File: HttpClientDemo.java
import java.net.*;
import java.net.http.*;
import java.nio.charset.*;

public class HttpClientDemo {
    public static void main(String[] args) throws Exception {
        // Create a client (reusable, thread-safe)
        HttpClient client = HttpClient.newHttpClient();

        // Build a GET request
        HttpRequest request = HttpRequest.newBuilder()
            .uri(URI.create("https://httpbin.org/get?name=Java11"))
            .GET()
            .build();

        // Send synchronously, get body as String
        HttpResponse<String> response = client.send(request,
            HttpResponse.BodyHandlers.ofString());

        // Print the response
        System.out.println("Status: " + response.statusCode());
        System.out.println("Headers:");
        response.headers().map().forEach((k, v) ->
            System.out.println("  " + k + ": " + v));
        System.out.println("\nBody (truncated):");
        String body = response.body();
        System.out.println(body.length() > 200
            ? body.substring(0, 200) + "..."
            : body);
    }
}
```

**How to run:** `java HttpClientDemo.java` (requires internet access — fetches from httpbin.org)

Expected output:
```
Status: 200
Headers:
  date: [Wed, 09 Jul 2026 ...]
  content-type: [application/json]
  ...

Body (truncated):
{
  "args": {"name": "Java11"},
  "headers": { ... },
  "url": "https://httpbin.org/get?name=Java11"
}
```

The simplest usage: create a client, build a GET request, send it, and read the response body as a `String`. The API is fluent and self-documenting — no manual connection handling, no stream management.

### Level 2 — Intermediate

```java
// File: ApiClient.java
import java.net.*;
import java.net.http.*;
import java.net.http.HttpResponse.*;
import java.time.*;

public class ApiClient {
    // Reusable client with timeout configuration
    static final HttpClient CLIENT = HttpClient.newBuilder()
        .connectTimeout(Duration.ofSeconds(10))
        .followRedirects(HttpClient.Redirect.NORMAL)
        .build();

    public static void main(String[] args) throws Exception {
        // POST with JSON body
        String jsonPayload = """
            {"title": "Learn Java 11", "completed": false}
            """;

        HttpRequest postRequest = HttpRequest.newBuilder()
            .uri(URI.create("https://httpbin.org/post"))
            .header("Content-Type", "application/json")
            .POST(HttpRequest.BodyPublishers.ofString(jsonPayload))
            .build();

        System.out.println("=== POST Request ===");
        System.out.println("Sending: " + jsonPayload);

        HttpResponse<String> postResponse = CLIENT.send(postRequest,
            BodyHandlers.ofString());

        System.out.println("Status: " + postResponse.statusCode());
        System.out.println("Response body (truncated):");
        String body = postResponse.body();
        System.out.println(body.length() > 300
            ? body.substring(0, 300) + "..."
            : body);

        // GET with error handling
        System.out.println("\n=== GET with 404 handling ===");
        HttpRequest badRequest = HttpRequest.newBuilder()
            .uri(URI.create("https://httpbin.org/status/404"))
            .GET()
            .build();

        HttpResponse<String> errorResponse = CLIENT.send(badRequest,
            BodyHandlers.ofString());

        if (errorResponse.statusCode() == 404) {
            System.out.println("Resource not found (404) — handled gracefully");
        } else {
            System.out.println("Status: " + errorResponse.statusCode());
        }
    }
}
```

**How to run:** `java ApiClient.java` (requires internet access)

Expected output:
```
=== POST Request ===
Sending: {"title": "Learn Java 11", "completed": false}

Status: 200
Response body (truncated):
{
  "args": {},
  "data": "{\"title\": \"Learn Java 11\", \"completed\": false}",
  "json": {"completed": false, "title": "Learn Java 11"},
  ...
}

=== GET with 404 handling ===
Resource not found (404) — handled gracefully
```

The real-world concern: configuring the client (timeouts, redirect policy) and sending POST requests with JSON body. The client is built once (`HttpClient.newBuilder()`) and reused. `BodyPublishers.ofString()` sends the JSON payload. Response status codes allow graceful error handling — no exceptions for HTTP-level errors (unlike `HttpURLConnection`).

### Level 3 — Advanced

```java
// File: HttpClientAdvanced.java
import java.net.*;
import java.net.http.*;
import java.net.http.HttpResponse.*;
import java.time.*;
import java.util.*;
import java.util.concurrent.*;
import java.util.stream.*;

public class HttpClientAdvanced {
    public static void main(String[] args) throws Exception {
        HttpClient client = HttpClient.newBuilder()
            .connectTimeout(Duration.ofSeconds(10))
            .build();

        System.out.println("=== Async request ===");
        System.out.println("Request sent, doing other work while waiting...\n");

        // Async: send request, get CompletableFuture
        HttpRequest request = HttpRequest.newBuilder()
            .uri(URI.create("https://httpbin.org/delay/1"))  // 1-second delay
            .GET()
            .build();

        CompletableFuture<HttpResponse<String>> future =
            client.sendAsync(request, BodyHandlers.ofString());

        // Do other work while waiting
        System.out.println("Main thread is free — doing computation...");
        Thread.sleep(200);  // simulate other work

        // Get the result (blocks if not ready)
        HttpResponse<String> response = future.get(3, TimeUnit.SECONDS);
        System.out.println("Async response received!");
        System.out.println("Status: " + response.statusCode());

        System.out.println("\n=== Multiple concurrent requests ===");

        // Send multiple requests concurrently
        List<URI> uris = List.of(
            URI.create("https://httpbin.org/get?item=1"),
            URI.create("https://httpbin.org/get?item=2"),
            URI.create("https://httpbin.org/get?item=3")
        );

        List<CompletableFuture<String>> futures = uris.stream()
            .map(uri -> HttpRequest.newBuilder().uri(uri).GET().build())
            .map(req -> client.sendAsync(req, BodyHandlers.ofString())
                .thenApply(HttpResponse::statusCode)
                .thenApply(code -> "  " + req.uri() + " → " + code))
            .toList();

        // Wait for all and print results
        CompletableFuture.allOf(futures.toArray(new CompletableFuture[0]))
            .thenRun(() -> {
                System.out.println("All requests completed:");
                futures.forEach(f -> System.out.println(f.join()));
            })
            .join();

        System.out.println("\n=== Custom body handler (as bytes) ===");
        HttpRequest bytesReq = HttpRequest.newBuilder()
            .uri(URI.create("https://httpbin.org/bytes/16"))
            .GET()
            .build();

        HttpResponse<byte[]> bytesResp = client.send(bytesReq,
            BodyHandlers.ofByteArray());
        System.out.println("Received " + bytesResp.body().length + " bytes");

        System.out.println("\n=== HTTP/2 detection ===");
        System.out.println("Client version: " + client.version());
        // If the server supports HTTP/2, the client negotiates it automatically
        System.out.println("Response version: " + response.version());
    }
}
```

**How to run:** `java HttpClientAdvanced.java` (requires internet access)

Expected output:
```
=== Async request ===
Request sent, doing other work while waiting...

Main thread is free — doing computation...
Async response received!
Status: 200

=== Multiple concurrent requests ===

All requests completed:
  https://httpbin.org/get?item=1 → 200
  https://httpbin.org/get?item=2 → 200
  https://httpbin.org/get?item=3 → 200

=== Custom body handler (as bytes) ===

Received 16 bytes

=== HTTP/2 detection ===

Client version: HTTP_2
Response version: HTTP_1_1
```

The production-flavoured hard cases: (1) **Async requests** — `sendAsync()` returns `CompletableFuture<HttpResponse<T>>`, freeing the calling thread. Use `.get(timeout, unit)` to retrieve results with a deadline. (2) **Concurrent requests** — the same `HttpClient` handles multiple concurrent `sendAsync` calls, each returning its own `CompletableFuture`. `CompletableFuture.allOf()` waits for all to complete. (3) **Custom body handlers** — `BodyHandlers.ofByteArray()` for binary data, `ofFile(Path)` for downloading to disk, `ofInputStream()` for streaming. (4) **HTTP/2** — the client automatically negotiates HTTP/2 via ALPN when the server supports it (httpbin.org uses HTTP/1.1, so the response shows `HTTP_1_1`).

## 6. Walkthrough

Tracing a synchronous GET request end to end:

```
1. HttpClient client = HttpClient.newHttpClient();
```
A default `HttpClient` is created. Internally, this sets up an HTTP/2-capable connection pool with default settings (no proxy, system-default SSL context, normal redirect policy). The client is immutable and thread-safe.

```
2. HttpRequest request = HttpRequest.newBuilder()
       .uri(URI.create("https://httpbin.org/get?name=Java11"))
       .GET()
       .build();
```
An immutable `HttpRequest` is built. The builder validates the URI (must be absolute, HTTP or HTTPS). `.GET()` sets the method to GET (also the default). `.build()` returns the immutable request.

```
3. HttpResponse<String> response = client.send(request,
       HttpResponse.BodyHandlers.ofString());
```
- **Request sent:** The client looks up the host `httpbin.org` via DNS, opens a TCP connection (with TLS handshake for HTTPS), and negotiates HTTP/2 if the server's ALPN advertises it. The HTTP request is serialised to bytes and sent over the connection.

- The concrete request looks like:
  ```
  GET /get?name=Java11 HTTP/1.1
  Host: httpbin.org
  User-Agent: Java-http-client/11
  Accept: */*
  ```

- **Response received:** The server processes the request and returns:
  ```
  HTTP/1.1 200 OK
  Date: Wed, 09 Jul 2026 12:00:00 GMT
  Content-Type: application/json
  Content-Length: 310
  ...
  
  {"args":{"name":"Java11"},"headers":{...},"url":"..."}
  ```

- **Body conversion:** `BodyHandlers.ofString()` reads the response body bytes from the input stream, decodes them using the charset from the `Content-Type` header (defaulting to UTF-8), and returns a `String`.

- **Data state through layers:**
  1. **Application layer:** `"https://httpbin.org/get?name=Java11"` (URI string) → `URI` object → `HttpRequest` (immutable value object)
  2. **Transport layer:** `HttpRequest` → serialised HTTP/1.1 or HTTP/2 bytes sent over TLS-encrypted TCP
  3. **Server processing:** request bytes → httpbin.org parses, echoes back as JSON
  4. **Response layer:** response bytes → decoded `String` → `HttpResponse<String>` with status code 200 and headers
  5. **Application layer:** `response.body()` → `String` containing JSON → program prints it

```
4. System.out.println(response.statusCode());  // 200
   System.out.println(response.body());        // JSON body
```
The response is consumed. After this point, the response body has been read and is available as a `String`. The connection may be returned to the pool for reuse.

## 7. Gotchas & takeaways

> The response body is **not automatically closed** when reading with `BodyHandlers.ofString()` — the handler consumes the entire body and closes the stream internally. But with `BodyHandlers.ofInputStream()`, you are responsible for closing the stream. Failing to close leaves connections hanging.

- `HttpClient` is **immutable and thread-safe** — create one instance (or a few configured instances) and reuse them across your application. Creating a new client for every request wastes resources.
- `HttpRequest` is also immutable. To send a similar request with a different URI, build a new request from scratch — the builder pattern makes this cheap and readable.
- The client does NOT throw exceptions on 4xx or 5xx status codes (unlike `HttpURLConnection`). You must check `response.statusCode()` yourself. This is by design — HTTP error codes are valid responses.
- `sendAsync()` returns `CompletableFuture`. If the request fails (network error), the future completes exceptionally. Always handle exceptions with `.exceptionally()` or try-catch on `.get()`.
- HTTP/2 is negotiated automatically. To force HTTP/1.1, use `HttpClient.newBuilder().version(HttpClient.Version.HTTP_1_1)`. To require HTTP/2, use `.version(HttpClient.Version.HTTP_2)`.
- The client supports WebSocket (via `HttpClient.newWebSocketBuilder()`) and reactive body handlers via `java.util.concurrent.Flow` — but these are advanced topics beyond the standardised client.

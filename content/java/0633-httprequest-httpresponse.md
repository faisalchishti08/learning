---
card: java
gi: 633
slug: httprequest-httpresponse
title: HttpRequest / HttpResponse
---

## 1. What it is

`HttpRequest` and `HttpResponse` are the **request and response types** of the `java.net.http` API, standardised in Java 11. `HttpRequest` is an immutable value object representing an HTTP request — method, URI, headers, and body — built via a fluent builder: `HttpRequest.newBuilder().uri(...).GET().build()`. `HttpResponse<T>` is a generic container for the server's response: it holds the status code, response headers, and a typed body `T` (where `T` is determined by the `BodyHandler` used when sending). Together they form the core data model of the modern JDK HTTP client, replacing the error-prone `HttpURLConnection` object that mixed connection management, request configuration, and response parsing into one class.

## 2. Why & when

`HttpURLConnection` is a notoriously poorly designed API: it extends `URLConnection`, inherits confusing behaviour, throws `IOException` for perfectly valid HTTP error responses (like 404), and requires casting. `HttpRequest` and `HttpResponse` cleanly separate concerns: the request is an immutable snapshot of what you want to send, the response is a typed snapshot of what came back, and neither manages connections (the `HttpClient` does that). Use `HttpRequest`/`HttpResponse` whenever you use `java.net.http.HttpClient` in Java 11+ — they are the fundamental types you work with.

## 3. Core concept

```java
// HttpRequest: immutable, built via builder
HttpRequest request = HttpRequest.newBuilder()
    .uri(URI.create("https://example.com/api/users"))
    .header("Accept", "application/json")
    .timeout(Duration.ofSeconds(5))
    .GET()
    .build();

// HttpResponse<T>: generic, typed by body handler
HttpResponse<String> response = client.send(request,
    HttpResponse.BodyHandlers.ofString());

// Access parts independently
int status = response.statusCode();        // 200
HttpHeaders headers = response.headers();   // map of header names → values
String body = response.body();             // typed body (String here)
URI uri = response.uri();                  // the final URI (may differ after redirects)
HttpClient.Version version = response.version(); // HTTP/1.1 or HTTP/2
```

`HttpRequest` is a pure data object (no behaviour beyond getters). `HttpResponse` bundles status, headers, and body — the body type is determined at send-time by the `BodyHandler`.

## 4. Diagram

<svg viewBox="0 0 560 150" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="HttpRequest is an immutable value object; HttpResponse bundles status, headers, and typed body">
  <rect x="10" y="10" width="540" height="130" rx="8" fill="#1c2430" stroke="#6db33f"/>

  <rect x="20" y="20" width="240" height="50" rx="4" fill="#0d1117" stroke="#79c0ff"/>
  <text x="140" y="40" fill="#79c0ff" font-size="11" text-anchor="middle" font-family="monospace">HttpRequest</text>
  <text x="140" y="55" fill="#8b949e" font-size="8" text-anchor="middle" font-family="monospace">.uri() .method() .headers() .bodyPublisher() .timeout()</text>
  <text x="140" y="66" fill="#8b949e" font-size="7" text-anchor="middle" font-family="monospace">Immutable — built once, never modified</text>

  <rect x="280" y="20" width="260" height="50" rx="4" fill="#0d1117" stroke="#3fb950"/>
  <text x="410" y="40" fill="#3fb950" font-size="11" text-anchor="middle" font-family="monospace">HttpResponse&lt;T&gt;</text>
  <text x="410" y="55" fill="#8b949e" font-size="8" text-anchor="middle" font-family="monospace">.statusCode() .headers() .body() .uri() .version()</text>
  <text x="410" y="66" fill="#8b949e" font-size="7" text-anchor="middle" font-family="monospace">T determined by BodyHandler&lt;T&gt;</text>

  <text x="20" y="95" fill="#8b949e" font-size="9" font-family="sans-serif">HttpRequest is built with newBuilder() → .GET()/.POST()/.PUT()/.DELETE() → .build()</text>
  <text x="20" y="113" fill="#f85149" font-size="9" font-family="sans-serif">HttpResponse body is consumed exactly once (unless cached). .body() may throw if already consumed.</text>
  <text x="20" y="131" fill="#8b949e" font-size="9" font-family="sans-serif">Both are part of java.net.http (Java 11+). Replaces HttpURLConnection which mixed concerns.</text>
</svg>

`HttpRequest` captures everything about the outgoing message; `HttpResponse` captures everything about the incoming reply. The types are clean, immutable, and generic.

## 5. Runnable example

Scenario: fetching and inspecting GitHub API data — starting with a basic GET request/response, extending to inspecting headers and handling redirects, and finally handling different response body types.

### Level 1 — Basic

```java
// File: HttpRequestResponseDemo.java
import java.net.*;
import java.net.http.*;

public class HttpRequestResponseDemo {
    public static void main(String[] args) throws Exception {
        HttpClient client = HttpClient.newHttpClient();

        // Build request
        HttpRequest request = HttpRequest.newBuilder()
            .uri(URI.create("https://httpbin.org/json"))
            .GET()
            .build();

        // Inspect the request (it's immutable)
        System.out.println("=== Request ===");
        System.out.println("Method: " + request.method());
        System.out.println("URI:    " + request.uri());
        System.out.println("Headers:" + request.headers().map());

        // Send and get response
        HttpResponse<String> response = client.send(request,
            HttpResponse.BodyHandlers.ofString());

        // Inspect the response
        System.out.println("\n=== Response ===");
        System.out.println("Status:  " + response.statusCode());
        System.out.println("Version: " + response.version());
        System.out.println("Headers: " + response.headers().map().keySet());
        System.out.println("Body (first 100 chars): " +
            response.body().substring(0, Math.min(100, response.body().length())));
    }
}
```

**How to run:** `java HttpRequestResponseDemo.java`

Expected output:
```
=== Request ===
Method: GET
URI:    https://httpbin.org/json
Headers:{}

=== Response ===
Status:  200
Version: HTTP_1_1
Headers: [date, content-type, content-length, ...]
Body (first 100 chars): {
  "slideshow": {
    ...
  }
}
```

The simplest usage: build an `HttpRequest` (immutable snapshot), send it, and get back an `HttpResponse<T>` with typed access to status, headers, and body.

### Level 2 — Intermediate

```java
// File: HeadersAndRedirects.java
import java.net.*;
import java.net.http.*;

public class HeadersAndRedirects {
    public static void main(String[] args) throws Exception {
        // Client that follows redirects
        HttpClient client = HttpClient.newBuilder()
            .followRedirects(HttpClient.Redirect.NORMAL)
            .build();

        // Request with custom headers
        HttpRequest request = HttpRequest.newBuilder()
            .uri(URI.create("https://httpbin.org/response-headers?X-Custom=Hello&X-Request-Id=12345"))
            .header("User-Agent", "Java11HttpClient/1.0")
            .header("Accept-Language", "en-US")
            .GET()
            .build();

        System.out.println("=== Outgoing Request ===");
        System.out.println("URI: " + request.uri());
        System.out.println("Custom headers:");
        request.headers().map().forEach((k, v) ->
            System.out.println("  " + k + ": " + v));

        HttpResponse<String> response = client.send(request,
            HttpResponse.BodyHandlers.ofString());

        System.out.println("\n=== Incoming Response ===");
        System.out.println("Status: " + response.statusCode());
        System.out.println("Final URI: " + response.uri());  // may differ after redirect

        System.out.println("\nAll response headers:");
        response.headers().map().forEach((k, v) ->
            System.out.println("  " + k + ": " + String.join(", ", v)));

        // First value helper
        response.headers().firstValue("X-Custom").ifPresent(
            val -> System.out.println("\nX-Custom header value: " + val));

        // Demonstrate redirect
        System.out.println("\n=== Redirect test ===");
        HttpRequest redirectReq = HttpRequest.newBuilder()
            .uri(URI.create("https://httpbin.org/redirect/2"))  // redirects twice
            .GET()
            .build();

        HttpResponse<String> redirectResp = client.send(redirectReq,
            HttpResponse.BodyHandlers.ofString());

        System.out.println("Original URI:  " + redirectReq.uri());
        System.out.println("Final URI:     " + redirectResp.uri());
        System.out.println("Status:        " + redirectResp.statusCode());
        System.out.println("Redirects followed: " +
            (!redirectReq.uri().equals(redirectResp.uri()) ? "yes" : "no"));
    }
}
```

**How to run:** `java HeadersAndRedirects.java`

Expected output:
```
=== Outgoing Request ===
URI: https://httpbin.org/response-headers?X-Custom=Hello&X-Request-Id=12345
Custom headers:
  User-Agent: Java11HttpClient/1.0
  Accept-Language: en-US

=== Incoming Response ===
Status: 200
Final URI: https://httpbin.org/response-headers?X-Custom=Hello&X-Request-Id=12345

All response headers:
  date: [Wed, 09 Jul 2026 ...]
  content-type: [application/json]
  X-Custom: [Hello]
  X-Request-Id: [12345]
  ...

X-Custom header value: Hello

=== Redirect test ===
Original URI:  https://httpbin.org/redirect/2
Final URI:     https://httpbin.org/get
Status:        200
Redirects followed: yes
```

The real-world concern: custom request headers and redirect handling. `request.headers()` gives read access to the outgoing headers; `response.headers()` gives full access to response headers (case-insensitive). `response.uri()` may differ from `request.uri()` after redirects — always check the response URI for the final resource location.

### Level 3 — Advanced

```java
// File: HttpResponseTypes.java
import java.net.*;
import java.net.http.*;
import java.nio.file.*;
import java.io.*;
import java.util.*;

public class HttpResponseTypes {
    public static void main(String[] args) throws Exception {
        HttpClient client = HttpClient.newHttpClient();

        HttpRequest request = HttpRequest.newBuilder()
            .uri(URI.create("https://httpbin.org/bytes/1024"))
            .GET()
            .build();

        System.out.println("=== Different response body types ===\n");

        // 1. As String
        HttpResponse<String> stringResp = client.send(request,
            HttpResponse.BodyHandlers.ofString());
        System.out.println("String body length: " + stringResp.body().length());

        // 2. As byte[]
        HttpResponse<byte[]> bytesResp = client.send(request,
            HttpResponse.BodyHandlers.ofByteArray());
        System.out.println("Byte array length: " + bytesResp.body().length);

        // 3. As InputStream (lazy — you must close it)
        HttpResponse<InputStream> streamResp = client.send(request,
            HttpResponse.BodyHandlers.ofInputStream());
        try (InputStream is = streamResp.body()) {
            byte[] firstBytes = is.readNBytes(16);
            System.out.println("First 16 bytes via InputStream: " + Arrays.toString(firstBytes));
        }

        // 4. As file (downloaded to disk)
        Path tempFile = Path.of("download.bin");
        HttpResponse<Path> fileResp = client.send(request,
            HttpResponse.BodyHandlers.ofFile(tempFile));
        System.out.println("Downloaded to: " + fileResp.body());
        System.out.println("File size: " + Files.size(tempFile));

        // 5. Discarding body (for when you only care about status)
        HttpResponse<Void> voidResp = client.send(request,
            HttpResponse.BodyHandlers.discarding());
        System.out.println("Discarding handler — status: " + voidResp.statusCode());
        System.out.println("Body: " + voidResp.body());  // null

        // Clean up
        Files.deleteIfExists(tempFile);

        System.out.println("\n=== Immutability proof ===\n");
        // HttpRequest is immutable — you can inspect it after sending
        System.out.println("Request method after send: " + request.method());
        System.out.println("Request URI after send:    " + request.uri());
        System.out.println("(unchanged — HttpRequest is immutable)");
    }
}
```

**How to run:** `java HttpResponseTypes.java`

Expected output:
```
=== Different response body types ===

String body length: 1024
Byte array length: 1024
First 16 bytes via InputStream: [...]
Downloaded to: download.bin
File size: 1024
Discarding handler — status: 200
Body: null

=== Immutability proof ===

Request method after send: GET
Request URI after send:    https://httpbin.org/bytes/1024
(unchanged — HttpRequest is immutable)
```

The production-flavoured hard cases: (1) **Body type selection** — the `BodyHandler<T>` parameter at send-time determines the response body type. Choose `ofString()` for text/JSON, `ofByteArray()` for binary, `ofFile()` for large downloads, `ofInputStream()` for streaming, and `discarding()` when you only need the status code. (2) **Body consumption** — the body can typically be consumed only once. After calling `response.body()`, the stream is closed. (3) **Immutability** — `HttpRequest` is immutable; you can reuse the reference safely across threads and inspect it after sending.

## 6. Walkthrough

Tracing a complete request/response cycle:

1. **Build request:** `HttpRequest.newBuilder().uri(URI.create("https://httpbin.org/json")).GET().build()`
   - The builder validates the URI scheme (must be http/https)
   - `.GET()` sets the HTTP method (also the default)
   - `.build()` creates an immutable `HttpRequest` with method=GET, uri=https://httpbin.org/json, no custom headers, no body, default timeout

2. **Send request:** `client.send(request, BodyHandlers.ofString())`
   - The client opens a TCP+TLS connection to httpbin.org:443
   - The request is serialised to wire format:
     ```
     GET /json HTTP/1.1
     Host: httpbin.org
     User-Agent: Java-http-client/11
     Accept: */*
     
     ```
   - The server processes the request and returns:
     ```
     HTTP/1.1 200 OK
     Content-Type: application/json
     Content-Length: 429
     
     {"slideshow": {"title": "Sample Slide Show", ...}}
     ```
   - The client reads status line → `HttpResponse.statusCode()` = 200
   - Headers are parsed into an immutable `HttpHeaders` map
   - `BodyHandlers.ofString()` reads the 429-byte body, decodes as UTF-8 (from Content-Type charset), returns the String

3. **Inspect response:** `response.statusCode()`, `response.headers()`, `response.body()`
   - Status code: 200 (success)
   - Headers: `{Content-Type: [application/json], Content-Length: [429], ...}`
   - Body: the JSON string `{"slideshow": {...}}`

The data flows through clear, typed boundaries: `URI string → URI → HttpRequest → bytes on wire → HttpResponse<T> → T (String/byte[]/Path/etc)`.

## 7. Gotchas & takeaways

> `HttpResponse.body()` can typically be called **only once** — the underlying stream is consumed and closed. For `ofString()` and `ofByteArray()`, the body is cached in memory so you can call `.body()` multiple times safely. But for `ofInputStream()`, the stream is stateful and must be managed. Always check the `BodyHandler` documentation for consumption semantics.

- `HttpRequest` is immutable — you cannot modify it after `.build()`. To send a similar request with one field changed, build a new request from a new builder. The builder is not reusable either — call `.build()` exactly once per builder.
- `HttpResponse.uri()` may differ from `HttpRequest.uri()` when redirects are followed. Always compare or use the response URI for subsequent requests to avoid redirect loops.
- `request.headers()` returns the outgoing headers (you set them). `response.headers()` returns incoming headers (server set them). Both are case-insensitive maps — `firstValue("content-type")` works regardless of capitalisation.
- For large responses, use `BodyHandlers.ofFile()` or `ofInputStream()` to avoid loading the entire body into memory. For small JSON/XML responses, `ofString()` is the simplest.
- `HttpRequest` and `HttpResponse` are interfaces (not classes) — the JDK provides internal implementations. This allows future JDK versions to evolve the implementation without breaking API compatibility.

---
card: java
gi: 331
slug: url-urlconnection
title: URL & URLConnection
---

## 1. What it is

`java.net.URL` parses and represents a Uniform Resource Locator (scheme, host, port, path, query string), and `java.net.URLConnection` is the object that actually performs the network operation described by that URL — opening a connection to the resource, reading its response, and exposing headers and metadata. `url.openConnection()` returns a `URLConnection` without yet talking to the network; the connection is only actually made lazily, the first time you call something that needs it, like `getInputStream()`.

```java
import java.io.*;
import java.net.URL;
import java.net.URLConnection;

public class UrlDemo {
    public static void main(String[] args) throws IOException {
        URL url = new URL("https://example.com");
        URLConnection connection = url.openConnection(); // not connected yet
        try (BufferedReader reader = new BufferedReader(
                new InputStreamReader(connection.getInputStream()))) { // connects here
            String firstLine = reader.readLine();
            System.out.println("First line: " + firstLine);
        }
    }
}
```

`new URL(...)` only parses the string into its components; `openConnection()` prepares (but doesn't yet execute) the request; `getInputStream()` is what actually triggers the network round trip.

## 2. Why & when

Before dedicated HTTP client libraries (and even today, for quick scripts or simple fetches), `URL`/`URLConnection` is the JDK's built-in way to fetch a remote resource without adding any external dependency — it handles the underlying socket, protocol negotiation, and response parsing for `http`, `https`, `file`, and other registered URL schemes.

- **Quick one-off fetches** — reading a remote text file, a simple API response, or checking a resource's metadata (like its content length or last-modified date) without pulling in a full HTTP client library.
- **Parsing and manipulating URL components** — `URL` exposes `getHost()`, `getPath()`, `getQuery()`, `getPort()`, etc., useful for validating or rewriting URLs even when you don't intend to open a connection at all.
- **Configuring low-level request behavior** — timeouts, request headers (via the `HttpURLConnection` subclass), and redirect-following are all controlled through `URLConnection` before the connection is actually made.

For anything beyond simple fetches — connection pooling, async requests, HTTP/2, more ergonomic error handling — a modern dedicated client (like Java's own `java.net.http.HttpClient`, introduced in Java 11) is usually a better choice; `URL`/`URLConnection` remains useful as a dependency-free baseline and because it underlies much of the older Java networking ecosystem.

## 3. Core concept

```java
import java.io.*;
import java.net.URL;
import java.net.URLConnection;

public class UrlCore {
    public static void main(String[] args) throws IOException {
        URL url = new URL("https://example.com/path?query=1");
        System.out.println("Host: " + url.getHost());
        System.out.println("Path: " + url.getPath());
        System.out.println("Query: " + url.getQuery());
        System.out.println("Protocol: " + url.getProtocol());

        URLConnection connection = url.openConnection();
        connection.setConnectTimeout(3000);
        connection.setReadTimeout(3000);
        System.out.println("Content-Type header (after connecting): " + connection.getContentType());
    }
}
```

**How to run:** `java UrlCore.java`

Reading `getContentType()` forces the connection to actually be established (since the content type comes from a response header), which is why timeouts are set beforehand — once the network call begins, those settings can no longer be changed.

## 4. Diagram

<svg viewBox="0 0 620 150" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="URL parses the address; openConnection prepares a request; getInputStream triggers the actual network call">
  <rect x="8" y="8" width="604" height="134" rx="8" fill="#0d1117"/>
  <rect x="20" y="30" width="160" height="40" rx="6" fill="#1c2430" stroke="#79c0ff"/>
  <text x="100" y="55" fill="#79c0ff" font-size="10" text-anchor="middle">new URL(string)</text>

  <rect x="220" y="30" width="180" height="40" rx="6" fill="#1c2430" stroke="#8b949e"/>
  <text x="310" y="55" fill="#8b949e" font-size="10" text-anchor="middle">openConnection() -- not sent yet</text>

  <rect x="440" y="30" width="160" height="40" rx="6" fill="#1c2430" stroke="#6db33f"/>
  <text x="520" y="55" fill="#6db33f" font-size="10" text-anchor="middle">getInputStream() -- connects</text>

  <text x="20" y="105" fill="#8b949e" font-size="9">Parsing, preparing, and connecting are three distinct, separately-timed steps.</text>
</svg>

## 5. Runnable example

Scenario: fetching a small local HTTP resource, evolved from a bare fetch with no error or timeout handling, into one with proper timeouts and status-code checking, into a production-style fetch that reads response headers and handles redirects and error codes distinctly.

### Level 1 — Basic

```java
import java.io.*;
import java.net.URL;
import java.net.URLConnection;
import com.sun.net.httpserver.HttpServer;
import java.net.InetSocketAddress;

public class UrlFetchBasic {
    public static void main(String[] args) throws Exception {
        HttpServer server = startLocalServer();
        int port = server.getAddress().getPort();

        URL url = new URL("http://localhost:" + port + "/hello");
        URLConnection connection = url.openConnection();
        try (BufferedReader reader = new BufferedReader(new InputStreamReader(connection.getInputStream()))) {
            System.out.println("Body: " + reader.readLine());
        }
        server.stop(0);
    }

    static HttpServer startLocalServer() throws IOException {
        HttpServer server = HttpServer.create(new InetSocketAddress(0), 0);
        server.createContext("/hello", exchange -> {
            byte[] body = "Hello from local server".getBytes();
            exchange.sendResponseHeaders(200, body.length);
            exchange.getResponseBody().write(body);
            exchange.getResponseBody().close();
        });
        server.start();
        return server;
    }
}
```

**How to run:** `java UrlFetchBasic.java`

This fetches the body successfully but sets no timeouts and checks no status code — if the server hung or returned an error page, this code would either block indefinitely or happily print an error page's HTML as if it were a normal response.

### Level 2 — Intermediate

```java
import java.io.*;
import java.net.URL;
import java.net.HttpURLConnection;
import com.sun.net.httpserver.HttpServer;
import java.net.InetSocketAddress;

public class UrlFetchIntermediate {
    public static void main(String[] args) throws Exception {
        HttpServer server = startLocalServer();
        int port = server.getAddress().getPort();

        URL url = new URL("http://localhost:" + port + "/hello");
        HttpURLConnection connection = (HttpURLConnection) url.openConnection();
        connection.setConnectTimeout(2000);
        connection.setReadTimeout(2000);

        int status = connection.getResponseCode();
        if (status == 200) {
            try (BufferedReader reader = new BufferedReader(new InputStreamReader(connection.getInputStream()))) {
                System.out.println("Body: " + reader.readLine());
            }
        } else {
            System.out.println("Unexpected status: " + status);
        }
        server.stop(0);
    }

    static HttpServer startLocalServer() throws IOException {
        HttpServer server = HttpServer.create(new InetSocketAddress(0), 0);
        server.createContext("/hello", exchange -> {
            byte[] body = "Hello from local server".getBytes();
            exchange.sendResponseHeaders(200, body.length);
            exchange.getResponseBody().write(body);
            exchange.getResponseBody().close();
        });
        server.start();
        return server;
    }
}
```

**How to run:** `java UrlFetchIntermediate.java`

Casting to `HttpURLConnection` exposes `getResponseCode()`, so the code checks the status explicitly before trusting the body, and both timeouts are set before any network call is triggered — a hung server now fails with a timeout exception instead of blocking forever.

### Level 3 — Advanced

```java
import java.io.*;
import java.net.URL;
import java.net.HttpURLConnection;
import com.sun.net.httpserver.HttpServer;
import java.net.InetSocketAddress;

public class UrlFetchAdvanced {
    public static void main(String[] args) throws Exception {
        HttpServer server = startLocalServer();
        int port = server.getAddress().getPort();

        System.out.println("Fetching /hello:");
        fetch("http://localhost:" + port + "/hello");
        System.out.println("Fetching /missing:");
        fetch("http://localhost:" + port + "/missing");

        server.stop(0);
    }

    static void fetch(String urlString) throws IOException {
        HttpURLConnection connection = (HttpURLConnection) new URL(urlString).openConnection();
        connection.setConnectTimeout(2000);
        connection.setReadTimeout(2000);
        connection.setInstanceFollowRedirects(true);

        int status = connection.getResponseCode();
        System.out.println("  Status: " + status);
        System.out.println("  Content-Type: " + connection.getContentType());

        InputStream stream = (status >= 200 && status < 300)
                ? connection.getInputStream()
                : connection.getErrorStream(); // 4xx/5xx bodies come from a DIFFERENT stream
        if (stream != null) {
            try (BufferedReader reader = new BufferedReader(new InputStreamReader(stream))) {
                System.out.println("  Body: " + reader.readLine());
            }
        }
        connection.disconnect();
    }

    static HttpServer startLocalServer() throws IOException {
        HttpServer server = HttpServer.create(new InetSocketAddress(0), 0);
        server.createContext("/hello", exchange -> {
            byte[] body = "Hello from local server".getBytes();
            exchange.sendResponseHeaders(200, body.length);
            exchange.getResponseBody().write(body);
            exchange.getResponseBody().close();
        });
        server.createContext("/missing", exchange -> {
            byte[] body = "Not Found".getBytes();
            exchange.sendResponseHeaders(404, body.length);
            exchange.getResponseBody().write(body);
            exchange.getResponseBody().close();
        });
        server.start();
        return server;
    }
}
```

**How to run:** `java UrlFetchAdvanced.java`

The key production-relevant detail here is that `getInputStream()` throws `IOException` for non-2xx status codes — the actual error body must instead be read from `getErrorStream()` — so `fetch` branches on the status code to pick the correct stream, and always calls `connection.disconnect()` afterward to release the underlying connection back to the connection pool/cache.

## 6. Walkthrough

Execution starts in `main`: it starts a local `HttpServer` with two routes (`/hello` returning 200, `/missing` returning 404), then calls `fetch` for each in turn.

For `fetch("http://localhost:PORT/hello")`: `new URL(...)` parses the string; `openConnection()` returns an unconnected `HttpURLConnection`; timeouts and redirect-following are configured. Calling `connection.getResponseCode()` is what actually triggers the request — the JVM opens a TCP socket to the server, sends an HTTP GET request line and headers, and waits for the response. The local server's `/hello` handler runs, calling `exchange.sendResponseHeaders(200, body.length)` (writing the status line and headers) followed by writing the body bytes — this is the complete HTTP response: status `200`, a `Content-Type` header, and the body `"Hello from local server"`.

Back in `fetch`, `getResponseCode()` returns `200`, which is printed, then `getContentType()` reads the already-received header. Since `status` is in the 200–299 range, `stream` is set from `connection.getInputStream()`, and the body line is read and printed. `connection.disconnect()` releases the connection.

For `fetch("http://localhost:PORT/missing")`: the same sequence runs, but the server's `/missing` handler sends status `404` with body `"Not Found"`. This time, `getResponseCode()` returns `404` — outside the 2xx range — so `stream` is set from `connection.getErrorStream()` instead; calling `getInputStream()` here would have thrown an `IOException`, since `HttpURLConnection` treats non-2xx responses as connection failures for that specific method. The error body `"Not Found"` is read and printed via the correct stream.

<svg viewBox="0 0 640 180" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="request flows from URL parsing through connection setup to the actual HTTP call, then branches on status code to pick the correct response stream">
  <rect x="8" y="8" width="624" height="164" rx="8" fill="#0d1117"/>
  <text x="20" y="30" fill="#79c0ff" font-size="10">new URL(...) -&gt; openConnection() -&gt; set timeouts (no network yet)</text>
  <text x="20" y="55" fill="#79c0ff" font-size="10">getResponseCode() -&gt; TCP connect + HTTP GET sent -&gt; server handler runs</text>
  <text x="20" y="80" fill="#6db33f" font-size="10">GET /hello  -&gt; 200 + body           -&gt; use getInputStream()</text>
  <text x="20" y="102" fill="#f85149" font-size="10">GET /missing -&gt; 404 + body          -&gt; use getErrorStream() instead</text>
  <text x="20" y="130" fill="#8b949e" font-size="10">getInputStream() on a 4xx/5xx response throws IOException -- must branch on status first</text>
  <text x="20" y="152" fill="#8b949e" font-size="10">disconnect() releases the underlying connection after each fetch</text>
</svg>

## 7. Gotchas & takeaways

> Calling `getInputStream()` on a connection that returned a 4xx or 5xx status throws `IOException` instead of giving you the error page's body — you must check `getResponseCode()` first and read `getErrorStream()` for non-2xx responses.

- `openConnection()` never touches the network by itself — the connection is made lazily, the first time something like `getInputStream()` or `getResponseCode()` is called.
- Set timeouts (`setConnectTimeout`, `setReadTimeout`) before triggering the connection — once the request is underway, these settings can no longer be applied.
- Cast to `HttpURLConnection` to access HTTP-specific features: status codes, request methods, headers, and redirect control.
- Always call `disconnect()` (or fully consume and close the stream) when done, so the underlying connection can be reused or released rather than leaked.
- For anything beyond simple fetches, prefer a modern HTTP client (`java.net.http.HttpClient` or a third-party library) — `URLConnection`'s API is dated and its error-handling quirks (like the input/error stream split) are easy to miss.

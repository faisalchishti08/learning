---
card: java
gi: 332
slug: httpurlconnection
title: HttpURLConnection
---

## 1. What it is

`HttpURLConnection` is the HTTP-specific subclass of `URLConnection`, obtained by casting the result of `url.openConnection()` when the URL's scheme is `http` or `https`. It adds everything generic `URLConnection` doesn't have: setting the HTTP method (`GET`, `POST`, `PUT`, `DELETE`, ...), writing a request body, reading the numeric status code, and reading/setting individual request and response headers.

```java
import java.io.*;
import java.net.HttpURLConnection;
import java.net.URL;

public class HttpUrlConnectionDemo {
    public static void main(String[] args) throws IOException {
        URL url = new URL("https://example.com");
        HttpURLConnection connection = (HttpURLConnection) url.openConnection();
        connection.setRequestMethod("GET");
        System.out.println("Status: " + connection.getResponseCode());
        connection.disconnect();
    }
}
```

`setRequestMethod("GET")` must be called before the connection is made (before reading the response), since it configures what request will actually be sent.

## 2. Why & when

Whenever a Java program needs to send more than a plain `GET` — submitting form data, posting JSON to a REST API, setting custom headers like `Authorization` or `Content-Type` — the generic `URLConnection` isn't enough, because it has no concept of an HTTP method or a request body; `HttpURLConnection` is the layer that adds those HTTP-specific capabilities.

- **Calling a REST API that requires POST/PUT with a JSON body** — setting the method, setting `Content-Type: application/json`, writing the JSON bytes to the connection's output stream.
- **Sending authentication or custom headers** — `setRequestProperty("Authorization", "Bearer ...")` and similar calls attach headers to the outgoing request.
- **Inspecting response headers and status precisely** — `getResponseCode()`, `getHeaderField(name)`, and `getHeaderFields()` expose exactly what the server sent back, needed for anything beyond just reading the body.

`HttpURLConnection` predates modern fluent HTTP clients and has some rough edges (the input/error stream split, the need to call `setDoOutput(true)` before writing a body), but it remains dependency-free and is still what many older codebases and libraries use under the hood.

## 3. Core concept

```java
import java.io.*;
import java.net.HttpURLConnection;
import java.net.URL;
import java.nio.charset.StandardCharsets;

public class HttpUrlConnectionCore {
    public static void main(String[] args) throws IOException {
        URL url = new URL("https://httpbin.org/post");
        HttpURLConnection connection = (HttpURLConnection) url.openConnection();
        connection.setRequestMethod("POST");
        connection.setRequestProperty("Content-Type", "application/json");
        connection.setDoOutput(true); // required before writing a request body

        String json = "{\"name\":\"Ada\"}";
        try (OutputStream os = connection.getOutputStream()) {
            os.write(json.getBytes(StandardCharsets.UTF_8));
        }

        System.out.println("Status: " + connection.getResponseCode());
        connection.disconnect();
    }
}
```

**How to run:** `java HttpUrlConnectionCore.java` (requires internet access to httpbin.org)

`setDoOutput(true)` tells the connection it must be prepared to send a request body; without it, calling `getOutputStream()` throws an exception, because by default `HttpURLConnection` assumes no body is being sent (as with a plain `GET`).

## 4. Diagram

<svg viewBox="0 0 600 160" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="configure method, headers, and body before connecting; then read status code, headers, and body after">
  <rect x="8" y="8" width="584" height="144" rx="8" fill="#0d1117"/>
  <text x="20" y="30" fill="#79c0ff" font-size="10">Before connecting: setRequestMethod, setRequestProperty(headers), setDoOutput, write body</text>
  <rect x="20" y="45" width="250" height="30" rx="6" fill="#1c2430" stroke="#79c0ff"/>
  <text x="145" y="65" fill="#79c0ff" font-size="9" text-anchor="middle">request configuration phase</text>

  <text x="290" y="65" fill="#8b949e" font-size="14">→</text>

  <rect x="320" y="45" width="250" height="30" rx="6" fill="#1c2430" stroke="#6db33f"/>
  <text x="445" y="65" fill="#6db33f" font-size="9" text-anchor="middle">connection triggered (first blocking call)</text>

  <text x="20" y="110" fill="#8b949e" font-size="10">After connecting: getResponseCode, getHeaderField, getInputStream/getErrorStream</text>
</svg>

## 5. Runnable example

Scenario: submitting form-like data to a local test server, evolved from a plain unauthenticated POST with no error handling, into one that sets a custom header and checks the status code, into a production-style client that handles both success and error responses and reads response headers.

### Level 1 — Basic

```java
import java.io.*;
import java.net.HttpURLConnection;
import java.net.URL;
import java.net.InetSocketAddress;
import com.sun.net.httpserver.HttpServer;
import java.nio.charset.StandardCharsets;

public class HttpPostBasic {
    public static void main(String[] args) throws Exception {
        HttpServer server = startLocalServer();
        int port = server.getAddress().getPort();

        URL url = new URL("http://localhost:" + port + "/submit");
        HttpURLConnection connection = (HttpURLConnection) url.openConnection();
        connection.setRequestMethod("POST");
        connection.setDoOutput(true);
        try (OutputStream os = connection.getOutputStream()) {
            os.write("name=Ada".getBytes(StandardCharsets.UTF_8));
        }

        try (BufferedReader reader = new BufferedReader(new InputStreamReader(connection.getInputStream()))) {
            System.out.println("Response: " + reader.readLine());
        }
        server.stop(0);
    }

    static HttpServer startLocalServer() throws IOException {
        HttpServer server = HttpServer.create(new InetSocketAddress(0), 0);
        server.createContext("/submit", exchange -> {
            byte[] body = ("received: " + new String(exchange.getRequestBody().readAllBytes())).getBytes();
            exchange.sendResponseHeaders(200, body.length);
            exchange.getResponseBody().write(body);
            exchange.getResponseBody().close();
        });
        server.start();
        return server;
    }
}
```

**How to run:** `java HttpPostBasic.java`

This sends a POST body and reads the response, but has no status check and no headers set — it assumes the server always succeeds and never needs to identify the content type of the body being sent.

### Level 2 — Intermediate

```java
import java.io.*;
import java.net.HttpURLConnection;
import java.net.URL;
import java.net.InetSocketAddress;
import com.sun.net.httpserver.HttpServer;
import java.nio.charset.StandardCharsets;

public class HttpPostIntermediate {
    public static void main(String[] args) throws Exception {
        HttpServer server = startLocalServer();
        int port = server.getAddress().getPort();

        URL url = new URL("http://localhost:" + port + "/submit");
        HttpURLConnection connection = (HttpURLConnection) url.openConnection();
        connection.setRequestMethod("POST");
        connection.setRequestProperty("Content-Type", "application/x-www-form-urlencoded");
        connection.setRequestProperty("X-Client", "HttpPostIntermediate-demo");
        connection.setDoOutput(true);
        try (OutputStream os = connection.getOutputStream()) {
            os.write("name=Ada".getBytes(StandardCharsets.UTF_8));
        }

        int status = connection.getResponseCode();
        if (status == 200) {
            try (BufferedReader reader = new BufferedReader(new InputStreamReader(connection.getInputStream()))) {
                System.out.println("Response: " + reader.readLine());
            }
        } else {
            System.out.println("Request failed with status " + status);
        }
        server.stop(0);
    }

    static HttpServer startLocalServer() throws IOException {
        HttpServer server = HttpServer.create(new InetSocketAddress(0), 0);
        server.createContext("/submit", exchange -> {
            String clientHeader = exchange.getRequestHeaders().getFirst("X-Client");
            byte[] body = ("received from " + clientHeader + ": "
                    + new String(exchange.getRequestBody().readAllBytes())).getBytes();
            exchange.sendResponseHeaders(200, body.length);
            exchange.getResponseBody().write(body);
            exchange.getResponseBody().close();
        });
        server.start();
        return server;
    }
}
```

**How to run:** `java HttpPostIntermediate.java`

Now a `Content-Type` header correctly describes the body format, a custom `X-Client` header is attached (and the server reads it back), and the status code is checked before trusting the response body — a request that failed server-side would now be reported instead of silently mishandled.

### Level 3 — Advanced

```java
import java.io.*;
import java.net.HttpURLConnection;
import java.net.URL;
import java.net.InetSocketAddress;
import com.sun.net.httpserver.HttpServer;
import java.nio.charset.StandardCharsets;

public class HttpPostAdvanced {
    public static void main(String[] args) throws Exception {
        HttpServer server = startLocalServer();
        int port = server.getAddress().getPort();

        submit("http://localhost:" + port + "/submit", "name=Ada");
        submit("http://localhost:" + port + "/submit", "name=BAD"); // triggers server-side validation error

        server.stop(0);
    }

    static void submit(String urlString, String formBody) throws IOException {
        HttpURLConnection connection = (HttpURLConnection) new URL(urlString).openConnection();
        connection.setRequestMethod("POST");
        connection.setRequestProperty("Content-Type", "application/x-www-form-urlencoded");
        connection.setConnectTimeout(2000);
        connection.setReadTimeout(2000);
        connection.setDoOutput(true);
        try (OutputStream os = connection.getOutputStream()) {
            os.write(formBody.getBytes(StandardCharsets.UTF_8));
        }

        int status = connection.getResponseCode();
        System.out.println("POST " + formBody + " -> status " + status
                + ", Content-Length header: " + connection.getHeaderField("Content-Length"));

        InputStream stream = (status >= 200 && status < 300)
                ? connection.getInputStream()
                : connection.getErrorStream();
        try (BufferedReader reader = new BufferedReader(new InputStreamReader(stream))) {
            System.out.println("  Body: " + reader.readLine());
        }
        connection.disconnect();
    }

    static HttpServer startLocalServer() throws IOException {
        HttpServer server = HttpServer.create(new InetSocketAddress(0), 0);
        server.createContext("/submit", exchange -> {
            String requestBody = new String(exchange.getRequestBody().readAllBytes());
            byte[] responseBody;
            int status;
            if (requestBody.contains("BAD")) {
                status = 400;
                responseBody = "Invalid name".getBytes();
            } else {
                status = 200;
                responseBody = ("received: " + requestBody).getBytes();
            }
            exchange.sendResponseHeaders(status, responseBody.length);
            exchange.getResponseBody().write(responseBody);
            exchange.getResponseBody().close();
        });
        server.start();
        return server;
    }
}
```

**How to run:** `java HttpPostAdvanced.java`

The `submit` helper sets connect/read timeouts, reads a specific response header (`Content-Length`) via `getHeaderField`, and correctly branches between `getInputStream()` and `getErrorStream()` based on the status code — demonstrated concretely by the second call, whose `"name=BAD"` body triggers the server's validation logic to return `400` with an error body that must be read from `getErrorStream()`.

## 6. Walkthrough

Execution starts in `main`, which starts a local server with one `/submit` route that validates the request body, then calls `submit` twice.

**First call — `submit(url, "name=Ada")`:** a `HttpURLConnection` is configured for `POST` with a `Content-Type` header, `setDoOutput(true)`, and timeouts; then `connection.getOutputStream()` opens the request body stream and the code writes `"name=Ada"` into it. Calling `connection.getResponseCode()` is the moment the actual HTTP request is sent: `POST /submit HTTP/1.1` with header `Content-Type: application/x-www-form-urlencoded` and body `name=Ada`. On the server, the handler reads the full request body via `readAllBytes()`, sees it does not contain `"BAD"`, and responds with status `200` and body `"received: name=Ada"`.

Back in `submit`, `getResponseCode()` returns `200`; `getHeaderField("Content-Length")` reads that response header directly. Since `status` is in the 2xx range, `stream` is set from `getInputStream()`, and the body line `"received: name=Ada"` is printed.

**Second call — `submit(url, "name=BAD")`:** the same request/response cycle runs, but this time the server's validation sees `"BAD"` in the body and responds with status `400` and body `"Invalid name"`. Back in `submit`, `getResponseCode()` returns `400` — outside the 2xx range — so `stream` is set from `connection.getErrorStream()` instead of `getInputStream()` (calling `getInputStream()` here would throw `IOException`, since `HttpURLConnection` treats 4xx as a connection-level failure for that method). The error body `"Invalid name"` is read and printed correctly.

<svg viewBox="0 0 640 190" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="request body flows from client through connection to server handler, validation branches the response status, and client picks input or error stream accordingly">
  <rect x="8" y="8" width="624" height="174" rx="8" fill="#0d1117"/>
  <text x="20" y="30" fill="#79c0ff" font-size="10">client: write "name=Ada" to output stream -&gt; POST sent with Content-Type header</text>
  <text x="20" y="55" fill="#6db33f" font-size="10">server: readAllBytes() -&gt; no "BAD" -&gt; 200 + "received: name=Ada"</text>
  <text x="20" y="77" fill="#79c0ff" font-size="10">client: status 200 -&gt; getInputStream() -&gt; prints body</text>
  <text x="20" y="105" fill="#79c0ff" font-size="10">client: write "name=BAD" to output stream -&gt; POST sent</text>
  <text x="20" y="130" fill="#f85149" font-size="10">server: readAllBytes() -&gt; contains "BAD" -&gt; 400 + "Invalid name"</text>
  <text x="20" y="152" fill="#f85149" font-size="10">client: status 400 -&gt; getErrorStream() (NOT getInputStream) -&gt; prints error body</text>
</svg>

## 7. Gotchas & takeaways

> Forgetting `setDoOutput(true)` before writing a request body causes `getOutputStream()` to throw `ProtocolException` — by default, `HttpURLConnection` assumes no request body will be sent.

- Set the request method, headers, and `setDoOutput(true)` *before* writing the body or reading the response — once the request is triggered, these can't be changed.
- Use `getInputStream()` only for successful (2xx) responses; use `getErrorStream()` for 4xx/5xx responses, checking `getResponseCode()` first to know which one applies.
- `setRequestProperty(name, value)` sets a request header; `getHeaderField(name)` reads a response header — don't confuse the two directions.
- Always set `setConnectTimeout`/`setReadTimeout` for any request that isn't guaranteed to hit a fast, trusted, local service.
- Call `disconnect()` when finished so the underlying TCP connection is released (or returned to the connection cache) rather than left open indefinitely.

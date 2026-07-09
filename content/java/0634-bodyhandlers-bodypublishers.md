---
card: java
gi: 634
slug: bodyhandlers-bodypublishers
title: BodyHandlers / BodyPublishers
---

## 1. What it is

`BodyHandlers` and `BodyPublishers` are **factory classes** in `java.net.http` that produce handlers for response bodies and publishers for request bodies, respectively. `BodyHandlers` provides static methods that convert raw HTTP response bytes into usable Java types: `ofString()`, `ofByteArray()`, `ofFile(Path)`, `ofInputStream()`, `ofLines()`, `discarding()`, and more. `BodyPublishers` provides static methods that convert Java objects into HTTP request body bytes: `ofString(String)`, `ofByteArray(byte[])`, `ofFile(Path)`, `ofInputStream(Supplier)`, `noBody()`, and more. Together they handle the serialisation/deserialisation boundary between your Java code and the HTTP wire format.

## 2. Why & when

In the old `HttpURLConnection` API, sending a request body meant writing to an `OutputStream` manually, and reading a response meant wrapping an `InputStream` in a `BufferedReader` — boilerplate code that mixed I/O management with business logic. `BodyPublishers` and `BodyHandlers` encapsulate these conversions into reusable, composable components. Use the built-in factories for common cases (`ofString`, `ofByteArray`, `ofFile`). Implement `BodyHandler<T>` or `BodyPublisher` yourself when you need custom serialisation (e.g. JSON via Jackson, XML via JAXB, or streaming large multipart uploads).

## 3. Core concept

```java
// ---- BodyPublishers (request body) ----
HttpRequest.BodyPublishers.ofString("{\"name\":\"Alice\"}");    // JSON string
HttpRequest.BodyPublishers.ofByteArray(new byte[]{1, 2, 3});        // raw bytes
HttpRequest.BodyPublishers.ofFile(Path.of("data.json"));             // file contents
HttpRequest.BodyPublishers.noBody();                                 // no body (GET, DELETE)

// ---- BodyHandlers (response body) ----
HttpResponse.BodyHandlers.ofString();                  // body → String
HttpResponse.BodyHandlers.ofByteArray();               // body → byte[]
HttpResponse.BodyHandlers.ofFile(Path.of("out.bin"));  // body → saved file
HttpResponse.BodyHandlers.ofLines();                   // body → Stream<String> of lines
HttpResponse.BodyHandlers.ofInputStream();             // body → InputStream (lazy)
HttpResponse.BodyHandlers.discarding();                // body → Void (ignored)
```

Both are factory classes with only static methods — you never instantiate them.

## 4. Diagram

<svg viewBox="0 0 580 160" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="BodyPublishers convert Java types to request bytes; BodyHandlers convert response bytes to Java types">
  <rect x="10" y="10" width="560" height="140" rx="8" fill="#1c2430" stroke="#6db33f"/>

  <text x="30" y="35" fill="#8b949e" font-size="10" font-family="sans-serif" font-weight="bold">Request side (outgoing)</text>
  <rect x="30" y="45" width="150" height="35" rx="4" fill="#0d1117" stroke="#79c0ff"/>
  <text x="105" y="60" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="monospace">String / byte[] / Path</text>
  <text x="105" y="74" fill="#8b949e" font-size="7" text-anchor="middle" font-family="monospace">(your Java object)</text>
  <text x="190" y="65" fill="#8b949e" font-size="14" font-family="monospace" text-anchor="middle">→</text>
  <rect x="205" y="45" width="130" height="35" rx="4" fill="#6db33f" stroke="#6db33f"/>
  <text x="270" y="60" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="monospace">BodyPublisher</text>
  <text x="270" y="74" fill="#8b949e" font-size="7" text-anchor="middle" font-family="monospace">(converts to bytes)</text>
  <text x="345" y="65" fill="#8b949e" font-size="14" font-family="monospace" text-anchor="middle">→</text>
  <text x="360" y="65" fill="#8b949e" font-size="9" font-family="monospace">HTTP request body</text>

  <text x="30" y="105" fill="#8b949e" font-size="10" font-family="sans-serif" font-weight="bold">Response side (incoming)</text>
  <rect x="30" y="115" width="130" height="35" rx="4" fill="#0d1117" stroke="#3fb950"/>
  <text x="95" y="130" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="monospace">HTTP response bytes</text>
  <text x="170" y="135" fill="#8b949e" font-size="14" font-family="monospace" text-anchor="middle">→</text>
  <rect x="185" y="115" width="130" height="35" rx="4" fill="#6db33f" stroke="#6db33f"/>
  <text x="250" y="130" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="monospace">BodyHandler&lt;T&gt;</text>
  <text x="250" y="144" fill="#8b949e" font-size="7" text-anchor="middle" font-family="monospace">(converts bytes to T)</text>
  <text x="325" y="135" fill="#8b949e" font-size="14" font-family="monospace" text-anchor="middle">→</text>
  <rect x="340" y="115" width="150" height="35" rx="4" fill="#0d1117" stroke="#3fb950"/>
  <text x="415" y="130" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="monospace">String / byte[] / Path</text>
  <text x="415" y="144" fill="#8b949e" font-size="7" text-anchor="middle" font-family="monospace">(your Java type)</text>
</svg>

`BodyPublishers` and `BodyHandlers` are symmetric: one converts Java → HTTP bytes (request), the other converts HTTP bytes → Java (response). Both are used as arguments to `HttpRequest` builder and `HttpClient.send()` respectively.

## 5. Runnable example

Scenario: building a file-upload and download service that sends and receives various content types — starting with basic string body publishing/handling, extending to file upload/download, and finally handling streaming and custom body types.

### Level 1 — Basic

```java
// File: BodyHandlersDemo.java
import java.net.*;
import java.net.http.*;
import java.nio.charset.*;

public class BodyHandlersDemo {
    public static void main(String[] args) throws Exception {
        HttpClient client = HttpClient.newHttpClient();

        // POST with string body (BodyPublishers.ofString)
        String jsonPayload = "{\"message\": \"Hello from Java 11\"}";
        HttpRequest postRequest = HttpRequest.newBuilder()
            .uri(URI.create("https://httpbin.org/post"))
            .header("Content-Type", "application/json")
            .POST(HttpRequest.BodyPublishers.ofString(jsonPayload))
            .build();

        // Response body as String (BodyHandlers.ofString)
        HttpResponse<String> response = client.send(postRequest,
            HttpResponse.BodyHandlers.ofString());

        System.out.println("Status: " + response.statusCode());
        System.out.println("Body (truncated):");
        System.out.println(response.body().substring(0,
            Math.min(200, response.body().length())));
    }
}
```

**How to run:** `java BodyHandlersDemo.java`

Expected output:
```
Status: 200
Body (truncated):
{
  "data": "{\"message\": \"Hello from Java 11\"}",
  "json": {"message": "Hello from Java 11"},
  ...
}
```

The simplest usage: `BodyPublishers.ofString()` sends a string as the request body; `BodyHandlers.ofString()` reads the response body as a string. The symmetry is intentional.

### Level 2 — Intermediate

```java
// File: FileUploadDownload.java
import java.net.*;
import java.net.http.*;
import java.nio.file.*;
import java.io.*;

public class FileUploadDownload {
    public static void main(String[] args) throws Exception {
        HttpClient client = HttpClient.newHttpClient();

        // Create a sample file to upload
        Path uploadFile = Path.of("upload-data.txt");
        Files.writeString(uploadFile, "Sample data for upload\nLine 2\nLine 3");

        System.out.println("=== File upload ===");
        System.out.println("Uploading: " + uploadFile + " (" + Files.size(uploadFile) + " bytes)");

        // Upload file (BodyPublishers.ofFile)
        HttpRequest uploadRequest = HttpRequest.newBuilder()
            .uri(URI.create("https://httpbin.org/post"))
            .POST(HttpRequest.BodyPublishers.ofFile(uploadFile))
            .build();

        HttpResponse<String> uploadResponse = client.send(uploadRequest,
            HttpResponse.BodyHandlers.ofString());

        System.out.println("Upload status: " + uploadResponse.statusCode());

        System.out.println("\n=== File download ===");

        // Download to file (BodyHandlers.ofFile)
        Path downloadPath = Path.of("download-result.bin");
        HttpRequest downloadRequest = HttpRequest.newBuilder()
            .uri(URI.create("https://httpbin.org/bytes/512"))
            .GET()
            .build();

        HttpResponse<Path> downloadResponse = client.send(downloadRequest,
            HttpResponse.BodyHandlers.ofFile(downloadPath));

        System.out.println("Downloaded to: " + downloadResponse.body());
        System.out.println("File size: " + Files.size(downloadPath) + " bytes");
        System.out.println("Status: " + downloadResponse.statusCode());

        // Read first few bytes of downloaded file
        byte[] preview = Files.readAllBytes(downloadPath);
        System.out.println("First 10 bytes: " +
            java.util.Arrays.toString(java.util.Arrays.copyOf(preview, 10)));

        // Clean up
        Files.deleteIfExists(uploadFile);
        Files.deleteIfExists(downloadPath);
    }
}
```

**How to run:** `java FileUploadDownload.java`

Expected output:
```
=== File upload ===
Uploading: upload-data.txt (31 bytes)
Upload status: 200

=== File download ===
Downloaded to: download-result.bin
File size: 512 bytes
Status: 200
First 10 bytes: [...]
```

The real-world concern: file transfer. `BodyPublishers.ofFile()` streams a file's contents as the request body without loading it entirely into memory. `BodyHandlers.ofFile()` streams the response directly to disk. Both are essential for large file operations.

### Level 3 — Advanced

```java
// File: BodyHandlersAdvanced.java
import java.net.*;
import java.net.http.*;
import java.nio.file.*;
import java.util.*;
import java.util.stream.*;
import java.io.*;

public class BodyHandlersAdvanced {
    public static void main(String[] args) throws Exception {
        HttpClient client = HttpClient.newHttpClient();

        System.out.println("=== ofLines() — streaming lines ===");

        HttpRequest linesRequest = HttpRequest.newBuilder()
            .uri(URI.create("https://httpbin.org/stream/5"))  // streams 5 JSON lines
            .GET()
            .build();

        HttpResponse<Stream<String>> linesResponse = client.send(linesRequest,
            HttpResponse.BodyHandlers.ofLines());

        // Process lines as a stream
        System.out.println("Status: " + linesResponse.statusCode());
        linesResponse.body().limit(3).forEach(line ->
            System.out.println("  Line: " + line.substring(0, Math.min(60, line.length())) + "..."));

        System.out.println("\n=== discarding() — ignore body ===");

        HttpResponse<Void> discardResp = client.send(
            HttpRequest.newBuilder()
                .uri(URI.create("https://httpbin.org/get"))
                .GET().build(),
            HttpResponse.BodyHandlers.discarding());

        System.out.println("Status: " + discardResp.statusCode());
        System.out.println("Body: " + discardResp.body());  // null

        System.out.println("\n=== Custom body publishing (byte array) ===");

        // Send raw bytes
        byte[] rawData = new byte[256];
        for (int i = 0; i < rawData.length; i++) rawData[i] = (byte) (i % 256);

        HttpRequest byteRequest = HttpRequest.newBuilder()
            .uri(URI.create("https://httpbin.org/post"))
            .header("Content-Type", "application/octet-stream")
            .POST(HttpRequest.BodyPublishers.ofByteArray(rawData))
            .build();

        HttpResponse<byte[]> byteResponse = client.send(byteRequest,
            HttpResponse.BodyHandlers.ofByteArray());

        System.out.println("Sent " + rawData.length + " bytes, received " +
            byteResponse.body().length + " bytes");

        System.out.println("\n=== Available handlers/publishers summary ===");
        System.out.println("BodyPublishers:");
        System.out.println("  ofString(), ofByteArray(), ofFile(), ofInputStream()");
        System.out.println("  noBody(), fromPublisher(Flow.Publisher)");
        System.out.println("BodyHandlers:");
        System.out.println("  ofString(), ofByteArray(), ofFile(), ofInputStream()");
        System.out.println("  ofLines(), discarding(), buffering(), fromSubscriber()");
    }
}
```

**How to run:** `java BodyHandlersAdvanced.java`

Expected output:
```
=== ofLines() — streaming lines ===
Status: 200
  Line: {"url": "https://httpbin.org/stream/5", "id": 0, ...}...
  Line: {"url": "https://httpbin.org/stream/5", "id": 1, ...}...
  Line: {"url": "https://httpbin.org/stream/5", "id": 2, ...}...

=== discarding() — ignore body ===
Status: 200
Body: null

=== Custom body publishing (byte array) ===
Sent 256 bytes, received ... bytes

=== Available handlers/publishers summary ===
BodyPublishers:
  ofString(), ofByteArray(), ofFile(), ofInputStream()
  noBody(), fromPublisher(Flow.Publisher)
BodyHandlers:
  ofString(), ofByteArray(), ofFile(), ofInputStream()
  ofLines(), discarding(), buffering(), fromSubscriber()
```

The production-flavoured hard cases: (1) **Streaming lines** — `BodyHandlers.ofLines()` returns `HttpResponse<Stream<String>>`, allowing line-by-line processing of large responses without loading the entire body into a single `String`. (2) **Discarding** — `BodyHandlers.discarding()` is for when you only care about status/headers (e.g. health checks, ping endpoints). (3) **Binary data** — `ofByteArray()` for small binary payloads; for large ones, use `ofFile()` or `ofInputStream()`.

## 6. Walkthrough

Tracing a file upload with `BodyPublishers.ofFile()`:

1. `HttpRequest.BodyPublishers.ofFile(Path.of("data.json"))` is called. Internally, this creates a `BodyPublisher` that, when subscribed to, opens a `FileChannel` to `data.json` and publishes its bytes as a `ByteBuffer` stream.

2. The `BodyPublisher` is passed to the `HttpRequest` builder: `.POST(publisher)`. The builder stores it — no I/O has occurred yet.

3. `.build()` creates the immutable `HttpRequest`. The `BodyPublisher` is embedded but not yet activated.

4. `client.send(request, BodyHandlers.ofString())` triggers the request:
   - The client opens a connection to the server.
   - It subscribes to the `BodyPublisher`, which begins reading the file in chunks and writing them to the request output stream.
   - The server receives the byte stream.

5. On the response side, `BodyHandlers.ofString()` subscribes to the response body. It reads all response bytes, decodes them as UTF-8, and returns a `String`.

6. The `HttpResponse<String>` is returned. Status, headers, and body are all available.

The data flows through clear layers:
- **Input:** `Path("data.json")` → `BodyPublisher` → HTTP request bytes on the wire
- **Output:** HTTP response bytes on the wire → `BodyHandler<String>` → Java `String`

## 7. Gotchas & takeaways

> `BodyHandlers.ofLines()` returns `Stream<String>` which **must be closed** after use (or used within try-with-resources). The underlying HTTP connection is held open until the stream is fully consumed or closed. Failing to close the stream leaks connections.

- `BodyPublishers` and `BodyHandlers` are **factory classes** — they only contain static methods and cannot be instantiated. They follow the same pattern as `Collectors` in the Stream API.
- Both are designed for **reactive streams** integration. `BodyPublisher` extends `Flow.Publisher<ByteBuffer>` and `BodyHandler` accepts a `ResponseInfo` and returns a `BodySubscriber<T>`. This enables backpressure-aware custom implementations.
- The built-in factories cover 95% of use cases. Only implement custom `BodyPublisher`/`BodySubscriber` when you need custom serialisation (Jackson, Protocol Buffers) or specific streaming behaviour.
- `ofFile()` for both request and response handles files of any size efficiently — it streams directly between file channels and network sockets without loading the entire file into memory.
- For empty request bodies, use `BodyPublishers.noBody()` (default for GET, DELETE, HEAD). Do not pass `null` — it will throw `NullPointerException`.

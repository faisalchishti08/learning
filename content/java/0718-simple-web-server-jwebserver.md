---
card: java
gi: 718
slug: simple-web-server-jwebserver
title: Simple Web Server (jwebserver)
---

## 1. What it is

**Java 18** (JEP 408) ships a **minimal static file HTTP server**, launched from the command line with the new `jwebserver` tool (or programmatically via `com.sun.net.httpserver.SimpleFileServer`). It serves the files in a given directory over HTTP with zero configuration — no build file, no dependency, no server code to write. Point it at a folder, run one command, and every file underneath becomes reachable over `http://localhost:<port>/`. It is explicitly *not* meant for production: no HTTPS, no CGI/servlets, no authentication, minimal request handling — just enough to serve static files for quick, local, throwaway purposes.

## 2. Why & when

Java developers constantly need a quick way to serve a folder of static files: testing a generated HTML report, prototyping a front end that fetches local JSON, checking what a directory of build output looks like in a browser, or giving a teammate a one-line command to preview something. Historically this meant reaching for `python -m http.server`, installing `http-server` via npm, or writing throwaway server code with `com.sun.net.httpserver.HttpServer` — all fine, but all requiring a tool outside the JDK itself, or boilerplate. JEP 408 exists purely for this "quick prototyping, testing, and experimentation" niche — the JEP text is explicit that a fully-featured production HTTP server is a *non-goal*. Reach for `jwebserver` when you want to eyeball static output in a browser right now, and reach for a real framework (Spring Boot, or a proper `HttpServer`/`HttpsServer` setup) the moment you need dynamic responses, HTTPS, or anything resembling a real deployment.

## 3. Core concept

```
jwebserver                                  # serve current directory on port 8000
jwebserver -p 9000                          # custom port
jwebserver -d /path/to/files                # custom directory
jwebserver -b 0.0.0.0                       # bind all interfaces, not just localhost
jwebserver -o verbose                       # log every request
```

Under the hood, `jwebserver` is a thin CLI wrapper around `com.sun.net.httpserver.SimpleFileServer`, so the exact same server can be embedded in a Java program instead of launched from the shell.

## 4. Diagram

<svg viewBox="0 0 640 200" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="jwebserver maps a directory on disk directly to URL paths served over HTTP">
  <rect x="30" y="60" width="200" height="100" rx="8" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="130" y="82" fill="#e6edf3" font-size="12" text-anchor="middle" font-family="sans-serif">./site/</text>
  <text x="130" y="104" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">index.html</text>
  <text x="130" y="122" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">style.css</text>
  <text x="130" y="140" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">data/report.json</text>

  <line x1="235" y1="110" x2="405" y2="110" stroke="#3fb950" stroke-width="2" marker-end="url(#a1)"/>
  <text x="320" y="100" fill="#3fb950" font-size="11" text-anchor="middle" font-family="sans-serif">jwebserver -d ./site -p 8000</text>

  <rect x="410" y="60" width="200" height="100" rx="8" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="510" y="82" fill="#e6edf3" font-size="12" text-anchor="middle" font-family="sans-serif">http://localhost:8000</text>
  <text x="510" y="104" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">/index.html</text>
  <text x="510" y="122" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">/style.css</text>
  <text x="510" y="140" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">/data/report.json</text>

  <defs><marker id="a1" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#3fb950"/></marker></defs>
</svg>

Every file's path on disk becomes its URL path — no routing configuration needed.

## 5. Runnable example

Scenario: serving a small generated report directory, first with the bare defaults, then adding an explicit port and output logging for a repeatable local workflow, then embedding the same server programmatically in a Java program with a custom output level and a graceful shutdown — the exact scenario `jwebserver` targets: previewing generated static files without writing a real web app.

### Level 1 — Basic

```java
// File: GenerateReportBasic.java
// Generates a tiny static site into ./out — jwebserver then serves it directly
// from the shell, no code needed for the serving part itself.
import java.io.IOException;
import java.nio.file.*;

public class GenerateReportBasic {
    public static void main(String[] args) throws IOException {
        Path dir = Path.of("out");
        Files.createDirectories(dir);
        Files.writeString(dir.resolve("index.html"),
            "<html><body><h1>Report</h1><p>Generated by GenerateReportBasic</p></body></html>");
        System.out.println("Wrote " + dir.resolve("index.html").toAbsolutePath());
        System.out.println("Now run: jwebserver -d " + dir.toAbsolutePath() + " -p 8000");
    }
}
```

**How to run:**
```
java GenerateReportBasic.java
jwebserver -d "$(pwd)/out" -p 8000
# then visit http://localhost:8000/index.html
```

Expected output:
```
Wrote /path/to/out/index.html
Now run: jwebserver -d /path/to/out -p 8000
```
The `jwebserver` command itself then prints something like:
```
Binding to loopback by default. For all interfaces use "-b 0.0.0.0" or "-b ::".
Serving /path/to/out and subdirectories on 127.0.0.1 port 8000
URL http://127.0.0.1:8000/
```

### Level 2 — Intermediate

```java
// File: GenerateReportIntermediate.java
// Adds nested data output, matching a more realistic "generated report" shape,
// and prints the exact jwebserver invocation with verbose logging enabled so
// every request the browser makes while previewing is visible.
import java.io.IOException;
import java.nio.file.*;

public class GenerateReportIntermediate {
    public static void main(String[] args) throws IOException {
        Path dir = Path.of("out");
        Path dataDir = dir.resolve("data");
        Files.createDirectories(dataDir);

        Files.writeString(dir.resolve("index.html"), """
            <html><body>
              <h1>Report</h1>
              <p>See <a href="data/summary.json">summary.json</a></p>
            </body></html>
            """);
        Files.writeString(dataDir.resolve("summary.json"), """
            {"rows": 42, "status": "ok"}
            """);

        System.out.println("Report tree ready under " + dir.toAbsolutePath());
        System.out.println("Run with request logging:");
        System.out.println("  jwebserver -d " + dir.toAbsolutePath() + " -p 8000 -o verbose");
    }
}
```

**How to run:**
```
java GenerateReportIntermediate.java
jwebserver -d "$(pwd)/out" -p 8000 -o verbose
# visiting http://localhost:8000/ and clicking the link logs each request to the terminal
```

Expected output from the Java program:
```
Report tree ready under /path/to/out
Run with request logging:
  jwebserver -d /path/to/out -p 8000 -o verbose
```
With `-o verbose`, `jwebserver` additionally logs each request it handles, e.g.:
```
127.0.0.1 - - [10/Jul/2026:00:00:00 +0000] "GET /index.html HTTP/1.1" 200 -
127.0.0.1 - - [10/Jul/2026:00:00:01 +0000] "GET /data/summary.json HTTP/1.1" 200 -
```

### Level 3 — Advanced

```java
// File: EmbeddedSimpleFileServer.java
// Instead of shelling out to `jwebserver`, embeds the exact same server
// programmatically via SimpleFileServer — useful for test harnesses that
// need to spin a static server up and down around test code.
import com.sun.net.httpserver.HttpServer;
import com.sun.net.httpserver.SimpleFileServer;
import com.sun.net.httpserver.SimpleFileServer.OutputLevel;
import java.io.IOException;
import java.net.InetSocketAddress;
import java.net.URI;
import java.net.http.HttpClient;
import java.net.http.HttpRequest;
import java.net.http.HttpResponse;
import java.nio.file.*;

public class EmbeddedSimpleFileServer {
    public static void main(String[] args) throws IOException, InterruptedException {
        Path dir = Path.of("out");
        Files.createDirectories(dir);
        Files.writeString(dir.resolve("index.html"), "<html><body>Embedded server</body></html>");

        HttpServer server = SimpleFileServer.createFileServer(
                new InetSocketAddress("127.0.0.1", 0), // port 0 -> OS picks a free port
                dir,
                OutputLevel.INFO);
        server.start();
        int port = server.getAddress().getPort();
        System.out.println("Embedded server started on port " + port);

        // Act as our own client, proving the server actually answers requests.
        HttpClient client = HttpClient.newHttpClient();
        HttpRequest request = HttpRequest.newBuilder(URI.create("http://127.0.0.1:" + port + "/index.html")).build();
        HttpResponse<String> response = client.send(request, HttpResponse.BodyHandlers.ofString());

        System.out.println("Status: " + response.statusCode());
        System.out.println("Body: " + response.body());

        server.stop(0);
        System.out.println("Server stopped.");
    }
}
```

**How to run:**
```
java EmbeddedSimpleFileServer.java
```

Expected output:
```
Embedded server started on port <some free port>
Status: 200
Body: <html><body>Embedded server</body></html>
Server stopped.
```

## 6. Walkthrough

1. `EmbeddedSimpleFileServer.main` first writes an `index.html` file to `./out` — this is the exact same static-file-directory shape `jwebserver` expects on the command line; nothing about the served content changes between the CLI tool and the embedded API.
2. `SimpleFileServer.createFileServer(address, dir, OutputLevel.INFO)` builds the server object. This one call *is* what `jwebserver` runs internally: a bind address, a root directory to serve, and a logging verbosity level (`NONE`, `INFO`, or `VERBOSE`, matching `jwebserver -o`).
3. `server.start()` begins listening; `server.getAddress().getPort()` reads back the actual port, since port `0` was requested (meaning "let the OS assign any free port") — handy for test code that must not hard-code a port that might already be in use.
4. The program then acts as its own **client**: `HttpClient` sends a `GET /index.html` request to the server it just started, exactly the way a browser would.
5. **Request:** `GET http://127.0.0.1:<port>/index.html HTTP/1.1`, no body, no special headers required for a static-file GET.
6. Inside the server, `SimpleFileServer` maps the URL path `/index.html` directly onto the file `out/index.html` on disk — there is no routing layer, no controller, no business logic; the file's bytes become the response body verbatim, and its content type is inferred from the extension (`.html` → `text/html`).
7. **Response:** `200 OK`, `Content-Type: text/html`, body equal to the exact bytes of `out/index.html`. The client prints `response.statusCode()` (`200`) and `response.body()` (the HTML content), confirming the round trip.
8. `server.stop(0)` shuts the server down immediately (`0` seconds grace period), and the program exits — mirroring how a developer would `Ctrl+C` a `jwebserver` process running in a terminal.

```
Browser / HttpClient                 jwebserver / SimpleFileServer            Filesystem
        |  GET /data/summary.json            |                                    |
        |------------------------------------>|                                    |
        |                                     |  map URL path -> file path         |
        |                                     |----------------------------------->|
        |                                     |             read bytes             |
        |                                     |<-----------------------------------|
        |     200 OK + file bytes as body     |                                    |
        |<------------------------------------|                                    |
```

## 7. Gotchas & takeaways

> `jwebserver` binds to **loopback (`127.0.0.1`) by default**, not all network interfaces — colleagues on the same network cannot reach it until you explicitly pass `-b 0.0.0.0` (or `-b ::` for IPv6). This is a deliberate safety default, since the server has no authentication.
- There is no HTTPS support, no CGI, no servlets, and no way to run server-side code — `jwebserver` only ever serves the literal bytes of files under the given directory. Anything dynamic requires a real server.
- By default it only serves `GET` and `HEAD` requests and refuses to serve files outside the given root directory, but it still has no authentication layer — never point it at a directory containing anything sensitive, and never expose it beyond localhost on an untrusted network.
- The default port is `8000`; the default directory is the current working directory — running bare `jwebserver` with no flags in the wrong directory can accidentally expose more files than intended, so always check `pwd` first.
- Because it's built on the same `com.sun.net.httpserver` package used for lightweight embedded servers, output-level control (`-o none|info|verbose`) maps directly to `SimpleFileServer.OutputLevel`, making it straightforward to promote a quick CLI experiment into a small embedded test-harness server later, as shown in Level 3.

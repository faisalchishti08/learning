---
card: spring-framework
gi: 140
slug: servletcontextresource-inputstreamresource-bytearrayresource
title: "ServletContextResource, InputStreamResource, ByteArrayResource"
---

## 1. What it is

Three specialized `Resource` implementations covering web-app relative paths, raw streams, and in-memory byte arrays:

- **`ServletContextResource`** — resolves paths relative to the web application root; reads via `ServletContext.getResourceAsStream`. Location prefix: none (path starts with `/`).
- **`InputStreamResource`** — wraps an existing `InputStream`. Single-read (`isOpen()=true`). Used when you already have a stream and need to pass it as a `Resource`.
- **`ByteArrayResource`** — wraps a `byte[]`. Multiple reads; no file I/O. Ideal for in-memory data in tests and batch processing.

```java
Resource isr = new InputStreamResource(socket.getInputStream());
Resource bar = new ByteArrayResource("{\"ok\":true}".getBytes(), "JSON payload");
```

## 2. Why & when

| Implementation | Choose when |
|---|---|
| `ServletContextResource` | Web app; resolve `/WEB-INF/config.xml`, `/static/schema.json` |
| `InputStreamResource` | Already holding an open stream; need to pass it as a `Resource` |
| `ByteArrayResource` | In-memory data; test fixtures; response caching; protocol buffers |

`InputStreamResource` should be the last resort — it is single-read and cannot report `contentLength()` reliably. `ByteArrayResource` is almost always preferred for in-memory data.

## 3. Core concept

`ServletContextResource`:
- Resolves from the web application root, not the classpath.
- `getFile()` works only if the resource is not inside a WAR; in a packaged WAR it throws.
- `getURL()` delegates to `ServletContext.getResource(path)`.

`InputStreamResource`:
- `isOpen()` returns `true` — signals that the stream cannot be re-read.
- `exists()` and `isReadable()` return `true` (the stream is assumed to be open).
- `contentLength()` is not supported.
- Once `getInputStream()` is called and the stream is consumed, a second call to `getInputStream()` returns the same (exhausted) stream — behavior is undefined.

`ByteArrayResource`:
- Wraps `byte[]`; each `getInputStream()` call creates a fresh `ByteArrayInputStream`.
- `contentLength()` returns `byte[].length`.
- `isOpen()` returns `false` — reusable.
- Optional `description` string for diagnostic messages.

## 4. Diagram

<svg viewBox="0 0 700 195" xmlns="http://www.w3.org/2000/svg">
  <!-- Resource interface -->
  <rect x="10" y="80" width="120" height="35" rx="6" fill="#1c2430" stroke="#6db33f" stroke-width="2"/>
  <text x="70" y="101" fill="#6db33f" font-size="11" text-anchor="middle" font-family="sans-serif">&lt;&lt;Resource&gt;&gt;</text>

  <!-- ServletContextResource -->
  <rect x="195" y="18" width="200" height="50" rx="6" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="295" y="38" fill="#79c0ff" font-size="11" text-anchor="middle" font-family="sans-serif">ServletContextResource</text>
  <text x="295" y="55" fill="#8b949e" font-size="9"  text-anchor="middle" font-family="sans-serif">web-root relative; ServletContext.getResource</text>

  <!-- InputStreamResource -->
  <rect x="195" y="80" width="200" height="50" rx="6" fill="#1c2430" stroke="#8b949e" stroke-width="1.5"/>
  <text x="295" y="100" fill="#8b949e" font-size="11" text-anchor="middle" font-family="sans-serif">InputStreamResource</text>
  <text x="295" y="116" fill="#8b949e" font-size="9"  text-anchor="middle" font-family="sans-serif">isOpen=true; single-read; no contentLength</text>

  <!-- ByteArrayResource -->
  <rect x="195" y="142" width="200" height="50" rx="6" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="295" y="162" fill="#6db33f" font-size="11" text-anchor="middle" font-family="sans-serif">ByteArrayResource</text>
  <text x="295" y="178" fill="#8b949e" font-size="9"  text-anchor="middle" font-family="sans-serif">byte[]; multi-read; isOpen=false; testable</text>

  <defs>
    <marker id="a140" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#6db33f"/></marker>
  </defs>
  <line x1="132" y1="90" x2="192" y2="43"  stroke="#6db33f" stroke-width="1.5" marker-end="url(#a140)"/>
  <line x1="132" y1="97" x2="192" y2="105" stroke="#6db33f" stroke-width="1.5" marker-end="url(#a140)"/>
  <line x1="132" y1="104" x2="192" y2="167" stroke="#6db33f" stroke-width="1.5" marker-end="url(#a140)"/>
</svg>

`ByteArrayResource` is multi-read; `InputStreamResource` is single-read (`isOpen=true`); `ServletContextResource` resolves from the web-app root.

## 5. Runnable example

### Level 1 — Basic

`ByteArrayResource` multi-read versus `InputStreamResource` single-read; demonstrate `isOpen`.

```java
// SpecializedResourceBasic.java
import org.springframework.core.io.*;

public class SpecializedResourceBasic {
    static void read(Resource r, String label) throws Exception {
        System.out.printf("[%s] isOpen=%b exists=%b readable=%b%n",
            label, r.isOpen(), r.exists(), r.isReadable());
        try {
            String content = new String(r.getInputStream().readAllBytes());
            System.out.printf("  1st read: %s%n", content);
            content = new String(r.getInputStream().readAllBytes());
            System.out.printf("  2nd read: %s%n", content.isEmpty() ? "(empty—stream exhausted)" : content);
        } catch (Exception e) {
            System.out.printf("  2nd read threw: %s%n", e.getMessage());
        }
    }

    public static void main(String[] args) throws Exception {
        byte[] payload = "Hello from bytes!".getBytes();

        // ByteArrayResource — multi-read
        ByteArrayResource bar = new ByteArrayResource(payload, "test payload");
        read(bar, "ByteArrayResource");
        System.out.println("  contentLength: " + bar.contentLength());
        System.out.println("  description:   " + bar.getDescription());

        System.out.println();

        // InputStreamResource — single-read
        var stream = new java.io.ByteArrayInputStream(payload);
        InputStreamResource isr = new InputStreamResource(stream, "wrapped stream");
        read(isr, "InputStreamResource");
    }
}
```

How to run: `java SpecializedResourceBasic.java`

`ByteArrayResource` returns a fresh `ByteArrayInputStream` on each `getInputStream()` — the second read succeeds. `InputStreamResource`'s stream is exhausted after the first read — the second read returns empty bytes (or throws, depending on the stream type).

### Level 2 — Intermediate

`ByteArrayResource` as a test-friendly `Resource`; simulate a response body; demonstrate the optional description for debugging.

```java
// SpecializedResourceTest.java
import org.springframework.core.io.*;
import java.util.Properties;

// A service that loads configuration from a Resource
class ConfigLoader {
    private final Properties config = new Properties();

    public ConfigLoader(Resource source) throws Exception {
        if (!source.exists()) throw new IllegalArgumentException(
            "Config resource not found: " + source.getDescription());
        config.load(source.getInputStream());
        System.out.println("[ConfigLoader] loaded from: " + source.getDescription());
    }

    public String get(String key) { return config.getProperty(key, "<missing>"); }
    public int getInt(String key, int def) {
        String v = config.getProperty(key);
        return v != null ? Integer.parseInt(v) : def;
    }
}

public class SpecializedResourceTest {
    public static void main(String[] args) throws Exception {
        // Production-like: load from classpath
        java.nio.file.Files.writeString(java.nio.file.Path.of("prod.properties"),
            "db.url=jdbc:pg://prod/app\ndb.pool=20\nfeature.new-ui=true\n");

        var prodLoader = new ConfigLoader(new ClassPathResource("prod.properties"));
        System.out.println("prod db.url:  " + prodLoader.get("db.url"));
        System.out.println("prod db.pool: " + prodLoader.getInt("db.pool", 5));

        System.out.println();

        // Test: use ByteArrayResource to inject fixture data without touching the filesystem
        byte[] testCfg = ("db.url=jdbc:h2:mem:test\n" +
                          "db.pool=2\n" +
                          "feature.new-ui=false\n").getBytes();

        var testLoader = new ConfigLoader(
            new ByteArrayResource(testCfg, "test-fixture: in-memory config"));
        System.out.println("test db.url:  " + testLoader.get("db.url"));
        System.out.println("test db.pool: " + testLoader.getInt("db.pool", 5));
        System.out.println("test feature: " + testLoader.get("feature.new-ui"));

        // A third ConfigLoader with missing resource — expect exception
        try {
            new ConfigLoader(new ByteArrayResource(new byte[0], "empty-resource") {
                @Override public boolean exists() { return false; }
            });
        } catch (IllegalArgumentException e) {
            System.out.println("\nExpected error: " + e.getMessage());
        }

        java.nio.file.Files.deleteIfExists(java.nio.file.Path.of("prod.properties"));
    }
}
```

How to run: `java SpecializedResourceTest.java`

`ConfigLoader` accepts any `Resource` — both the classpath file and the in-memory `ByteArrayResource` work. The description string `"test-fixture: in-memory config"` appears in the `[ConfigLoader] loaded from:` message, making test failures easier to diagnose.

### Level 3 — Advanced

`InputStreamResource` for wrapping a network socket or pipe; `ByteArrayResource` for response body caching; multiple consumers.

```java
// SpecializedResourceAdvanced.java
import org.springframework.core.io.*;
import java.io.*;
import java.nio.file.*;
import java.util.*;

// Simulate a remote data fetch returning an InputStream
class RemoteDataFetcher {
    static InputStream fetchRaw(String topic) {
        System.out.println("[RemoteDataFetcher] opening stream for: " + topic);
        String data = switch (topic) {
            case "users"    -> "id,name\n1,Alice\n2,Bob\n3,Carol\n";
            case "products" -> "sku,price\nSKU001,19.99\nSKU002,49.99\n";
            default         -> "";
        };
        return new ByteArrayInputStream(data.getBytes());
    }
}

// A pipeline that needs to read a Resource multiple times (validation + processing)
class DataPipeline {
    private final Resource source;
    private final String name;

    DataPipeline(Resource source, String name) {
        this.source = source;
        this.name   = name;
    }

    public void run() throws Exception {
        // Step 1: validate (needs one read)
        byte[] raw = source.getInputStream().readAllBytes();
        System.out.println("[" + name + "] validate: " + raw.length + " bytes, " +
            new String(raw).lines().count() + " lines");

        // Step 2: process (needs another read)
        try (var reader = new BufferedReader(
                new InputStreamReader(source.getInputStream()))) {
            reader.readLine(); // header
            String line;
            while ((line = reader.readLine()) != null) {
                System.out.println("[" + name + "] record: " + line);
            }
        }
    }
}

public class SpecializedResourceAdvanced {
    public static void main(String[] args) throws Exception {
        // Pattern 1: fetch once into ByteArrayResource for multi-step pipeline
        System.out.println("=== ByteArrayResource (buffered) ===");
        InputStream rawStream = RemoteDataFetcher.fetchRaw("users");
        byte[] buffer = rawStream.readAllBytes();  // buffer the stream
        ByteArrayResource buffered = new ByteArrayResource(buffer, "users-csv");

        new DataPipeline(buffered, "users").run();  // reads twice — works

        // Pattern 2: InputStreamResource for a single pass (log file, pipe)
        System.out.println("\n=== InputStreamResource (single-pass) ===");
        InputStream logStream = RemoteDataFetcher.fetchRaw("products");
        InputStreamResource streamRes = new InputStreamResource(logStream, "products-stream");

        System.out.println("isOpen: " + streamRes.isOpen());
        try (var reader = new BufferedReader(
                new InputStreamReader(streamRes.getInputStream()))) {
            reader.lines().forEach(l -> System.out.println("  line: " + l));
        }
        // Second read — stream is exhausted
        byte[] second = streamRes.getInputStream().readAllBytes();
        System.out.println("2nd getInputStream bytes: " + second.length + " (exhausted)");

        // Pattern 3: save ByteArrayResource to disk
        System.out.println("\n=== Persist ByteArrayResource ===");
        ByteArrayResource jsonPayload = new ByteArrayResource(
            "{\"status\":\"ok\",\"count\":3}".getBytes(), "api-response");
        Path out = Files.createTempFile("cached-response-", ".json");
        Files.write(out, jsonPayload.getByteArray());
        System.out.println("Saved " + jsonPayload.contentLength() + " bytes to " + out.getFileName());
        System.out.println("Content: " + Files.readString(out));
        Files.deleteIfExists(out);
    }
}
```

How to run: `java SpecializedResourceAdvanced.java`

Pattern 1: buffer the network stream into `ByteArrayResource` so the pipeline can read twice. Pattern 2: `InputStreamResource` for a genuine single-pass pipeline (reading a piped stream). Pattern 3: `ByteArrayResource.getByteArray()` gives direct access to the underlying `byte[]` without a stream.

## 6. Walkthrough

Execution for Level 3 Pattern 1:

1. **`RemoteDataFetcher.fetchRaw("users")`** returns a `ByteArrayInputStream` (simulating a network socket).
2. **`rawStream.readAllBytes()`** drains the stream into a `byte[]` buffer.
3. **`new ByteArrayResource(buffer, "users-csv")`** wraps the buffer.
4. **`DataPipeline.run()`** — Step 1: `source.getInputStream()` → fresh `ByteArrayInputStream(buffer)` → reads all bytes for validation.
5. Step 2: `source.getInputStream()` → another fresh `ByteArrayInputStream(buffer)` → reads line by line.
6. Both reads succeed because `ByteArrayResource` creates a new `ByteArrayInputStream` on each call.

## 7. Gotchas & takeaways

> `InputStreamResource.getInputStream()` does NOT create a new stream each time — it returns the original `InputStream` passed at construction. A second call returns the same (potentially exhausted) stream. This is by design but widely misunderstood. When in doubt, buffer first with `ByteArrayResource`.

> `ByteArrayResource.getByteArray()` returns the raw `byte[]` reference — not a copy. If the caller modifies the array, the `Resource`'s content changes. Defensive-copy if you need immutability.

- `ServletContextResource` is primarily used internally by Spring MVC's `DefaultResourceLoader`. In modern Spring Boot apps with embedded servers, web resources are served via `ResourceHttpRequestHandler`, not directly via `ServletContextResource`.
- `InputStreamResource` reports `contentLength()` as `-1` — avoid using it where `Content-Length` is required (e.g., streaming HTTP responses).
- For large data sets, prefer streaming (`InputStreamResource`) over buffering (`ByteArrayResource`) to avoid heap pressure. Buffer only when multi-read is required.
- `ByteArrayResource` with a description string helps produce useful error messages when a resource fails validation — always provide one in production code.

---
card: spring-framework
gi: 336
slug: streamingresponsebody
title: "StreamingResponseBody"
---

## 1. What it is

`StreamingResponseBody` is a functional-interface return type for Spring MVC handler methods that hands you the raw `OutputStream` of the HTTP response and lets you write bytes to it directly, on a separate thread, as they become available — without buffering the entire response in memory first. Unlike `SseEmitter`, it has no event framing or protocol; it's a general-purpose mechanism for streaming any content (a large file being generated on the fly, a big CSV export, a proxied download) efficiently.

```java
@GetMapping("/export")
public StreamingResponseBody export() {
    return outputStream -> {
        for (int i = 0; i < 1_000_000; i++) {
            outputStream.write((i + "\n").getBytes());
        }
    };
}
```

## 2. Why & when

Returning a fully-built `String`, `byte[]`, or `List<T>` from a handler means Spring holds the *entire* response in memory before writing any of it to the client. For large responses (a multi-gigabyte export, a report with millions of rows, a file being generated dynamically) this means high memory pressure and a long delay before the client sees the first byte.

Use `StreamingResponseBody` when:
- Generating a large export (CSV, JSON Lines, a file) where holding the full result in memory is wasteful or risky (OOM on large datasets).
- Proxying a large download from another service without buffering it entirely first.
- You want the client to start receiving bytes immediately (better perceived latency, matters for progress bars/download managers) rather than waiting for the whole payload to be ready.

It's the right tool for **one-shot large payloads** — contrast with `SseEmitter`, which is for ongoing, event-based, typically long-lived pushes (see the previous card). `StreamingResponseBody` runs once, writes until done, and the response completes.

## 3. Core concept

```
Normal handler (buffered):
  build full byte[] or String in memory
       |
       v
  ONE write of the complete response
       |
       v
  client waits for ALL data, THEN receives it as one block

StreamingResponseBody handler:
  return a lambda: (OutputStream out) -> { ... }
       |
       v
  Spring hands the RAW OutputStream to your lambda,
  running on a separate thread from the request thread
       |
       v
  your code writes bytes incrementally:
    out.write(chunk1); out.flush();
    out.write(chunk2); out.flush();
    ...
       |
       v
  client receives each chunk as soon as it's flushed —
  HTTP chunked transfer encoding, no need to know total size upfront
```

Because writing happens on a separate thread, the servlet container's request-handling thread is freed while the stream is still being written — important for scalability under many concurrent large downloads.

## 4. Diagram

<svg viewBox="0 0 720 220" xmlns="http://www.w3.org/2000/svg" font-family="monospace" font-size="12">
  <rect width="720" height="220" fill="#0d1117"/>
  <text x="360" y="22" text-anchor="middle" fill="#8b949e">Buffered response vs StreamingResponseBody</text>

  <rect x="20" y="50" width="320" height="70" rx="5" fill="#1c2430" stroke="#e6edf3"/>
  <text x="180" y="72" text-anchor="middle" fill="#e6edf3">Buffered</text>
  <text x="180" y="90" text-anchor="middle" fill="#8b949e" font-size="10">build full result in memory,</text>
  <text x="180" y="105" text-anchor="middle" fill="#8b949e" font-size="10">then send it all at once</text>

  <rect x="380" y="50" width="320" height="70" rx="5" fill="#1c2430" stroke="#6db33f"/>
  <text x="540" y="72" text-anchor="middle" fill="#6db33f">StreamingResponseBody</text>
  <text x="540" y="90" text-anchor="middle" fill="#8b949e" font-size="10">write chunk, flush, repeat —</text>
  <text x="540" y="105" text-anchor="middle" fill="#8b949e" font-size="10">bounded memory, early first byte</text>

  <line x1="180" y1="120" x2="180" y2="160" stroke="#e6edf3" marker-end="url(#a12)"/>
  <line x1="540" y1="120" x2="540" y2="160" stroke="#6db33f" marker-end="url(#a12)"/>

  <rect x="60" y="160" width="240" height="40" rx="4" fill="#1c2430" stroke="#8b949e"/>
  <text x="180" y="184" text-anchor="middle" fill="#e6edf3" font-size="10">client waits, then gets everything</text>

  <rect x="420" y="160" width="240" height="40" rx="4" fill="#1c2430" stroke="#8b949e"/>
  <text x="540" y="184" text-anchor="middle" fill="#e6edf3" font-size="10">client sees bytes arriving progressively</text>

  <defs>
    <marker id="a12" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto">
      <path d="M0,0 L0,6 L8,3 z" fill="#8b949e"/>
    </marker>
  </defs>
</svg>

*Streaming trades a moment of upfront buffering for progressive delivery and bounded server memory use.*

## 5. Runnable example

### Level 1 — Basic

Streaming a large sequence of numbers instead of building a giant string first:

```java
// ExportController.java
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RestController;
import org.springframework.web.servlet.mvc.method.annotation.StreamingResponseBody;

@RestController
public class ExportController {

    @GetMapping("/export/numbers")
    public StreamingResponseBody exportNumbers() {
        return outputStream -> {
            for (int i = 0; i < 100_000; i++) {
                outputStream.write((i + "\n").getBytes());
            }
        };
    }
}
```

**How to run:**
```bash
./mvnw spring-boot:run

curl http://localhost:8080/export/numbers | wc -l
# 100000
```

No `String` or `byte[]` holding all 100,000 lines is ever built in memory — each line is written straight to the response's `OutputStream` as it's produced. The handler method itself returns almost instantly (it just returns a lambda); the actual writing happens afterward, driven by Spring's async request processing.

### Level 2 — Intermediate

Streaming a CSV export with proper headers (`Content-Disposition` for file download, `Content-Type`), and periodic flushing so the client sees progress on a slow-to-generate report:

```java
// ExportController.java (extended)
import org.springframework.http.HttpHeaders;
import org.springframework.http.MediaType;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RestController;
import org.springframework.web.servlet.mvc.method.annotation.StreamingResponseBody;

import java.io.PrintWriter;
import java.nio.charset.StandardCharsets;

@RestController
public class ExportController {

    record Product(long id, String name, double price) {}

    @GetMapping("/export/products.csv")
    public ResponseEntity<StreamingResponseBody> exportProducts() {
        StreamingResponseBody body = outputStream -> {
            PrintWriter writer = new PrintWriter(new java.io.OutputStreamWriter(outputStream, StandardCharsets.UTF_8));
            writer.println("id,name,price");
            for (int i = 1; i <= 50_000; i++) {
                Product p = new Product(i, "Product " + i, 9.99 + i * 0.01);
                writer.println(p.id() + "," + p.name() + "," + p.price());
                if (i % 5000 == 0) writer.flush();   // periodic flush -> client sees progress
            }
            writer.flush();
        };

        return ResponseEntity.ok()
                .header(HttpHeaders.CONTENT_DISPOSITION, "attachment; filename=\"products.csv\"")
                .contentType(MediaType.parseMediaType("text/csv"))
                .body(body);
    }
}
```

**How to run:**
```bash
./mvnw spring-boot:run

curl -o products.csv http://localhost:8080/export/products.csv
wc -l products.csv
# 50001 products.csv     (50,000 rows + header)

head -3 products.csv
# id,name,price
# 1,Product 1,10.0
# 2,Product 2,10.01
```

**What changed:** Wrapping the `StreamingResponseBody` in a `ResponseEntity` allows setting `Content-Disposition: attachment` (so a browser prompts a file download instead of rendering the CSV inline) and an explicit `Content-Type`. Periodic `writer.flush()` calls push data to the client in batches rather than only at the very end, useful for very large exports where you want the client to start receiving data well before generation completes.

### Level 3 — Advanced

Production concerns: bounding memory when the source data itself comes from a paginated database query (never loading the full dataset at once), handling client disconnection mid-stream gracefully, and applying a timeout so a stuck generator doesn't hold server resources indefinitely:

```java
// ExportController.java (production version)
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.http.HttpHeaders;
import org.springframework.http.MediaType;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RestController;
import org.springframework.web.context.request.async.AsyncRequestTimeoutException;
import org.springframework.web.servlet.mvc.method.annotation.StreamingResponseBody;

import java.io.IOException;
import java.io.PrintWriter;
import java.nio.charset.StandardCharsets;
import java.util.List;

@RestController
public class ExportController {

    private static final Logger log = LoggerFactory.getLogger(ExportController.class);

    record Product(long id, String name, double price) {}

    interface ProductRepository {
        List<Product> findPage(int page, int size);   // real implementation queries a database
    }

    private final ProductRepository repository = (page, size) -> {
        // Simulated paginated source — real code would issue a LIMIT/OFFSET or keyset query per page
        List<Product> results = new java.util.ArrayList<>();
        for (int i = 0; i < size; i++) {
            long id = (long) page * size + i + 1;
            if (id > 200_000) break;
            results.add(new Product(id, "Product " + id, 9.99));
        }
        return results;
    };

    @GetMapping(value = "/export/products-large.csv", produces = "text/csv")
    public ResponseEntity<StreamingResponseBody> exportLarge() {
        StreamingResponseBody body = outputStream -> {
            PrintWriter writer = new PrintWriter(new java.io.OutputStreamWriter(outputStream, StandardCharsets.UTF_8));
            writer.println("id,name,price");
            writer.flush();

            int page = 0;
            int pageSize = 1000;
            try {
                while (true) {
                    // Only ONE page (1000 rows) is ever in memory at a time — bounded, regardless
                    // of whether the full export is 10,000 or 10,000,000 rows.
                    List<Product> batch = repository.findPage(page, pageSize);
                    if (batch.isEmpty()) break;

                    for (Product p : batch) {
                        writer.println(p.id() + "," + p.name() + "," + p.price());
                    }
                    writer.flush();

                    if (writer.checkError()) {
                        // checkError() returns true once the underlying stream has failed —
                        // typically means the client disconnected. Stop generating work no one will read.
                        log.info("client disconnected mid-export at page {}", page);
                        return;
                    }
                    page++;
                }
            } catch (Exception e) {
                log.error("export failed at page {}", page, e);
                throw e;
            }
        };

        return ResponseEntity.ok()
                .header(HttpHeaders.CONTENT_DISPOSITION, "attachment; filename=\"products-large.csv\"")
                .header("X-Accel-Buffering", "no")   // hint reverse proxies (e.g. nginx) not to buffer the stream
                .contentType(MediaType.parseMediaType("text/csv"))
                .body(body);
    }

    @org.springframework.web.bind.annotation.ExceptionHandler(AsyncRequestTimeoutException.class)
    public ResponseEntity<String> handleTimeout() {
        return ResponseEntity.status(org.springframework.http.HttpStatus.SERVICE_UNAVAILABLE)
                .body("Export took too long and was aborted");
    }
}
```

`application.yml`:
```yaml
spring:
  mvc:
    async:
      request-timeout: 300000   # 5 minutes — generous but bounded, so a stuck export can't hold resources forever
```

**How to run:**
```bash
./mvnw spring-boot:run

curl -o products-large.csv http://localhost:8080/export/products-large.csv
wc -l products-large.csv
# 200001 products-large.csv

# Simulate a client disconnect mid-download:
curl -o /dev/null http://localhost:8080/export/products-large.csv --max-time 1
# curl aborts after 1s; server log shows "client disconnected mid-export at page N" and generation stops
```

**What changed and why:**
- Data is pulled **page by page** from the repository instead of loading the whole 200,000-row dataset into a `List` upfront — memory use stays bounded at roughly one page's worth of objects, regardless of total export size. This is the difference between an export that works at 200,000 rows and OOMs at 20,000,000, versus one that scales to either.
- `writer.checkError()` after each flush detects a broken/closed connection (client disconnected, network dropped) so the server stops doing pointless work (querying more pages, generating more CSV rows) for a client that's no longer listening — a real resource-efficiency concern under load.
- `spring.mvc.async.request-timeout` bounds how long any single streaming response can run — without it, a stuck or infinitely slow generator would hold server resources (an async dispatch, a database connection) indefinitely.

## 6. Walkthrough

**Request: `GET /export/products-large.csv` (Level 3 code, client stays connected for the full download).**

1. `DispatcherServlet` dispatches to `exportLarge()`. The method builds and returns a `ResponseEntity<StreamingResponseBody>` — headers (`Content-Disposition`, `Content-Type`, `X-Accel-Buffering`) are set immediately, but the lambda body inside `StreamingResponseBody` has not executed yet.
2. Spring MVC recognizes the async return type, starts an asynchronous request handling context, and hands the response's `OutputStream` to the lambda — running on a task executor thread, separate from the original servlet request thread (which is released back to the pool).
3. Inside the lambda: `writer.println("id,name,price")` writes the CSV header row, then `writer.flush()` pushes it to the client immediately — the browser/`curl` starts receiving bytes right away, long before row 200,000 is generated.
4. The `while (true)` loop begins: `page = 0`, `repository.findPage(0, 1000)` executes a (simulated) database query returning rows `1`–`1000`. Note only these 1000 objects exist in memory at this point — not the full 200,000.
5. Each of the 1000 `Product` records is written as a CSV line; `writer.flush()` pushes this batch to the client.
6. `writer.checkError()` is `false` (client still connected) — loop continues: `page = 1`, fetches rows `1001`–`2000`, writes, flushes, checks again.
7. This repeats — page 0 through page 199 — until `repository.findPage(200, 1000)` returns an empty list (past `id > 200_000`), breaking the loop.
8. The lambda returns normally; Spring MVC completes the async response, closing the HTTP connection cleanly. The client's downloaded file now has 200,001 lines (1 header + 200,000 data rows).

**Same request, but the client disconnects after receiving roughly 50,000 rows (`curl --max-time 1`):**

1–6. Identical up through several successful page iterations, writing and flushing batches.
7. At some page (say page 50), `writer.flush()` attempts to push bytes to a socket the client has already closed. The underlying `PrintWriter` catches the resulting `IOException` internally (that's `PrintWriter`'s documented behavior — it never throws, it just records the failure) and marks its error state.
8. The next `writer.checkError()` call returns `true`. The lambda logs `"client disconnected mid-export at page 50"` and returns immediately via the early `return` statement — no further database pages are queried, no further CSV rows are generated for a client that will never read them.
9. Spring MVC notices the stream ended (whether cleanly or early) and completes the async response, releasing any associated resources.

## 7. Gotchas & takeaways

> **Building the entire dataset into a `List` before streaming it defeats the entire purpose of `StreamingResponseBody`.** If your "streaming" handler does `List<Product> all = repository.findAll(); return out -> { for (p : all) out.write(...); }`, you've already paid the full memory cost upfront — the streaming only saves you the *response buffering*, not the *source data* memory. Page through the source data too, as in Level 3.

> **Forgetting to check for a broken pipe (`checkError()` on `PrintWriter`, or catching `IOException` on a raw `OutputStream`) means a slow, resource-intensive generator keeps running for a client that already left.** Under real traffic with many aborted downloads (common for large file exports where users cancel), this wastes significant server-side work.

> **The default async request timeout in Spring Boot is relatively short (typically 30 seconds) and will silently kill long-running streams unless explicitly extended** via `spring.mvc.async.request-timeout` — a large export that legitimately takes minutes will otherwise fail partway through with `AsyncRequestTimeoutException`, confusing anyone who didn't know the default applied to streaming responses too.

- `StreamingResponseBody` is for one-shot, large, or slow-to-generate payloads — not for open-ended event pushing (use `SseEmitter` for that).
- Page/batch the underlying data source too, not just the HTTP response — otherwise you've only moved the memory problem, not solved it.
- Detect and react to client disconnection (`checkError()`, catching `IOException`) so a departed client doesn't keep the server generating unread data.
- Set an explicit, generous-but-bounded async request timeout for any endpoint expected to stream for more than the framework's short default.

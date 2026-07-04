---
card: spring-framework
gi: 203
slug: data-buffers-codecs
title: Data buffers & codecs
---

## 1. What it is

Spring's **data buffer abstraction** (`DataBuffer`, `DataBufferFactory`) is a unified API over raw byte buffers — including Netty's `ByteBuf`, Java NIO's `ByteBuffer`, and others — so reactive code can handle bytes without leaking framework-specific types. **Codecs** (`Encoder<T>`, `Decoder<T>`, `HttpMessageReader<T>`, `HttpMessageWriter<T>`) sit on top: they read or write a stream of `DataBuffer` objects and convert them to/from Java objects (JSON, XML, protobuf, form data).

This machinery powers Spring WebFlux's reactive HTTP layer. When WebFlux receives a request body, it arrives as a `Flux<DataBuffer>`; a codec (e.g. `Jackson2JsonDecoder`) subscribes, accumulates bytes, and deserialises them to a domain object.

## 2. Why & when

Traditional Servlet I/O blocks a thread while reading or writing bytes. Reactive HTTP (WebFlux, Reactor Netty) uses non-blocking I/O — bytes arrive in chunks on event-loop threads. You need:

1. **A common buffer type** that wraps whatever the underlying transport gives you (Netty `ByteBuf`, `ByteBuffer`, etc.) without copying bytes unnecessarily.
2. **Backpressure-aware encoding/decoding** so large payloads are streamed rather than fully loaded into memory.
3. **Pooled buffers** (Netty) that must be explicitly released to avoid memory leaks.

You interact with these APIs when building custom `WebFilter`s that inspect request bodies, writing custom codecs for proprietary binary formats, or tuning WebFlux codec configuration (max in-memory size, CBOR, protobuf).

## 3. Core concept

Think of a `DataBuffer` as a labelled envelope of bytes — it knows how it was allocated, and (for pooled implementations) must be returned to the post office when you're done. A `Codec` is a translator that reads a stream of such envelopes and produces a typed value, or vice versa.

Key types:

| Type | Role |
|------|------|
| `DataBuffer` | Single chunk of bytes (read/write position, capacity) |
| `DataBufferFactory` | Creates `DataBuffer` instances; hides Netty vs JDK differences |
| `DataBufferUtils` | Utility: join, release, read from `InputStream`/`Resource` |
| `Encoder<T>` | `T → Flux<DataBuffer>` (encode object to byte stream) |
| `Decoder<T>` | `Flux<DataBuffer> → Mono<T>` (decode byte stream to object) |
| `HttpMessageReader<T>` | Wraps `Decoder`, handles HTTP content negotiation |
| `HttpMessageWriter<T>` | Wraps `Encoder`, handles HTTP content negotiation |

**Buffer lifecycle:** `DefaultDataBuffer` (JDK-backed) is garbage collected normally. `NettyDataBuffer` is reference-counted — call `DataBufferUtils.release(buffer)` when you're done, or use `DataBufferUtils.join(flux).doFinally(s -> DataBufferUtils.release(joined))`.

## 4. Diagram

<svg viewBox="0 0 640 220" xmlns="http://www.w3.org/2000/svg">
  <!-- HTTP Request -->
  <rect x="15" y="80" width="100" height="50" rx="7" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="65" y="103" fill="#e6edf3" font-size="11" text-anchor="middle" font-family="sans-serif">HTTP Request</text>
  <text x="65" y="119" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">bytes arrive</text>

  <!-- Arrow -->
  <line x1="115" y1="105" x2="170" y2="105" stroke="#79c0ff" stroke-width="1.5" marker-end="url(#a)"/>
  <text x="143" y="97" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">Flux&lt;DataBuffer&gt;</text>

  <!-- Decoder -->
  <rect x="170" y="75" width="130" height="60" rx="7" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="235" y="101" fill="#79c0ff" font-size="11" text-anchor="middle" font-family="sans-serif">Decoder</text>
  <text x="235" y="117" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">(e.g. Jackson2Json)</text>

  <!-- Arrow -->
  <line x1="300" y1="105" x2="360" y2="105" stroke="#6db33f" stroke-width="1.5" marker-end="url(#a)"/>
  <text x="330" y="97" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">Mono&lt;MyDto&gt;</text>

  <!-- Handler -->
  <rect x="360" y="80" width="120" height="50" rx="7" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="420" y="108" fill="#e6edf3" font-size="11" text-anchor="middle" font-family="sans-serif">Handler / Controller</text>

  <!-- Encoder path (response) -->
  <line x1="420" y1="130" x2="420" y2="165" stroke="#6db33f" stroke-width="1" stroke-dasharray="4 2"/>
  <rect x="360" y="165" width="120" height="40" rx="7" fill="#1c2430" stroke="#6db33f" stroke-width="1"/>
  <text x="420" y="188" fill="#6db33f" font-size="10" text-anchor="middle" font-family="sans-serif">Encoder → response</text>

  <!-- Release note -->
  <text x="235" y="155" fill="#e06c75" font-size="9" text-anchor="middle" font-family="sans-serif">release pooled buffers!</text>

  <defs>
    <marker id="a" markerWidth="8" markerHeight="6" refX="8" refY="3" orient="auto">
      <polygon points="0 0,8 3,0 6" fill="#79c0ff"/>
    </marker>
  </defs>
</svg>

Request bytes arrive as `Flux<DataBuffer>`, the decoder assembles them into a typed object, the handler processes it, and an encoder serialises the response back.

## 5. Runnable example

Scenario: a **byte-processing pipeline** — first manually creating and reading a `DataBuffer`, then encoding/decoding a simple object, then a full custom codec that handles a proprietary CSV format.

### Level 1 — Basic

Create a `DataBuffer`, write bytes, read them back.

```java
// DataBufferDemo.java
import org.springframework.core.io.buffer.*;
import java.nio.charset.*;

public class DataBufferDemo {
    public static void main(String[] args) {
        DataBufferFactory factory = new DefaultDataBufferFactory();

        // Allocate a buffer and write a UTF-8 string
        DataBuffer buf = factory.allocateBuffer(64);
        buf.write("Hello, DataBuffer!".getBytes(StandardCharsets.UTF_8));

        // Read back
        byte[] bytes = new byte[buf.readableByteCount()];
        buf.read(bytes);
        System.out.println("Read: " + new String(bytes, StandardCharsets.UTF_8));

        // Release (DefaultDataBuffer is GC'd, but good habit)
        DataBufferUtils.release(buf);
    }
}
```

How to run: `java -cp spring-core.jar:reactor-core.jar:. DataBufferDemo.java`

`DefaultDataBufferFactory` creates a JDK-heap-backed buffer. `write(byte[])` advances the write position; `readableByteCount()` returns how many bytes are available to read. Always release — critical for Netty-backed buffers.

---

### Level 2 — Intermediate

Use `Jackson2JsonEncoder`/`Jackson2JsonDecoder` to encode a Java object to a `Flux<DataBuffer>` and decode it back.

```java
// DataBufferDemo.java
import org.springframework.core.io.buffer.*;
import org.springframework.http.codec.json.*;
import org.springframework.core.*;
import org.springframework.util.*;
import reactor.core.publisher.*;
import java.util.*;

public class DataBufferDemo {
    public static void main(String[] args) {
        var factory = new DefaultDataBufferFactory();
        var encoder = new Jackson2JsonEncoder();
        var decoder = new Jackson2JsonDecoder();

        // Object to encode
        Map<String, Object> payload = Map.of("id", 42, "name", "Alice");

        // Encode: Map -> Flux<DataBuffer>
        Flux<DataBuffer> encoded = encoder.encode(
            Mono.just(payload),
            factory,
            ResolvableType.forClass(Map.class),
            org.springframework.http.MediaType.APPLICATION_JSON,
            Map.of()
        );

        // Decode: Flux<DataBuffer> -> Mono<Map>
        Mono<Map> decoded = decoder.decodeToMono(
            encoded,
            ResolvableType.forClass(Map.class),
            org.springframework.http.MediaType.APPLICATION_JSON,
            Map.of()
        ).cast(Map.class);

        decoded.subscribe(m -> System.out.println("Decoded: " + m));
    }
}
```

How to run: `java -cp spring-core.jar:spring-web.jar:jackson-databind.jar:reactor-core.jar:. DataBufferDemo.java`

`encoder.encode(…)` produces a `Flux<DataBuffer>` containing the JSON bytes. `decoder.decodeToMono(…)` subscribes to that flux, accumulates chunks, and parses the JSON. The `ResolvableType` carries generic type information (like `TypeToken` in Gson).

---

### Level 3 — Advanced

Write a custom `Encoder`/`Decoder` pair for a simple CSV format: `id,name` fields, one record per line.

```java
// DataBufferDemo.java
import org.springframework.core.io.buffer.*;
import org.springframework.core.*;
import org.springframework.http.*;
import org.springframework.http.codec.*;
import reactor.core.publisher.*;
import java.nio.charset.*;
import java.util.*;

// Domain object
record Person(int id, String name) {}

// Custom CSV Encoder
class CsvPersonEncoder implements HttpMessageWriter<Person> {
    private final DataBufferFactory factory = new DefaultDataBufferFactory();

    @Override public List<MediaType> getWritableMediaTypes() {
        return List.of(MediaType.parseMediaType("text/csv"));
    }
    @Override public boolean canWrite(ResolvableType et, MediaType mt) {
        return Person.class.isAssignableFrom(et.toClass());
    }
    @Override public Mono<Void> write(
            org.reactivestreams.Publisher<? extends Person> inputStream,
            ResolvableType et, MediaType ct,
            org.springframework.http.ReactiveHttpOutputMessage msg,
            Map<String,Object> hints) {
        Flux<DataBuffer> body = Flux.from(inputStream).map(p -> {
            String csv = p.id() + "," + p.name() + "\n";
            byte[] bytes = csv.getBytes(StandardCharsets.UTF_8);
            DataBuffer buf = factory.allocateBuffer(bytes.length);
            buf.write(bytes);
            return buf;
        });
        return msg.writeWith(body);
    }
}

// Custom CSV Decoder
class CsvPersonDecoder implements HttpMessageReader<Person> {
    @Override public List<MediaType> getReadableMediaTypes() {
        return List.of(MediaType.parseMediaType("text/csv"));
    }
    @Override public boolean canRead(ResolvableType et, MediaType mt) {
        return Person.class.isAssignableFrom(et.toClass());
    }
    @Override public Flux<Person> read(
            ResolvableType et, org.springframework.http.ReactiveHttpInputMessage msg,
            Map<String,Object> hints) {
        return DataBufferUtils.join(msg.getBody())
            .flatMapMany(buf -> {
                String csv = buf.toString(StandardCharsets.UTF_8);
                DataBufferUtils.release(buf);
                return Flux.fromArray(csv.split("\n"))
                    .filter(line -> !line.isBlank())
                    .map(line -> {
                        String[] parts = line.split(",", 2);
                        return new Person(Integer.parseInt(parts[0].trim()), parts[1].trim());
                    });
            });
    }
    @Override public Mono<Person> readMono(
            ResolvableType et, org.springframework.http.ReactiveHttpInputMessage msg,
            Map<String,Object> hints) {
        return read(et, msg, hints).next();
    }
}

public class DataBufferDemo {
    public static void main(String[] args) {
        // Simulate encoding
        var factory = new DefaultDataBufferFactory();
        var people = List.of(new Person(1, "Alice"), new Person(2, "Bob"));
        Flux<DataBuffer> csvStream = Flux.fromIterable(people).map(p -> {
            byte[] bytes = (p.id() + "," + p.name() + "\n").getBytes(StandardCharsets.UTF_8);
            DataBuffer buf = factory.allocateBuffer(bytes.length);
            buf.write(bytes);
            return buf;
        });

        // Simulate decoding
        DataBufferUtils.join(csvStream)
            .flatMapMany(buf -> {
                String csv = buf.toString(StandardCharsets.UTF_8);
                DataBufferUtils.release(buf);
                return Flux.fromArray(csv.split("\n"))
                    .filter(l -> !l.isBlank())
                    .map(line -> {
                        String[] p = line.split(",", 2);
                        return new Person(Integer.parseInt(p[0].trim()), p[1].trim());
                    });
            })
            .subscribe(p -> System.out.println("Decoded: " + p));
    }
}
```

How to run: `java -cp spring-core.jar:spring-web.jar:reactor-core.jar:. DataBufferDemo.java`

`DataBufferUtils.join(flux)` collects all chunks into one buffer. The `flatMapMany` then splits lines and parses each into a `Person`. `DataBufferUtils.release(buf)` is called immediately after reading the bytes to return the buffer to the pool — skipping this causes memory leaks in Netty environments.

## 6. Walkthrough

**Encoding pipeline (Level 2):**
1. `encoder.encode(Mono.just(payload), factory, …)` is called — no bytes yet; this returns a cold `Flux<DataBuffer>`.
2. `decoder.decodeToMono(encoded, …)` subscribes to the flux — this triggers the encoder.
3. The encoder calls Jackson's `ObjectMapper.writeValueAsBytes(payload)` → `{"id":42,"name":"Alice"}`.
4. It allocates a `DataBuffer` via `factory.allocateBuffer(bytes.length)`, writes the JSON bytes, and emits it.
5. The decoder receives the single `DataBuffer`, reads the bytes, calls `mapper.readValue(bytes, Map.class)`.
6. The result `Map` is emitted by the `Mono<Map>`.

**Custom codec execution (Level 3):**
1. `Flux.fromIterable(people)` emits two `Person` objects.
2. The map operator converts each to a `DataBuffer` containing one CSV line.
3. `DataBufferUtils.join(csvStream)` subscribes and accumulates both `DataBuffer`s into one using `allocateBuffer(sumOfCapacities)` and `buf.write(chunk)`.
4. `toString(UTF_8)` reads all bytes as a string: `"1,Alice\n2,Bob\n"`.
5. `split("\n")` → `["1,Alice", "2,Bob"]`.
6. Each line splits on `,` to construct a `Person` record.
7. `release(buf)` returns the joined buffer to the pool.

**Output:**
```
Decoded: Person[id=1, name=Alice]
Decoded: Person[id=2, name=Bob]
```

## 7. Gotchas & takeaways

> **Netty `ByteBuf` reference counting causes leaks.** When using Reactor Netty (the default WebFlux server), `DataBuffer` wraps a reference-counted `ByteBuf`. Every buffer you receive must be released exactly once with `DataBufferUtils.release(buf)` — or use operators like `DataBufferUtils.join` which handle release internally.

> **`DataBufferUtils.join` loads the full body into memory.** For large request bodies, this defeats streaming. Use `Flux<DataBuffer>` pipelines that process chunks rather than joining them all.

- Never hold a `DataBuffer` across a reactive boundary (e.g., store it in a field for later use) — by then it may already be released.
- `ResolvableType` is Spring's answer to Java's type erasure: `ResolvableType.forClassWithGenerics(List.class, Person.class)` encodes `List<Person>` at runtime.
- `DefaultDataBufferFactory.sharedInstance` is a thread-safe singleton suitable for most non-Netty use cases.
- Custom codecs must be registered via `WebFluxConfigurer.configureHttpMessageCodecs(ServerCodecConfigurer)` to be picked up by WebFlux.
- The `CodecConfigurer.defaultCodecs().maxInMemorySize(size)` setting controls the buffer limit for `decodeToMono` — default is 256 KB; increase for large JSON bodies.

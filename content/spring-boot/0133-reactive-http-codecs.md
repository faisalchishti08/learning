---
card: spring-boot
gi: 133
slug: reactive-http-codecs
title: Reactive HTTP codecs
---

## 1. What it is

**Reactive HTTP codecs** are the read/write pipeline that converts raw bytes (from Reactor Netty's `DataBuffer` stream) into Java objects and back, in a fully non-blocking way. Spring WebFlux uses `HttpMessageReader` and `HttpMessageWriter` interfaces — reactive equivalents of Spring MVC's `HttpMessageConverter`. Spring Boot auto-configures a standard set of codecs (JSON via Jackson, strings, bytes, multipart, SSE) and lets you customise them via `CodecCustomizer` beans or `spring.codec.*` properties.

## 2. Why & when

In Servlet-based Spring MVC, `HttpMessageConverter` reads the request body as a blocking `InputStream`. In WebFlux, the body arrives as a reactive `Flux<DataBuffer>` — a stream of byte chunks that may arrive asynchronously over time. Reactive codecs consume that stream without blocking any thread, which is essential for the event-loop model.

You interact with codec configuration when:

- A response body exceeds the default 256 KB in-memory buffer (`DataBufferLimitException`).
- You need a custom content type deserialised (e.g. `application/cbor`, a proprietary binary format).
- You want to add `@JsonView` filtering or custom Jackson modules globally.

## 3. Core concept

Auto-configured codecs (ordered by priority):

| Codec | Handles |
|---|---|
| `Jackson2JsonEncoder/Decoder` | `application/json`, `application/*+json` |
| `StringDecoder/Encoder` | `text/plain`, `text/*` |
| `ByteArrayDecoder/Encoder` | `application/octet-stream` |
| `ResourceDecoder/Encoder` | `Resource` objects |
| `ServerSentEventHttpMessageReader/Writer` | `text/event-stream` |
| `FormHttpMessageReader/Writer` | `application/x-www-form-urlencoded` |
| `MultipartHttpMessageReader/Writer` | `multipart/form-data` |

`CodecCustomizer` is the hook to modify this list or the `ObjectMapper` used by Jackson codecs.

## 4. Diagram

<svg viewBox="0 0 680 220" xmlns="http://www.w3.org/2000/svg">
  <rect x="20" y="80" width="130" height="60" rx="8" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="85" y="108" text-anchor="middle" fill="#6db33f" font-size="12" font-family="sans-serif">Raw bytes</text>
  <text x="85" y="125" text-anchor="middle" fill="#8b949e" font-size="11" font-family="sans-serif">Flux&lt;DataBuffer&gt;</text>
  <rect x="230" y="80" width="220" height="60" rx="8" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="340" y="105" text-anchor="middle" fill="#79c0ff" font-size="12" font-family="sans-serif">HttpMessageReader</text>
  <text x="340" y="122" text-anchor="middle" fill="#8b949e" font-size="11" font-family="sans-serif">Jackson2JsonDecoder / StringDecoder…</text>
  <rect x="530" y="80" width="130" height="60" rx="8" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="595" y="108" text-anchor="middle" fill="#e6edf3" font-size="12" font-family="sans-serif">Java Object</text>
  <text x="595" y="125" text-anchor="middle" fill="#8b949e" font-size="11" font-family="sans-serif">Mono / Flux</text>
  <line x1="152" y1="110" x2="226" y2="110" stroke="#6db33f" stroke-width="1.5" marker-end="url(#rc)"/>
  <text x="189" y="104" text-anchor="middle" fill="#8b949e" font-size="10" font-family="sans-serif">decode</text>
  <line x1="452" y1="110" x2="526" y2="110" stroke="#79c0ff" stroke-width="1.5" marker-end="url(#rc2)"/>
  <text x="489" y="104" text-anchor="middle" fill="#8b949e" font-size="10" font-family="sans-serif">Mono&lt;T&gt;</text>
  <rect x="230" y="165" width="220" height="40" rx="8" fill="#1c2430" stroke="#8b949e" stroke-width="1"/>
  <text x="340" y="189" text-anchor="middle" fill="#8b949e" font-size="11" font-family="sans-serif">CodecCustomizer (add/modify codecs)</text>
  <defs>
    <marker id="rc" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L6,3 L0,6 Z" fill="#6db33f"/></marker>
    <marker id="rc2" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L6,3 L0,6 Z" fill="#79c0ff"/></marker>
  </defs>
</svg>

Raw byte buffers flow into an `HttpMessageReader` which decodes them into Java objects as a reactive `Mono`; `CodecCustomizer` modifies the codec pipeline at startup.

## 5. Runnable example

```java
// ReactiveCodecsApp.java  —  Spring Boot project with spring-boot-starter-webflux
import com.fasterxml.jackson.databind.ObjectMapper;
import com.fasterxml.jackson.databind.SerializationFeature;
import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.springframework.boot.web.codec.CodecCustomizer;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.http.codec.json.Jackson2JsonEncoder;
import org.springframework.web.bind.annotation.*;
import reactor.core.publisher.Mono;

import java.time.LocalDate;

@SpringBootApplication
public class ReactiveCodecsApp {
    public static void main(String[] args) {
        SpringApplication.run(ReactiveCodecsApp.class, args);
    }
}

record Event(String name, LocalDate date) {}

@Configuration
class CodecConfig {

    @Bean
    public CodecCustomizer jacksonCustomizer() {
        return configurer -> {
            // Use a custom ObjectMapper with pretty-print disabled and dates as ISO strings
            ObjectMapper mapper = new ObjectMapper()
                    .findAndRegisterModules()
                    .disable(SerializationFeature.WRITE_DATES_AS_TIMESTAMPS);

            configurer.defaultCodecs()
                    .jackson2JsonEncoder(new Jackson2JsonEncoder(mapper));

            // Raise the in-memory buffer limit to 2 MB (default is 256 KB)
            configurer.defaultCodecs().maxInMemorySize(2 * 1024 * 1024);
        };
    }
}

@RestController
class EventController {

    @GetMapping("/event")
    public Mono<Event> getEvent() {
        return Mono.just(new Event("Spring Summit", LocalDate.of(2025, 10, 15)));
    }

    @PostMapping("/event")
    public Mono<String> createEvent(@RequestBody Mono<Event> body) {
        return body.map(e -> "Received: " + e.name() + " on " + e.date());
    }
}
```

**How to run:** start the app, then:
- `curl http://localhost:8080/event` — returns JSON with ISO date string (not timestamp).
- `curl -X POST http://localhost:8080/event -H "Content-Type: application/json" -d '{"name":"JavaConf","date":"2025-11-01"}'`

## 6. Walkthrough

- `CodecCustomizer` is a functional interface; the lambda receives a `CodecConfigurer`. The configurer exposes `defaultCodecs()` for modifying the auto-registered set.
- `configurer.defaultCodecs().jackson2JsonEncoder(new Jackson2JsonEncoder(mapper))` replaces the default encoder's `ObjectMapper` with ours — which has `JavaTimeModule` (via `findAndRegisterModules()`) and ISO date serialisation enabled.
- `configurer.defaultCodecs().maxInMemorySize(2 * 1024 * 1024)` raises the buffer limit. When a response body exceeds the limit, Spring WebFlux throws `DataBufferLimitException`; raising the limit is the fix for large JSON payloads.
- `@RequestBody Mono<Event>` in `createEvent` demonstrates reactive decoding — the body bytes arrive as a `Flux<DataBuffer>` and are decoded to `Mono<Event>` by `Jackson2JsonDecoder`. The handler doesn't block.
- `LocalDate` in the `Event` record is serialised as `"2025-10-15"` (ISO) rather than `[2025,10,15]` because `WRITE_DATES_AS_TIMESTAMPS` is disabled.

## 7. Gotchas & takeaways

> `DataBufferLimitException: Exceeded limit on max bytes to buffer` is the most common codec error. Fix: `spring.codec.max-in-memory-size=5MB` in `application.properties`, or set it via `CodecCustomizer`.

> Do not hold `DataBuffer` objects across subscription boundaries — they are pooled by Reactor Netty and must be released after reading. Use the codec layer instead of reading `DataBuffer` manually.

- `spring.codec.max-in-memory-size` property applies to both the server codecs and `WebClient` codecs.
- Custom codecs (for `application/cbor`, Avro, etc.) are registered via `configurer.customCodecs().register(new MyDecoder())`.
- `CodecCustomizer` applies to both the WebFlux server codecs and `WebClient` codecs built from the auto-configured `WebClient.Builder`.
- For multipart file uploads, the relevant codec is `DefaultPartHttpMessageReader`; its buffer limit and disk-offload threshold are controlled separately via `spring.servlet.multipart.*` (or `spring.webflux.multipart.*` for WebFlux).

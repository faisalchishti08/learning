---
card: spring-framework
gi: 389
slug: restclient-synchronous-fluent-client
title: "RestClient (synchronous fluent client)"
---

## 1. What it is

`RestClient` is Spring's modern synchronous HTTP client, introduced in Spring Framework 6.1. It gives you the same fluent, chainable API style as the reactive `WebClient` (request, then body, then headers, then retrieve), but it blocks the calling thread and returns a plain object instead of a `Mono`/`Flux`. It's meant to be the direct successor to `RestTemplate` for teams that write imperative (blocking) code and don't need reactive streams.

```java
RestClient client = RestClient.create("https://api.example.com");

Product product = client.get()
        .uri("/products/{id}", 42)
        .retrieve()
        .body(Product.class);
```

## 2. Why & when

`RestTemplate` has been in "maintenance mode" for years — it still works, but its template-method API (`getForObject`, `postForEntity`, `exchange`, ...) is clunky compared to `WebClient`'s fluent builder. `RestClient` exists to give synchronous applications that same ergonomic API without forcing them onto Reactor's reactive types, which many teams find harder to read, debug, and step through.

Reach for `RestClient` when:

- You're writing a classic Spring MVC (servlet-based) application and don't need non-blocking I/O.
- You want `WebClient`-style fluent chaining (readable request building, built-in error handling hooks) but a plain blocking return value.
- You're modernizing code that currently uses `RestTemplate` — `RestClient` is the recommended replacement for new code.

Stick with `WebClient` if you're already in a reactive WebFlux application, since mixing a blocking client into a reactive pipeline defeats the point of non-blocking I/O.

## 3. Core concept

`RestClient` is built with a small, composable set of steps: pick a method (`get`/`post`/`put`/`delete`/...), set a URI, optionally add headers or a body, then call `retrieve()` to get a response spec, and finally extract the body as a Java type.

```
RestClient.create()
      |
      v
  .get() / .post() / .put() / .delete()   <- choose HTTP method
      |
      v
  .uri("/path/{id}", id)                   <- target URL
      |
      v
  .header(...) / .body(...)                <- optional headers/body
      |
      v
  .retrieve()                              <- send the request, get ResponseSpec
      |
      v
  .body(Type.class) / .toEntity(Type.class) <- convert response body
```

A single `RestClient` instance is thread-safe and meant to be built once (often as a `@Bean`) and reused for every call, just like `RestTemplate` and `WebClient`.

## 4. Diagram

<svg viewBox="0 0 640 200" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="RestClient fluent chain from method to body extraction">
  <rect x="10" y="80" width="110" height="50" rx="8" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="65" y="110" fill="#e6edf3" font-size="12" text-anchor="middle" font-family="sans-serif">.get()</text>

  <rect x="150" y="80" width="110" height="50" rx="8" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="205" y="110" fill="#e6edf3" font-size="12" text-anchor="middle" font-family="sans-serif">.uri(...)</text>

  <rect x="290" y="80" width="110" height="50" rx="8" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="345" y="110" fill="#e6edf3" font-size="12" text-anchor="middle" font-family="sans-serif">.retrieve()</text>

  <rect x="430" y="80" width="160" height="50" rx="8" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="510" y="110" fill="#e6edf3" font-size="12" text-anchor="middle" font-family="sans-serif">.body(Product.class)</text>

  <line x1="120" y1="105" x2="145" y2="105" stroke="#8b949e" stroke-width="2" marker-end="url(#a)"/>
  <line x1="260" y1="105" x2="285" y2="105" stroke="#8b949e" stroke-width="2" marker-end="url(#a)"/>
  <line x1="400" y1="105" x2="425" y2="105" stroke="#8b949e" stroke-width="2" marker-end="url(#a)"/>
  <defs><marker id="a" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#8b949e"/></marker></defs>
</svg>

Each step in the chain narrows the request down until `.body(...)` blocks the thread and returns the deserialized object.

## 5. Runnable example

### Level 1 — Basic

A minimal program that fetches a JSON resource and prints it. It uses a public test API so it runs as-is.

```java
import org.springframework.web.client.RestClient;

public class RestClientBasic {

    record TodoItem(int userId, int id, String title, boolean completed) {}

    public static void main(String[] args) {
        RestClient client = RestClient.create("https://jsonplaceholder.typicode.com");

        TodoItem todoItem = client.get()
                .uri("/todos/{id}", 1)
                .retrieve()
                .body(TodoItem.class);

        System.out.println(todoItem);
    }
}
```

How to run: save as `RestClientBasic.java`, add `spring-web` (and Jackson) on the classpath (or run inside a Spring Boot project with `spring-boot-starter-web`), then `java RestClientBasic.java`.

This builds one `RestClient` pointed at a base URL, issues a `GET /todos/1`, and converts the JSON response body directly into a `TodoItem` record. No manual JSON parsing, no manual connection management — `RestClient` handles serialization via the message converters it shares with Spring MVC.

### Level 2 — Intermediate

Real services return error status codes, and a client that blindly deserializes every response will throw a confusing exception on a 404. This version adds explicit status handling and default headers set once for every request.

```java
import org.springframework.http.HttpStatusCode;
import org.springframework.web.client.RestClient;
import org.springframework.web.client.HttpClientErrorException;

public class RestClientIntermediate {

    record TodoItem(int userId, int id, String title, boolean completed) {}

    public static void main(String[] args) {
        RestClient client = RestClient.builder()
                .baseUrl("https://jsonplaceholder.typicode.com")
                .defaultHeader("Accept", "application/json")
                .build();

        TodoItem todoItem = client.get()
                .uri("/todos/{id}", 999999)
                .retrieve()
                .onStatus(HttpStatusCode::is4xxClientError, (req, res) -> {
                    throw new IllegalStateException("TodoItem not found: " + res.getStatusCode());
                })
                .body(TodoItem.class);

        System.out.println(todoItem);
    }
}
```

How to run: `java RestClientIntermediate.java` (same classpath as Level 1).

The change is `.onStatus(...)`: it intercepts 4xx responses before body conversion happens and lets you translate the raw `ClientHttpResponse` into a domain-specific exception, instead of letting an opaque `HttpClientErrorException` propagate. `defaultHeader` on the builder means every request from this client automatically sends `Accept: application/json`, instead of repeating it on each call.

### Level 3 — Advanced

Production code also needs timeouts (so a hung server doesn't hang your thread forever) and structured error responses (`toEntity` to inspect status + headers, not just the body). This version adds a configured request factory with timeouts and full response inspection.

```java
import org.apache.hc.client5.http.impl.classic.HttpClients;
import org.springframework.http.HttpStatusCode;
import org.springframework.http.ResponseEntity;
import org.springframework.http.client.HttpComponentsClientHttpRequestFactory;
import org.springframework.web.client.RestClient;

import java.time.Duration;

public class RestClientAdvanced {

    record TodoItem(int userId, int id, String title, boolean completed) {}

    public static void main(String[] args) {
        var factory = new HttpComponentsClientHttpRequestFactory(HttpClients.createDefault());
        factory.setConnectTimeout((int) Duration.ofSeconds(2).toMillis());
        factory.setConnectionRequestTimeout((int) Duration.ofSeconds(2).toMillis());

        RestClient client = RestClient.builder()
                .baseUrl("https://jsonplaceholder.typicode.com")
                .requestFactory(factory)
                .defaultHeader("Accept", "application/json")
                .build();

        ResponseEntity<TodoItem> response = client.get()
                .uri("/todos/{id}", 1)
                .retrieve()
                .onStatus(HttpStatusCode::is5xxServerError,
                        (req, res) -> { throw new IllegalStateException("Upstream failure: " + res.getStatusCode()); })
                .toEntity(TodoItem.class);

        System.out.println("status=" + response.getStatusCode());
        System.out.println("headers=" + response.getHeaders().getContentType());
        System.out.println("body=" + response.getBody());
    }
}
```

How to run: needs `org.apache.httpcomponents.client5:httpclient5` on the classpath in addition to `spring-web`; then `java RestClientAdvanced.java` (or add both dependencies to a Spring Boot project and run as a `CommandLineRunner`).

Here a real `HttpComponentsClientHttpRequestFactory` replaces the JDK default so connect timeouts are enforced — without this, a stalled server could block the thread indefinitely. `toEntity(TodoItem.class)` (instead of `body(TodoItem.class)`) returns the full `ResponseEntity`, exposing the status code and headers alongside the body, which is what you need to log or branch on in production code.

## 6. Walkthrough

Trace `RestClientAdvanced.main` end to end:

1. **Factory setup.** `HttpComponentsClientHttpRequestFactory` wraps Apache HttpClient 5 and is configured with 2-second connect and connection-request timeouts. This factory is what actually opens the TCP socket later.
2. **Client build.** `RestClient.builder()` composes the base URL, the custom request factory, and a default `Accept` header into one immutable, thread-safe `RestClient`.
3. **Request assembly.** `.get().uri("/todos/{id}", 1)` expands the URI template to `GET https://jsonplaceholder.typicode.com/todos/1` and records the method/URI/headers into a request spec — nothing has gone over the network yet.
4. **`retrieve()` fires the call.** This is the point where the request is actually sent. Conceptually:

   ```
   Request:  GET /todos/1 HTTP/1.1
             Host: jsonplaceholder.typicode.com
             Accept: application/json

   Response: HTTP/1.1 200 OK
             Content-Type: application/json; charset=utf-8

             {"userId":1,"id":1,"title":"delectus aut autem","completed":false}
   ```
5. **Status interception.** Before the body is touched, `.onStatus(is5xxServerError, ...)` checks the status line. Since this response is `200 OK`, the handler is skipped and processing continues.
6. **Body conversion.** `.toEntity(TodoItem.class)` hands the response bytes to a registered `HttpMessageConverter` (Jackson, since the content type is JSON), which deserializes the JSON object into a `TodoItem` record, and wraps it plus the status/headers into a `ResponseEntity<TodoItem>`.
7. **Return to caller.** The blocking call returns; `main` prints the status (`200 OK`), the content type header, and the deserialized `TodoItem` — the thread was blocked for the duration of steps 4–6, which is the defining trait of a synchronous client.

```
Client thread                         Server
     |--- GET /todos/1 ------------------>|
     |            (thread blocked)        | builds JSON
     |<--- 200 OK + JSON body -------------|
  deserialize -> TodoItem -> ResponseEntity
```

## 7. Gotchas & takeaways

> Gotcha: the default `RestClient.create()` uses the JDK's built-in `HttpClient` request factory, which has no connect/read timeouts configured out of the box — a hanging upstream server can block your thread indefinitely unless you explicitly configure a factory with timeouts, as in Level 3.

- `RestClient` is synchronous/blocking — each call ties up the calling thread until the response arrives; don't use it inside reactive (WebFlux) request-handling threads.
- Build one `RestClient` (or one per base URL) and reuse it; it's immutable and thread-safe, so building a new one per request wastes resources.
- `.retrieve().body(Type.class)` throws `RestClientException` subtypes on 4xx/5xx by default; use `.onStatus(...)` or `.toEntity(...)` when you need to inspect the error response instead of catching an exception.
- Prefer `RestClient` over `RestTemplate` for all new synchronous HTTP client code — `RestTemplate` remains supported but is not actively enhanced.

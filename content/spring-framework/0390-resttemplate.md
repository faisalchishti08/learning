---
card: spring-framework
gi: 390
slug: resttemplate
title: "RestTemplate"
---

## 1. What it is

`RestTemplate` is Spring's original synchronous HTTP client, part of the framework since Spring 3.0. It offers template methods like `getForObject`, `postForEntity`, and `exchange` that send an HTTP request and convert the response body into a Java object in one call. It has been in maintenance mode since `RestClient` and `WebClient` arrived, but it remains extremely common in existing codebases.

```java
RestTemplate restTemplate = new RestTemplate();

Product product = restTemplate.getForObject(
        "https://api.example.com/products/{id}", Product.class, 42);
```

## 2. Why & when

`RestTemplate` predates both the reactive stack and `RestClient`'s fluent API. It exists because, before it, calling an HTTP endpoint from Java meant hand-rolling `HttpURLConnection` or Apache HttpClient code, manually managing streams, and manually parsing JSON. `RestTemplate` bundled connection handling, error translation, and message conversion into a small set of convenience methods.

You'll still see (and need to maintain) `RestTemplate` when:

- Working in an existing codebase built before Spring Framework 6.1 (when `RestClient` was introduced).
- The project depends on Spring Cloud components (like older versions of Feign or load-balanced clients) that are wired around `RestTemplate` beans.
- You need a quick, simple client and don't want to reason about `RestClient`'s newer fluent API for a one-off call.

For any new synchronous client code today, the framework itself recommends `RestClient` instead — it offers a nicer API on top of the same underlying infrastructure.

## 3. Core concept

`RestTemplate` exposes one method per HTTP verb, each with several overloads for how you want the response represented:

```
getForObject(url, Type.class, ...)     -> body only, as Type
getForEntity(url, Type.class, ...)     -> ResponseEntity<Type> (status+headers+body)
postForObject(url, body, Type.class)   -> POST, body only
postForEntity(url, body, Type.class)   -> POST, full ResponseEntity
exchange(url, HttpMethod, HttpEntity, Type.class) -> full control (any verb, custom headers)
delete(url, ...)                       -> DELETE, no response body
```

Under the hood, every method delegates to `execute()`, which opens a connection through a `ClientHttpRequestFactory`, writes the request using an `HttpMessageConverter` (Jackson for JSON, by default), and reads the response back through the same converter mechanism `@RequestBody`/`@ResponseBody` use in Spring MVC.

## 4. Diagram

<svg viewBox="0 0 640 200" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="RestTemplate methods funnel into execute which uses a request factory and message converters">
  <rect x="20" y="20" width="180" height="40" rx="6" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="110" y="45" fill="#e6edf3" font-size="12" text-anchor="middle" font-family="sans-serif">getForObject(...)</text>

  <rect x="20" y="80" width="180" height="40" rx="6" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="110" y="105" fill="#e6edf3" font-size="12" text-anchor="middle" font-family="sans-serif">postForEntity(...)</text>

  <rect x="20" y="140" width="180" height="40" rx="6" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="110" y="165" fill="#e6edf3" font-size="12" text-anchor="middle" font-family="sans-serif">exchange(...)</text>

  <rect x="280" y="80" width="140" height="40" rx="6" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="350" y="105" fill="#e6edf3" font-size="12" text-anchor="middle" font-family="sans-serif">execute()</text>

  <rect x="480" y="80" width="140" height="40" rx="6" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="550" y="98" fill="#e6edf3" font-size="11" text-anchor="middle" font-family="sans-serif">RequestFactory +</text>
  <text x="550" y="112" fill="#e6edf3" font-size="11" text-anchor="middle" font-family="sans-serif">MessageConverters</text>

  <line x1="200" y1="40" x2="345" y2="85" stroke="#8b949e" stroke-width="1.5"/>
  <line x1="200" y1="100" x2="280" y2="100" stroke="#8b949e" stroke-width="1.5" marker-end="url(#a)"/>
  <line x1="200" y1="160" x2="345" y2="115" stroke="#8b949e" stroke-width="1.5"/>
  <line x1="420" y1="100" x2="475" y2="100" stroke="#8b949e" stroke-width="1.5" marker-end="url(#a)"/>
  <defs><marker id="a" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#8b949e"/></marker></defs>
</svg>

Every convenience method eventually funnels through the same `execute()` machinery.

## 5. Runnable example

### Level 1 — Basic

Fetch a single resource and print it.

```java
import org.springframework.web.client.RestTemplate;

public class RestTemplateBasic {

    record TodoItem(int userId, int id, String title, boolean completed) {}

    public static void main(String[] args) {
        RestTemplate restTemplate = new RestTemplate();

        TodoItem todoItem = restTemplate.getForObject(
                "https://jsonplaceholder.typicode.com/todos/{id}", TodoItem.class, 1);

        System.out.println(todoItem);
    }
}
```

How to run: put `spring-web` and Jackson on the classpath (or use a Spring Boot project with `spring-boot-starter-web`), then `java RestTemplateBasic.java`.

`getForObject` builds a `GET` request against the templated URL, substitutes `1` for `{id}`, and converts the JSON response straight into a `TodoItem` record using Jackson — no manual stream reading.

### Level 2 — Intermediate

Real calls need to send a body (POST) and read back status and headers, not just the payload.

```java
import org.springframework.http.*;
import org.springframework.web.client.RestTemplate;

public class RestTemplateIntermediate {

    record TodoItem(int userId, int id, String title, boolean completed) {}
    record NewTodo(int userId, String title, boolean completed) {}

    public static void main(String[] args) {
        RestTemplate restTemplate = new RestTemplate();

        HttpHeaders headers = new HttpHeaders();
        headers.setContentType(MediaType.APPLICATION_JSON);
        HttpEntity<NewTodo> request = new HttpEntity<>(
                new NewTodo(1, "Write tutorial", false), headers);

        ResponseEntity<TodoItem> response = restTemplate.postForEntity(
                "https://jsonplaceholder.typicode.com/todos", request, TodoItem.class);

        System.out.println("status=" + response.getStatusCode());
        System.out.println("body=" + response.getBody());
    }
}
```

How to run: `java RestTemplateIntermediate.java` (same classpath as Level 1).

`HttpEntity` bundles a body with headers so the `Content-Type` is explicit. `postForEntity` (instead of `postForObject`) returns the full `ResponseEntity`, exposing the created resource's status code (`201 Created` from this test API) alongside its body.

### Level 3 — Advanced

Production code needs timeouts and custom error handling — by default, `RestTemplate` throws a generic `RestClientException` on 4xx/5xx, discarding the response body that might explain what went wrong.

```java
import org.springframework.boot.web.client.ClientHttpRequestFactorySettings;
import org.springframework.boot.web.client.ClientHttpRequestFactories;
import org.springframework.http.client.ClientHttpResponse;
import org.springframework.web.client.DefaultResponseErrorHandler;
import org.springframework.web.client.RestTemplate;

import java.io.IOException;
import java.time.Duration;

public class RestTemplateAdvanced {

    record TodoItem(int userId, int id, String title, boolean completed) {}

    public static void main(String[] args) {
        var settings = ClientHttpRequestFactorySettings.defaults()
                .withConnectTimeout(Duration.ofSeconds(2))
                .withReadTimeout(Duration.ofSeconds(2));

        RestTemplate restTemplate = new RestTemplate(
                ClientHttpRequestFactories.get(settings));

        restTemplate.setErrorHandler(new DefaultResponseErrorHandler() {
            @Override
            public void handleError(ClientHttpResponse response) throws IOException {
                throw new IllegalStateException(
                        "Upstream call failed: " + response.getStatusCode()
                                + " body=" + new String(response.getBody().readAllBytes()));
            }
        });

        TodoItem todoItem = restTemplate.getForObject(
                "https://jsonplaceholder.typicode.com/todos/{id}", TodoItem.class, 1);
        System.out.println(todoItem);
    }
}
```

How to run: run inside a Spring Boot project (`spring-boot-starter-web`) so `ClientHttpRequestFactories`/`ClientHttpRequestFactorySettings` are on the classpath, then execute `RestTemplateAdvanced.main`.

Timeouts are set via `ClientHttpRequestFactorySettings` so a stalled server fails fast instead of hanging the thread. The custom `DefaultResponseErrorHandler` override reads the actual error body before throwing, so failures carry the upstream's explanation instead of being swallowed.

## 6. Walkthrough

Trace `RestTemplateAdvanced.main`:

1. **Factory configuration.** `ClientHttpRequestFactorySettings` captures a 2-second connect and read timeout; `ClientHttpRequestFactories.get(settings)` builds a concrete `ClientHttpRequestFactory` honoring them.
2. **Template construction.** `new RestTemplate(factory)` wires that factory in, and `setErrorHandler(...)` replaces the default error handling.
3. **Method call.** `getForObject(url, TodoItem.class, 1)` expands the template, producing `GET /todos/1`.
4. **Request sent.**

   ```
   Request:  GET /todos/1 HTTP/1.1
             Host: jsonplaceholder.typicode.com

   Response: HTTP/1.1 200 OK
             Content-Type: application/json

             {"userId":1,"id":1,"title":"delectus aut autem","completed":false}
   ```
5. **Error-handler check.** Before conversion, `RestTemplate` asks the error handler whether the response counts as an error (via `hasError()`, based on the status code). `200 OK` is not an error, so the custom `handleError` is never invoked.
6. **Body conversion.** The response bytes and `Content-Type: application/json` are handed to the `MappingJackson2HttpMessageConverter`, producing a `TodoItem` record.
7. **Return.** `getForObject` returns the `TodoItem` synchronously; `main` prints it. Had the server responded `404`, step 5 would have triggered `handleError`, which reads the response body and throws `IllegalStateException` with the upstream's message included.

```
Client thread                         Server
     |--- GET /todos/1 ------------------>|
     |            (thread blocked)        |
     |<--- 200 OK + JSON -------------------|
  hasError()? no -> convert -> TodoItem
```

## 7. Gotchas & takeaways

> Gotcha: the default `RestTemplate()` constructor uses `SimpleClientHttpRequestFactory` under the JDK's `HttpURLConnection`, which has no connect/read timeout by default — exactly like `RestClient`'s default, a slow or dead upstream can hang the calling thread indefinitely unless you configure timeouts explicitly.

- `RestTemplate` is in maintenance mode; use `RestClient` for new synchronous client code, but expect to keep reading and fixing `RestTemplate` code in existing projects for years.
- Build one `RestTemplate` (ideally as a Spring `@Bean`) and reuse it across the application; it's thread-safe once configured.
- The default error handler discards the response body on 4xx/5xx — override `ResponseErrorHandler` if you need the server's error payload for logging or user-facing messages.
- `exchange()` is the escape hatch for anything the convenience methods don't cover: custom HTTP methods, generic collection types via `ParameterizedTypeReference`, or fine-grained header control.

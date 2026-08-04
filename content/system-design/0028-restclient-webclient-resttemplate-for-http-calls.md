---
card: system-design
gi: 28
slug: restclient-webclient-resttemplate-for-http-calls
title: "RestClient / WebClient / RestTemplate for HTTP calls"
---

## 1. What it is

Spring provides three different HTTP client tools for one service to call another over REST: **RestTemplate** (the original, older, synchronous client, now in maintenance mode), **WebClient** (the newer, non-blocking, reactive client), and **RestClient** (a modern, synchronous client with a fluent, easy-to-read API, introduced to give a simple blocking option without RestTemplate's older, more awkward design).

## 2. Why & when

Whenever a Spring service needs to call another HTTP service — a downstream microservice, a third-party API — it needs one of these three clients. Which one you pick affects both code readability and, for `WebClient`, whether the call blocks the calling thread while waiting for a response. This ties directly back to the synchronous-vs-asynchronous tradeoff covered earlier in this section: `RestTemplate` and `RestClient` are synchronous (blocking); `WebClient` supports non-blocking, asynchronous calls.

## 3. Core concept

**RestTemplate:** the original Spring HTTP client, synchronous (blocking) only. Still widely used in existing codebases, but Spring's documentation now recommends `RestClient` for new synchronous code, since `RestTemplate`'s API predates modern Java features like fluent builders.

**RestClient:** a modern synchronous client with a fluent, chainable API, introduced as the recommended replacement for `RestTemplate` in new blocking code. It reads like a sentence: `restClient.get().uri(...).retrieve().body(...)`.

**WebClient:** part of Spring's reactive stack (Spring WebFlux). It is non-blocking: calling it returns immediately with a `Mono` (a publisher of zero or one result) or `Flux` (a publisher of zero or many results), and the actual HTTP call happens asynchronously, with your code reacting to the result when it arrives, rather than waiting for it inline.

**How Spring wires these in:** each is typically configured once as a `@Bean` (often with a base URL, timeouts, and default headers set centrally), then injected wherever a service needs to make outbound calls — keeping HTTP configuration in one place instead of repeated across every call site.

| Client | Blocking? | Best fit |
|---|---|---|
| `RestTemplate` | Yes (blocking) | Legacy code; avoid in new code |
| `RestClient` | Yes (blocking) | New synchronous code — the modern default |
| `WebClient` | No (non-blocking, reactive) | High-concurrency services, reactive stacks |

## 4. Diagram

```
 Your Service (Controller/Service layer)
        |
        | uses an injected, pre-configured bean
        v
 RestClient / WebClient / RestTemplate  --HTTP request-->  Downstream Service
        |                                                          |
        |<-------------------------HTTP response-------------------|
        v
 .body(SomeDto.class) -- deserialized into your Java type
```
*Caption: a pre-configured client bean sends the HTTP request and deserializes the response body into a typed Java object.*

## 5. Runnable example

### Artifact: minimal Java showing the three clients' call styles side by side (using RestClient, Spring's modern synchronous default)

```java
import org.springframework.web.client.RestClient;

public class HttpClientDemo {

    record User(int id, String name) {}

    public static void main(String[] args) {
        // In a real Spring app, this bean is configured once and injected;
        // shown here directly for a runnable, minimal example.
        RestClient restClient = RestClient.builder()
            .baseUrl("https://api.example.com")
            .build();

        // Fluent, readable call chain: GET /users/42 -> deserialize into User.
        User user = restClient.get()
            .uri("/users/{id}", 42)
            .retrieve()
            .body(User.class);

        System.out.println("Fetched user: " + user);

        // For comparison, WebClient's equivalent call is non-blocking:
        // webClient.get().uri("/users/{id}", 42).retrieve().bodyToMono(User.class)
        //     .subscribe(u -> System.out.println("Async result: " + u));
        // -- note: .subscribe() returns immediately; the callback runs later.
    }
}
```

**How to run:** this snippet needs the `spring-web` dependency on the classpath (`org.springframework:spring-web`) to compile and run, since `RestClient` is a Spring class, not part of core Java. In a full Spring Boot project, add `spring-boot-starter-web` and run via your build tool; the call chain shown works identically once the dependency is present.

## 6. Walkthrough

1. `RestClient.builder().baseUrl(...).build()` creates a configured client instance, in a real app this is normally done once as a `@Bean` and injected wherever needed, rather than rebuilt per call.
2. `.get().uri("/users/{id}", 42)` builds a `GET` request to `/users/42`, with the URI template variable substituted safely.
3. `.retrieve()` actually sends the request and prepares to read the response.
4. `.body(User.class)` blocks until the response arrives, then deserializes the JSON response body directly into a `User` record — this is the synchronous, blocking behavior: the calling thread waits here.
5. The commented-out `WebClient` example shows the contrast: `.subscribe(...)` returns immediately, and the callback inside it runs later, asynchronously, once the response actually arrives — the calling thread is never blocked waiting.
6. Expected output (assuming the downstream API returns `{"id":42,"name":"Ada"}`):
```
Fetched user: User[id=42, name=Ada]
```

## 7. Gotchas & takeaways

> **Gotcha:** using `WebClient` inside a traditional blocking Spring MVC application, then immediately calling `.block()` on its result to force it to behave synchronously. This throws away all of `WebClient`'s non-blocking benefit while adding its reactive complexity — if you need blocking behavior, use `RestClient` instead.

- `RestTemplate`: legacy, avoid for new code. `RestClient`: the modern synchronous default. `WebClient`: the non-blocking, reactive choice.
- Configure HTTP clients once as a `@Bean` with shared settings (base URL, timeouts), rather than constructing them per call site.
- Match the client to your application's concurrency model: blocking Spring MVC apps fit `RestClient`; reactive Spring WebFlux apps fit `WebClient`.

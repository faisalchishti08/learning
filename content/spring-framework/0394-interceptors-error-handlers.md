---
card: spring-framework
gi: 394
slug: interceptors-error-handlers
title: "Interceptors & error handlers"
---

## 1. What it is

`ClientHttpRequestInterceptor` (for `RestTemplate`) and `ExchangeFilterFunction` (for `WebClient`), together with `ResponseErrorHandler`, are the hook points that let you run code around every outgoing HTTP call a client makes — adding headers, logging, retrying, or translating errors — without repeating that logic at every call site.

```java
ClientHttpRequestInterceptor loggingInterceptor = (request, body, execution) -> {
    System.out.println("Calling " + request.getURI());
    return execution.execute(request, body);
};
restTemplate.getInterceptors().add(loggingInterceptor);
```

## 2. Why & when

Every real HTTP client needs cross-cutting behavior — an auth header on every request, a correlation ID for tracing, request/response logging, or a consistent way of turning a 4xx/5xx into a domain exception. Interceptors and error handlers exist so that behavior lives in one place instead of being copy-pasted into every `.get()`/`.post()` call.

Use interceptors when you need to:

- Add a header (bearer token, correlation ID, API key) to every outgoing request from a given client.
- Log requests and responses uniformly for debugging or auditing.
- Implement client-side retry or circuit-breaking logic around the actual network call.

Use a custom `ResponseErrorHandler` (or `RestClient`'s `onStatus`/`defaultStatusHandler`) when you want non-2xx responses translated into meaningful exceptions instead of the framework's generic `HttpClientErrorException`/`HttpServerErrorException`.

## 3. Core concept

```
RestTemplate.execute()
     |
     v
 Interceptor 1 --> Interceptor 2 --> ... --> actual network call
     |                  |                          |
     |  each interceptor can inspect/modify        |
     |  the request, then call execution.execute()  |
     |  to pass control to the next one              |
     v
 response comes back up through the same chain
     |
     v
 ResponseErrorHandler.hasError(response)?
     |                    |
    yes                   no
     |                    |
handleError(response)   convert body to Java type
```

Interceptors form a chain — the classic chain-of-responsibility pattern — where each one decides whether (and how) to call the next. The error handler runs once, after the full chain, right before the response body would be converted.

## 4. Diagram

<svg viewBox="0 0 640 200" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Interceptor chain wraps the actual HTTP call, error handler runs on the way back">
  <rect x="10" y="70" width="120" height="46" rx="8" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="70" y="98" fill="#e6edf3" font-size="11" text-anchor="middle" font-family="sans-serif">Auth header</text>

  <rect x="160" y="70" width="120" height="46" rx="8" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="220" y="98" fill="#e6edf3" font-size="11" text-anchor="middle" font-family="sans-serif">Logging</text>

  <rect x="310" y="70" width="130" height="46" rx="8" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="375" y="98" fill="#e6edf3" font-size="11" text-anchor="middle" font-family="sans-serif">Network call</text>

  <rect x="480" y="70" width="150" height="46" rx="8" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="555" y="90" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">ResponseErrorHandler</text>
  <text x="555" y="105" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">hasError? handleError</text>

  <line x1="130" y1="93" x2="155" y2="93" stroke="#3fb950" stroke-width="2" marker-end="url(#a)"/>
  <line x1="280" y1="93" x2="305" y2="93" stroke="#3fb950" stroke-width="2" marker-end="url(#a)"/>
  <line x1="440" y1="88" x2="475" y2="88" stroke="#79c0ff" stroke-width="2" marker-end="url(#b)"/>
  <defs>
    <marker id="a" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#3fb950"/></marker>
    <marker id="b" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#79c0ff"/></marker>
  </defs>
</svg>

Requests flow left-to-right through interceptors before hitting the network; the error handler inspects the response on the way back, before body conversion.

## 5. Runnable example

### Level 1 — Basic

A single logging interceptor added to `RestTemplate`.

```java
import org.springframework.http.client.ClientHttpRequestInterceptor;
import org.springframework.web.client.RestTemplate;

public class InterceptorBasic {

    record TodoItem(int userId, int id, String title, boolean completed) {}

    public static void main(String[] args) {
        RestTemplate restTemplate = new RestTemplate();

        ClientHttpRequestInterceptor logging = (request, body, execution) -> {
            System.out.println(">> " + request.getMethod() + " " + request.getURI());
            var response = execution.execute(request, body);
            System.out.println("<< " + response.getStatusCode());
            return response;
        };
        restTemplate.getInterceptors().add(logging);

        TodoItem todoItem = restTemplate.getForObject(
                "https://jsonplaceholder.typicode.com/todos/{id}", TodoItem.class, 1);
        System.out.println(todoItem);
    }
}
```

How to run: `java InterceptorBasic.java` with `spring-web` and Jackson on the classpath.

The lambda receives the outgoing `request`, its `body` bytes, and an `execution` object representing "the rest of the chain." Calling `execution.execute(request, body)` actually sends the request and returns the response — logging before and after that call brackets the real network I/O.

### Level 2 — Intermediate

Add a second interceptor for an auth header, showing that order matters (they compose), plus a custom error handler that reads the error body instead of discarding it.

```java
import org.springframework.http.client.ClientHttpRequestInterceptor;
import org.springframework.http.client.ClientHttpResponse;
import org.springframework.web.client.DefaultResponseErrorHandler;
import org.springframework.web.client.RestTemplate;

import java.io.IOException;

public class InterceptorIntermediate {

    record TodoItem(int userId, int id, String title, boolean completed) {}

    public static void main(String[] args) {
        RestTemplate restTemplate = new RestTemplate();

        ClientHttpRequestInterceptor auth = (request, body, execution) -> {
            request.getHeaders().add("Authorization", "Bearer demo-token");
            return execution.execute(request, body);
        };
        ClientHttpRequestInterceptor logging = (request, body, execution) -> {
            System.out.println(">> " + request.getMethod() + " " + request.getURI());
            return execution.execute(request, body);
        };
        restTemplate.getInterceptors().add(auth);
        restTemplate.getInterceptors().add(logging);

        restTemplate.setErrorHandler(new DefaultResponseErrorHandler() {
            @Override
            public void handleError(ClientHttpResponse response) throws IOException {
                String errorBody = new String(response.getBody().readAllBytes());
                throw new IllegalStateException(
                        "Call failed: " + response.getStatusCode() + " -> " + errorBody);
            }
        });

        TodoItem todoItem = restTemplate.getForObject(
                "https://jsonplaceholder.typicode.com/todos/{id}", TodoItem.class, 1);
        System.out.println(todoItem);
    }
}
```

How to run: `java InterceptorIntermediate.java` (same classpath as Level 1).

Interceptors run in the order they're added: `auth` sets the header first, then calls `execution.execute`, which invokes `logging`, which calls the real network execution — so the log line prints the request *with* the auth header already attached. The custom error handler reads and includes the response body on failure, unlike the default which discards it.

### Level 3 — Advanced

A production interceptor chain often needs to add a correlation ID per request (for distributed tracing) and retry idempotent GET calls on transient network failures — both implemented purely as interceptors, with no change to call sites.

```java
import org.springframework.http.HttpMethod;
import org.springframework.http.client.ClientHttpRequestInterceptor;
import org.springframework.http.client.ClientHttpResponse;
import org.springframework.web.client.RestTemplate;

import java.io.IOException;
import java.util.UUID;

public class InterceptorAdvanced {

    record TodoItem(int userId, int id, String title, boolean completed) {}

    public static void main(String[] args) {
        RestTemplate restTemplate = new RestTemplate();

        ClientHttpRequestInterceptor correlationId = (request, body, execution) -> {
            request.getHeaders().add("X-Correlation-Id", UUID.randomUUID().toString());
            return execution.execute(request, body);
        };

        ClientHttpRequestInterceptor retryOnFailure = (request, body, execution) -> {
            if (request.getMethod() != HttpMethod.GET) {
                return execution.execute(request, body); // only retry idempotent calls
            }
            IOException lastError = null;
            for (int attempt = 1; attempt <= 3; attempt++) {
                try {
                    ClientHttpResponse response = execution.execute(request, body);
                    if (response.getStatusCode().is5xxServerError() && attempt < 3) {
                        System.out.println("Attempt " + attempt + " got 5xx, retrying...");
                        continue;
                    }
                    return response;
                } catch (IOException ex) {
                    lastError = ex;
                    System.out.println("Attempt " + attempt + " failed: " + ex.getMessage());
                }
            }
            throw lastError;
        };

        restTemplate.getInterceptors().add(correlationId);
        restTemplate.getInterceptors().add(retryOnFailure);

        TodoItem todoItem = restTemplate.getForObject(
                "https://jsonplaceholder.typicode.com/todos/{id}", TodoItem.class, 1);
        System.out.println(todoItem);
    }
}
```

How to run: `java InterceptorAdvanced.java` with `spring-web` and Jackson on the classpath.

`retryOnFailure` guards on `HttpMethod.GET` because retrying a `POST` blindly could duplicate a non-idempotent write — a real production concern, not a demo simplification. It calls `execution.execute` up to three times, retrying on 5xx responses or `IOException`, and only propagates the final failure after all attempts are exhausted.

## 6. Walkthrough

Trace `InterceptorAdvanced.main` for a normal successful call:

1. **Interceptor list built.** `restTemplate.getInterceptors()` holds `[correlationId, retryOnFailure]` in that order, wrapped internally into a single chain by `InterceptingHttpAccessor`.
2. **Call initiated.** `getForObject(...)` eventually calls `restTemplate.execute(...)`, which hands off to the first interceptor in the chain, `correlationId`.
3. **`correlationId` runs.** It adds an `X-Correlation-Id: <uuid>` header to the request, then calls `execution.execute(request, body)` — this hands control to the *next* interceptor, `retryOnFailure`, not directly to the network yet.
4. **`retryOnFailure` runs.** Since the method is `GET`, it enters its retry loop and calls `execution.execute(request, body)` again — this time, because it's the last interceptor, `execution.execute` performs the actual network call.
5. **Real HTTP exchange.**

   ```
   Request:  GET /todos/1 HTTP/1.1
             Host: jsonplaceholder.typicode.com
             X-Correlation-Id: 3fa1...  (added in step 3)

   Response: HTTP/1.1 200 OK
             Content-Type: application/json

             {"userId":1,"id":1,"title":"delectus aut autem","completed":false}
   ```
6. **Response climbs back up.** `retryOnFailure` sees a `200` (not 5xx), so it returns the response immediately without retrying — the response then passes back up through `correlationId`, which returns it unchanged, back to `RestTemplate`'s core `execute` logic.
7. **Error handler check, then conversion.** `RestTemplate` asks its `ResponseErrorHandler` whether this response `hasError()` — `200` is not an error — so the body is converted to a `TodoItem` via the JSON message converter and returned to `main`.

```
correlationId  -> adds header -> calls next
   retryOnFailure -> (GET, loop) -> calls next -> [real network I/O] -> 200 OK
   retryOnFailure -> not 5xx -> return response
correlationId  -> return response
RestTemplate   -> hasError? no -> convert -> TodoItem
```

If step 5 had returned a 503, `retryOnFailure` would log "Attempt 1 got 5xx, retrying..." and loop back to call `execution.execute` again — the correlation ID interceptor is *not* re-entered on retry, since the retry loop lives entirely inside `retryOnFailure` and reuses the same already-headers-attached request.

## 7. Gotchas & takeaways

> Gotcha: retrying non-idempotent requests (`POST`, sometimes `PATCH`) blindly can duplicate side effects — e.g., retrying a failed-looking `POST /orders` that actually succeeded server-side but timed out on the response can create two orders. Always gate retry interceptors on HTTP method (or an explicit idempotency key) rather than retrying everything uniformly.

- Interceptors compose in the order they're added to the list; put cross-cutting concerns like correlation IDs before behavior that depends on them, like logging or retries.
- `RestClient`/`WebClient` have their own equivalent hooks (`ClientHttpRequestInterceptor` also works with `RestClient`; `WebClient` uses `ExchangeFilterFunction` via `.filter(...)`) — the same chain-of-responsibility pattern applies across all three clients.
- A custom `ResponseErrorHandler` (or `RestClient`'s `onStatus`) is the right place to translate HTTP status codes into typed exceptions once, instead of checking status codes at every call site.
- Keep interceptors focused and composable — one interceptor per concern (auth, logging, retry, tracing) is easier to test and reorder than one interceptor doing everything.

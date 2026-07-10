---
card: spring-framework
gi: 392
slug: http-interface-httpexchange-declarative-clients
title: "HTTP Interface (@HttpExchange declarative clients)"
---

## 1. What it is

The HTTP Interface feature lets you declare an HTTP client as a plain Java interface, annotated with `@HttpExchange` (and its shortcuts `@GetExchange`, `@PostExchange`, etc.), instead of writing imperative `RestClient`/`WebClient` call chains by hand. At startup, Spring generates a proxy implementation of the interface backed by a `RestClient` or `WebClient`, so calling a method on the interface actually performs the HTTP call.

```java
public interface TodoClient {
    @GetExchange("/todos/{id}")
    TodoItem getTodo(@PathVariable int id);
}
```

## 2. Why & when

Writing out `.get().uri(...).retrieve().body(...)` for every endpoint of a service you call gets repetitive, and it mixes HTTP plumbing with your business logic at every call site. HTTP Interface exists to let you describe *what* a remote API looks like — its endpoints, parameters, and return types — as a plain interface, the same way Spring Data lets you describe a repository as an interface instead of writing SQL by hand.

Use it when:

- You call the same external or internal service from multiple places and want one typed contract for it instead of scattered client-building code.
- You want your business logic to depend on a clean interface (easy to mock in tests) rather than a concrete `RestClient`/`WebClient` chain.
- You're already comfortable with `RestClient` or `WebClient`, since HTTP Interface is a thin declarative layer built directly on top of one of them — it does not replace understanding how the underlying client works.

Skip it for a single one-off call where writing the interface is more ceremony than the call itself would be.

## 3. Core concept

```
 interface TodoClient {
     @GetExchange("/todos/{id}")
     TodoItem getTodo(@PathVariable int id);
 }
        |
        v
 HttpServiceProxyFactory.builder(adapter).build()
        |
        v
 TodoClient proxy = factory.createClient(TodoClient.class)
        |
        v
 proxy.getTodo(1)  --> proxy translates method call into
                        client.get().uri("/todos/{id}", 1).retrieve().body(TodoItem.class)
```

The interface method's annotations (`@GetExchange`, `@PathVariable`, `@RequestParam`, `@RequestBody`) describe the HTTP request declaratively; the proxy interprets them at call time and delegates to a real `RestClient` (blocking) or `WebClient` (reactive) that you supply — the interface itself doesn't care which.

## 4. Diagram

<svg viewBox="0 0 640 190" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Interface method call is proxied into a RestClient or WebClient HTTP call">
  <rect x="10" y="70" width="170" height="50" rx="8" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="95" y="100" fill="#e6edf3" font-size="12" text-anchor="middle" font-family="sans-serif">client.getTodo(1)</text>

  <rect x="240" y="70" width="170" height="50" rx="8" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="325" y="94" fill="#e6edf3" font-size="11" text-anchor="middle" font-family="sans-serif">JDK dynamic proxy</text>
  <text x="325" y="110" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">reads @GetExchange</text>

  <rect x="470" y="70" width="160" height="50" rx="8" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="550" y="94" fill="#e6edf3" font-size="11" text-anchor="middle" font-family="sans-serif">RestClient / WebClient</text>
  <text x="550" y="110" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">GET /todos/1</text>

  <line x1="180" y1="95" x2="235" y2="95" stroke="#8b949e" stroke-width="2" marker-end="url(#a)"/>
  <line x1="410" y1="95" x2="465" y2="95" stroke="#8b949e" stroke-width="2" marker-end="url(#a)"/>
  <defs><marker id="a" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#8b949e"/></marker></defs>
</svg>

Your code only ever sees the interface; the proxy and underlying client stay hidden.

## 5. Runnable example

### Level 1 — Basic

Declare the interface, build the proxy from a `RestClient`, and call a method.

```java
import org.springframework.web.bind.annotation.GetExchange;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.client.RestClient;
import org.springframework.web.client.support.RestClientAdapter;
import org.springframework.web.service.invoker.HttpServiceProxyFactory;

public class HttpInterfaceBasic {

    interface TodoClient {
        @GetExchange("/todos/{id}")
        TodoItem getTodo(@PathVariable int id);
    }

    record TodoItem(int userId, int id, String title, boolean completed) {}

    public static void main(String[] args) {
        RestClient restClient = RestClient.create("https://jsonplaceholder.typicode.com");
        RestClientAdapter adapter = RestClientAdapter.create(restClient);
        HttpServiceProxyFactory factory = HttpServiceProxyFactory.builderFor(adapter).build();

        TodoClient client = factory.createClient(TodoClient.class);
        TodoItem todoItem = client.getTodo(1);

        System.out.println(todoItem);
    }
}
```

How to run: needs `spring-web` on the classpath (or a Spring Boot project with `spring-boot-starter-web`), then `java HttpInterfaceBasic.java`.

`RestClientAdapter.create(restClient)` bridges the generic proxy machinery to a specific `RestClient` instance; `HttpServiceProxyFactory` uses that adapter to build a real `TodoClient` implementation. Calling `client.getTodo(1)` looks like a plain method call but performs a real `GET /todos/1` underneath.

### Level 2 — Intermediate

Real interfaces have multiple endpoints, including ones that send a request body and ones that use query parameters — declared the same way `@RequestMapping` methods are declared on a `@RestController`.

```java
import org.springframework.web.bind.annotation.*;
import org.springframework.web.client.RestClient;
import org.springframework.web.client.support.RestClientAdapter;
import org.springframework.web.service.invoker.HttpServiceProxyFactory;

import java.util.List;

public class HttpInterfaceIntermediate {

    record TodoItem(int userId, int id, String title, boolean completed) {}
    record NewTodo(int userId, String title, boolean completed) {}

    interface TodoClient {
        @GetExchange("/todos/{id}")
        TodoItem getTodo(@PathVariable int id);

        @GetExchange("/todos")
        List<TodoItem> getTodosByUser(@RequestParam int userId);

        @PostExchange("/todos")
        TodoItem createTodo(@RequestBody NewTodo newTodo);
    }

    public static void main(String[] args) {
        RestClient restClient = RestClient.create("https://jsonplaceholder.typicode.com");
        TodoClient client = HttpServiceProxyFactory
                .builderFor(RestClientAdapter.create(restClient))
                .build()
                .createClient(TodoClient.class);

        List<TodoItem> todos = client.getTodosByUser(1);
        System.out.println("Found " + todos.size() + " todos for user 1");

        TodoItem created = client.createTodo(new NewTodo(1, "Learn HTTP Interface", false));
        System.out.println("Created: " + created);
    }
}
```

How to run: `java HttpInterfaceIntermediate.java` (same classpath as Level 1).

`@RequestParam int userId` on `getTodosByUser` turns into `?userId=1` on the query string. `@PostExchange` plus `@RequestBody` sends `newTodo` as a JSON body with `POST`. Notice the interface reads exactly like a `@RestController`'s method signatures, just describing an outbound call instead of an inbound one.

### Level 3 — Advanced

Production interfaces need per-call timeouts and error translation, and often need to swap the underlying client between blocking and reactive without changing the interface. This example configures a timeout-aware `RestClient` and adds a default exception-translating error handler.

```java
import org.apache.hc.client5.http.impl.classic.HttpClients;
import org.springframework.http.client.HttpComponentsClientHttpRequestFactory;
import org.springframework.web.bind.annotation.*;
import org.springframework.web.client.RestClient;
import org.springframework.web.client.support.RestClientAdapter;
import org.springframework.web.service.invoker.HttpServiceProxyFactory;

import java.time.Duration;

public class HttpInterfaceAdvanced {

    record TodoItem(int userId, int id, String title, boolean completed) {}

    static class TodoNotFoundException extends RuntimeException {
        TodoNotFoundException(int id) { super("TodoItem " + id + " not found"); }
    }

    interface TodoClient {
        @GetExchange("/todos/{id}")
        TodoItem getTodo(@PathVariable int id);
    }

    public static void main(String[] args) {
        var factory = new HttpComponentsClientHttpRequestFactory(HttpClients.createDefault());
        factory.setConnectTimeout((int) Duration.ofSeconds(2).toMillis());

        RestClient restClient = RestClient.builder()
                .baseUrl("https://jsonplaceholder.typicode.com")
                .requestFactory(factory)
                .defaultStatusHandler(status -> status.value() == 404,
                        (req, res) -> { throw new TodoNotFoundException(0); })
                .build();

        TodoClient client = HttpServiceProxyFactory
                .builderFor(RestClientAdapter.create(restClient))
                .build()
                .createClient(TodoClient.class);

        try {
            TodoItem missing = client.getTodo(999999);
            System.out.println(missing);
        } catch (TodoNotFoundException e) {
            System.out.println("Handled cleanly: " + e.getMessage());
        }
    }
}
```

How to run: needs `httpclient5` plus `spring-web` on the classpath, then `java HttpInterfaceAdvanced.java`.

The timeout and error translation live entirely in how the `RestClient` is configured — the `TodoClient` interface itself never changes. `defaultStatusHandler` converts every `404` from any interface method into a typed `TodoNotFoundException`, so callers of `client.getTodo(...)` catch a meaningful exception instead of a generic HTTP error.

## 6. Walkthrough

Trace `HttpInterfaceAdvanced.main`:

1. **Request factory built.** A `HttpComponentsClientHttpRequestFactory` with a 2-second connect timeout is created, same underlying mechanism as the `RestClient` card.
2. **`RestClient` built.** `.defaultStatusHandler(...)` registers a rule: any response with status 404 triggers the given handler for every call made through this client, regardless of which interface method triggered it.
3. **Proxy created.** `RestClientAdapter.create(restClient)` + `HttpServiceProxyFactory` produce a `TodoClient` proxy backed by that specific configured `RestClient`.
4. **Method invocation.** `client.getTodo(999999)` looks like a normal call; internally, the proxy's `InvocationHandler` inspects the `@GetExchange("/todos/{id}")` annotation and the `@PathVariable` parameter to build the request description.
5. **Delegation to `RestClient`.** The proxy calls the equivalent of `restClient.get().uri("/todos/{id}", 999999).retrieve().body(TodoItem.class)`.
6. **HTTP exchange.**

   ```
   Request:  GET /todos/999999 HTTP/1.1
             Host: jsonplaceholder.typicode.com

   Response: HTTP/1.1 404 Not Found
   ```
7. **Status handler fires.** Because the response status is 404, the registered `defaultStatusHandler` runs before any body conversion is attempted, throwing `TodoNotFoundException`.
8. **Exception propagates.** The exception travels back up through the proxy's `InvocationHandler` and out of `client.getTodo(...)` exactly as if `getTodo` had thrown it directly — the caller in `main` catches `TodoNotFoundException` in the `try/catch` without knowing an HTTP call or a proxy was involved at all.

```
main() -> client.getTodo(999999)
             -> proxy reads @GetExchange
                 -> RestClient GET /todos/999999
                     -> 404 -> defaultStatusHandler -> throw TodoNotFoundException
             <- exception propagates through proxy
main() catches TodoNotFoundException
```

## 7. Gotchas & takeaways

> Gotcha: `@HttpExchange` interfaces have no implementation of their own to unit test — all the real behavior lives in the `RestClient`/`WebClient` adapter you wire up. Testing usually means either integration-testing against a real (or `MockWebServer`-style stub) endpoint, or mocking the interface itself in tests of the code that *calls* it, not testing the interface in isolation.

- The same `@HttpExchange` interface can be backed by either a blocking `RestClientAdapter` or a reactive `WebClientAdapter` — the interface's method signatures determine which (return `TodoItem` for blocking, `Mono<TodoItem>`/`Flux<TodoItem>` for reactive), so choose the adapter to match how the interface is declared.
- All request-level configuration (timeouts, error handling, base URL, interceptors) belongs on the underlying `RestClient`/`WebClient`, not the interface — the interface only declares shape, not behavior.
- HTTP Interface is a thin proxy over `RestClient`/`WebClient`; understanding those clients first makes this feature's behavior predictable rather than "magic."
- Great fit for typed clients to internal microservices where you control (or can codify) the API shape as an interface shared conceptually with the server's controller.

---
card: spring-framework
gi: 425
slug: web-contexts-webappconfiguration
title: "Web contexts (@WebAppConfiguration)"
---

## 1. What it is

`@WebAppConfiguration` tells the TestContext Framework to load a `WebApplicationContext` instead of a plain `ApplicationContext` for a test class — necessary for any test that needs web-specific infrastructure (a `ServletContext`, request/session-scoped beans, or `MockMvc` built from a real context via `webAppContextSetup`) rather than a plain non-web context.

```java
@SpringJUnitConfig(WebConfig.class)
@WebAppConfiguration // loads a WebApplicationContext, backed by a MockServletContext
class ProductControllerIntegrationTest {
    @Autowired WebApplicationContext webApplicationContext;
    MockMvc mockMvc;

    @BeforeEach
    void setUp() { mockMvc = MockMvcBuilders.webAppContextSetup(webApplicationContext).build(); }
}
```

## 2. Why & when

A plain `AnnotationConfigApplicationContext` has no concept of a `ServletContext`, HTTP requests, or web-scoped beans (`@RequestScope`, `@SessionScope`) — it simply can't satisfy configuration that depends on those. `@WebAppConfiguration` swaps in a `WebApplicationContext` (backed, in tests, by a `MockServletContext` rather than a real running server) so that web-layer configuration loads correctly and web-scoped beans can actually be resolved, without needing a real Servlet container running anywhere.

Reach for `@WebAppConfiguration` when:

- Building `MockMvc` from a full `WebApplicationContext` via `webAppContextSetup(...)` (the "advanced," context-backed style from the Spring MVC Test card), rather than the narrower `standaloneSetup(...)`.
- Testing configuration or beans that specifically require `ServletContext` access, or request/session-scoped beans, and need that infrastructure present even without a real server.
- Verifying web-specific Spring configuration (a `WebMvcConfigurer`, resource handler mappings, `@RequestScope` bean behavior) in isolation from a fully deployed server.

In Spring Boot projects, `@SpringBootTest(webEnvironment = ...)` typically supersedes needing `@WebAppConfiguration` directly, since Boot's test support already wires up the right kind of context based on the `webEnvironment` setting — but understanding `@WebAppConfiguration` remains relevant for Spring Framework projects without Boot's auto-configuration, and for understanding what's happening underneath Boot's abstraction.

## 3. Core concept

```
 @SpringJUnitConfig(WebConfig.class)
 @WebAppConfiguration
        |
        v
 WebTestContextBootstrapper (instead of the default bootstrapper)
        |
        v
 builds a WebApplicationContext, backed by:
   MockServletContext   <- simulates a Servlet container's ServletContext, no real server
        |
        v
 request/session-scoped beans CAN be resolved
 (using a MockHttpServletRequest bound to the current thread, when needed)
        |
        v
 MockMvcBuilders.webAppContextSetup(webApplicationContext) -- builds MockMvc from this REAL context
```

`@WebAppConfiguration` changes *what kind* of context gets built, not whether a real server starts — the `MockServletContext` is a fully in-memory simulation, consistent with the rest of `MockMvc`'s approach of using real application code against mock Servlet infrastructure.

## 4. Diagram

<svg viewBox="0 0 640 190" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="WebAppConfiguration builds a WebApplicationContext backed by MockServletContext, feeding a context-based MockMvc">
  <rect x="10" y="70" width="170" height="50" rx="8" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="95" y="92" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">@WebAppConfiguration</text>
  <text x="95" y="108" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">test class</text>

  <rect x="240" y="70" width="180" height="50" rx="8" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="330" y="92" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">WebApplicationContext</text>
  <text x="330" y="108" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">(MockServletContext-backed)</text>

  <rect x="480" y="70" width="150" height="50" rx="8" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="555" y="99" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">webAppContextSetup MockMvc</text>

  <line x1="180" y1="95" x2="235" y2="95" stroke="#8b949e" stroke-width="2" marker-end="url(#a)"/>
  <line x1="420" y1="95" x2="475" y2="95" stroke="#8b949e" stroke-width="2" marker-end="url(#a)"/>
  <defs><marker id="a" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#8b949e"/></marker></defs>
</svg>

The annotation is the trigger; everything downstream (web-scoped beans, context-backed `MockMvc`) depends on this specific kind of context existing.

## 5. Runnable example

### Level 1 — Basic

A minimal `@WebAppConfiguration` test confirming the injected context is genuinely a `WebApplicationContext` with a real (mock) `ServletContext` attached — the foundational capability this annotation provides.

```java
import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.context.annotation.*;
import org.springframework.test.context.junit.jupiter.SpringJUnitConfig;
import org.springframework.test.context.web.WebAppConfiguration;
import org.springframework.web.context.WebApplicationContext;

public class WebAppConfigBasic {

    @Configuration
    static class WebConfig {}

    @SpringJUnitConfig(WebConfig.class)
    @WebAppConfiguration
    static class ContextTypeTest {
        @Autowired WebApplicationContext webApplicationContext;

        @Test
        void injectedContextIsWebAware() {
            System.out.println("Context class: " + webApplicationContext.getClass().getSimpleName());
            System.out.println("ServletContext: " + webApplicationContext.getServletContext().getClass().getSimpleName());
            if (webApplicationContext.getServletContext() == null) {
                throw new AssertionError("Expected a non-null ServletContext");
            }
            System.out.println("injectedContextIsWebAware -- PASS");
        }
    }

    public static void main(String[] args) {
        var launcher = org.junit.platform.launcher.core.LauncherFactory.create();
        var request = org.junit.platform.launcher.core.LauncherDiscoveryRequestBuilder.request()
                .selectors(org.junit.platform.engine.discovery.DiscoverySelectors.selectClass(ContextTypeTest.class))
                .build();
        launcher.execute(request);
    }
}
```

How to run: add `spring-test`, `spring-context`, `spring-web`, `jakarta.servlet-api`, JUnit 5, and the JUnit Platform Launcher to the classpath, then `java WebAppConfigBasic.java`.

Without `@WebAppConfiguration`, `@Autowired WebApplicationContext` would fail — a plain `@SpringJUnitConfig` test builds a non-web `ApplicationContext`, which isn't even assignment-compatible with `WebApplicationContext`. With it present, the injected context genuinely has a working (mock) `ServletContext` attached, confirmed by calling `getServletContext()` directly.

### Level 2 — Intermediate

Build a context-backed `MockMvc` from the `@WebAppConfiguration`-provided context and drive a real controller through it — the direct payoff this annotation exists for, connecting back to the Spring MVC Test card's `webAppContextSetup` style.

```java
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.context.annotation.*;
import org.springframework.test.context.junit.jupiter.SpringJUnitConfig;
import org.springframework.test.context.web.WebAppConfiguration;
import org.springframework.test.web.servlet.MockMvc;
import org.springframework.test.web.servlet.setup.MockMvcBuilders;
import org.springframework.web.bind.annotation.*;
import org.springframework.web.context.WebApplicationContext;
import org.springframework.web.servlet.config.annotation.EnableWebMvc;

import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.get;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.*;

public class WebAppConfigIntermediate {

    record Product(long id, String name) {}

    @RestController
    static class ProductController {
        @GetMapping("/products/{id}")
        Product get(@PathVariable long id) { return new Product(id, "Laptop"); }
    }

    @Configuration
    @EnableWebMvc
    static class WebConfig {
        @Bean ProductController productController() { return new ProductController(); }
    }

    @SpringJUnitConfig(WebConfig.class)
    @WebAppConfiguration
    static class ProductControllerTest {
        @Autowired WebApplicationContext webApplicationContext;
        MockMvc mockMvc;

        @BeforeEach
        void setUp() {
            mockMvc = MockMvcBuilders.webAppContextSetup(webApplicationContext).build();
        }

        @Test
        void getReturnsProduct() throws Exception {
            mockMvc.perform(get("/products/42"))
                    .andExpect(status().isOk())
                    .andExpect(jsonPath("$.name").value("Laptop"));
            System.out.println("getReturnsProduct -- PASS");
        }
    }

    public static void main(String[] args) {
        var launcher = org.junit.platform.launcher.core.LauncherFactory.create();
        var request = org.junit.platform.launcher.core.LauncherDiscoveryRequestBuilder.request()
                .selectors(org.junit.platform.engine.discovery.DiscoverySelectors.selectClass(ProductControllerTest.class))
                .build();
        launcher.execute(request);
    }
}
```

How to run: same dependencies as Level 1, plus Jackson; then `java WebAppConfigIntermediate.java`.

`webAppContextSetup(webApplicationContext)` requires a genuine `WebApplicationContext` — only possible because `@WebAppConfiguration` produced one. This is meaningfully different from `standaloneSetup(new ProductController())` (the narrower style from the Spring MVC Test card): here, `@EnableWebMvc`'s full configuration, and any other beans registered in `WebConfig`, are genuinely part of what `MockMvc` drives requests through, not just the one controller instance passed in manually.

### Level 3 — Advanced

Exercise a request-scoped bean, which specifically requires the web-aware infrastructure `@WebAppConfiguration` provides — request scope needs an active request context to resolve against, something a plain `ApplicationContext` has no mechanism for at all.

```java
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.context.annotation.*;
import org.springframework.test.context.junit.jupiter.SpringJUnitConfig;
import org.springframework.test.context.web.WebAppConfiguration;
import org.springframework.test.web.servlet.MockMvc;
import org.springframework.test.web.servlet.setup.MockMvcBuilders;
import org.springframework.web.bind.annotation.*;
import org.springframework.web.context.WebApplicationContext;
import org.springframework.web.context.annotation.RequestScope;
import org.springframework.web.servlet.config.annotation.EnableWebMvc;

import java.util.UUID;

import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.get;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.*;

public class WebAppConfigAdvanced {

    static class RequestTracker {
        final String requestId = UUID.randomUUID().toString();
    }

    @RestController
    static class TrackedController {
        private final RequestTracker requestTracker; // request-scoped: a NEW instance per HTTP request
        TrackedController(RequestTracker requestTracker) { this.requestTracker = requestTracker; }

        @GetMapping("/track")
        String track() { return requestTracker.requestId; }
    }

    @Configuration
    @EnableWebMvc
    static class WebConfig {
        @Bean
        @RequestScope
        RequestTracker requestTracker() { return new RequestTracker(); }

        @Bean
        TrackedController trackedController(RequestTracker requestTracker) { return new TrackedController(requestTracker); }
    }

    @SpringJUnitConfig(WebConfig.class)
    @WebAppConfiguration
    static class RequestScopeTest {
        @Autowired WebApplicationContext webApplicationContext;
        MockMvc mockMvc;

        @BeforeEach
        void setUp() { mockMvc = MockMvcBuilders.webAppContextSetup(webApplicationContext).build(); }

        @Test
        void eachRequestGetsADifferentRequestScopedInstance() throws Exception {
            String firstId = mockMvc.perform(get("/track"))
                    .andExpect(status().isOk())
                    .andReturn().getResponse().getContentAsString();

            String secondId = mockMvc.perform(get("/track"))
                    .andExpect(status().isOk())
                    .andReturn().getResponse().getContentAsString();

            System.out.println("First request's RequestTracker id: " + firstId);
            System.out.println("Second request's RequestTracker id: " + secondId);

            if (firstId.equals(secondId)) {
                throw new AssertionError("Expected a NEW RequestTracker instance per request, but got the same id");
            }
            System.out.println("Confirmed: each HTTP request got its own RequestTracker instance -- PASS");
        }
    }

    public static void main(String[] args) {
        var launcher = org.junit.platform.launcher.core.LauncherFactory.create();
        var request = org.junit.platform.launcher.core.LauncherDiscoveryRequestBuilder.request()
                .selectors(org.junit.platform.engine.discovery.DiscoverySelectors.selectClass(RequestScopeTest.class))
                .build();
        var listener = new org.junit.platform.launcher.listeners.SummaryGeneratingListener();
        launcher.registerTestExecutionListeners(listener);
        launcher.execute(request);
        listener.getSummary().printFailuresTo(new java.io.PrintWriter(System.out));
    }
}
```

How to run: same dependencies as Level 2; then `java WebAppConfigAdvanced.java`.

`@RequestScope` on `requestTracker()` means Spring creates a brand-new `RequestTracker` instance for every distinct HTTP request, discarding it once that request completes — this scope mechanism specifically depends on an active request context being bound to the current thread while the bean is being resolved, infrastructure that only exists because `MockMvc` was built from a genuine `@WebAppConfiguration`-provided `WebApplicationContext`. The two separate `mockMvc.perform(get("/track"))` calls each establish and tear down their own request context, producing two different `requestId` values — proof the scope mechanism genuinely works, not just that the annotation is present.

## 6. Walkthrough

Trace `WebAppConfigAdvanced.RequestScopeTest.eachRequestGetsADifferentRequestScopedInstance()`'s first call:

1. **`mockMvc.perform(get("/track"))` begins.** Internally, `MockMvc` constructs a `MockHttpServletRequest` and binds it to the current thread via `RequestContextHolder` — this is the specific piece of infrastructure `@WebAppConfiguration`'s `MockServletContext`-backed setup makes available, and it's what request-scoped bean resolution depends on.
2. **`DispatcherServlet` routes to `TrackedController`.** Before the controller method runs, Spring needs to resolve `TrackedController`'s constructor dependency on `RequestTracker` — a `@RequestScope` bean.
3. **Request-scoped bean creation.** Because no `RequestTracker` exists yet for *this* request (the scope's storage is checked against the currently-bound request from step 1), Spring instantiates a new one — its constructor runs, generating a fresh `UUID` for `requestId`.
4. **Controller method runs.** `track()` returns `requestTracker.requestId` — the freshly generated UUID from step 3.
5. **Request context torn down.** After the mock request completes, the bound request context is cleared; the request-scoped `RequestTracker` instance is discarded, since request scope's storage is tied to that now-completed request.
6. **Second `perform(get("/track"))` repeats the whole cycle independently.** A new `MockHttpServletRequest` is bound, a *new* `RequestTracker` is created (a different `UUID`), the controller returns it, and the request context is torn down again.
7. **Assertion.** `firstId` and `secondId` are compared and found to differ, confirming request scope genuinely created two separate instances — one per request — rather than reusing a singleton.

```
perform(get("/track")) #1
   -> bind MockHttpServletRequest to thread
   -> resolve RequestTracker: none exists for this request -> create new (UUID A)
   -> controller returns UUID A
   -> unbind request

perform(get("/track")) #2
   -> bind a NEW MockHttpServletRequest
   -> resolve RequestTracker: none exists for THIS request -> create new (UUID B)
   -> controller returns UUID B
   -> unbind request

assert UUID A != UUID B -- PASS
```

## 7. Gotchas & takeaways

> Gotcha: `@WebAppConfiguration` alone doesn't automatically wire request/session-scoped beans correctly outside of an actual request being processed through `MockMvc` — trying to directly `context.getBean(RequestScopeBean.class)` from a test method *without* an active `MockMvc`-driven request (or manually bound `RequestContextHolder` context) typically throws an `IllegalStateException` about no thread-bound request being found. Request-scoped beans need to be resolved *during* request processing (as in Level 3's controller-mediated access), not fetched directly from the context in arbitrary test code.

- `@WebAppConfiguration` is the trigger for building a `WebApplicationContext` (backed by a `MockServletContext`) instead of a plain `ApplicationContext` — required for web-specific configuration, request/session-scoped beans, and context-backed `MockMvc`.
- `MockMvcBuilders.webAppContextSetup(...)` (needing a real `WebApplicationContext`) exercises the full web configuration a real deployment would use, in contrast to `standaloneSetup(...)`'s narrower, single-controller scope.
- Request- and session-scoped beans specifically require the web-aware infrastructure this annotation provides — a plain non-web `ApplicationContext` cannot resolve them at all.
- In Spring Boot projects, `@SpringBootTest(webEnvironment = ...)` typically supersedes direct use of `@WebAppConfiguration`, though the same underlying web-context concepts apply.

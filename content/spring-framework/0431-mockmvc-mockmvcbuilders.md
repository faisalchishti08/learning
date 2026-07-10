---
card: spring-framework
gi: 431
slug: mockmvc-mockmvcbuilders
title: "MockMvc & MockMvcBuilders"
---

## 1. What it is

`MockMvcBuilders` is the factory class offering the two ways to construct a `MockMvc` instance — `standaloneSetup(...)` (pass controller instances directly, minimal configuration) and `webAppContextSetup(...)` (build from a real `WebApplicationContext`, full configuration) — plus a shared set of builder methods (`addFilters`, `defaultRequest`, `alwaysExpect`, `apply`) common to both, letting you configure cross-cutting behavior once for every request the resulting `MockMvc` will process.

```java
MockMvc standaloneMvc = MockMvcBuilders.standaloneSetup(new ProductController())
        .setControllerAdvice(new GlobalExceptionHandler())
        .build();

MockMvc contextMvc = MockMvcBuilders.webAppContextSetup(webApplicationContext)
        .addFilters(new CharacterEncodingFilter("UTF-8", true))
        .build();
```

## 2. Why & when

The Spring MVC Test and web-contexts cards already introduced both builder styles individually; this card is about the builders' shared configuration surface and choosing deliberately between them, since the choice has real consequences for what a test actually verifies. `standaloneSetup` builds the fastest, most narrowly-scoped `MockMvc` — you explicitly list which controllers participate, and nothing else from a real application's configuration (filters, interceptors, other `@ControllerAdvice` classes) applies unless you also explicitly add it. `webAppContextSetup` builds from genuinely complete configuration, exercising everything a real deployment would — at the cost of needing that full configuration (and a `@WebAppConfiguration`-provided context) available in the first place.

Choose deliberately:

- `standaloneSetup` for fast, narrow controller-logic tests where you don't care about (or want to isolate away from) the rest of the web configuration — request mapping, argument binding, and the specific controller's own logic.
- `webAppContextSetup` when interceptors, filters, security configuration, or other globally-registered web infrastructure are part of what you're verifying, or when you want maximum confidence that a test reflects real deployed behavior.

The shared builder methods (`addFilters`, `defaultRequest`, `alwaysExpect`, `apply`) matter regardless of which style you pick — they're how you configure cross-cutting concerns once, rather than repeating them on every `mockMvc.perform(...)` call in every test method.

## 3. Core concept

```
 MockMvcBuilders.standaloneSetup(controllers...)     MockMvcBuilders.webAppContextSetup(context)
        |                                                     |
        +----------------------- both return ------------------------+
                                    |
                                    v
                    ConfigurableMockMvcBuilder (shared configuration surface)
                          .addFilters(...)         <- register Servlet Filters
                          .defaultRequest(...)      <- common request setup (headers, etc.)
                          .alwaysExpect(...)         <- assertion applied to EVERY request
                          .apply(configurer)          <- plug in reusable configuration (e.g. Spring Security)
                                    |
                                    v
                                .build() -> MockMvc
```

Both builder entry points converge on the same shared configuration API before `.build()` produces the final, immutable `MockMvc` instance.

## 4. Diagram

<svg viewBox="0 0 640 190" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Two MockMvc builder entry points converge on shared configuration before producing MockMvc">
  <rect x="10" y="20" width="200" height="44" rx="8" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="110" y="47" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">standaloneSetup(controllers)</text>

  <rect x="10" y="120" width="200" height="44" rx="8" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="110" y="147" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">webAppContextSetup(context)</text>

  <rect x="330" y="70" width="200" height="50" rx="8" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="430" y="92" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">shared builder methods</text>
  <text x="430" y="108" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">addFilters, defaultRequest, apply</text>

  <rect x="560" y="70" width="70" height="50" rx="8" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="595" y="99" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">MockMvc</text>

  <line x1="210" y1="42" x2="325" y2="80" stroke="#8b949e" stroke-width="1.5"/>
  <line x1="210" y1="142" x2="325" y2="105" stroke="#8b949e" stroke-width="1.5"/>
  <line x1="530" y1="95" x2="555" y2="95" stroke="#8b949e" stroke-width="2" marker-end="url(#a)"/>
  <defs><marker id="a" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#8b949e"/></marker></defs>
</svg>

Whichever entry point you start from, the shared configuration API is where cross-cutting `MockMvc` behavior gets set up.

## 5. Runnable example

### Level 1 — Basic

`standaloneSetup` with `addFilters(...)` — registering a real Servlet `Filter` so it applies to every request the resulting `MockMvc` processes, without a full web application context.

```java
import jakarta.servlet.*;
import org.springframework.test.web.servlet.MockMvc;
import org.springframework.test.web.servlet.setup.MockMvcBuilders;
import org.springframework.web.bind.annotation.*;

import java.io.IOException;

import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.get;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.*;

public class MockMvcBuildersBasic {

    static class RequestCountingFilter implements Filter {
        static int count = 0;
        @Override
        public void doFilter(ServletRequest request, ServletResponse response, FilterChain chain)
                throws IOException, ServletException {
            count++;
            chain.doFilter(request, response);
        }
    }

    @RestController
    static class PingController {
        @GetMapping("/ping")
        String ping() { return "pong"; }
    }

    public static void main(String[] args) throws Exception {
        MockMvc mockMvc = MockMvcBuilders.standaloneSetup(new PingController())
                .addFilters(new RequestCountingFilter()) // applies to EVERY request through this MockMvc
                .build();

        mockMvc.perform(get("/ping")).andExpect(status().isOk()).andExpect(content().string("pong"));
        mockMvc.perform(get("/ping")).andExpect(status().isOk());

        System.out.println("RequestCountingFilter saw " + RequestCountingFilter.count + " requests");
        if (RequestCountingFilter.count != 2) throw new AssertionError("Expected 2, got " + RequestCountingFilter.count);
        System.out.println("addFilters correctly applied to every request -- PASS");
    }
}
```

How to run: add `spring-test`, `spring-webmvc`, and `jakarta.servlet-api` to the classpath, then `java MockMvcBuildersBasic.java`.

`standaloneSetup` normally only involves the listed controller — no filters apply by default, since there's no real `web.xml`/filter chain being loaded. `.addFilters(new RequestCountingFilter())` explicitly registers a filter into the mock filter chain `MockMvc` builds internally, and it fires for every subsequent `perform(...)` call on this `MockMvc` instance, confirmed by the counter reaching `2` after two requests.

### Level 2 — Intermediate

`defaultRequest(...)` and `alwaysExpect(...)` — configuring common request setup and a blanket assertion applied to every request, removing the need to repeat them at every call site.

```java
import org.springframework.http.MediaType;
import org.springframework.test.web.servlet.MockMvc;
import org.springframework.test.web.servlet.setup.MockMvcBuilders;
import org.springframework.web.bind.annotation.*;

import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.get;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.*;

public class MockMvcBuildersIntermediate {

    @RestController
    static class EchoController {
        @GetMapping("/echo-header")
        String echoHeader(@org.springframework.web.bind.annotation.RequestHeader("X-Client-Id") String clientId) {
            return "client=" + clientId;
        }
    }

    public static void main(String[] args) throws Exception {
        MockMvc mockMvc = MockMvcBuilders.standaloneSetup(new EchoController())
                .defaultRequest(get("/").header("X-Client-Id", "test-suite")) // applied as a BASE for every request
                .alwaysExpect(header().string("Content-Type", org.hamcrest.Matchers.startsWith(MediaType.TEXT_PLAIN_VALUE)))
                .build();

        mockMvc.perform(get("/echo-header")) // no need to repeat the X-Client-Id header here
                .andExpect(status().isOk())
                .andExpect(content().string("client=test-suite"));
        System.out.println("defaultRequest correctly applied the shared header -- PASS");

        // alwaysExpect fires for THIS call too, in addition to whatever .andExpect(...) is chained explicitly.
        mockMvc.perform(get("/echo-header"))
                .andExpect(status().isOk());
        System.out.println("alwaysExpect correctly verified Content-Type on every request -- PASS");
    }
}
```

How to run: same dependencies as Level 1, then `java MockMvcBuildersIntermediate.java`.

`defaultRequest(get("/").header("X-Client-Id", "test-suite"))` sets a base request configuration merged into every subsequent `perform(...)` call unless a test explicitly overrides that header — removing the need to repeat `.header("X-Client-Id", "test-suite")` on every single request builder throughout the test class. `alwaysExpect(...)` registers an assertion checked on *every* response from this `MockMvc`, in addition to whatever `.andExpect(...)` calls a specific test adds — useful for suite-wide invariants (a security header always present, a consistent content type) you don't want to risk forgetting on any individual test.

### Level 3 — Advanced

`apply(configurer)` — plugging in a reusable `MockMvcConfigurer` (the extension point Spring Security's own `SecurityMockMvcConfigurers.springSecurity()` uses in real projects) to bundle a whole block of related configuration behind one call, demonstrated here with a custom configurer that standardizes JSON request/response handling and a shared authentication header across every request.

```java
import org.springframework.test.web.servlet.MockMvc;
import org.springframework.test.web.servlet.request.MockHttpServletRequestBuilder;
import org.springframework.test.web.servlet.setup.ConfigurableMockMvcBuilder;
import org.springframework.test.web.servlet.setup.MockMvcBuilders;
import org.springframework.test.web.servlet.setup.MockMvcConfigurer;
import org.springframework.web.bind.annotation.*;
import org.springframework.web.context.WebApplicationContext;

import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.get;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.*;

public class MockMvcBuildersAdvanced {

    @RestController
    static class SecuredController {
        @GetMapping("/secure/data")
        String getData(@org.springframework.web.bind.annotation.RequestHeader("Authorization") String auth) {
            return "data-for:" + auth;
        }
    }

    // A reusable configurer bundling a block of related configuration behind one .apply(...) call --
    // the same extension pattern Spring Security's springSecurity() configurer uses in real projects.
    static class FakeAuthMockMvcConfigurer implements MockMvcConfigurer {
        private final String token;
        FakeAuthMockMvcConfigurer(String token) { this.token = token; }

        @Override
        public void afterConfigurerAdded(ConfigurableMockMvcBuilder<?> builder) {
            builder.defaultRequest(get("/").header("Authorization", "Bearer " + token));
        }

        @Override
        public org.springframework.test.web.servlet.request.RequestPostProcessor beforeMockMvcCreated(
                ConfigurableMockMvcBuilder<?> builder, WebApplicationContext context) {
            return request -> request; // no per-request mutation needed for this simple example
        }
    }

    public static void main(String[] args) throws Exception {
        MockMvc mockMvc = MockMvcBuilders.standaloneSetup(new SecuredController())
                .apply(new FakeAuthMockMvcConfigurer("fake-jwt-12345")) // one call bundles the auth setup
                .build();

        mockMvc.perform(get("/secure/data")) // no need to attach the Authorization header manually here
                .andExpect(status().isOk())
                .andExpect(content().string("data-for:Bearer fake-jwt-12345"));

        System.out.println("apply(FakeAuthMockMvcConfigurer) correctly injected shared auth configuration -- PASS");
    }
}
```

How to run: same dependencies as Level 1, then `java MockMvcBuildersAdvanced.java`.

`MockMvcConfigurer` is the extension interface for packaging a *block* of related builder configuration (here, just one `defaultRequest` call, but real configurers like Spring Security's often register filters, request post-processors, and default request setup together) behind a single `.apply(...)` call — every test class needing this same authentication setup calls `.apply(new FakeAuthMockMvcConfigurer(...))` once instead of repeating the underlying `defaultRequest`/`addFilters` calls individually.

## 6. Walkthrough

Trace `MockMvcBuildersAdvanced.main`'s single request:

1. **Builder configuration.** `MockMvcBuilders.standaloneSetup(new SecuredController())` starts a builder scoped to just this one controller; `.apply(new FakeAuthMockMvcConfigurer("fake-jwt-12345"))` invokes the configurer's `afterConfigurerAdded(builder)` method immediately, which itself calls `builder.defaultRequest(get("/").header("Authorization", "Bearer fake-jwt-12345"))` — registering that header as part of every future request's baseline.
2. **`.build()` finalizes.** The resulting `MockMvc` instance now has both the standalone controller setup and the configurer-contributed default request baked in.
3. **Request built.** `mockMvc.perform(get("/secure/data"))` constructs a `MockHttpServletRequest` for this specific call — internally, `MockMvc` merges this request's own builder state with the `defaultRequest` baseline from step 1, meaning the final mock request carries `Authorization: Bearer fake-jwt-12345` even though the test's own `get("/secure/data")` call never explicitly set it.
4. **Dispatch.** The merged request reaches `SecuredController.getData(...)`, whose `@RequestHeader("Authorization")` parameter binds to that merged-in header value.
5. **Response and assertion.** The controller returns `"data-for:Bearer fake-jwt-12345"`; the test's `andExpect(content().string(...))` confirms the exact expected string, proving the configurer-injected header genuinely reached the controller.

```
.apply(FakeAuthMockMvcConfigurer)
   -> afterConfigurerAdded(builder)
        -> builder.defaultRequest(header Authorization: Bearer fake-jwt-12345)
.build() -> MockMvc (with that default baked in)

perform(get("/secure/data"))
   -> merged request = this call's builder + defaultRequest baseline
   -> Authorization header present, though never set explicitly on THIS call
   -> SecuredController.getData(auth) -> "data-for:Bearer fake-jwt-12345"
```

## 7. Gotchas & takeaways

> Gotcha: `defaultRequest(...)`'s configuration merges with, rather than being fully overridden by, a specific `perform(...)` call's own request builder — if both set the *same* header, behavior can depend on the specific merge semantics of the attribute involved (some are additive, some the per-call value wins), which is easy to get wrong without checking. When a test's request seems to have an unexpected header or attribute value, checking whether a `defaultRequest(...)` baseline is contributing something unexpected is a useful first diagnostic step.

- `standaloneSetup` and `webAppContextSetup` are two different trade-offs (speed/isolation vs. completeness/realism), not one "correct" choice — pick deliberately based on what a given test needs to verify.
- Both builder styles converge on the same shared configuration surface (`addFilters`, `defaultRequest`, `alwaysExpect`, `apply`), which is where cross-cutting `MockMvc` behavior belongs, rather than repeating setup at every individual `perform(...)` call.
- `alwaysExpect(...)` is useful for suite-wide invariants that should hold on every response — a way to enforce a convention across a whole test class without relying on every test method remembering to check it individually.
- `MockMvcConfigurer` (via `.apply(...)`) is the extension point for packaging reusable, multi-part `MockMvc` configuration — the same mechanism Spring Security's `springSecurity()` configurer uses in real projects to wire in security-aware request processing with one call.

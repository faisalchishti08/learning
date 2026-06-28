---
card: spring-boot
gi: 225
slug: auto-configured-mockmvc-mockmvctester
title: Auto-configured MockMvc / MockMvcTester
---

## 1. What it is

`@AutoConfigureMockMvc` wires Spring's `MockMvc` into your test context automatically, letting you fire HTTP requests against your controller layer without starting a real server. `MockMvcTester` (Spring Boot 3.2+) wraps `MockMvc` in a fluent, AssertJ-based API so assertions read like plain English.

## 2. Why & when

Use it when you want full Spring MVC pipeline coverage (filters, converters, exception handlers) but don't need a live port. Faster than `@SpringBootTest(webEnvironment=RANDOM_PORT)` and avoids socket overhead. Perfect for controller integration tests that need the real `DispatcherServlet` without the HTTP stack.

## 3. Core concept

`@SpringBootTest` loads the complete application context. Combining it with `@AutoConfigureMockMvc` (or the shorthand `@WebMvcTest`) registers `MockMvc` as a bean. You inject `MockMvc` or `MockMvcTester` and call `perform(get("/path"))` to simulate requests. The result carries status, headers, and body for assertion.

`MockMvcTester` is the newer, preferred style: it wraps `MockMvc` and returns an `AssertableMvcResult` that integrates with AssertJ, eliminating `andExpect(...)` chains.

## 4. Diagram

<svg viewBox="0 0 640 300" xmlns="http://www.w3.org/2000/svg" font-family="monospace" font-size="13">
  <rect width="640" height="300" fill="#1c2430" rx="10"/>
  <!-- Test class -->
  <rect x="20" y="30" width="160" height="60" rx="6" fill="#2d3748" stroke="#6db33f" stroke-width="1.5"/>
  <text x="100" y="56" text-anchor="middle" fill="#6db33f" font-size="12">@SpringBootTest</text>
  <text x="100" y="74" text-anchor="middle" fill="#e6edf3" font-size="11">+ @AutoConfigureMockMvc</text>
  <!-- MockMvc -->
  <rect x="240" y="30" width="140" height="60" rx="6" fill="#2d3748" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="310" y="56" text-anchor="middle" fill="#79c0ff">MockMvc</text>
  <text x="310" y="74" text-anchor="middle" fill="#e6edf3" font-size="11">/ MockMvcTester</text>
  <!-- DispatcherServlet -->
  <rect x="440" y="30" width="170" height="60" rx="6" fill="#2d3748" stroke="#8b949e" stroke-width="1.5"/>
  <text x="525" y="65" text-anchor="middle" fill="#e6edf3">DispatcherServlet</text>
  <!-- arrows -->
  <line x1="180" y1="60" x2="238" y2="60" stroke="#6db33f" stroke-width="1.5" marker-end="url(#arr)"/>
  <line x1="380" y1="60" x2="438" y2="60" stroke="#6db33f" stroke-width="1.5" marker-end="url(#arr)"/>
  <!-- boxes below -->
  <rect x="440" y="140" width="170" height="50" rx="6" fill="#2d3748" stroke="#8b949e" stroke-width="1"/>
  <text x="525" y="161" text-anchor="middle" fill="#e6edf3" font-size="12">Filters</text>
  <text x="525" y="178" text-anchor="middle" fill="#8b949e" font-size="11">Converters / Handlers</text>
  <line x1="525" y1="90" x2="525" y2="138" stroke="#8b949e" stroke-width="1" stroke-dasharray="4 3"/>
  <!-- Controller -->
  <rect x="440" y="230" width="170" height="50" rx="6" fill="#2d3748" stroke="#6db33f" stroke-width="1.5"/>
  <text x="525" y="261" text-anchor="middle" fill="#6db33f">@RestController</text>
  <line x1="525" y1="190" x2="525" y2="228" stroke="#8b949e" stroke-width="1" stroke-dasharray="4 3"/>
  <!-- label -->
  <text x="100" y="170" text-anchor="middle" fill="#8b949e" font-size="12">No real TCP socket</text>
  <text x="100" y="188" text-anchor="middle" fill="#8b949e" font-size="12">No HTTP overhead</text>
  <defs>
    <marker id="arr" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto">
      <path d="M0,0 L0,6 L8,3 z" fill="#6db33f"/>
    </marker>
  </defs>
</svg>

_MockMvc intercepts at the DispatcherServlet level — full MVC pipeline, no real server._

## 5. Runnable example

```java
// File: MockMvcDemoTest.java
// How to run: place inside a Spring Boot 3.x project's test source root;
// run: ./mvnw test -Dtest=MockMvcDemoTest
// (Requires spring-boot-starter-web and spring-boot-starter-test on the classpath)

import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.autoconfigure.web.servlet.WebMvcTest;
import org.springframework.test.web.servlet.MockMvc;
import org.springframework.test.web.servlet.assertj.MockMvcTester;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RestController;

import static org.assertj.core.api.Assertions.assertThat;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.get;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.content;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.status;

// Minimal controller defined inline for demo purposes
@RestController
class HelloController {
    @GetMapping("/hello")
    String hello() { return "Hello, MockMvc!"; }
}

@WebMvcTest(HelloController.class)   // loads only web layer
class MockMvcDemoTest {

    @Autowired MockMvc mockMvc;           // classic API
    @Autowired MockMvcTester mvc;         // fluent AssertJ API (Boot 3.2+)

    @Test
    void classicApi() throws Exception {
        mockMvc.perform(get("/hello"))
               .andExpect(status().isOk())
               .andExpect(content().string("Hello, MockMvc!"));
    }

    @Test
    void fluentApi() {
        // MockMvcTester: no checked exception, AssertJ chaining
        assertThat(mvc.get().uri("/hello").exchange())
            .hasStatusOk()
            .hasBodyTextEqualTo("Hello, MockMvc!");
    }
}
```

**How to run:** Add to a Spring Boot 3.x project's test root and execute `./mvnw test -Dtest=MockMvcDemoTest`. Both tests should go green.

## 6. Walkthrough

1. `@WebMvcTest(HelloController.class)` — tells Boot to spin up only the web slice: controller, filters, converters. No service or repository beans are loaded.
2. `@Autowired MockMvc mockMvc` — Spring auto-configures and injects the `MockMvc` instance.
3. `@Autowired MockMvcTester mvc` — Boot 3.2+ also registers a `MockMvcTester` bean wrapping the same `MockMvc`.
4. `classicApi()` — `perform(get("/hello"))` builds a mock request; `andExpect(status().isOk())` asserts HTTP 200; `andExpect(content().string(...))` asserts body.
5. `fluentApi()` — `mvc.get().uri("/hello").exchange()` executes the same request and returns an `AssertableMvcResult`. The `.hasStatusOk()` and `.hasBodyTextEqualTo()` calls are AssertJ-style and never throw checked exceptions.

## 7. Gotchas & takeaways

> `@WebMvcTest` does **not** load `@Service` or `@Repository` beans. If your controller depends on a service, you must `@MockBean` it or the context will fail to start.

> `MockMvcTester` requires Spring Boot **3.2+**. On older versions, stick with the classic `MockMvc` API.

- Prefer `@WebMvcTest` over `@SpringBootTest` for pure controller tests — it's faster and isolates the web layer.
- Use `@AutoConfigureMockMvc` with `@SpringBootTest` only when you need the full application context (e.g., real service beans).
- `MockMvcTester` eliminates checked-exception boilerplate and produces clearer failure messages via AssertJ.
- Both APIs share the same underlying `MockMvc` engine — choose style, not behaviour.

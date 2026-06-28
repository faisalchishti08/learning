---
card: spring-boot
gi: 231
slug: testcontext-bean-override
title: TestContext bean override
---

## 1. What it is

Spring Boot 3.4 introduced `@TestBean`, `@MockitoBean`, and `@MockitoSpyBean` — a new, unified set of annotations for overriding beans in the test `ApplicationContext`. They replace the older `@MockBean` and `@SpyBean` (which came from `spring-boot-test`), provide cleaner semantics, and no longer depend on Mockito's `@MockitoSettings` internals.

## 2. Why & when

Tests often need to replace a real service bean with a fake: prevent email sending, avoid external API calls, inject a stub clock. Previously `@MockBean` was the only out-of-the-box tool. Boot 3.4's bean-override annotations are more explicit about what they override and integrate better with factory-method bean definitions and `@Configuration` classes.

## 3. Core concept

| Annotation | From | Behaviour |
|---|---|---|
| `@MockitoBean` | `spring-boot-test` 3.4+ | Registers a Mockito mock, replacing any matching production bean |
| `@MockitoSpyBean` | `spring-boot-test` 3.4+ | Wraps the real bean in a Mockito spy |
| `@TestBean` | `spring-context` 6.2 / Boot 3.4+ | Registers a real replacement bean produced by a factory method in the test class |

All three annotations operate at the `ApplicationContext` level: the override is applied before the context is used, so `@Autowired` fields receive the mock/spy/stub. Context caching is aware of overrides — a context with a mock and one without are treated as distinct.

## 4. Diagram

<svg viewBox="0 0 640 280" xmlns="http://www.w3.org/2000/svg" font-family="monospace" font-size="13">
  <rect width="640" height="280" fill="#1c2430" rx="10"/>
  <!-- Production context -->
  <rect x="20" y="40" width="185" height="200" rx="8" fill="#2d3748" stroke="#8b949e" stroke-width="1.5"/>
  <text x="112" y="68" text-anchor="middle" fill="#8b949e">Production Context</text>
  <rect x="35" y="82" width="155" height="35" rx="4" fill="#1c2430" stroke="#8b949e" stroke-width="1"/>
  <text x="112" y="105" text-anchor="middle" fill="#e6edf3" font-size="12">EmailService (real)</text>
  <rect x="35" y="128" width="155" height="35" rx="4" fill="#1c2430" stroke="#8b949e" stroke-width="1"/>
  <text x="112" y="151" text-anchor="middle" fill="#e6edf3" font-size="12">PaymentGateway (real)</text>
  <rect x="35" y="174" width="155" height="35" rx="4" fill="#1c2430" stroke="#8b949e" stroke-width="1"/>
  <text x="112" y="197" text-anchor="middle" fill="#e6edf3" font-size="12">OrderService (real)</text>
  <!-- Test context -->
  <rect x="260" y="40" width="360" height="200" rx="8" fill="#2d3748" stroke="#6db33f" stroke-width="2"/>
  <text x="440" y="68" text-anchor="middle" fill="#6db33f">Test Context (overrides applied)</text>
  <rect x="275" y="82" width="330" height="35" rx="4" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="440" y="105" text-anchor="middle" fill="#79c0ff" font-size="12">@MockitoBean EmailService — Mockito mock</text>
  <rect x="275" y="128" width="330" height="35" rx="4" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="440" y="151" text-anchor="middle" fill="#6db33f" font-size="12">@TestBean PaymentGateway — stub via factory</text>
  <rect x="275" y="174" width="330" height="35" rx="4" fill="#1c2430" stroke="#8b949e" stroke-width="1"/>
  <text x="440" y="197" text-anchor="middle" fill="#8b949e" font-size="12">OrderService (real — not overridden)</text>
  <!-- arrow -->
  <line x1="205" y1="140" x2="258" y2="140" stroke="#6db33f" stroke-width="2" marker-end="url(#a6)" stroke-dasharray="6 3"/>
  <text x="231" y="132" text-anchor="middle" fill="#6db33f" font-size="11">override</text>
  <defs>
    <marker id="a6" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto">
      <path d="M0,0 L0,6 L8,3 z" fill="#6db33f"/>
    </marker>
  </defs>
</svg>

_Bean override annotations replace or wrap specific beans while leaving the rest of the context intact._

## 5. Runnable example

```java
// File: BeanOverrideTest.java
// How to run: place in a Spring Boot 3.4+ project's test source root;
// run: ./mvnw test -Dtest=BeanOverrideTest
// Requires spring-boot-starter-test 3.4+

import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.boot.test.context.TestConfiguration;
import org.springframework.context.annotation.Bean;
import org.springframework.stereotype.Service;
import org.springframework.test.context.bean.override.mockito.MockitoBean;
import org.springframework.test.context.bean.override.mockito.MockitoSpyBean;

import static org.assertj.core.api.Assertions.assertThat;
import static org.mockito.BDDMockito.given;
import static org.mockito.Mockito.verify;

// --- Production services (normally in src/main/java) ---
@Service
class NotificationService {
    public String send(String msg) {
        throw new UnsupportedOperationException("Real implementation hits an external API");
    }
}

@Service
class AuditService {
    private int count = 0;
    public void log(String event) { count++; }
    public int getCount() { return count; }
}

@Service
class OrderProcessor {
    private final NotificationService notifications;
    private final AuditService audit;

    OrderProcessor(NotificationService notifications, AuditService audit) {
        this.notifications = notifications;
        this.audit = audit;
    }

    public String process(String orderId) {
        audit.log("order:" + orderId);
        return notifications.send("Order " + orderId + " processed");
    }
}

// --- Test ---
@SpringBootTest(webEnvironment = SpringBootTest.WebEnvironment.NONE)
class BeanOverrideTest {

    // Replace with a Mockito mock — real bean is NOT called
    @MockitoBean
    NotificationService notifications;

    // Wrap real bean in a spy — real method IS called, but we can verify
    @MockitoSpyBean
    AuditService audit;

    @Autowired
    OrderProcessor processor;

    @Test
    void processCallsNotificationAndAudit() {
        given(notifications.send("Order O-1 processed")).willReturn("OK");

        String result = processor.process("O-1");

        assertThat(result).isEqualTo("OK");
        verify(audit).log("order:O-1");        // spy: verify real method was invoked
        verify(notifications).send("Order O-1 processed");  // mock: verify call
    }
}
```

**How to run:** `./mvnw test -Dtest=BeanOverrideTest` against a Spring Boot 3.4+ project.

## 6. Walkthrough

1. `@MockitoBean NotificationService notifications` — before the context starts, Spring replaces the `NotificationService` bean with a Mockito mock. Calling its methods does nothing by default.
2. `@MockitoSpyBean AuditService audit` — wraps the real `AuditService` bean in a spy. Real methods execute, but Mockito records calls for verification.
3. `@Autowired OrderProcessor processor` — receives the full `OrderProcessor` with mocked `NotificationService` and spy `AuditService`.
4. `given(notifications.send(...)).willReturn("OK")` — stubs the mock to return `"OK"` instead of throwing.
5. `processor.process("O-1")` — calls the real `OrderProcessor` logic; it calls the spy and the mock.
6. `verify(audit).log(...)` — asserts the spy recorded the call to the real method.
7. `verify(notifications).send(...)` — asserts the mock was invoked with the right argument.

## 7. Gotchas & takeaways

> `@MockitoBean` is the Boot 3.4+ replacement for `@MockBean`. If you're on Boot < 3.4, use `@MockBean` from `org.springframework.boot.test.mock.mockito` — they work identically in earlier versions.

> Each unique set of bean overrides creates a **separate** cached application context. Overusing `@MockitoBean` on many different fields across many test classes can balloon the number of contexts and slow your test suite significantly.

> `@MockitoSpyBean` wraps the **real** bean — the real bean must still exist in the context. If the bean is `@Lazy` or conditionally absent, the spy will fail to register.

- Prefer `@MockitoBean` over `@MockitoSpyBean` when you don't need real logic — mocks are faster and more predictable.
- Group tests that share the same overrides into a shared base class or `@ContextConfiguration` to maximize context cache hits.
- Use `@TestBean` (Spring Framework 6.2+) when you want a real Java stub (not a mock framework) as the replacement — provides stronger compile-time guarantees.
- Reset mock state between tests with `@DirtiesContext` only as a last resort; prefer stateless mocks instead.

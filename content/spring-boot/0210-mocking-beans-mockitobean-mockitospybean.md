---
card: spring-boot
gi: 210
slug: mocking-beans-mockitobean-mockitospybean
title: "Mocking beans (@MockitoBean / @MockitoSpyBean)"
---

## 1. What it is

`@MockitoBean` and `@MockitoSpyBean` are Spring Boot test annotations that integrate Mockito with the Spring application context. `@MockitoBean` replaces a bean in the context with a Mockito mock — calls return `null` / default values unless stubbed. `@MockitoSpyBean` wraps an existing bean with a Mockito spy — real methods are called by default, but individual methods can be stubbed or verified. Both annotations reset the mock/spy after each test method.

## 2. Why & when

Use `@MockitoBean` when:
- You want to test a service layer without a real database or external service.
- A dependency has side effects (email, payment, audit) that must not fire in tests.
- You want to control exactly what a dependency returns for a specific test scenario.

Use `@MockitoSpyBean` when:
- You want real behavior from a dependency but need to stub or verify just one method.
- You're adding observability (counting calls) to an existing bean without replacing it.

Note: in Spring Boot 3.4+, `@MockitoBean` replaces the older `@MockBean`, and `@MockitoSpyBean` replaces `@SpyBean`. The old annotations still work but are deprecated.

## 3. Core concept

```java
@SpringBootTest
class OrderServiceTest {

    @MockitoBean
    OrderRepository orderRepository;   // real context bean replaced with Mockito mock

    @MockitoSpyBean
    AuditService auditService;         // real bean wrapped with spy (real calls + verify)

    @Autowired
    OrderService orderService;         // gets the mock OrderRepository injected

    @Test
    void createOrder_savesAndAudits() {
        // Arrange: stub the mock
        when(orderRepository.save(any())).thenReturn(new Order("ORD-1", "alice"));

        // Act
        Order result = orderService.createOrder(new OrderRequest("alice", 99.99));

        // Assert with JUnit/AssertJ
        assertThat(result.id()).isEqualTo("ORD-1");
        // Verify on mock
        verify(orderRepository).save(any(Order.class));
        // Verify on spy (real method was called)
        verify(auditService).record("ORDER_CREATED", "ORD-1");
    }
}
```

The mock is injected into every bean that depends on `OrderRepository` in the context.

## 4. Diagram

<svg viewBox="0 0 680 200" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="@MockitoBean replaces a real bean with a Mockito mock in the context; @MockitoSpyBean wraps an existing bean with a spy; both allow stubbing and verification; mock is reset after each test">
  <!-- Real beans (left) -->
  <rect x="10" y="30" width="140" height="42" rx="6" fill="#1c2430" stroke="#8b949e" stroke-width="1.5"/>
  <text x="80" y="49" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">OrderRepository</text>
  <text x="80" y="63" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">(real — has DB)</text>

  <rect x="10" y="85" width="140" height="42" rx="6" fill="#1c2430" stroke="#8b949e" stroke-width="1.5"/>
  <text x="80" y="104" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">AuditService</text>
  <text x="80" y="118" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">(real bean)</text>

  <!-- Replacement arrows -->
  <line x1="152" y1="50" x2="235" y2="50" stroke="#6db33f" stroke-width="1.5" marker-end="url(#mba)"/>
  <text x="195" y="43" fill="#6db33f" font-size="7" text-anchor="middle" font-family="sans-serif">@MockitoBean</text>
  <text x="195" y="53" fill="#8b949e" font-size="7" text-anchor="middle" font-family="sans-serif">replaces</text>

  <line x1="152" y1="106" x2="235" y2="106" stroke="#79c0ff" stroke-width="1.5" marker-end="url(#mbb)"/>
  <text x="195" y="99" fill="#79c0ff" font-size="7" text-anchor="middle" font-family="sans-serif">@MockitoSpyBean</text>
  <text x="195" y="109" fill="#8b949e" font-size="7" text-anchor="middle" font-family="sans-serif">wraps</text>

  <!-- Mockito mock -->
  <rect x="240" y="30" width="150" height="42" rx="6" fill="#0d1117" stroke="#6db33f" stroke-width="2"/>
  <text x="315" y="49" fill="#6db33f" font-size="9" text-anchor="middle" font-family="sans-serif" font-weight="bold">Mockito Mock</text>
  <text x="315" y="63" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">when(repo.save(any())).thenReturn(..)</text>

  <!-- Mockito spy -->
  <rect x="240" y="85" width="150" height="42" rx="6" fill="#0d1117" stroke="#79c0ff" stroke-width="2"/>
  <text x="315" y="104" fill="#79c0ff" font-size="9" text-anchor="middle" font-family="sans-serif" font-weight="bold">Mockito Spy</text>
  <text x="315" y="118" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">calls real method + verify(spy).record(..)</text>

  <!-- OrderService -->
  <rect x="405" y="55" width="155" height="50" rx="8" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="482" y="75" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif" font-weight="bold">OrderService</text>
  <text x="482" y="90" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">gets mock/spy injected</text>
  <text x="482" y="102" fill="#8b949e" font-size="7" text-anchor="middle" font-family="sans-serif">real service, fake deps</text>

  <line x1="392" y1="51" x2="403" y2="72" stroke="#6db33f" stroke-width="1.5" marker-end="url(#mba)"/>
  <line x1="392" y1="106" x2="403" y2="92" stroke="#79c0ff" stroke-width="1.5" marker-end="url(#mbb)"/>

  <!-- Reset banner -->
  <rect x="240" y="145" width="315" height="22" rx="6" fill="#1c2430" stroke="#8b949e" stroke-width="1"/>
  <text x="397" y="160" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">Mock &amp; spy reset (Mockito.reset) after each @Test method</text>

  <!-- Test -->
  <rect x="565" y="55" width="105" height="50" rx="6" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="617" y="73" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif" font-weight="bold">@Test</text>
  <text x="617" y="88" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">verify(repo)</text>
  <text x="617" y="100" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">verify(spy)</text>

  <line x1="562" y1="80" x2="573" y2="80" stroke="#6db33f" stroke-width="1.5" marker-end="url(#mba)"/>

  <defs>
    <marker id="mba" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L6,3 L0,6 Z" fill="#6db33f"/></marker>
    <marker id="mbb" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L6,3 L0,6 Z" fill="#79c0ff"/></marker>
  </defs>
</svg>

`@MockitoBean` injects a pure mock (no real calls); `@MockitoSpyBean` wraps a real bean (all calls are real unless stubbed); both are reset after each test.

## 5. Runnable example

```java
// MockitoBeanDemo.java — demonstrates @MockitoBean and @MockitoSpyBean patterns
// How to run: java MockitoBeanDemo.java  (JDK 17+, no dependencies)
// Real Spring Boot: annotate test fields with @MockitoBean / @MockitoSpyBean in @SpringBootTest

import java.util.*;

public class MockitoBeanDemo {

    // Production layer
    interface OrderRepository {
        String save(String customer, double total);
        boolean existsById(String id);
    }

    interface AuditService {
        void record(String event, String resourceId);
        List<String> getRecords();
    }

    // Real implementations (would not be used in tests with @MockitoBean)
    static class RealOrderRepository implements OrderRepository {
        @Override public String save(String customer, double total) {
            throw new RuntimeException("Would hit database — not wanted in test");
        }
        @Override public boolean existsById(String id) { return false; }
    }

    static class RealAuditService implements AuditService {
        private final List<String> log = new ArrayList<>();
        @Override public void record(String event, String resourceId) {
            log.add(event + ":" + resourceId);
            System.out.println("  [RealAudit] " + event + " " + resourceId);
        }
        @Override public List<String> getRecords() { return log; }
    }

    // The service under test
    static class OrderService {
        private final OrderRepository repo;
        private final AuditService    audit;
        OrderService(OrderRepository repo, AuditService audit) {
            this.repo = repo; this.audit = audit;
        }
        String createOrder(String customer, double total) {
            String id = repo.save(customer, total);
            audit.record("ORDER_CREATED", id);
            return id;
        }
        boolean cancelOrder(String id) {
            if (!repo.existsById(id)) return false;
            audit.record("ORDER_CANCELLED", id);
            return true;
        }
    }

    // === Simulate @MockitoBean ===
    static class MockOrderRepository implements OrderRepository {
        private final Map<String, String> stubs = new LinkedHashMap<>();
        private final List<String> calls = new ArrayList<>();
        // Simulates when(repo.save(...)).thenReturn("ORD-1")
        void stubSave(String customer, String returnValue) { stubs.put(customer, returnValue); }
        @Override public String save(String customer, double total) {
            calls.add("save(" + customer + "," + total + ")");
            return stubs.getOrDefault(customer, null);
        }
        @Override public boolean existsById(String id) {
            calls.add("existsById(" + id + ")");
            return stubs.containsValue(id);
        }
        void verifyCall(String expected) {
            if (!calls.contains(expected))
                throw new AssertionError("Expected call: " + expected + " but got: " + calls);
            System.out.println("  ✓ verify: " + expected + " was called");
        }
        void reset() { stubs.clear(); calls.clear(); }
    }

    // === Simulate @MockitoSpyBean (wraps real bean) ===
    static class SpyAuditService extends RealAuditService {
        private final List<String> verifyCalls = new ArrayList<>();
        @Override public void record(String event, String resourceId) {
            verifyCalls.add(event + ":" + resourceId);
            super.record(event, resourceId); // calls real method
        }
        void verifyRecord(String event, String resourceId) {
            String expected = event + ":" + resourceId;
            if (!verifyCalls.contains(expected))
                throw new AssertionError("Expected spy call: " + expected);
            System.out.println("  ✓ verify spy: record(" + event + ", " + resourceId + ")");
        }
        void reset() { verifyCalls.clear(); getRecords().clear(); }
    }

    static void expect(boolean condition, String message) {
        if (!condition) throw new AssertionError("FAIL: " + message);
        System.out.println("  ✓ " + message);
    }

    public static void main(String[] args) {
        System.out.println("=== @MockitoBean / @MockitoSpyBean Demo ===\n");

        MockOrderRepository mockRepo = new MockOrderRepository();
        SpyAuditService     spyAudit = new SpyAuditService();
        OrderService        service  = new OrderService(mockRepo, spyAudit);

        // --- Test 1: createOrder ---
        System.out.println("--- Test 1: createOrder ---");
        mockRepo.stubSave("alice", "ORD-1");            // when(repo.save("alice",any)).thenReturn("ORD-1")

        String result = service.createOrder("alice", 99.99);

        expect("ORD-1".equals(result),                  "returns stubbed order id");
        mockRepo.verifyCall("save(alice,99.99)");        // verify(repo).save(...)
        spyAudit.verifyRecord("ORDER_CREATED", "ORD-1");// verify(spy).record(...)
        // Real audit service recorded it:
        expect(spyAudit.getRecords().contains("ORDER_CREATED:ORD-1"),
               "spy called real record()");

        // Simulate reset after @Test method
        mockRepo.reset(); spyAudit.reset();

        // --- Test 2: cancelOrder (different scenario) ---
        System.out.println("\n--- Test 2: cancelOrder existing order ---");
        mockRepo.stubSave("bob", "ORD-2");
        service.createOrder("bob", 49.99);
        mockRepo.reset(); spyAudit.reset(); // reset between logical "tests"

        // existsById returns true because "ORD-2" is in stubs
        mockRepo.stubSave("bob", "ORD-2"); // re-seed so existsById works
        boolean cancelled = service.cancelOrder("ORD-2");
        expect(cancelled, "cancelOrder returns true for existing order");
        spyAudit.verifyRecord("ORDER_CANCELLED", "ORD-2");

        System.out.println("\n--- @MockitoBean vs @MockitoSpyBean ---");
        System.out.println("@MockitoBean    → pure mock (no real calls, returns null by default)");
        System.out.println("@MockitoSpyBean → spy wraps real bean (real calls unless doReturn/when used)");
        System.out.println("Both reset after each @Test method automatically");
        System.out.println("\nIn Spring Boot 3.4+: @MockitoBean replaces @MockBean");
        System.out.println("                     @MockitoSpyBean replaces @SpyBean");
    }
}
```

**How to run:** `java MockitoBeanDemo.java`

## 6. Walkthrough

- **`MockOrderRepository`** (simulates `@MockitoBean`): no real logic — `save()` returns only pre-stubbed values. The real `RealOrderRepository` would throw (simulating a missing DB). The mock is safe in tests.
- **`SpyAuditService`** (simulates `@MockitoSpyBean`): extends `RealAuditService` and delegates to `super.record()` — the real implementation runs and records to `log`. The spy records calls for verification without replacing behavior.
- **Reset between tests**: `mockRepo.reset()` and `spyAudit.reset()` simulate what Spring Boot does automatically after each `@Test` method. Without reset, stubs from test 1 would bleed into test 2.
- **Test 2 pattern**: demonstrates a different scenario (cancel) reusing the same context. Each test configures its own stubs — no shared state carries over.

## 7. Gotchas & takeaways

> `@MockitoBean` **replaces** the bean in the context — all beans that depend on `OrderRepository` get the mock injected. This triggers a **context reload** if the replacement changes the context signature. Avoid changing `@MockitoBean` configuration between test classes; put them in a shared base test class to maximize context caching.

> `@MockitoSpyBean` wraps the **existing Spring bean** — the real bean must exist in the context. If no `OrderRepository` bean is found, the annotation fails. Use `@MockitoBean` when you want to prevent the real bean from loading at all.

- Auto-reset: Spring Boot calls `Mockito.reset(mock)` after each test method automatically — no manual `@AfterEach` needed.
- Unstubbed methods on `@MockitoBean` return `null` for objects, `0` for numbers, `false` for booleans. Add `@MockitoSettings(defaultAnswer = RETURNS_SMART_NULLS)` to get better NPE messages.
- `@MockitoBean` on an interface does NOT require an implementation on the classpath. `@MockitoSpyBean` requires a real bean.
- For simple "does this method get called with these args?" verification, `@MockitoBean` + `verify(mock).method(args)` is cleaner than `@MockitoSpyBean`.

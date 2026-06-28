---
card: spring-boot
gi: 221
slug: graphqltest
title: "@GraphQlTest"
---

## 1. What it is

`@GraphQlTest` is a Spring Boot test slice for Spring for GraphQL. It loads `@Controller` beans that handle GraphQL queries/mutations/subscriptions, the GraphQL schema, and auto-configures a `GraphQlTester` for making test requests. It does NOT load JPA, web filters, or service beans. It is the right slice for testing GraphQL resolvers in isolation.

## 2. Why & when

Use `@GraphQlTest` to test:
- Query and mutation mappings (`@QueryMapping`, `@MutationMapping`).
- Argument binding and validation (`@Argument`).
- Response field selection and JSON structure.
- GraphQL error handling (type errors, custom error types).
- Subscription emissions (streaming results).

Use `@MockitoBean` for services the resolver depends on. The slice ensures your GraphQL schema is valid and that field resolvers return the correct response shape — without starting a full HTTP server.

## 3. Core concept

```java
@GraphQlTest(OrderController.class)
class OrderQueryTest {

    @Autowired GraphQlTester graphQlTester;
    @MockitoBean OrderService orderService;

    @Test
    void queryOrder_returnsFields() {
        when(orderService.findById("1")).thenReturn(new Order("1", "alice", 99.99));

        graphQlTester.document("""
            query {
                order(id: "1") {
                    id
                    customer
                    total
                }
            }
        """)
        .execute()
        .path("order.id").entity(String.class).isEqualTo("1")
        .path("order.customer").entity(String.class).isEqualTo("alice")
        .path("order.total").entity(Double.class).isEqualTo(99.99);
    }

    @Test
    void createOrder_mutationReturnsId() {
        when(orderService.create(any())).thenReturn(new Order("ORD-1", "bob", 49.99));

        graphQlTester.document("""
            mutation {
                createOrder(customer: "bob", total: 49.99) { id }
            }
        """)
        .execute()
        .path("createOrder.id").entity(String.class).isEqualTo("ORD-1");
    }
}
```

Schema is loaded from `src/main/resources/graphql/*.graphqls` automatically.

## 4. Diagram

<svg viewBox="0 0 680 185" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="@GraphQlTest loads GraphQL controllers and schema; GraphQlTester sends query documents; schema validates and routes to @QueryMapping; mock service returns data; response path assertions verify result">
  <!-- GraphQlTester -->
  <rect x="10" y="60" width="140" height="70" rx="8" fill="#0d1117" stroke="#79c0ff" stroke-width="2"/>
  <text x="75" y="82" fill="#79c0ff" font-size="10" text-anchor="middle" font-family="sans-serif" font-weight="bold">GraphQlTester</text>
  <text x="75" y="98" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">.document(query)</text>
  <text x="75" y="112" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">.execute()</text>
  <text x="75" y="124" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">.path("order.id")</text>

  <!-- Arrow -->
  <line x1="152" y1="95" x2="200" y2="95" stroke="#79c0ff" stroke-width="1.5" marker-end="url(#gqa)"/>

  <!-- GraphQL slice -->
  <rect x="205" y="25" width="265" height="140" rx="10" fill="#1c2430" stroke="#79c0ff" stroke-width="2"/>
  <text x="337" y="47" fill="#e6edf3" font-size="11" text-anchor="middle" font-family="sans-serif" font-weight="bold">@GraphQlTest Slice</text>
  <rect x="218" y="58" width="240" height="26" rx="5" fill="#0d1117" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="338" y="75" fill="#79c0ff" font-size="9" text-anchor="middle" font-family="sans-serif">GraphQL Schema (*.graphqls files)</text>
  <rect x="218" y="91" width="240" height="26" rx="5" fill="#0d1117" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="338" y="108" fill="#79c0ff" font-size="9" text-anchor="middle" font-family="sans-serif">@QueryMapping / @MutationMapping</text>
  <rect x="218" y="124" width="240" height="26" rx="5" fill="#0d1117" stroke="#8b949e" stroke-width="1"/>
  <text x="338" y="141" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">RuntimeWiringConfigurer, scalar types</text>

  <!-- Mock service -->
  <line x1="472" y1="95" x2="530" y2="95" stroke="#79c0ff" stroke-width="1.5" marker-end="url(#gqb)"/>
  <rect x="535" y="65" width="135" height="60" rx="8" fill="#1c2430" stroke="#8b949e" stroke-width="1.5"/>
  <text x="602" y="87" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif" font-weight="bold">@MockitoBean</text>
  <text x="602" y="102" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">OrderService</text>
  <text x="602" y="116" fill="#8b949e" font-size="7" text-anchor="middle" font-family="sans-serif">stubbed returns</text>

  <text x="337" y="178" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">✗ JPA, HTTP filters, security, web layer excluded</text>

  <defs>
    <marker id="gqa" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L6,3 L0,6 Z" fill="#79c0ff"/></marker>
    <marker id="gqb" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L6,3 L0,6 Z" fill="#8b949e"/></marker>
  </defs>
</svg>

`GraphQlTester` sends GraphQL documents; the schema validates and routes to `@QueryMapping` controllers; mock services provide data; path assertions verify the response.

## 5. Runnable example

```java
// GraphQlTestDemo.java — simulates @GraphQlTest GraphQlTester patterns
// How to run: java GraphQlTestDemo.java  (JDK 17+, no dependencies)
// Real use: @GraphQlTest(OrderController.class) + @Autowired GraphQlTester

import java.util.*;
import java.util.regex.*;

public class GraphQlTestDemo {

    record Order(String id, String customer, double total, List<String> items) {}
    record OrderError(String message, String type) {}

    // Simulates OrderService (would be @MockitoBean in real test)
    static class MockOrderService {
        private final Map<String, Order> orders = new LinkedHashMap<>();
        void stub(Order o) { orders.put(o.id(), o); }
        Order findById(String id) { return orders.get(id); }
        List<Order> findAll() { return List.copyOf(orders.values()); }
        Order create(String customer, double total) {
            String id = "ORD-" + (orders.size() + 1);
            Order o = new Order(id, customer, total, List.of());
            orders.put(id, o);
            return o;
        }
    }

    // Simulates GraphQL execution engine (schema + resolver)
    static class GraphQlEngine {
        private final MockOrderService svc;

        GraphQlEngine(MockOrderService svc) { this.svc = svc; }

        Map<String, Object> execute(String document) {
            System.out.println("  [GraphQL] " + document.trim().replaceAll("\\s+", " "));
            document = document.trim();

            if (document.startsWith("query") && document.contains("order(id:")) {
                String id = extractArg(document, "id");
                Order o = svc.findById(id);
                if (o == null) return Map.of("errors", List.of(Map.of("message", "Order not found: " + id)));
                return Map.of("data", Map.of("order", orderMap(o)));
            }
            if (document.startsWith("query") && document.contains("orders {")) {
                List<Map<String, Object>> list = svc.findAll().stream().map(this::orderMap).toList();
                return Map.of("data", Map.of("orders", list));
            }
            if (document.startsWith("mutation") && document.contains("createOrder")) {
                String customer = extractArg(document, "customer");
                double total    = Double.parseDouble(extractArg(document, "total"));
                Order o = svc.create(customer, total);
                return Map.of("data", Map.of("createOrder", orderMap(o)));
            }
            return Map.of("errors", List.of(Map.of("message", "Unknown operation")));
        }

        private Map<String, Object> orderMap(Order o) {
            return new LinkedHashMap<>(Map.of("id", o.id(), "customer", o.customer(), "total", o.total()));
        }

        private String extractArg(String doc, String key) {
            Matcher m = Pattern.compile(key + ":\\s*\"?([^,)\"\\s]+)\"?").matcher(doc);
            return m.find() ? m.group(1) : null;
        }
    }

    // Simulates GraphQlTester assertions
    static class GraphQlTesterResult {
        private final Map<String, Object> result;
        GraphQlTesterResult(Map<String, Object> result) { this.result = result; }

        GraphQlTesterResult hasNoErrors() {
            if (result.containsKey("errors"))
                throw new AssertionError("Expected no errors but got: " + result.get("errors"));
            System.out.println("  ✓ hasNoErrors()");
            return this;
        }

        @SuppressWarnings("unchecked")
        GraphQlTesterResult pathEquals(String path, Object expected, String label) {
            // Walk dot-separated path into the result
            String[] parts = path.split("\\.");
            Object current = ((Map<?,?>) result.get("data"));
            for (String part : parts) {
                if (current instanceof Map) current = ((Map<?,?>) current).get(part);
                else { throw new AssertionError("Path not found: " + path); }
            }
            if (!expected.equals(current) && !expected.toString().equals(String.valueOf(current)))
                throw new AssertionError(label + ": path " + path + " = " + current + " expected " + expected);
            System.out.println("  ✓ " + label + " [" + path + " = " + current + "]");
            return this;
        }

        @SuppressWarnings("unchecked")
        int listSize(String path) {
            String[] parts = path.split("\\.");
            Object current = ((Map<?,?>) result.get("data"));
            for (String part : parts) current = ((Map<?,?>) current).get(part);
            return ((List<?>) current).size();
        }

        boolean hasErrors() { return result.containsKey("errors"); }
    }

    static GraphQlTesterResult execute(GraphQlEngine engine, String query) {
        return new GraphQlTesterResult(engine.execute(query));
    }

    public static void main(String[] args) {
        System.out.println("=== @GraphQlTest / GraphQlTester Demo ===\n");

        MockOrderService svc = new MockOrderService();
        svc.stub(new Order("1", "alice", 99.99, List.of("Widget A")));
        svc.stub(new Order("2", "bob",   149.50, List.of("Gadget B")));

        GraphQlEngine engine = new GraphQlEngine(svc);

        // Test 1: query by ID
        System.out.println("--- Test 1: query order(id: \"1\") ---");
        execute(engine, "query { order(id: \"1\") { id customer total } }")
            .hasNoErrors()
            .pathEquals("order.id",       "1",     "order.id")
            .pathEquals("order.customer", "alice",  "order.customer")
            .pathEquals("order.total",    99.99,    "order.total");

        // Test 2: query not found → error
        System.out.println("\n--- Test 2: order not found → GraphQL error ---");
        GraphQlTesterResult notFound = execute(engine, "query { order(id: \"999\") { id } }");
        if (!notFound.hasErrors()) throw new AssertionError("Expected GraphQL error");
        System.out.println("  ✓ GraphQL error returned for unknown id");

        // Test 3: list all orders
        System.out.println("\n--- Test 3: query orders { ... } ---");
        GraphQlTesterResult all = execute(engine, "query { orders { id customer } }");
        all.hasNoErrors();
        int size = all.listSize("orders");
        if (size != 2) throw new AssertionError("Expected 2 orders, got " + size);
        System.out.println("  ✓ orders list has 2 items");

        // Test 4: mutation createOrder
        System.out.println("\n--- Test 4: mutation createOrder ---");
        execute(engine, "mutation { createOrder(customer: \"carol\", total: 75.00) { id } }")
            .hasNoErrors()
            .pathEquals("createOrder.id", "ORD-3", "new order id");

        System.out.println("\n--- Real @GraphQlTest ---");
        System.out.println("""
@GraphQlTest(OrderController.class)
class OrderQueryTest {
    @Autowired GraphQlTester graphQlTester;
    @MockitoBean OrderService orderService;

    @Test void queryOrder() {
        when(orderService.findById("1")).thenReturn(new Order("1","alice",99.99));
        graphQlTester.document(\"""
            query { order(id: "1") { id customer total } }
        \""")
        .execute()
        .path("order.id").entity(String.class).isEqualTo("1")
        .path("order.customer").entity(String.class).isEqualTo("alice");
    }

    @Test void createOrder() {
        when(orderService.create(any())).thenReturn(new Order("ORD-1","bob",49.99));
        graphQlTester.document("mutation { createOrder(customer:\\"bob\\", total:49.99) { id } }")
        .execute()
        .path("createOrder.id").entity(String.class).isEqualTo("ORD-1");
    }
}""");

        System.out.println("\nAll tests passed.");
    }
}
```

**How to run:** `java GraphQlTestDemo.java`

## 6. Walkthrough

- **Test 1 (query by ID)**: sends a GraphQL query document. The engine validates it against the schema (in real Spring for GraphQL), routes to `@QueryMapping Order order(String id)`, calls the service, and serializes the result. `pathEquals("order.id", "1")` asserts the JSON path in the response.
- **Test 2 (not found → error)**: the service returns `null` → the resolver converts to a GraphQL error. `hasErrors()` confirms the errors array is present — GraphQL returns `200 OK` even for errors; the error is in the response body.
- **Test 3 (list query)**: returns a `Flux`/`List` of orders. `listSize("orders")` verifies the collection count.
- **Test 4 (mutation)**: `createOrder` writes a new order and returns it. The response path `createOrder.id` contains the new ID.

## 7. Gotchas & takeaways

> GraphQL always returns **HTTP 200** regardless of errors. Test for GraphQL errors using `.errors()` assertions, not HTTP status codes. `graphQlTester.document(query).execute().errors().verify()` asserts that there are no errors; `.errors().expect(e -> ...)` asserts on specific errors.

> `@GraphQlTest` validates your schema file at test startup. A typo in `schema.graphqls` (wrong type, missing field) fails the test on context load — useful for catching schema regressions early.

- GraphQL subscriptions: test with `graphQlTester.document(subscription).executeSubscription().toFlux(...)` and use `StepVerifier` for reactive assertions.
- `@GraphQlTest` does NOT include Spring Security. For auth-guarded queries, combine with `@WithMockUser` after adding security integration.
- `HttpGraphQlTester` vs `GraphQlTester`: `HttpGraphQlTester` makes real HTTP calls (`@SpringBootTest` with web env); plain `GraphQlTester` dispatches directly — much faster for slice tests.

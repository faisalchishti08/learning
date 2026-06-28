---
card: spring-boot
gi: 222
slug: restdocs-auto-config-autoconfigurerestdocs
title: "@RestDocs auto-config (@AutoConfigureRestDocs)"
---

## 1. What it is

`@AutoConfigureRestDocs` is a Spring Boot annotation that auto-configures **Spring REST Docs** in a test. When added to a `@WebMvcTest` or `@SpringBootTest` class, it configures `MockMvc` (or `WebTestClient`) to generate AsciiDoc snippets on every request. REST Docs generates documentation from your actual tests — if the test passes, the documentation is accurate, because it is derived from real requests and responses.

## 2. Why & when

Spring REST Docs is the alternative to Swagger/OpenAPI for teams that want documentation **verified by tests**. Use it when:
- Documentation must be accurate — any undocumented or incorrectly described field causes a test failure.
- You write API tests anyway — REST Docs adds snippet generation at zero extra cost.
- Your docs need custom formatting (AsciiDoc/Markdown, not auto-generated Swagger UI).
- You want to enforce documentation completeness: `requestFields(...)` fails if your request has fields you didn't document.

`@AutoConfigureRestDocs` handles setup: it creates the output directory for snippets, wraps `MockMvc` with a `MockMvcRestDocumentationConfigurer`, and applies URI customization (host, port, scheme for generated curl samples).

## 3. Core concept

```java
@WebMvcTest(OrderController.class)
@AutoConfigureRestDocs          // ← enables REST Docs; snippets go to target/generated-snippets
class OrderApiDocsTest {

    @Autowired MockMvc mockMvc;
    @MockitoBean OrderService orderService;

    @Test
    void getOrder_documentedWithRestDocs() throws Exception {
        when(orderService.findById("1")).thenReturn(new Order("1", "alice", 99.99));

        mockMvc.perform(get("/orders/1").accept(MediaType.APPLICATION_JSON))
               .andExpect(status().isOk())
               .andDo(document("get-order",          // ← snippet name
                   pathParameters(
                       parameterWithName("id").description("Order ID")),
                   responseFields(
                       fieldWithPath("id").description("Unique order identifier"),
                       fieldWithPath("customer").description("Customer name"),
                       fieldWithPath("total").description("Order total in USD"))));
    }
}
```

Snippet files written to `target/generated-snippets/get-order/`:
- `curl-request.adoc`, `http-request.adoc`, `http-response.adoc`
- `path-parameters.adoc`, `response-fields.adoc`

These snippets are `include::`d into an AsciiDoc master document and processed by the Asciidoctor Maven/Gradle plugin to produce the final HTML or PDF documentation.

## 4. Diagram

<svg viewBox="0 0 680 200" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="@AutoConfigureRestDocs wraps MockMvc; test calls mockMvc.perform with .andDo(document(...)); REST Docs interceptor captures request and response and writes AsciiDoc snippets; Asciidoctor builds HTML docs from snippets">
  <!-- Test -->
  <rect x="10" y="55" width="145" height="100" rx="8" fill="#0d1117" stroke="#6db33f" stroke-width="2"/>
  <text x="82" y="77" fill="#6db33f" font-size="10" text-anchor="middle" font-family="sans-serif" font-weight="bold">@WebMvcTest</text>
  <text x="82" y="92" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">@AutoConfigureRestDocs</text>
  <text x="82" y="107" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">mockMvc.perform(get(...))</text>
  <text x="82" y="121" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">  .andExpect(status().isOk())</text>
  <text x="82" y="135" fill="#6db33f" font-size="8" text-anchor="middle" font-family="sans-serif">  .andDo(document(...))</text>
  <text x="82" y="149" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">RestDocsMockMvcSupport</text>

  <!-- MockMvc + interceptor -->
  <rect x="205" y="35" width="220" height="130" rx="10" fill="#1c2430" stroke="#6db33f" stroke-width="2"/>
  <text x="315" y="57" fill="#e6edf3" font-size="11" text-anchor="middle" font-family="sans-serif" font-weight="bold">@AutoConfigureRestDocs</text>
  <rect x="218" y="68" width="195" height="28" rx="5" fill="#0d1117" stroke="#6db33f" stroke-width="1.5"/>
  <text x="315" y="83" fill="#6db33f" font-size="8.5" text-anchor="middle" font-family="sans-serif">MockMvc (REST Docs interceptor)</text>
  <text x="315" y="96" fill="#8b949e" font-size="7" text-anchor="middle" font-family="sans-serif">captures req/resp per test</text>
  <rect x="218" y="103" width="195" height="28" rx="5" fill="#0d1117" stroke="#8b949e" stroke-width="1"/>
  <text x="315" y="119" fill="#8b949e" font-size="8.5" text-anchor="middle" font-family="sans-serif">URI customization</text>
  <text x="315" y="132" fill="#8b949e" font-size="7" text-anchor="middle" font-family="sans-serif">host/port/scheme for curl samples</text>
  <rect x="218" y="138" width="195" height="20" rx="4" fill="#0d1117" stroke="#8b949e" stroke-width="1"/>
  <text x="315" y="152" fill="#8b949e" font-size="7" text-anchor="middle" font-family="sans-serif">output: target/generated-snippets/</text>

  <!-- Snippets -->
  <rect x="480" y="35" width="190" height="90" rx="8" fill="#0d1117" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="575" y="57" fill="#79c0ff" font-size="9.5" text-anchor="middle" font-family="sans-serif" font-weight="bold">AsciiDoc Snippets</text>
  <text x="575" y="74" fill="#8b949e" font-size="7.5" text-anchor="middle" font-family="sans-serif">curl-request.adoc</text>
  <text x="575" y="87" fill="#8b949e" font-size="7.5" text-anchor="middle" font-family="sans-serif">http-request.adoc / http-response.adoc</text>
  <text x="575" y="100" fill="#8b949e" font-size="7.5" text-anchor="middle" font-family="sans-serif">path-parameters.adoc</text>
  <text x="575" y="113" fill="#8b949e" font-size="7.5" text-anchor="middle" font-family="sans-serif">response-fields.adoc</text>

  <!-- Asciidoctor -->
  <rect x="480" y="140" width="190" height="50" rx="8" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="575" y="161" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif" font-weight="bold">Asciidoctor (build)</text>
  <text x="575" y="178" fill="#8b949e" font-size="7.5" text-anchor="middle" font-family="sans-serif">include:: snippets → HTML / PDF docs</text>

  <!-- Arrows -->
  <line x1="157" y1="105" x2="203" y2="105" stroke="#6db33f" stroke-width="1.5" marker-end="url(#rda)"/>
  <line x1="427" y1="90" x2="478" y2="80" stroke="#79c0ff" stroke-width="1.5" marker-end="url(#rdb)"/>
  <line x1="575" y1="127" x2="575" y2="138" stroke="#79c0ff" stroke-width="1.5" marker-end="url(#rdb)"/>

  <text x="340" y="192" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">Docs guaranteed accurate — generated from tests that must pass</text>

  <defs>
    <marker id="rda" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L6,3 L0,6 Z" fill="#6db33f"/></marker>
    <marker id="rdb" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L6,3 L0,6 Z" fill="#79c0ff"/></marker>
  </defs>
</svg>

Tests produce AsciiDoc snippets; Asciidoctor assembles them into HTML/PDF docs. If the test fails, the docs are not generated — accuracy is enforced by the build.

## 5. Runnable example

```java
// RestDocsAutoConfigDemo.java — simulates @AutoConfigureRestDocs / Spring REST Docs patterns
// How to run: java RestDocsAutoConfigDemo.java  (JDK 17+, no dependencies)
// Real use: @WebMvcTest + @AutoConfigureRestDocs; andDo(document("snippet-name", ...))

import java.util.*;

public class RestDocsAutoConfigDemo {

    record Order(String id, String customer, double total) {}
    record SnippetField(String path, String description) {}

    // Simulates MockMvc request result for REST Docs
    static class MockMvcResult {
        final String method;
        final String url;
        final int status;
        final Map<String, Object> responseBody;

        MockMvcResult(String method, String url, int status, Map<String, Object> body) {
            this.method = method; this.url = url;
            this.status = status; this.responseBody = body;
        }
    }

    // Simulates REST Docs snippet generator
    static class RestDocsDocumenter {
        private final String outputDir;
        private final Map<String, List<String>> snippets = new LinkedHashMap<>();

        RestDocsDocumenter(String outputDir) { this.outputDir = outputDir; }

        void document(String snippetName, MockMvcResult result, List<SnippetField> responseFields) {
            System.out.println("\n  [RestDocs] Documenting: " + snippetName);

            // Validate: every response field must be documented
            Set<String> documented = new LinkedHashSet<>();
            for (SnippetField f : responseFields) documented.add(f.path());

            Set<String> actual = result.responseBody.keySet();
            Set<String> missing = new LinkedHashSet<>(actual);
            missing.removeAll(documented);
            if (!missing.isEmpty())
                throw new AssertionError("Undocumented fields in '" + snippetName + "': " + missing
                        + "\n  → REST Docs fails the test if any response field is not described.");

            List<String> files = new ArrayList<>();

            // curl-request.adoc
            String curl = "----\n$ curl -X " + result.method + " 'http://localhost:8080" + result.url + "'\n----";
            files.add("curl-request.adoc:\n" + curl);

            // http-response.adoc
            StringBuilder resp = new StringBuilder("----\nHTTP/1.1 " + result.status + "\n\n");
            resp.append(jsonFrom(result.responseBody)).append("\n----");
            files.add("http-response.adoc:\n" + resp);

            // response-fields.adoc
            StringBuilder fields = new StringBuilder("|===\n|Path|Description\n\n");
            for (SnippetField f : responseFields)
                fields.append("|`").append(f.path()).append("`|").append(f.description()).append("\n");
            fields.append("|===");
            files.add("response-fields.adoc:\n" + fields);

            snippets.put(outputDir + "/" + snippetName, files);
            for (String file : files) System.out.println("    " + file.replace("\n", "\n    "));
        }

        void printIndex() {
            System.out.println("\n  [RestDocs] Generated snippet directories:");
            snippets.keySet().forEach(k -> System.out.println("    " + k + "/"));
        }

        private String jsonFrom(Map<String, Object> map) {
            List<String> parts = new ArrayList<>();
            for (var e : map.entrySet())
                parts.add("  \"" + e.getKey() + "\": " + (e.getValue() instanceof String ? "\"" + e.getValue() + "\"" : e.getValue()));
            return "{\n" + String.join(",\n", parts) + "\n}";
        }
    }

    // Simulates the controller under test (loaded by @WebMvcTest)
    static class MockMvcOrderController {
        private final Map<String, Order> db;

        MockMvcOrderController(Map<String, Order> db) { this.db = db; }

        MockMvcResult perform(String method, String url) {
            System.out.println("  [MockMvc] " + method + " " + url);
            if (url.startsWith("/orders/")) {
                String id = url.substring("/orders/".length());
                Order o = db.get(id);
                if (o == null) return new MockMvcResult(method, url, 404, Map.of("error", "Not Found"));
                return new MockMvcResult(method, url, 200,
                        new LinkedHashMap<>(Map.of("id", o.id(), "customer", o.customer(), "total", o.total())));
            }
            return new MockMvcResult(method, url, 404, Map.of("error", "Not Found"));
        }
    }

    static void expect(boolean c, String m) {
        if (!c) throw new AssertionError("FAIL: " + m);
        System.out.println("  ✓ " + m);
    }

    public static void main(String[] args) {
        System.out.println("=== @AutoConfigureRestDocs / Spring REST Docs Demo ===\n");

        Map<String, Order> db = new LinkedHashMap<>();
        db.put("1", new Order("1", "alice", 99.99));
        db.put("2", new Order("2", "bob",   149.50));

        MockMvcOrderController controller = new MockMvcOrderController(db);
        RestDocsDocumenter docs = new RestDocsDocumenter("target/generated-snippets");

        // Test 1: GET /orders/1 — fully documented
        System.out.println("--- Test 1: GET /orders/1 — documented ---");
        MockMvcResult result = controller.perform("GET", "/orders/1");
        expect(result.status == 200, "status 200");
        docs.document("get-order", result, List.of(
                new SnippetField("id",       "Unique order identifier"),
                new SnippetField("customer", "Customer name"),
                new SnippetField("total",    "Order total in USD")));
        System.out.println("  ✓ Snippets written for get-order");

        // Test 2: missing field documentation → REST Docs fails the test
        System.out.println("\n--- Test 2: undocumented field causes test failure ---");
        MockMvcResult result2 = controller.perform("GET", "/orders/2");
        try {
            docs.document("get-order-partial", result2, List.of(
                    new SnippetField("id", "Order id")
                    // 'customer' and 'total' not documented — should fail
            ));
            throw new AssertionError("Expected documentation failure");
        } catch (AssertionError e) {
            System.out.println("  ✓ REST Docs correctly failed: " + e.getMessage().split("\n")[0]);
        }

        // Test 3: all fields documented → passes
        System.out.println("\n--- Test 3: GET /orders/2 — all fields documented ---");
        docs.document("get-order-2", result2, List.of(
                new SnippetField("id",       "Order identifier"),
                new SnippetField("customer", "Customer name"),
                new SnippetField("total",    "Order total")));
        System.out.println("  ✓ Snippets written for get-order-2");

        docs.printIndex();

        System.out.println("\n--- Real @AutoConfigureRestDocs ---");
        System.out.println("""
@WebMvcTest(OrderController.class)
@AutoConfigureRestDocs(outputDir = "target/generated-snippets", host = "api.example.com", port = 443)
class OrderApiDocsTest {
    @Autowired MockMvc mockMvc;
    @MockitoBean OrderService orderService;

    @Test
    void getOrder() throws Exception {
        when(orderService.findById("1")).thenReturn(new Order("1","alice",99.99));

        mockMvc.perform(get("/orders/{id}", "1").accept(APPLICATION_JSON))
               .andExpect(status().isOk())
               .andDo(document("get-order",
                   pathParameters(parameterWithName("id").description("Order ID")),
                   responseFields(
                       fieldWithPath("id").description("Order identifier"),
                       fieldWithPath("customer").description("Customer name"),
                       fieldWithPath("total").description("Total in USD"))));
        // target/generated-snippets/get-order/*.adoc written on success
    }
}

// In src/docs/asciidoc/index.adoc:
// == Get Order
// include::{snippets}/get-order/http-request.adoc[]
// include::{snippets}/get-order/http-response.adoc[]
// include::{snippets}/get-order/response-fields.adoc[]""");

        System.out.println("\nAll tests passed.");
    }
}
```

**How to run:** `java RestDocsAutoConfigDemo.java`

## 6. Walkthrough

- **Test 1 (full documentation)**: `controller.perform(GET, /orders/1)` returns a 200 response with `{id, customer, total}`. `docs.document("get-order", ...)` validates that all three response fields are documented, then writes: `curl-request.adoc` (a curl command), `http-response.adoc` (the full HTTP response), and `response-fields.adoc` (a table of field descriptions).
- **Test 2 (missing field)**: only `id` is documented but the response also has `customer` and `total`. REST Docs throws an assertion error — the test fails, preventing silently incomplete documentation.
- **Test 3 (all fields)**: complete documentation for the second order — passes and writes snippets.
- **Asciidoctor**: the generated `*.adoc` files are assembled into a master document and built into HTML/PDF by the Maven/Gradle Asciidoctor plugin during the build lifecycle.

## 7. Gotchas & takeaways

> REST Docs enforces **documentation completeness** at test time. If you add a new field to your API response but forget to add it to `responseFields(...)`, the test fails. This is the key advantage over Swagger: documentation drift is caught by the build, not discovered by users.

> `@AutoConfigureRestDocs` attribute `outputDir` defaults to `target/generated-snippets`. In Gradle projects it's usually `build/generated-snippets`. Set it explicitly: `@AutoConfigureRestDocs(outputDir = "build/generated-snippets")`.

- `relaxedResponseFields(...)` documents a subset of fields without failing on undocumented fields — useful for partial documentation of large responses. Prefer strict `responseFields(...)` for correctness.
- `@AutoConfigureRestDocs` on class vs `@AutoConfigureRestDocs` per-test: applies class-wide — all `mockMvc.perform(...)` calls in the test class participate in REST Docs.
- `preprocessRequest(prettyPrint())`, `preprocessResponse(prettyPrint())` format the snippet output for readability.
- `WebTestClient` (reactive): use `@AutoConfigureRestDocs` with `WebTestClientRestDocumentationConfigurer` — same pattern, different client.
- Alternative URI: `@AutoConfigureRestDocs(host = "api.example.com", port = 443, scheme = "https")` generates curl samples with your production URL.

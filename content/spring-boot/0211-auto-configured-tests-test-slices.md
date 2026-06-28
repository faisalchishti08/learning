---
card: spring-boot
gi: 211
slug: auto-configured-tests-test-slices
title: Auto-configured tests (test slices)
---

## 1. What it is

**Test slices** are Spring Boot's approach to partial context loading in tests. Each slice annotation (`@WebMvcTest`, `@DataJpaTest`, `@DataMongoTest`, etc.) starts only the beans needed for one architectural layer. The slice is pre-configured with the minimal set of auto-configurations for that layer. This is much faster than `@SpringBootTest` (which loads everything) while still testing real Spring wiring within the slice.

## 2. Why & when

Full `@SpringBootTest` loads JPA, security, caching, Actuator, and everything else — even when your test only cares about a controller's request mapping. Test slices solve this:
- `@WebMvcTest`: only web layer (controllers, filters, MVC config) — no JPA.
- `@DataJpaTest`: only JPA/Hibernate + in-memory DB — no web.
- `@JsonTest`: only Jackson serialization — no web, no JPA.

Use slices to keep **unit-style tests fast** while still exercising real Spring configuration (request parsing, JSON serialization, SQL generation) that you can't test with a plain JUnit test.

## 3. Core concept

**Available slice annotations:**

| Slice | What's loaded |
|---|---|
| `@WebMvcTest` | Controllers, `@ControllerAdvice`, filters, `MockMvc` |
| `@WebFluxTest` | Reactive controllers, `WebTestClient` |
| `@DataJpaTest` | JPA repositories, `EntityManager`, in-memory H2 |
| `@DataJdbcTest` | Spring Data JDBC repositories |
| `@DataMongoTest` | MongoDB repositories (embedded Flapdoodle) |
| `@DataRedisTest` | Redis repositories |
| `@JsonTest` | Jackson `ObjectMapper`, JSON serialization |
| `@RestClientTest` | `RestTemplate`, `MockRestServiceServer` |
| `@JooqTest` | jOOQ `DSLContext` |
| `@GraphQlTest` | Spring for GraphQL |

Slice annotations **exclude `@Service` and `@Repository`** beans unless you add them via `@Import` or use `@MockitoBean` for dependencies. This is intentional — the slice tests one layer while mocking adjacent layers.

## 4. Diagram

<svg viewBox="0 0 680 205" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Full @SpringBootTest loads all layers; test slices load only one layer with relevant auto-configuration; adjacent layers are mocked">
  <!-- Full context -->
  <rect x="10" y="20" width="130" height="165" rx="8" fill="#1c2430" stroke="#8b949e" stroke-width="1.5"/>
  <text x="75" y="42" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif" font-weight="bold">@SpringBootTest</text>
  <text x="75" y="58" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">full context</text>
  <rect x="20" y="68" width="110" height="22" rx="4" fill="#0d1117" stroke="#6db33f" stroke-width="1"/>
  <text x="75" y="83" fill="#6db33f" font-size="8" text-anchor="middle" font-family="sans-serif">Web Layer</text>
  <rect x="20" y="96" width="110" height="22" rx="4" fill="#0d1117" stroke="#6db33f" stroke-width="1"/>
  <text x="75" y="111" fill="#6db33f" font-size="8" text-anchor="middle" font-family="sans-serif">Service Layer</text>
  <rect x="20" y="124" width="110" height="22" rx="4" fill="#0d1117" stroke="#6db33f" stroke-width="1"/>
  <text x="75" y="139" fill="#6db33f" font-size="8" text-anchor="middle" font-family="sans-serif">JPA / DB</text>
  <rect x="20" y="152" width="110" height="22" rx="4" fill="#0d1117" stroke="#6db33f" stroke-width="1"/>
  <text x="75" y="167" fill="#6db33f" font-size="8" text-anchor="middle" font-family="sans-serif">Security / Actuator</text>

  <!-- @WebMvcTest slice -->
  <rect x="160" y="20" width="155" height="165" rx="8" fill="#1c2430" stroke="#6db33f" stroke-width="2"/>
  <text x="237" y="42" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif" font-weight="bold">@WebMvcTest</text>
  <rect x="170" y="55" width="135" height="50" rx="4" fill="#0d1117" stroke="#6db33f" stroke-width="1.5"/>
  <text x="237" y="73" fill="#6db33f" font-size="9" text-anchor="middle" font-family="sans-serif">Web Layer only</text>
  <text x="237" y="88" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">Controllers, MockMvc</text>
  <text x="237" y="100" fill="#8b949e" font-size="7" text-anchor="middle" font-family="sans-serif">@ControllerAdvice, Filters</text>
  <rect x="170" y="115" width="135" height="30" rx="4" fill="#1c2430" stroke="#8b949e" stroke-width="1"/>
  <text x="237" y="133" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">@MockitoBean Service</text>
  <rect x="170" y="150" width="135" height="28" rx="4" fill="#1c2430" stroke="#8b949e" stroke-width="1"/>
  <text x="237" y="168" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">no JPA, no Actuator</text>

  <!-- @DataJpaTest slice -->
  <rect x="330" y="20" width="155" height="165" rx="8" fill="#1c2430" stroke="#79c0ff" stroke-width="2"/>
  <text x="407" y="42" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif" font-weight="bold">@DataJpaTest</text>
  <rect x="340" y="55" width="135" height="50" rx="4" fill="#0d1117" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="407" y="73" fill="#79c0ff" font-size="9" text-anchor="middle" font-family="sans-serif">JPA layer only</text>
  <text x="407" y="88" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">Repositories, EntityManager</text>
  <text x="407" y="100" fill="#8b949e" font-size="7" text-anchor="middle" font-family="sans-serif">In-memory H2 (rolled back)</text>
  <rect x="340" y="115" width="135" height="30" rx="4" fill="#1c2430" stroke="#8b949e" stroke-width="1"/>
  <text x="407" y="133" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">no web, no security</text>
  <rect x="340" y="150" width="135" height="28" rx="4" fill="#1c2430" stroke="#8b949e" stroke-width="1"/>
  <text x="407" y="168" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">@Transactional rollback</text>

  <!-- @JsonTest slice -->
  <rect x="500" y="20" width="170" height="165" rx="8" fill="#1c2430" stroke="#79c0ff" stroke-width="2"/>
  <text x="585" y="42" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif" font-weight="bold">@JsonTest</text>
  <rect x="510" y="55" width="150" height="50" rx="4" fill="#0d1117" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="585" y="73" fill="#79c0ff" font-size="9" text-anchor="middle" font-family="sans-serif">JSON only</text>
  <text x="585" y="88" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">ObjectMapper (Jackson)</text>
  <text x="585" y="100" fill="#8b949e" font-size="7" text-anchor="middle" font-family="sans-serif">JacksonTester, JsonbTester</text>
  <rect x="510" y="115" width="150" height="30" rx="4" fill="#1c2430" stroke="#8b949e" stroke-width="1"/>
  <text x="585" y="133" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">no web, no JPA, no Mockito</text>
  <rect x="510" y="150" width="150" height="28" rx="4" fill="#1c2430" stroke="#8b949e" stroke-width="1"/>
  <text x="585" y="168" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">fastest: one ObjectMapper</text>
</svg>

Each slice loads only the relevant infrastructure; adjacent layers must be mocked. Slices are far faster than full `@SpringBootTest`.

## 5. Runnable example

```java
// TestSlicesDemo.java — demonstrates what each test slice provides and excludes
// How to run: java TestSlicesDemo.java  (JDK 17+, no dependencies)
// Real tests: use @WebMvcTest / @DataJpaTest / @JsonTest on test classes

import java.util.*;

public class TestSlicesDemo {

    // Describes what a test slice includes
    record Slice(String annotation, List<String> included, List<String> excluded,
                 String primaryTestUtil, String idealFor) {}

    static final List<Slice> SLICES = List.of(
        new Slice("@WebMvcTest",
            List.of("Controllers (@RestController, @Controller)",
                    "@ControllerAdvice, HandlerInterceptors",
                    "Spring MVC configuration, JSON converters",
                    "MockMvc auto-configured",
                    "Spring Security (if on classpath)"),
            List.of("@Service, @Repository beans",
                    "JPA auto-configuration",
                    "Actuator endpoints",
                    "Full @SpringBootApplication scan"),
            "MockMvc",
            "Testing request mapping, response JSON, HTTP status codes, validation"
        ),
        new Slice("@DataJpaTest",
            List.of("JPA repositories",
                    "EntityManager, TestEntityManager",
                    "H2 in-memory database (auto-configured)",
                    "Flyway / Liquibase (if on classpath)",
                    "@Transactional (rolls back after each test)"),
            List.of("@Service, @Controller beans",
                    "Web layer, security",
                    "RabbitMQ, Kafka, Redis auto-configuration"),
            "TestEntityManager / JpaRepository",
            "Testing custom JPQL queries, entity constraints, repository methods"
        ),
        new Slice("@JsonTest",
            List.of("JacksonAutoConfiguration (ObjectMapper)",
                    "JacksonTester<T>",
                    "JsonbTester (if Jsonb on classpath)",
                    "GsonTester (if Gson on classpath)"),
            List.of("All web, JPA, security, messaging auto-configs"),
            "JacksonTester",
            "Testing @JsonProperty, @JsonInclude, custom serializers/deserializers"
        ),
        new Slice("@RestClientTest",
            List.of("RestTemplate / RestClient",
                    "MockRestServiceServer",
                    "Jackson ObjectMapper"),
            List.of("Web layer, JPA, security"),
            "MockRestServiceServer",
            "Testing HTTP clients — stub external API responses"
        ),
        new Slice("@WebFluxTest",
            List.of("Reactive controllers (@RestController)",
                    "WebFlux configuration",
                    "WebTestClient auto-configured"),
            List.of("JPA, security (unless configured)"),
            "WebTestClient",
            "Testing reactive endpoints, SSE, WebSocket"
        )
    );

    public static void main(String[] args) {
        System.out.println("=== Test Slices (Auto-configured Tests) Overview ===\n");

        for (Slice s : SLICES) {
            System.out.println("┌─ " + s.annotation() + " ─────────────────────────");
            System.out.println("│  Primary test utility: " + s.primaryTestUtil());
            System.out.println("│  Ideal for: " + s.idealFor());
            System.out.println("│  Included:");
            s.included().forEach(i -> System.out.println("│    ✓ " + i));
            System.out.println("│  Excluded:");
            s.excluded().forEach(e -> System.out.println("│    ✗ " + e));
            System.out.println("└─────────────────────────────────────────────\n");
        }

        System.out.println("--- Key patterns ---");
        System.out.println("""
// @WebMvcTest: test controller in isolation
@WebMvcTest(OrderController.class)
class OrderControllerTest {
    @Autowired MockMvc mockMvc;
    @MockitoBean OrderService orderService; // mock the service layer

    @Test void getOrder_returns200() throws Exception {
        when(orderService.findById("1")).thenReturn(new Order("1","alice"));
        mockMvc.perform(get("/api/orders/1"))
               .andExpect(status().isOk())
               .andExpect(jsonPath("$.id").value("1"));
    }
}

// @DataJpaTest: test repository in isolation
@DataJpaTest
class OrderRepositoryTest {
    @Autowired OrderRepository repo;
    @Autowired TestEntityManager em;

    @Test void findByCustomer_returnsOrders() {
        em.persist(new Order("alice", 99.99));
        em.flush();
        var orders = repo.findByCustomer("alice");
        assertThat(orders).hasSize(1);
    }
}""");
    }
}
```

**How to run:** `java TestSlicesDemo.java`

## 6. Walkthrough

- **`@WebMvcTest`**: includes controllers and MVC infrastructure but NOT services or JPA. Services that your controller depends on must be `@MockitoBean`. The mock is injected into the controller. This makes web tests fast and isolated from database issues.
- **`@DataJpaTest`**: includes only JPA and uses H2 in-memory. Each test method runs in a transaction that is rolled back at the end — the database is clean for every test without truncating tables. `TestEntityManager` lets you persist test data directly.
- **`@JsonTest`**: the smallest slice — only an `ObjectMapper`. `JacksonTester<T>` provides `write(obj).getJson()` and `parse(json).getObject()`. Used to test custom serialization annotations without starting any server.
- **`@RestClientTest`**: provides `MockRestServiceServer` to intercept `RestTemplate` calls and return stubbed responses. Tests your HTTP client code without making real network calls.
- The code snippet shows the `@WebMvcTest` + `@MockitoBean OrderService` pattern — the most common slice usage.

## 7. Gotchas & takeaways

> `@WebMvcTest` includes Spring Security by default — if your app has a `SecurityFilterChain`, requests may get a `401` or `403` in tests. Add `@MockitoBean` for `UserDetailsService` or use `@WithMockUser` to authenticate.

> `@DataJpaTest` replaces the production datasource with H2 by default. To test against a real database (PostgreSQL, MySQL), add `@AutoConfigureTestDatabase(replace = Replace.NONE)` and use Testcontainers for the datasource.

- Each slice loads only its `AutoConfiguration` — they don't conflict with each other.
- Beans not loaded by the slice must be provided via `@MockitoBean` or `@Import(SomeConfig.class)`.
- Slice tests are much faster than `@SpringBootTest` — aim to cover your controller layer with `@WebMvcTest` and your data layer with `@DataJpaTest` before reaching for full integration tests.
- You can create your own slice with `@TypeExcludeFilters` and `@AutoConfigureXxx` — useful for custom frameworks or reusable test infrastructure in large organizations.

---
card: microservices
gi: 424
slug: springboottest-slices-full-context-tests
title: "@SpringBootTest slices & full-context tests"
---

## 1. What it is

`@SpringBootTest` is the annotation that tells Spring Boot to boot a real `ApplicationContext` for a test — wiring up beans, configuration, and (optionally) an embedded web server, the same machinery that runs in production. Used plain, it loads the **full context**: every `@Component`, `@Service`, `@Repository`, `@Configuration`, and auto-configuration your application defines. A **test slice** is a narrower, purpose-built alternative — annotations like `@WebMvcTest` or `@DataJpaTest` that load only the beans relevant to one architectural layer (the web layer, the data layer) and skip everything else. Both are built on the same underlying context-caching machinery; the difference is how much of the application each one asks Spring to actually stand up.

## 2. Why & when

You choose between a full-context test and a slice based on a direct trade-off between **realism** and **speed**, and understanding that trade-off is the single most important decision in Spring Boot testing:

- **A full `@SpringBootTest` is the most realistic test you can run without a browser or real HTTP client hitting a deployed instance.** It exercises real auto-configuration, real bean wiring, and (with `webEnvironment = RANDOM_PORT`) a real embedded server — closest to what [component testing](0414-component-testing-single-service-in-isolation.md) asks for.
- **It's also the slowest and most expensive test to run**, because Spring has to construct the entire object graph: every repository, every service, every configuration class, potentially a real or embedded database connection. A suite with hundreds of full-context tests can take minutes just booting contexts repeatedly.
- **A slice trims the object graph to exactly what one layer needs.** `@WebMvcTest` boots controllers, filters, and MVC infrastructure but not repositories; `@DataJpaTest` boots repositories and a database but not controllers. Fewer beans means faster startup and a test that fails for reasons specific to that layer, not because an unrelated bean somewhere else in the app couldn't be constructed.
- **Spring caches contexts across tests with identical configuration**, so the real cost isn't "one full-context test is slow" — it's "many *differently configured* full-context tests each force a fresh, slow context build," which is exactly what happens when tests casually add one-off `@MockBean`s or profile overrides without realizing each unique combination busts the cache.

You reach for a slice by default, for the same reason the [test pyramid](0411-test-pyramid-for-microservices.md) favors cheap tests: most logic can be verified without needing the whole application wired up. You reach for a full `@SpringBootTest` specifically when you need to verify that beans actually wire together correctly end-to-end within the service — something no slice, by design, can check.

## 3. Core concept

Picture your Spring application as a fully furnished house. A full-context test turns on every light, every appliance, every system in the house before you check whether the kitchen faucet works — thorough, but slow, and you pay that cost even if you only care about the faucet. A test slice is like a technician who only needs to check the plumbing: they connect just the pipes and the water supply, skip the electrical system entirely, and get to the answer in a fraction of the time, with a failure that's obviously about plumbing rather than something ambiguous involving the whole house.

Concretely, three context-loading strategies exist, from broadest to narrowest:

1. **`@SpringBootTest`** — loads the full `ApplicationContext`. Configurable via `webEnvironment`: `MOCK` (default, a mock servlet environment, no real port), `RANDOM_PORT` or `DEFINED_PORT` (a real embedded server you can hit with a real HTTP client), or `NONE` (no web environment at all, for pure service-layer full-context checks).
2. **Test slices** — `@WebMvcTest`, `@WebFluxTest`, `@DataJpaTest`, `@JsonTest`, and others, each registered by Spring Boot to auto-configure only the beans relevant to that slice and explicitly exclude full auto-configuration. Anything a slice doesn't provide (like a `@Service` a `@WebMvcTest`-scoped controller depends on) must be supplied as a `@MockBean`/`@MockitoBean`.
3. **Context caching** — Spring's test framework keys a cache on the exact combination of configuration (active profiles, property overrides, mocked beans, context initializers) a test class requests. Tests sharing an identical combination reuse the same booted context instead of paying startup cost again; tests with even a slightly different combination force a new context build.

```java
@SpringBootTest(webEnvironment = SpringBootTest.WebEnvironment.RANDOM_PORT)
class OrderServiceApplicationTests {
    @Autowired TestRestTemplate restTemplate;

    @Test
    void applicationContextLoadsAndRespondsToHealthCheck() {
        var response = restTemplate.getForEntity("/actuator/health", String.class);
        assertThat(response.getStatusCode().is2xxSuccessful()).isTrue();
    }
}
```

`RANDOM_PORT` boots a real embedded server on an unused port, and `TestRestTemplate` makes a genuine HTTP call to it — this is as close to "run the real app" as a test gets without deploying anywhere.

## 4. Diagram

<svg viewBox="0 0 640 260" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="A full SpringBootTest context contains web, service, and repository beans together; a WebMvcTest slice contains only web-layer beans with the rest mocked; a DataJpaTest slice contains only repository and database beans, skipping web and service beans entirely">
  <text x="120" y="20" fill="#e6edf3" font-size="12" text-anchor="middle" font-family="sans-serif">@SpringBootTest (full)</text>
  <rect x="20" y="30" width="200" height="150" rx="10" fill="#1c2430" stroke="#6db33f" stroke-width="2"/>
  <rect x="35" y="45" width="80" height="30" rx="5" fill="#1c2430" stroke="#79c0ff"/>
  <text x="75" y="64" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">Controller</text>
  <rect x="130" y="45" width="80" height="30" rx="5" fill="#1c2430" stroke="#79c0ff"/>
  <text x="170" y="64" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">Service</text>
  <rect x="35" y="90" width="80" height="30" rx="5" fill="#1c2430" stroke="#79c0ff"/>
  <text x="75" y="109" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">Repository</text>
  <rect x="130" y="90" width="80" height="30" rx="5" fill="#1c2430" stroke="#79c0ff"/>
  <text x="170" y="109" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">DataSource</text>
  <text x="120" y="160" fill="#f0883e" font-size="9" text-anchor="middle" font-family="sans-serif">everything wired -- slow, realistic</text>

  <text x="330" y="20" fill="#e6edf3" font-size="12" text-anchor="middle" font-family="sans-serif">@WebMvcTest</text>
  <rect x="270" y="30" width="120" height="150" rx="10" fill="#1c2430" stroke="#79c0ff" stroke-width="2"/>
  <rect x="285" y="45" width="90" height="30" rx="5" fill="#1c2430" stroke="#6db33f"/>
  <text x="330" y="64" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">Controller</text>
  <rect x="285" y="90" width="90" height="30" rx="5" fill="#1c2430" stroke="#f85149" stroke-dasharray="3,2"/>
  <text x="330" y="109" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">Service (mocked)</text>
  <text x="330" y="160" fill="#6db33f" font-size="9" text-anchor="middle" font-family="sans-serif">web layer only -- fast</text>

  <text x="530" y="20" fill="#e6edf3" font-size="12" text-anchor="middle" font-family="sans-serif">@DataJpaTest</text>
  <rect x="470" y="30" width="140" height="150" rx="10" fill="#1c2430" stroke="#f0883e" stroke-width="2"/>
  <rect x="485" y="45" width="110" height="30" rx="5" fill="#1c2430" stroke="#6db33f"/>
  <text x="540" y="64" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">Repository</text>
  <rect x="485" y="90" width="110" height="30" rx="5" fill="#1c2430" stroke="#6db33f"/>
  <text x="540" y="109" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">embedded/test DB</text>
  <text x="540" y="160" fill="#6db33f" font-size="9" text-anchor="middle" font-family="sans-serif">data layer only -- fast</text>

  <text x="320" y="230" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">slices trade realism for speed by loading only the beans one layer needs</text>
</svg>

A full context wires every layer together; each slice narrows the object graph to one layer, trading some realism for a large speed gain.

## 5. Runnable example

Scenario: an `OrderLookupService` that depends on an `OrderRepository`. We model Spring's context-loading behavior in plain Java (standing in for the real framework) — first a "full context" that wires everything, then a "slice" that wires only what's needed, then a context-cache simulation showing why unnecessary configuration differences cost real test-suite time.

### Level 1 — Basic

```java
// File: FullContextBasic.java -- simulates a FULL SpringBootTest context:
// every bean gets constructed and wired together, standing in for what
// @SpringBootTest actually does at test startup.
import java.util.*;

public class FullContextBasic {
    static class OrderRepository {
        Map<String, String> data = Map.of("order-1", "Widget x3");
        String findById(String id) { return data.get(id); }
    }
    static class OrderLookupService {
        final OrderRepository repository;
        OrderLookupService(OrderRepository repository) { this.repository = repository; }
        String lookup(String orderId) { return repository.findById(orderId); }
    }
    static class OrderController {
        final OrderLookupService service;
        OrderController(OrderLookupService service) { this.service = service; }
        String handleGet(String orderId) { return service.lookup(orderId); }
    }

    // Simulates Spring constructing the WHOLE object graph -- controller, service, repository, all wired.
    static OrderController bootFullContext() {
        System.out.println("[FullContext] constructing OrderRepository, OrderLookupService, OrderController...");
        OrderRepository repository = new OrderRepository();
        OrderLookupService service = new OrderLookupService(repository);
        return new OrderController(service);
    }

    public static void main(String[] args) {
        OrderController controller = bootFullContext();
        System.out.println("Full-context result: " + controller.handleGet("order-1"));
    }
}
```

How to run: `java FullContextBasic.java`

`bootFullContext` constructs every layer — repository, service, controller — exactly the way a real `@SpringBootTest` boots the whole `ApplicationContext` before a test runs. The test then exercises the top of the stack (`handleGet`) and implicitly proves every layer beneath it wired together correctly, which is the realism a full-context test buys you.

### Level 2 — Intermediate

```java
// File: SliceContextBasic.java -- the SAME architecture, now simulating a
// WEB-LAYER SLICE (like @WebMvcTest): only the controller is real, and the
// service it depends on is a STAND-IN (mocked), never a real repository.
public class SliceContextBasic {
    interface OrderLookupService { String lookup(String orderId); }

    static class OrderController {
        final OrderLookupService service;
        OrderController(OrderLookupService service) { this.service = service; }
        String handleGet(String orderId) { return service.lookup(orderId); }
    }

    // A hand-rolled stand-in for @MockBean: NO real OrderRepository is ever constructed.
    static class MockOrderLookupService implements OrderLookupService {
        String scriptedResponse;
        MockOrderLookupService(String scriptedResponse) { this.scriptedResponse = scriptedResponse; }
        public String lookup(String orderId) {
            System.out.println("[MockOrderLookupService] returning scripted response, no real repository involved");
            return scriptedResponse;
        }
    }

    // Simulates Spring constructing ONLY the web-layer bean, with its collaborator mocked.
    static OrderController bootWebSlice() {
        System.out.println("[WebSlice] constructing OrderController only -- service layer is mocked, no repository, no database");
        OrderLookupService mockService = new MockOrderLookupService("Widget x3");
        return new OrderController(mockService);
    }

    public static void main(String[] args) {
        OrderController controller = bootWebSlice();
        System.out.println("Slice result: " + controller.handleGet("order-1"));
    }
}
```

How to run: `java SliceContextBasic.java`

`bootWebSlice` constructs only `OrderController`, exactly what `@WebMvcTest(OrderController.class)` does in real Spring Boot — the `OrderLookupService` dependency is satisfied with `MockOrderLookupService`, a stand-in for `@MockBean`, rather than the real service and its real repository. Nothing here proves the *real* service or repository work correctly; it proves only that the controller correctly delegates to whatever `OrderLookupService` it's given — a narrower but much faster claim.

### Level 3 — Advanced

```java
// File: ContextCacheSimulation.java -- the SAME two boot strategies, now
// with a CONTEXT CACHE simulation showing the production-flavored problem:
// tests with EVEN SLIGHTLY different configuration each force an expensive
// fresh context build, while identically configured tests reuse one context.
import java.util.*;

public class ContextCacheSimulation {
    record ContextKey(String testType, List<String> activeProfiles, List<String> mockedBeans) {}

    static class ContextCache {
        private final Map<ContextKey, Object> cache = new HashMap<>();
        private int contextsBuilt = 0;

        Object getOrBuild(ContextKey key) {
            if (cache.containsKey(key)) {
                System.out.println("[Cache] REUSED context for " + key);
                return cache.get(key);
            }
            contextsBuilt++;
            System.out.println("[Cache] BUILDING new context (#" + contextsBuilt + ") for " + key
                    + " -- this is the expensive path");
            Object context = new Object();
            cache.put(key, context);
            return context;
        }

        int contextsBuilt() { return contextsBuilt; }
    }

    public static void main(String[] args) {
        ContextCache cache = new ContextCache();

        // Three tests using IDENTICAL configuration -- should share ONE context.
        cache.getOrBuild(new ContextKey("WebMvcTest", List.of("test"), List.of("OrderLookupService")));
        cache.getOrBuild(new ContextKey("WebMvcTest", List.of("test"), List.of("OrderLookupService")));
        cache.getOrBuild(new ContextKey("WebMvcTest", List.of("test"), List.of("OrderLookupService")));

        // A FOURTH test adds one extra @MockBean -- looks harmless, but changes the
        // cache key entirely, forcing a brand-new context build.
        cache.getOrBuild(new ContextKey("WebMvcTest", List.of("test"), List.of("OrderLookupService", "AuditLogger")));

        // A FIFTH test uses a different active profile -- ALSO forces a new build,
        // even though the mocked beans are otherwise identical.
        cache.getOrBuild(new ContextKey("WebMvcTest", List.of("test", "audit-enabled"), List.of("OrderLookupService")));

        System.out.println("Total contexts actually built: " + cache.contextsBuilt()
                + " (out of 5 tests) -- each unique config combination pays full startup cost once.");
    }
}
```

How to run: `java ContextCacheSimulation.java`

`ContextKey` models exactly what Spring's `TestContext` framework uses to decide whether to reuse a cached context: the test type/configuration class, active profiles, and the set of mocked beans. The first three calls share an identical key and reuse one context. The fourth call adds a single extra mocked bean — a completely reasonable-looking change in isolation — and it silently produces a brand-new cache key, forcing an expensive rebuild. The fifth call changes only the active profile list and, for the same reason, also forces a rebuild. This is the real-world trap: a test suite can look like it's using "the same slice everywhere" while actually paying for five separate context builds because of small, easy-to-miss configuration differences.

## 6. Walkthrough

Trace `ContextCacheSimulation.main` in order. **First**, `cache.getOrBuild` is called with key `(WebMvcTest, [test], [OrderLookupService])`. The cache is empty, so this **builds** context #1 and stores it under that exact key.

**Next**, the same key is passed twice more. Both calls find an exact match in `cache` and **reuse** context #1 — no new construction happens, which is why running many tests that share identical `@WebMvcTest` configuration is cheap after the first one pays the startup cost.

**Then**, a fourth call passes a key that adds `"AuditLogger"` to the mocked-beans list. Because `ContextKey` is a record, equality is based on *all* its fields — `mockedBeans` now differs from every previously cached key, so no match is found, and the cache **builds** context #2, paying the full construction cost again.

**Finally**, a fifth call changes `activeProfiles` to include `"audit-enabled"` while reverting the mocked beans back to the original single-service list. Even though this configuration shares its mocked-beans list with the very first key, the profile list differs, so it's still a cache miss — the cache **builds** context #3.

```
[Cache] BUILDING new context (#1) for ContextKey[testType=WebMvcTest, activeProfiles=[test], mockedBeans=[OrderLookupService]]
[Cache] REUSED context for ContextKey[testType=WebMvcTest, activeProfiles=[test], mockedBeans=[OrderLookupService]]
[Cache] REUSED context for ContextKey[testType=WebMvcTest, activeProfiles=[test], mockedBeans=[OrderLookupService]]
[Cache] BUILDING new context (#2) for ContextKey[testType=WebMvcTest, activeProfiles=[test], mockedBeans=[OrderLookupService, AuditLogger]]
[Cache] BUILDING new context (#3) for ContextKey[testType=WebMvcTest, activeProfiles=[test, audit-enabled], mockedBeans=[OrderLookupService]]
Total contexts actually built: 3 (out of 5 tests) -- each unique config combination pays full startup cost once.
```

## 7. Gotchas & takeaways

> Adding a single `@MockBean` to just one test class in an otherwise-shared slice configuration silently busts the context cache for that class and any others that don't share its exact bean set — a whole test suite can end up rebuilding contexts dozens of times without anyone noticing, because each individual test still "looks fine" in isolation. Auditing CI build time by counting distinct context configurations often finds this before anyone thinks to look for it directly.

- Prefer slices (`@WebMvcTest`, `@DataJpaTest`, and friends) for the bulk of your Spring-aware tests, matching the [test pyramid](0411-test-pyramid-for-microservices.md)'s preference for cheap, focused tests over broad, slow ones.
- Reserve full `@SpringBootTest` for genuinely verifying that beans wire together correctly, or for a thin top layer of tests closest to [component testing](0414-component-testing-single-service-in-isolation.md) — not as the default for every test class.
- Keep test configuration (profiles, mocked beans, property overrides) consistent across test classes wherever possible; every unique combination is a new context build the whole suite pays for.
- See [web layer tests](0425-web-layer-tests-webmvctest-webfluxtest.md) and [data layer tests](0426-data-layer-tests-datajpatest-etc.md) for the two most common slices in practice, and [@MockBean / @MockitoBean](0432-mockbean-mockitobean-for-collaborators.md) for how slices supply the collaborators they don't construct themselves.
- `webEnvironment = RANDOM_PORT` full-context tests are the closest thing to running the real application and are a reasonable substitute for a dedicated [component test](0414-component-testing-single-service-in-isolation.md) harness when a service is small enough that the extra boot cost stays manageable.

---
card: spring-framework
gi: 106
slug: repository-service-controller-stereotypes
title: "@Repository, @Service, @Controller stereotypes"
---

## 1. What it is

`@Repository`, `@Service`, and `@Controller` are specialised stereotypes — each is a `@Component` with a semantic label. They auto-register beans exactly like `@Component` does, but they carry additional meaning and, in the case of `@Repository`, additional behaviour.

| Annotation | Layer | Extra behaviour |
|---|---|---|
| `@Repository` | Data access (DAO) | Translates persistence exceptions into Spring's `DataAccessException` hierarchy |
| `@Service` | Business logic | No extra behaviour — pure semantic label |
| `@Controller` | Spring MVC web layer | Makes the class a request-handler; `@RequestMapping` methods become endpoints |

## 2. Why & when

All three register beans the same way as `@Component`. The reason to use the specific stereotype is:

- **Readability** — a new developer immediately knows the layer a class belongs to.
- **Exception translation** (`@Repository`) — persistence exceptions from JDBC, JPA, or Hibernate are wrapped into Spring's uniform `DataAccessException` hierarchy, hiding vendor-specific exception types from callers.
- **AOP pointcuts** — teams apply transaction management, security, and logging via aspect-oriented pointcuts that target classes annotated with specific stereotypes.
- **Tooling** — IDEs and Spring Boot DevTools understand the stereotypes and offer specialised hints.

Use the most specific annotation that fits:
- Data access class → `@Repository`
- Business logic class → `@Service`
- MVC request handler → `@Controller` (or `@RestController` for JSON/XML REST endpoints)
- Anything else → `@Component`

## 3. Core concept

All three annotations are meta-annotated with `@Component`, so component scanning treats them identically for bean registration. The extra semantics are applied by additional mechanisms:

- **`@Repository` exception translation** — `PersistenceExceptionTranslationPostProcessor` (a `BeanPostProcessor`) wraps `@Repository` beans in a proxy that intercepts persistence exceptions and converts them.
- **`@Service`** — no post-processing beyond component registration; the label is purely informational.
- **`@Controller`** — `RequestMappingHandlerMapping` (part of Spring MVC) inspects the class for `@RequestMapping` / `@GetMapping` / etc. and registers request routes.

## 4. Diagram

<svg viewBox="0 0 700 220" xmlns="http://www.w3.org/2000/svg">
  <!-- @Component root -->
  <rect x="270" y="10" width="160" height="36" rx="7" fill="#1c2430" stroke="#6db33f" stroke-width="2"/>
  <text x="350" y="32" fill="#6db33f" font-size="13" text-anchor="middle" font-family="sans-serif">@Component</text>

  <!-- Three children -->
  <rect x="20" y="90" width="155" height="44" rx="7" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="97" y="113" fill="#79c0ff" font-size="12" text-anchor="middle" font-family="sans-serif">@Repository</text>
  <text x="97" y="127" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">DAO + exception xlate</text>

  <rect x="272" y="90" width="155" height="44" rx="7" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="349" y="113" fill="#6db33f" font-size="12" text-anchor="middle" font-family="sans-serif">@Service</text>
  <text x="349" y="127" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">business logic label</text>

  <rect x="524" y="90" width="155" height="44" rx="7" fill="#1c2430" stroke="#e6edf3" stroke-width="1.5"/>
  <text x="601" y="113" fill="#e6edf3" font-size="12" text-anchor="middle" font-family="sans-serif">@Controller</text>
  <text x="601" y="127" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">MVC request handler</text>

  <!-- Lines from @Component to children -->
  <line x1="295" y1="46" x2="140" y2="88" stroke="#6db33f" stroke-width="1.5" marker-end="url(#a106)"/>
  <line x1="350" y1="46" x2="350" y2="88" stroke="#6db33f" stroke-width="1.5" marker-end="url(#a106)"/>
  <line x1="405" y1="46" x2="560" y2="88" stroke="#6db33f" stroke-width="1.5" marker-end="url(#a106)"/>

  <!-- All register beans -->
  <rect x="270" y="175" width="160" height="36" rx="7" fill="#1c2430" stroke="#8b949e" stroke-width="1.5"/>
  <text x="350" y="197" fill="#8b949e" font-size="11" text-anchor="middle" font-family="sans-serif">Same: auto-registers bean</text>
  <line x1="97"  y1="134" x2="270" y2="187" stroke="#8b949e" stroke-width="1" stroke-dasharray="4,3" marker-end="url(#b106)"/>
  <line x1="349" y1="134" x2="349" y2="173" stroke="#8b949e" stroke-width="1" stroke-dasharray="4,3" marker-end="url(#b106)"/>
  <line x1="601" y1="134" x2="430" y2="187" stroke="#8b949e" stroke-width="1" stroke-dasharray="4,3" marker-end="url(#b106)"/>
  <defs>
    <marker id="a106" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#6db33f"/></marker>
    <marker id="b106" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#8b949e"/></marker>
  </defs>
</svg>

All three stereotypes extend `@Component` and auto-register beans; `@Repository` adds exception translation, `@Controller` activates MVC routing.

## 5. Runnable example

### Level 1 — Basic

Three classes across three layers, each with the correct stereotype.

```java
// StereotypesBasic.java
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.context.annotation.*;
import org.springframework.stereotype.*;
import java.util.*;

@Repository
class UserRepository {
    private final Map<Integer, String> db = new HashMap<>(Map.of(1, "Alice", 2, "Bob"));

    public String findById(int id) {
        System.out.println("[Repository] findById(" + id + ")");
        return db.get(id);
    }

    public void save(int id, String name) {
        db.put(id, name);
        System.out.println("[Repository] saved: " + id + " → " + name);
    }
}

@Service
class UserService {
    @Autowired private UserRepository repo;

    public String getUser(int id) {
        System.out.println("[Service] getUser(" + id + ")");
        String user = repo.findById(id);
        return user != null ? user : "Unknown";
    }

    public void createUser(int id, String name) {
        System.out.println("[Service] createUser(" + name + ")");
        repo.save(id, name);
    }
}

@Controller
class UserController {
    @Autowired private UserService userService;

    // Simulated request handler (no web context — called directly)
    public String handleGetUser(int id) {
        System.out.println("[Controller] GET /users/" + id);
        return "200 OK: " + userService.getUser(id);
    }

    public String handleCreateUser(int id, String name) {
        System.out.println("[Controller] POST /users");
        userService.createUser(id, name);
        return "201 Created";
    }
}

@Configuration
@ComponentScan
class LayerCfg {}

public class StereotypesBasic {
    public static void main(String[] args) {
        var ctx = new AnnotationConfigApplicationContext(LayerCfg.class);
        var ctrl = ctx.getBean(UserController.class);
        System.out.println(ctrl.handleGetUser(1));
        System.out.println(ctrl.handleCreateUser(3, "Carol"));
        System.out.println(ctrl.handleGetUser(3));
        ctx.close();
    }
}
```

How to run: `java StereotypesBasic.java`

Each class is discovered by component scanning and registered with its stereotype. Calls flow Controller → Service → Repository, each layer printing its own trace so the layered architecture is visible.

### Level 2 — Intermediate

`@Repository` exception translation in action: a simulated persistence exception is caught and re-thrown as a Spring `DataAccessException`.

```java
// StereotypesExcept.java
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.context.annotation.*;
import org.springframework.dao.*;
import org.springframework.dao.support.PersistenceExceptionTranslationPostProcessor;
import org.springframework.stereotype.*;

// Simulated vendor-specific persistence exception
class VendorDbException extends RuntimeException {
    VendorDbException(String msg) { super(msg); }
}

@Repository
class ProductRepository {
    public String findById(int id) {
        if (id < 0) {
            // In real code this would be a JPA/JDBC exception
            throw new VendorDbException("DB error: invalid id " + id);
        }
        return "Product#" + id;
    }
}

@Service
class ProductService {
    @Autowired private ProductRepository repo;

    public String get(int id) {
        try {
            return repo.findById(id);
        } catch (DataAccessException e) {
            // Spring's unified exception — no vendor lock-in
            return "DataAccessException: " + e.getMessage();
        }
    }
}

@Configuration
@ComponentScan
class ExcCfg {
    @Bean
    public static PersistenceExceptionTranslationPostProcessor petpp() {
        return new PersistenceExceptionTranslationPostProcessor();
    }
}

public class StereotypesExcept {
    public static void main(String[] args) {
        var ctx = new AnnotationConfigApplicationContext(ExcCfg.class);
        var svc = ctx.getBean(ProductService.class);
        System.out.println(svc.get(5));    // happy path
        System.out.println(svc.get(-1));   // triggers exception translation
        ctx.close();
    }
}
```

How to run: `java StereotypesExcept.java`

`PersistenceExceptionTranslationPostProcessor` wraps `@Repository` beans. When `VendorDbException` is thrown, the proxy intercepts it, translates it to a Spring `DataAccessException` subclass (specifically `UncategorizedDataAccessException`), and re-throws it — so `ProductService` catches a `DataAccessException`, not a vendor-specific type.

### Level 3 — Advanced

A full three-layer flow with explicit layer boundaries, transaction-like state tracking, and an audit trail showing how data changes at each layer.

```java
// StereotypesFullFlow.java
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.context.annotation.*;
import org.springframework.stereotype.*;
import java.util.*;

record Order(int id, String item, double amount) {}

@Repository
class OrderRepository {
    private final Map<Integer, Order> store = new HashMap<>();
    private int seq = 100;

    public Order save(String item, double amount) {
        int id = ++seq;
        var order = new Order(id, item, amount);
        store.put(id, order);
        System.out.println("[Repository] INSERT orders(id=" + id + ", item=" + item + ", amount=" + amount + ")");
        return order;
    }

    public Optional<Order> findById(int id) {
        System.out.println("[Repository] SELECT * FROM orders WHERE id=" + id);
        return Optional.ofNullable(store.get(id));
    }

    public Collection<Order> findAll() { return store.values(); }
}

@Service
class OrderService {
    @Autowired private OrderRepository repo;

    public Order placeOrder(String item, double amount) {
        System.out.println("[Service] placeOrder: item=" + item + ", amount=" + amount);
        if (item == null || item.isBlank()) throw new IllegalArgumentException("item required");
        if (amount <= 0) throw new IllegalArgumentException("amount must be positive");
        var order = repo.save(item, amount);
        System.out.println("[Service] order placed: " + order);
        return order;
    }

    public Optional<Order> getOrder(int id) {
        System.out.println("[Service] getOrder: id=" + id);
        return repo.findById(id);
    }
}

@Controller
class OrderController {
    @Autowired private OrderService service;

    public String postOrder(String item, double amount) {
        System.out.println("[Controller] POST /orders  body={item=" + item + ", amount=" + amount + "}");
        try {
            var order = service.placeOrder(item, amount);
            return "201 Created: " + order;
        } catch (IllegalArgumentException e) {
            return "400 Bad Request: " + e.getMessage();
        }
    }

    public String getOrder(int id) {
        System.out.println("[Controller] GET /orders/" + id);
        return service.getOrder(id)
            .map(o -> "200 OK: " + o)
            .orElse("404 Not Found");
    }
}

@Configuration
@ComponentScan
class FullFlowCfg {}

public class StereotypesFullFlow {
    public static void main(String[] args) {
        var ctx = new AnnotationConfigApplicationContext(FullFlowCfg.class);
        var ctrl = ctx.getBean(OrderController.class);
        System.out.println("---");
        System.out.println(ctrl.postOrder("Widget", 29.99));
        System.out.println("---");
        System.out.println(ctrl.getOrder(101));
        System.out.println("---");
        System.out.println(ctrl.postOrder("", 0.0));  // validation failure
        ctx.close();
    }
}
```

How to run: `java StereotypesFullFlow.java`

Each layer prints its own trace — Controller, Service, Repository — showing exactly how data transforms as it flows down and back up through the architecture.

## 6. Walkthrough

Execution order for the `postOrder("Widget", 29.99)` request:

1. **`[Controller] POST /orders`** — `OrderController.postOrder` receives item and amount. Calls `service.placeOrder(...)`.
2. **`[Service] placeOrder`** — validates item (non-blank) and amount (>0). Both pass. Calls `repo.save("Widget", 29.99)`.
3. **`[Repository] INSERT`** — assigns id=101, creates `Order(101, "Widget", 29.99)`, stores it. Returns order.
4. **`[Service]`** — receives the new order, logs it. Returns to controller.
5. **`[Controller]`** — formats `"201 Created: Order[id=101, ...]"`. Returns to `main`.

For the bad request (`postOrder("", 0.0)`):
- Service throws `IllegalArgumentException("item required")`.
- Controller catches it → `"400 Bad Request: item required"`.
- Repository is never called.

Expected output (first request block):
```
[Controller] POST /orders  body={item=Widget, amount=29.99}
[Service] placeOrder: item=Widget, amount=29.99
[Repository] INSERT orders(id=101, item=Widget, amount=29.99)
[Service] order placed: Order[id=101, item=Widget, amount=29.99]
201 Created: Order[id=101, item=Widget, amount=29.99]
```

## 7. Gotchas & takeaways

> `@Repository` exception translation only works when `PersistenceExceptionTranslationPostProcessor` is registered (it's auto-registered in Spring Boot but must be added manually in plain Spring). Without it, vendor exceptions propagate untranslated.

> `@Service` and `@Component` are functionally identical. `@Service` is purely a convention label — no additional Spring machinery is attached to it. Use `@Service` anyway — it communicates intent.

- All three inherit from `@Component` — component scanning treats them equally for bean registration.
- `@Controller` is for Spring MVC; for REST APIs that return JSON/XML directly use `@RestController` (`@Controller` + `@ResponseBody`).
- Stereotypes are the primary mechanism for layer-based AOP pointcuts — e.g., `@Transactional` on `@Service` methods is the standard Spring transaction pattern.
- Use `@Repository` on every data-access class — it documents the layer and enables exception translation consistently.

---
card: spring-framework
gi: 181
slug: aot-processed-bean-definitions
title: AOT-processed bean definitions
---

## 1. What it is

During `spring-boot:process-aot`, the AOT engine generates **`*__BeanDefinitions.java`** source files that reproduce your application's bean setup programmatically — without classpath scanning, annotation reading, or any runtime reflection.

For every `@Component`, `@Bean`, `@Configuration`, and related bean-registered class, Spring generates a companion class such as:

```java
// Generated: UserService__BeanDefinitions.java
public class UserService__BeanDefinitions {
    public static BeanDefinitionHolder getUserServiceBeanDefinition(
            RegisteredBean registeredBean) {
        var bd = new RootBeanDefinition(UserService.class);
        bd.setInstanceSupplier(UserService::new);  // no reflection
        return new BeanDefinitionHolder(bd, "userService");
    }
}
```

These generated classes are compiled and bundled into the application JAR. At runtime, a generated `ApplicationContextInitializer` calls them to register beans instead of scanning.

## 2. Why & when

- **Native image** — `native-image` cannot perform classpath scanning at runtime. Pre-generated bean definitions eliminate the need: beans are registered via direct Java calls instead of reflection.
- **Faster JVM startup** — skipping `@ComponentScan` (which reads class files) and condition evaluation at startup reduces startup time by 20–60% in large apps.
- **Build-time validation** — if a `@Configuration` class is structurally broken (missing constructor, circular dependency), the AOT engine catches it at build time.
- **Framework evolution** — framework developers can inspect generated sources to understand exactly what Spring wires for their application; it makes the implicit explicit.

## 3. Core concept

The generated output lives in `target/spring-aot/main/sources/` after running `spring-boot:process-aot`.

**Generated class naming:** `<OriginalClass>__BeanDefinitions` — double underscore distinguishes generated from user code.

**Generated `ApplicationContextInitializer`:** a top-level generated class (e.g., `com.example.App__ApplicationContextInitializer`) that implements `ApplicationContextInitializer<GenericApplicationContext>`. Its `initialize` method registers all beans by calling the `__BeanDefinitions` methods.

**Instance supplier vs reflection:** `bd.setInstanceSupplier(UserService::new)` is a method reference that the JVM resolves at link time — no `Class.forName()`, no `Constructor.newInstance()`, no reflection overhead.

**Condition evaluation:** `@ConditionalOnProperty` and `@ConditionalOnClass` are evaluated once at AOT build time. Beans whose conditions evaluate to `false` during `process-aot` are simply absent from the generated initialiser.

## 4. Diagram

<svg viewBox="0 0 700 200" xmlns="http://www.w3.org/2000/svg">
  <defs>
    <marker id="bda" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L6,3 L0,6 Z" fill="#6db33f"/></marker>
  </defs>

  <!-- Source → AOT → Generated -->
  <rect x="5" y="10" width="130" height="50" rx="5" fill="#1c2430" stroke="#8b949e" stroke-width="1.5"/>
  <text x="70" y="30" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">@Service</text>
  <text x="70" y="44" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">class UserService</text>
  <text x="70" y="55" fill="#8b949e" font-size="7" text-anchor="middle" font-family="sans-serif">(your code)</text>

  <line x1="137" y1="35" x2="157" y2="35" stroke="#6db33f" stroke-width="1.5" marker-end="url(#bda)"/>

  <rect x="160" y="10" width="150" height="50" rx="5" fill="#6db33f" opacity="0.2" stroke="#6db33f" stroke-width="1.5"/>
  <text x="235" y="28" fill="#6db33f" font-size="9" text-anchor="middle" font-family="sans-serif">spring-boot:process-aot</text>
  <text x="235" y="42" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">BeanRegistrationAot</text>
  <text x="235" y="53" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">Processor analyses</text>

  <line x1="312" y1="35" x2="332" y2="35" stroke="#6db33f" stroke-width="1.5" marker-end="url(#bda)"/>

  <rect x="335" y="5" width="200" height="110" rx="5" fill="#1c2430" stroke="#6db33f" stroke-width="2"/>
  <text x="435" y="23" fill="#6db33f" font-size="9" text-anchor="middle" font-family="sans-serif" font-weight="bold">Generated sources</text>
  <text x="355" y="40" fill="#8b949e" font-size="7" font-family="monospace">UserService__BeanDefinitions.java</text>
  <text x="355" y="53" fill="#e6edf3" font-size="7" font-family="monospace">  bd = new RootBeanDefinition(…);</text>
  <text x="355" y="64" fill="#e6edf3" font-size="7" font-family="monospace">  bd.setInstanceSupplier(</text>
  <text x="355" y="75" fill="#e6edf3" font-size="7" font-family="monospace">    UserService::new);</text>
  <text x="355" y="93" fill="#8b949e" font-size="7" font-family="monospace">App__AppCtxInitializer.java</text>
  <text x="355" y="106" fill="#e6edf3" font-size="7" font-family="monospace">  context.register(UserService…)</text>

  <line x1="537" y1="60" x2="557" y2="60" stroke="#6db33f" stroke-width="1.5" marker-end="url(#bda)"/>

  <rect x="560" y="30" width="130" height="60" rx="5" fill="#6db33f" opacity="0.3" stroke="#6db33f" stroke-width="1.5"/>
  <text x="625" y="50" fill="#6db33f" font-size="9" text-anchor="middle" font-family="sans-serif">Compiled into JAR</text>
  <text x="625" y="65" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">runtime: AOT initializer</text>
  <text x="625" y="78" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">called instead of scan</text>

  <!-- Generated files list -->
  <text x="350" y="140" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">target/spring-aot/main/sources/</text>
  <text x="350" y="153" fill="#e6edf3" font-size="8" text-anchor="middle" font-family="sans-serif">  UserService__BeanDefinitions.java</text>
  <text x="350" y="165" fill="#e6edf3" font-size="8" text-anchor="middle" font-family="sans-serif">  OrderService__BeanDefinitions.java</text>
  <text x="350" y="177" fill="#6db33f" font-size="8" text-anchor="middle" font-family="sans-serif">  com.example.App__ApplicationContextInitializer.java</text>
</svg>

Each bean gets a `__BeanDefinitions` companion; a top-level `__ApplicationContextInitializer` wires them all together without scanning.

## 5. Runnable example

The scenario is an **order management service** — growing from a standard scanned context, to AOT-style programmatic registration, to inspecting what a real AOT-processed app produces.

### Level 1 — Basic

A standard Spring context — the baseline before AOT. Shows what scanning does.

```java
// AotBeanDefsBasic.java
import org.springframework.context.annotation.*;
import org.springframework.stereotype.*;

@Service
class OrderService {
    public String placeOrder(String product, int qty) {
        return "Order: " + qty + "x " + product;
    }
}

@Service
class InventoryService {
    public boolean inStock(String product) { return true; }
}

@Configuration
@ComponentScan
class OrderConfig { }

public class AotBeanDefsBasic {
    public static void main(String[] args) {
        var ctx = new AnnotationConfigApplicationContext(OrderConfig.class);

        // At this point Spring did:
        // 1. Classpath scan to find @Service classes
        // 2. Read annotations via reflection to build BeanDefinitions
        // 3. Instantiate beans + inject dependencies

        var orders    = ctx.getBean(OrderService.class);
        var inventory = ctx.getBean(InventoryService.class);

        if (inventory.inStock("Laptop")) {
            System.out.println(orders.placeOrder("Laptop", 2));
        }

        // Show the raw BeanDefinition for OrderService
        var bd = ctx.getBeanFactory().getBeanDefinition("orderService");
        System.out.println("BeanDefinition class: " + bd.getClass().getSimpleName());
        System.out.println("Bean class:           " + bd.getBeanClassName());
        System.out.println("Scope:                " + bd.getScope());

        ctx.close();
    }
}
```

How to run: `java AotBeanDefsBasic.java`

`ctx.getBeanFactory().getBeanDefinition("orderService")` returns the `RootBeanDefinition` Spring built from the `@Service` annotation. In a normal JVM run this is created via classpath scanning and annotation reflection. AOT pre-generates equivalent code so this work is skipped at runtime.

### Level 2 — Intermediate

Manually replicate what AOT generates — programmatic `RootBeanDefinition` registration with supplier.

```java
// AotBeanDefsIntermediate.java
import org.springframework.beans.factory.config.*;
import org.springframework.beans.factory.support.*;
import org.springframework.context.support.*;

// Same service classes — no annotations needed; registered programmatically
class OrderServiceAot {
    public String placeOrder(String product, int qty) {
        return "Order: " + qty + "x " + product;
    }
}

class InventoryServiceAot {
    private boolean inStock = true;
    InventoryServiceAot() { this(true); }
    InventoryServiceAot(boolean inStock) { this.inStock = inStock; }
    public boolean inStock(String product) { return inStock; }
}

public class AotBeanDefsIntermediate {
    public static void main(String[] args) {
        // This code mirrors what AOT generates in *__BeanDefinitions.java
        var factory = new DefaultListableBeanFactory();

        // Register InventoryService — AOT-style
        var invBd = new RootBeanDefinition(InventoryServiceAot.class);
        invBd.setInstanceSupplier(InventoryServiceAot::new);  // method reference, no reflection
        invBd.setScope(BeanDefinition.SCOPE_SINGLETON);
        factory.registerBeanDefinition("inventoryService", invBd);

        // Register OrderService with explicit constructor dependency
        var ordBd = new RootBeanDefinition(OrderServiceAot.class);
        ordBd.setInstanceSupplier(OrderServiceAot::new);
        ordBd.setScope(BeanDefinition.SCOPE_SINGLETON);
        factory.registerBeanDefinition("orderService", ordBd);

        var ctx = new GenericApplicationContext(factory);
        ctx.refresh();

        var inv = factory.getBean(InventoryServiceAot.class);
        var ord = factory.getBean(OrderServiceAot.class);

        if (inv.inStock("Laptop")) {
            System.out.println(ord.placeOrder("Laptop", 2));
        }

        // Show the BeanDefinition — it now has an instanceSupplier
        var bd = factory.getMergedBeanDefinition("orderService");
        System.out.println("Has instance supplier: " +
            (bd instanceof RootBeanDefinition rbd && rbd.getInstanceSupplier() != null));

        ctx.close();
    }
}
```

How to run: `java AotBeanDefsIntermediate.java`

`setInstanceSupplier(OrderServiceAot::new)` stores a `InstanceSupplier<OrderServiceAot>` (effectively a `Supplier`) inside the `RootBeanDefinition`. When Spring creates the bean it calls `supplier.get()` directly — no `Class.forName`, no `Constructor.newInstance`, no annotation processing. This is exactly the pattern in AOT-generated `__BeanDefinitions` files.

### Level 3 — Advanced

A Spring Boot app; after running `process-aot`, the generated `__BeanDefinitions` files appear in `target/spring-aot/main/sources/`. This level shows what the generated output looks like and how to inspect it.

```java
// AotBeanDefsAdvanced.java — Spring Boot app; inspect generated output after process-aot
import org.springframework.boot.*;
import org.springframework.boot.autoconfigure.*;
import org.springframework.stereotype.*;
import org.springframework.web.bind.annotation.*;
import java.util.*;

record Item(String id, String name, double price) {}

@org.springframework.stereotype.Repository
class ItemRepository {
    private final List<Item> items = List.of(
        new Item("i1", "Laptop", 1200.0),
        new Item("i2", "Phone",   800.0)
    );
    public List<Item> findAll() { return items; }
    public Optional<Item> findById(String id) {
        return items.stream().filter(i -> i.id().equals(id)).findFirst();
    }
}

@Service
class ItemService {
    private final ItemRepository repo;
    ItemService(ItemRepository repo) { this.repo = repo; }
    public List<Item> listItems()          { return repo.findAll(); }
    public Optional<Item> getItem(String id) { return repo.findById(id); }
}

@RestController
@RequestMapping("/items")
class ItemController {
    private final ItemService svc;
    ItemController(ItemService svc) { this.svc = svc; }
    @GetMapping            public List<Item>     all()                   { return svc.listItems(); }
    @GetMapping("/{id}")   public Item           get(@PathVariable String id) {
        return svc.getItem(id).orElseThrow();
    }
}

@SpringBootApplication
public class AotBeanDefsAdvanced {
    public static void main(String[] args) {
        SpringApplication.run(AotBeanDefsAdvanced.class, args);
        // After: ./mvnw spring-boot:process-aot
        // Inspect: target/spring-aot/main/sources/
        //   ItemRepository__BeanDefinitions.java     ← supplier: ItemRepository::new
        //   ItemService__BeanDefinitions.java        ← supplier + constructor arg: ItemRepository
        //   ItemController__BeanDefinitions.java     ← supplier + constructor arg: ItemService
        //   AotBeanDefsAdvanced__ApplicationContextInitializer.java  ← registers all of the above
    }
}
```

How to run: `./mvnw spring-boot:run` (normal), or `./mvnw spring-boot:process-aot` to generate AOT sources

After `process-aot`, open `target/spring-aot/main/sources/` to read the generated files. `ItemService__BeanDefinitions` contains a `getInstanceSupplier()` method that returns a `InstanceSupplier` using a constructor reference that wires `ItemRepository` — no reflection at all. The `__ApplicationContextInitializer` calls all three `__BeanDefinitions` classes in dependency order.

## 6. Walkthrough

Tracing startup of `AotBeanDefsAdvanced` when running in AOT mode (`spring.aot.enabled=true`):

**Step 1 — JVM starts, `SpringApplication.run` called:**
- `SpringApplication` checks the classpath for a class named `<appPackage>.<AppClass>__ApplicationContextInitializer`.
- Finds `com.example.AotBeanDefsAdvanced__ApplicationContextInitializer`.
- Calls `initializer.initialize(context)` instead of `@ComponentScan`.

**Step 2 — `initialize(context)` runs (generated code):**

```java
// (generated — simplified)
public void initialize(GenericApplicationContext context) {
    // Register ItemRepository
    var repoSupplier = InstanceSupplier.of(ItemRepository::new);
    context.registerBeanDefinition("itemRepository",
        new RootBeanDefinition(ItemRepository.class, repoSupplier));

    // Register ItemService (depends on ItemRepository)
    var svcSupplier = InstanceSupplier.of(ctx ->
        new ItemService(ctx.getBean(ItemRepository.class)));
    context.registerBeanDefinition("itemService",
        new RootBeanDefinition(ItemService.class, svcSupplier));

    // Register ItemController
    var ctrlSupplier = InstanceSupplier.of(ctx ->
        new ItemController(ctx.getBean(ItemService.class)));
    context.registerBeanDefinition("itemController",
        new RootBeanDefinition(ItemController.class, ctrlSupplier));
}
```

**Step 3 — `context.refresh()` creates the beans:**
- `ItemRepository` constructed via supplier → `new ItemRepository()`.
- `ItemService` constructed via supplier → `new ItemService(itemRepository)`.
- `ItemController` constructed via supplier → `new ItemController(itemService)`.

No annotation reading. No classpath scanning. No `Class.forName`. The entire startup uses direct constructor calls.

**Step 4 — Request `GET /items`:**
```
→ ItemController.all()
→ svc.listItems() → repo.findAll()
← [{"id":"i1","name":"Laptop","price":1200.0}, {"id":"i2","name":"Phone","price":800.0}]
```

## 7. Gotchas & takeaways

> **Never edit `__BeanDefinitions` files directly.** They are regenerated on every `process-aot` run. Customise bean wiring by adjusting your application's `@Configuration` / `@Bean` classes or by implementing `BeanRegistrationAotProcessor` to intercept the generation.

> **`@Conditional` beans absent at AOT time are absent at native runtime.** The generated initialiser reflects the state at `process-aot` time. If `MY_FEATURE_FLAG=false` when AOT ran, the flagged bean is not in the generated initialiser — even if `MY_FEATURE_FLAG=true` at runtime. Re-run `process-aot` with the correct environment for each deployment profile.

- The generated files are in `target/spring-aot/main/sources/` — version-control your source code and build config, not these generated files.
- Inspect generated files to debug "bean not found" errors in native images: if a bean's `__BeanDefinitions` class is missing, the condition was evaluated to `false` at AOT time.
- `BeanRegistrationAotProcessor` is the SPI for framework authors to customise code generation for their beans (e.g., Spring Data generates repository implementations in generated sources).
- Generated bean definitions include autowiring metadata: `bd.setAutowiredConstructorArgumentTypes(...)` records injection point types so Spring can resolve dependencies without scanning at runtime.

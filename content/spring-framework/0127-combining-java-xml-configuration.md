---
card: spring-framework
gi: 127
slug: combining-java-xml-configuration
title: "Combining Java & XML configuration"
---

## 1. What it is

Spring supports two root-config entry points for mixing Java and XML configuration:

1. **Java-first** — start with `AnnotationConfigApplicationContext` and use `@ImportResource` to pull in XML files.
2. **XML-first** — start with `ClassPathXmlApplicationContext` and add `<context:annotation-config/>` plus `<bean class="YourJavaConfig"/>` to let the XML context process your `@Configuration` classes.

Both approaches produce a single unified `ApplicationContext` where beans from all sources can inject into each other.

## 2. Why & when

- **Incremental migration** — you're moving a large XML-based codebase to Java config. You adopt `@Configuration` module by module while keeping the rest in XML.
- **Ops-controlled config** — some teams prefer to keep infrastructure wiring in XML (datasource, JMS, transaction manager) while business logic lives in Java config.
- **Spring MVC** — the `DispatcherServlet` traditionally loads its own XML context (servlet context) that can reference beans from the root XML/Java context.
- **Testing** — a test class imports a Java config but loads additional beans from a test XML fixture.

## 3. Core concept

**Java-first path** (`AnnotationConfigApplicationContext`):

```java
@Configuration
@ImportResource("classpath:infrastructure.xml")
class AppConfig {
    @Bean Service service(DataSource ds) { return new Service(ds); }
    // ds comes from XML-defined <bean id="dataSource">
}
ApplicationContext ctx = new AnnotationConfigApplicationContext(AppConfig.class);
```

**XML-first path** (`ClassPathXmlApplicationContext`):

```xml
<!-- root-context.xml -->
<context:annotation-config/>
<bean class="com.example.AppConfig"/>   <!-- processes @Bean methods -->
<bean id="legacyRepo" class="com.example.LegacyRepo"/>
```

```java
ApplicationContext ctx = new ClassPathXmlApplicationContext("root-context.xml");
```

Both paths result in the same merged `BeanFactory`. The difference is which API you bootstrap with — which determines how you configure the servlet container or test framework.

## 4. Diagram

<svg viewBox="0 0 700 195" xmlns="http://www.w3.org/2000/svg">
  <!-- Java-first -->
  <rect x="10" y="30" width="195" height="70" rx="8" fill="#1c2430" stroke="#6db33f" stroke-width="2"/>
  <text x="107" y="53" fill="#6db33f" font-size="12" text-anchor="middle" font-family="sans-serif">Java-first</text>
  <text x="107" y="70" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">AnnotationConfigApp...</text>
  <text x="107" y="87" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">@ImportResource(xml)</text>

  <!-- XML-first -->
  <rect x="10" y="115" width="195" height="70" rx="8" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="107" y="138" fill="#79c0ff" font-size="12" text-anchor="middle" font-family="sans-serif">XML-first</text>
  <text x="107" y="155" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">ClassPathXmlApp...</text>
  <text x="107" y="172" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">&lt;bean class="JavaConfig"/&gt;</text>

  <!-- Unified context -->
  <rect x="310" y="68" width="185" height="65" rx="8" fill="#1c2430" stroke="#8b949e" stroke-width="1.5"/>
  <text x="402" y="92" fill="#e6edf3" font-size="12" text-anchor="middle" font-family="sans-serif">Unified Context</text>
  <text x="402" y="110" fill="#6db33f" font-size="10" text-anchor="middle" font-family="sans-serif">Java + XML beans merged</text>
  <text x="402" y="125" fill="#8b949e" font-size="9"  text-anchor="middle" font-family="sans-serif">cross-injection works</text>

  <!-- Output -->
  <rect x="580" y="78" width="110" height="45" rx="7" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="635" y="98" fill="#6db33f" font-size="11" text-anchor="middle" font-family="sans-serif">App runs</text>
  <text x="635" y="114" fill="#8b949e" font-size="9"  text-anchor="middle" font-family="sans-serif">one registry</text>

  <line x1="207" y1="65" x2="307" y2="100" stroke="#6db33f" stroke-width="2" marker-end="url(#a127)"/>
  <line x1="207" y1="150" x2="307" y2="120" stroke="#79c0ff" stroke-width="1.5" marker-end="url(#b127)"/>
  <line x1="497" y1="100" x2="577" y2="100" stroke="#8b949e" stroke-width="1.5" marker-end="url(#c127)"/>
  <defs>
    <marker id="a127" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#6db33f"/></marker>
    <marker id="b127" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#79c0ff"/></marker>
    <marker id="c127" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#8b949e"/></marker>
  </defs>
  <text x="350" y="187" fill="#8b949e" font-size="11" text-anchor="middle" font-family="sans-serif">Both paths produce one BeanFactory — choose entry point based on your bootstrap mechanism</text>
</svg>

Java-first and XML-first are entry-point choices; the resulting context is the same merged registry.

## 5. Runnable example

### Level 1 — Basic

Java-first: `AnnotationConfigApplicationContext` imports an XML file.

```java
// CombineJavaFirst.java
import org.springframework.beans.factory.annotation.*;
import org.springframework.context.annotation.*;
import java.nio.file.*;

class DbPool {
    private final String url;
    public DbPool(String url) { this.url = url; System.out.println("[DbPool] " + url); }
    public String borrow() { return "conn@" + url; }
}

class UserService {
    @Autowired DbPool pool;  // from XML
    public String getUser(int id) { return "User#" + id + " via " + pool.borrow(); }
}

@Configuration
@ImportResource("classpath:combine-infra.xml")
class AppConfig {
    @Bean public UserService userService() { return new UserService(); }
}

public class CombineJavaFirst {
    public static void main(String[] args) throws Exception {
        Files.writeString(Path.of("combine-infra.xml"), """
            <?xml version="1.0" encoding="UTF-8"?>
            <beans xmlns="http://www.springframework.org/schema/beans"
                   xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
                   xsi:schemaLocation="http://www.springframework.org/schema/beans
                   https://www.springframework.org/schema/beans/spring-beans.xsd">
                <bean id="dbPool" class="DbPool">
                    <constructor-arg value="jdbc:h2:mem:test"/>
                </bean>
            </beans>
            """);

        var ctx = new AnnotationConfigApplicationContext(AppConfig.class);
        System.out.println(ctx.getBean(UserService.class).getUser(1));
        System.out.println(ctx.getBean(UserService.class).getUser(2));
        ctx.close();
        Files.deleteIfExists(Path.of("combine-infra.xml"));
    }
}
```

How to run: `java CombineJavaFirst.java`

`AppConfig` is the Java-config entry point. `@ImportResource` loads `combine-infra.xml` which defines `dbPool`. `UserService` (Java bean) injects `dbPool` (XML bean) seamlessly.

### Level 2 — Intermediate

XML-first: `ClassPathXmlApplicationContext` loads a `@Configuration` class and XML-defined beans together.

```java
// CombineXmlFirst.java
import org.springframework.beans.factory.annotation.*;
import org.springframework.context.*;
import org.springframework.context.annotation.*;
import org.springframework.context.support.ClassPathXmlApplicationContext;
import java.nio.file.*;

// Java config — business layer
@Configuration
class BusinessConfig {
    @Bean
    public OrderService orderService(PaymentService pay, InventoryService inv) {
        System.out.println("[Java] creating OrderService");
        return new OrderService(pay, inv);
    }
}

class PaymentService {
    PaymentService() { System.out.println("[XML] PaymentService ready"); }
    public String charge(double amount) { return "charged $" + amount; }
}

class InventoryService {
    InventoryService() { System.out.println("[XML] InventoryService ready"); }
    public boolean reserve(int qty) { return qty <= 100; }
}

class OrderService {
    final PaymentService pay; final InventoryService inv;
    OrderService(PaymentService p, InventoryService i) { this.pay = p; this.inv = i; }
    public void place(int qty, double price) {
        if (inv.reserve(qty)) System.out.println("Order placed: " + pay.charge(price));
        else System.out.println("Inventory insufficient");
    }
}

public class CombineXmlFirst {
    public static void main(String[] args) throws Exception {
        Files.writeString(Path.of("combine-root.xml"), """
            <?xml version="1.0" encoding="UTF-8"?>
            <beans xmlns="http://www.springframework.org/schema/beans"
                   xmlns:context="http://www.springframework.org/schema/context"
                   xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
                   xsi:schemaLocation="
                     http://www.springframework.org/schema/beans
                     https://www.springframework.org/schema/beans/spring-beans.xsd
                     http://www.springframework.org/schema/context
                     https://www.springframework.org/schema/context/spring-context.xsd">
                <!-- Activate annotation processing -->
                <context:annotation-config/>
                <!-- Java config class registered as a bean -->
                <bean class="BusinessConfig"/>
                <!-- XML-defined infrastructure beans -->
                <bean id="paymentService" class="PaymentService"/>
                <bean id="inventoryService" class="InventoryService"/>
            </beans>
            """);

        ApplicationContext ctx = new ClassPathXmlApplicationContext("combine-root.xml");
        ctx.getBean(OrderService.class).place(5, 199.99);
        System.out.println("Beans from XML context: " + ctx.getBeanDefinitionCount());
        ((ClassPathXmlApplicationContext) ctx).close();
        Files.deleteIfExists(Path.of("combine-root.xml"));
    }
}
```

How to run: `java CombineXmlFirst.java`

`ClassPathXmlApplicationContext` loads the XML which includes `<bean class="BusinessConfig"/>`. Spring processes `BusinessConfig` as a `@Configuration` class, registering `orderService` which injects the XML-defined `paymentService` and `inventoryService`.

### Level 3 — Advanced

A layered setup: root XML context (infrastructure) + Java child context (web/business layer) that inherits from the root — simulating a Spring MVC parent-child context hierarchy.

```java
// CombineHierarchy.java
import org.springframework.beans.factory.annotation.*;
import org.springframework.context.*;
import org.springframework.context.annotation.*;
import org.springframework.context.support.ClassPathXmlApplicationContext;
import org.springframework.context.support.GenericApplicationContext;
import java.nio.file.*;

// --- Root context: infrastructure (XML-based) ---
class DataSource {
    DataSource() { System.out.println("[Root] DataSource created"); }
    public String connect() { return "jdbc:postgresql://prod/shopdb"; }
}

class TransactionManager {
    @Autowired DataSource ds;
    TransactionManager() { System.out.println("[Root] TxManager created"); }
    public String begin() { return "tx@" + ds.connect(); }
}

// --- Child context: business layer (Java-based) ---
class ProductService {
    @Autowired DataSource ds;            // parent bean — visible in child
    @Autowired TransactionManager txMgr; // parent bean

    ProductService() { System.out.println("[Child] ProductService created"); }

    public void save(String product) {
        System.out.println("[Save] " + product + " in " + txMgr.begin());
    }
}

@Configuration
class BusinessLayer {
    @Bean public ProductService productService() { return new ProductService(); }
}

public class CombineHierarchy {
    public static void main(String[] args) throws Exception {
        Files.writeString(Path.of("combine-root-ctx.xml"), """
            <?xml version="1.0" encoding="UTF-8"?>
            <beans xmlns="http://www.springframework.org/schema/beans"
                   xmlns:context="http://www.springframework.org/schema/context"
                   xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
                   xsi:schemaLocation="
                     http://www.springframework.org/schema/beans
                     https://www.springframework.org/schema/beans/spring-beans.xsd
                     http://www.springframework.org/schema/context
                     https://www.springframework.org/schema/context/spring-context.xsd">
                <context:annotation-config/>
                <bean id="dataSource"        class="DataSource"/>
                <bean id="transactionManager" class="TransactionManager"/>
            </beans>
            """);

        // Root context (parent)
        ApplicationContext parent = new ClassPathXmlApplicationContext("combine-root-ctx.xml");

        // Child context (Java config) with parent
        AnnotationConfigApplicationContext child = new AnnotationConfigApplicationContext();
        child.setParent(parent);
        child.register(BusinessLayer.class);
        child.refresh();

        // Child can see parent beans
        System.out.println("\n=== Using child context ===");
        child.getBean(ProductService.class).save("Widget-Pro");
        child.getBean(ProductService.class).save("Gadget-X");

        System.out.println("\n=== Parent does NOT see child beans ===");
        System.out.println("productService in parent: " + parent.containsBean("productService"));
        System.out.println("productService in child:  " + child.containsBean("productService"));

        child.close();
        ((ClassPathXmlApplicationContext) parent).close();
        Files.deleteIfExists(Path.of("combine-root-ctx.xml"));
    }
}
```

How to run: `java CombineHierarchy.java`

The parent (XML) context holds `dataSource` and `transactionManager`. The child (Java) context holds `productService` and can inject from the parent. Parent beans are visible in child; child beans are NOT visible in parent — this is the standard Spring parent-child context model.

## 6. Walkthrough

Execution for Level 3:

1. **`ClassPathXmlApplicationContext("combine-root-ctx.xml")` created** — processes XML, creates `dataSource` and `transactionManager`.
2. **`AnnotationConfigApplicationContext` created with parent** — `setParent(parent)` links the two contexts.
3. **`register(BusinessLayer.class)` + `refresh()`** — processes `BusinessLayer`, creates `productService`.
4. **`productService` injected** — `@Autowired DataSource ds` resolves from parent context. `@Autowired TransactionManager txMgr` resolves from parent.
5. **`productService.save("Widget-Pro")`** → `txMgr.begin()` → `"tx@jdbc:postgresql://prod/shopdb"`. Prints full save message.
6. **Parent containsBean check** — parent has no `productService` (child beans not visible upward).

Expected output:
```
[Root] DataSource created
[Root] TxManager created
[Child] ProductService created

=== Using child context ===
[Save] Widget-Pro in tx@jdbc:postgresql://prod/shopdb
[Save] Gadget-X in tx@jdbc:postgresql://prod/shopdb

=== Parent does NOT see child beans ===
productService in parent: false
productService in child:  true
```

## 7. Gotchas & takeaways

> In an XML-first setup, `<context:annotation-config/>` activates `@Autowired`, `@Value`, and `@PostConstruct` processing but **does not** scan for `@Component` classes. You still need `<context:component-scan>` to detect `@Service`/`@Repository`/`@Component` classes, or explicitly `<bean class="YourConfig"/>`.

> Parent-child context hierarchies introduce a subtle trap: `@Transactional` and AOP proxies in the child are NOT applied to beans in the parent. Infrastructure beans like the `PlatformTransactionManager` must be in the correct context (usually the root) for transactions to work.

- Prefer Java-first (`AnnotationConfigApplicationContext` + `@ImportResource`) for new projects — it's easier to reason about.
- Use XML-first (`ClassPathXmlApplicationContext` + `<bean class="JavaConfig">`) when an existing XML bootstrap mechanism (like a servlet container web.xml) is the entry point.
- Mixed-source beans inject normally: `ref="javaBean"` in XML and `@Autowired` in Java both work against the merged registry.
- Spring Boot replaces this pattern with `application.properties` and auto-configuration — if you're on Boot, you rarely need mixed Java/XML config.

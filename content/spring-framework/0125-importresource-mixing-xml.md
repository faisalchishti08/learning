---
card: spring-framework
gi: 125
slug: importresource-mixing-xml
title: "@ImportResource (mixing XML)"
---

## 1. What it is

`@ImportResource` is a Spring annotation that loads one or more XML (or Groovy) Spring configuration files into the same application context as your Java-based `@Configuration` classes. It bridges the gap between legacy XML configuration and modern Java config — you can adopt `@Configuration` incrementally without rewriting all existing XML at once.

```java
@Configuration
@ImportResource("classpath:legacy-beans.xml")
class AppConfig {
    // Java @Bean methods here alongside beans from XML
}
```

All beans from the XML file and from `@Bean` methods share the same `BeanFactory` — they can inject into each other freely.

## 2. Why & when

- **Migration** — your app has an existing XML config. You start adding `@Configuration` and want to keep the XML working while gradually porting beans.
- **Third-party XML** — a library ships an XML configuration file you must include.
- **Team split** — some teams prefer XML, others Java config; both participate in the same context.
- **Testing** — a test needs to override one XML bean with a Java-config bean, or vice versa.

## 3. Core concept

`@ImportResource` accepts:

- A single string: `@ImportResource("classpath:beans.xml")`
- An array: `@ImportResource({"classpath:data.xml", "classpath:security.xml"})`
- `locations` alias: `@ImportResource(locations = "classpath:beans.xml")`
- `reader` attribute to specify a custom `BeanDefinitionReader` (default: auto-detected from extension — `.xml` → `XmlBeanDefinitionReader`, `.groovy` → `GroovyBeanDefinitionReader`).

Resource path prefixes:
- `classpath:` — searches the classpath.
- `file:` — absolute file system path.
- `classpath*:` — searches all classpath locations (useful for modular apps).

The XML beans and Java beans merge into a single `DefaultListableBeanFactory`. Name conflicts follow the standard rule: later registrations override earlier ones (last-write-wins in a single context).

## 4. Diagram

<svg viewBox="0 0 700 195" xmlns="http://www.w3.org/2000/svg">
  <!-- Java config -->
  <rect x="10" y="50" width="175" height="100" rx="8" fill="#1c2430" stroke="#6db33f" stroke-width="2"/>
  <text x="97" y="73" fill="#6db33f" font-size="12" text-anchor="middle" font-family="sans-serif">@Configuration</text>
  <text x="97" y="92" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">@ImportResource(xml)</text>
  <text x="97" y="110" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">@Bean javaBean()</text>
  <text x="97" y="128" fill="#8b949e" font-size="9"  text-anchor="middle" font-family="sans-serif">can @Autowired xmlBean</text>
  <text x="97" y="143" fill="#8b949e" font-size="9"  text-anchor="middle" font-family="sans-serif">and vice versa</text>

  <!-- XML file -->
  <rect x="10" y="165" width="175" height="25" rx="6" fill="#1c2430" stroke="#8b949e" stroke-width="1.5"/>
  <text x="97" y="182" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">legacy-beans.xml</text>

  <!-- Arrow up -->
  <line x1="97" y1="163" x2="97" y2="153" stroke="#8b949e" stroke-width="1.5" marker-end="url(#c125)"/>

  <!-- Merge -->
  <rect x="280" y="75" width="165" height="50" rx="8" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="362" y="97" fill="#79c0ff" font-size="12" text-anchor="middle" font-family="sans-serif">Merged Factory</text>
  <text x="362" y="113" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">XML + Java beans</text>

  <!-- Output -->
  <rect x="535" y="75" width="155" height="50" rx="8" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="612" y="97" fill="#6db33f" font-size="12" text-anchor="middle" font-family="sans-serif">Application</text>
  <text x="612" y="113" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">inject across sources</text>

  <line x1="187" y1="100" x2="277" y2="100" stroke="#6db33f" stroke-width="2" marker-end="url(#a125)"/>
  <line x1="447" y1="100" x2="532" y2="100" stroke="#79c0ff" stroke-width="2" marker-end="url(#b125)"/>
  <defs>
    <marker id="a125" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#6db33f"/></marker>
    <marker id="b125" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#79c0ff"/></marker>
    <marker id="c125" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#8b949e"/></marker>
  </defs>
  <text x="350" y="185" fill="#8b949e" font-size="11" text-anchor="middle" font-family="sans-serif">@ImportResource merges XML bean definitions into the Java-config context</text>
</svg>

XML and Java beans live in the same context — cross-injection works both ways.

## 5. Runnable example

### Level 1 — Basic

Load a single XML file alongside a `@Configuration` class; inject an XML bean into a Java bean.

```java
// ImportResourceBasic.java
import org.springframework.beans.factory.annotation.*;
import org.springframework.context.annotation.*;
import java.io.*;
import java.nio.file.*;

class LegacyService {
    private final String mode;
    public LegacyService(String mode) { this.mode = mode; }
    public String status() { return "[Legacy:" + mode + "] running"; }
}

class NewService {
    @Autowired private LegacyService legacy;  // injected from XML
    public String call() { return "[New] delegates to " + legacy.status(); }
}

@Configuration
@ImportResource("classpath:legacy-config.xml")
class AppConfig {
    @Bean public NewService newService() { return new NewService(); }
}

public class ImportResourceBasic {
    public static void main(String[] args) throws Exception {
        // Write the XML to a temp location on the classpath root
        String xml = """
            <?xml version="1.0" encoding="UTF-8"?>
            <beans xmlns="http://www.springframework.org/schema/beans"
                   xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
                   xsi:schemaLocation="http://www.springframework.org/schema/beans
                   https://www.springframework.org/schema/beans/spring-beans.xsd">
                <bean id="legacyService" class="LegacyService">
                    <constructor-arg value="compatibility"/>
                </bean>
            </beans>
            """;
        // Write to a directory on classpath (current dir for this demo)
        Files.writeString(Path.of("legacy-config.xml"), xml);

        var ctx = new AnnotationConfigApplicationContext(AppConfig.class);
        System.out.println(ctx.getBean(LegacyService.class).status());
        System.out.println(ctx.getBean(NewService.class).call());
        ctx.close();
        Files.deleteIfExists(Path.of("legacy-config.xml"));
    }
}
```

How to run: `java ImportResourceBasic.java`

The XML file defines `legacyService` which is injected into `NewService` defined in `AppConfig`. Both live in the same context — `@Autowired` works across the source boundary.

### Level 2 — Intermediate

Multiple XML files plus Java config; XML bean injects a Java-defined bean by name.

```java
// ImportResourceMultiple.java
import org.springframework.beans.factory.annotation.*;
import org.springframework.context.annotation.*;
import java.nio.file.*;

// --- Java-defined infrastructure ---
class ConnectionPool {
    private final int size;
    public ConnectionPool(int size) { this.size = size; }
    public String borrow() { return "conn[pool-" + size + "]"; }
}

// --- Beans that will come from XML ---
class UserRepository {
    private ConnectionPool pool;  // injected from Java config via XML ref
    public void setPool(ConnectionPool p) { this.pool = p; }
    public String find(int id) { return "[UserRepo via " + pool.borrow() + "] user#" + id; }
}

class OrderRepository {
    private ConnectionPool pool;
    public void setPool(ConnectionPool p) { this.pool = p; }
    public String find(int id) { return "[OrderRepo via " + pool.borrow() + "] order#" + id; }
}

// --- Java service that uses XML-defined repos ---
class ShopService {
    @Autowired private UserRepository userRepo;
    @Autowired private OrderRepository orderRepo;
    public void run(int uid, int oid) {
        System.out.println(userRepo.find(uid));
        System.out.println(orderRepo.find(oid));
    }
}

@Configuration
@ImportResource({"classpath:repos.xml"})
class ShopConfig {
    @Bean public ConnectionPool connectionPool() { return new ConnectionPool(10); }
    @Bean public ShopService shopService() { return new ShopService(); }
}

public class ImportResourceMultiple {
    public static void main(String[] args) throws Exception {
        String reposXml = """
            <?xml version="1.0" encoding="UTF-8"?>
            <beans xmlns="http://www.springframework.org/schema/beans"
                   xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
                   xsi:schemaLocation="http://www.springframework.org/schema/beans
                   https://www.springframework.org/schema/beans/spring-beans.xsd">
                <bean id="userRepository" class="UserRepository">
                    <property name="pool" ref="connectionPool"/>
                </bean>
                <bean id="orderRepository" class="OrderRepository">
                    <property name="pool" ref="connectionPool"/>
                </bean>
            </beans>
            """;
        Files.writeString(Path.of("repos.xml"), reposXml);

        var ctx = new AnnotationConfigApplicationContext(ShopConfig.class);
        ctx.getBean(ShopService.class).run(1, 42);

        System.out.println("connectionPool from Java: " +
            ctx.getBean(ConnectionPool.class).borrow());
        ctx.close();
        Files.deleteIfExists(Path.of("repos.xml"));
    }
}
```

How to run: `java ImportResourceMultiple.java`

The XML uses `ref="connectionPool"` to reference the `ConnectionPool` bean defined in `ShopConfig`. Cross-injection between XML and Java config works seamlessly — Spring resolves `ref` lookups against the merged factory.

### Level 3 — Advanced

Override an XML bean with a Java config bean by registering under the same name (Java wins as it's processed later), demonstrating the migration pattern.

```java
// ImportResourceOverride.java
import org.springframework.beans.factory.annotation.*;
import org.springframework.context.annotation.*;
import java.nio.file.*;

interface PaymentGateway { String charge(double amount); }

class LegacyPaymentGateway implements PaymentGateway {
    public String charge(double amount) { return "[LEGACY] charged $" + amount; }
}

class ModernPaymentGateway implements PaymentGateway {
    public String charge(double amount) { return "[MODERN] charged $" + amount + " via Stripe"; }
}

class OrderService {
    @Autowired PaymentGateway gateway;
    public void place(int id, double amount) {
        System.out.println("[Order#" + id + "] " + gateway.charge(amount));
    }
}

// Migration step: still import the XML, but override the gateway bean in Java
@Configuration
@ImportResource("classpath:payment-legacy.xml")
class MigratedConfig {
    // This @Bean registration overrides the XML "paymentGateway" bean
    @Bean
    public PaymentGateway paymentGateway() {
        System.out.println("[Config] Using ModernPaymentGateway (Java override)");
        return new ModernPaymentGateway();
    }

    @Bean public OrderService orderService() { return new OrderService(); }
}

public class ImportResourceOverride {
    public static void main(String[] args) throws Exception {
        String xml = """
            <?xml version="1.0" encoding="UTF-8"?>
            <beans xmlns="http://www.springframework.org/schema/beans"
                   xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
                   xsi:schemaLocation="http://www.springframework.org/schema/beans
                   https://www.springframework.org/schema/beans/spring-beans.xsd">
                <!-- This bean will be overridden by the Java config @Bean of same name -->
                <bean id="paymentGateway" class="LegacyPaymentGateway"/>
            </beans>
            """;
        Files.writeString(Path.of("payment-legacy.xml"), xml);

        var ctx = new AnnotationConfigApplicationContext(MigratedConfig.class);
        ctx.getBean(OrderService.class).place(1, 99.99);
        ctx.getBean(OrderService.class).place(2, 149.50);

        // Verify ModernPaymentGateway won
        System.out.println("\nActual gateway: " +
            ctx.getBean(PaymentGateway.class).getClass().getSimpleName());
        ctx.close();
        Files.deleteIfExists(Path.of("payment-legacy.xml"));
    }
}
```

How to run: `java ImportResourceOverride.java`

The XML registers `paymentGateway` as `LegacyPaymentGateway`. The Java `@Bean` method of the same name registers `ModernPaymentGateway` and overrides the XML definition. `OrderService` receives the modern implementation — this is how you incrementally migrate XML beans to Java config.

## 6. Walkthrough

Execution for Level 3:

1. **`AnnotationConfigApplicationContext(MigratedConfig.class)` created** — `ConfigurationClassPostProcessor` processes `MigratedConfig`.
2. **`@ImportResource("classpath:payment-legacy.xml")` processed** — `XmlBeanDefinitionReader` reads the XML and registers `paymentGateway` → `LegacyPaymentGateway`.
3. **`MigratedConfig.paymentGateway()` `@Bean` processed** — registers `paymentGateway` → `ModernPaymentGateway`. This overrides the XML registration (Java config processed after XML import).
4. **`MigratedConfig.orderService()` `@Bean` processed** — registers `OrderService`.
5. **`orderService` instantiated** — `@Autowired PaymentGateway` resolves to `ModernPaymentGateway`.
6. **`place(1, 99.99)`** → `[Order#1] [MODERN] charged $99.99 via Stripe`.

Expected output:
```
[Config] Using ModernPaymentGateway (Java override)
[Order#1] [MODERN] charged $99.99 via Stripe
[Order#2] [MODERN] charged $149.5 via Stripe

Actual gateway: ModernPaymentGateway
```

## 7. Gotchas & takeaways

> The override order depends on processing order. `@ImportResource` XML is loaded before the `@Bean` methods of the same `@Configuration` class. So a Java `@Bean` with the same name as an XML bean **wins** — it registers last and overrides the XML definition.

> If you import XML that itself imports more XML (`<import resource="...">`), Spring follows the chain. The entire XML import tree is resolved under the same factory — beans in nested XML can inject beans from Java config.

- Resource paths use Spring's `ResourceLoader` — `classpath:`, `file:`, `classpath*:` all work.
- Beans from XML and Java can cross-inject: XML uses `ref="javaBeanName"`, Java uses `@Autowired` or `@Qualifier("xmlBeanName")`.
- In Spring Boot, `@SpringBootApplication` does not scan XML by default. You must add `@ImportResource` explicitly to include XML files.
- Use `classpath*:` to pick up XML files spread across multiple JARs (e.g., modular projects where each JAR ships a `beans.xml`).

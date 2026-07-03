---
card: spring-framework
gi: 124
slug: importbeandefinitionregistrar
title: "ImportBeanDefinitionRegistrar"
---

## 1. What it is

`ImportBeanDefinitionRegistrar` is an interface that lets you register `BeanDefinition`s programmatically when an `@Import` is processed. It is a lower-level sibling to `ImportSelector`: instead of returning class names for Spring to process, you register `BeanDefinition` objects directly into the `BeanDefinitionRegistry`.

```java
class MyRegistrar implements ImportBeanDefinitionRegistrar {
    @Override
    public void registerBeanDefinitions(
            AnnotationMetadata importingClassMetadata,
            BeanDefinitionRegistry registry) {
        // register any BeanDefinition directly
    }
}
```

Spring calls `registerBeanDefinitions()` during configuration class processing — before instantiation.

## 2. Why & when

`ImportBeanDefinitionRegistrar` is the right tool when:

- You need to register beans **programmatically** based on annotation attributes — e.g., registering proxy beans or dynamic subclass beans.
- You are implementing a framework feature that introspects the importing class (like scanning specific annotations on its fields or methods) and registers infrastructure beans accordingly.
- The beans you need to register cannot be expressed as `@Bean` methods or `ImportSelector` class names — e.g., dynamically named beans, beans with custom scopes, or beans created from bytecode generation.

Examples in the Spring ecosystem: `@MapperScan` in MyBatis-Spring, `@EnableFeignClients` in Spring Cloud, `@EnableJpaRepositories` in Spring Data — all use `ImportBeanDefinitionRegistrar` to scan for annotated interfaces and register proxy beans.

## 3. Core concept

The two parameters to `registerBeanDefinitions`:

- **`AnnotationMetadata importingClassMetadata`** — metadata of the `@Configuration` class that has `@Import(YourRegistrar.class)`. Use it to read annotation attributes (e.g., `@EnableRepos(basePackages="com.example")`).
- **`BeanDefinitionRegistry registry`** — the bean definition store. Call `registry.registerBeanDefinition(name, definition)` to add beans.

Typical pattern:

```java
class ClientRegistrar implements ImportBeanDefinitionRegistrar {
    @Override
    public void registerBeanDefinitions(AnnotationMetadata meta,
                                        BeanDefinitionRegistry registry) {
        // Read annotation attributes
        AnnotationAttributes attrs = AnnotationAttributes.fromMap(
            meta.getAnnotationAttributes(EnableClients.class.getName()));

        // Build a BeanDefinition
        BeanDefinitionBuilder builder = BeanDefinitionBuilder
            .genericBeanDefinition(ClientFactoryBean.class)
            .addConstructorArgValue(attrs.getString("url"));

        // Register it
        registry.registerBeanDefinition("myClient", builder.getBeanDefinition());
    }
}
```

`BeanDefinitionBuilder` is the fluent API for building `BeanDefinition`s without manually constructing `RootBeanDefinition` or `GenericBeanDefinition`.

## 4. Diagram

<svg viewBox="0 0 700 200" xmlns="http://www.w3.org/2000/svg">
  <!-- @Import trigger -->
  <rect x="10" y="55" width="165" height="90" rx="8" fill="#1c2430" stroke="#6db33f" stroke-width="2"/>
  <text x="92" y="78" fill="#6db33f" font-size="12" text-anchor="middle" font-family="sans-serif">@Import</text>
  <text x="92" y="95" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">IBDRegistrar.class</text>
  <text x="92" y="115" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">AnnotationMetadata</text>
  <text x="92" y="130" fill="#8b949e" font-size="9"  text-anchor="middle" font-family="sans-serif">of importing class</text>
  <text x="92" y="143" fill="#8b949e" font-size="9"  text-anchor="middle" font-family="sans-serif">+ annotation attrs</text>

  <!-- Registrar -->
  <rect x="263" y="55" width="185" height="90" rx="8" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="355" y="78" fill="#79c0ff" font-size="12" text-anchor="middle" font-family="sans-serif">Registrar</text>
  <text x="355" y="97" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">registerBeanDefinitions()</text>
  <text x="355" y="115" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">BeanDefinitionBuilder</text>
  <text x="355" y="132" fill="#8b949e" font-size="9"  text-anchor="middle" font-family="sans-serif">registry.register(name, bd)</text>

  <!-- Registry -->
  <rect x="540" y="55" width="150" height="90" rx="8" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="615" y="78" fill="#6db33f" font-size="12" text-anchor="middle" font-family="sans-serif">BeanRegistry</text>
  <text x="615" y="98" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">dynamicBean1 → BD</text>
  <text x="615" y="115" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">dynamicBean2 → BD</text>
  <text x="615" y="132" fill="#8b949e" font-size="9"  text-anchor="middle" font-family="sans-serif">(custom BDs)</text>

  <line x1="177" y1="100" x2="260" y2="100" stroke="#6db33f" stroke-width="2" marker-end="url(#a124)"/>
  <line x1="450" y1="100" x2="537" y2="100" stroke="#79c0ff" stroke-width="2" marker-end="url(#b124)"/>
  <defs>
    <marker id="a124" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#6db33f"/></marker>
    <marker id="b124" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#79c0ff"/></marker>
  </defs>
  <text x="350" y="185" fill="#8b949e" font-size="11" text-anchor="middle" font-family="sans-serif">Registrar writes BeanDefinitions directly — more control than ImportSelector</text>
</svg>

`ImportBeanDefinitionRegistrar` writes `BeanDefinition`s directly into the registry, bypassing the usual `@Bean` / component-scan pipeline.

## 5. Runnable example

### Level 1 — Basic

Register a bean dynamically — simulating what a library might do when you use an `@Enable*` annotation.

```java
// RegistrarBasic.java
import org.springframework.beans.factory.support.*;
import org.springframework.context.annotation.*;
import org.springframework.core.type.AnnotationMetadata;
import java.lang.annotation.*;

// The bean type the registrar creates
class AuditService {
    private final String target;
    AuditService(String target) { this.target = target; }
    public void record(String action) {
        System.out.println("[Audit→" + target + "] " + action);
    }
}

// The registrar
class AuditRegistrar implements ImportBeanDefinitionRegistrar {
    @Override
    public void registerBeanDefinitions(AnnotationMetadata meta,
                                        BeanDefinitionRegistry registry) {
        AnnotationAttributes attrs = AnnotationAttributes.fromMap(
            meta.getAnnotationAttributes(EnableAudit.class.getName()));
        String target = attrs == null ? "default" : attrs.getString("target");
        System.out.println("[Registrar] registering AuditService for target=" + target);

        var bd = BeanDefinitionBuilder
            .genericBeanDefinition(AuditService.class)
            .addConstructorArgValue(target)
            .getBeanDefinition();

        registry.registerBeanDefinition("auditService", bd);
    }
}

// Custom enable annotation
@Target(ElementType.TYPE) @Retention(RetentionPolicy.RUNTIME)
@Import(AuditRegistrar.class)
@interface EnableAudit { String target() default "general"; }

@Configuration
@EnableAudit(target = "orders")
class AppCfg {}

public class RegistrarBasic {
    public static void main(String[] args) {
        var ctx = new AnnotationConfigApplicationContext(AppCfg.class);
        ctx.getBean(AuditService.class).record("order placed");
        ctx.getBean(AuditService.class).record("payment received");
        ctx.close();
    }
}
```

How to run: `java RegistrarBasic.java`

`AuditRegistrar` reads `target="orders"` from `@EnableAudit` and registers an `AuditService` bean with that constructor argument — no `@Bean` method required.

### Level 2 — Intermediate

Register multiple beans from a list of names supplied in the annotation — simulating dynamic client registration.

```java
// RegistrarMultiple.java
import org.springframework.beans.factory.annotation.*;
import org.springframework.beans.factory.support.*;
import org.springframework.context.annotation.*;
import org.springframework.core.type.AnnotationMetadata;
import java.lang.annotation.*;
import java.util.*;

// Generic REST client
class RestClient {
    private final String baseUrl;
    RestClient(String url) {
        this.baseUrl = url;
        System.out.println("[RestClient] created for " + url);
    }
    public String get(String path) { return "[GET " + baseUrl + path + "]"; }
}

// Registrar that creates one RestClient per named service
class RestClientRegistrar implements ImportBeanDefinitionRegistrar {
    @Override
    public void registerBeanDefinitions(AnnotationMetadata meta,
                                        BeanDefinitionRegistry registry) {
        AnnotationAttributes attrs = AnnotationAttributes.fromMap(
            meta.getAnnotationAttributes(EnableRestClients.class.getName()));
        if (attrs == null) return;

        String[] clients = attrs.getStringArray("clients");
        String baseUrl   = attrs.getString("baseUrl");

        for (String client : clients) {
            String beanName = client + "Client";
            System.out.println("[Registrar] registering " + beanName);
            var bd = BeanDefinitionBuilder
                .genericBeanDefinition(RestClient.class)
                .addConstructorArgValue(baseUrl + "/" + client)
                .getBeanDefinition();
            registry.registerBeanDefinition(beanName, bd);
        }
    }
}

@Target(ElementType.TYPE) @Retention(RetentionPolicy.RUNTIME)
@Import(RestClientRegistrar.class)
@interface EnableRestClients {
    String[] clients() default {};
    String baseUrl()   default "http://localhost:8080";
}

// Service that uses two registered clients
class OrderProcessingService {
    @Autowired @Qualifier("userClient")    RestClient userClient;
    @Autowired @Qualifier("productClient") RestClient productClient;

    public void processOrder(int userId, int productId) {
        System.out.println(userClient.get("/users/" + userId));
        System.out.println(productClient.get("/products/" + productId));
        System.out.println("[Order] processed for user " + userId);
    }
}

@Configuration
@EnableRestClients(
    clients = {"user", "product"},
    baseUrl = "https://api.acme.com"
)
@ComponentScan(basePackageClasses = RegistrarMultiple.class)
class AppCfg2 {}

public class RegistrarMultiple {
    public static void main(String[] args) {
        var ctx = new AnnotationConfigApplicationContext(AppCfg2.class);
        ctx.getBean(OrderProcessingService.class).processOrder(1, 42);
        System.out.println("\nAll RestClient beans:");
        ctx.getBeansOfType(RestClient.class).forEach((name, c) ->
            System.out.println("  " + name + ": " + c.get("/ping")));
        ctx.close();
    }
}
```

How to run: `java RegistrarMultiple.java`

`EnableRestClients(clients={"user","product"})` triggers `RestClientRegistrar` which loops and registers `userClient` and `productClient` beans. Both become available for injection via `@Qualifier`.

### Level 3 — Advanced

`ImportBeanDefinitionRegistrar` that inspects the importing class's other annotations and registers infrastructure beans based on what it finds — simulating what Spring Data's `@EnableJpaRepositories` does.

```java
// RegistrarAdvanced.java
import org.springframework.beans.factory.annotation.*;
import org.springframework.beans.factory.support.*;
import org.springframework.context.annotation.*;
import org.springframework.core.type.*;
import org.springframework.core.annotation.AnnotationAttributes;
import java.lang.annotation.*;
import java.util.*;

// Simple "repository" interface and implementation
interface Repo<T> { T find(int id); }

class InMemRepo<T> implements Repo<T> {
    private final Map<Integer, T> store = new HashMap<>();
    private final String name;
    InMemRepo(String n) { this.name = n; System.out.println("[Repo] " + n + " created"); }
    @SuppressWarnings("unchecked")
    public T find(int id) { return (T)("[" + name + "#" + id + "]"); }
    public void add(int id, T val) { store.put(id, val); }
}

// Factory bean that creates Repo instances by name
class RepoFactory {
    public static Repo<?> create(String repoName) { return new InMemRepo<>(repoName); }
}

// Registrar: creates one Repo bean per name listed in @EnableRepos
class RepoRegistrar implements ImportBeanDefinitionRegistrar {
    @Override
    public void registerBeanDefinitions(AnnotationMetadata meta,
                                        BeanDefinitionRegistry registry) {
        AnnotationAttributes attrs = AnnotationAttributes.fromMap(
            meta.getAnnotationAttributes(EnableRepos.class.getName()));
        if (attrs == null) return;

        String[] names = attrs.getStringArray("value");
        System.out.println("[RepoRegistrar] registering repos: " + Arrays.toString(names));
        for (String name : names) {
            String beanName = name + "Repo";
            var bd = BeanDefinitionBuilder
                .genericBeanDefinition(InMemRepo.class)
                .addConstructorArgValue(name)
                .getBeanDefinition();
            registry.registerBeanDefinition(beanName, bd);
        }

        // Also register a registry of all repo names
        var summaryBd = BeanDefinitionBuilder
            .genericBeanDefinition(RepoSummary.class)
            .addConstructorArgValue(names)
            .getBeanDefinition();
        registry.registerBeanDefinition("repoSummary", summaryBd);
    }
}

class RepoSummary {
    private final String[] repos;
    RepoSummary(String[] repos) { this.repos = repos; }
    public void print() {
        System.out.println("Active repos: " + Arrays.toString(repos));
    }
}

@Target(ElementType.TYPE) @Retention(RetentionPolicy.RUNTIME)
@Import(RepoRegistrar.class)
@interface EnableRepos { String[] value() default {}; }

class ShopService {
    @Autowired @Qualifier("userRepo")    InMemRepo<?> userRepo;
    @Autowired @Qualifier("productRepo") InMemRepo<?> productRepo;
    @Autowired @Qualifier("orderRepo")   InMemRepo<?> orderRepo;

    public void run() {
        System.out.println(userRepo.find(1));
        System.out.println(productRepo.find(2));
        System.out.println(orderRepo.find(3));
    }
}

@Configuration
@EnableRepos({"user", "product", "order"})
@ComponentScan(basePackageClasses = RegistrarAdvanced.class)
class ShopCfg {}

public class RegistrarAdvanced {
    public static void main(String[] args) {
        var ctx = new AnnotationConfigApplicationContext(ShopCfg.class);
        ctx.getBean(RepoSummary.class).print();
        ctx.getBean(ShopService.class).run();
        ctx.close();
    }
}
```

How to run: `java RegistrarAdvanced.java`

`RepoRegistrar` creates three `InMemRepo` beans (`userRepo`, `productRepo`, `orderRepo`) plus a `RepoSummary` bean — all registered programmatically without any `@Bean` method. `ShopService` injects them by `@Qualifier`.

## 6. Walkthrough

Execution for Level 3:

1. **`AnnotationConfigApplicationContext(ShopCfg.class)` created** — `ConfigurationClassPostProcessor` finds `@Import(RepoRegistrar.class)` via `@EnableRepos`.
2. **`RepoRegistrar.registerBeanDefinitions()` called** — `importingClassMetadata` is `ShopCfg`'s metadata. Reads `@EnableRepos({"user","product","order"})`.
3. **Loop registers** `userRepo`, `productRepo`, `orderRepo` as `InMemRepo` beans with constructor args `"user"`, `"product"`, `"order"`.
4. **Registers `repoSummary`** as `RepoSummary` bean with constructor arg `["user","product","order"]`.
5. **Component scan finds `ShopService`** — `@Autowired` fields resolved.
6. **`repoSummary.print()`** → `Active repos: [user, product, order]`.
7. **`shopService.run()`** → three `find()` calls printing `[user#1]`, `[product#2]`, `[order#3]`.

Expected output:
```
[RepoRegistrar] registering repos: [user, product, order]
[Repo] user created
[Repo] product created
[Repo] order created
Active repos: [user, product, order]
[user#1]
[product#2]
[order#3]
```

## 7. Gotchas & takeaways

> `registerBeanDefinitions()` is called during configuration processing — the `BeanDefinitionRegistry` reflects only beans processed so far. You can inspect what's already registered, but the full context isn't yet ready. Do not call `ctx.getBean()` inside the registrar.

> `BeanDefinitionBuilder.genericBeanDefinition(ClassName.class)` creates a standard `GenericBeanDefinition`. For full singleton semantics with lifecycle callbacks, ensure you set scope and apply property values correctly — the builder's defaults match singleton scope.

- Use `registry.containsBeanDefinition(name)` before registering to avoid duplicates.
- `BeanDefinitionBuilder` supports `.setScope()`, `.setLazyInit()`, `.addPropertyValue()`, `.addPropertyReference()` for full bean configuration.
- `ImportBeanDefinitionRegistrar` can also implement `EnvironmentAware`, `ResourceLoaderAware`, or `BeanClassLoaderAware` to receive those resources before `registerBeanDefinitions()` is called.
- This is the mechanism behind `@EnableJpaRepositories`, `@MapperScan`, `@EnableFeignClients` — understanding it demystifies how those annotations create proxy beans for every repository interface.

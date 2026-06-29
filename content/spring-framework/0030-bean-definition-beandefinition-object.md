---
card: spring-framework
gi: 30
slug: bean-definition-beandefinition-object
title: Bean definition & BeanDefinition object
---

## 1. What it is

A **`BeanDefinition`** is the metadata object Spring stores internally for each bean. It is not the bean itself — it is the *recipe* that tells the container how to create, configure, and wire a bean.

Every `@Component`, `@Bean` method, or XML `<bean>` element is parsed into a `BeanDefinition` stored in `DefaultListableBeanFactory`'s `beanDefinitionMap`. The map key is the bean name; the value is the `BeanDefinition`.

Key properties of `BeanDefinition`:

| Property | API | Example |
|---|---|---|
| Bean class | `getBeanClassName()` | `"com.example.OrderService"` |
| Scope | `getScope()` | `"singleton"`, `"prototype"` |
| Lazy | `isLazyInit()` | `false` |
| Constructor args | `getConstructorArgumentValues()` | typed/index arg list |
| Property values | `getPropertyValues()` | setter-based deps |
| Init method | `getInitMethodName()` | `"init"` |
| Destroy method | `getDestroyMethodName()` | `"close"` |
| Primary | `isPrimary()` | `true` |
| Description | `getDescription()` | free-form |

In one sentence: **`BeanDefinition` is the blueprint the container stores for each bean — it holds all the metadata needed to create, configure, and destroy the bean at the right time.**

## 2. Why & when

You interact with `BeanDefinition` directly in two scenarios:

1. **Framework extension.** Writing a `BeanFactoryPostProcessor` that modifies bean configuration before instantiation (e.g., `PropertySourcesPlaceholderConfigurer` resolves `${...}` expressions by reading `BeanDefinition`'s property values).

2. **Programmatic registration.** Using `GenericApplicationContext` or `DefaultListableBeanFactory` to register beans at runtime without XML or annotations.

For everyday application code you never touch `BeanDefinition` directly — `@Component` and `@Bean` create them for you. Understanding them helps debug why a bean is created a certain way or how to dynamically add beans in a framework.

## 3. Core concept

`BeanDefinition` is an interface. The main implementations are:

```
BeanDefinition (interface)
  ├── AbstractBeanDefinition
  │     ├── RootBeanDefinition       (the merged, final form used at creation time)
  │     └── GenericBeanDefinition    (used when registering programmatically)
  └── AnnotatedBeanDefinition        (preserves annotation metadata)
        └── ScannedGenericBeanDefinition  (from @Component scan)
```

The container processes `BeanDefinition` objects in two phases:

```
Phase 1: BeanFactoryPostProcessors run
  → read and modify BeanDefinitions
  → e.g., resolve ${property.key} in property values

Phase 2: finishBeanFactoryInitialization()
  → for each BeanDefinition:
      → merge with parent definitions (if any)
      → instantiate via constructor or factory method
      → inject properties/constructor args
      → call init methods
      → apply BeanPostProcessors (AOP proxy, etc.)
      → store singleton in singletonObjects map
```

You create one with `BeanDefinitionBuilder`:

```java
BeanDefinition def = BeanDefinitionBuilder
    .genericBeanDefinition(OrderService.class)
    .addConstructorArgReference("emailService")
    .setScope("singleton")
    .setLazyInit(false)
    .setInitMethodName("init")
    .getBeanDefinition();
```

## 4. Diagram

<svg viewBox="0 0 680 230" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="BeanDefinition metadata fields mapping to the runtime bean: class, scope, constructor args, init/destroy methods">
  <defs>
    <marker id="a30" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#6db33f"/></marker>
  </defs>

  <!-- BeanDefinition box -->
  <rect x="10" y="20" width="240" height="180" rx="8" fill="#1c2430" stroke="#79c0ff" stroke-width="2"/>
  <text x="130" y="44" fill="#79c0ff" font-size="12" text-anchor="middle" font-family="sans-serif">BeanDefinition</text>
  <text x="130" y="62" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">beanClass = OrderService.class</text>
  <text x="130" y="78" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">scope = "singleton"</text>
  <text x="130" y="94" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">lazyInit = false</text>
  <text x="130" y="110" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">constructorArgs = [ref:emailService]</text>
  <text x="130" y="126" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">initMethodName = "init"</text>
  <text x="130" y="142" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">destroyMethodName = "close"</text>
  <text x="130" y="158" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">primary = true</text>
  <text x="130" y="174" fill="#6db33f" font-size="8" text-anchor="middle" font-family="sans-serif">stored in beanDefinitionMap["orderService"]</text>

  <!-- Arrow to container -->
  <line x1="250" y1="110" x2="310" y2="110" stroke="#6db33f" stroke-width="2" marker-end="url(#a30)"/>
  <text x="280" y="104" fill="#6db33f" font-size="8" text-anchor="middle" font-family="sans-serif">create</text>

  <!-- Runtime bean -->
  <rect x="312" y="50" width="180" height="120" rx="8" fill="#1c2430" stroke="#6db33f" stroke-width="2"/>
  <text x="402" y="74" fill="#6db33f" font-size="11" text-anchor="middle" font-family="sans-serif">OrderService</text>
  <text x="402" y="90" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">singleton in heap</text>
  <text x="402" y="106" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">emailService injected</text>
  <text x="402" y="122" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">init() called ✓</text>
  <text x="402" y="138" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">ready for getBean()</text>
  <text x="402" y="155" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">close() → destroy()</text>

  <!-- BFPP path -->
  <rect x="510" y="20" width="160" height="56" rx="6" fill="#1c2430" stroke="#8b949e" stroke-width="1"/>
  <text x="590" y="43" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">BeanFactoryPostProcessor</text>
  <text x="590" y="61" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">can modify BeanDefinition</text>

  <line x1="590" y1="76" x2="295" y2="95" stroke="#8b949e" stroke-width="1" stroke-dasharray="4,2" marker-end="url(#a30)"/>
  <text x="490" y="90" fill="#8b949e" font-size="7" font-family="sans-serif">before instantiation</text>

  <text x="340" y="200" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">BeanDefinition = recipe. Bean = the cooked object. Both live in the same container.</text>
</svg>

`BeanDefinition` holds the recipe. A `BeanFactoryPostProcessor` can modify it before creation. The container reads the recipe and produces the singleton.

## 5. Runnable example

Scenario: a customer notification system. We show the `BeanDefinition`-like metadata layer explicitly — first simple, then with a post-processor that overrides the email endpoint, then with runtime registration of an extra bean.

### Level 1 — Basic

A simple `BeanDefinition`-style record: store class + constructor args, instantiate on demand.

```java
// BeanDefDemo.java — run with: java BeanDefDemo.java
import java.util.*;
import java.lang.reflect.*;

public class BeanDefDemo {

    record BeanDef(String name, Class<?> beanClass, List<Object> ctorArgs,
                   String scope, String initMethod) {}

    // Domain
    static class EmailSender {
        private final String host;
        EmailSender(String host) { this.host = host; }
        void send(String to, String msg) {
            System.out.printf("  [EMAIL via %s → %s] %s%n", host, to, msg);
        }
    }

    static class NotificationService {
        private final EmailSender email;
        NotificationService(EmailSender email) { this.email = email; }
        void notify(String user, String msg) { email.send(user, msg); }
    }

    // Container that stores BeanDefs and creates beans from them
    static class BeanDefContainer {
        private final Map<String, BeanDef>  defs  = new LinkedHashMap<>();
        private final Map<String, Object>   beans = new LinkedHashMap<>();

        void registerDef(BeanDef def) {
            defs.put(def.name(), def);
            System.out.println("  [DEF REGISTERED] " + def.name()
                + " class=" + def.beanClass().getSimpleName()
                + " scope=" + def.scope());
        }

        void refresh() throws Exception {
            System.out.println("[REFRESH] Creating beans from definitions...");
            for (var d : defs.values()) {
                if ("singleton".equals(d.scope())) {
                    beans.put(d.name(), instantiate(d));
                    System.out.println("  Created: " + d.name());
                }
            }
        }

        Object instantiate(BeanDef def) throws Exception {
            Object[] args = def.ctorArgs().stream()
                .map(a -> (a instanceof String s && beans.containsKey(s)) ? beans.get(s) : a)
                .toArray();
            Constructor<?> ctor = def.beanClass().getDeclaredConstructors()[0];
            Object bean = ctor.newInstance(args);
            if (def.initMethod() != null)
                def.beanClass().getDeclaredMethod(def.initMethod()).invoke(bean);
            return bean;
        }

        @SuppressWarnings("unchecked")
        <T> T getBean(String name) { return (T) beans.get(name); }
    }

    public static void main(String[] args) throws Exception {
        BeanDefContainer ctx = new BeanDefContainer();

        // These BeanDefs are what @Bean methods produce internally in Spring
        ctx.registerDef(new BeanDef("emailSender", EmailSender.class,
            List.of("smtp.example.com"), "singleton", null));
        ctx.registerDef(new BeanDef("notificationService", NotificationService.class,
            List.of("emailSender"),        "singleton", null));

        ctx.refresh();

        NotificationService svc = ctx.getBean("notificationService");
        svc.notify("alice@example.com", "Your order shipped!");
        svc.notify("bob@example.com",   "Invoice ready.");
    }
}
```

How to run: `java BeanDefDemo.java`

`BeanDef` mirrors Spring's `BeanDefinition`. The container stores definitions first (no objects yet), then creates all singletons at `refresh()`. Constructor arg `"emailSender"` is a bean reference — resolved to the already-created `EmailSender` singleton.

### Level 2 — Intermediate

Add a `BeanDefinitionPostProcessor` that modifies the `emailSender` definition before instantiation — simulating `BeanFactoryPostProcessor` changing a property.

```java
// BeanDefDemo2.java — run with: java BeanDefDemo2.java
import java.util.*;
import java.lang.reflect.*;

public class BeanDefDemo2 {

    // Mutable BeanDef (post-processors can change it before instantiation)
    static class MutableBeanDef {
        String name;
        Class<?> beanClass;
        List<Object> ctorArgs;
        String scope = "singleton";

        MutableBeanDef(String name, Class<?> cls, Object... args) {
            this.name = name; this.beanClass = cls; this.ctorArgs = new ArrayList<>(List.of(args));
        }
        @Override public String toString() {
            return "BeanDef{" + name + ", class=" + beanClass.getSimpleName() + ", args=" + ctorArgs + "}";
        }
    }

    // Domain
    static class EmailSender {
        private final String host;
        private final int    port;
        EmailSender(String host, int port) { this.host = host; this.port = port; }
        void send(String to, String msg) {
            System.out.printf("  [EMAIL %s:%d → %s] %s%n", host, port, to, msg);
        }
    }

    static class NotificationService {
        private final EmailSender email;
        NotificationService(EmailSender email) { this.email = email; }
        void notify(String user, String msg) { email.send(user, msg); }
    }

    // BeanDefinitionPostProcessor — modifies definitions before instantiation
    interface BeanDefPostProcessor {
        void postProcess(Map<String, MutableBeanDef> defs);
    }

    // Overrides emailSender host from an external config
    static class EnvironmentConfigurer implements BeanDefPostProcessor {
        private final String smtpHost;
        private final int    smtpPort;
        EnvironmentConfigurer(String host, int port) { smtpHost = host; smtpPort = port; }

        public void postProcess(Map<String, MutableBeanDef> defs) {
            MutableBeanDef emailDef = defs.get("emailSender");
            if (emailDef != null) {
                System.out.println("  [BFPP] EnvironmentConfigurer: overriding emailSender args");
                System.out.println("    Before: " + emailDef.ctorArgs);
                emailDef.ctorArgs = new ArrayList<>(List.of(smtpHost, smtpPort));
                System.out.println("    After:  " + emailDef.ctorArgs);
            }
        }
    }

    static class BFPPContainer {
        private final Map<String, MutableBeanDef>   defs    = new LinkedHashMap<>();
        private final List<BeanDefPostProcessor>     bfpps   = new ArrayList<>();
        private final Map<String, Object>            beans   = new LinkedHashMap<>();

        void register(MutableBeanDef def) { defs.put(def.name, def); }
        void addPostProcessor(BeanDefPostProcessor pp) { bfpps.add(pp); }

        void refresh() throws Exception {
            System.out.println("[REFRESH] Step 5: BeanDefinitionPostProcessors...");
            for (var pp : bfpps) pp.postProcess(defs);

            System.out.println("[REFRESH] Step 11: Creating singletons...");
            for (var d : defs.values()) {
                beans.put(d.name, instantiate(d));
                System.out.println("  Created: " + d.name);
            }
            System.out.println();
        }

        Object instantiate(MutableBeanDef d) throws Exception {
            Object[] args = d.ctorArgs.stream()
                .map(a -> (a instanceof String s && beans.containsKey(s)) ? beans.get(s) : a)
                .toArray();
            return d.beanClass.getDeclaredConstructors()[0].newInstance(args);
        }

        @SuppressWarnings("unchecked") <T> T getBean(String n) { return (T) beans.get(n); }
    }

    public static void main(String[] args) throws Exception {
        BFPPContainer ctx = new BFPPContainer();

        // Registered definitions (default / dev values)
        ctx.register(new MutableBeanDef("emailSender", EmailSender.class, "localhost", 25));
        ctx.register(new MutableBeanDef("notificationService", NotificationService.class, "emailSender"));

        // BeanFactoryPostProcessor overrides values from "production" environment
        ctx.addPostProcessor(new EnvironmentConfigurer("smtp.prod.example.com", 587));

        ctx.refresh();

        NotificationService svc = ctx.getBean("notificationService");
        svc.notify("alice@example.com", "Your order shipped!");
    }
}
```

How to run: `java BeanDefDemo2.java`

`EnvironmentConfigurer.postProcess` runs in step 5 — it replaces `localhost:25` with the production SMTP host/port **before** `EmailSender` is created. The `EmailSender` bean is born with the production configuration. This is exactly how Spring's `PropertySourcesPlaceholderConfigurer` works: it reads `BeanDefinition` property values and substitutes `${smtp.host}` tokens with real values before instantiation.

### Level 3 — Advanced

Runtime bean registration: add a new `BeanDefinition` **after** the initial context is configured — dynamic plugin-style registration.

```java
// BeanDefDemo3.java — run with: java BeanDefDemo3.java
import java.util.*;
import java.lang.reflect.*;
import java.util.function.*;

public class BeanDefDemo3 {

    interface NotificationChannel {
        String name();
        void send(String to, String msg);
    }

    static class EmailChannel implements NotificationChannel {
        public String name() { return "email"; }
        public void send(String to, String msg) {
            System.out.printf("  [EMAIL → %s] %s%n", to, msg);
        }
    }

    static class SmsChannel implements NotificationChannel {
        public String name() { return "sms"; }
        public void send(String to, String msg) {
            System.out.printf("  [SMS → %s] %s%n", to, msg);
        }
    }

    static class SlackChannel implements NotificationChannel {
        private final String workspace;
        SlackChannel(String workspace) { this.workspace = workspace; }
        public String name() { return "slack#" + workspace; }
        public void send(String to, String msg) {
            System.out.printf("  [SLACK:%s → %s] %s%n", workspace, to, msg);
        }
    }

    // Aggregator — depends on all NotificationChannel beans
    static class NotificationService {
        private final List<NotificationChannel> channels;
        NotificationService(List<NotificationChannel> channels) { this.channels = channels; }
        void notifyAll(String user, String msg) {
            System.out.println("  Notifying via " + channels.size() + " channels:");
            channels.forEach(c -> c.send(user, msg));
        }
    }

    // Container supporting runtime BeanDefinition registration
    static class DynamicContainer {
        private final Map<String, Supplier<Object>> defs  = new LinkedHashMap<>();
        private final Map<String, Object>           beans = new LinkedHashMap<>();

        void register(String name, Supplier<Object> factory) {
            defs.put(name, factory);
            System.out.println("  [DEF] Registered: " + name);
        }

        // Runtime registration — adds new bean def and instantiates immediately
        void registerAndRefreshBean(String name, Supplier<Object> factory) {
            System.out.println("  [DYNAMIC DEF] Runtime registration: " + name);
            beans.put(name, factory.get());
            System.out.println("  [DYNAMIC DEF] Bean ready: " + name);
        }

        void refresh() {
            System.out.println("[REFRESH] Creating initial singletons...");
            for (var e : defs.entrySet()) {
                if (!beans.containsKey(e.getKey())) {
                    beans.put(e.getKey(), e.getValue().get());
                    System.out.println("  Ready: " + e.getKey());
                }
            }
        }

        @SuppressWarnings("unchecked")
        <T> List<T> getBeansOfType(Class<T> type) {
            return beans.values().stream()
                .filter(type::isInstance)
                .map(b -> (T) b)
                .toList();
        }

        @SuppressWarnings("unchecked")
        <T> T getBean(String name) { return (T) beans.get(name); }
    }

    public static void main(String[] args) {
        DynamicContainer ctx = new DynamicContainer();

        ctx.register("emailChannel", EmailChannel::new);
        ctx.register("smsChannel",   SmsChannel::new);

        ctx.refresh();

        System.out.println("\n=== Runtime: Slack plugin added (dynamic BeanDef registration) ===");
        ctx.registerAndRefreshBean("slackChannel", () -> new SlackChannel("engineering"));

        // NotificationService uses ALL channel beans
        List<NotificationChannel> allChannels = ctx.getBeansOfType(NotificationChannel.class);
        NotificationService svc = new NotificationService(allChannels);

        System.out.println("\n=== Notifying user ===");
        svc.notifyAll("alice@example.com", "Deployment complete!");

        System.out.println("\n=== BeanDefinition summary ===");
        System.out.println("  Channels registered: " + allChannels.stream().map(NotificationChannel::name).toList());
    }
}
```

How to run: `java BeanDefDemo3.java`

`SlackChannel` is registered *after* initial `refresh()` — dynamic registration. `getBeansOfType(NotificationChannel.class)` then finds all three channels. In real Spring, `DefaultListableBeanFactory.registerBeanDefinition()` allows exactly this — adding beans at runtime before they are first requested, enabling plugin architectures.

## 6. Walkthrough

**Level 3 — dynamic registration and discovery:**

```
Initial refresh():
  defs = {emailChannel, smsChannel}
  → EmailChannel() created → beans["emailChannel"]
  → SmsChannel()  created → beans["smsChannel"]

Runtime registerAndRefreshBean("slackChannel", ...):
  → SlackChannel("engineering") created immediately
  → beans["slackChannel"] = SlackChannel

getBeansOfType(NotificationChannel.class):
  → scan beans.values():
      EmailChannel  implements NotificationChannel → included
      SmsChannel    implements NotificationChannel → included
      SlackChannel  implements NotificationChannel → included
  → returns List.of(email, sms, slack)

NotificationService(allChannels).notifyAll("alice@example.com", "Deployment complete!"):
  → email.send() → "[EMAIL → alice@example.com] Deployment complete!"
  → sms.send()   → "[SMS → alice@example.com] Deployment complete!"
  → slack.send() → "[SLACK:engineering → alice@example.com] Deployment complete!"
```

**BeanDefinition lifecycle at each level:**

| Level | When metadata is resolved | Post-processor runs | Result |
|---|---|---|---|
| 1 (basic) | At registration | None | Bean created with original args |
| 2 (BFPP) | At registration; modified before instantiation | Yes — changes constructor args | Bean created with overridden args |
| 3 (dynamic) | At runtime after refresh | None for dynamic beans | Bean immediately usable |

## 7. Gotchas & takeaways

> **`BeanDefinition` is the source of truth for the container, not the annotation.** If a `BeanFactoryPostProcessor` changes `beanDefinition.setScope("prototype")` on a class annotated `@Singleton`, the container creates a prototype. The annotation is only read once at parse time; the `BeanDefinition` in the registry is what actually drives behavior.

> **`BeanDefinition.getResolvableType()` is more reliable than `getBeanClassName()` for generic beans.** For `@Bean` methods returning `List<OrderEvent>`, `getBeanClassName()` returns `"java.util.List"` — `getResolvableType()` returns the full generic signature.

- Access the registry in a `BeanFactoryPostProcessor` via the `ConfigurableListableBeanFactory` parameter: `factory.getBeanDefinition("myBean").setLazyInit(true)`.
- `DefaultListableBeanFactory.getBeanDefinitionNames()` lists all registered bean names — useful for debugging unexpected beans.
- `BeanDefinitionOverrideException` is thrown (Spring 5.3+) if two configurations declare the same bean name — enable override with `spring.main.allow-bean-definition-overriding=true` in Spring Boot.
- Parent bean definitions (`<bean parent="...">` in XML) create an inheritance chain — child inherits all metadata from the parent definition and can override individual properties.
- `BeanDefinition` for a `@Bean` method is a `ConfigurationClassBeanDefinition` — it stores a reference to the factory method so the container can invoke it during instantiation.

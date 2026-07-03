---
card: spring-framework
gi: 104
slug: customautowireconfigurer
title: CustomAutowireConfigurer
---

## 1. What it is

`CustomAutowireConfigurer` is a `BeanFactoryPostProcessor` that lets you register **custom qualifier annotation types** with Spring's autowiring system without those annotations needing `@Qualifier` as a meta-annotation. It tells Spring: "also treat annotations of type `X` as qualifier annotations when resolving autowiring."

In other words, it provides a programmatic alternative to placing `@Qualifier` as a meta-annotation on your custom annotation.

## 2. Why & when

The typical situation is a third-party or legacy annotation you can't modify. Suppose an external library ships:

```java
@interface FastProcessor {}  // no @Qualifier meta-annotation
```

You want to use `@FastProcessor` as a qualifier in Spring, but you can't edit the library. `CustomAutowireConfigurer` lets you register `FastProcessor.class` as a qualifying annotation type at boot time, so `@Autowired @FastProcessor` works the same as if `@FastProcessor` had `@Qualifier` meta-annotated on it.

Use `CustomAutowireConfigurer` when:
- You can't add `@Qualifier` to an existing annotation (third-party, generated code).
- You want to centrally declare which annotations act as qualifiers in a config class.

For annotations you own, simply add `@Qualifier` as meta-annotation — that's cleaner.

## 3. Core concept

`CustomAutowireConfigurer` implements `BeanFactoryPostProcessor`. It receives the `ConfigurableListableBeanFactory` and calls `bf.registerAutowireCandidateResolver(...)` (or its internal equivalent) to append the given annotation types to the list of qualifier annotation types recognized during autowiring.

Registration example in Java config:
```java
@Bean
public static CustomAutowireConfigurer cac() {
    var c = new CustomAutowireConfigurer();
    c.setCustomQualifierTypes(Set.of(FastProcessor.class, LowLatency.class));
    return c;
}
```

After this, any bean annotated `@FastProcessor` and any injection point annotated `@FastProcessor` form a matching pair — just as if `@FastProcessor` declared `@Qualifier` internally.

## 4. Diagram

<svg viewBox="0 0 700 210" xmlns="http://www.w3.org/2000/svg">
  <!-- External annotation -->
  <rect x="10" y="40" width="185" height="44" rx="8" fill="#1c2430" stroke="#ff7b72" stroke-width="1.5" stroke-dasharray="5,3"/>
  <text x="102" y="63" fill="#ff7b72" font-size="12" text-anchor="middle" font-family="sans-serif">@FastProcessor</text>
  <text x="102" y="77" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">no @Qualifier meta-annotation</text>

  <!-- CAC -->
  <rect x="10" y="120" width="185" height="44" rx="8" fill="#1c2430" stroke="#6db33f" stroke-width="2"/>
  <text x="102" y="141" fill="#6db33f" font-size="12" text-anchor="middle" font-family="sans-serif">CustomAutowire</text>
  <text x="102" y="155" fill="#6db33f" font-size="12" text-anchor="middle" font-family="sans-serif">Configurer</text>

  <!-- After registration -->
  <rect x="310" y="80" width="195" height="54" rx="8" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="407" y="103" fill="#e6edf3" font-size="12" text-anchor="middle" font-family="sans-serif">@Autowired</text>
  <text x="407" y="118" fill="#6db33f" font-size="10" text-anchor="middle" font-family="sans-serif">@FastProcessor — now recognized</text>

  <!-- Bean -->
  <rect x="560" y="80" width="130" height="54" rx="8" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="625" y="103" fill="#6db33f" font-size="12" text-anchor="middle" font-family="sans-serif">Fast bean ✓</text>
  <text x="625" y="118" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">injected</text>

  <line x1="197" y1="142" x2="307" y2="112" stroke="#6db33f" stroke-width="2" marker-end="url(#a104)"/>
  <line x1="197" y1="62" x2="307" y2="92" stroke="#ff7b72" stroke-width="1.5" stroke-dasharray="4,3" marker-end="url(#c104)"/>
  <line x1="507" y1="107" x2="557" y2="107" stroke="#6db33f" stroke-width="2" marker-end="url(#a104)"/>
  <defs>
    <marker id="a104" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#6db33f"/></marker>
    <marker id="c104" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#ff7b72"/></marker>
  </defs>
  <text x="350" y="190" fill="#8b949e" font-size="11" text-anchor="middle" font-family="sans-serif">CAC registers the external annotation as a qualifier type — Spring then treats it like @Qualifier</text>
</svg>

`CustomAutowireConfigurer` bridges an external annotation into Spring's qualifier resolution system.

## 5. Runnable example

### Level 1 — Basic

Register a custom annotation (one you'd normally mark with `@Qualifier`) via `CustomAutowireConfigurer` instead of meta-annotating it.

```java
// CacBasic.java
import org.springframework.beans.factory.annotation.*;
import org.springframework.beans.factory.annotation.CustomAutowireConfigurer;
import org.springframework.context.annotation.*;
import org.springframework.stereotype.*;
import java.lang.annotation.*;
import java.util.Set;

// Imagine this came from a library — no @Qualifier meta-annotation on it
@Target({ElementType.TYPE, ElementType.FIELD, ElementType.PARAMETER})
@Retention(RetentionPolicy.RUNTIME)
@interface FastProcessor {}

interface Processor {
    String process(String input);
}

@Component
@FastProcessor           // marks this as the "fast" candidate
class ConcurrentProcessor implements Processor {
    public String process(String in) { return "[FAST] " + in.toUpperCase(); }
}

@Component
class BatchProcessor implements Processor {
    public String process(String in) { return "[BATCH] " + in; }
}

@Service
class WorkflowService {
    @Autowired
    @FastProcessor       // selects ConcurrentProcessor via custom qualifier
    private Processor processor;

    public void run(String data) { System.out.println(processor.process(data)); }
}

@Configuration
@ComponentScan
class CacCfg {
    @Bean
    public static CustomAutowireConfigurer cac() {
        var c = new CustomAutowireConfigurer();
        c.setCustomQualifierTypes(Set.of(FastProcessor.class));
        return c;
    }
}

public class CacBasic {
    public static void main(String[] args) {
        var ctx = new AnnotationConfigApplicationContext(CacCfg.class);
        ctx.getBean(WorkflowService.class).run("hello world");
        ctx.close();
    }
}
```

How to run: `java CacBasic.java`

`@FastProcessor` has no `@Qualifier` meta-annotation, but `CustomAutowireConfigurer` registers it as a qualifying annotation type. Spring then uses it to match `ConcurrentProcessor` to the `@FastProcessor`-annotated injection point.

### Level 2 — Intermediate

Register multiple custom qualifier annotations and show that each selects only its designated bean.

```java
// CacMultiple.java
import org.springframework.beans.factory.annotation.*;
import org.springframework.beans.factory.annotation.CustomAutowireConfigurer;
import org.springframework.context.annotation.*;
import org.springframework.stereotype.*;
import java.lang.annotation.*;
import java.util.Set;

@Target({ElementType.TYPE, ElementType.FIELD, ElementType.PARAMETER})
@Retention(RetentionPolicy.RUNTIME)
@interface HighThroughput {}

@Target({ElementType.TYPE, ElementType.FIELD, ElementType.PARAMETER})
@Retention(RetentionPolicy.RUNTIME)
@interface LowLatency {}

interface EventProcessor {
    void handle(String event);
}

@Component @HighThroughput
class BatchEventProcessor implements EventProcessor {
    public void handle(String e) { System.out.println("[BATCH] " + e); }
}

@Component @LowLatency
class RealtimeEventProcessor implements EventProcessor {
    public void handle(String e) { System.out.println("[REALTIME] " + e); }
}

@Service
class EventRouter {
    @Autowired @HighThroughput private EventProcessor batchProc;
    @Autowired @LowLatency     private EventProcessor rtProc;

    public void route(String event, boolean urgent) {
        if (urgent) rtProc.handle(event);
        else        batchProc.handle(event);
    }
}

@Configuration
@ComponentScan
class MultiCacCfg {
    @Bean
    public static CustomAutowireConfigurer cac() {
        var c = new CustomAutowireConfigurer();
        c.setCustomQualifierTypes(Set.of(HighThroughput.class, LowLatency.class));
        return c;
    }
}

public class CacMultiple {
    public static void main(String[] args) {
        var ctx = new AnnotationConfigApplicationContext(MultiCacCfg.class);
        var router = ctx.getBean(EventRouter.class);
        router.route("order.created", false);   // batch
        router.route("payment.failed", true);   // realtime
        ctx.close();
    }
}
```

How to run: `java CacMultiple.java`

Both `@HighThroughput` and `@LowLatency` are registered as qualifier types. Each selects its matching bean exactly as `@Qualifier` would.

### Level 3 — Advanced

Simulate a third-party library annotation scenario: the annotation is in a separate "library" class (inner class standing in), CAC registers it, and two services independently select different implementations.

```java
// CacLibrary.java
import org.springframework.beans.factory.annotation.*;
import org.springframework.beans.factory.annotation.CustomAutowireConfigurer;
import org.springframework.context.annotation.*;
import org.springframework.stereotype.*;
import java.lang.annotation.*;
import java.util.Set;

// "Library" annotations — cannot be modified to add @Qualifier
@Target({ElementType.TYPE, ElementType.FIELD, ElementType.METHOD, ElementType.PARAMETER})
@Retention(RetentionPolicy.RUNTIME)
@interface Encrypted {}

@Target({ElementType.TYPE, ElementType.FIELD, ElementType.METHOD, ElementType.PARAMETER})
@Retention(RetentionPolicy.RUNTIME)
@interface Plaintext {}

interface StorageService {
    void write(String path, String content);
    String read(String path);
}

@Component @Encrypted
class EncryptedStorage implements StorageService {
    private final java.util.Map<String,String> store = new java.util.HashMap<>();
    public void write(String p, String c) {
        store.put(p, "ENC[" + c + "]");
        System.out.println("Encrypted write → " + p + ": ENC[" + c + "]");
    }
    public String read(String p) {
        String v = store.getOrDefault(p, null);
        return v != null ? v.replace("ENC[","").replace("]","") : null;
    }
}

@Component @Plaintext
class PlaintextStorage implements StorageService {
    private final java.util.Map<String,String> store = new java.util.HashMap<>();
    public void write(String p, String c) {
        store.put(p, c);
        System.out.println("Plaintext write  → " + p + ": " + c);
    }
    public String read(String p) { return store.get(p); }
}

@Service
class ConfigService {
    @Autowired @Plaintext private StorageService plainStorage;
    @Autowired @Encrypted private StorageService encStorage;

    public void demo() {
        plainStorage.write("config/app.yml", "debug: true");
        encStorage.write("secrets/db.pass", "s3cr3t");

        System.out.println("Config  read: " + plainStorage.read("config/app.yml"));
        System.out.println("Secret  read: " + encStorage.read("secrets/db.pass"));
    }
}

@Configuration
@ComponentScan
class LibCacCfg {
    @Bean
    public static CustomAutowireConfigurer cac() {
        var c = new CustomAutowireConfigurer();
        c.setCustomQualifierTypes(Set.of(Encrypted.class, Plaintext.class));
        return c;
    }
}

public class CacLibrary {
    public static void main(String[] args) {
        var ctx = new AnnotationConfigApplicationContext(LibCacCfg.class);
        ctx.getBean(ConfigService.class).demo();
        ctx.close();
    }
}
```

How to run: `java CacLibrary.java`

`@Encrypted` and `@Plaintext` come from a "library" (no `@Qualifier` on them). CAC registers both. `ConfigService` injects the correct storage variant for config (plaintext) and secrets (encrypted) independently.

## 6. Walkthrough

Execution order for the Level 3 example:

1. **`cac()` bean instantiated first** — Spring sees `CustomAutowireConfigurer` is a `BeanFactoryPostProcessor` and creates it early.
2. **`postProcessBeanFactory` fires** — CAC calls the internal resolver to register `Encrypted.class` and `Plaintext.class` as qualifier annotation types alongside `@Qualifier`.
3. **`EncryptedStorage` and `PlaintextStorage` instantiated** — both annotated with the now-registered qualifier annotations.
4. **`ConfigService` instantiated** — `@Autowired @Plaintext StorageService plainStorage`:
   - Candidates: `EncryptedStorage` (has `@Encrypted`), `PlaintextStorage` (has `@Plaintext`).
   - Required qualifier: `@Plaintext`. `PlaintextStorage` matches. Injected.
5. **`@Autowired @Encrypted StorageService encStorage`** — `@Encrypted` matches `EncryptedStorage`. Injected.
6. **`demo()` called** — writes then reads from both stores. Output shows the `ENC[...]` wrapper for encrypted and plain text for config.

Expected output:
```
Plaintext write  → config/app.yml: debug: true
Encrypted write  → secrets/db.pass: ENC[s3cr3t]
Config  read: debug: true
Secret  read: s3cr3t
```

## 7. Gotchas & takeaways

> `CustomAutowireConfigurer` must be declared as a **`static @Bean`** — it's a `BeanFactoryPostProcessor` and must be instantiated before regular beans.

> The custom annotation must still have `@Retention(RetentionPolicy.RUNTIME)` — if it's compiled away before runtime, Spring can't read it.

- `CustomAutowireConfigurer` is the programmatic alternative to placing `@Qualifier` as a meta-annotation. When you own the annotation, just add `@Qualifier` to it — don't use CAC.
- The registered annotation types are used for matching on both the bean definition **and** the injection point — both sides must carry the annotation for a match.
- Rarely needed in modern Spring Boot projects; `@Qualifier` meta-annotation is almost always the right approach for custom annotations you write.
- In older Spring XML config, the same effect was achieved via `<bean class="org.springframework.beans.factory.annotation.CustomAutowireConfigurer">`.

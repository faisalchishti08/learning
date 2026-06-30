---
card: spring-framework
gi: 95
slug: optional-objectprovider-optional-injection
title: Optional/ObjectProvider/Optional<> injection
---

## 1. What it is

Spring offers three modern ways to inject dependencies that might not exist:

- **`Optional<T>`** (Java 8) — Spring wraps the result in `Optional.of(bean)` if found, or `Optional.empty()` if absent. No null-checking needed.
- **`ObjectProvider<T>`** (Spring 4.3) — a lazy, iterable provider that can return zero, one, or many beans; it also defers bean creation until `getIfAvailable()` is called.
- **`@Autowired(required = false)`** — the older form; the injected field is simply `null` when absent (covered in the previous tutorial).

`Optional<T>` and `ObjectProvider<T>` are the idiomatic modern replacements for `required = false`.

## 2. Why & when

Use these when a dependency is **optional** or when you want to **defer** or **avoid eager creation** of a bean:

| Situation | Best choice |
|---|---|
| Inject one optional bean cleanly | `Optional<T>` |
| Inject one optional bean lazily | `ObjectProvider<T>` |
| Inject all beans of a type, lazily | `ObjectProvider<T>` (stream) |
| Legacy optional injection | `@Autowired(required = false)` |

`ObjectProvider` is especially useful for avoiding circular dependency issues because the provider is injected eagerly but the actual bean is fetched lazily.

## 3. Core concept

`Optional<T>` injection:
- Spring sees the parameter/field type is `Optional<X>`.
- If a bean of type `X` exists, Spring injects `Optional.of(x)`.
- If absent, injects `Optional.empty()`.
- The caller uses `.isPresent()`, `.ifPresent(…)`, `.map(…)`, etc. — no null checks.

`ObjectProvider<T>` injection:
- Spring injects a proxy/provider object immediately (always succeeds).
- The actual bean is resolved when you call `getIfAvailable()`, `getIfUnique()`, or `stream()`.
- Returns `null` (or empty stream) if no matching bean exists.
- Calling `getObject()` on an absent bean throws `NoSuchBeanDefinitionException`.

## 4. Diagram

<svg viewBox="0 0 700 240" xmlns="http://www.w3.org/2000/svg">
  <!-- Spring Context -->
  <rect x="10" y="80" width="155" height="80" rx="8" fill="#1c2430" stroke="#8b949e" stroke-width="1.5"/>
  <text x="87" y="105" fill="#8b949e" font-size="11" text-anchor="middle" font-family="sans-serif">Spring Context</text>
  <text x="87" y="122" fill="#e6edf3" font-size="11" text-anchor="middle" font-family="sans-serif">MetricsBean (present)</text>
  <text x="87" y="140" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">TracingBean (absent)</text>

  <!-- Optional path -->
  <rect x="280" y="50" width="165" height="44" rx="8" fill="#1c2430" stroke="#6db33f" stroke-width="2"/>
  <text x="362" y="73" fill="#6db33f" font-size="12" text-anchor="middle" font-family="sans-serif">Optional&lt;MetricsBean&gt;</text>
  <text x="362" y="87" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">Optional.of(bean) / .empty()</text>

  <!-- ObjectProvider path -->
  <rect x="280" y="120" width="165" height="44" rx="8" fill="#1c2430" stroke="#79c0ff" stroke-width="2"/>
  <text x="362" y="143" fill="#79c0ff" font-size="12" text-anchor="middle" font-family="sans-serif">ObjectProvider&lt;T&gt;</text>
  <text x="362" y="157" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">lazy — resolves on demand</text>

  <!-- Target -->
  <rect x="540" y="85" width="145" height="80" rx="8" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="612" y="110" fill="#e6edf3" font-size="12" text-anchor="middle" font-family="sans-serif">MyService</text>
  <text x="612" y="128" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">.isPresent() / .map()</text>
  <text x="612" y="144" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">.getIfAvailable()</text>

  <line x1="167" y1="112" x2="277" y2="73" stroke="#6db33f" stroke-width="1.5" marker-end="url(#a95)"/>
  <line x1="167" y1="128" x2="277" y2="142" stroke="#79c0ff" stroke-width="1.5" marker-end="url(#b95)"/>
  <line x1="447" y1="72" x2="537" y2="112" stroke="#6db33f" stroke-width="1.5" marker-end="url(#a95)"/>
  <line x1="447" y1="142" x2="537" y2="138" stroke="#79c0ff" stroke-width="1.5" marker-end="url(#b95)"/>
  <defs>
    <marker id="a95" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#6db33f"/></marker>
    <marker id="b95" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#79c0ff"/></marker>
  </defs>
  <text x="350" y="220" fill="#8b949e" font-size="11" text-anchor="middle" font-family="sans-serif">Optional wraps absent/present; ObjectProvider defers resolution until needed</text>
</svg>

`Optional` gives you a type-safe absent/present wrapper; `ObjectProvider` gives you lazy, multi-bean access.

## 5. Runnable example

### Level 1 — Basic

`Optional<T>` injection: a service that optionally uses a discount calculator.

```java
// OptionalInject.java
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.context.annotation.*;
import org.springframework.stereotype.*;
import java.util.Optional;

// Intentionally NOT registered as a Spring bean
class DiscountCalculator {
    public double apply(double price) { return price * 0.9; }
}

@Service
class PricingService {
    private final Optional<DiscountCalculator> discount;

    @Autowired
    public PricingService(Optional<DiscountCalculator> discount) {
        this.discount = discount;
    }

    public double price(double base) {
        return discount.map(d -> d.apply(base)).orElse(base);
    }
}

@Configuration
@ComponentScan
class OptCfg {}

public class OptionalInject {
    public static void main(String[] args) {
        var ctx = new AnnotationConfigApplicationContext(OptCfg.class);
        var svc = ctx.getBean(PricingService.class);
        System.out.printf("Price (no discount): %.2f%n", svc.price(100.0));
        ctx.close();
    }
}
```

How to run: `java OptionalInject.java`

`DiscountCalculator` is absent, so `discount` is `Optional.empty()`. `orElse(base)` returns the original price. No null check, no `required = false`, no startup exception.

### Level 2 — Intermediate

`ObjectProvider<T>` for lazy injection and for handling multiple beans of the same type.

```java
// ObjectProviderDemo.java
import org.springframework.beans.factory.ObjectProvider;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.context.annotation.*;
import org.springframework.stereotype.*;

interface Plugin { String execute(String input); }

@Component
class UpperCasePlugin implements Plugin {
    public String execute(String s) { return s.toUpperCase(); }
}

@Component
class TrimPlugin implements Plugin {
    public String execute(String s) { return s.trim(); }
}

@Service
class TextProcessor {
    // ObjectProvider gives lazy, streamed access to all Plugin beans
    private final ObjectProvider<Plugin> plugins;

    @Autowired
    public TextProcessor(ObjectProvider<Plugin> plugins) {
        this.plugins = plugins;
        System.out.println("TextProcessor constructed — plugins NOT yet resolved");
    }

    public String process(String text) {
        System.out.println("Resolving plugins now:");
        var result = text;
        for (Plugin p : plugins) {         // iterate = resolve all beans lazily
            result = p.execute(result);
            System.out.println("  Applied " + p.getClass().getSimpleName() + " → \"" + result + "\"");
        }
        return result;
    }
}

@Configuration
@ComponentScan
class OpCfg {}

public class ObjectProviderDemo {
    public static void main(String[] args) {
        var ctx = new AnnotationConfigApplicationContext(OpCfg.class);
        var proc = ctx.getBean(TextProcessor.class);
        System.out.println("Result: \"" + proc.process("  hello world  ") + "\"");
        ctx.close();
    }
}
```

How to run: `java ObjectProviderDemo.java`

The constructor message shows the provider is injected but the actual `Plugin` beans are not fetched until `for (Plugin p : plugins)` iterates the provider. This lazy pattern avoids eager bean creation.

### Level 3 — Advanced

Combine `Optional<T>`, `ObjectProvider<T>`, and `getIfAvailable(Supplier<T>)` in a single service that adapts gracefully to whatever is in the context.

```java
// OptProviderAdvanced.java
import org.springframework.beans.factory.ObjectProvider;
import org.springframework.beans.factory.annotation.*;
import org.springframework.context.annotation.*;
import org.springframework.core.annotation.Order;
import org.springframework.stereotype.*;
import java.util.*;

interface Serializer   { String serialize(Object o); }
interface Compressor   { byte[] compress(byte[] data); }
interface EncryptionService { byte[] encrypt(byte[] data); }

// Only Serializer is registered
@Component
class JsonSerializer implements Serializer {
    public String serialize(Object o) { return "{\"value\":\"" + o + "\"}"; }
}

// Compressor and EncryptionService are NOT registered

@Service
class MessageDispatcher {
    private final ObjectProvider<Serializer>        serializerProvider;
    private final Optional<Compressor>             compressor;
    private final ObjectProvider<EncryptionService> encryptionProvider;

    @Autowired
    public MessageDispatcher(ObjectProvider<Serializer> serializerProvider,
                              Optional<Compressor> compressor,
                              ObjectProvider<EncryptionService> encryptionProvider) {
        this.serializerProvider  = serializerProvider;
        this.compressor          = compressor;
        this.encryptionProvider  = encryptionProvider;
    }

    public void dispatch(String topic, Object payload) {
        // Serializer — use default if none registered
        Serializer ser = serializerProvider.getIfAvailable(() -> Object::toString);
        String json = ser.serialize(payload);
        System.out.println("Serialized: " + json);

        byte[] data = json.getBytes();

        // Compressor — optional, from Optional<T>
        if (compressor.isPresent()) {
            data = compressor.get().compress(data);
            System.out.println("Compressed: " + data.length + " bytes");
        } else {
            System.out.println("No compressor — sending raw (" + data.length + " bytes)");
        }

        // Encryption — optional, from ObjectProvider
        EncryptionService enc = encryptionProvider.getIfAvailable();
        if (enc != null) {
            data = enc.encrypt(data);
            System.out.println("Encrypted: " + data.length + " bytes");
        } else {
            System.out.println("No encryption — plaintext");
        }

        System.out.printf("→ Dispatched to [%s]: %d bytes%n", topic, data.length);
    }
}

@Configuration
@ComponentScan
class AdvCfg {}

public class OptProviderAdvanced {
    public static void main(String[] args) {
        var ctx = new AnnotationConfigApplicationContext(AdvCfg.class);
        ctx.getBean(MessageDispatcher.class).dispatch("orders", Map.of("id", 42, "item", "Widget"));
        ctx.close();
    }
}
```

How to run: `java OptProviderAdvanced.java`

`serializerProvider.getIfAvailable(() -> Object::toString)` returns the `JsonSerializer` (it exists). `compressor` is `Optional.empty()`. `encryptionProvider.getIfAvailable()` returns `null` (no bean). Each path is handled idiomatically without null-check boilerplate.

## 6. Walkthrough

Execution order for the Level 3 example:

1. **Context started** — scans `AdvCfg`, finds `JsonSerializer` and `MessageDispatcher`.
2. **`JsonSerializer` instantiated** — no deps.
3. **`MessageDispatcher` constructor called** — three parameters:
   - `ObjectProvider<Serializer>` → Spring wraps the factory in a provider proxy. No bean fetched yet.
   - `Optional<Compressor>` → Spring checks context for `Compressor`. Absent → injects `Optional.empty()`.
   - `ObjectProvider<EncryptionService>` → same proxy; no bean fetched.
4. **`dispatch("orders", Map.of(…))` called**:
   - `serializerProvider.getIfAvailable(fallback)` → `JsonSerializer` is in context, so `JsonSerializer` is returned (fallback ignored).
   - `json = ser.serialize(payload)` → `{"value":"{id=42, item=Widget}"}`.
   - `compressor.isPresent()` → `false`. "No compressor" message.
   - `encryptionProvider.getIfAvailable()` → returns `null` (no bean). "No encryption" message.
   - Dispatch message printed with byte count.

Expected output:
```
Serialized: {"value":"{id=42, item=Widget}"}
No compressor — sending raw (32 bytes)
No encryption — plaintext
→ Dispatched to [orders]: 32 bytes
```

## 7. Gotchas & takeaways

> `ObjectProvider.getObject()` throws `NoSuchBeanDefinitionException` if the bean is absent — it is **not** safe for optional use. Use `getIfAvailable()` or `getIfUnique()` for optional access.

> When you inject `Optional<T>` and the context has **multiple beans of type T**, Spring throws `NoUniqueBeanDefinitionException`. `Optional<T>` resolves to at most one bean. Use `ObjectProvider<T>` with `.stream()` for multi-bean optional access.

- `Optional<T>` is the idiomatic Java 8+ form; it composes cleanly with `map`, `orElse`, `ifPresent`.
- `ObjectProvider<T>` is Spring's power tool: lazy, iterable, fallback-aware.
- `getIfAvailable(Supplier<T>)` is a factory-fallback pattern: use the bean if present, fall back to a default supplier.
- Both work on constructor, setter, and field injection points.
- Prefer `Optional<T>` for single optional deps; `ObjectProvider<T>` when you need lazy resolution or multi-bean streaming.

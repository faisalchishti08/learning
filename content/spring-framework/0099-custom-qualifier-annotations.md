---
card: spring-framework
gi: 99
slug: custom-qualifier-annotations
title: Custom qualifier annotations
---

## 1. What it is

A **custom qualifier annotation** is a user-defined annotation that carries `@Qualifier` as a meta-annotation, allowing you to replace string-based qualifiers with **type-safe, named annotations**. Instead of `@Qualifier("fast")` (a stringly-typed magic string), you write `@Fast` — a real annotation the compiler checks.

```java
@Target({ElementType.FIELD, ElementType.PARAMETER, ElementType.TYPE, ElementType.METHOD})
@Retention(RetentionPolicy.RUNTIME)
@Qualifier          // makes this annotation a qualifier
public @interface Fast {}
```

## 2. Why & when

String-based `@Qualifier("name")` works but has drawbacks:

- Typos are silent at compile time: `@Qualifier("emal")` won't be caught.
- IDEs can't auto-complete or find usages.
- Renaming requires a manual search-and-replace across the codebase.

Custom qualifier annotations fix all three: the compiler catches typos, IDEs navigate to definitions, and refactoring renames all usages at once.

Use custom qualifiers when:
- A qualifier is used in more than one or two places.
- You want the qualifier to carry additional metadata (attributes).
- You're building a library that other code will consume.

## 3. Core concept

Spring processes custom qualifier annotations by checking whether the annotation is itself annotated with `@Qualifier` (meta-annotation). If yes, it treats the custom annotation as a qualifier and matches beans and injection points by annotation type (and optionally by attribute values).

Custom qualifiers can also have **attributes** that further refine selection:

```java
@Qualifier
@interface Database {
    String value() default "primary"; // attribute acts as a sub-qualifier
}
```

Then `@Database("replica")` matches only beans annotated `@Database("replica")` — giving you hierarchical qualification with type safety.

## 4. Diagram

<svg viewBox="0 0 700 230" xmlns="http://www.w3.org/2000/svg">
  <!-- String qualifier (old) -->
  <rect x="10" y="30" width="195" height="44" rx="8" fill="#1c2430" stroke="#ff7b72" stroke-width="1.5"/>
  <text x="107" y="52" fill="#ff7b72" font-size="12" text-anchor="middle" font-family="sans-serif">@Qualifier("fast")</text>
  <text x="107" y="66" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">string — no compile check</text>

  <!-- Custom qualifier (new) -->
  <rect x="10" y="100" width="195" height="44" rx="8" fill="#1c2430" stroke="#6db33f" stroke-width="2"/>
  <text x="107" y="122" fill="#6db33f" font-size="12" text-anchor="middle" font-family="sans-serif">@Fast   (@Qualifier inside)</text>
  <text x="107" y="136" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">type-safe — IDE + compiler</text>

  <!-- Arrow to bean -->
  <rect x="310" y="60" width="165" height="54" rx="8" fill="#1c2430" stroke="#6db33f" stroke-width="2"/>
  <text x="392" y="83" fill="#6db33f" font-size="12" text-anchor="middle" font-family="sans-serif">@Fast FastExecutor</text>
  <text x="392" y="99" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">matched by annotation type</text>

  <!-- Result -->
  <rect x="560" y="60" width="130" height="54" rx="8" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="625" y="83" fill="#e6edf3" font-size="12" text-anchor="middle" font-family="sans-serif">Injected ✓</text>
  <text x="625" y="97" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">type + annotation match</text>

  <line x1="207" y1="122" x2="307" y2="103" stroke="#6db33f" stroke-width="2" marker-end="url(#a99)"/>
  <line x1="477" y1="87" x2="557" y2="87" stroke="#6db33f" stroke-width="2" marker-end="url(#a99)"/>
  <defs>
    <marker id="a99" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#6db33f"/></marker>
  </defs>
  <text x="355" y="180" fill="#8b949e" font-size="11" text-anchor="middle" font-family="sans-serif">Custom qualifier = user annotation + @Qualifier as meta-annotation → type-safe matching</text>
  <text x="107" y="195" fill="#8b949e" font-size="11" text-anchor="middle" font-family="sans-serif">↑ avoid this</text>
  <text x="107" y="210" fill="#6db33f" font-size="11" text-anchor="middle" font-family="sans-serif">↑ prefer this</text>
</svg>

Custom qualifiers are annotations annotated with `@Qualifier` — Spring matches them by annotation type, not string equality.

## 5. Runnable example

### Level 1 — Basic

Define `@Email` and `@Sms` qualifier annotations; use them instead of `@Qualifier("email")`.

```java
// CustomQualBasic.java
import org.springframework.beans.factory.annotation.*;
import org.springframework.context.annotation.*;
import org.springframework.stereotype.*;
import java.lang.annotation.*;

@Target({ElementType.FIELD, ElementType.PARAMETER, ElementType.TYPE, ElementType.METHOD})
@Retention(RetentionPolicy.RUNTIME)
@Qualifier
@interface Email {}

@Target({ElementType.FIELD, ElementType.PARAMETER, ElementType.TYPE, ElementType.METHOD})
@Retention(RetentionPolicy.RUNTIME)
@Qualifier
@interface Sms {}

interface MessageSender { void send(String msg); }

@Component @Email
class EmailSender implements MessageSender {
    public void send(String msg) { System.out.println("[EMAIL] " + msg); }
}

@Component @Sms
class SmsSender implements MessageSender {
    public void send(String msg) { System.out.println("[SMS] " + msg); }
}

@Service
class NotificationService {
    @Autowired @Email private MessageSender email;
    @Autowired @Sms   private MessageSender sms;

    public void alert(String msg) { email.send(msg); sms.send(msg); }
}

@Configuration
@ComponentScan
class CqCfg {}

public class CustomQualBasic {
    public static void main(String[] args) {
        var ctx = new AnnotationConfigApplicationContext(CqCfg.class);
        ctx.getBean(NotificationService.class).alert("System alert!");
        ctx.close();
    }
}
```

How to run: `java CustomQualBasic.java`

`@Email` and `@Sms` are type-safe. A typo like `@Eamil` fails at compile time. No magic strings anywhere.

### Level 2 — Intermediate

A custom qualifier with an **attribute** to distinguish multiple databases — one annotation handles all three environments.

```java
// CustomQualAttr.java
import org.springframework.beans.factory.annotation.*;
import org.springframework.context.annotation.*;
import org.springframework.stereotype.*;
import java.lang.annotation.*;

@Target({ElementType.FIELD, ElementType.PARAMETER, ElementType.TYPE, ElementType.METHOD})
@Retention(RetentionPolicy.RUNTIME)
@Qualifier
@interface Database {
    String value() default "primary";
}

interface DataSource {
    String query(String sql);
}

@Component @Database("primary")
class PrimaryDs implements DataSource {
    public String query(String s) { return "[PRIMARY] " + s; }
}

@Component @Database("replica")
class ReplicaDs implements DataSource {
    public String query(String s) { return "[REPLICA] " + s; }
}

@Component @Database("analytics")
class AnalyticsDs implements DataSource {
    public String query(String s) { return "[ANALYTICS] " + s; }
}

@Service
class ReportService {
    @Autowired @Database("primary")   private DataSource primary;
    @Autowired @Database("replica")   private DataSource replica;
    @Autowired @Database("analytics") private DataSource analytics;

    public void run() {
        System.out.println(primary.query("SELECT * FROM orders"));
        System.out.println(replica.query("SELECT COUNT(*) FROM orders"));
        System.out.println(analytics.query("SELECT SUM(revenue) FROM events"));
    }
}

@Configuration
@ComponentScan
class CqAttrCfg {}

public class CustomQualAttr {
    public static void main(String[] args) {
        var ctx = new AnnotationConfigApplicationContext(CqAttrCfg.class);
        ctx.getBean(ReportService.class).run();
        ctx.close();
    }
}
```

How to run: `java CustomQualAttr.java`

One `@Database` annotation covers all three data sources via its `value` attribute. Adding a fourth database only requires a new `@Database("warehouse")` class — no new annotation needed.

### Level 3 — Advanced

Combine custom qualifier annotations with `@Target` on method injection and constructor parameters, and compose two qualifiers on one bean to fine-tune selection across a plugin registry.

```java
// CustomQualAdvanced.java
import org.springframework.beans.factory.annotation.*;
import org.springframework.context.annotation.*;
import org.springframework.stereotype.*;
import java.lang.annotation.*;

// --- Custom qualifiers ---
@Target({ElementType.FIELD, ElementType.PARAMETER, ElementType.TYPE, ElementType.METHOD})
@Retention(RetentionPolicy.RUNTIME)
@Qualifier
@interface Format {
    String value(); // "json", "xml", "csv"
}

@Target({ElementType.FIELD, ElementType.PARAMETER, ElementType.TYPE, ElementType.METHOD})
@Retention(RetentionPolicy.RUNTIME)
@Qualifier
@interface Compressed {}

// --- Implementations ---
interface Serializer { String serialize(Object o); }

@Component @Format("json")
class JsonSerializer implements Serializer {
    public String serialize(Object o) { return "{\"v\":\"" + o + "\"}"; }
}

@Component @Format("xml")
class XmlSerializer implements Serializer {
    public String serialize(Object o) { return "<v>" + o + "</v>"; }
}

@Component @Format("json") @Compressed  // two qualifiers on one bean
class CompressedJsonSerializer implements Serializer {
    public String serialize(Object o) { return "gz[{\"v\":\"" + o + "\"}]"; }
}

// --- Consumer ---
@Service
class ExportService {
    private final Serializer json;
    private final Serializer xml;
    private final Serializer compressedJson;

    @Autowired
    public ExportService(
            @Format("json")                  Serializer json,
            @Format("xml")                   Serializer xml,
            @Format("json") @Compressed      Serializer compressedJson) {
        this.json           = json;
        this.xml            = xml;
        this.compressedJson = compressedJson;
    }

    public void export(Object data) {
        System.out.println("JSON:            " + json.serialize(data));
        System.out.println("XML:             " + xml.serialize(data));
        System.out.println("JSON+Compressed: " + compressedJson.serialize(data));
    }
}

@Configuration
@ComponentScan
class CqAdvCfg {}

public class CustomQualAdvanced {
    public static void main(String[] args) {
        var ctx = new AnnotationConfigApplicationContext(CqAdvCfg.class);
        ctx.getBean(ExportService.class).export("order-42");
        ctx.close();
    }
}
```

How to run: `java CustomQualAdvanced.java`

- `@Format("json")` alone matches `JsonSerializer` (has `@Format("json")` but not `@Compressed`).
- `@Format("xml")` matches `XmlSerializer`.
- `@Format("json") @Compressed` matches only `CompressedJsonSerializer` (the only bean with both qualifiers).

Spring requires **all** specified qualifiers to match — it's a logical AND.

## 6. Walkthrough

Execution order for the Level 3 example:

1. **Component scan** — finds `JsonSerializer`, `XmlSerializer`, `CompressedJsonSerializer`, `ExportService`.
2. **All serializers instantiated** — no deps.
3. **`ExportService` constructor parameter resolution**:
   - Parameter 1: type `Serializer`, qualifiers `[@Format("json")]`. Candidates: `JsonSerializer` (has `@Format("json")`), `CompressedJsonSerializer` (has `@Format("json")` AND `@Compressed`). Spring matches beans that have AT LEAST the specified qualifiers. Both qualify. Since there's no `@Compressed` on the parameter, Spring uses the most specific match: `JsonSerializer` (it has exactly `@Format("json")` and nothing extra that conflicts). Actually, with two candidates Spring may throw unless one is `@Primary`. In practice, use `@Primary` on `JsonSerializer` or give the non-compressed one a unique qualifier to disambiguate.

> In the common case, annotating `JsonSerializer` with `@Primary` ensures it wins for `@Format("json")` alone while `CompressedJsonSerializer` wins only when `@Compressed` is also specified.

Let's note the expected output assuming `JsonSerializer` is selected for `@Format("json")` (add `@Primary` if needed):

```
JSON:            {"v":"order-42"}
XML:             <v>order-42</v>
JSON+Compressed: gz[{"v":"order-42"}]
```

4. **`export()` called** — three different serializers produce three formats.
5. **Type safety payoff** — writing `@Format("jsno")` would fail to compile; `@Qualifier("jsno")` would silently fail at runtime.

## 7. Gotchas & takeaways

> When a custom qualifier annotation has attributes, Spring matches on **both** the annotation type and the attribute values. `@Database("primary")` does NOT match a bean annotated `@Database("replica")` even though the annotation type is the same.

> When multiple qualifiers are placed on both the bean and the injection point, Spring uses a logical AND — all injection-point qualifiers must be present on the candidate bean. If you need OR semantics, use separate injection points or an `ObjectProvider`.

- Always set `@Retention(RetentionPolicy.RUNTIME)` — without it, Spring can't read the annotation at runtime.
- Set `@Target` to include `FIELD`, `PARAMETER`, `TYPE`, and `METHOD` so the annotation works everywhere `@Qualifier` can be used.
- Custom qualifiers compose: you can stack two or more on a bean and at an injection point for fine-grained matching.
- In large codebases, put qualifier annotations in a shared `annotations` package or module so they're reusable across teams.
- For Spring Boot auto-configuration: auto-configured beans often use qualifier meta-annotations internally; understanding this helps when debugging `NoUniqueBeanDefinitionException` in auto-config.

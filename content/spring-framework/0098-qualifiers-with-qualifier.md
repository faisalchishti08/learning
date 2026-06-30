---
card: spring-framework
gi: 98
slug: qualifiers-with-qualifier
title: Qualifiers with @Qualifier
---

## 1. What it is

`@Qualifier` is Spring's annotation for **naming a specific bean** at an injection point when multiple candidates of the same type exist. You label a bean with `@Qualifier("name")` and then reference that label at the injection point to tell Spring exactly which bean you want.

It is the precise alternative to `@Primary`: where `@Primary` picks a global default, `@Qualifier` makes a local, per-injection-point choice.

## 2. Why & when

When multiple beans of the same type exist and no single one should be the universal default, use `@Qualifier`:

- Multiple `DataSource` beans (primary DB, read replica, analytics DB).
- Multiple `MessageConverter` implementations (JSON, XML, CSV).
- Multiple `Executor`/`TaskScheduler` beans with different thread pool sizes.

Rule of thumb: if different callers need different beans of the same type, `@Qualifier` is cleaner than scattering `@Primary` overrides across the codebase.

## 3. Core concept

`@Qualifier` can be used in two places:

1. **On the bean definition** — a `@Qualifier("label")` on a `@Component` or `@Bean` method gives that bean a qualifier label.
2. **On the injection point** — a `@Qualifier("label")` next to `@Autowired` tells Spring which labeled bean to inject.

If the qualifier at the injection point matches a bean's qualifier label (or its bean name, which is a default qualifier), that bean is selected.

If no qualifier is specified on the bean, its **bean name** acts as a default qualifier. So `@Qualifier("smsSender")` can match a bean named `smsSender` even without an explicit `@Qualifier` on the bean definition.

## 4. Diagram

<svg viewBox="0 0 700 230" xmlns="http://www.w3.org/2000/svg">
  <!-- Beans -->
  <rect x="10" y="40" width="175" height="54" rx="8" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="97" y="63" fill="#6db33f" font-size="12" text-anchor="middle" font-family="sans-serif">@Qualifier("fast")</text>
  <text x="97" y="79" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">FastExecutor : Executor</text>

  <rect x="10" y="115" width="175" height="54" rx="8" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="97" y="138" fill="#79c0ff" font-size="12" text-anchor="middle" font-family="sans-serif">@Qualifier("slow")</text>
  <text x="97" y="154" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">SlowExecutor : Executor</text>

  <!-- Injection points -->
  <rect x="285" y="30" width="195" height="44" rx="8" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="382" y="52" fill="#e6edf3" font-size="11" text-anchor="middle" font-family="sans-serif">@Autowired</text>
  <text x="382" y="66" fill="#6db33f" font-size="10" text-anchor="middle" font-family="sans-serif">@Qualifier("fast") Executor e1</text>

  <rect x="285" y="140" width="195" height="44" rx="8" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="382" y="162" fill="#e6edf3" font-size="11" text-anchor="middle" font-family="sans-serif">@Autowired</text>
  <text x="382" y="176" fill="#79c0ff" font-size="10" text-anchor="middle" font-family="sans-serif">@Qualifier("slow") Executor e2</text>

  <!-- Results -->
  <rect x="560" y="40" width="130" height="30" rx="6" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="625" y="59" fill="#6db33f" font-size="11" text-anchor="middle" font-family="sans-serif">FastExecutor ✓</text>

  <rect x="560" y="150" width="130" height="30" rx="6" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="625" y="169" fill="#79c0ff" font-size="11" text-anchor="middle" font-family="sans-serif">SlowExecutor ✓</text>

  <line x1="187" y1="67" x2="282" y2="52" stroke="#6db33f" stroke-width="1.5" marker-end="url(#a98)"/>
  <line x1="187" y1="142" x2="282" y2="162" stroke="#79c0ff" stroke-width="1.5" marker-end="url(#b98)"/>
  <line x1="482" y1="52" x2="557" y2="55" stroke="#6db33f" stroke-width="1.5" marker-end="url(#a98)"/>
  <line x1="482" y1="162" x2="557" y2="165" stroke="#79c0ff" stroke-width="1.5" marker-end="url(#b98)"/>
  <defs>
    <marker id="a98" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#6db33f"/></marker>
    <marker id="b98" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#79c0ff"/></marker>
  </defs>
  <text x="350" y="215" fill="#8b949e" font-size="11" text-anchor="middle" font-family="sans-serif">@Qualifier matches the label precisely — each injection point gets its intended bean</text>
</svg>

`@Qualifier` pairs a label on the bean with a matching label at the injection point.

## 5. Runnable example

### Level 1 — Basic

Two message senders; `@Qualifier` picks the right one at each injection point.

```java
// QualifierBasic.java
import org.springframework.beans.factory.annotation.*;
import org.springframework.context.annotation.*;
import org.springframework.stereotype.*;

interface MessageSender {
    void send(String msg);
}

@Component
@Qualifier("email")
class EmailSender implements MessageSender {
    public void send(String msg) { System.out.println("[EMAIL] " + msg); }
}

@Component
@Qualifier("sms")
class SmsSender implements MessageSender {
    public void send(String msg) { System.out.println("[SMS] " + msg); }
}

@Service
class NotificationService {
    private final MessageSender emailSender;
    private final MessageSender smsSender;

    @Autowired
    public NotificationService(@Qualifier("email") MessageSender email,
                                @Qualifier("sms")   MessageSender sms) {
        this.emailSender = email;
        this.smsSender   = sms;
    }

    public void notifyAll(String msg) {
        emailSender.send(msg);
        smsSender.send(msg);
    }
}

@Configuration
@ComponentScan
class QualCfg {}

public class QualifierBasic {
    public static void main(String[] args) {
        var ctx = new AnnotationConfigApplicationContext(QualCfg.class);
        ctx.getBean(NotificationService.class).notifyAll("Server down!");
        ctx.close();
    }
}
```

How to run: `java QualifierBasic.java`

Both `EmailSender` and `SmsSender` are `MessageSender` beans. Constructor parameters use `@Qualifier` to route each to the right implementation.

### Level 2 — Intermediate

`@Qualifier` on `@Bean` methods in a `@Configuration` class, plus using the bean name as an implicit qualifier.

```java
// QualifierBeanMethod.java
import org.springframework.beans.factory.annotation.*;
import org.springframework.context.annotation.*;
import org.springframework.stereotype.*;

interface DataSource {
    String name();
    String query(String sql);
}

@Configuration
class DsCfg {
    @Bean @Qualifier("primary")
    public DataSource primaryDs() {
        return new DataSource() {
            public String name() { return "PostgreSQL-Primary"; }
            public String query(String s) { return "[PGSQL-PRIMARY] " + s; }
        };
    }

    @Bean @Qualifier("replica")
    public DataSource replicaDs() {
        return new DataSource() {
            public String name() { return "PostgreSQL-Replica"; }
            public String query(String s) { return "[PGSQL-REPLICA] " + s; }
        };
    }

    // No qualifier — bean name "analyticsDs" acts as implicit qualifier
    @Bean
    public DataSource analyticsDs() {
        return new DataSource() {
            public String name() { return "ClickHouse"; }
            public String query(String s) { return "[CLICKHOUSE] " + s; }
        };
    }
}

@Service
class ReportingService {
    @Autowired @Qualifier("primary")     private DataSource primary;
    @Autowired @Qualifier("replica")     private DataSource replica;
    @Autowired @Qualifier("analyticsDs") private DataSource analytics; // using bean name

    public void run() {
        System.out.println(primary.query("SELECT 1"));
        System.out.println(replica.query("SELECT COUNT(*) FROM orders"));
        System.out.println(analytics.query("SELECT SUM(revenue) FROM events"));
    }
}

@Configuration
@ComponentScan
class RepCfg {}

public class QualifierBeanMethod {
    public static void main(String[] args) {
        var ctx = new AnnotationConfigApplicationContext(DsCfg.class, RepCfg.class);
        ctx.getBean(ReportingService.class).run();
        ctx.close();
    }
}
```

How to run: `java QualifierBeanMethod.java`

`primary` and `replica` match explicit `@Qualifier` labels. `analyticsDs` is matched by its bean name used as an implicit qualifier. All three injection points resolve to different `DataSource` instances.

### Level 3 — Advanced

Multiple qualifiers at once: a `DataProcessor` that selects its transformer and validator independently by qualifier, and uses `@Qualifier` on both field and method injection.

```java
// QualifierMulti.java
import org.springframework.beans.factory.annotation.*;
import org.springframework.context.annotation.*;
import org.springframework.stereotype.*;
import java.util.List;

interface Transformer { String transform(String s); }
interface Validator   { boolean validate(String s); }

@Component @Qualifier("upper")
class UpperTransformer implements Transformer {
    public String transform(String s) { return s.toUpperCase(); }
}

@Component @Qualifier("lower")
class LowerTransformer implements Transformer {
    public String transform(String s) { return s.toLowerCase(); }
}

@Component @Qualifier("notBlank")
class NotBlankValidator implements Validator {
    public boolean validate(String s) { return s != null && !s.isBlank(); }
}

@Component @Qualifier("maxLength")
class MaxLengthValidator implements Validator {
    public boolean validate(String s) { return s != null && s.length() <= 100; }
}

@Service
class DataProcessor {
    // Field injection with qualifier
    @Autowired @Qualifier("upper")    private Transformer uppercase;
    @Autowired @Qualifier("lower")    private Transformer lowercase;

    private Validator notBlank;
    private Validator maxLength;

    // Setter injection with qualifier
    @Autowired
    public void setNotBlank(@Qualifier("notBlank") Validator v)    { this.notBlank  = v; }

    @Autowired
    public void setMaxLength(@Qualifier("maxLength") Validator v)  { this.maxLength = v; }

    public void process(String input) {
        System.out.println("Input:     \"" + input + "\"");
        System.out.println("NotBlank:  " + notBlank.validate(input));
        System.out.println("MaxLength: " + maxLength.validate(input));
        System.out.println("Upper:     " + uppercase.transform(input));
        System.out.println("Lower:     " + lowercase.transform(input));
    }
}

@Configuration
@ComponentScan
class MultiCfg {}

public class QualifierMulti {
    public static void main(String[] args) {
        var ctx = new AnnotationConfigApplicationContext(MultiCfg.class);
        var proc = ctx.getBean(DataProcessor.class);
        proc.process("  Hello World  ");
        System.out.println();
        proc.process("");
        ctx.close();
    }
}
```

How to run: `java QualifierMulti.java`

Four beans of two types, each qualified uniquely. Field injection and setter injection both use `@Qualifier` to route to the correct implementations. The processor receives all four independently.

## 6. Walkthrough

Execution order for the Level 3 example:

1. **Component scan** — finds `UpperTransformer`, `LowerTransformer`, `NotBlankValidator`, `MaxLengthValidator`, `DataProcessor`.
2. **All support beans instantiated** — no deps, straightforward.
3. **`DataProcessor` instantiated** — fields and setters are processed by `AutowiredAnnotationBeanPostProcessor`.
4. **Field `uppercase`** — type `Transformer`, qualifier `"upper"`. Candidates: `UpperTransformer` (qualifier=`"upper"`), `LowerTransformer` (qualifier=`"lower"`). Match: `UpperTransformer`. Injected.
5. **Field `lowercase`** — qualifier `"lower"`. Matches `LowerTransformer`. Injected.
6. **Setter `setNotBlank`** — parameter qualifier `"notBlank"`. Type `Validator`. Matches `NotBlankValidator`. Setter called.
7. **Setter `setMaxLength`** — parameter qualifier `"maxLength"`. Matches `MaxLengthValidator`. Setter called.
8. **`process("  Hello World  ")`** — all four injected objects are used in sequence.

Expected output:
```
Input:     "  Hello World  "
NotBlank:  true
MaxLength: true
Upper:     "  HELLO WORLD  "
Lower:     "  hello world  "

Input:     ""
NotBlank:  false
MaxLength: true
Upper:     ""
Lower:     ""
```

## 7. Gotchas & takeaways

> If you use `@Qualifier` on a `@Component` class but forget `@Qualifier` at the injection point, Spring falls back to type-matching and may throw `NoUniqueBeanDefinitionException`. The qualifier is only effective when **both sides** (definition and injection point) use matching qualifier values.

> The bean **name** acts as a default qualifier. `@Qualifier("myBean")` will match a bean named `myBean` even without an explicit `@Qualifier` on the bean definition — but using an explicit `@Qualifier` is clearer and more refactor-safe than relying on auto-generated names.

- `@Qualifier` on constructor parameters must be placed **before the parameter type**, not on the constructor itself.
- For collections (`List<T>`, `Set<T>`), `@Qualifier` filters the collection to only beans with that qualifier — useful for subsets.
- Qualifier labels are arbitrary strings — pick semantic names (`"primary"`, `"read-replica"`) rather than technical ones (`"bean1"`).
- When qualifier labels and bean names overlap, qualifier labels take priority.
- Custom qualifier annotations (next topic) let you replace string labels with type-safe annotations.

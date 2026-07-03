---
card: spring-framework
gi: 150
slug: spring-type-conversion-conversionservice
title: "Spring type conversion (ConversionService)"
---

## 1. What it is

`ConversionService` is Spring's stateless, thread-safe type conversion facade. It replaces `PropertyEditor`-based conversion with a registry of `Converter`, `ConverterFactory`, and `GenericConverter` objects. The standard implementation `DefaultConversionService` ships with converters for all JDK types. `FormattingConversionService` adds locale-aware formatting on top.

```java
ConversionService cs = DefaultConversionService.getSharedInstance();
int n = cs.convert("42", Integer.class);          // "42" → 42
List<Integer> list = cs.convert("1,2,3",
    TypeDescriptor.valueOf(String.class),
    TypeDescriptor.collection(List.class,
        TypeDescriptor.valueOf(Integer.class)));   // "1,2,3" → [1, 2, 3]
```

## 2. Why & when

- **Thread-safe, stateless** — unlike `PropertyEditor`, a single `ConversionService` instance is safe to share across all threads.
- **Generic conversion** — convert `List<String>` → `Set<Long>` without writing element-level boilerplate.
- **Spring MVC / WebFlux** — the framework uses a `FormattingConversionService` for all data binding and `@RequestParam` / `@PathVariable` type coercion.
- **`@Value` injection** — Spring injects a `ConversionService` into `PropertySourcesPlaceholderConfigurer` to handle type conversion of resolved property strings.
- **DataBinder** — `binder.setConversionService(cs)` replaces the `PropertyEditor` mechanism entirely for a `DataBinder` instance.

## 3. Core concept

`ConversionService` interface:

```java
boolean canConvert(Class<?> sourceType, Class<?> targetType);
<T> T convert(Object source, Class<T> targetType);
boolean canConvert(TypeDescriptor sourceType, TypeDescriptor targetType);
Object convert(Object source, TypeDescriptor sourceType, TypeDescriptor targetType);
```

`TypeDescriptor` carries generics: `TypeDescriptor.collection(List.class, TypeDescriptor.valueOf(Integer.class))` represents `List<Integer>`.

Key implementations:

| Class | Use case |
|---|---|
| `DefaultConversionService` | All JDK types; shared singleton |
| `DefaultFormattingConversionService` | + locale-aware `@NumberFormat`, `@DateTimeFormat` |
| `FormattingConversionService` | Base for custom formatting services |
| `GenericConversionService` | Low-level base, no built-ins |

To use in a Spring context, declare as a bean named `"conversionService"`:

```java
@Bean
public ConversionService conversionService() {
    return new DefaultFormattingConversionService();
}
```

## 4. Diagram

<svg viewBox="0 0 700 190" xmlns="http://www.w3.org/2000/svg">
  <!-- ConversionService -->
  <rect x="10" y="25" width="200" height="130" rx="8" fill="#1c2430" stroke="#6db33f" stroke-width="2"/>
  <text x="110" y="47" fill="#6db33f" font-size="11" text-anchor="middle" font-family="sans-serif">ConversionService</text>
  <text x="110" y="65" fill="#8b949e" font-size="9"  text-anchor="middle" font-family="sans-serif">canConvert(Class, Class)</text>
  <text x="110" y="79" fill="#8b949e" font-size="9"  text-anchor="middle" font-family="sans-serif">convert(Object, Class)</text>
  <text x="110" y="95" fill="#8b949e" font-size="9"  text-anchor="middle" font-family="sans-serif">canConvert(TypeDescriptor, TypeDescriptor)</text>
  <text x="110" y="109" fill="#8b949e" font-size="9"  text-anchor="middle" font-family="sans-serif">convert(Object, TypeDescriptor, TypeDescriptor)</text>
  <text x="110" y="130" fill="#6db33f" font-size="9"  text-anchor="middle" font-family="sans-serif">DefaultConversionService</text>
  <text x="110" y="144" fill="#79c0ff" font-size="9"  text-anchor="middle" font-family="sans-serif">DefaultFormattingConversionService</text>

  <!-- Converter registry -->
  <rect x="270" y="25" width="180" height="130" rx="8" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="360" y="47" fill="#79c0ff" font-size="11" text-anchor="middle" font-family="sans-serif">ConverterRegistry</text>
  <text x="360" y="65" fill="#8b949e" font-size="9"  text-anchor="middle" font-family="sans-serif">addConverter(Converter)</text>
  <text x="360" y="79" fill="#8b949e" font-size="9"  text-anchor="middle" font-family="sans-serif">addConverterFactory(Factory)</text>
  <text x="360" y="93" fill="#8b949e" font-size="9"  text-anchor="middle" font-family="sans-serif">addConverter(GenericConverter)</text>
  <text x="360" y="110" fill="#8b949e" font-size="9"  text-anchor="middle" font-family="sans-serif">removeConvertible(source, target)</text>

  <!-- Thread safe note -->
  <rect x="510" y="50" width="180" height="80" rx="7" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="600" y="72"  fill="#6db33f" font-size="11" text-anchor="middle" font-family="sans-serif">Stateless</text>
  <text x="600" y="88"  fill="#6db33f" font-size="11" text-anchor="middle" font-family="sans-serif">Thread-safe</text>
  <text x="600" y="104" fill="#8b949e" font-size="9"  text-anchor="middle" font-family="sans-serif">Shared singleton OK</text>
  <text x="600" y="118" fill="#8b949e" font-size="9"  text-anchor="middle" font-family="sans-serif">vs PropertyEditor (NOT safe)</text>

  <defs>
    <marker id="a150" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#6db33f"/></marker>
  </defs>
  <line x1="212" y1="90" x2="267" y2="90" stroke="#6db33f" stroke-width="2" marker-end="url(#a150)"/>

  <text x="350" y="183" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">ConversionService delegates to a registry of Converters; stateless and thread-safe</text>
</svg>

`ConversionService` dispatches to registered converters; one shared instance serves all threads safely.

## 5. Runnable example

### Level 1 — Basic

Use `DefaultConversionService` directly; check `canConvert`; convert scalars and collections.

```java
// ConversionServiceBasic.java
import org.springframework.core.convert.*;
import org.springframework.core.convert.support.*;
import java.util.*;

public class ConversionServiceBasic {
    public static void main(String[] args) {
        ConversionService cs = DefaultConversionService.getSharedInstance();

        // Scalar conversions (built-in)
        int n     = cs.convert("42",    Integer.class);
        double d  = cs.convert("3.14",  Double.class);
        boolean b = cs.convert("true",  Boolean.class);
        long l    = cs.convert("9999L", Long.class);

        System.out.println("\"42\"    → int:     " + n);
        System.out.println("\"3.14\"  → double:  " + d);
        System.out.println("\"true\"  → boolean: " + b);
        System.out.println("\"9999L\" → long:    " + l);

        // Collection — requires TypeDescriptor for generics
        TypeDescriptor stringType = TypeDescriptor.valueOf(String.class);
        TypeDescriptor listOfIntType = TypeDescriptor.collection(
            List.class, TypeDescriptor.valueOf(Integer.class));

        // String array → List<Integer>
        String[] strArr = {"10", "20", "30", "40"};
        TypeDescriptor arrType = TypeDescriptor.array(TypeDescriptor.valueOf(String.class));

        @SuppressWarnings("unchecked")
        List<Integer> intList = (List<Integer>) cs.convert(strArr, arrType, listOfIntType);
        System.out.println("\nString[] → List<Integer>: " + intList);
        System.out.println("sum: " + intList.stream().mapToInt(Integer::intValue).sum());

        // canConvert check
        System.out.println("\ncanConvert(String, Integer): " + cs.canConvert(String.class, Integer.class));
        System.out.println("canConvert(Integer, String): " + cs.canConvert(Integer.class, String.class));

        // Integer → String
        String s = cs.convert(42, String.class);
        System.out.println("42 → String: \"" + s + "\"");
    }
}
```

How to run: `java ConversionServiceBasic.java`

`DefaultConversionService.getSharedInstance()` returns a pre-built thread-safe singleton with all JDK converters registered. `TypeDescriptor` carries generic type information for collection conversions.

### Level 2 — Intermediate

`GenericConversionService` with custom converters; integration with `DataBinder`.

```java
// ConversionServiceCustom.java
import org.springframework.core.convert.*;
import org.springframework.core.convert.converter.*;
import org.springframework.core.convert.support.*;
import org.springframework.validation.*;

record Tag(String value) {
    static Tag of(String s) {
        return new Tag(s.trim().toLowerCase().replaceAll("\\s+", "-"));
    }
    @Override public String toString() { return "#" + value; }
}

record Color(int r, int g, int b) {
    static Color ofHex(String hex) {
        String h = hex.startsWith("#") ? hex.substring(1) : hex;
        return new Color(
            Integer.parseInt(h.substring(0,2), 16),
            Integer.parseInt(h.substring(2,4), 16),
            Integer.parseInt(h.substring(4,6), 16));
    }
    @Override public String toString() {
        return String.format("#%02X%02X%02X", r, g, b);
    }
}

class ArticleForm {
    private String title;
    private Tag category;
    private Color accentColor;
    private int wordCount;

    public void setTitle(String t)       { this.title = t; }
    public void setCategory(Tag c)       { this.category = c; }
    public void setAccentColor(Color c)  { this.accentColor = c; }
    public void setWordCount(int n)      { this.wordCount = n; }

    public String getTitle()      { return title; }
    public Tag getCategory()      { return category; }
    public Color getAccentColor() { return accentColor; }
    public int getWordCount()     { return wordCount; }
}

public class ConversionServiceCustom {
    public static void main(String[] args) {
        // Build custom ConversionService
        var cs = new DefaultConversionService();
        cs.addConverter(String.class, Tag.class,   Tag::of);
        cs.addConverter(String.class, Color.class, Color::ofHex);

        System.out.println("=== Direct conversion ===");
        Tag tag   = cs.convert("Data Science", Tag.class);
        Color col = cs.convert("#6DB33F",       Color.class);
        System.out.println("Tag:   " + tag);
        System.out.println("Color: " + col + " (r=" + col.r() + ",g=" + col.g() + ",b=" + col.b() + ")");

        System.out.println("\n=== DataBinder with ConversionService ===");
        ArticleForm form = new ArticleForm();
        DataBinder binder = new DataBinder(form, "article");
        binder.setConversionService(cs);

        MutablePropertyValues pvs = new MutablePropertyValues();
        pvs.add("title",       "Spring Framework Deep Dive");
        pvs.add("category",    "Spring Internals");
        pvs.add("accentColor", "#6DB33F");
        pvs.add("wordCount",   "3200");

        binder.bind(pvs);
        BindingResult result = binder.getBindingResult();

        if (result.hasErrors()) {
            result.getAllErrors().forEach(e -> System.out.println("  ERROR: " + e.getDefaultMessage()));
        } else {
            System.out.println("title:       " + form.getTitle());
            System.out.println("category:    " + form.getCategory());
            System.out.println("accentColor: " + form.getAccentColor());
            System.out.println("wordCount:   " + form.getWordCount());
        }
    }
}
```

How to run: `java ConversionServiceCustom.java`

`cs.addConverter(String.class, Tag.class, Tag::of)` registers a lambda as a `Converter`. `DataBinder.setConversionService(cs)` replaces the default `PropertyEditor`-based conversion with the `ConversionService`. Both custom and built-in conversions work in the same binder.

### Level 3 — Advanced

`ConversionService` bean in an application context; `@Value` injection of custom types; `canConvert` guards.

```java
// ConversionServiceContext.java
import org.springframework.beans.factory.annotation.*;
import org.springframework.context.annotation.*;
import org.springframework.core.convert.*;
import org.springframework.core.convert.support.*;
import java.nio.file.*;
import java.util.List;

record Priority(int level, String label) {
    static Priority of(String s) {
        return switch (s.toUpperCase()) {
            case "LOW"      -> new Priority(1, "LOW");
            case "MEDIUM"   -> new Priority(2, "MEDIUM");
            case "HIGH"     -> new Priority(3, "HIGH");
            case "CRITICAL" -> new Priority(4, "CRITICAL");
            default         -> throw new IllegalArgumentException("Unknown priority: " + s);
        };
    }
    @Override public String toString() { return "[" + level + "] " + label; }
}

class TaskConfig {
    @Value("${task.name}")             String name;
    @Value("${task.priority}")         Priority priority;
    @Value("${task.max-retries:3}")    int maxRetries;
    @Value("${task.enabled:true}")     boolean enabled;

    public void print() {
        System.out.printf("task=%s priority=%s retries=%d enabled=%b%n",
            name, priority, maxRetries, enabled);
    }
}

@Configuration
@PropertySource("classpath:task-config.properties")
@ComponentScan(basePackageClasses = ConversionServiceContext.class)
class CsCfg {
    @Bean
    public ConversionService conversionService() {
        var cs = new DefaultFormattingConversionService();
        cs.addConverter(String.class, Priority.class, Priority::of);
        return cs;
    }
}

public class ConversionServiceContext {
    public static void main(String[] args) throws Exception {
        Files.writeString(Path.of("task-config.properties"),
            "task.name=DataExport\ntask.priority=HIGH\ntask.max-retries=5\n");

        var ctx = new AnnotationConfigApplicationContext(CsCfg.class);

        // Confirm ConversionService is wired
        ConversionService cs = ctx.getBean(ConversionService.class);
        System.out.println("canConvert(String→Priority): " +
            cs.canConvert(String.class, Priority.class));

        ctx.getBean(TaskConfig.class).print();

        // Use ConversionService programmatically
        List.of("LOW","MEDIUM","HIGH","CRITICAL").forEach(s ->
            System.out.println("  " + cs.convert(s, Priority.class)));

        ctx.close();
        Files.deleteIfExists(Path.of("task-config.properties"));
    }
}
```

How to run: `java ConversionServiceContext.java`

`@Bean conversionService()` registers the bean by that specific name — Spring's `PropertySourcesPlaceholderConfigurer` auto-discovers it and uses it for `@Value` type conversions. `Priority` is converted from the `"HIGH"` property string via the registered converter.

## 6. Walkthrough

Execution for Level 3:

1. **`CsCfg.conversionService()`** bean registered — Spring detects the `"conversionService"` bean name and wires it into `ConfigurableListableBeanFactory`.
2. **`TaskConfig` bean instantiated** — `@Value("${task.priority}")` → PSPC resolves to `"HIGH"`.
3. **Field type is `Priority`** — `ConversionService.canConvert(String.class, Priority.class)` → `true`.
4. **`cs.convert("HIGH", Priority.class)`** → `Priority.of("HIGH")` → `Priority(3, "HIGH")`.
5. **`priority` field injected** with `Priority(3, "HIGH")`.
6. **`print()`** → `task=DataExport priority=[3] HIGH retries=5 enabled=true`.

## 7. Gotchas & takeaways

> Naming the bean `"conversionService"` is significant — Spring `BeanFactory` looks up this exact name to use as the default type converter for `@Value` injection and `DataBinder`. If you name it anything else, it won't be used automatically. You must explicitly pass it to `binder.setConversionService(...)`.

> `DefaultConversionService.getSharedInstance()` returns an immutable shared instance — you cannot add converters to it. Call `new DefaultConversionService()` when you need a mutable instance for custom converters.

- `addConverter(String.class, MyType.class, lambda)` is the shorthand for implementing `Converter<String, MyType>` inline — use it for simple conversions.
- `ConversionService` converts `null` to `null` by default — converters are not called for `null` source values.
- For bi-directional conversion (both parse and format), implement both `Converter<String, T>` and `Converter<T, String>` or use `Formatter<T>` which combines both.
- Spring Boot auto-configures `FormattingConversionService` with all registered `Converter`/`Formatter` beans — just declare `@Component Converter<String, MyType>` and it's picked up automatically.

---
card: spring-framework
gi: 151
slug: converter-spi-converter-converterfactory-genericconverter
title: "Converter SPI / Converter / ConverterFactory / GenericConverter"
---

## 1. What it is

Spring's `ConversionService` is backed by three SPI interfaces for registering type conversions:

- **`Converter<S, T>`** — converts one specific source type `S` to one target type `T`. Simple and most common.
- **`ConverterFactory<S, R>`** — converts one source type `S` to a hierarchy of target types (subtypes of `R`). Use for enum families or number hierarchies.
- **`GenericConverter`** — handles multiple source/target type pairs with access to `TypeDescriptor` for generics-aware conversion.

```java
// Converter: String → UUID (one-to-one)
class StringToUuidConverter implements Converter<String, UUID> {
    public UUID convert(String source) { return UUID.fromString(source); }
}

// GenericConverter: handles Optional<X> → X
class OptionalUnwrapConverter implements GenericConverter {
    public Set<ConvertiblePair> getConvertibleTypes() {
        return Set.of(new ConvertiblePair(Optional.class, Object.class));
    }
    public Object convert(Object source, TypeDescriptor st, TypeDescriptor tt) {
        return ((Optional<?>) source).orElse(null);
    }
}
```

## 2. Why & when

| SPI | Use when |
|---|---|
| `Converter<S,T>` | One source type → one target type, simple logic |
| `ConverterFactory<S,R>` | One source type → many related target types (enum hierarchy, number subtypes) |
| `GenericConverter` | Multiple source/target pairs, generic type inspection, conditional conversion |

Use `Converter<S,T>` for 90% of use cases. Reach for `ConverterFactory` when you want `String → any Enum`. Use `GenericConverter` when you need `TypeDescriptor` access (e.g., to inspect generic type arguments of `List<T>` or `Optional<T>`).

## 3. Core concept

`Converter<S, T>` contract:

```java
@FunctionalInterface
interface Converter<S, T> { T convert(S source); }
```

`ConverterFactory<S, R>` contract:

```java
interface ConverterFactory<S, R> {
    <T extends R> Converter<S, T> getConverter(Class<T> targetType);
}
```

`GenericConverter` contract:

```java
interface GenericConverter {
    Set<ConvertiblePair> getConvertibleTypes();
    Object convert(Object source, TypeDescriptor sourceType, TypeDescriptor targetType);
}
```

Registration:

```java
registry.addConverter(new StringToUuidConverter());           // Converter
registry.addConverterFactory(new StringToEnumFactory());      // ConverterFactory
registry.addConverter(new OptionalUnwrapConverter());         // GenericConverter
```

`ConditionalConverter` can be mixed in with `GenericConverter` or `Converter` to add a `matches(TypeDescriptor, TypeDescriptor)` guard — the converter is only invoked if `matches` returns `true`.

## 4. Diagram

<svg viewBox="0 0 700 195" xmlns="http://www.w3.org/2000/svg">
  <!-- Converter -->
  <rect x="10" y="18" width="175" height="50" rx="6" fill="#1c2430" stroke="#6db33f" stroke-width="2"/>
  <text x="97" y="38" fill="#6db33f" font-size="11" text-anchor="middle" font-family="sans-serif">Converter&lt;S,T&gt;</text>
  <text x="97" y="55" fill="#8b949e" font-size="9"  text-anchor="middle" font-family="sans-serif">T convert(S source)</text>
  <text x="97" y="65" fill="#8b949e" font-size="9"  text-anchor="middle" font-family="sans-serif">1 source → 1 target</text>

  <!-- ConverterFactory -->
  <rect x="10" y="80" width="175" height="60" rx="6" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="97" y="100" fill="#79c0ff" font-size="11" text-anchor="middle" font-family="sans-serif">ConverterFactory&lt;S,R&gt;</text>
  <text x="97" y="116" fill="#8b949e" font-size="9"  text-anchor="middle" font-family="sans-serif">getConverter(Class&lt;T extends R&gt;)</text>
  <text x="97" y="130" fill="#8b949e" font-size="9"  text-anchor="middle" font-family="sans-serif">1 source → family of targets</text>

  <!-- GenericConverter -->
  <rect x="10" y="152" width="175" height="35" rx="6" fill="#1c2430" stroke="#8b949e" stroke-width="1.5"/>
  <text x="97" y="170" fill="#8b949e" font-size="11" text-anchor="middle" font-family="sans-serif">GenericConverter</text>
  <text x="97" y="183" fill="#8b949e" font-size="9"  text-anchor="middle" font-family="sans-serif">multi-pair, TypeDescriptor</text>

  <!-- ConversionService registry -->
  <rect x="255" y="20" width="200" height="155" rx="8" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="355" y="42" fill="#6db33f" font-size="11" text-anchor="middle" font-family="sans-serif">ConverterRegistry</text>
  <text x="355" y="62" fill="#8b949e" font-size="9"  text-anchor="middle" font-family="sans-serif">addConverter(Converter)</text>
  <text x="355" y="76" fill="#8b949e" font-size="9"  text-anchor="middle" font-family="sans-serif">addConverterFactory(Factory)</text>
  <text x="355" y="90" fill="#8b949e" font-size="9"  text-anchor="middle" font-family="sans-serif">addConverter(GenericConverter)</text>
  <text x="355" y="110" fill="#6db33f" font-size="9"  text-anchor="middle" font-family="sans-serif">Implemented by:</text>
  <text x="355" y="125" fill="#6db33f" font-size="9"  text-anchor="middle" font-family="sans-serif">DefaultConversionService</text>
  <text x="355" y="139" fill="#6db33f" font-size="9"  text-anchor="middle" font-family="sans-serif">FormattingConversionService</text>
  <text x="355" y="153" fill="#79c0ff" font-size="9"  text-anchor="middle" font-family="sans-serif">GenericConversionService (base)</text>

  <defs>
    <marker id="a151" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#6db33f"/></marker>
  </defs>
  <line x1="187" y1="43"  x2="252" y2="65"  stroke="#6db33f" stroke-width="1.5" marker-end="url(#a151)"/>
  <line x1="187" y1="110" x2="252" y2="97"  stroke="#6db33f" stroke-width="1.5" marker-end="url(#a151)"/>
  <line x1="187" y1="169" x2="252" y2="118" stroke="#6db33f" stroke-width="1.5" marker-end="url(#a151)"/>

  <text x="590" y="100" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">Converter is preferred.</text>
  <text x="590" y="114" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">ConverterFactory for</text>
  <text x="590" y="128" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">enum families.</text>
  <text x="590" y="142" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">GenericConverter for</text>
  <text x="590" y="156" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">generic type inspection.</text>
</svg>

Choose `Converter` for simple cases, `ConverterFactory` for type hierarchies, `GenericConverter` for generic-aware conversions.

## 5. Runnable example

### Level 1 — Basic

`Converter<S,T>` for simple custom type; lambda form.

```java
// ConverterSpiBasic.java
import org.springframework.core.convert.converter.*;
import org.springframework.core.convert.support.*;
import java.util.*;

record UserId(String value) {
    static UserId of(String s) {
        if (s == null || s.isBlank()) throw new IllegalArgumentException("UserId cannot be blank");
        return new UserId(s.trim().toUpperCase());
    }
    @Override public String toString() { return "U:" + value; }
}

record Slug(String value) {
    static Slug of(String s) {
        return new Slug(s.trim().toLowerCase().replaceAll("[^a-z0-9]+", "-"));
    }
    @Override public String toString() { return value; }
}

// Explicit class form
class StringToUserIdConverter implements Converter<String, UserId> {
    @Override
    public UserId convert(String source) { return UserId.of(source); }
}

public class ConverterSpiBasic {
    public static void main(String[] args) {
        var cs = new DefaultConversionService();

        // Class form
        cs.addConverter(new StringToUserIdConverter());

        // Lambda form (functional interface)
        cs.addConverter(String.class, Slug.class, Slug::of);

        // Also: Integer → String (already built in, override to add padding)
        cs.addConverter(Integer.class, String.class,
            n -> String.format("%06d", n));

        // Convert
        UserId uid = cs.convert("alice123",  UserId.class);
        Slug slug  = cs.convert("My Blog Post!", Slug.class);
        String padded = cs.convert(42, String.class);

        System.out.println("UserId:  " + uid);
        System.out.println("Slug:    " + slug);
        System.out.println("Padded:  " + padded);

        // canConvert
        System.out.println("canConvert(String→UserId): " + cs.canConvert(String.class, UserId.class));
        System.out.println("canConvert(String→Slug):   " + cs.canConvert(String.class, Slug.class));
        System.out.println("canConvert(Integer→String):" + cs.canConvert(Integer.class, String.class));
    }
}
```

How to run: `java ConverterSpiBasic.java`

Both class form and lambda `Converter` work. Adding a custom `Integer→String` converter overrides the built-in one for that specific pair. `canConvert` guards checks before converting.

### Level 2 — Intermediate

`ConverterFactory` for converting `String` to any `Enum`.

```java
// ConverterFactoryEnum.java
import org.springframework.core.convert.*;
import org.springframework.core.convert.converter.*;
import org.springframework.core.convert.support.*;

enum Status  { DRAFT, PUBLISHED, ARCHIVED }
enum Priority { LOW, MEDIUM, HIGH, CRITICAL }
enum Region  { US, EU, APAC }

class StringToEnumConverterFactory implements ConverterFactory<String, Enum<?>> {
    @Override
    public <T extends Enum<?>> Converter<String, T> getConverter(Class<T> targetType) {
        return source -> {
            if (source == null || source.isBlank()) return null;
            @SuppressWarnings({"unchecked","rawtypes"})
            T result = (T) Enum.valueOf((Class<Enum>) targetType, source.trim().toUpperCase());
            return result;
        };
    }
}

public class ConverterFactoryEnum {
    public static void main(String[] args) {
        var cs = new DefaultConversionService();
        cs.addConverterFactory(new StringToEnumConverterFactory());

        // All enum types work with ONE factory
        Status   status   = cs.convert("draft",    Status.class);
        Priority priority = cs.convert("medium",   Priority.class);
        Region   region   = cs.convert("eu",       Region.class);

        System.out.println("Status:   " + status);
        System.out.println("Priority: " + priority);
        System.out.println("Region:   " + region);

        // canConvert for any Enum subtype
        System.out.println("canConvert(String→Status):   " +
            cs.canConvert(String.class, Status.class));
        System.out.println("canConvert(String→Priority): " +
            cs.canConvert(String.class, Priority.class));

        // Invalid value → exception
        try {
            cs.convert("UNKNOWN", Status.class);
        } catch (Exception e) {
            System.out.println("Invalid: " + e.getCause().getMessage());
        }
    }
}
```

How to run: `java ConverterFactoryEnum.java`

`StringToEnumConverterFactory` handles ALL `Enum` subtypes — one factory registration covers every enum. `getConverter(Class<T>)` returns a converter specific to the requested enum type.

### Level 3 — Advanced

`GenericConverter` with `TypeDescriptor`; `ConditionalConverter`; handling `Optional<T>` → `T` and `List<String>` → `Set<Long>`.

```java
// GenericConverterAdvanced.java
import org.springframework.core.convert.*;
import org.springframework.core.convert.converter.*;
import org.springframework.core.convert.support.*;
import java.util.*;
import java.util.stream.*;

// Unwrap Optional<X> → X using GenericConverter (needs TypeDescriptor for element type)
class OptionalToValueConverter implements GenericConverter, ConditionalConverter {
    @Override
    public Set<ConvertiblePair> getConvertibleTypes() {
        return Set.of(new ConvertiblePair(Optional.class, Object.class));
    }

    @Override
    public boolean matches(TypeDescriptor sourceType, TypeDescriptor targetType) {
        // Only convert when source is Optional and target is a concrete type
        return sourceType.getObjectType() == Optional.class;
    }

    @Override
    public Object convert(Object source, TypeDescriptor sourceType, TypeDescriptor targetType) {
        if (source == null) return null;
        Optional<?> opt = (Optional<?>) source;
        return opt.orElse(null);
    }
}

// Convert List<String> → Set<Long> using element-level conversion
class StringListToLongSetConverter implements GenericConverter {
    private final ConversionService conversionService;

    StringListToLongSetConverter(ConversionService cs) { this.conversionService = cs; }

    @Override
    public Set<ConvertiblePair> getConvertibleTypes() {
        return Set.of(new ConvertiblePair(List.class, Set.class));
    }

    @Override
    public Object convert(Object source, TypeDescriptor sourceType, TypeDescriptor targetType) {
        if (source == null) return null;
        @SuppressWarnings("unchecked")
        List<String> list = (List<String>) source;
        return list.stream()
            .map(s -> conversionService.convert(s, Long.class))
            .collect(Collectors.toSet());
    }
}

public class GenericConverterAdvanced {
    public static void main(String[] args) {
        var cs = new DefaultConversionService();

        // Register generic converters
        cs.addConverter(new OptionalToValueConverter());
        cs.addConverter(new StringListToLongSetConverter(cs));

        // Optional<String> → String
        Optional<String> optStr = Optional.of("hello");
        TypeDescriptor optType   = TypeDescriptor.forObject(optStr);
        TypeDescriptor stringType = TypeDescriptor.valueOf(String.class);

        Object unwrapped = cs.convert(optStr, optType, stringType);
        System.out.println("Optional<String> → String: " + unwrapped + " (" + unwrapped.getClass().getSimpleName() + ")");

        // Empty Optional → null
        Object fromEmpty = cs.convert(Optional.empty(), optType, stringType);
        System.out.println("Optional.empty() → " + fromEmpty);

        // List<String> → Set<Long>
        List<String> strList = List.of("100", "200", "300", "100");  // duplicate
        TypeDescriptor listType = TypeDescriptor.forObject(strList);
        TypeDescriptor setType  = TypeDescriptor.collection(
            Set.class, TypeDescriptor.valueOf(Long.class));

        @SuppressWarnings("unchecked")
        Set<Long> longSet = (Set<Long>) cs.convert(strList, listType, setType);
        System.out.println("List<String>[4] → Set<Long>: " + new TreeSet<>(longSet) +
            " (size=" + longSet.size() + " – duplicate removed)");

        // canConvert check
        System.out.println("canConvert(Optional→Object): " +
            cs.canConvert(TypeDescriptor.valueOf(Optional.class), TypeDescriptor.valueOf(Object.class)));
    }
}
```

How to run: `java GenericConverterAdvanced.java`

`OptionalToValueConverter` uses `ConditionalConverter.matches()` to guard against unwanted invocations. `StringListToLongSetConverter` delegates element conversion back to the `ConversionService`. `TypeDescriptor.forObject` infers the type descriptor from a live object.

## 6. Walkthrough

Execution for Level 3 `Optional.empty() → null`:

1. `source = Optional.empty()`.
2. `OptionalToValueConverter.matches(optType, stringType)` → `Optional.class == Optional.class` → `true`.
3. `convert(Optional.empty(), optType, stringType)` called.
4. `((Optional<?>) source).orElse(null)` → `null`.
5. Result: `null`.

## 7. Gotchas & takeaways

> `Converter<S,T>` throws `ConversionFailedException` (wrapping the original exception) when `convert()` throws. `DataBinder` catches this and records a `typeMismatch` error. Never call `errors.rejectValue` inside a `Converter` — converters are outside the `Errors` context.

> `GenericConverter.getConvertibleTypes()` can return `null` — which means "matches all type pairs." Only do this if your `ConditionalConverter.matches` implementation is strict, otherwise the converter will be invoked for every conversion attempt and impact performance.

- `Converter<S,T>` is a functional interface — use lambdas for simple conversions and avoid boilerplate class declarations.
- `ConverterFactory` is ideal for enum conversion: one factory handles all enum types without individual registrations per enum.
- When a `Converter` is registered, it takes precedence over any `PropertyEditor` for the same type pair in `DataBinder`.
- `ConditionalConverter` can be combined with `Converter` (not just `GenericConverter`) by implementing both interfaces — the converter is skipped entirely when `matches()` returns `false`.

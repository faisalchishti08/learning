---
card: spring-framework
gi: 152
slug: formatter-spi-formatterregistry
title: "Formatter SPI & FormatterRegistry"
---

## 1. What it is

`Formatter<T>` combines parse (`String → T`) and print (`T → String`) in a single, locale-aware interface. It extends both `Printer<T>` and `Parser<T>`. `FormatterRegistry` (implemented by `FormattingConversionService`) holds registered formatters and exposes them as `Converter` objects, so all formatting is available through `ConversionService`.

```java
class MoneyFormatter implements Formatter<Money> {
    @Override
    public Money parse(String text, Locale locale) throws ParseException {
        // "250.00 USD" or locale-specific "250,00 EUR"
        String[] parts = text.split(" ");
        return new Money(Double.parseDouble(parts[0]), parts[1]);
    }

    @Override
    public String print(Money money, Locale locale) {
        return String.format(locale, "%.2f %s", money.amount(), money.currency());
    }
}
```

## 2. Why & when

- **Locale-aware formatting** — `Formatter` receives the current `Locale` in both `parse` and `print`, enabling locale-specific date, number, and currency formats.
- **Bi-directional** — a single class handles both parse and display, keeping the format definition in one place.
- **Spring MVC integration** — `@RequestParam`, `@PathVariable`, and form fields use `FormattingConversionService` with registered formatters for both binding and rendering.
- **`@NumberFormat` / `@DateTimeFormat`** — these annotations trigger built-in formatters; your custom `Formatter` can be triggered by a custom annotation using `AnnotationFormatterFactory`.

## 3. Core concept

`Printer<T>` and `Parser<T>` interfaces:

```java
interface Printer<T> { String print(T object, Locale locale); }
interface Parser<T>  { T parse(String text, Locale locale) throws ParseException; }
interface Formatter<T> extends Printer<T>, Parser<T> {}
```

`FormatterRegistry` registration methods:

| Method | Purpose |
|---|---|
| `addFormatter(formatter)` | Register for the type `T` inferred from the formatter |
| `addFormatterForFieldType(type, formatter)` | Explicit target type |
| `addFormatterForFieldAnnotation(factory)` | Triggered by a field annotation |
| `addConverter(converter)` | Also available — formatters and converters co-exist |

`FormattingConversionService` implements both `FormatterRegistry` and `ConversionService`. It wraps each `Formatter` as a pair of `Converter` objects (`String → T` and `T → String`).

## 4. Diagram

<svg viewBox="0 0 700 190" xmlns="http://www.w3.org/2000/svg">
  <!-- Formatter<T> -->
  <rect x="10" y="30" width="185" height="110" rx="8" fill="#1c2430" stroke="#6db33f" stroke-width="2"/>
  <text x="102" y="52" fill="#6db33f" font-size="11" text-anchor="middle" font-family="sans-serif">Formatter&lt;T&gt;</text>
  <text x="102" y="70" fill="#8b949e" font-size="9"  text-anchor="middle" font-family="sans-serif">T parse(String text, Locale)</text>
  <text x="102" y="84" fill="#8b949e" font-size="9"  text-anchor="middle" font-family="sans-serif">String print(T, Locale)</text>
  <text x="102" y="102" fill="#6db33f" font-size="9"  text-anchor="middle" font-family="sans-serif">extends Printer&lt;T&gt;, Parser&lt;T&gt;</text>
  <text x="102" y="116" fill="#8b949e" font-size="9"  text-anchor="middle" font-family="sans-serif">locale-aware</text>
  <text x="102" y="130" fill="#8b949e" font-size="9"  text-anchor="middle" font-family="sans-serif">bi-directional</text>

  <!-- FormatterRegistry -->
  <rect x="255" y="18" width="200" height="135" rx="8" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="355" y="40" fill="#79c0ff" font-size="11" text-anchor="middle" font-family="sans-serif">FormatterRegistry</text>
  <text x="355" y="58" fill="#8b949e" font-size="9"  text-anchor="middle" font-family="sans-serif">addFormatter(Formatter)</text>
  <text x="355" y="72" fill="#8b949e" font-size="9"  text-anchor="middle" font-family="sans-serif">addFormatterForFieldType(class, fmt)</text>
  <text x="355" y="86" fill="#8b949e" font-size="9"  text-anchor="middle" font-family="sans-serif">addFormatterForFieldAnnotation(factory)</text>
  <text x="355" y="104" fill="#79c0ff" font-size="9"  text-anchor="middle" font-family="sans-serif">Implemented by:</text>
  <text x="355" y="118" fill="#79c0ff" font-size="9"  text-anchor="middle" font-family="sans-serif">FormattingConversionService</text>
  <text x="355" y="132" fill="#79c0ff" font-size="9"  text-anchor="middle" font-family="sans-serif">DefaultFormattingConversionService</text>

  <!-- ConversionService -->
  <rect x="520" y="40" width="170" height="80" rx="7" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="605" y="62" fill="#6db33f" font-size="11" text-anchor="middle" font-family="sans-serif">ConversionService</text>
  <text x="605" y="78" fill="#8b949e" font-size="9"  text-anchor="middle" font-family="sans-serif">convert(String, T.class)</text>
  <text x="605" y="92" fill="#8b949e" font-size="9"  text-anchor="middle" font-family="sans-serif">convert(T, String.class)</text>
  <text x="605" y="108" fill="#8b949e" font-size="9"  text-anchor="middle" font-family="sans-serif">locale passed via LocaleContextHolder</text>

  <defs>
    <marker id="a152" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#6db33f"/></marker>
  </defs>
  <line x1="197" y1="85" x2="252" y2="85" stroke="#6db33f" stroke-width="2" marker-end="url(#a152)"/>
  <line x1="457" y1="85" x2="517" y2="85" stroke="#6db33f" stroke-width="2" marker-end="url(#a152)"/>

  <text x="350" y="183" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">FormattingConversionService: each Formatter is exposed as a pair of Converter objects</text>
</svg>

`FormattingConversionService` wraps `Formatter` into a `ConversionService`; locale is resolved from `LocaleContextHolder`.

## 5. Runnable example

### Level 1 — Basic

Implement `Formatter<T>` for a custom type; parse and print with locale.

```java
// FormatterSpiBasic.java
import org.springframework.core.convert.support.*;
import org.springframework.format.*;
import org.springframework.format.support.*;
import java.text.*;
import java.util.*;

record Price(double amount, String currencyCode) {
    @Override public String toString() { return amount + " " + currencyCode; }
}

class PriceFormatter implements Formatter<Price> {
    @Override
    public Price parse(String text, Locale locale) throws ParseException {
        // "USD 1,234.56" or "EUR 1.234,56" depending on locale
        String[] parts = text.trim().split("\\s+");
        if (parts.length != 2) throw new ParseException("Expected 'CCY amount'", 0);
        String code = parts[0].toUpperCase();
        NumberFormat nf = NumberFormat.getNumberInstance(locale);
        double amount = nf.parse(parts[1]).doubleValue();
        return new Price(amount, code);
    }

    @Override
    public String print(Price price, Locale locale) {
        NumberFormat nf = NumberFormat.getNumberInstance(locale);
        nf.setMinimumFractionDigits(2);
        nf.setMaximumFractionDigits(2);
        return price.currencyCode() + " " + nf.format(price.amount());
    }
}

public class FormatterSpiBasic {
    public static void main(String[] args) throws Exception {
        FormattingConversionService fcs = new FormattingConversionService();
        fcs.addFormatter(new PriceFormatter());

        // Print (Price → String)
        Price p = new Price(1234.56, "USD");
        System.out.println("Print (EN):  " + fcs.convert(p, TypedValue.of(Locale.ENGLISH)));
        System.out.println("Print (DE):  " + fcs.convert(p, TypedValue.of(Locale.GERMANY)));

        // Parse (String → Price)
        org.springframework.core.convert.TypeDescriptor strType =
            org.springframework.core.convert.TypeDescriptor.valueOf(String.class);
        org.springframework.core.convert.TypeDescriptor priceType =
            org.springframework.core.convert.TypeDescriptor.valueOf(Price.class);

        Price parsed = fcs.convert("USD 1,234.56", Price.class);
        System.out.println("Parsed: " + parsed);
        System.out.println("canConvert: " + fcs.canConvert(String.class, Price.class));
    }
}

class TypedValue {
    static Object of(Locale locale) { return null; } // stub for locale context setup
}
```

How to run: `java FormatterSpiBasic.java`

`FormattingConversionService` wraps `PriceFormatter` as both a `String → Price` converter and a `Price → String` converter. The locale is obtained from `LocaleContextHolder` at conversion time in Spring MVC context; in standalone use, the default locale applies.

### Level 2 — Intermediate

Multiple formatters; `DefaultFormattingConversionService` with built-in formatters; annotation-driven lookup.

```java
// FormatterSpiMultiple.java
import org.springframework.format.*;
import org.springframework.format.support.*;
import java.text.*;
import java.time.*;
import java.time.format.*;
import java.util.*;

record Percentage(double value) {
    @Override public String toString() { return value + "%"; }
}

record Duration(long seconds) {
    static Duration of(String s) {
        // "2h30m" or "150m" or "9000s"
        if (s.endsWith("h"))  return new Duration(Long.parseLong(s.substring(0, s.length()-1)) * 3600);
        if (s.endsWith("m"))  return new Duration(Long.parseLong(s.substring(0, s.length()-1)) * 60);
        if (s.endsWith("s"))  return new Duration(Long.parseLong(s.substring(0, s.length()-1)));
        return new Duration(Long.parseLong(s));
    }
    @Override public String toString() {
        long h = seconds / 3600, m = (seconds % 3600) / 60, s = seconds % 60;
        return (h > 0 ? h + "h" : "") + (m > 0 ? m + "m" : "") + (s > 0 ? s + "s" : "");
    }
}

class PercentageFormatter implements Formatter<Percentage> {
    @Override
    public Percentage parse(String text, Locale locale) {
        String t = text.trim().replace("%", "");
        return new Percentage(Double.parseDouble(t));
    }
    @Override
    public String print(Percentage p, Locale locale) {
        return String.format(locale, "%.1f%%", p.value());
    }
}

class DurationFormatter implements Formatter<Duration> {
    @Override public Duration parse(String text, Locale locale) { return Duration.of(text.trim()); }
    @Override public String print(Duration d, Locale locale)     { return d.toString(); }
}

public class FormatterSpiMultiple {
    public static void main(String[] args) {
        var fcs = new DefaultFormattingConversionService();
        fcs.addFormatterForFieldType(Percentage.class, new PercentageFormatter());
        fcs.addFormatterForFieldType(Duration.class,   new DurationFormatter());

        // Custom type conversions
        System.out.println("=== Custom formatters ===");
        Percentage pct = fcs.convert("35.5%",  Percentage.class);
        Duration   dur = fcs.convert("2h30m",  Duration.class);
        System.out.println("Percentage: " + pct + " (value=" + pct.value() + ")");
        System.out.println("Duration:   " + dur + " (seconds=" + dur.seconds() + ")");

        // Built-in number/date formatters still work
        System.out.println("\n=== Built-in converters (also in DefaultFormattingConversionService) ===");
        System.out.println("String→Integer: " + fcs.convert("42",   Integer.class));
        System.out.println("String→Double:  " + fcs.convert("3.14", Double.class));
        System.out.println("String→Boolean: " + fcs.convert("true", Boolean.class));

        // Print back
        System.out.println("\n=== Print (type → String) ===");
        System.out.println("Percentage→String: " + fcs.convert(new Percentage(42.5), String.class));
        System.out.println("Duration→String:   " + fcs.convert(new Duration(5400),   String.class));
    }
}
```

How to run: `java FormatterSpiMultiple.java`

`addFormatterForFieldType(Percentage.class, ...)` associates the formatter with the target type. `DefaultFormattingConversionService` includes all built-in `Converter` and `Formatter` registrations (dates, numbers, etc.). Both parse and print directions are accessible via `convert()`.

### Level 3 — Advanced

`AnnotationFormatterFactory` — formatter triggered by a field annotation; Spring context integration.

```java
// FormatterAnnotationFactory.java
import org.springframework.beans.factory.annotation.*;
import org.springframework.context.annotation.*;
import org.springframework.format.*;
import org.springframework.format.support.*;
import java.lang.annotation.*;
import java.text.*;
import java.util.*;

// Custom annotation: @Masked(character='*', visibleSuffix=4)
@Target({ElementType.FIELD, ElementType.PARAMETER})
@Retention(RetentionPolicy.RUNTIME)
@interface Masked {
    char character() default '*';
    int visibleSuffix() default 4;
}

// AnnotationFormatterFactory binds the formatter to the annotation
class MaskedAnnotationFormatterFactory
        implements AnnotationFormatterFactory<Masked> {

    @Override
    public Set<Class<?>> getFieldTypes() {
        return Set.of(String.class);
    }

    @Override
    public Printer<?> getPrinter(Masked annotation, Class<?> fieldType) {
        return (Printer<String>) (value, locale) -> {
            if (value == null || value.length() <= annotation.visibleSuffix()) return value;
            int maskLen = value.length() - annotation.visibleSuffix();
            return String.valueOf(annotation.character()).repeat(maskLen) +
                value.substring(maskLen);
        };
    }

    @Override
    public Parser<?> getParser(Masked annotation, Class<?> fieldType) {
        return (Parser<String>) (text, locale) -> text;  // pass-through
    }
}

class SensitiveData {
    @Value("${card.number}")  @Masked(visibleSuffix=4)  String cardNumber;
    @Value("${api.key}")      @Masked(character='X', visibleSuffix=6) String apiKey;
    @Value("${user.email}")   String email;  // no masking

    public void print(FormattingConversionService fcs) {
        System.out.println("card:  " + cardNumber);  // raw value injected
        System.out.println("key:   " + apiKey);
        System.out.println("email: " + email);
    }
}

@Configuration
@PropertySource("classpath:sensitive.properties")
@ComponentScan(basePackageClasses = FormatterAnnotationFactory.class)
class FmtCfg {
    @Bean
    public FormattingConversionService conversionService() {
        var fcs = new DefaultFormattingConversionService();
        fcs.addFormatterForFieldAnnotation(new MaskedAnnotationFormatterFactory());
        return fcs;
    }
}

public class FormatterAnnotationFactory {
    public static void main(String[] args) throws Exception {
        java.nio.file.Files.writeString(java.nio.file.Path.of("sensitive.properties"),
            "card.number=4111111111114242\napi.key=sk-live-abcdef012345\nuser.email=alice@example.com\n");

        var ctx = new AnnotationConfigApplicationContext(FmtCfg.class);

        // Demonstrate Printer via ConversionService (annotation not passed automatically here —
        // in MVC, Spring passes the annotation via TypeDescriptor)
        var fcs = ctx.getBean(FormattingConversionService.class);

        // Manually invoke printer-side for demo
        String card = "4111111111114242";
        // Use the formatter factory directly to demonstrate masking
        var factory = new MaskedAnnotationFormatterFactory();
        Masked annotation = SensitiveData.class.getDeclaredField("cardNumber")
            .getAnnotation(Masked.class);
        @SuppressWarnings("unchecked")
        Printer<String> printer = (Printer<String>) factory.getPrinter(annotation, String.class);
        System.out.println("card (raw):    " + card);
        System.out.println("card (masked): " + printer.print(card, Locale.ENGLISH));

        var apiAnnot = SensitiveData.class.getDeclaredField("apiKey").getAnnotation(Masked.class);
        @SuppressWarnings("unchecked")
        Printer<String> keyPrinter = (Printer<String>) factory.getPrinter(apiAnnot, String.class);
        System.out.println("key (masked):  " + keyPrinter.print("sk-live-abcdef012345", Locale.ENGLISH));

        ctx.close();
        java.nio.file.Files.deleteIfExists(java.nio.file.Path.of("sensitive.properties"));
    }
}
```

How to run: `java FormatterAnnotationFactory.java`

`AnnotationFormatterFactory<Masked>` links the `@Masked` annotation to a formatter. In Spring MVC, fields annotated with `@Masked` automatically use the `MaskedAnnotationFormatterFactory` printer when rendering model attributes to view templates.

## 6. Walkthrough

Execution for Level 3 card masking:

1. `factory.getPrinter(annotation, String.class)` → returns a `Printer<String>` lambda.
2. `printer.print("4111111111114242", Locale.ENGLISH)`:
   - `value.length() = 16`, `visibleSuffix = 4`.
   - `maskLen = 16 - 4 = 12`.
   - `'*'.repeat(12) = "************"`.
   - `value.substring(12) = "4242"`.
   - Result: `"************4242"`.

## 7. Gotchas & takeaways

> `Formatter<T>.parse()` is allowed to throw `ParseException` — this is the standard way to signal parse failure. Spring MVC / `DataBinder` catches `ParseException` and records it as a `typeMismatch` error. Do NOT return `null` on parse failure; throw instead.

> `FormattingConversionService` uses `LocaleContextHolder.getLocale()` as the current locale when converting via `ConversionService.convert()` (without a `Locale` argument). In non-web contexts, this is `Locale.getDefault()`. Only Spring MVC sets `LocaleContextHolder` from the request.

- `Formatter<T>` is simpler than maintaining separate `Converter<String, T>` and `Converter<T, String>` implementations — use it whenever the format depends on locale.
- `DefaultFormattingConversionService` auto-registers built-in formatters for `@NumberFormat`, `@DateTimeFormat`, JSR-310 types, etc. — call `new DefaultFormattingConversionService()` instead of `new FormattingConversionService()` to get them for free.
- Spring Boot's auto-configuration picks up `@Component Formatter<T>` beans automatically — no `FormatterRegistry` wiring needed.
- `AnnotationFormatterFactory` is how `@NumberFormat` and `@DateTimeFormat` are implemented internally — the same mechanism for custom annotations.

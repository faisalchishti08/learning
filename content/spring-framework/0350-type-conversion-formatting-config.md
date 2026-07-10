---
card: spring-framework
gi: 350
slug: type-conversion-formatting-config
title: "Type conversion & formatting config"
---

## 1. What it is

Type conversion and formatting configuration lets you register custom `Converter`/`Formatter` implementations with Spring MVC's `FormattingConversionService`, teaching it how to convert request data (path variables, query parameters, form fields — always arriving as `String`) into richer Java types beyond what's built in, and how to format Java objects back into strings for display. You register these via `WebMvcConfigurer.addFormatters(FormatterRegistry registry)`.

```java
@Override
public void addFormatters(FormatterRegistry registry) {
    registry.addConverter(new StringToProductIdConverter());
}
```

## 2. Why & when

Spring MVC already handles common conversions automatically — `String` to `int`, `long`, `boolean`, `LocalDate` (via ISO format), enums (by name), and more — using its built-in `ConversionService`. You need custom conversion configuration when:

- A path variable or query parameter represents a domain-specific type (a value object like `ProductId`, `Money`, or `EmailAddress`) that isn't a plain primitive, and you want Spring to construct it automatically rather than parsing a raw `String` manually inside every handler.
- Request data arrives in a non-default format (a date as `dd-MM-yyyy` instead of ISO, a comma-formatted number) that the built-in converters don't recognize.
- You want the *same* conversion/formatting logic applied consistently everywhere a type appears — path variables, request parameters, form binding, and even Thymeleaf's own EL expressions all share the same `ConversionService`.

This is a lighter-weight, more general mechanism than `@InitBinder`'s `PropertyEditor`-based approach (an earlier card) — `Converter`/`Formatter` beans are registered globally, once, and reused everywhere, rather than per-controller.

## 3. Core concept

```
FormatterRegistry (backs the shared ConversionService):

  Converter<S, T>:  S -> T, ONE direction only
    e.g. Converter<String, ProductId>   (parsing input)

  Formatter<T> extends Printer<T>, Parser<T>:  BOTH directions
    parse(String, Locale)   -> T      (String -> object, e.g. from a request)
    print(T, Locale)        -> String (object -> String, e.g. for display in a view)

Registered types apply UNIFORMLY across:
  @PathVariable ProductId id            <- path variable binding
  @RequestParam ProductId id            <- query parameter binding
  @ModelAttribute Order { ProductId productId; }   <- form field binding
  ${#conversions.convert(product.id, 'String')}     <- Thymeleaf EL, same ConversionService

Request: GET /products/PROD-42
      |
      v
"PROD-42" (raw path variable string)
      |
      v
registered Converter<String, ProductId> invoked
      |
      v
ProductId{value="PROD-42"} bound to the handler's @PathVariable parameter
```

## 4. Diagram

<svg viewBox="0 0 720 210" xmlns="http://www.w3.org/2000/svg" font-family="monospace" font-size="12">
  <rect width="720" height="210" fill="#0d1117"/>
  <text x="360" y="22" text-anchor="middle" fill="#8b949e">One registered Converter, used everywhere the type appears</text>

  <rect x="20" y="50" width="180" height="120" rx="5" fill="#1c2430" stroke="#6db33f"/>
  <text x="110" y="70" text-anchor="middle" fill="#6db33f" font-size="10">Converter&lt;String,ProductId&gt;</text>
  <text x="110" y="95" text-anchor="middle" fill="#8b949e" font-size="9">registered ONCE via</text>
  <text x="110" y="110" text-anchor="middle" fill="#8b949e" font-size="9">addFormatters(registry)</text>

  <line x1="200" y1="80" x2="260" y2="80" stroke="#8b949e" marker-end="url(#a26)"/>
  <line x1="200" y1="110" x2="260" y2="140" stroke="#8b949e" marker-end="url(#a26)"/>
  <line x1="200" y1="140" x2="260" y2="170" stroke="#8b949e" marker-end="url(#a26)"/>

  <rect x="260" y="55" width="200" height="35" rx="4" fill="#1c2430" stroke="#79c0ff"/>
  <text x="360" y="77" text-anchor="middle" fill="#79c0ff" font-size="10">@PathVariable ProductId</text>

  <rect x="260" y="120" width="200" height="35" rx="4" fill="#1c2430" stroke="#79c0ff"/>
  <text x="360" y="142" text-anchor="middle" fill="#79c0ff" font-size="10">@RequestParam ProductId</text>

  <rect x="260" y="155" width="200" height="35" rx="4" fill="#1c2430" stroke="#79c0ff"/>
  <text x="360" y="177" text-anchor="middle" fill="#79c0ff" font-size="10">form field ProductId</text>

  <defs>
    <marker id="a26" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto">
      <path d="M0,0 L0,6 L8,3 z" fill="#8b949e"/>
    </marker>
  </defs>
</svg>

*A single registered `Converter` applies consistently across path variables, query parameters, and form fields.*

## 5. Runnable example

### Level 1 — Basic

A custom value object (`ProductId`) parsed automatically from a path variable:

```java
// ProductId.java
public record ProductId(String value) {
    public ProductId {
        if (!value.matches("PROD-\\d+")) {
            throw new IllegalArgumentException("Invalid product id format: " + value);
        }
    }
}
```

```java
// StringToProductIdConverter.java
import org.springframework.core.convert.converter.Converter;
import org.springframework.stereotype.Component;

@Component
public class StringToProductIdConverter implements Converter<String, ProductId> {
    @Override
    public ProductId convert(String source) {
        return new ProductId(source);
    }
}
```

```java
// WebConfig.java
import org.springframework.context.annotation.Configuration;
import org.springframework.format.FormatterRegistry;
import org.springframework.web.servlet.config.annotation.WebMvcConfigurer;

@Configuration
public class WebConfig implements WebMvcConfigurer {
    @Override
    public void addFormatters(FormatterRegistry registry) {
        registry.addConverter(new StringToProductIdConverter());
    }
}
```

```java
// ProductController.java
import org.springframework.web.bind.annotation.*;

@RestController
public class ProductController {

    @GetMapping("/products/{id}")
    public String get(@PathVariable ProductId id) {
        return "Looking up product: " + id.value();
    }
}
```

**How to run:**
```bash
./mvnw spring-boot:run

curl http://localhost:8080/products/PROD-42
# Looking up product: PROD-42

curl -i http://localhost:8080/products/not-a-valid-id
# HTTP/1.1 400 Bad Request       <- conversion throws IllegalArgumentException, Spring maps it to 400
```

Without the registered `Converter`, `@PathVariable ProductId id` would fail at startup or request time — Spring has no idea how to turn a raw path segment string into a `ProductId` unless taught to. The handler method never has to call `new ProductId(...)` itself; conversion (including validation via the record's compact constructor) happens before the method body runs.

### Level 2 — Intermediate

A `Formatter` (bidirectional) for a `Money` value object, used both for parsing form input and for consistent display output:

```java
// Money.java
import java.math.BigDecimal;

public record Money(BigDecimal amount, String currency) {
    @Override
    public String toString() { return currency + " " + amount; }
}
```

```java
// MoneyFormatter.java
import org.springframework.format.Formatter;
import org.springframework.stereotype.Component;

import java.math.BigDecimal;
import java.util.Locale;

@Component
public class MoneyFormatter implements Formatter<Money> {

    @Override
    public Money parse(String text, Locale locale) {
        // Expects format like "USD 29.99"
        String[] parts = text.trim().split("\\s+", 2);
        return new Money(new BigDecimal(parts[1]), parts[0]);
    }

    @Override
    public String print(Money money, Locale locale) {
        return money.currency() + " " + money.amount();
    }
}
```

```java
// WebConfig.java (extended)
import org.springframework.context.annotation.Configuration;
import org.springframework.format.FormatterRegistry;
import org.springframework.web.servlet.config.annotation.WebMvcConfigurer;

@Configuration
public class WebConfig implements WebMvcConfigurer {
    @Override
    public void addFormatters(FormatterRegistry registry) {
        registry.addConverter(new StringToProductIdConverter());
        registry.addFormatter(new MoneyFormatter());
    }
}
```

```java
// ProductController.java (extended)
import org.springframework.web.bind.annotation.*;

@RestController
public class ProductController {

    @GetMapping("/products/{id}")
    public String get(@PathVariable ProductId id) {
        return "Looking up product: " + id.value();
    }

    @GetMapping("/products/price-check")
    public String priceCheck(@RequestParam Money price) {
        boolean premium = price.amount().doubleValue() > 25;
        return "Received " + price + " — premium: " + premium;
    }
}
```

**How to run:**
```bash
./mvnw spring-boot:run

curl "http://localhost:8080/products/price-check?price=USD%2029.99"
# Received USD 29.99 — premium: true
```

**What changed:** `Formatter<Money>` implements both `parse` (used for incoming request data, exactly like a `Converter`) and `print` (used when Spring needs to render a `Money` value back to text — for instance, in a Thymeleaf template via `${#conversions.convert(...)}` or when re-populating a form field after a validation failure). Registering it via `addFormatter` (rather than `addConverter`) makes both directions available through the one registration.

### Level 3 — Advanced

Production concern: locale-aware formatting (the same `Money` type printed differently per locale), and a `ConversionServiceFactoryBean`-free approach that layers custom converters on top of Spring's defaults without disabling them — a common mistake being accidentally replacing the whole default `ConversionService` instead of adding to it:

```java
// MoneyFormatter.java (production version, locale-aware)
import org.springframework.format.Formatter;
import org.springframework.stereotype.Component;

import java.math.BigDecimal;
import java.text.NumberFormat;
import java.util.Locale;

@Component
public class MoneyFormatter implements Formatter<Money> {

    @Override
    public Money parse(String text, Locale locale) throws java.text.ParseException {
        String[] parts = text.trim().split("\\s+", 2);
        if (parts.length != 2) {
            throw new java.text.ParseException("Expected '<CURRENCY> <amount>', got: " + text, 0);
        }
        NumberFormat numberFormat = NumberFormat.getNumberInstance(locale);
        Number amount = numberFormat.parse(parts[1]);   // locale-aware: "1.234,56" (de) vs "1,234.56" (en)
        return new Money(new BigDecimal(amount.toString()), parts[0]);
    }

    @Override
    public String print(Money money, Locale locale) {
        NumberFormat numberFormat = NumberFormat.getNumberInstance(locale);
        numberFormat.setMinimumFractionDigits(2);
        return money.currency() + " " + numberFormat.format(money.amount());
    }
}
```

```java
// WebConfig.java (production version) — addFormatters ADDS to defaults, never replaces them
import org.springframework.context.annotation.Configuration;
import org.springframework.format.FormatterRegistry;
import org.springframework.web.servlet.config.annotation.WebMvcConfigurer;

@Configuration
public class WebConfig implements WebMvcConfigurer {

    // IMPORTANT: overriding addFormatters (a WebMvcConfigurer method) is SAFE — it ADDS
    // registrations on top of Spring's default ConversionService. This is DIFFERENT from
    // manually declaring a bean of type ConversionService yourself, which REPLACES the
    // default entirely and silently disables built-in conversions (String->int, ->LocalDate, etc.)
    // unless you re-register every one of them by hand.
    @Override
    public void addFormatters(FormatterRegistry registry) {
        registry.addConverter(new StringToProductIdConverter());
        registry.addFormatter(new MoneyFormatter());
    }
}
```

```java
// ProductController.java (production version)
import org.springframework.web.bind.annotation.*;

@RestController
public class ProductController {

    @GetMapping("/products/price-check")
    public String priceCheck(@RequestParam Money price) {
        // Built-in conversions (String -> int, -> LocalDate, etc.) STILL work fine here,
        // proving addFormatters only ADDED our custom types, never disabled the defaults.
        return "Received " + price;
    }

    @GetMapping("/products/{id}/available-from")
    public String availableFrom(@PathVariable String id, @RequestParam java.time.LocalDate date) {
        return "Product " + id + " available from " + date;   // built-in String->LocalDate still works
    }
}
```

**How to run:**
```bash
./mvnw spring-boot:run

curl "http://localhost:8080/products/price-check?price=USD%2029.99" -H "Accept-Language: en"
# Received USD 29.99

curl "http://localhost:8080/products/1/available-from?date=2026-08-01"
# Product 1 available from 2026-08-01   <- built-in LocalDate conversion, untouched by our additions
```

**What changed and why:**
- `NumberFormat.getNumberInstance(locale)` makes parsing and printing locale-sensitive — a German-locale client sending `"EUR 1.234,56"` (comma as decimal separator) and an English-locale client sending `"USD 1,234.56"` (comma as thousands separator) are both parsed correctly, because the `Locale` parameter Spring passes to `Formatter` methods reflects the resolved request locale.
- The comment in `WebConfig` calls out a genuinely common mistake: declaring your own `@Bean ConversionService` (instead of using `addFormatters`) replaces Spring's entire default conversion service, silently breaking built-in conversions like `String → LocalDate` unless you manually re-register `DateTimeFormatterRegistrar` and everything else Spring normally provides for free. `addFormatters` avoids this trap entirely by layering onto the existing default service.
- `availableFrom`'s `@RequestParam LocalDate date` demonstrates the built-in ISO-date conversion continuing to work unaffected, proving the custom `Money`/`ProductId` registrations were purely additive.

## 6. Walkthrough

**Request: `GET /products/price-check?price=USD%2029.99` with `Accept-Language: en` (Level 3 code).**

1. `DispatcherServlet` matches the request to `priceCheck(Money price)`. Before invoking the method, Spring's argument resolution machinery needs to convert the raw query parameter string `"USD 29.99"` into a `Money` object.
2. It consults the application's `FormattingConversionService` (the shared service `addFormatters` registered onto) for a converter/formatter capable of producing `Money` from a `String`. It finds the registered `MoneyFormatter`.
3. Before calling `parse`, Spring resolves the request's effective `Locale` — via the configured `LocaleResolver`, reading `Accept-Language: en` → `Locale.ENGLISH`.
4. `MoneyFormatter.parse("USD 29.99", Locale.ENGLISH)` executes: splits on whitespace into `["USD", "29.99"]`. `NumberFormat.getNumberInstance(Locale.ENGLISH).parse("29.99")` interprets `.` as the decimal separator (correct for English locale) → `29.99`. Returns `new Money(new BigDecimal("29.99"), "USD")`.
5. The resulting `Money` object is bound to the `price` parameter, and `priceCheck` executes: `"Received " + price` implicitly calls `Money`'s `toString()` (not the registered `Formatter`'s `print` — that's used specifically by Spring's own conversion/rendering paths like Thymeleaf's EL, not by ordinary Java string concatenation) → `"Received USD 29.99"`.
6. Response:
   ```
   HTTP/1.1 200 OK
   Content-Type: text/plain;charset=UTF-8

   Received USD 29.99
   ```

**Contrast — the same request with `Accept-Language: de` and a German-formatted amount, `price=EUR%201.234,56`:**

1–3. Identical up through locale resolution — `Accept-Language: de` resolves to `Locale.GERMAN`.
4. `MoneyFormatter.parse("EUR 1.234,56", Locale.GERMAN)` splits into `["EUR", "1.234,56"]`. `NumberFormat.getNumberInstance(Locale.GERMAN).parse("1.234,56")` correctly interprets `.` as a thousands separator and `,` as the decimal separator (the German convention) → the numeric value `1234.56`. Returns `new Money(new BigDecimal("1234.56"), "EUR")`.
5. Without locale-aware parsing, this same input string would have been misparsed under an English-locale `NumberFormat` (which would choke on or misinterpret the German-style separators) — this is exactly why `Formatter.parse`/`print` receive a `Locale` parameter that a plain `Converter` does not.

## 7. Gotchas & takeaways

> **Declaring your own `@Bean` of type `ConversionService` replaces Spring's default conversion service entirely**, silently disabling built-in conversions (`String → int`, `String → LocalDate`, `String → enum`, etc.) unless you painstakingly re-register every one Spring normally provides. Always use `WebMvcConfigurer.addFormatters(FormatterRegistry)` to layer custom converters onto the existing default service instead.

> **A `Converter` that throws an unchecked exception (like `IllegalArgumentException`) during conversion results in a `400 Bad Request` by default** — this is convenient for validation-at-parse-time (as in the `ProductId` example) but means conversion errors and "genuinely malformed request" errors look identical to the client unless you add more specific exception handling (see the `@ExceptionHandler` cards) to distinguish them.

> **`Formatter.parse`/`print` receive a `Locale` argument that plain `Converter.convert` does not** — if a type's textual representation is locale-sensitive (numbers, dates, currency), always implement `Formatter`, not just `Converter`, even if you only need one direction right now; retrofitting locale-awareness onto a `Converter`-only implementation later requires switching interfaces anyway.

- `Converter<S,T>` is one-directional; `Formatter<T>` (parse + print) is bidirectional and locale-aware.
- Register custom types via `WebMvcConfigurer.addFormatters(FormatterRegistry)` — never by declaring a competing `ConversionService` bean, which replaces rather than extends the defaults.
- Once registered, a converter/formatter applies uniformly across path variables, query parameters, and form binding — write it once, use it everywhere that type appears.
- Use `Formatter` over `Converter` whenever the textual representation could reasonably vary by locale (numbers, currency, dates).

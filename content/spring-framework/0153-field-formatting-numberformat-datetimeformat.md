---
card: spring-framework
gi: 153
slug: field-formatting-numberformat-datetimeformat
title: "Field formatting (@NumberFormat, @DateTimeFormat)"
---

## 1. What it is

`@NumberFormat` and `@DateTimeFormat` are Spring's built-in field-level formatting annotations. Placed on a bean field or method parameter, they tell `FormattingConversionService` how to parse incoming strings and how to print the value back to a string. They are resolved by `NumberFormatAnnotationFormatterFactory` and `DateTimeFormatterRegistrar` respectively.

```java
class ReportFilters {
    @NumberFormat(style = Style.CURRENCY)
    BigDecimal minAmount;

    @DateTimeFormat(iso = ISO.DATE)
    LocalDate fromDate;

    @DateTimeFormat(pattern = "dd-MM-yyyy HH:mm")
    LocalDateTime reportTime;
}
```

## 2. Why & when

- **Spring MVC form binding** — a `<input type="text" value="2026-01-15">` field bound to a `LocalDate` property uses `@DateTimeFormat(iso = ISO.DATE)` for parsing.
- **`@RequestParam` / `@PathVariable`** — path variables and query params of date/number types are parsed using these annotations on method parameters.
- **No `@Value` conversion** — these annotations work with `DataBinder`-based binding; `@Value` uses `ConversionService` without annotation metadata.
- **Locale-aware numbers** — `@NumberFormat(style = Style.NUMBER)` formats `1234567.89` as `"1,234,567.89"` in `en_US` and `"1.234.567,89"` in `de_DE`.

## 3. Core concept

`@NumberFormat` attributes:

| Attribute | Values |
|---|---|
| `style` | `NUMBER`, `CURRENCY`, `PERCENT`, `INTEGER` |
| `pattern` | Custom `DecimalFormat` pattern: `"#,##0.##"` |
| (default) | Locale-specific number format |

`@DateTimeFormat` attributes:

| Attribute | Values |
|---|---|
| `iso` | `ISO.DATE` (`yyyy-MM-dd`), `ISO.TIME`, `ISO.DATE_TIME`, `ISO.NONE` |
| `pattern` | Custom `DateTimeFormatter` pattern: `"dd/MM/yyyy"` |
| `style` | `"SS"`, `"MM"`, `"LL"`, `"FF"` — short/medium/long/full for date/time |
| (default) | Locale-specific format |

`FormattingConversionService` must be the active `ConversionService` for these annotations to be resolved. In Spring MVC, `WebMvcConfigurationSupport` wires this automatically. Standalone, use `DefaultFormattingConversionService`.

## 4. Diagram

<svg viewBox="0 0 700 185" xmlns="http://www.w3.org/2000/svg">
  <!-- Field with annotation -->
  <rect x="10" y="30" width="200" height="60" rx="7" fill="#1c2430" stroke="#6db33f" stroke-width="2"/>
  <text x="110" y="52" fill="#6db33f" font-size="10" text-anchor="middle" font-family="sans-serif">@NumberFormat(style=CURRENCY)</text>
  <text x="110" y="68" fill="#6db33f" font-size="10" text-anchor="middle" font-family="sans-serif">BigDecimal price;</text>
  <text x="110" y="83" fill="#8b949e" font-size="9"  text-anchor="middle" font-family="sans-serif">@DateTimeFormat(iso=DATE)</text>

  <!-- Factory -->
  <rect x="270" y="18" width="200" height="80" rx="8" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="370" y="40" fill="#79c0ff" font-size="11" text-anchor="middle" font-family="sans-serif">AnnotationFormatterFactory</text>
  <text x="370" y="58" fill="#8b949e" font-size="9"  text-anchor="middle" font-family="sans-serif">NumberFormatAnnotationFormatterFactory</text>
  <text x="370" y="72" fill="#8b949e" font-size="9"  text-anchor="middle" font-family="sans-serif">DateTimeFormatterRegistrar</text>
  <text x="370" y="86" fill="#8b949e" font-size="9"  text-anchor="middle" font-family="sans-serif">reads annotation attributes</text>

  <!-- Input/Output -->
  <rect x="535" y="18"  width="155" height="40" rx="6" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="612" y="35"  fill="#6db33f" font-size="10" text-anchor="middle" font-family="sans-serif">parse: "$1,250.00"</text>
  <text x="612" y="50"  fill="#6db33f" font-size="10" text-anchor="middle" font-family="sans-serif">→ BigDecimal 1250.00</text>

  <rect x="535" y="70"  width="155" height="40" rx="6" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="612" y="87"  fill="#79c0ff" font-size="10" text-anchor="middle" font-family="sans-serif">print: BigDecimal 1250</text>
  <text x="612" y="102" fill="#79c0ff" font-size="10" text-anchor="middle" font-family="sans-serif">→ "$1,250.00"</text>

  <defs>
    <marker id="a153" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#6db33f"/></marker>
  </defs>
  <line x1="212" y1="60" x2="267" y2="60" stroke="#6db33f" stroke-width="2" marker-end="url(#a153)"/>
  <line x1="472" y1="38" x2="532" y2="38" stroke="#6db33f" stroke-width="2" marker-end="url(#a153)"/>
  <line x1="472" y1="88" x2="532" y2="88" stroke="#6db33f" stroke-width="2" marker-end="url(#a153)"/>

  <text x="350" y="150" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">Annotation attributes configure parse/print behaviour via the FormattingConversionService</text>

  <!-- Bottom row: examples -->
  <rect x="10" y="158" width="330" height="23" rx="5" fill="#1c2430" stroke="#6db33f" stroke-width="1"/>
  <text x="170" y="174" fill="#6db33f" font-size="9" text-anchor="middle" font-family="sans-serif">@NumberFormat: style=CURRENCY → "$1,250.00" | style=PERCENT → "42%"</text>

  <rect x="355" y="158" width="335" height="23" rx="5" fill="#1c2430" stroke="#79c0ff" stroke-width="1"/>
  <text x="522" y="174" fill="#79c0ff" font-size="9" text-anchor="middle" font-family="sans-serif">@DateTimeFormat: iso=DATE → "2026-07-04" | pattern="dd/MM/yyyy" → "04/07/2026"</text>
</svg>

Annotation attributes configure locale-aware parse and print via `FormattingConversionService`; one annotation per field.

## 5. Runnable example

### Level 1 — Basic

`@NumberFormat` and `@DateTimeFormat` on bean fields with `DataBinder`.

```java
// FieldFormattingBasic.java
import org.springframework.format.annotation.*;
import org.springframework.format.annotation.NumberFormat.*;
import org.springframework.format.support.*;
import org.springframework.validation.*;
import java.math.*;
import java.time.*;
import java.util.*;

class OrderForm {
    @NumberFormat(style = Style.CURRENCY)
    BigDecimal totalAmount;

    @NumberFormat(pattern = "#,##0.##")
    double weight;

    @DateTimeFormat(iso = DateTimeFormat.ISO.DATE)
    LocalDate orderDate;

    @DateTimeFormat(pattern = "dd-MMM-yyyy HH:mm")
    LocalDateTime scheduledAt;

    public BigDecimal getTotalAmount()    { return totalAmount; }
    public double getWeight()            { return weight; }
    public LocalDate getOrderDate()      { return orderDate; }
    public LocalDateTime getScheduledAt(){ return scheduledAt; }

    public void setTotalAmount(BigDecimal v)  { this.totalAmount = v; }
    public void setWeight(double v)           { this.weight = v; }
    public void setOrderDate(LocalDate v)     { this.orderDate = v; }
    public void setScheduledAt(LocalDateTime v){ this.scheduledAt = v; }
}

public class FieldFormattingBasic {
    public static void main(String[] args) {
        var fcs = new DefaultFormattingConversionService(true); // true = include @NumberFormat, @DateTimeFormat

        OrderForm form = new OrderForm();
        DataBinder binder = new DataBinder(form, "order");
        binder.setConversionService(fcs);

        MutablePropertyValues pvs = new MutablePropertyValues();
        pvs.add("totalAmount",  "$1,250.00");
        pvs.add("weight",       "5,250.75");
        pvs.add("orderDate",    "2026-07-04");
        pvs.add("scheduledAt",  "15-Jul-2026 14:30");

        binder.bind(pvs);
        BindingResult result = binder.getBindingResult();

        if (result.hasErrors()) {
            result.getAllErrors().forEach(e ->
                System.out.println("  ERROR: " + e.getDefaultMessage()));
        } else {
            System.out.println("totalAmount:  " + form.getTotalAmount());
            System.out.println("weight:       " + form.getWeight());
            System.out.println("orderDate:    " + form.getOrderDate());
            System.out.println("scheduledAt:  " + form.getScheduledAt());
        }
    }
}
```

How to run: `java FieldFormattingBasic.java`

`DefaultFormattingConversionService(true)` registers the `@NumberFormat` and `@DateTimeFormat` annotation factories. `DataBinder.setConversionService(fcs)` enables annotation-driven field formatting. `"$1,250.00"` parses to `BigDecimal("1250.00")`; `"2026-07-04"` to `LocalDate`.

### Level 2 — Intermediate

Locale-specific number formatting; `@NumberFormat(style = PERCENT)` and `CURRENCY`; multiple locales.

```java
// FieldFormattingLocale.java
import org.springframework.format.annotation.*;
import org.springframework.format.annotation.NumberFormat.*;
import org.springframework.format.support.*;
import org.springframework.validation.*;
import java.math.*;

class PriceReport {
    @NumberFormat(style = Style.CURRENCY)    BigDecimal unitPrice;
    @NumberFormat(style = Style.PERCENT)     BigDecimal taxRate;
    @NumberFormat(style = Style.NUMBER)      long quantity;
    @NumberFormat(pattern = "0.0000")        double exchangeRate;

    public void setUnitPrice(BigDecimal v)    { this.unitPrice = v; }
    public void setTaxRate(BigDecimal v)      { this.taxRate = v; }
    public void setQuantity(long v)           { this.quantity = v; }
    public void setExchangeRate(double v)     { this.exchangeRate = v; }

    public BigDecimal getUnitPrice()  { return unitPrice; }
    public BigDecimal getTaxRate()    { return taxRate; }
    public long getQuantity()         { return quantity; }
    public double getExchangeRate()   { return exchangeRate; }

    @Override
    public String toString() {
        return "unitPrice=" + unitPrice + " taxRate=" + taxRate +
            " qty=" + quantity + " fx=" + exchangeRate;
    }
}

public class FieldFormattingLocale {
    static void bind(String locale, MutablePropertyValues pvs) {
        System.out.println("=== Locale: " + locale + " ===");
        // Note: in standalone use, locale is Locale.getDefault()
        // In Spring MVC, LocaleContextHolder is set per request
        var fcs = new DefaultFormattingConversionService(true);

        PriceReport report = new PriceReport();
        DataBinder binder = new DataBinder(report, "report");
        binder.setConversionService(fcs);
        binder.bind(pvs);

        BindingResult result = binder.getBindingResult();
        if (result.hasErrors()) {
            result.getFieldErrors().forEach(e ->
                System.out.println("  ERROR [" + e.getField() + "]: " + e.getDefaultMessage()));
        } else {
            System.out.println("  " + report);
        }
    }

    public static void main(String[] args) {
        // English format: $1,250.00 / 8% / 1,000 / 1.0750
        MutablePropertyValues en = new MutablePropertyValues();
        en.add("unitPrice",    "$1,250.00");
        en.add("taxRate",      "8%");
        en.add("quantity",     "1,000");
        en.add("exchangeRate", "1.0750");
        bind("en_US", en);

        // Simulate a bad pattern
        System.out.println("\n=== Bad format ===");
        MutablePropertyValues bad = new MutablePropertyValues();
        bad.add("unitPrice",    "not-a-number");
        bad.add("taxRate",      "8%");
        bad.add("quantity",     "500");
        bad.add("exchangeRate", "1.05");
        bind("bad", bad);
    }
}
```

How to run: `java FieldFormattingLocale.java`

`Style.PERCENT` parses `"8%"` into a `BigDecimal`; `Style.CURRENCY` parses `"$1,250.00"` removing the currency symbol. A malformed value produces a `typeMismatch` error.

### Level 3 — Advanced

`@DateTimeFormat` with multiple formats; Spring context with `conversionService` bean; JSR-310 types.

```java
// FieldFormattingAdvanced.java
import org.springframework.beans.factory.annotation.*;
import org.springframework.context.annotation.*;
import org.springframework.format.annotation.*;
import org.springframework.format.support.*;
import org.springframework.validation.*;
import java.math.*;
import java.time.*;
import java.time.format.*;

class EventForm {
    @DateTimeFormat(iso = DateTimeFormat.ISO.DATE)
    LocalDate eventDate;

    @DateTimeFormat(iso = DateTimeFormat.ISO.DATE_TIME)
    LocalDateTime startTime;

    @DateTimeFormat(pattern = "HH:mm")
    LocalTime duration;

    @NumberFormat(style = NumberFormat.Style.CURRENCY)
    BigDecimal ticketPrice;

    @NumberFormat(style = NumberFormat.Style.NUMBER)
    int capacity;

    public void setEventDate(LocalDate v)   { this.eventDate = v; }
    public void setStartTime(LocalDateTime v){ this.startTime = v; }
    public void setDuration(LocalTime v)    { this.duration = v; }
    public void setTicketPrice(BigDecimal v){ this.ticketPrice = v; }
    public void setCapacity(int v)          { this.capacity = v; }

    public LocalDate getEventDate()     { return eventDate; }
    public LocalDateTime getStartTime() { return startTime; }
    public LocalTime getDuration()      { return duration; }
    public BigDecimal getTicketPrice()  { return ticketPrice; }
    public int getCapacity()            { return capacity; }
}

@Configuration
class EventCfg {
    @Bean
    public FormattingConversionService conversionService() {
        return new DefaultFormattingConversionService(true);
    }
}

public class FieldFormattingAdvanced {
    public static void main(String[] args) {
        var ctx = new AnnotationConfigApplicationContext(EventCfg.class);
        FormattingConversionService fcs = ctx.getBean(FormattingConversionService.class);

        EventForm form = new EventForm();
        DataBinder binder = new DataBinder(form, "event");
        binder.setConversionService(fcs);

        MutablePropertyValues pvs = new MutablePropertyValues();
        pvs.add("eventDate",   "2026-08-15");
        pvs.add("startTime",   "2026-08-15T09:00:00");
        pvs.add("duration",    "02:30");  // 2 hours 30 min as HH:mm
        pvs.add("ticketPrice", "$149.99");
        pvs.add("capacity",    "500");

        binder.bind(pvs);
        BindingResult result = binder.getBindingResult();

        if (result.hasErrors()) {
            result.getFieldErrors().forEach(e ->
                System.out.println("ERROR [" + e.getField() + "]: " +
                    e.getDefaultMessage() + " (rejected: " + e.getRejectedValue() + ")"));
        } else {
            System.out.println("eventDate:   " + form.getEventDate());
            System.out.println("startTime:   " + form.getStartTime());
            System.out.println("duration:    " + form.getDuration());
            System.out.println("ticketPrice: " + form.getTicketPrice());
            System.out.println("capacity:    " + form.getCapacity());

            // Print back via ConversionService
            System.out.println("\n=== Print back ===");
            System.out.println("eventDate → String: " + fcs.convert(form.getEventDate(), String.class));
            System.out.println("startTime → String: " + fcs.convert(form.getStartTime(), String.class));
        }

        ctx.close();
    }
}
```

How to run: `java FieldFormattingAdvanced.java`

`@DateTimeFormat(iso = ISO.DATE_TIME)` parses `"2026-08-15T09:00:00"` into `LocalDateTime`. `@DateTimeFormat(pattern = "HH:mm")` parses `"02:30"` into `LocalTime`. All parsing is annotation-driven — the formatter is selected by inspecting the annotation on the field via `TypeDescriptor`.

## 6. Walkthrough

Execution for Level 3 `duration` field:

1. `binder.bind(pvs)` processes `"duration" = "02:30"`.
2. `DataBinder` uses `FormattingConversionService` to find the converter for `String → LocalTime` with a `@DateTimeFormat(pattern = "HH:mm")` annotation on the field.
3. `DateTimeFormatterRegistrar` provides a formatter using `DateTimeFormatter.ofPattern("HH:mm")`.
4. `parse("02:30", Locale.ENGLISH)` → `LocalTime.of(2, 30)`.
5. `form.setDuration(LocalTime.of(2, 30))`.

## 7. Gotchas & takeaways

> `@DateTimeFormat` and `@NumberFormat` only work when a `FormattingConversionService` (specifically `DefaultFormattingConversionService`) is the active conversion service. A plain `DefaultConversionService` does NOT process these annotations. Always use `DefaultFormattingConversionService(true)` in non-MVC contexts.

> `@DateTimeFormat(iso = ISO.DATE)` expects `"yyyy-MM-dd"` strictly. `"04/07/2026"` will fail with a `typeMismatch`. If users enter dates in different formats, use `pattern` with the exact expected format.

- `@NumberFormat(style = PERCENT)` expects the `%` symbol in the input string — `"0.08"` parses to `0.0008`, not `8`. If you want `"8"` to mean `8%`, use `pattern = "##"` and divide by 100 in the model.
- In Spring Boot, `DefaultFormattingConversionService` is auto-configured as the application's conversion service — `@DateTimeFormat` and `@NumberFormat` work out of the box.
- For `@RequestParam` in Spring MVC, these annotations go on the method parameter: `public String search(@RequestParam @DateTimeFormat(iso=ISO.DATE) LocalDate from)`.
- Both annotations support `fallbackPatterns` (since Spring 5.3) — a list of additional patterns to try if the primary pattern fails — useful for accepting multiple date formats from different clients.

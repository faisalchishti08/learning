---
card: spring-framework
gi: 196
slug: javabeans-propertyeditor-registration-customeditorconfigurer
title: "JavaBeans PropertyEditor registration (CustomEditorConfigurer)"
---

## 1. What it is

`PropertyEditor` is a JavaBeans mechanism for converting a `String` to a typed Java object. Spring uses property editors to convert String values (from XML config, `@Value`, environment properties) into custom types when binding to bean properties. `CustomEditorConfigurer` registers custom editors globally for the Spring container.

```java
// Custom type
record EmailAddress(String local, String domain) {
    static EmailAddress parse(String email) {
        var parts = email.split("@", 2);
        return new EmailAddress(parts[0], parts[1]);
    }
}

// PropertyEditor converts String → EmailAddress
class EmailAddressEditor extends PropertyEditorSupport {
    @Override
    public void setAsText(String text) {
        setValue(EmailAddress.parse(text));
    }
    @Override
    public String getAsText() {
        var e = (EmailAddress) getValue();
        return e.local() + "@" + e.domain();
    }
}

// Register via CustomEditorConfigurer
@Bean
CustomEditorConfigurer editorConfigurer() {
    var configurer = new CustomEditorConfigurer();
    configurer.setCustomEditors(Map.of(EmailAddress.class, EmailAddressEditor.class));
    return configurer;
}

// Now @Value("${admin.email}") EmailAddress email works automatically
```

Spring provides built-in editors for `URL`, `UUID`, `Path`, `Charset`, `Currency`, `Locale`, and many others. Register custom ones for domain types.

## 2. Why & when

- **Custom type binding from properties** — `@Value("${server.address}")` InetAddress, or `@Value("${app.currency}")` `Currency`.
- **XML bean config** — `<property name="email" value="admin@example.com"/>` with `EmailAddress` type on the bean.
- **`@Value` with domain objects** — convert `String` to a value-object type automatically.
- **Don't use** when Spring's built-in `ConversionService` / `Converter<S,T>` is available for the same conversion — `Converter` is the modern replacement (thread-safe, testable, works with Spring MVC data binding too).
- **Prefer `Converter<S,T>`** for new code; property editors are JavaBeans legacy but still supported and common in older Spring code.

## 3. Core concept

Spring's `BeanWrapper` uses `PropertyEditor`s when converting `String` values to property types during bean creation. The flow:

```
@Value("${admin.email}")              →  "admin@example.com"  (String)
                                               ↓
Spring BeanWrapper finds PropertyEditor for EmailAddress
                                               ↓
EmailAddressEditor.setAsText("admin@example.com")
                                               ↓
setValue(EmailAddress("admin", "example.com"))
                                               ↓
EmailAddress injected into the bean
```

**Registration mechanisms:**

| Mechanism | Scope | When to use |
|---|---|---|
| `CustomEditorConfigurer` | Container-wide | All beans in the ApplicationContext |
| `@InitBinder` in `@Controller` | Request-scoped | MVC form binding only |
| Direct `BeanWrapper.registerCustomEditor(...)` | Bean-level | Rarely needed |

**`PropertyEditorSupport`** — extend this instead of implementing `PropertyEditor` directly; override only `setAsText` (String→type) and `getAsText` (type→String).

**`PropertyEditorRegistrar`** — a callback interface for registering editors programmatically. Pass to `CustomEditorConfigurer.setPropertyEditorRegistrars(...)` for programmatic registration, useful when editors need constructor arguments or Spring beans.

**Important:** `PropertyEditor` is NOT thread-safe (it holds state: `value`). Spring creates a new instance per conversion. When using `CustomEditorConfigurer.setCustomEditors(Map<Class, Class>)`, Spring instantiates the editor class on each use. Do NOT use `PropertyEditorRegistrar` to share a single editor instance across threads.

## 4. Diagram

<svg viewBox="0 0 700 175" xmlns="http://www.w3.org/2000/svg">
  <defs>
    <marker id="peda" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L6,3 L0,6 Z" fill="#6db33f"/></marker>
  </defs>

  <!-- Source: string value -->
  <rect x="5" y="35" width="120" height="50" rx="4" fill="#1c2430" stroke="#79c0ff" stroke-width="2"/>
  <text x="62" y="55" fill="#79c0ff" font-size="8.5" text-anchor="middle" font-family="sans-serif" font-weight="bold">String value</text>
  <text x="62" y="70" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">"admin@acme.com"</text>
  <text x="62" y="82" fill="#8b949e" font-size="7" text-anchor="middle" font-family="sans-serif">from @Value / XML / props</text>

  <!-- BeanWrapper -->
  <rect x="175" y="15" width="180" height="120" rx="6" fill="#1c2430" stroke="#8b949e" stroke-width="1.5"/>
  <text x="265" y="35" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif" font-weight="bold">BeanWrapper</text>
  <text x="265" y="52" fill="#8b949e" font-size="7.5" text-anchor="middle" font-family="sans-serif">finds PropertyEditor</text>
  <text x="265" y="65" fill="#8b949e" font-size="7.5" text-anchor="middle" font-family="sans-serif">for target type</text>
  <text x="265" y="83" fill="#6db33f" font-size="7.5" text-anchor="middle" font-family="sans-serif">1. Custom editors (registered)</text>
  <text x="265" y="96" fill="#6db33f" font-size="7.5" text-anchor="middle" font-family="sans-serif">2. Built-in editors (URL, UUID…)</text>
  <text x="265" y="109" fill="#6db33f" font-size="7.5" text-anchor="middle" font-family="sans-serif">3. ConversionService fallback</text>
  <text x="265" y="122" fill="#8b949e" font-size="7" text-anchor="middle" font-family="sans-serif">new instance per conversion</text>
  <line x1="127" y1="60" x2="173" y2="60" stroke="#79c0ff" stroke-width="1.5" marker-end="url(#peda)"/>

  <!-- PropertyEditor -->
  <rect x="410" y="30" width="165" height="80" rx="4" fill="#6db33f" opacity="0.2" stroke="#6db33f" stroke-width="1.5"/>
  <text x="492" y="50" fill="#6db33f" font-size="9" text-anchor="middle" font-family="sans-serif" font-weight="bold">EmailAddressEditor</text>
  <text x="492" y="65" fill="#8b949e" font-size="7.5" text-anchor="middle" font-family="sans-serif">setAsText("admin@acme.com")</text>
  <text x="492" y="79" fill="#8b949e" font-size="7.5" text-anchor="middle" font-family="sans-serif">setValue(new EmailAddress(...))</text>
  <text x="492" y="93" fill="#8b949e" font-size="7.5" text-anchor="middle" font-family="sans-serif">getValue() → EmailAddress</text>
  <line x1="357" y1="60" x2="408" y2="60" stroke="#6db33f" stroke-width="1.5" marker-end="url(#peda)"/>

  <!-- Result -->
  <rect x="590" y="42" width="105" height="40" rx="4" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="642" y="58" fill="#6db33f" font-size="8" text-anchor="middle" font-family="sans-serif">EmailAddress</text>
  <text x="642" y="72" fill="#8b949e" font-size="7" text-anchor="middle" font-family="sans-serif">injected into bean</text>
  <line x1="577" y1="62" x2="588" y2="62" stroke="#6db33f" stroke-width="1.5" marker-end="url(#peda)"/>

  <!-- CustomEditorConfigurer -->
  <rect x="175" y="148" width="180" height="22" rx="3" fill="#1c2430" stroke="#8b949e" stroke-width="1"/>
  <text x="265" y="163" fill="#8b949e" font-size="7.5" text-anchor="middle" font-family="sans-serif">CustomEditorConfigurer registers editors at startup</text>
</svg>

`BeanWrapper` resolves the editor; `CustomEditorConfigurer` registers custom editors globally; each conversion gets a fresh editor instance.

## 5. Runnable example

Scenario: **application configuration binding** — custom types for IP range, email address, and currency code.

### Level 1 — Basic

Simple `PropertyEditorSupport` for a custom type; `CustomEditorConfigurer` registration.

```java
// PropertyEditorBasic.java
import org.springframework.beans.PropertyEditorRegistrar;
import org.springframework.beans.PropertyEditorRegistry;
import org.springframework.beans.factory.config.CustomEditorConfigurer;
import org.springframework.beans.propertyeditors.CustomNumberEditor;
import org.springframework.context.annotation.*;
import java.beans.PropertyEditorSupport;
import java.util.Map;

// Custom domain type
record Percentage(double value) {
    static Percentage parse(String s) {
        var clean = s.endsWith("%") ? s.substring(0, s.length()-1) : s;
        return new Percentage(Double.parseDouble(clean));
    }
    @Override public String toString() { return value + "%"; }
}

// PropertyEditor for Percentage
class PercentageEditor extends PropertyEditorSupport {
    @Override
    public void setAsText(String text) throws IllegalArgumentException {
        setValue(Percentage.parse(text.trim()));
    }
    @Override
    public String getAsText() {
        var p = (Percentage) getValue();
        return p == null ? "" : p.value() + "%";
    }
}

@Configuration
class PeConfig {
    @Bean
    CustomEditorConfigurer customEditorConfigurer() {
        var configurer = new CustomEditorConfigurer();
        // Map: target type → editor class (Spring instantiates per use)
        configurer.setCustomEditors(Map.of(Percentage.class, PercentageEditor.class));
        return configurer;
    }

    @Bean
    DiscountBean discountBean() {
        var bean = new DiscountBean();
        bean.setDiscount(Percentage.parse("15%"));
        return bean;
    }
}

class DiscountBean {
    private Percentage discount;
    public void setDiscount(Percentage d) { this.discount = d; }
    public Percentage getDiscount() { return discount; }
}

public class PropertyEditorBasic {
    public static void main(String[] args) {
        var ctx = new AnnotationConfigApplicationContext(PeConfig.class);
        var bean = ctx.getBean(DiscountBean.class);
        System.out.println("Discount: " + bean.getDiscount());

        // Demonstrate editor directly
        var editor = new PercentageEditor();
        editor.setAsText("25.5%");
        System.out.println("Parsed: " + editor.getValue());
        System.out.println("Text: " + editor.getAsText());

        ctx.close();
    }
}
```

How to run: `java PropertyEditorBasic.java`

`CustomEditorConfigurer` is a `BeanFactoryPostProcessor` — it runs before any beans are created, registering editors in the `BeanFactory`. `setCustomEditors(Map<Class, Class>)` maps the target type to the editor class. Spring reflects `new PercentageEditor()` for each conversion.

### Level 2 — Intermediate

`PropertyEditorRegistrar`; multiple editors; `@Value` injection with custom type.

```java
// PropertyEditorIntermediate.java
import org.springframework.beans.*;
import org.springframework.beans.factory.config.CustomEditorConfigurer;
import org.springframework.context.annotation.*;
import org.springframework.beans.factory.annotation.Value;
import java.beans.PropertyEditorSupport;
import java.net.*;

// Custom type: IpRange
record IpRange(String startIp, String endIp) {
    static IpRange parse(String s) {
        var parts = s.split("-", 2);
        return new IpRange(parts[0].trim(), parts[1].trim());
    }
    @Override public String toString() { return startIp + " – " + endIp; }
}
class IpRangeEditor extends PropertyEditorSupport {
    @Override public void setAsText(String t) { setValue(IpRange.parse(t)); }
}

// Custom type: CurrencyCode
record CurrencyCode(String code) {
    static CurrencyCode of(String s) {
        if (s.length() != 3) throw new IllegalArgumentException("Currency must be 3 chars");
        return new CurrencyCode(s.toUpperCase());
    }
}
class CurrencyCodeEditor extends PropertyEditorSupport {
    @Override public void setAsText(String t) { setValue(CurrencyCode.of(t.trim())); }
}

// PropertyEditorRegistrar — registers editors programmatically (can inject Spring beans)
class AppEditorRegistrar implements PropertyEditorRegistrar {
    @Override
    public void registerCustomEditors(PropertyEditorRegistry registry) {
        registry.registerCustomEditor(IpRange.class,      new IpRangeEditor());
        registry.registerCustomEditor(CurrencyCode.class, new CurrencyCodeEditor());
        System.out.println("[Registrar] Registered IpRange + CurrencyCode editors");
    }
}

@Configuration
@PropertySource("classpath:app-editors.properties")
class PeIntermConfig {
    @Bean
    CustomEditorConfigurer customEditorConfigurer() {
        var configurer = new CustomEditorConfigurer();
        configurer.setPropertyEditorRegistrars(new PropertyEditorRegistrar[]{
            new AppEditorRegistrar()
        });
        return configurer;
    }

    // @Value will use the registered IpRange editor automatically
    @Bean
    NetworkConfig networkConfig(
            @Value("${network.allowed.range:10.0.0.1-10.0.0.254}") IpRange allowedRange,
            @Value("${billing.currency:USD}") CurrencyCode currency) {
        return new NetworkConfig(allowedRange, currency);
    }
}

record NetworkConfig(IpRange allowedRange, CurrencyCode currency) {}

public class PropertyEditorIntermediate {
    public static void main(String[] args) throws Exception {
        // Write properties file
        var f = new java.io.File("app-editors.properties");
        java.nio.file.Files.writeString(f.toPath(),
            "network.allowed.range=192.168.1.1-192.168.1.255\nbilling.currency=EUR\n");
        // Add directory to classpath for @PropertySource to find it (or put in src/main/resources)

        var ctx = new AnnotationConfigApplicationContext(PeIntermConfig.class);
        var cfg = ctx.getBean(NetworkConfig.class);
        System.out.println("Allowed range: " + cfg.allowedRange());
        System.out.println("Currency:      " + cfg.currency().code());
        ctx.close();
        f.delete();
    }
}
```

How to run: `java PropertyEditorIntermediate.java`

`PropertyEditorRegistrar` is preferred over `setCustomEditors(Map)` when editors need constructor arguments (e.g., a date format string). `registerCustomEditors(registry)` is called before each bean creation, ensuring a fresh editor instance per use.

### Level 3 — Advanced

`@InitBinder` for web form binding; `ConversionService` comparison; custom editor via `WebDataBinder`.

```java
// PropertyEditorAdvanced.java
import org.springframework.beans.*;
import org.springframework.beans.factory.config.CustomEditorConfigurer;
import org.springframework.context.annotation.*;
import org.springframework.format.support.*;
import org.springframework.core.convert.*;
import org.springframework.core.convert.converter.*;
import java.beans.PropertyEditorSupport;
import java.util.*;

// Custom type
record ColorHex(int r, int g, int b) {
    static ColorHex parse(String hex) {
        var s = hex.startsWith("#") ? hex.substring(1) : hex;
        return new ColorHex(
            Integer.parseInt(s.substring(0,2), 16),
            Integer.parseInt(s.substring(2,4), 16),
            Integer.parseInt(s.substring(4,6), 16)
        );
    }
    @Override public String toString() {
        return String.format("#%02X%02X%02X", r, g, b);
    }
}

// ---- PropertyEditor (legacy approach) ----
class ColorHexEditor extends PropertyEditorSupport {
    @Override public void setAsText(String t) { setValue(ColorHex.parse(t.trim())); }
    @Override public String getAsText() {
        var c = (ColorHex) getValue();
        return c == null ? "" : c.toString();
    }
}

// ---- ConversionService Converter (modern approach for comparison) ----
class StringToColorHexConverter implements Converter<String, ColorHex> {
    @Override public ColorHex convert(String source) { return ColorHex.parse(source); }
}

@Configuration
class PeAdvConfig {
    // Register PropertyEditor globally (legacy path)
    @Bean
    CustomEditorConfigurer propertyEditors() {
        var cfg = new CustomEditorConfigurer();
        cfg.setCustomEditors(Map.of(ColorHex.class, ColorHexEditor.class));
        return cfg;
    }

    // Also register a ConversionService with a Converter (modern path)
    @Bean
    ConversionService conversionService() {
        var cs = new DefaultFormattingConversionService();
        cs.addConverter(new StringToColorHexConverter());
        return cs;
    }
}

@org.springframework.stereotype.Component
class ThemeConfig {
    private final ColorHex primaryColor;

    ThemeConfig() {
        // Simulate @Value injection — demonstrate both approaches
        var editor = new ColorHexEditor();
        editor.setAsText("#3A86FF");
        this.primaryColor = (ColorHex) editor.getValue();
    }

    public ColorHex getPrimaryColor() { return primaryColor; }
}

public class PropertyEditorAdvanced {
    public static void main(String[] args) {
        // Show PropertyEditor approach
        var editor = new ColorHexEditor();
        editor.setAsText("#6DB33F");
        var fromEditor = (ColorHex) editor.getValue();
        System.out.println("PropertyEditor parsed: " + fromEditor + " = rgb("
            + fromEditor.r() + "," + fromEditor.g() + "," + fromEditor.b() + ")");

        // Show ConversionService approach
        var cs = new DefaultFormattingConversionService();
        cs.addConverter(new StringToColorHexConverter());
        var fromConverter = cs.convert("#79C0FF", ColorHex.class);
        System.out.println("Converter parsed:      " + fromConverter);

        // Spring context
        var ctx = new AnnotationConfigApplicationContext(PeAdvConfig.class);
        var theme = ctx.getBean(ThemeConfig.class);
        System.out.println("Theme primary: " + theme.getPrimaryColor());
        ctx.close();
    }
}
```

How to run: `java PropertyEditorAdvanced.java`

`ConversionService` (`Converter<S,T>`) is the modern replacement for `PropertyEditor`. Key difference: `PropertyEditor` is stateful (not thread-safe) and limited to `String` conversion. `Converter<S,T>` is stateless, thread-safe, and can convert between any two types. Spring MVC data binding uses `ConversionService` first, falls back to `PropertyEditor`. For new code, use `Converter`.

## 6. Walkthrough

Tracing `@Value("${network.allowed.range:10.0.0.1-10.0.0.254}") IpRange allowedRange`:

**Step 1 — Context refresh begins. `CustomEditorConfigurer.postProcessBeanFactory` called.**
- `AppEditorRegistrar.registerCustomEditors(registry)` is stored for later use.
- Prints `[Registrar] Registered IpRange + CurrencyCode editors`.

**Step 2 — `networkConfig` bean is about to be created.**
- Spring resolves `@Value("${network.allowed.range}")` → `"192.168.1.1-192.168.1.255"`.
- Target type: `IpRange`.

**Step 3 — `BeanWrapper` looks for an editor for `IpRange`:**
- Checks custom editors → found `IpRangeEditor` (registered by `AppEditorRegistrar`).
- Creates new instance: `new IpRangeEditor()`.
- Calls `editor.setAsText("192.168.1.1-192.168.1.255")`.
- `IpRange.parse(...)` returns `IpRange("192.168.1.1", "192.168.1.255")`.
- `editor.getValue()` returns the `IpRange` instance.

**Step 4 — Spring injects the `IpRange` into the `@Bean` method parameter.**

**Step 5 — `NetworkConfig` bean created with the resolved `IpRange` and `CurrencyCode`.**

## 7. Gotchas & takeaways

> **`PropertyEditor` is NOT thread-safe** — it holds state (`value` field). Spring creates a new instance for every conversion. Never pass a shared `PropertyEditor` instance to `registry.registerCustomEditor(type, instance)` — this is a threading bug. Always use `registerCustomEditor(type, editorClass)` (class, not instance) or `PropertyEditorRegistrar`.

> **`CustomEditorConfigurer` is a `BeanFactoryPostProcessor`.** It must be a bean in the same `ApplicationContext`. If defined in a parent context (root), child context (MVC) beans won't automatically see it.

- **`PropertyEditorSupport` null guard:** `getValue()` can return `null` in `getAsText()`. Always guard: `return getValue() == null ? "" : ...`.
- **`@InitBinder` for MVC:** register editors for Spring MVC form binding in `@Controller` with `@InitBinder` methods — these apply only to that controller's request binding, not to the broader container. Example: `binder.registerCustomEditor(Date.class, new CustomDateEditor(...))`.
- **When to use `Converter<S,T>` instead:** always for new code. `Converter` is stateless, thread-safe, works with Spring MVC data binding and `@Value`, and integrates with `FormattingConversionService`. `PropertyEditor` is retained for legacy XML config compatibility.
- **Built-in editors Spring registers:** `ClassEditor`, `FileEditor`, `InputStreamEditor`, `LocaleEditor`, `PatternEditor`, `PropertiesEditor`, `ResourceEditor`, `StringArrayPropertyEditor`, `TimeZoneEditor`, `URLEditor`, `UUIDEditor`. These cover most common types — check before writing a custom one.

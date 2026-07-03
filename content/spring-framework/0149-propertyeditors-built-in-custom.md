---
card: spring-framework
gi: 149
slug: propertyeditors-built-in-custom
title: "PropertyEditors (built-in & custom)"
---

## 1. What it is

`PropertyEditor` (from `java.beans`) converts between `String` representations and typed Java objects. Spring registers built-in editors for common types (`URL`, `File`, `Date`, `Class`, `Locale`, `Pattern`, etc.) and lets you register custom editors for domain types via `DataBinder` or `@InitBinder`. When `BeanWrapper` or `DataBinder` binds a `String` value to a typed field, the matching `PropertyEditor` performs the conversion.

```java
// Custom editor for a Money value type
class MoneyEditor extends PropertyEditorSupport {
    @Override
    public void setAsText(String text) {
        String[] parts = text.split(" ");
        setValue(new Money(Double.parseDouble(parts[0]), parts[1]));
    }
    @Override
    public String getAsText() {
        Money m = (Money) getValue();
        return m.amount() + " " + m.currency();
    }
}
```

## 2. Why & when

- **Custom value types** — convert `"250.00 USD"` → `Money`, `"2026-07-04"` → `LocalDate` (before Spring 3 `ConversionService`).
- **Spring MVC forms** — `@InitBinder` registers editors for request parameters bound to controller method arguments.
- **`@PropertySource` value conversion** — when `@Value("${max.amount}") Money max` is used, the registered editor handles the conversion.
- **Legacy code** — pre-`ConversionService` Spring applications use `PropertyEditor` extensively. New code should prefer `Converter` (next tutorial), but editors remain supported and are still used by Spring MVC form binding.

## 3. Core concept

Built-in editors registered by `BeanWrapperImpl`:

| Editor | Converts |
|---|---|
| `ClassEditor` | `"com.example.Foo"` → `Class<?>` |
| `FileEditor` | `"path/to/file"` → `java.io.File` |
| `UrlEditor` | `"https://..."` → `java.net.URL` |
| `LocaleEditor` | `"en_US"` → `java.util.Locale` |
| `PatternEditor` | `"\\d+"` → `java.util.regex.Pattern` |
| `CharsetEditor` | `"UTF-8"` → `java.nio.charset.Charset` |
| `CustomDateEditor` | `"2026-07-04"` → `java.util.Date` (format configurable) |
| `CustomNumberEditor` | `"42"` → numeric types |
| `StringArrayPropertyEditor` | `"a,b,c"` → `String[]` |
| `PathEditor` | `"path/to/file"` → `java.nio.file.Path` |

Custom registration via `DataBinder`:

```java
binder.registerCustomEditor(Money.class, new MoneyEditor());
```

Spring MVC `@InitBinder`:

```java
@InitBinder
void initBinder(WebDataBinder binder) {
    binder.registerCustomEditor(Money.class, new MoneyEditor());
}
```

`PropertyEditorSupport` is the base class — override `setAsText(String)` and `getAsText()`.

## 4. Diagram

<svg viewBox="0 0 700 185" xmlns="http://www.w3.org/2000/svg">
  <!-- String input -->
  <rect x="10" y="65" width="130" height="55" rx="7" fill="#1c2430" stroke="#8b949e" stroke-width="1.5"/>
  <text x="75" y="87" fill="#8b949e" font-size="11" text-anchor="middle" font-family="sans-serif">String input</text>
  <text x="75" y="104" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">"250.00 USD"</text>

  <!-- PropertyEditor -->
  <rect x="200" y="40" width="200" height="110" rx="8" fill="#1c2430" stroke="#6db33f" stroke-width="2"/>
  <text x="300" y="62" fill="#6db33f" font-size="12" text-anchor="middle" font-family="sans-serif">PropertyEditor</text>
  <text x="300" y="80" fill="#8b949e" font-size="9"  text-anchor="middle" font-family="sans-serif">setAsText(String)</text>
  <text x="300" y="94" fill="#8b949e" font-size="9"  text-anchor="middle" font-family="sans-serif">getAsText() → String</text>
  <text x="300" y="110" fill="#8b949e" font-size="9"  text-anchor="middle" font-family="sans-serif">setValue(Object)</text>
  <text x="300" y="124" fill="#8b949e" font-size="9"  text-anchor="middle" font-family="sans-serif">getValue() → Object</text>
  <text x="300" y="140" fill="#6db33f" font-size="9"  text-anchor="middle" font-family="sans-serif">extend PropertyEditorSupport</text>

  <!-- Typed output -->
  <rect x="460" y="65" width="230" height="55" rx="7" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="575" y="88" fill="#6db33f" font-size="11" text-anchor="middle" font-family="sans-serif">Typed object</text>
  <text x="575" y="106" fill="#6db33f" font-size="10" text-anchor="middle" font-family="sans-serif">Money(250.0, "USD")</text>

  <defs>
    <marker id="a149" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#6db33f"/></marker>
  </defs>
  <line x1="142" y1="92" x2="197" y2="92" stroke="#6db33f" stroke-width="2" marker-end="url(#a149)"/>
  <line x1="402" y1="92" x2="457" y2="92" stroke="#6db33f" stroke-width="2" marker-end="url(#a149)"/>

  <text x="350" y="178" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">PropertyEditor.setAsText converts String to typed object; getAsText converts back</text>
</svg>

`PropertyEditorSupport.setAsText` converts `String → type`; `getAsText` converts `type → String` for display.

## 5. Runnable example

### Level 1 — Basic

Use a built-in editor; register a simple custom editor for a value type.

```java
// PropertyEditorBasic.java
import org.springframework.beans.*;
import org.springframework.beans.propertyeditors.*;
import java.beans.*;
import java.io.*;
import java.net.*;
import java.nio.charset.*;

record EmailAddress(String local, String domain) {
    static EmailAddress of(String s) {
        String[] parts = s.split("@");
        if (parts.length != 2) throw new IllegalArgumentException("Bad email: " + s);
        return new EmailAddress(parts[0], parts[1]);
    }

    @Override public String toString() { return local + "@" + domain; }
}

class EmailAddressEditor extends PropertyEditorSupport {
    @Override
    public void setAsText(String text) { setValue(EmailAddress.of(text.trim())); }

    @Override
    public String getAsText() {
        return getValue() == null ? "" : getValue().toString();
    }
}

class Contact {
    private String name;
    private EmailAddress email;
    private URL website;
    private Charset encoding;
    private File configFile;

    public void setName(String n)         { this.name = n; }
    public void setEmail(EmailAddress e)  { this.email = e; }
    public void setWebsite(URL u)         { this.website = u; }
    public void setEncoding(Charset c)    { this.encoding = c; }
    public void setConfigFile(File f)     { this.configFile = f; }

    public String getName()         { return name; }
    public EmailAddress getEmail()  { return email; }
    public URL getWebsite()         { return website; }
    public Charset getEncoding()    { return encoding; }
    public File getConfigFile()     { return configFile; }
}

public class PropertyEditorBasic {
    public static void main(String[] args) throws Exception {
        Contact contact = new Contact();
        BeanWrapper bw = new BeanWrapperImpl(contact);

        // Register custom editor
        bw.registerCustomEditor(EmailAddress.class, new EmailAddressEditor());

        // Bind string values — editors do the type conversion
        bw.setPropertyValue("name",       "Alice");
        bw.setPropertyValue("email",      "alice@example.com");  // custom editor
        bw.setPropertyValue("website",    "https://example.com");  // built-in UrlEditor
        bw.setPropertyValue("encoding",   "UTF-8");               // built-in CharsetEditor
        bw.setPropertyValue("configFile", "app.properties");      // built-in FileEditor

        System.out.println("name:       " + contact.getName());
        System.out.println("email:      " + contact.getEmail() + " (class: " + contact.getEmail().getClass().getSimpleName() + ")");
        System.out.println("website:    " + contact.getWebsite() + " (class: " + contact.getWebsite().getClass().getSimpleName() + ")");
        System.out.println("encoding:   " + contact.getEncoding());
        System.out.println("configFile: " + contact.getConfigFile());

        // Read back as text
        System.out.println("\ngetAsText(email): " +
            bw.getPropertyDescriptor("email").getReadMethod().invoke(contact));
    }
}
```

How to run: `java PropertyEditorBasic.java`

`"alice@example.com"` → `EmailAddress` via `EmailAddressEditor`. `"https://example.com"` → `URL` via Spring's built-in `UrlEditor`. `"UTF-8"` → `Charset` via `CharsetEditor`. All conversions happen automatically when the editor is registered.

### Level 2 — Intermediate

Register editors on `DataBinder`; stateless vs stateful editors; thread-safety consideration.

```java
// PropertyEditorDataBinder.java
import org.springframework.validation.*;
import java.beans.*;
import java.time.*;
import java.time.format.*;

record DateRange(LocalDate start, LocalDate end) {
    static DateRange of(String s) {
        // "2026-01-01:2026-12-31"
        String[] parts = s.split(":");
        return new DateRange(LocalDate.parse(parts[0]), LocalDate.parse(parts[1]));
    }
    @Override public String toString() { return start + ":" + end; }
}

class DateRangeEditor extends PropertyEditorSupport {
    @Override public void setAsText(String s) { setValue(DateRange.of(s)); }
    @Override public String getAsText() {
        return getValue() == null ? "" : getValue().toString();
    }
}

record Percentage(double value) {
    static Percentage of(String s) {
        String trimmed = s.endsWith("%") ? s.substring(0, s.length()-1) : s;
        return new Percentage(Double.parseDouble(trimmed));
    }
    @Override public String toString() { return value + "%"; }
}

class PercentageEditor extends PropertyEditorSupport {
    @Override public void setAsText(String s) { setValue(Percentage.of(s)); }
    @Override public String getAsText() {
        return getValue() == null ? "" : getValue().toString();
    }
}

class ReportRequest {
    private String title;
    private DateRange period;
    private Percentage discountRate;

    public void setTitle(String t)            { this.title = t; }
    public void setPeriod(DateRange r)        { this.period = r; }
    public void setDiscountRate(Percentage p) { this.discountRate = p; }

    public String getTitle()          { return title; }
    public DateRange getPeriod()      { return period; }
    public Percentage getDiscountRate() { return discountRate; }
}

public class PropertyEditorDataBinder {
    public static void main(String[] args) {
        ReportRequest request = new ReportRequest();
        DataBinder binder = new DataBinder(request, "reportRequest");

        // Register custom editors
        binder.registerCustomEditor(DateRange.class,  new DateRangeEditor());
        binder.registerCustomEditor(Percentage.class, new PercentageEditor());

        MutablePropertyValues pvs = new MutablePropertyValues();
        pvs.add("title",        "Q2 Sales Report");
        pvs.add("period",       "2026-04-01:2026-06-30");
        pvs.add("discountRate", "12.5%");

        binder.bind(pvs);

        BindingResult result = binder.getBindingResult();
        if (result.hasErrors()) {
            result.getAllErrors().forEach(e ->
                System.out.println("ERROR: " + e.getDefaultMessage()));
        } else {
            System.out.println("title:        " + request.getTitle());
            System.out.println("period:       " + request.getPeriod());
            System.out.println("discountRate: " + request.getDiscountRate());
        }

        // Simulate a type-conversion failure
        System.out.println("\n--- bad period format ---");
        ReportRequest bad = new ReportRequest();
        DataBinder binder2 = new DataBinder(bad, "reportRequest");
        binder2.registerCustomEditor(DateRange.class, new DateRangeEditor());
        binder2.registerCustomEditor(Percentage.class, new PercentageEditor());

        MutablePropertyValues bad_pvs = new MutablePropertyValues();
        bad_pvs.add("period",       "not-a-date-range");
        bad_pvs.add("discountRate", "not-a-percent");
        binder2.bind(bad_pvs);

        binder2.getBindingResult().getFieldErrors().forEach(fe ->
            System.out.println("  field=" + fe.getField() +
                " code=" + fe.getCode() +
                " rejected='" + fe.getRejectedValue() + "'"));
    }
}
```

How to run: `java PropertyEditorDataBinder.java`

`binder.registerCustomEditor(DateRange.class, new DateRangeEditor())` makes `"2026-04-01:2026-06-30"` → `DateRange`. Conversion exceptions from `setAsText` are caught by `DataBinder` and recorded as `typeMismatch` errors.

### Level 3 — Advanced

Spring context with `CustomEditorConfigurer`; global editor registration; editor-per-type and editor-per-field.

```java
// PropertyEditorGlobal.java
import org.springframework.beans.*;
import org.springframework.beans.factory.annotation.*;
import org.springframework.beans.factory.config.*;
import org.springframework.context.annotation.*;
import java.beans.*;
import java.util.*;

record Version(int major, int minor, int patch) {
    static Version of(String s) {
        String[] p = s.split("\\.");
        return new Version(Integer.parseInt(p[0]), Integer.parseInt(p[1]), Integer.parseInt(p[2]));
    }
    @Override public String toString() { return major + "." + minor + "." + patch; }
}

class VersionEditor extends PropertyEditorSupport {
    @Override public void setAsText(String s) { setValue(Version.of(s)); }
    @Override public String getAsText() { return getValue() == null ? "" : getValue().toString(); }
}

class AppMetadata {
    @Value("${app.version}")  Version version;
    @Value("${app.name}")     String name;

    public void print() {
        System.out.println("App: " + name + " v" + version +
            " (major=" + version.major() + ")");
    }
}

@Configuration
@PropertySource("classpath:app-meta.properties")
@ComponentScan(basePackageClasses = PropertyEditorGlobal.class)
class EditorCfg {
    @Bean
    public CustomEditorConfigurer customEditorConfigurer() {
        var cfg = new CustomEditorConfigurer();
        cfg.setCustomEditors(Map.of(Version.class, VersionEditor.class));
        return cfg;
    }
}

public class PropertyEditorGlobal {
    public static void main(String[] args) throws Exception {
        java.nio.file.Files.writeString(java.nio.file.Path.of("app-meta.properties"),
            "app.version=3.14.1\napp.name=GlobalApp\n");

        var ctx = new AnnotationConfigApplicationContext(EditorCfg.class);
        ctx.getBean(AppMetadata.class).print();
        ctx.close();

        java.nio.file.Files.deleteIfExists(java.nio.file.Path.of("app-meta.properties"));
    }
}
```

How to run: `java PropertyEditorGlobal.java`

`CustomEditorConfigurer` registers `VersionEditor` globally — all beans in the context can use `@Value("${version.key}") Version v` without individual `binder.registerCustomEditor()` calls. The editor is shared but stateless, so this is thread-safe.

## 6. Walkthrough

Execution for Level 3:

1. **`CustomEditorConfigurer.setCustomEditors(Map.of(Version.class, VersionEditor.class))`** — registered globally as a `BeanFactoryPostProcessor`.
2. **Context refresh** — `CustomEditorConfigurer` runs, registers `VersionEditor` with the `BeanFactory`.
3. **`AppMetadata` bean instantiated** — `@Value("${app.version}")` → resolves to `"3.14.1"` via PSPC.
4. `BeanWrapper` for `AppMetadata` encounters `Version`-typed field — looks up registered editor → `VersionEditor`.
5. `VersionEditor.setAsText("3.14.1")` → `Version.of("3.14.1")` → `Version(3, 14, 1)`.
6. `version` field injected with `Version(3, 14, 1)`.

## 7. Gotchas & takeaways

> `PropertyEditor` is **NOT thread-safe** — each instance holds the current value in a mutable field (`setValue`/`getValue`). Never share a single `PropertyEditor` instance across threads. `CustomEditorConfigurer` accepts `Class<? extends PropertyEditor>` (not instances) precisely because Spring creates a new instance per use. When calling `binder.registerCustomEditor(Type.class, new MyEditor())`, you're safe in single-request scope; in multi-threaded contexts, always pass a fresh instance.

> Spring's `ConversionService` (next tutorial) is stateless and thread-safe — it is the preferred type conversion mechanism for new code. `PropertyEditor` is still used in Spring MVC form binding and `@Value` injection, but `ConversionService` is preferred for `DataBinder`-level conversion.

- `PropertyEditorSupport.setAsText` throwing any `IllegalArgumentException` causes `DataBinder` to record a `typeMismatch` error — no need to call `Errors` explicitly.
- For `@InitBinder` in Spring MVC: register per-field editors with `binder.registerCustomEditor(Type.class, "fieldName", new MyEditor())` — the second argument scopes the editor to that field only.
- Spring's built-in editors are in `org.springframework.beans.propertyeditors` — check there before writing a custom editor for common types.
- `PropertyEditorRegistrar` is a cleaner way to encapsulate a set of editor registrations — implement it and pass to `DataBinder.addValidators` or `CustomEditorConfigurer.setPropertyEditorRegistrars`.

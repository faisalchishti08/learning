---
card: spring-framework
gi: 191
slug: internationalization-messagesource
title: "Internationalization (MessageSource)"
---

## 1. What it is

`MessageSource` is Spring's interface for resolving locale-aware messages from a resource bundle (`.properties` files). Inject it into any bean to retrieve translated strings by key, optionally with message arguments and a fallback default.

```java
@Autowired
MessageSource messageSource;

public String greet(String name, Locale locale) {
    // Resolves "greeting" key from messages_en.properties or messages_fr.properties
    return messageSource.getMessage("greeting", new Object[]{name}, locale);
}
```

**`messages_en.properties`**
```properties
greeting=Hello, {0}!
```

**`messages_fr.properties`**
```properties
greeting=Bonjour, {0} !
```

Spring Boot auto-configures a `MessageSource` bean named `messageSource` backed by `messages.properties` on the classpath. Plain Spring requires an explicit bean definition.

## 2. Why & when

- **Multi-language web apps and APIs** — return locale-specific error messages, labels, and notifications.
- **Validation messages** — Spring Validation uses `MessageSource` to resolve constraint messages by key.
- **Thymeleaf / Spring MVC** — `#{key}` in templates resolves via `MessageSource`.
- **Don't use** when localisation is not a requirement — a plain `String` constant is simpler.

## 3. Core concept

`MessageSource` has three key methods:

```java
String getMessage(String code, Object[] args, Locale locale)              // throws NoSuchMessageException
String getMessage(String code, Object[] args, String defaultMessage, Locale locale)  // returns default if not found
String getMessage(MessageSourceResolvable resolvable, Locale locale)      // for MessageSourceAware objects
```

`{0}`, `{1}`, `{2}` in the message string are positional parameters filled from the `args` array via `java.text.MessageFormat`.

**Resolution chain (`HierarchicalMessageSource`):**
1. Try locale + variant → `messages_en_US.properties`
2. Try language only → `messages_en.properties`
3. Try base bundle → `messages.properties`
4. Delegate to parent `MessageSource` (if set)
5. Throw `NoSuchMessageException` or return default

**Built-in implementations:**

| Class | Use |
|---|---|
| `ResourceBundleMessageSource` | Standard `.properties` files; caches ResourceBundle at startup |
| `ReloadableResourceBundleMessageSource` | Can reload files at runtime (dev-friendly); supports non-classpath paths |
| `StaticMessageSource` | Programmatic key→message map; useful for tests |

## 4. Diagram

<svg viewBox="0 0 700 175" xmlns="http://www.w3.org/2000/svg">
  <defs>
    <marker id="msa" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L6,3 L0,6 Z" fill="#6db33f"/></marker>
  </defs>

  <!-- Service call -->
  <rect x="5" y="55" width="150" height="55" rx="4" fill="#1c2430" stroke="#6db33f" stroke-width="2"/>
  <text x="80" y="75" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif" font-weight="bold">Service / Controller</text>
  <text x="80" y="90" fill="#6db33f" font-size="8" text-anchor="middle" font-family="sans-serif">getMessage("err.notfound",</text>
  <text x="80" y="102" fill="#6db33f" font-size="8" text-anchor="middle" font-family="sans-serif">args, Locale.FRENCH)</text>

  <!-- MessageSource -->
  <rect x="200" y="30" width="180" height="100" rx="6" fill="#1c2430" stroke="#8b949e" stroke-width="1.5"/>
  <text x="290" y="52" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif" font-weight="bold">MessageSource</text>
  <text x="290" y="68" fill="#8b949e" font-size="7" text-anchor="middle" font-family="sans-serif">1. try messages_fr.properties</text>
  <text x="290" y="80" fill="#8b949e" font-size="7" text-anchor="middle" font-family="sans-serif">2. try messages.properties</text>
  <text x="290" y="92" fill="#8b949e" font-size="7" text-anchor="middle" font-family="sans-serif">3. parent MessageSource</text>
  <text x="290" y="104" fill="#8b949e" font-size="7" text-anchor="middle" font-family="sans-serif">4. throw NoSuchMessageException</text>
  <text x="290" y="116" fill="#6db33f" font-size="7" text-anchor="middle" font-family="sans-serif">fill {0},{1} via MessageFormat</text>
  <line x1="157" y1="82" x2="198" y2="82" stroke="#6db33f" stroke-width="1.5" marker-end="url(#msa)"/>

  <!-- Properties files -->
  <rect x="430" y="10" width="130" height="30" rx="4" fill="#79c0ff" opacity="0.2" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="495" y="29" fill="#79c0ff" font-size="8" text-anchor="middle" font-family="sans-serif">messages_fr.properties</text>

  <rect x="430" y="50" width="130" height="30" rx="4" fill="#6db33f" opacity="0.2" stroke="#6db33f" stroke-width="1.5"/>
  <text x="495" y="69" fill="#6db33f" font-size="8" text-anchor="middle" font-family="sans-serif">messages.properties</text>

  <rect x="430" y="90" width="130" height="30" rx="4" fill="#1c2430" stroke="#8b949e" stroke-width="1.5"/>
  <text x="495" y="109" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">messages_en.properties</text>

  <line x1="382" y1="65" x2="428" y2="25" stroke="#79c0ff" stroke-width="1.5" marker-end="url(#msa)"/>
  <line x1="382" y1="80" x2="428" y2="65" stroke="#6db33f" stroke-width="1.5" marker-end="url(#msa)"/>
  <line x1="382" y1="95" x2="428" y2="105" stroke="#8b949e" stroke-width="1.5" marker-end="url(#msa)"/>

  <!-- Return -->
  <text x="350" y="145" fill="#6db33f" font-size="8" text-anchor="middle" font-family="sans-serif">→ resolved: "Ressource introuvable : {id}"</text>
</svg>

`getMessage` walks locale variants → base bundle → parent; fills positional params via `MessageFormat` before returning the resolved string.

## 5. Runnable example

Scenario: **e-commerce error message service** — returns locale-specific error messages and labels.

### Level 1 — Basic

`StaticMessageSource` with explicit key→locale entries.

```java
// I18nBasic.java
import org.springframework.context.support.*;
import java.util.Locale;

public class I18nBasic {
    public static void main(String[] args) {
        var ms = new StaticMessageSource();
        ms.addMessage("order.notfound", Locale.ENGLISH, "Order {0} not found.");
        ms.addMessage("order.notfound", Locale.FRENCH,  "Commande {0} introuvable.");
        ms.addMessage("order.notfound", Locale.GERMAN,  "Bestellung {0} nicht gefunden.");

        ms.addMessage("order.total", Locale.ENGLISH, "Order total: {0} {1}");
        ms.addMessage("order.total", Locale.FRENCH,  "Total de la commande : {0} {1}");

        // Resolve with arguments
        System.out.println(ms.getMessage("order.notfound", new Object[]{"ORD-007"}, Locale.ENGLISH));
        System.out.println(ms.getMessage("order.notfound", new Object[]{"ORD-007"}, Locale.FRENCH));
        System.out.println(ms.getMessage("order.notfound", new Object[]{"ORD-007"}, Locale.GERMAN));

        // Default message when key is missing
        System.out.println(ms.getMessage("order.status", null,
            "Status unknown", Locale.ENGLISH));

        // With multiple args
        System.out.println(ms.getMessage("order.total", new Object[]{"99.90", "EUR"}, Locale.FRENCH));
    }
}
```

How to run: `java I18nBasic.java`

`StaticMessageSource` stores messages in memory — no files needed, great for tests. `getMessage(code, args, default, locale)` returns the default string if the key is missing, avoiding `NoSuchMessageException`.

### Level 2 — Intermediate

`ResourceBundleMessageSource` backed by `.properties` files; Spring context; locale fallback chain.

```java
// I18nIntermediate.java
import org.springframework.context.MessageSource;
import org.springframework.context.annotation.*;
import org.springframework.context.support.*;
import java.util.Locale;

@Configuration
class I18nConfig {
    @Bean
    public MessageSource messageSource() {
        var ms = new ResourceBundleMessageSource();
        ms.setBasenames("messages/app");    // looks for app.properties, app_fr.properties etc. in classpath
        ms.setDefaultEncoding("UTF-8");
        ms.setFallbackToSystemLocale(false); // don't use JVM locale; fall to base bundle
        return ms;
    }
}

public class I18nIntermediate {
    public static void main(String[] args) throws Exception {
        // Write temporary .properties files to the classpath root (for standalone demo)
        writeProps("messages/app.properties",
            "product.label=Product\nproduct.price=Price: {0,number,currency}\nproduct.oos=Out of stock");
        writeProps("messages/app_fr.properties",
            "product.label=Produit\nproduct.price=Prix : {0,number,currency}\nproduct.oos=En rupture de stock");
        writeProps("messages/app_de.properties",
            "product.label=Produkt\nproduct.price=Preis: {0,number,currency}");
        // Note: app_de.properties is missing product.oos → falls back to app.properties

        var ctx = new AnnotationConfigApplicationContext(I18nConfig.class);
        var ms = ctx.getBean(MessageSource.class);

        double price = 49.99;
        for (Locale locale : new Locale[]{Locale.ENGLISH, Locale.FRENCH, Locale.GERMAN}) {
            System.out.printf("[%s] label=%s | price=%s | oos=%s%n",
                locale.getLanguage(),
                ms.getMessage("product.label", null, locale),
                ms.getMessage("product.price", new Object[]{price}, locale),
                ms.getMessage("product.oos",   null, locale)
            );
        }
        ctx.close();
        cleanup();
    }
    static void writeProps(String path, String content) throws Exception {
        var f = new java.io.File(path);
        f.getParentFile().mkdirs();
        java.nio.file.Files.writeString(f.toPath(), content);
    }
    static void cleanup() {
        new java.io.File("messages/app.properties").delete();
        new java.io.File("messages/app_fr.properties").delete();
        new java.io.File("messages/app_de.properties").delete();
    }
}
```

How to run: `java I18nIntermediate.java`

`{0,number,currency}` uses `java.text.MessageFormat` currency formatting — the number is formatted according to the locale's currency convention. German locale falls back to the base `app.properties` for `product.oos` because `app_de.properties` doesn't contain that key.

### Level 3 — Advanced

Spring Boot auto-configured `MessageSource`; `MessageSourceResolvable`; `LocaleContextHolder`; validation messages.

```java
// I18nAdvanced.java
import org.springframework.boot.*;
import org.springframework.boot.autoconfigure.*;
import org.springframework.context.*;
import org.springframework.context.i18n.*;
import org.springframework.context.support.*;
import org.springframework.stereotype.*;
import java.util.Locale;

// MessageSourceResolvable carries the key + args + default, resolved lazily
record ErrorDetail(String code, Object[] args, String defaultMsg)
    implements MessageSourceResolvable {
    @Override public String[]   getCodes()          { return new String[]{code}; }
    @Override public Object[]   getArguments()      { return args; }
    @Override public String     getDefaultMessage()  { return defaultMsg; }
}

@Service
class ProductMessageService {
    private final MessageSource ms;
    ProductMessageService(MessageSource ms) { this.ms = ms; }

    public String resolveForCurrentLocale(String code, Object... args) {
        // LocaleContextHolder holds the locale for the current request thread
        Locale locale = LocaleContextHolder.getLocale();
        return ms.getMessage(code, args, locale);
    }

    public String resolveResolvable(MessageSourceResolvable resolvable) {
        return ms.getMessage(resolvable, LocaleContextHolder.getLocale());
    }
}

@SpringBootApplication
public class I18nAdvanced implements CommandLineRunner {
    private final ProductMessageService svc;
    I18nAdvanced(ProductMessageService svc) { this.svc = svc; }

    public static void main(String[] args) {
        SpringApplication.run(I18nAdvanced.class, args);
    }

    @Override
    public void run(String... args) throws Exception {
        // Write messages for Spring Boot (classpath:messages.properties)
        writeProps("src/main/resources/messages.properties",
            "product.available=Product {0} is available ({1} in stock)\n"
            + "product.error=Error for product {0}");
        writeProps("src/main/resources/messages_fr.properties",
            "product.available=Le produit {0} est disponible ({1} en stock)\n"
            + "product.error=Erreur pour le produit {0}");

        for (Locale locale : new Locale[]{Locale.ENGLISH, Locale.FRENCH}) {
            LocaleContextHolder.setLocale(locale);
            System.out.println("[" + locale.getLanguage() + "] direct: "
                + svc.resolveForCurrentLocale("product.available", "SKU-A", 42));

            var err = new ErrorDetail("product.error", new Object[]{"SKU-Z"}, "Unknown error");
            System.out.println("[" + locale.getLanguage() + "] resolvable: "
                + svc.resolveResolvable(err));
        }
        LocaleContextHolder.resetLocaleContext();
    }

    static void writeProps(String path, String content) throws Exception {
        var f = new java.io.File(path);
        f.getParentFile().mkdirs();
        java.nio.file.Files.writeString(f.toPath(), content);
    }
}
```

How to run: `./mvnw spring-boot:run` in a Spring Boot project.

`LocaleContextHolder` is Spring MVC's thread-local locale holder — `DispatcherServlet` sets it per-request from `Accept-Language` or `LocaleResolver`. `MessageSourceResolvable` is the interface used by Spring's validation framework (`FieldError`, `ObjectError`) so that validation messages are resolved via `MessageSource` and are therefore locale-aware.

## 6. Walkthrough

Tracing `ms.getMessage("product.price", new Object[]{49.99}, Locale.GERMAN)`:

**Step 1 — `ResourceBundleMessageSource` asked for `product.price` in `de`.**

**Step 2 — Resolution chain:**
- Try `messages/app_de.properties` → found? Yes, `"Preis: {0,number,currency}"`.

**Step 3 — `MessageFormat` applied:**
- Pattern: `"Preis: {0,number,currency}"`
- Args: `[49.99]`, locale: `de`
- `{0,number,currency}` formats `49.99` as `49,99 €` (German currency format).

**Step 4 — Returns `"Preis: 49,99 €"`.**

**If the key were missing from `app_de.properties`:**
- Try `app_de.properties` → miss
- Try `app.properties` (base bundle) → found `"Price: {0,number,currency}"`
- Format in German locale: `"Price: 49,99 €"` — English label but German number format (mixed — often an acceptable fallback).

## 7. Gotchas & takeaways

> **`setFallbackToSystemLocale(false)` on `ResourceBundleMessageSource` is usually what you want.** The default (`true`) falls back to the JVM's `Locale.getDefault()` before using the base bundle. This causes locale-specific tests to produce different results on different machines. Always set it to `false` in production.

> **`MessageFormat` interprets single quotes specially.** A literal `'` in a message pattern must be escaped as `''`. `"It''s ready"` → `"It's ready"`. Forgetting this silently drops text following a single quote.

- `ResourceBundleMessageSource` caches bundles at startup for performance. Use `ReloadableResourceBundleMessageSource` in dev to pick up file changes without restart (next tutorial).
- `getMessage(code, args, locale)` throws `NoSuchMessageException` if the key is missing and no default is provided. Always provide a fallback default in production code: `getMessage(code, args, code, locale)` (fall back to the key itself as a last resort).
- In Spring Boot, `spring.messages.basename` (default: `messages`) and `spring.messages.encoding` (default: `UTF-8`) configure the auto-configured `MessageSource`. Override them in `application.properties`.
- Validation: when Spring Validation rejects a field, it creates `FieldError` objects whose codes follow a convention like `NotBlank.user.email`, `NotBlank.email`, `NotBlank`, allowing fine-grained message customisation in `messages.properties`.

---
card: spring-boot
gi: 267
slug: internationalization-messagesource-auto-config
title: Internationalization (MessageSource auto-config)
---

## 1. What it is

**Internationalization (i18n)** in Spring Boot means providing translated text, locale-aware formatting, and culture-specific content so the same application serves users in different languages and regions correctly.

Spring Boot auto-configures a `MessageSource` bean when message property files are found on the classpath. The default base name is `messages`, so Spring looks for:

- `messages.properties` — default (fallback) messages
- `messages_fr.properties` — French
- `messages_de.properties` — German
- `messages_zh_CN.properties` — Simplified Chinese

Beyond `MessageSource`, full i18n involves:
- **`LocaleResolver`** — decides the current locale (from Accept-Language header, URL parameter, cookie, session).
- **`LocaleChangeInterceptor`** — changes the locale based on a URL parameter (e.g., `?lang=fr`).
- **Thymeleaf / JSP integration** — `#{message.key}` in templates resolves via `MessageSource`.
- **Validation messages** — `@NotBlank`, `@Size`, etc. read from `messages.properties` automatically.

## 2. Why & when

You need i18n when:
- Your app serves users in multiple languages.
- You need locale-aware date, number, or currency formatting (a price of `1,234.50` in English, `1.234,50` in German).
- You want validation error messages in the user's language.
- You have regulatory requirements to support specific locales.

Even for single-language apps, externalising all user-visible strings into `messages.properties` is good practice — it separates content from code and makes future i18n trivial.

## 3. Core concept

The auto-configuration chain:

1. `MessageSourceAutoConfiguration` detects `messages.properties` on the classpath and creates a `ResourceBundleMessageSource` bean.
2. Messages are looked up with `messageSource.getMessage("key", args, locale)`.
3. Thymeleaf's `#{key}` and Spring MVC's `@ModelAttribute` bindings call `MessageSource` automatically.
4. `LocaleResolver` (default: `AcceptHeaderLocaleResolver`) reads the browser's `Accept-Language: fr-FR` header and returns the locale.
5. Spring MVC chooses the right `.properties` file for that locale.

Key property:
```properties
spring.messages.basename=messages,i18n/errors
spring.messages.encoding=UTF-8
spring.messages.fallback-to-system-locale=false
spring.messages.cache-duration=3600s
```

The `basename` can be a comma-separated list, allowing messages to be split across files (e.g., main messages + validation messages separately).

## 4. Diagram

<svg viewBox="0 0 700 240" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Spring Boot MessageSource i18n flow from HTTP request locale detection to translated message lookup">
  <defs>
    <marker id="arr" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#6db33f"/></marker>
  </defs>

  <!-- HTTP Request -->
  <rect x="10" y="95" width="120" height="50" rx="6" fill="#1c2430" stroke="#8b949e" stroke-width="1.5"/>
  <text x="70" y="115" fill="#e6edf3" font-size="11" text-anchor="middle" font-family="sans-serif">HTTP Request</text>
  <text x="70" y="133" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">Accept-Language: fr</text>

  <!-- LocaleResolver -->
  <rect x="175" y="80" width="140" height="80" rx="6" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="245" y="105" fill="#e6edf3" font-size="11" text-anchor="middle" font-family="sans-serif">LocaleResolver</text>
  <text x="245" y="123" fill="#79c0ff" font-size="9" text-anchor="middle" font-family="sans-serif">Extracts Locale</text>
  <text x="245" y="141" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">→ Locale.FRENCH</text>

  <!-- MessageSource -->
  <rect x="360" y="80" width="160" height="80" rx="6" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="440" y="105" fill="#e6edf3" font-size="11" text-anchor="middle" font-family="sans-serif">MessageSource</text>
  <text x="440" y="123" fill="#6db33f" font-size="9" text-anchor="middle" font-family="sans-serif">messages_fr.properties</text>
  <text x="440" y="141" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">welcome=Bonjour!</text>

  <!-- Response -->
  <rect x="570" y="95" width="120" height="50" rx="6" fill="#1c2430" stroke="#6db33f" stroke-width="2"/>
  <text x="630" y="115" fill="#e6edf3" font-size="11" text-anchor="middle" font-family="sans-serif">Response</text>
  <text x="630" y="133" fill="#6db33f" font-size="9" text-anchor="middle" font-family="sans-serif">Bonjour!</text>

  <!-- Arrows -->
  <line x1="130" y1="120" x2="173" y2="120" stroke="#8b949e" stroke-width="1.5" marker-end="url(#arr)"/>
  <line x1="315" y1="120" x2="358" y2="120" stroke="#79c0ff" stroke-width="1.5" marker-end="url(#arr)"/>
  <line x1="520" y1="120" x2="568" y2="120" stroke="#6db33f" stroke-width="1.5" marker-end="url(#arr)"/>

  <!-- Property files -->
  <text x="350" y="210" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">src/main/resources/messages.properties  messages_fr.properties  messages_de.properties  ...</text>
</svg>

The request's Accept-Language header drives locale detection; MessageSource looks up the right properties file automatically.

## 5. Runnable example

```java
// I18nDemo.java — run with: java I18nDemo.java
// Demonstrates Spring Boot MessageSource auto-configuration, message
// file format, LocaleResolver setup, and Thymeleaf integration patterns.

import java.text.*;
import java.util.*;

public class I18nDemo {

    // Simulated message source (Spring auto-configures ResourceBundleMessageSource)
    static final Map<Locale, Map<String,String>> MESSAGES = Map.of(
        Locale.ENGLISH, Map.of(
            "welcome",          "Hello, {0}!",
            "items.count",      "You have {0} item(s) in your cart.",
            "price.label",      "Price:",
            "error.required",   "This field is required."
        ),
        Locale.FRENCH, Map.of(
            "welcome",          "Bonjour, {0} !",
            "items.count",      "Vous avez {0} article(s) dans votre panier.",
            "price.label",      "Prix :",
            "error.required",   "Ce champ est obligatoire."
        ),
        Locale.GERMAN, Map.of(
            "welcome",          "Hallo, {0}!",
            "items.count",      "Sie haben {0} Artikel in Ihrem Warenkorb.",
            "price.label",      "Preis:",
            "error.required",   "Dieses Feld ist erforderlich."
        )
    );

    public static void main(String[] args) {
        System.out.println("=== Spring Boot MessageSource i18n Demo ===\n");

        printFileStructure();
        demonstrateMessages();
        demonstrateLocaleFormats();
        printSpringConfig();
    }

    static void printFileStructure() {
        System.out.println("--- File structure (src/main/resources/) ---");
        System.out.println("""
            messages.properties          ← default (English fallback)
            messages_fr.properties       ← French
            messages_de.properties       ← German
            messages_zh_CN.properties    ← Simplified Chinese
            messages_ja.properties       ← Japanese

            # Optional: split by concern
            # spring.messages.basename=messages,validation/messages
            validation/messages.properties
            validation/messages_fr.properties
            """);
    }

    static void demonstrateMessages() {
        System.out.println("--- Message lookup simulation ---");
        for (Locale locale : List.of(Locale.ENGLISH, Locale.FRENCH, Locale.GERMAN)) {
            Map<String,String> msgs = MESSAGES.getOrDefault(locale, MESSAGES.get(Locale.ENGLISH));

            String welcome = MessageFormat.format(
                msgs.getOrDefault("welcome", "Hello, {0}!"), "Maria");
            String cart = MessageFormat.format(
                msgs.getOrDefault("items.count", "You have {0} item(s)."), 3);

            System.out.printf("  [%s] %s | %s%n", locale.getLanguage(), welcome, cart);
        }
        System.out.println();
    }

    static void demonstrateLocaleFormats() {
        System.out.println("--- Locale-aware number and date formatting ---");
        double price = 1234.56;
        Date date = new Date();

        for (Locale locale : List.of(Locale.US, Locale.FRANCE, Locale.GERMANY, Locale.JAPAN)) {
            String formattedPrice = NumberFormat.getCurrencyInstance(locale).format(price);
            String formattedDate  = DateFormat.getDateInstance(DateFormat.MEDIUM, locale).format(date);
            System.out.printf("  %-8s  price: %-18s  date: %s%n",
                locale.getLanguage(), formattedPrice, formattedDate);
        }
        System.out.println();
    }

    static void printSpringConfig() {
        System.out.println("--- application.properties ---");
        System.out.println("""
            spring.messages.basename=messages
            spring.messages.encoding=UTF-8
            spring.messages.cache-duration=3600s
            spring.messages.fallback-to-system-locale=false

            # --- WebMvcConfigurer setup (Java config) ---
            # @Bean LocaleResolver localeResolver() {
            #   CookieLocaleResolver r = new CookieLocaleResolver("locale");
            #   r.setDefaultLocale(Locale.ENGLISH);
            #   return r;
            # }
            # @Bean LocaleChangeInterceptor localeChangeInterceptor() {
            #   LocaleChangeInterceptor i = new LocaleChangeInterceptor();
            #   i.setParamName("lang");   // ?lang=fr changes the locale
            #   return i;
            # }
            """);

        System.out.println("--- Thymeleaf template usage ---");
        System.out.println("""
            <!-- messages.properties: welcome=Hello, {0}! -->
            <p th:text="#{welcome(${user.name})}">Hello</p>

            <!-- messages_fr.properties: welcome=Bonjour, {0} ! -->
            <!-- With Accept-Language: fr, renders: Bonjour, Maria ! -->

            <!-- Validation messages auto-resolved: -->
            <span th:errors="*{email}" th:class="error">Error</span>
            <!-- Uses NotBlank.user.email or NotBlank from messages.properties -->
            """);
    }
}
```

**How to run:** `java I18nDemo.java`

## 6. Walkthrough

- **`MessageFormat.format(template, args)`** — shows how Spring's `messageSource.getMessage("welcome", new Object[]{"Maria"}, locale)` works internally. The `{0}` token in the message string is substituted by `MessageFormat` with the provided argument array.
- **`NumberFormat.getCurrencyInstance(locale).format(price)`** — demonstrates locale-aware formatting. The same `1234.56` becomes `$1,234.56` (US), `1 234,56 €` (France), `1.234,56 €` (Germany), `¥1,235` (Japan). Spring's `@NumberFormat` and Thymeleaf's `#numbers.formatCurrency(price)` use this JDK mechanism.
- **`fallback-to-system-locale=false`** — prevents Spring from falling back to the OS locale when no message is found in the requested locale. With `true`, a French request might get unexpected English messages if German is the server's OS locale. Set to `false` to always fall back to `messages.properties`.
- **`cache-duration=3600s`** — `ResourceBundleMessageSource` caches message files after first load. In development, set this to `0` (or DevTools sets it automatically) so you can edit message files without restarting. In production, `3600s` (1 hour) prevents repeated file system reads.
- **`LocaleChangeInterceptor` with `?lang=fr`** — the most user-friendly locale-switching mechanism. A URL like `https://example.com/products?lang=fr` switches the locale to French for all subsequent requests (stored in a cookie or session, depending on the `LocaleResolver`).

## 7. Gotchas & takeaways

> **Message files must be in UTF-8 and declared as such.** Java's `ResourceBundle` historically read `.properties` files as ISO-8859-1 (Latin-1). Spring Boot sets `spring.messages.encoding=UTF-8` by default; if you're using IntelliJ, also check `Settings → Editor → File Encodings` and set the properties file encoding to UTF-8 — otherwise Chinese/Japanese characters are saved as `?`.

> **`fallback-to-system-locale=false` is essential for predictable behaviour.** With the default `true`, if no message file matches the requested locale, Spring falls back to the JVM's default locale (set by the OS or `-Duser.language`). In a Docker container this might be `POSIX` or `C`, giving users nonsensical fallback text. Set to `false` to always fall back to `messages.properties`.

- Message keys for validation: Spring MVC uses `<annotation>.<objectName>.<fieldName>` (e.g., `NotBlank.user.email`) or just `NotBlank` as fallback. Define these in `messages.properties` to translate validation errors.
- Use `LocaleContextHolder.getLocale()` in service layer code when you need the current locale outside of a controller.
- `AcceptHeaderLocaleResolver` (default) reads `Accept-Language` — useful for REST APIs. `CookieLocaleResolver` or `SessionLocaleResolver` are better for traditional web apps where users explicitly switch language.
- Test i18n: set `Accept-Language: fr` header in Postman/curl and verify responses are in French.
- The `spring-boot-starter-thymeleaf` includes Thymeleaf's i18n support — `#{key}` and `#{key(arg)}` resolve via `MessageSource` automatically.

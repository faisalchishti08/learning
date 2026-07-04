---
card: spring-framework
gi: 300
slug: locale-theme-resolution
title: "Locale & theme resolution"
---

## 1. What it is

**Locale resolution** is the mechanism by which Spring MVC determines the current `java.util.Locale` for each HTTP request — used by message sources (i18n), date/number formatting, and Thymeleaf template selection.

**Theme resolution** (deprecated / historical) was an analogous mechanism for selecting a named CSS/image theme per request.  Spring 6 removed `ThemeResolver` from the default configuration; modern apps handle theming entirely in client-side code.  This tutorial focuses on locale resolution as the live, still-relevant half.

`LocaleResolver` is a strategy interface with six built-in implementations:

| Implementation | Source of locale |
|---|---|
| `AcceptHeaderLocaleResolver` | `Accept-Language` HTTP header (default) |
| `SessionLocaleResolver` | HTTP session attribute |
| `CookieLocaleResolver` | browser cookie |
| `FixedLocaleResolver` | always the same locale (for testing) |
| `LocaleContextResolver` | extension point for time-zone-aware locale |

`DispatcherServlet` calls `LocaleResolver.resolveLocale(request)` early in every request and stores the result in `LocaleContextHolder` — a thread-local accessible throughout the request lifecycle.

---

## 2. Why & when

Use locale resolution when:

- Serving translated content with `MessageSource` (Spring i18n) or `th:text="#{key}"` in Thymeleaf.
- Formatting dates and numbers per-locale (`DateTimeFormatter`, `NumberFormat`).
- Allowing users to pick their preferred language (session or cookie resolver + `LocaleChangeInterceptor`).

`AcceptHeaderLocaleResolver` requires zero configuration and works for REST APIs where the client sets `Accept-Language`.  Use `SessionLocaleResolver` or `CookieLocaleResolver` when the user can change their language via a UI control and you want the preference to persist across requests.

---

## 3. Core concept

```
Request arrives
  ↓
DispatcherServlet.doDispatch()
  ↓
LocaleResolver.resolveLocale(request)    → Locale (e.g. "fr_FR")
  ↓
LocaleContextHolder.setLocale(locale)    ← thread-local
  ↓
Controller / Service / Template reads:
  LocaleContextHolder.getLocale()
  MessageSource.getMessage("key", null, locale)
  th:text="#{welcome}"  → "Bienvenue" (fr template)
```

`LocaleChangeInterceptor` sits in the interceptor chain and reads a query parameter (e.g. `?lang=fr`) to mutate the locale stored in the resolver before the controller runs.

---

## 4. Diagram

<svg viewBox="0 0 760 310" xmlns="http://www.w3.org/2000/svg" font-family="monospace" font-size="12">
  <rect width="760" height="310" fill="#0d1117"/>

  <!-- Request -->
  <rect x="10" y="130" width="140" height="50" rx="5" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="80" y="150" text-anchor="middle" fill="#79c0ff">HTTP Request</text>
  <text x="80" y="165" text-anchor="middle" fill="#8b949e" font-size="10">Accept-Language: fr,en;q=0.8</text>
  <text x="80" y="178" text-anchor="middle" fill="#8b949e" font-size="10">?lang=de (optional)</text>

  <!-- arrow -->
  <line x1="150" y1="155" x2="195" y2="155" stroke="#8b949e" marker-end="url(#al)"/>

  <!-- LocaleChangeInterceptor -->
  <rect x="195" y="120" width="155" height="70" rx="5" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="272" y="142" text-anchor="middle" fill="#6db33f">LocaleChange</text>
  <text x="272" y="156" text-anchor="middle" fill="#6db33f">Interceptor</text>
  <text x="272" y="172" text-anchor="middle" fill="#8b949e" font-size="10">reads ?lang= param</text>
  <text x="272" y="185" text-anchor="middle" fill="#8b949e" font-size="10">calls resolver.setLocale()</text>

  <!-- arrow -->
  <line x1="350" y1="155" x2="395" y2="155" stroke="#8b949e" marker-end="url(#al)"/>

  <!-- LocaleResolver box -->
  <rect x="395" y="100" width="165" height="110" rx="5" fill="#1c2430" stroke="#6db33f" stroke-width="1"/>
  <text x="477" y="120" text-anchor="middle" fill="#6db33f" font-weight="bold">LocaleResolver</text>
  <rect x="405" y="128" width="145" height="20" rx="3" fill="#0d1117" stroke="#6db33f"/>
  <text x="477" y="142" text-anchor="middle" fill="#6db33f" font-size="11">AcceptHeaderLocaleResolver</text>
  <rect x="405" y="153" width="145" height="20" rx="3" fill="#0d1117" stroke="#8b949e"/>
  <text x="477" y="167" text-anchor="middle" fill="#8b949e" font-size="11">SessionLocaleResolver</text>
  <rect x="405" y="178" width="145" height="20" rx="3" fill="#0d1117" stroke="#8b949e"/>
  <text x="477" y="192" text-anchor="middle" fill="#8b949e" font-size="11">CookieLocaleResolver</text>

  <!-- Locale result arrow -->
  <line x1="560" y1="155" x2="605" y2="155" stroke="#6db33f" marker-end="url(#al)"/>
  <text x="582" y="148" text-anchor="middle" fill="#6db33f" font-size="10">Locale</text>

  <!-- LocaleContextHolder -->
  <rect x="605" y="130" width="145" height="50" rx="5" fill="#1c2430" stroke="#79c0ff" stroke-width="1"/>
  <text x="677" y="150" text-anchor="middle" fill="#79c0ff">LocaleContext</text>
  <text x="677" y="165" text-anchor="middle" fill="#79c0ff">Holder</text>

  <!-- ThreadLocal annotation -->
  <text x="677" y="198" text-anchor="middle" fill="#8b949e" font-size="10">(thread-local)</text>

  <!-- Usage arrow down -->
  <line x1="677" y1="180" x2="677" y2="230" stroke="#8b949e" stroke-dasharray="3,2" marker-end="url(#al)"/>
  <rect x="565" y="230" width="220" height="40" rx="5" fill="#1c2430" stroke="#8b949e"/>
  <text x="675" y="248" text-anchor="middle" fill="#e6edf3">MessageSource / Thymeleaf</text>
  <text x="675" y="262" text-anchor="middle" fill="#8b949e" font-size="10">getMessage("key", null, locale)</text>

  <!-- caption -->
  <text x="380" y="295" text-anchor="middle" fill="#8b949e" font-size="11">LocaleChangeInterceptor mutates resolver state; LocaleContextHolder exposes locale thread-locally</text>

  <defs>
    <marker id="al" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto">
      <path d="M0,0 L0,6 L8,3 z" fill="#8b949e"/>
    </marker>
  </defs>
</svg>

*`LocaleResolver` determines the locale once per request; `LocaleContextHolder` distributes it to every layer without method parameters.*

---

## 5. Runnable example

### Level 1 — Basic

A simple controller that greets users in their browser language using `MessageSource`:

```java
// GreetingController.java
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.context.MessageSource;
import org.springframework.web.bind.annotation.*;
import java.util.Locale;

@RestController
public class GreetingController {
    @Autowired MessageSource messageSource;

    @GetMapping("/greet")
    public String greet(Locale locale) { // Spring injects the resolved locale here
        return messageSource.getMessage("greeting", null, locale);
    }
}
```

```properties
# src/main/resources/messages.properties  (default / English)
greeting=Hello!
```

```properties
# src/main/resources/messages_fr.properties
greeting=Bonjour!
```

```properties
# src/main/resources/messages_de.properties
greeting=Hallo!
```

```properties
# application.properties — AcceptHeaderLocaleResolver is the default, nothing to configure
spring.messages.basename=messages
```

**How to run:**
```bash
./mvnw spring-boot:run

curl -H "Accept-Language: fr" http://localhost:8080/greet
# Bonjour!

curl -H "Accept-Language: de" http://localhost:8080/greet
# Hallo!

curl -H "Accept-Language: ja" http://localhost:8080/greet
# Hello!   (fallback to default)
```

`AcceptHeaderLocaleResolver` parses the `Accept-Language` header's quality-weighted list (`fr,en;q=0.8`) and returns the best-matching `Locale`.  Spring injects the resolved locale directly into the controller method as a `Locale` parameter (populated from `LocaleContextHolder`).  `MessageSource.getMessage()` looks up the `greeting` key in `messages_fr.properties` for `Locale.FRENCH`.

---

### Level 2 — Intermediate

Same i18n scenario — user greeting — but now the user can **change their preferred language** via a URL parameter (`?lang=fr`), and the preference is persisted in the HTTP session using `SessionLocaleResolver` + `LocaleChangeInterceptor`:

```java
// MvcConfig.java
import org.springframework.context.annotation.*;
import org.springframework.web.servlet.LocaleResolver;
import org.springframework.web.servlet.config.annotation.*;
import org.springframework.web.servlet.i18n.*;
import java.util.Locale;

@Configuration
public class MvcConfig implements WebMvcConfigurer {

    @Bean
    public LocaleResolver localeResolver() {
        SessionLocaleResolver slr = new SessionLocaleResolver();
        slr.setDefaultLocale(Locale.ENGLISH); // fallback when no session key yet
        return slr;
    }

    @Bean
    public LocaleChangeInterceptor localeChangeInterceptor() {
        LocaleChangeInterceptor lci = new LocaleChangeInterceptor();
        lci.setParamName("lang"); // reads ?lang=XX
        return lci;
    }

    @Override
    public void addInterceptors(InterceptorRegistry registry) {
        registry.addInterceptor(localeChangeInterceptor());
    }
}
```

**How to run:**
```bash
./mvnw spring-boot:run

# First request — defaults to English
curl -c cookies.txt http://localhost:8080/greet
# Hello!

# Switch to French
curl -c cookies.txt -b cookies.txt "http://localhost:8080/greet?lang=fr"
# Bonjour!

# Second request — session remembers French, no ?lang needed
curl -b cookies.txt http://localhost:8080/greet
# Bonjour!
```

**What changed:** `SessionLocaleResolver` stores the chosen locale in the HTTP session under a well-known attribute key.  `LocaleChangeInterceptor.preHandle()` reads `req.getParameter("lang")`, converts it to a `Locale`, and calls `localeResolver.setLocale(req, res, newLocale)` — which writes the new locale into the session.  Subsequent requests without `?lang=` read the stored session locale instead of the `Accept-Language` header.

---

### Level 3 — Advanced

Production scenario: `CookieLocaleResolver` so locale preference persists across sessions (no server-side state), plus support for only an **allowed set of locales**, rejecting unsupported ones with a 400:

```java
// MvcConfig.java (cookie-based, validated)
import org.springframework.web.servlet.i18n.*;
import org.springframework.web.servlet.*;
import jakarta.servlet.http.*;
import java.util.*;

@Configuration
public class MvcConfig implements WebMvcConfigurer {

    private static final Set<String> SUPPORTED = Set.of("en", "fr", "de", "ja");

    @Bean
    public LocaleResolver localeResolver() {
        CookieLocaleResolver clr = new CookieLocaleResolver("APP_LOCALE");
        clr.setDefaultLocale(Locale.ENGLISH);
        clr.setCookieMaxAge(Duration.ofDays(365)); // 1 year
        clr.setCookieHttpOnly(true);
        return clr;
    }

    @Bean
    public LocaleChangeInterceptor localeChangeInterceptor() {
        return new LocaleChangeInterceptor() {
            @Override
            public boolean preHandle(HttpServletRequest req,
                                     HttpServletResponse res, Object handler) throws Exception {
                String lang = req.getParameter(getParamName());
                if (lang != null && !SUPPORTED.contains(lang)) {
                    res.sendError(HttpServletResponse.SC_BAD_REQUEST,
                                  "Unsupported locale: " + lang);
                    return false;
                }
                return super.preHandle(req, res, handler);
            }
        };
    }

    @Override
    public void addInterceptors(InterceptorRegistry registry) {
        registry.addInterceptor(localeChangeInterceptor());
    }
}
```

```java
// GreetingController.java (unchanged from Level 1)
@GetMapping("/greet")
public String greet(Locale locale) {
    return messageSource.getMessage("greeting", null, locale);
}
```

**How to run:**
```bash
./mvnw spring-boot:run

# Switch to French — sets APP_LOCALE cookie
curl -c cookies.txt -b cookies.txt "http://localhost:8080/greet?lang=fr"
# Bonjour!
# Response: Set-Cookie: APP_LOCALE=fr; Max-Age=31536000; HttpOnly

# Cookie persists across sessions:
curl -b "APP_LOCALE=fr" http://localhost:8080/greet
# Bonjour!

# Unsupported locale:
curl -i "http://localhost:8080/greet?lang=xx"
# HTTP/1.1 400 Bad Request: Unsupported locale: xx
```

**What changed and why:**
- `CookieLocaleResolver` stores the locale in a browser cookie rather than the server session — no server memory consumed, works across load-balanced instances without sticky sessions.
- `setCookieMaxAge(365 days)` makes the preference survive browser restarts.
- `setCookieHttpOnly(true)` prevents JavaScript from reading the cookie — baseline security for any cookie that isn't needed client-side.
- The custom `LocaleChangeInterceptor` override rejects unsupported locales with 400 before calling `super.preHandle()`, preventing `IllegalArgumentException` from `Locale.forLanguageTag("xx")` and blocking locale-injection attacks.

<svg viewBox="0 0 700 210" xmlns="http://www.w3.org/2000/svg" font-family="monospace" font-size="11">
  <rect width="700" height="210" fill="#0d1117"/>

  <!-- Cookie resolver flow -->
  <rect x="10" y="40" width="120" height="40" rx="4" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="70" y="58" text-anchor="middle" fill="#79c0ff">Request</text>
  <text x="70" y="73" text-anchor="middle" fill="#8b949e" font-size="10">Cookie: APP_LOCALE=fr</text>

  <line x1="130" y1="60" x2="165" y2="60" stroke="#8b949e" marker-end="url(#alc)"/>

  <rect x="165" y="40" width="145" height="40" rx="4" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="237" y="58" text-anchor="middle" fill="#6db33f">CookieLocaleResolver</text>
  <text x="237" y="73" text-anchor="middle" fill="#8b949e" font-size="10">reads APP_LOCALE cookie</text>

  <line x1="310" y1="60" x2="345" y2="60" stroke="#8b949e" marker-end="url(#alc)"/>

  <rect x="345" y="40" width="120" height="40" rx="4" fill="#1c2430" stroke="#6db33f" stroke-width="1"/>
  <text x="405" y="58" text-anchor="middle" fill="#6db33f">Locale.FRENCH</text>
  <text x="405" y="73" text-anchor="middle" fill="#8b949e" font-size="10">→ LocaleContextHolder</text>

  <line x1="465" y1="60" x2="500" y2="60" stroke="#8b949e" marker-end="url(#alc)"/>

  <rect x="500" y="40" width="130" height="40" rx="4" fill="#1c2430" stroke="#8b949e" stroke-width="1"/>
  <text x="565" y="58" text-anchor="middle" fill="#e6edf3">messages_fr.properties</text>
  <text x="565" y="73" text-anchor="middle" fill="#8b949e" font-size="10">greeting=Bonjour!</text>

  <!-- Response with Set-Cookie -->
  <rect x="165" y="120" width="145" height="50" rx="4" fill="#1c2430" stroke="#6db33f" stroke-width="1"/>
  <text x="237" y="140" text-anchor="middle" fill="#6db33f">?lang=de change</text>
  <text x="237" y="155" text-anchor="middle" fill="#8b949e" font-size="10">Set-Cookie: APP_LOCALE=de</text>
  <text x="237" y="169" text-anchor="middle" fill="#8b949e" font-size="10">Max-Age=31536000; HttpOnly</text>

  <text x="350" y="200" text-anchor="middle" fill="#8b949e" font-size="10">Cookie persists locale across sessions — no server memory required</text>

  <defs><marker id="alc" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L0,6 L8,3 z" fill="#8b949e"/></marker></defs>
</svg>

---

## 6. Walkthrough

**Startup (once):**

1. `MvcConfig` registers `CookieLocaleResolver` as the bean named `localeResolver` — `DispatcherServlet` discovers it by that exact bean name.
2. `LocaleChangeInterceptor` is registered in the interceptor chain (order 0).
3. `MessageSource` scans `classpath:/messages*.properties` and builds a locale → bundle map.

**Per-request — locale change (`?lang=fr`):**

4. `GET /greet?lang=fr` arrives, cookie `APP_LOCALE=de` (previous preference).
5. `LocaleChangeInterceptor.preHandle()` reads `lang=fr`, validates against `SUPPORTED` set — valid.
6. Calls `localeResolver.setLocale(req, res, Locale.FRENCH)`.
7. `CookieLocaleResolver.setLocale()` writes `Set-Cookie: APP_LOCALE=fr; Max-Age=31536000; HttpOnly` to the response.
8. Handler runs. `DispatcherServlet` calls `localeResolver.resolveLocale(req)` — reads the *just-set* locale from the cookie store (now `fr`).
9. `LocaleContextHolder.setLocale(Locale.FRENCH)`.
10. `GreetingController.greet(Locale.FRENCH)` called. `messageSource.getMessage("greeting", null, Locale.FRENCH)` returns `"Bonjour!"`.
11. Response: `200 OK` body `Bonjour!` + `Set-Cookie: APP_LOCALE=fr`.

**State changes at each layer:**

| Layer | State |
|---|---|
| Interceptor.preHandle | validates lang param; calls setLocale() |
| CookieLocaleResolver | writes Set-Cookie header; stores locale in response |
| DispatcherServlet.resolveLocale | reads cookie → Locale.FRENCH |
| LocaleContextHolder | thread-local Locale = FRENCH |
| MessageSource | key "greeting" → "Bonjour!" |
| Response | 200 + "Bonjour!" + Set-Cookie |

**Next request (no `?lang=`, cookie `APP_LOCALE=fr`):**

`CookieLocaleResolver.resolveLocale()` reads the cookie, returns `Locale.FRENCH` directly — no interceptor change needed.

---

## 7. Gotchas & takeaways

> **The bean must be named `localeResolver` (exact spelling).**  `DispatcherServlet` looks it up by this name in the application context.  A differently named bean of type `LocaleResolver` is silently ignored; `AcceptHeaderLocaleResolver` stays active.

> **`LocaleChangeInterceptor` must be registered BEFORE the controller interceptors that use the locale.**  It mutates the locale via `setLocale()`; any interceptor running before it will see the old locale.  Register it first in `addInterceptors()`.

> **`AcceptHeaderLocaleResolver` does not support `setLocale()` — it always reads the header.**  Calling `localeResolver.setLocale()` throws `UnsupportedOperationException`.  Only `SessionLocaleResolver` and `CookieLocaleResolver` support runtime locale changes.

- Default resolver: `AcceptHeaderLocaleResolver` — zero config, reads `Accept-Language` header.
- `SessionLocaleResolver`: persists locale server-side (session); needs sticky sessions or session replication in clusters.
- `CookieLocaleResolver`: persists locale client-side; stateless servers, works in load-balanced setups.
- `LocaleContextHolder.getLocale()` gives the current locale anywhere in the request thread (services, helpers) without method parameters.
- Always validate the `?lang=` parameter against a supported-locales whitelist to prevent locale injection.
- Theme resolution (`ThemeResolver`) was removed from Spring 6 defaults — use CSS classes / JavaScript for theming instead.

---
card: spring-security
gi: 124
slug: localization-of-messages
title: "Localization of messages"
---

## 1. What it is

Every exception this course has covered — `BadCredentialsException`, `LockedException`, `AccountExpiredException`, `AccessDeniedException` — carries a default English message, but Spring Security never hard-codes that text directly into the exception classes themselves; instead, every message is looked up through a `MessageSourceAccessor`, backed by Spring's general-purpose `MessageSource` infrastructure, using a specific message code (`"AbstractUserDetailsAuthenticationProvider.badCredentials"`, for instance) as the lookup key. Spring Security ships its own default translations for this exact set of codes across many languages inside `spring-security-core`'s `messages.properties` (and `messages_de.properties`, `messages_fr.properties`, and so on) — an application only needs to override specific codes, or add support for an additional locale, rather than reimplementing the whole message catalog.

```properties
# messages.properties (English default, ships with spring-security-core)
AbstractUserDetailsAuthenticationProvider.badCredentials=Bad credentials
AbstractUserDetailsAuthenticationProvider.locked=User account is locked
AbstractUserDetailsAuthenticationProvider.expired=User account has expired
AccessDeniedException=Access is denied
```
```java
@Bean
public MessageSource messageSource() {
    ReloadableResourceBundleMessageSource messageSource = new ReloadableResourceBundleMessageSource();
    messageSource.setBasenames("classpath:custom-messages", "classpath:org/springframework/security/messages");
    messageSource.setDefaultEncoding("UTF-8");
    return messageSource;
}
```

## 2. Why & when

Every earlier card that discussed a specific exception (card 0054's account-status exceptions, card 0100's JWT resource server failures) focused on *which* exception fires and *when* — but the actual text a user or API consumer sees is a genuinely separate concern, and hard-coding it in English inside the framework itself would make every non-English-speaking deployment either live with English error messages or fork the framework to change them. Message externalization via `MessageSource` — the same mechanism Spring itself uses for validation error messages and other user-facing text throughout the ecosystem — lets Spring Security ship translated defaults for common cases while remaining fully overridable per application, per specific message, or per additional locale an application needs to support.

Reach for customizing message localization when:

- The application serves users in multiple languages and needs authentication/authorization error messages to appear in the user's own locale, matching the rest of the application's already-localized UI text.
- A specific default message needs different wording for a particular application's tone or terminology — overriding just that one code, rather than the whole catalog, in a custom `messages.properties` that takes precedence.
- Debugging why an error message unexpectedly appears in the wrong language (or reverts to English) — this almost always traces to either a missing translation for the requested `Locale` (falling back to the default bundle) or the request's resolved locale not matching what was expected.
- Auditing what user-facing text a security failure actually produces, since the message code (not just the final rendered string) is often more useful for programmatic error handling than parsing localized text.

## 3. Core concept

```
An exception is thrown, e.g.: new LockedException("User account is locked")
    -- BUT this literal string is really just the DEFAULT (English) fallback

The actual lookup, wherever Spring Security surfaces this to a user-facing message, goes through:
    messageSourceAccessor.getMessage(
        "AbstractUserDetailsAuthenticationProvider.locked",  <-- the STABLE lookup code
        new Object[]{},                                       <-- any message arguments
        "User account is locked")                             <-- fallback if NO translation found at all

MessageSource resolution, given a code + Locale:
  1. look up the code in the bundle matching the REQUEST's resolved Locale (e.g. messages_de.properties)
  2. found?    -> return the LOCALIZED text
     not found? -> fall back to the DEFAULT bundle (messages.properties, no locale suffix)
     still not found? -> return the literal fallback text supplied in code

An application's OWN MessageSource, configured with its own basenames listed FIRST,
takes priority over spring-security-core's bundled messages for any code it also defines --
letting ONE overridden property in a custom properties file take precedence over the entire
built-in translation for that specific message, without needing to override anything else.
```

The message *code* is the stable, language-independent identifier; the resolved *text* is locale-dependent and freely swappable — this separation is exactly what makes overriding one message, or adding a new locale, additive rather than requiring wholesale replacement.

## 4. Diagram

<svg viewBox="0 0 660 220" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Diagram showing a locked exception being looked up by its stable message code against the requests resolved locale first checking a german bundle then falling back to the default english bundle if no german translation exists">
  <rect x="20" y="20" width="200" height="50" rx="7" fill="#1c2430" stroke="#79c0ff" stroke-width="1.3"/>
  <text x="120" y="42" fill="#79c0ff" font-size="9.5" text-anchor="middle" font-family="sans-serif">LockedException thrown</text>
  <text x="120" y="58" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">code: ....locked</text>

  <line x1="220" y1="45" x2="265" y2="45" stroke="#79c0ff" stroke-width="1.6" marker-end="url(#loc124)"/>

  <rect x="270" y="20" width="200" height="50" rx="7" fill="#1c2430" stroke="#f0883e" stroke-width="1.4"/>
  <text x="370" y="40" fill="#f0883e" font-size="9.5" text-anchor="middle" font-family="sans-serif">try messages_de.properties</text>
  <text x="370" y="56" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">(request Locale = de)</text>

  <line x1="370" y1="70" x2="370" y2="100" stroke="#f0883e" stroke-width="1.6" stroke-dasharray="4,3" marker-end="url(#loc124b)"/>
  <text x="440" y="90" fill="#f0883e" font-size="8" font-family="sans-serif">NOT FOUND for this code</text>

  <rect x="270" y="102" width="200" height="50" rx="7" fill="#1c2430" stroke="#6db33f" stroke-width="1.4"/>
  <text x="370" y="122" fill="#6db33f" font-size="9.5" text-anchor="middle" font-family="sans-serif">fall back to messages.properties</text>
  <text x="370" y="138" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">(default, no locale suffix)</text>

  <line x1="370" y1="152" x2="370" y2="180" stroke="#6db33f" stroke-width="1.6" marker-end="url(#loc124c)"/>

  <rect x="270" y="182" width="200" height="30" rx="6" fill="#1c2430" stroke="#3fb950" stroke-width="1.3"/>
  <text x="370" y="202" fill="#3fb950" font-size="9" text-anchor="middle" font-family="sans-serif">"User account is locked"</text>

  <defs>
    <marker id="loc124" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#79c0ff"/></marker>
    <marker id="loc124b" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#f0883e"/></marker>
    <marker id="loc124c" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#6db33f"/></marker>
  </defs>
</svg>

The lookup walks from the most specific matching bundle down to the default, using the stable message code the whole way.

## 5. Runnable example

The scenario: a from-scratch message-resolution engine, growing from a single-locale lookup into multi-locale fallback, then into demonstrating that overriding just one code in a custom bundle takes precedence without needing to duplicate the whole catalog.

### Level 1 — Basic

A single bundle, one lookup by code.

```java
import java.util.*;

public class LocalizationLevel1 {
    static class MessageSource {
        private final Map<String, String> messages;
        MessageSource(Map<String, String> messages) { this.messages = messages; }

        String getMessage(String code, String defaultMessage) {
            return messages.getOrDefault(code, defaultMessage);
        }
    }

    public static void main(String[] args) {
        MessageSource englishDefaults = new MessageSource(Map.of(
                "AbstractUserDetailsAuthenticationProvider.locked", "User account is locked"));

        String message = englishDefaults.getMessage("AbstractUserDetailsAuthenticationProvider.locked", "Locked (fallback)");
        System.out.println(message);

        String unknownCode = englishDefaults.getMessage("SomeOther.code", "Fallback text");
        System.out.println(unknownCode);
    }
}
```

**How to run:** save as `LocalizationLevel1.java`, run `java LocalizationLevel1.java` (JDK 17+ runs single files directly).

Expected output:
```
User account is locked
Fallback text
```

`getMessage` mirrors `MessageSourceAccessor`'s basic contract: look up a stable code, return a fallback if nothing is found — this is the mechanism behind every default English message a Spring Security exception ever surfaces.

### Level 2 — Intermediate

Add locale-specific bundles with fallback to the default when a translation is missing for a given locale.

```java
import java.util.*;

public class LocalizationLevel2 {
    static class LocaleAwareMessageSource {
        private final Map<String, Map<String, String>> bundlesByLocale = new HashMap<>();

        void addBundle(String locale, Map<String, String> messages) { bundlesByLocale.put(locale, messages); }

        // mirrors MessageSource resolution: try the SPECIFIC locale, fall back to the DEFAULT bundle
        String getMessage(String code, String locale, String defaultText) {
            Map<String, String> localeBundle = bundlesByLocale.get(locale);
            if (localeBundle != null && localeBundle.containsKey(code)) {
                return localeBundle.get(code);
            }
            Map<String, String> defaultBundle = bundlesByLocale.get("default");
            if (defaultBundle != null && defaultBundle.containsKey(code)) {
                return defaultBundle.get(code);
            }
            return defaultText;
        }
    }

    public static void main(String[] args) {
        LocaleAwareMessageSource messageSource = new LocaleAwareMessageSource();
        messageSource.addBundle("default", Map.of(
                "AbstractUserDetailsAuthenticationProvider.locked", "User account is locked",
                "AbstractUserDetailsAuthenticationProvider.badCredentials", "Bad credentials"));
        messageSource.addBundle("de", Map.of(
                "AbstractUserDetailsAuthenticationProvider.locked", "Benutzerkonto ist gesperrt"));
        // NOTE: German bundle has NO translation for "badCredentials" -- deliberately, to show fallback

        System.out.println("de, locked: " + messageSource.getMessage(
                "AbstractUserDetailsAuthenticationProvider.locked", "de", "fallback"));
        System.out.println("de, badCredentials (missing translation): " + messageSource.getMessage(
                "AbstractUserDetailsAuthenticationProvider.badCredentials", "de", "fallback"));
        System.out.println("fr (no bundle at all for this locale): " + messageSource.getMessage(
                "AbstractUserDetailsAuthenticationProvider.locked", "fr", "fallback"));
    }
}
```

**How to run:** save as `LocalizationLevel2.java`, run `java LocalizationLevel2.java` (JDK 17+ runs single files directly).

Expected output:
```
de, locked: Benutzerkonto ist gesperrt
de, badCredentials (missing translation): Bad credentials
fr (no bundle at all for this locale): User account is locked
```

What changed: `getMessage` now checks the requested locale's bundle first, and falls back to the `"default"` (English) bundle for any code that locale doesn't define — a partially-translated German bundle correctly serves its own translation where available and the English default everywhere else, and a locale with no bundle configured at all (`"fr"`) falls straight through to the default, exactly mirroring how a real `ReloadableResourceBundleMessageSource` behaves when a translation file is incomplete or entirely missing for a given locale.

### Level 3 — Advanced

Demonstrate application-level override precedence: a custom bundle listing its basenames *before* Spring Security's own default bundle takes priority for any code it also defines, without needing to duplicate the rest of the catalog.

```java
import java.util.*;

public class LocalizationLevel3 {
    static class LocaleAwareMessageSource {
        // ORDERED list of bundle sources -- application-specific ones typically listed FIRST
        private final List<Map<String, Map<String, String>>> orderedBundleSets = new ArrayList<>();

        void addBundleSet(Map<String, Map<String, String>> bundlesByLocale) { orderedBundleSets.add(bundlesByLocale); }

        String getMessage(String code, String locale, String defaultText) {
            // check EACH bundle SET in order (application override first, framework defaults after)
            for (Map<String, Map<String, String>> bundleSet : orderedBundleSets) {
                Map<String, String> localeBundle = bundleSet.get(locale);
                if (localeBundle != null && localeBundle.containsKey(code)) return localeBundle.get(code);
                Map<String, String> defaultBundle = bundleSet.get("default");
                if (defaultBundle != null && defaultBundle.containsKey(code)) return defaultBundle.get(code);
            }
            return defaultText;
        }
    }

    public static void main(String[] args) {
        LocaleAwareMessageSource messageSource = new LocaleAwareMessageSource();

        // APPLICATION's own custom bundle -- overrides just ONE code, in ONE locale, registered FIRST
        Map<String, Map<String, String>> customBundles = new HashMap<>();
        customBundles.put("default", Map.of(
                "AbstractUserDetailsAuthenticationProvider.locked",
                "Your account has been temporarily locked. Please contact support.")); // CUSTOM wording
        messageSource.addBundleSet(customBundles);

        // SPRING SECURITY's own bundled defaults -- registered SECOND, lower priority
        Map<String, Map<String, String>> securityDefaults = new HashMap<>();
        securityDefaults.put("default", Map.of(
                "AbstractUserDetailsAuthenticationProvider.locked", "User account is locked",
                "AbstractUserDetailsAuthenticationProvider.badCredentials", "Bad credentials"));
        messageSource.addBundleSet(securityDefaults);

        // the OVERRIDDEN code -- application's custom wording wins
        System.out.println("locked (overridden): " + messageSource.getMessage(
                "AbstractUserDetailsAuthenticationProvider.locked", "default", "fallback"));

        // a code the application did NOT override -- falls through to Security's own default
        System.out.println("badCredentials (not overridden): " + messageSource.getMessage(
                "AbstractUserDetailsAuthenticationProvider.badCredentials", "default", "fallback"));
    }
}
```

**How to run:** save as `LocalizationLevel3.java`, run `java LocalizationLevel3.java` (JDK 17+ runs single files directly).

Expected output:
```
locked (overridden): Your account has been temporarily locked. Please contact support.
badCredentials (not overridden): Bad credentials
```

What changed: `orderedBundleSets` now lets an application's own bundle be checked *before* Spring Security's bundled defaults — the "locked" code, present in both, resolves to the application's custom wording (checked first), while "badCredentials," present only in Security's defaults, correctly falls through to that default since the application chose not to override it — exactly mirroring `ReloadableResourceBundleMessageSource.setBasenames(...)` listing a custom basename before `"classpath:org/springframework/security/messages"`.

## 6. Walkthrough

Trace a locked-account login attempt through message resolution, ending in the user-facing text actually rendered.

**Step 1 — authentication fails with a specific exception.** Card 0054's account-status handling determines the user's account is locked and throws `LockedException`, constructed internally with a default English message as its fallback text and, critically, associated with the stable code `"AbstractUserDetailsAuthenticationProvider.locked"`.

**Step 2 — the exception reaches error-handling code that needs to render a message to the user** — an `AuthenticationFailureHandler` rendering a login-page error, or a REST API's error response body. This code calls something equivalent to `messageSourceAccessor.getMessage("AbstractUserDetailsAuthenticationProvider.locked", exception.getMessage())`.

**Step 3 — the current request's `Locale` is resolved** (via Spring's standard `LocaleResolver` mechanism — the `Accept-Language` header, a session attribute, or a fixed default, depending on application configuration). Suppose it resolves to German (`de`).

**Step 4 — bundle lookup, application override first.** If the application registered a custom bundle overriding this exact code (as in Level 3), that translation is returned immediately — this corresponds to `messageSource.getMessage(..., "default", ...)` in Level 3 finding the custom wording in `orderedBundleSets`'s first entry.

**Step 5 — absent an override, Spring Security's own bundled translation is checked.** For German specifically, `messages_de.properties` (shipped inside `spring-security-core`) is checked next — if it defines this code, that German text is returned.

**Step 6 — absent even that, the default (English) bundle is the final fallback**, and if somehow the code isn't found anywhere at all, the literal fallback text supplied in the original `getMessage(code, fallback)` call is used as a last resort.

```
LockedException thrown, code = "....locked"
        |
        v
locale resolved: "de"
        |
        v
1. application's custom bundle, locale "de" or "default"?  -> if present, USE IT, stop here
2. Spring Security's messages_de.properties                -> if present, USE IT, stop here
3. Spring Security's messages.properties (English default)  -> USE IT
4. literal fallback text passed in code                     -> absolute last resort
```

## 7. Gotchas & takeaways

> **Gotcha:** overriding a message code in a custom bundle only takes effect if that bundle's basename is registered *before* Spring Security's own bundled messages in the `MessageSource`'s basename list — registering it afterward (or forgetting to register it at all on the actual `ObjectMapper`/`MessageSource` bean the application uses) silently means the override is never consulted, and the framework's default text keeps appearing despite the custom properties file existing and looking correct.

- Spring Security never hard-codes user-facing exception text — every message goes through a stable code, resolved against a `MessageSource`, with a literal fallback only as a last resort.
- Spring Security ships default translations for its own message codes across several languages inside `spring-security-core` itself — most applications only need to add missing locales or override specific wording, not build a catalog from scratch.
- Locale resolution falls back gracefully: a missing translation for a specific code in the requested locale falls through to the default (typically English) bundle, rather than producing an error or blank text.
- Application-specific overrides take precedence when their basename is registered before Spring Security's own message bundle — this lets one wording change apply without needing to duplicate the entire default catalog.
- The message *code* is the stable, programmatically useful identifier; the resolved *text* is what a human sees — code that needs to react to a specific kind of failure programmatically should generally match on the exception type or code, not on parsed, potentially-localized message text.

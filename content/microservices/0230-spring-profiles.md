---
card: microservices
gi: 230
slug: spring-profiles
title: "Spring profiles"
---

## 1. What it is

Spring profiles are named, activatable groups of beans and configuration that let a single Spring application define multiple variants of its behavior — one profile's beans and settings active in development, a different profile's active in production — selected at startup via a single, simple activation flag, implementing exactly the [environment-specific configuration](0220-environment-specific-configuration.md) pattern as a first-class Spring mechanism.

## 2. Why & when

An application often needs genuinely different beans, not just different property values, depending on environment — a development environment might use an in-memory embedded database and a mock external-payment client, while production wires up a real database connection pool and a real payment gateway client. Property-only externalization (`@Value`, `@ConfigurationProperties`) handles differing *values* well, but doesn't cleanly handle differing *bean definitions* — swapping an entire implementation, not just a setting. Spring profiles solve this: `@Profile("dev")` and `@Profile("production")` annotations tag entire bean definitions (or whole `application-<profile>.yaml` files) as belonging to a specific profile, and only the beans matching the currently active profile(s) get created.

Use profiles whenever different environments need genuinely different bean wiring, not just different property values — a mock vs. a real external client, an embedded vs. a networked database. For settings that only differ in value, not in which beans exist, plain profile-specific property files (`application-production.yaml` overriding `application.yaml`) without needing `@Profile`-annotated beans are often sufficient.

## 3. Core concept

A bean (or configuration class) tagged `@Profile("name")` is registered in the Spring application context only when that profile is among the currently active profiles, which are set via a single startup-time flag (`spring.profiles.active`); untagged beans are always registered regardless of active profile.

```java
@Configuration
public class PaymentClientConfig {
    @Bean
    @Profile("production") // ONLY registered when "production" is active
    PaymentClient realPaymentClient() { return new StripePaymentClient(); }

    @Bean
    @Profile("dev") // ONLY registered when "dev" is active -- mutually exclusive with the bean above
    PaymentClient mockPaymentClient() { return new MockPaymentClient(); }
}
// activated via: spring.profiles.active=production  (in application.yaml, an env var, or --spring.profiles.active=production)
```

## 4. Diagram

<svg viewBox="0 0 640 170" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="One active profile flag selects which of two mutually exclusive, profile-tagged bean definitions -- a mock payment client for dev, a real payment client for production -- gets registered in the Spring application context" >
  <rect x="20" y="65" width="150" height="45" rx="5" fill="#1c2430" stroke="#79c0ff"/>
  <text x="95" y="92" fill="#e6edf3" font-size="8" text-anchor="middle" font-family="sans-serif">spring.profiles.active</text>

  <rect x="240" y="20" width="160" height="45" rx="5" fill="#1c2430" stroke="#8b949e"/>
  <text x="320" y="47" fill="#8b949e" font-size="7.5" text-anchor="middle" font-family="sans-serif">@Profile("dev") mock bean</text>

  <rect x="240" y="105" width="160" height="45" rx="5" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="320" y="132" fill="#e6edf3" font-size="7.5" text-anchor="middle" font-family="sans-serif">@Profile("production") real bean</text>

  <rect x="470" y="65" width="150" height="45" rx="5" fill="#1c2430" stroke="#79c0ff"/>
  <text x="545" y="92" fill="#e6edf3" font-size="8" text-anchor="middle" font-family="sans-serif">Application context</text>

  <line x1="170" y1="80" x2="238" y2="45" stroke="#8b949e" stroke-dasharray="3,3" marker-end="url(#arr230)"/>
  <line x1="170" y1="90" x2="238" y2="120" stroke="#6db33f" stroke-width="1.5" marker-end="url(#arr230g)"/>
  <line x1="400" y1="127" x2="468" y2="90" stroke="#6db33f" stroke-width="1.5" marker-end="url(#arr230g)"/>

  <defs>
    <marker id="arr230" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L6,3 L0,6 Z" fill="#8b949e"/></marker>
    <marker id="arr230g" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L6,3 L0,6 Z" fill="#6db33f"/></marker>
  </defs>
</svg>

Only the bean matching the active profile is registered; the other definition is skipped entirely, not merely overridden.

## 5. Runnable example

Scenario: a payment-processing service that starts with a single hard-coded client implementation (unable to differ by environment), refactors to model Spring's profile-based bean selection (mock vs. real client, chosen by an active-profile flag), and finally demonstrates a multi-profile activation (combining a base profile with an environment-specific one) to show profiles composing rather than being purely exclusive.

### Level 1 — Basic

```java
// File: SingleHardCodedClient.java -- ONE client implementation, used
// regardless of environment; testing against a real payment gateway in
// every environment (including local dev) is unavoidable here.
public class SingleHardCodedClient {
    interface PaymentClient { String charge(int amountCents); }
    static class StripePaymentClient implements PaymentClient {
        public String charge(int amountCents) { return "REAL charge via Stripe: $" + amountCents / 100.0; }
    }

    public static void main(String[] args) {
        PaymentClient client = new StripePaymentClient(); // the ONLY option, everywhere
        System.out.println(client.charge(2500));
        System.out.println("Local development would ALSO hit the real Stripe API here -- no way to swap it out.");
    }
}
```

**How to run:** `javac SingleHardCodedClient.java && java SingleHardCodedClient` (JDK 17+).

### Level 2 — Intermediate

```java
// File: ProfileSelectedClient.java -- models Spring's @Profile selection:
// an ACTIVE PROFILE flag determines which of TWO client implementations
// gets used, mirroring how @Profile-tagged beans are conditionally registered.
public class ProfileSelectedClient {
    interface PaymentClient { String charge(int amountCents); }
    static class StripePaymentClient implements PaymentClient { // @Profile("production") equivalent
        public String charge(int amountCents) { return "REAL charge via Stripe: $" + amountCents / 100.0; }
    }
    static class MockPaymentClient implements PaymentClient { // @Profile("dev") equivalent
        public String charge(int amountCents) { return "MOCK charge (no real money moved): $" + amountCents / 100.0; }
    }

    static PaymentClient resolveClientForProfile(String activeProfile) { // mirrors Spring's bean registration decision
        return switch (activeProfile) {
            case "production" -> new StripePaymentClient();
            case "dev" -> new MockPaymentClient();
            default -> throw new IllegalArgumentException("no PaymentClient bean for profile: " + activeProfile);
        };
    }

    public static void main(String[] args) {
        PaymentClient devClient = resolveClientForProfile("dev");
        System.out.println("[profile=dev] " + devClient.charge(2500));

        PaymentClient prodClient = resolveClientForProfile("production");
        System.out.println("[profile=production] " + prodClient.charge(2500));
    }
}
```

**How to run:** `javac ProfileSelectedClient.java && java ProfileSelectedClient` (JDK 17+).

Expected output:
```
[profile=dev] MOCK charge (no real money moved): $25.0
[profile=production] REAL charge via Stripe: $25.0
```

### Level 3 — Advanced

```java
// File: MultipleActiveProfilesCompose.java -- models activating MULTIPLE
// profiles simultaneously (e.g. "production,eu-region") -- Spring profiles
// COMPOSE (a bean can require just one, or an AND/OR combination), not
// purely mutually exclusive.
import java.util.*;

public class MultipleActiveProfilesCompose {
    interface PaymentClient { String charge(int amountCents); }
    static class StripePaymentClient implements PaymentClient {
        public String charge(int amountCents) { return "REAL charge via Stripe: $" + amountCents / 100.0; }
    }
    static class MockPaymentClient implements PaymentClient {
        public String charge(int amountCents) { return "MOCK charge: $" + amountCents / 100.0; }
    }

    record BeanCandidate<T>(T bean, Set<String> requiredProfiles) {} // models @Profile({"a","b"}) -- ANY match activates it

    static <T> Optional<T> resolveForActiveProfiles(List<BeanCandidate<T>> candidates, Set<String> activeProfiles) {
        for (BeanCandidate<T> c : candidates) {
            boolean matches = c.requiredProfiles().stream().anyMatch(activeProfiles::contains); // ANY overlap activates it
            if (matches) return Optional.of(c.bean());
        }
        return Optional.empty();
    }

    public static void main(String[] args) {
        List<BeanCandidate<PaymentClient>> candidates = List.of(
            new BeanCandidate<>(new MockPaymentClient(), Set.of("dev", "test")),           // @Profile({"dev","test"})
            new BeanCandidate<>(new StripePaymentClient(), Set.of("production", "staging")) // @Profile({"production","staging"})
        );

        Set<String> activeProfiles = Set.of("production", "eu-region"); // MULTIPLE active profiles, like Spring supports
        PaymentClient resolved = resolveForActiveProfiles(candidates, activeProfiles)
            .orElseThrow(() -> new IllegalStateException("no bean matched active profiles: " + activeProfiles));

        System.out.println("Active profiles: " + activeProfiles);
        System.out.println("Resolved client: " + resolved.charge(2500));
        System.out.println("The bean requiring \"production\" activated even though \"eu-region\" wasn't in its own set -- ANY overlap matches, mirroring Spring's @Profile semantics.");
    }
}
```

**How to run:** `javac MultipleActiveProfilesCompose.java && java MultipleActiveProfilesCompose` (JDK 17+).

Expected output:
```
Active profiles: [production, eu-region]
Resolved client: REAL charge via Stripe: $25.0
The bean requiring "production" activated even though "eu-region" wasn't in its own set -- ANY overlap matches, mirroring Spring's @Profile semantics.
```

## 6. Walkthrough

1. **Level 1, the coupling problem** — `StripePaymentClient` is instantiated directly and unconditionally in `main`, meaning every run of this program, regardless of intended environment, hits the same (real) implementation — exactly the problem `@Profile`-based bean selection exists to solve.
2. **Level 2, mirroring @Profile's decision** — `resolveClientForProfile` takes an `activeProfile` string and returns a different concrete `PaymentClient` implementation depending on its value, modeling how Spring's container decides, per `@Profile`-tagged bean definition, whether to register that bean based on the currently active profile.
3. **Level 2, the mutually exclusive outcome** — calling `resolveClientForProfile` with `"dev"` returns `MockPaymentClient`, and with `"production"` returns `StripePaymentClient`; in a real Spring application, only the bean matching the active profile would actually exist in the context — the non-matching bean definition is skipped entirely, not merely shadowed.
4. **Level 3, modeling profile sets on beans** — `BeanCandidate.requiredProfiles` is a `Set<String>`, mirroring how a real `@Profile({"dev", "test"})` annotation lists more than one profile name that a bean can activate under.
5. **Level 3, the "any match" semantics** — `resolveForActiveProfiles` checks whether *any* of a candidate's `requiredProfiles` appears in the currently `activeProfiles` set (`anyMatch`), not whether *all* of them do — this mirrors Spring's actual `@Profile` behavior, where listing multiple profile names on one annotation means the bean activates if *any* of those named profiles is active, functioning as an OR condition.
6. **Level 3, multiple simultaneously active profiles** — `activeProfiles` contains both `"production"` and `"eu-region"` at once, modeling a real Spring application started with `spring.profiles.active=production,eu-region`; the `StripePaymentClient` candidate's `requiredProfiles` set contains `"production"` (even though it doesn't separately list `"eu-region"`), so it matches and is resolved — demonstrating that activating multiple profiles together is normal and expected, not a conflict, and that Spring resolves each bean independently against the full active set.

## 7. Gotchas & takeaways

> **Gotcha:** if two `@Profile`-tagged beans of the same type both end up active simultaneously (for example, one tagged `@Profile("production")` and another tagged `@Profile("!dev")`, both matching when profile `"production"` is active), Spring raises a `NoUniqueBeanDefinitionException` at startup — profile expressions need to be designed so that exactly one candidate matches for any realistic combination of active profiles, not assumed to be automatically mutually exclusive just because they look that way for the common cases.

- Spring profiles let entire bean definitions — not just property values — differ by environment, activated via a single `spring.profiles.active` flag.
- Use `@Profile` when different environments need genuinely different implementations wired in (a mock vs. a real client); use plain profile-specific property files when only values, not bean identities, differ.
- Multiple profiles can be active simultaneously, and a bean tagged with multiple profile names activates if *any* of them is active — profile matching is an OR condition across a bean's listed profiles, not an AND.
- Because profile expressions can support negation and combinations (`!dev`, `production & eu-region`), it's possible for more than one candidate bean to unintentionally become eligible at once, which fails startup with a "no unique bean" error rather than silently picking one.
- Profiles are Spring's dedicated implementation of the general [environment-specific configuration](0220-environment-specific-configuration.md) pattern, scoped specifically to bean registration rather than just property resolution.

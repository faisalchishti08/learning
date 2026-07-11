---
card: spring-security
gi: 61
slug: secured-object-configattribute-legacy
title: "Secured object & ConfigAttribute (legacy)"
---

## 1. What it is

`ConfigAttribute` is the legacy, single-method interface (`getAttribute()`, returning a plain string) representing one configured security requirement attached to a "secured object" — a URL pattern or a method — that the older `AccessDecisionVoter`s (from the previous card) inspected to decide their votes; `SecurityMetadataSource` (`FilterInvocationSecurityMetadataSource` for URLs, `MethodSecurityMetadataSource` for methods) was the interface responsible for looking up which `ConfigAttribute`s applied to a given secured object in the first place.

```java
public interface ConfigAttribute extends Serializable {
    String getAttribute(); // e.g. "ROLE_ADMIN", or an arbitrary custom string a voter interprets
}

public interface AccessDecisionVoter<S> {
    // the voter receives the SECURED OBJECT and its ASSOCIATED ConfigAttributes together
    int vote(Authentication authentication, S secureObject, Collection<ConfigAttribute> attributes);
}
```

## 2. Why & when

Before `AuthorizationManager`'s design unified everything behind one interface parameterized by the object being checked directly, the older architecture needed a way to associate arbitrary configuration strings with a "secured object" (a URL, a method) and have voters interpret those strings according to whatever convention each voter understood (`RoleVoter` looked for a `ROLE_` prefix specifically; other voters could define entirely their own string conventions) — `ConfigAttribute` was the deliberately generic, string-based carrier for this configuration, and `SecurityMetadataSource` was the lookup mechanism connecting a specific secured object to its list of applicable attributes.

Reach for understanding `ConfigAttribute`/`SecurityMetadataSource` when:

- Maintaining legacy code still expressing security rules through this older mechanism, particularly a custom `AccessDecisionVoter` that interprets `ConfigAttribute` strings according to its own bespoke convention.
- Recognizing that the modern equivalent of "a secured object with its associated configuration" is simply the second parameter (`T object`) passed directly to `AuthorizationManager.check(...)` — no separate attribute-carrying wrapper type is needed at all in the current design, since the object itself (a request, a method invocation) carries everything a modern manager needs to inspect directly.
- Never reach for this API in new code — it has been fully superseded by `AuthorizationManager`'s simpler design, where the object being checked is passed directly rather than through this generic, string-based configuration-attribute indirection.

## 3. Core concept

```
 LEGACY flow:
   1. SecurityMetadataSource.getAttributes(securedObject)
        -- LOOKS UP which ConfigAttributes apply to THIS specific URL/method
        -- e.g. for "/admin/**": returns [ConfigAttribute("ROLE_ADMIN")]
   2. AccessDecisionVoter.vote(authentication, securedObject, theseAttributes)
        -- the VOTER interprets the attribute STRINGS according to its OWN convention
        -- RoleVoter specifically looks for attributes STARTING WITH "ROLE_"
   3. AccessDecisionManager combines multiple voters' results (previous card)

 MODERN equivalent (AuthorizationManager):
   check(authentication, securedObjectDIRECTLY)
        -- NO separate ConfigAttribute lookup step at all
        -- the manager itself is CONSTRUCTED with whatever configuration it needs
           (e.g. AuthorityAuthorizationManager is constructed WITH "ROLE_ADMIN" directly)
```

The older design separated "what configuration applies here" (attributes) from "how to interpret it" (voters); the modern design simply builds each manager already knowing what it's looking for.

## 4. Diagram

<svg viewBox="0 0 640 170" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="A secured object like a URL pattern is looked up via SecurityMetadataSource to retrieve its associated ConfigAttribute strings which are then passed alongside the secured object to an AccessDecisionVoter for interpretation the modern AuthorizationManager design eliminates this indirection by constructing the manager already knowing its own configuration">
  <rect x="15" y="20" width="180" height="40" rx="7" fill="#1c2430" stroke="#8b949e" stroke-width="1.2"/>
  <text x="105" y="38" fill="#e6edf3" font-size="7.5" text-anchor="middle" font-family="sans-serif">secured object (URL)</text>
  <text x="105" y="51" fill="#e6edf3" font-size="7" text-anchor="middle" font-family="sans-serif">/admin/**</text>

  <rect x="230" y="20" width="180" height="40" rx="7" fill="#1c2430" stroke="#8b949e" stroke-width="1.2"/>
  <text x="320" y="38" fill="#e6edf3" font-size="7.5" text-anchor="middle" font-family="sans-serif">SecurityMetadataSource</text>
  <text x="320" y="51" fill="#e6edf3" font-size="7" text-anchor="middle" font-family="sans-serif">-&gt; [ConfigAttribute("ROLE_ADMIN")]</text>

  <rect x="445" y="20" width="180" height="40" rx="7" fill="#1c2430" stroke="#79c0ff" stroke-width="1.3"/>
  <text x="535" y="38" fill="#79c0ff" font-size="7.5" text-anchor="middle" font-family="sans-serif">AccessDecisionVoter</text>
  <text x="535" y="51" fill="#e6edf3" font-size="7" text-anchor="middle" font-family="sans-serif">interprets the string</text>

  <rect x="130" y="110" width="380" height="42" rx="8" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="320" y="130" fill="#6db33f" font-size="7.5" text-anchor="middle" font-family="sans-serif">MODERN: AuthorityAuthorizationManager("ROLE_ADMIN")</text>
  <text x="320" y="143" fill="#e6edf3" font-size="7" text-anchor="middle" font-family="sans-serif">already KNOWS its config -- no lookup step needed</text>

  <defs><marker id="a61" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#8b949e"/></marker></defs>
  <line x1="195" y1="40" x2="230" y2="40" stroke="#8b949e" stroke-width="1.2" marker-end="url(#a61)"/>
  <line x1="410" y1="40" x2="445" y2="40" stroke="#8b949e" stroke-width="1.2" marker-end="url(#a61)"/>
</svg>

The legacy three-step lookup-then-interpret chain collapses into one pre-configured object in the modern design.

## 5. Runnable example

The scenario: implement the legacy `ConfigAttribute`/`SecurityMetadataSource`/voter chain faithfully, then implement the equivalent modern `AuthorizationManager`, and directly compare the two side by side against identical inputs, confirming they produce the same decision through structurally different mechanisms.

### Level 1 — Basic

The legacy chain: a metadata source looking up attributes for a secured object, and a voter interpreting them.

```java
import java.util.*;

public class SecuredObjectLevel1 {
    record ConfigAttribute(String attribute) {}
    record Authentication(Set<String> authorities) {}

    // models SecurityMetadataSource: looks up WHICH attributes apply to a given secured object
    static Map<String, List<ConfigAttribute>> securityMetadata = Map.of(
            "/admin/**", List.of(new ConfigAttribute("ROLE_ADMIN")),
            "/reports/**", List.of(new ConfigAttribute("ROLE_ADMIN"), new ConfigAttribute("ROLE_MANAGER"))
    );

    static List<ConfigAttribute> getAttributes(String securedObject) {
        return securityMetadata.getOrDefault(securedObject, List.of());
    }

    // models RoleVoter: interprets ConfigAttribute strings, specifically those STARTING WITH "ROLE_"
    static int vote(Authentication authentication, List<ConfigAttribute> attributes) {
        boolean anyRoleAttributePresent = attributes.stream().anyMatch(a -> a.attribute().startsWith("ROLE_"));
        if (!anyRoleAttributePresent) return 0; // ABSTAIN -- this voter has no ROLE_ attributes to check at all
        boolean hasMatchingRole = attributes.stream().anyMatch(a -> authentication.authorities().contains(a.attribute()));
        return hasMatchingRole ? 1 : -1; // GRANTED or DENIED
    }

    public static void main(String[] args) {
        Authentication admin = new Authentication(Set.of("ROLE_ADMIN"));

        List<ConfigAttribute> adminAttributes = getAttributes("/admin/**");
        System.out.println("attributes for /admin/**: " + adminAttributes);
        System.out.println("vote result: " + vote(admin, adminAttributes) + " (1 = GRANTED)");
    }
}
```

How to run: `java SecuredObjectLevel1.java`

`getAttributes` looks up `"/admin/**"` in `securityMetadata`, returning `[ConfigAttribute("ROLE_ADMIN")]`; `vote` then interprets that specific attribute string, checking whether `admin`'s authorities contain it — this two-step lookup-then-interpret process is exactly what the legacy `SecurityMetadataSource`/`AccessDecisionVoter` pairing performs for every secured object.

### Level 2 — Intermediate

Show the same lookup-then-interpret pattern for a different secured object (`/reports/**`, requiring *either* of two roles), confirming the voter correctly interprets multiple attributes.

```java
import java.util.*;

public class SecuredObjectLevel2 {
    record ConfigAttribute(String attribute) {}
    record Authentication(Set<String> authorities) {}

    static Map<String, List<ConfigAttribute>> securityMetadata = Map.of(
            "/admin/**", List.of(new ConfigAttribute("ROLE_ADMIN")),
            "/reports/**", List.of(new ConfigAttribute("ROLE_ADMIN"), new ConfigAttribute("ROLE_MANAGER"))
    );

    static List<ConfigAttribute> getAttributes(String securedObject) {
        return securityMetadata.getOrDefault(securedObject, List.of());
    }

    static int vote(Authentication authentication, List<ConfigAttribute> attributes) {
        boolean anyRoleAttributePresent = attributes.stream().anyMatch(a -> a.attribute().startsWith("ROLE_"));
        if (!anyRoleAttributePresent) return 0;
        boolean hasMatchingRole = attributes.stream().anyMatch(a -> authentication.authorities().contains(a.attribute()));
        return hasMatchingRole ? 1 : -1;
    }

    public static void main(String[] args) {
        Authentication manager = new Authentication(Set.of("ROLE_MANAGER"));
        Authentication regularUser = new Authentication(Set.of("ROLE_USER"));

        List<ConfigAttribute> reportsAttributes = getAttributes("/reports/**");
        System.out.println("manager vote on /reports/**: " + vote(manager, reportsAttributes) + " (matches ROLE_MANAGER attribute)");
        System.out.println("regular user vote on /reports/**: " + vote(regularUser, reportsAttributes) + " (-1 = matches NEITHER attribute)");
    }
}
```

How to run: `java SecuredObjectLevel2.java`

`/reports/**`'s attribute list has two entries (`ROLE_ADMIN` and `ROLE_MANAGER`), and `vote`'s `anyMatch` check across both attributes correctly grants the manager (whose authorities include `ROLE_MANAGER`, satisfying the second attribute) while denying the regular user, whose authorities match neither of the two configured attributes.

### Level 3 — Advanced

Implement the modern `AuthorizationManager` equivalent for the identical `/reports/**` rule, side by side with the legacy chain, confirming both produce identical decisions for identical inputs through structurally different mechanisms.

```java
import java.util.*;
import java.util.function.Supplier;

public class SecuredObjectLevel3 {
    record ConfigAttribute(String attribute) {}
    record Authentication(Set<String> authorities) {}

    // LEGACY chain
    static Map<String, List<ConfigAttribute>> securityMetadata = Map.of(
            "/reports/**", List.of(new ConfigAttribute("ROLE_ADMIN"), new ConfigAttribute("ROLE_MANAGER"))
    );
    static List<ConfigAttribute> getAttributes(String securedObject) { return securityMetadata.getOrDefault(securedObject, List.of()); }
    static int legacyVote(Authentication authentication, List<ConfigAttribute> attributes) {
        boolean hasMatchingRole = attributes.stream().anyMatch(a -> authentication.authorities().contains(a.attribute()));
        return hasMatchingRole ? 1 : -1;
    }

    // MODERN equivalent: an AuthorizationManager already CONSTRUCTED with its own required roles, NO separate lookup step
    record AuthorizationDecision(boolean granted) {}
    interface AuthorizationManager { AuthorizationDecision check(Supplier<Authentication> authSupplier); }

    static AuthorizationManager reportsAccessManager = authSupplier -> {
        Authentication auth = authSupplier.get();
        boolean granted = auth.authorities().contains("ROLE_ADMIN") || auth.authorities().contains("ROLE_MANAGER");
        return new AuthorizationDecision(granted);
    };

    public static void main(String[] args) {
        Authentication manager = new Authentication(Set.of("ROLE_MANAGER"));
        Authentication regularUser = new Authentication(Set.of("ROLE_USER"));

        for (Authentication auth : List.of(manager, regularUser)) {
            int legacyResult = legacyVote(auth, getAttributes("/reports/**"));
            AuthorizationDecision modernResult = reportsAccessManager.check(() -> auth);

            System.out.println(auth.authorities() + " -- legacy vote: " + legacyResult
                    + " (1=granted, -1=denied), modern decision: " + modernResult
                    + ", AGREE? " + ((legacyResult == 1) == modernResult.granted()));
        }
    }
}
```

How to run: `java SecuredObjectLevel3.java`

Both mechanisms produce identical, agreeing decisions for both authentications — the legacy chain arrives at its answer via a separate lookup (`getAttributes`) followed by string-based interpretation (`legacyVote`), while the modern manager already has its required roles baked directly into its own construction, with no separate lookup or generic string-attribute indirection needed at all.

## 6. Walkthrough

Trace `reportsAccessManager.check(() -> manager)` from Level 3, where `manager` has authorities `{ROLE_MANAGER}`.

1. `check` is invoked with a `Supplier<Authentication>` lambda that, when called, returns `manager` directly.
2. Inside the manager's lambda body, `auth = authSupplier.get()` invokes the supplier, resolving `auth` to the same `manager` object, with `authorities = {ROLE_MANAGER}`.
3. `auth.authorities().contains("ROLE_ADMIN")` checks whether `{ROLE_MANAGER}` contains `"ROLE_ADMIN"` — it does not, so this is `false`.
4. `auth.authorities().contains("ROLE_MANAGER")` checks whether `{ROLE_MANAGER}` contains `"ROLE_MANAGER"` — it does, so this is `true`.
5. `false || true` evaluates to `true`, so `granted = true`, and the method returns `new AuthorizationDecision(true)` — note that at no point did this method perform any separate lookup step (like the legacy chain's `getAttributes` call) to discover *what* roles are required; that knowledge (`"ROLE_ADMIN"` and `"ROLE_MANAGER"`) is simply written directly into the manager's own code, baked in at construction time rather than retrieved dynamically from an external metadata source.

```
LEGACY:  getAttributes("/reports/**") -> [ROLE_ADMIN, ROLE_MANAGER]  (separate lookup step)
         legacyVote(manager, [ROLE_ADMIN, ROLE_MANAGER]) -> checks authorities against EACH attribute -> GRANTED

MODERN:  reportsAccessManager.check(manager)
         -> directly checks authorities.contains("ROLE_ADMIN") || authorities.contains("ROLE_MANAGER")
         -> the required roles are HARD-CODED into the manager itself, no external lookup needed -> GRANTED

both AGREE: true
```

## 7. Gotchas & takeaways

> **Gotcha:** the legacy `ConfigAttribute` mechanism's generic string-based design meant a voter had to establish its own convention for interpreting attribute strings (`RoleVoter`'s `ROLE_` prefix convention being the most common example) — a custom voter using a different, undocumented convention for its own attribute strings could easily confuse anyone reading the configuration later, since the attribute strings themselves carried no inherent structure or type safety beyond being plain text.

- `ConfigAttribute` and `SecurityMetadataSource` are legacy building blocks from the pre-`AuthorizationManager` architecture, used to associate generic, string-based configuration with a secured object (a URL or method) for voters to interpret.
- The modern `AuthorizationManager` design eliminates this indirection entirely — a manager is constructed already knowing exactly what it's checking for, with no separate metadata lookup step required.
- Recognizing that a legacy custom voter's attribute-interpretation logic maps directly onto a modern `AuthorizationManager`'s construction-time configuration is the key insight for migrating old code cleanly.
- This API is documented here purely for understanding and maintaining legacy code — `AuthorizationManager` (from two cards back) is the current, recommended approach for all new authorization logic.

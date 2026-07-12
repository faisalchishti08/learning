---
card: spring-security
gi: 123
slug: jackson-support-serializing-security-context
title: "Jackson support (serializing security context)"
---

## 1. What it is

Spring Security ships a set of Jackson `Module`s (`CoreJackson2Module`, `WebServletJackson2Module`, `OAuth2ClientJackson2Module`, and others per feature area) specifically so that its own types — `SecurityContext`, `Authentication` implementations, `UserDetails`, `GrantedAuthority` — can be safely serialized to and deserialized from JSON. This matters most for applications that store the `SecurityContext` outside the JVM's own memory — a distributed session store like Redis (via Spring Session), or any cache that needs to persist and later reconstruct these objects — since Jackson's *default*, reflection-based serialization mishandles several of Security's types badly: some have no default constructor, some intentionally hide internal state behind interfaces, and blindly deserializing arbitrary class names from an external JSON payload is itself a security risk Jackson's default typing must be deliberately restricted to avoid.

```java
@Bean
public ObjectMapper securityObjectMapper() {
    ClassLoader loader = getClass().getClassLoader();
    ObjectMapper mapper = new ObjectMapper();
    mapper.registerModules(SecurityJackson2Modules.getModules(loader)); // registers ALL relevant modules
    return mapper;
}
```

## 2. Why & when

The moment a `SecurityContext` needs to leave the JVM — written to Redis so a session survives across a cluster of application instances, or cached somewhere for reuse — it has to become bytes, and JSON is the common, human-inspectable choice most session stores default to. But `Authentication` implementations like `UsernamePasswordAuthenticationToken` carry an `Object principal` and `Object credentials` field whose *actual* runtime type varies (a `String`, a `UserDetails` implementation, a `Jwt`, an `OAuth2User`) — Jackson needs to be told, explicitly and safely, how to preserve and later reconstruct that exact type, or a deserialized `SecurityContext` would silently come back with the wrong principal type (or fail to deserialize at all), breaking every `@AuthenticationPrincipal`-typed controller parameter that expects a specific class.

Reach for Spring Security's Jackson modules when:

- Using Spring Session with a distributed store (Redis, Hazelcast, JDBC) — this is the single most common reason a `SecurityContext` needs safe JSON serialization at all, since Spring Session commonly uses Jackson under the hood to persist session attributes.
- Building a custom cache or distributed storage layer that holds `Authentication` objects or `UserDetails` instances directly, rather than a purpose-built session store that already handles this.
- Debugging a `SecurityContext` that deserializes with a wrong or generic principal type (a `LinkedHashMap` instead of the expected `UserDetails` implementation, for instance) — this almost always traces to the relevant Security Jackson module not being registered on the `ObjectMapper` actually performing the deserialization.
- Adding OAuth2 client or resource-server support alongside Spring Session — `OAuth2ClientJackson2Module` (and similar per-feature modules) must be registered in addition to the core module if `OAuth2AuthorizedClient`/`OAuth2User`/`Jwt` objects also need to survive serialization.

## 3. Core concept

```
Naive Jackson serialization of an Authentication (WITHOUT Security's modules):
    reflection-based -- tries to serialize EVERY field, including internal/hidden ones
    principal/credentials fields are typed Object -- Jackson has NO IDEA what concrete
        class to deserialize them back into without extra type information
    some Security classes have NO default (no-arg) constructor -- Jackson's default
        deserialization strategy can't construct them at all

SecurityJackson2Modules.getModules(classLoader):
    registers a MIXIN per Security type -- tells Jackson EXACTLY:
        - which fields to include/exclude
        - which constructor to use for deserialization
        - an explicit "@class" type marker so the CONCRETE principal/credentials type
          is preserved and safely restored, rather than guessed or left as a raw Map

Per-feature modules (register ONLY what you actually use):
    CoreJackson2Module            -- SecurityContext, UsernamePasswordAuthenticationToken, User, etc.
    WebServletJackson2Module      -- Servlet-specific Authentication details
    OAuth2ClientJackson2Module    -- OAuth2AuthorizedClient, OAuth2User, OidcUser
    CasJackson2Module             -- CAS-specific types (card 0121)
```

Registering these modules is what turns "Jackson technically CAN produce some JSON for this object" into "Jackson can produce JSON that, when read back, reconstructs the *exact same* typed object" — the difference between merely serializable and genuinely round-trippable.

## 4. Diagram

<svg viewBox="0 0 640 200" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Diagram showing an Authentication object being serialized to json with an explicit class type marker preserving the principals concrete type then deserialized back by an ObjectMapper with security jackson modules registered producing the exact same typed object rather than a generic map">
  <rect x="20" y="20" width="180" height="60" rx="7" fill="#1c2430" stroke="#79c0ff" stroke-width="1.3"/>
  <text x="110" y="42" fill="#79c0ff" font-size="9.5" text-anchor="middle" font-family="sans-serif">UsernamePasswordAuthenticationToken</text>
  <text x="110" y="60" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">principal: MyUserDetails instance</text>

  <line x1="200" y1="50" x2="245" y2="50" stroke="#79c0ff" stroke-width="1.6" marker-end="url(#jk123)"/>
  <text x="222" y="42" fill="#79c0ff" font-size="8" text-anchor="middle" font-family="sans-serif">serialize</text>

  <rect x="250" y="20" width="180" height="60" rx="7" fill="#1c2430" stroke="#8b949e" stroke-width="1.3"/>
  <text x="340" y="42" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">JSON with "@class" markers</text>
  <text x="340" y="60" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">stored in Redis / distributed cache</text>

  <line x1="430" y1="50" x2="475" y2="50" stroke="#6db33f" stroke-width="1.6" marker-end="url(#jk123b)"/>
  <text x="452" y="42" fill="#6db33f" font-size="8" text-anchor="middle" font-family="sans-serif">deserialize</text>

  <rect x="480" y="20" width="140" height="60" rx="7" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="550" y="42" fill="#6db33f" font-size="9" text-anchor="middle" font-family="sans-serif">EXACT SAME typed object</text>
  <text x="550" y="60" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">MyUserDetails, not a Map</text>

  <text x="320" y="110" fill="#f0883e" font-size="9" text-anchor="middle" font-family="sans-serif">WITHOUT Security's Jackson modules registered: deserializes to a generic LinkedHashMap instead</text>

  <defs>
    <marker id="jk123" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#79c0ff"/></marker>
    <marker id="jk123b" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#6db33f"/></marker>
  </defs>
</svg>

The explicit type marker is what lets deserialization reconstruct the exact original class, not just "some object with similar-looking fields."

## 5. Runnable example

The scenario: a simplified serialization round trip using a hand-rolled JSON-like map (standing in for real Jackson), growing from a naive approach that loses type information into one carrying an explicit type marker, then into round-tripping a full `Authentication`-equivalent object with a typed principal.

### Level 1 — Basic

Naive serialization losing the principal's concrete type.

```java
import java.util.*;

public class JacksonSupportLevel1 {
    interface Principal {}
    record MyUserDetails(String username, Set<String> roles) implements Principal {}

    // stands in for Jackson's DEFAULT, naive serialization -- just dumps fields into a generic map
    static Map<String, Object> naiveSerialize(Principal principal) {
        if (principal instanceof MyUserDetails details) {
            return Map.of("username", details.username(), "roles", details.roles());
            // NOTICE: nothing here records that this came from "MyUserDetails" specifically
        }
        throw new IllegalArgumentException("unsupported principal type");
    }

    public static void main(String[] args) {
        MyUserDetails original = new MyUserDetails("alice", Set.of("ROLE_USER"));

        Map<String, Object> serialized = naiveSerialize(original);
        System.out.println("serialized (generic map, type info LOST): " + serialized);
        System.out.println("no way to know, just from this map, that it should become a MyUserDetails again");
    }
}
```

**How to run:** save as `JacksonSupportLevel1.java`, run `java JacksonSupportLevel1.java` (JDK 17+ runs single files directly).

Expected output:
```
serialized (generic map, type info LOST): {username=alice, roles=[ROLE_USER]}
no way to know, just from this map, that it should become a MyUserDetails again
```

`naiveSerialize` mirrors what Jackson's default, unmodified behavior effectively produces for a field typed `Object` — the resulting data has no marker recording which concrete class it came from, so deserializing it back can, at best, only produce a generic map, never the original typed object.

### Level 2 — Intermediate

Add an explicit type marker, mirroring the `@class` field Spring Security's Jackson mixins inject, and use it to deserialize back into the correct concrete type.

```java
import java.util.*;

public class JacksonSupportLevel2 {
    interface Principal {}
    record MyUserDetails(String username, Set<String> roles) implements Principal {}
    record OtherPrincipalType(String subject) implements Principal {}

    static Map<String, Object> serializeWithType(Principal principal) {
        Map<String, Object> result = new LinkedHashMap<>();
        result.put("@class", principal.getClass().getSimpleName()); // the KEY addition -- explicit type marker
        if (principal instanceof MyUserDetails details) {
            result.put("username", details.username());
            result.put("roles", details.roles());
        } else if (principal instanceof OtherPrincipalType other) {
            result.put("subject", other.subject());
        }
        return result;
    }

    @SuppressWarnings("unchecked")
    static Principal deserialize(Map<String, Object> data) {
        String type = (String) data.get("@class");
        return switch (type) {
            case "MyUserDetails" -> new MyUserDetails((String) data.get("username"), (Set<String>) data.get("roles"));
            case "OtherPrincipalType" -> new OtherPrincipalType((String) data.get("subject"));
            default -> throw new IllegalArgumentException("unknown principal type: " + type);
        };
    }

    public static void main(String[] args) {
        MyUserDetails original = new MyUserDetails("alice", Set.of("ROLE_USER"));

        Map<String, Object> serialized = serializeWithType(original);
        System.out.println("serialized with type marker: " + serialized);

        Principal restored = deserialize(serialized);
        System.out.println("restored: " + restored + " (exact class: " + restored.getClass().getSimpleName() + ")");
    }
}
```

**How to run:** save as `JacksonSupportLevel2.java`, run `java JacksonSupportLevel2.java` (JDK 17+ runs single files directly).

Expected output:
```
serialized with type marker: {@class=MyUserDetails, username=alice, roles=[ROLE_USER]}
restored: MyUserDetails[username=alice, roles=[ROLE_USER]] (exact class: MyUserDetails)
```

What changed: the serialized data now carries an explicit `"@class"` marker, and `deserialize` uses it to reconstruct the *exact* original type rather than a generic map — this is precisely what Spring Security's registered mixins add on top of Jackson's default behavior, letting a round trip through JSON preserve type fidelity for fields as generically typed as `Authentication.getPrincipal()`.

### Level 3 — Advanced

Round-trip a full `Authentication`-equivalent object, including its typed principal and authorities, through a simulated `ObjectMapper`, and demonstrate why an untrusted or unrestricted deserializer (accepting *any* `@class` value) is itself a security risk worth guarding against.

```java
import java.util.*;

public class JacksonSupportLevel3 {
    interface Principal {}
    record MyUserDetails(String username, Set<String> roles) implements Principal {}
    record Authentication(Principal principal, Set<String> authorities, boolean authenticated) {}

    static class UntrustedTypeException extends RuntimeException {
        UntrustedTypeException(String message) { super(message); }
    }

    // mirrors SecurityJackson2Modules -- an ALLOWLIST of principal types this "ObjectMapper" will deserialize
    static class SecurityAwareObjectMapper {
        private final Set<String> allowedPrincipalTypes;
        SecurityAwareObjectMapper(Set<String> allowedPrincipalTypes) { this.allowedPrincipalTypes = allowedPrincipalTypes; }

        Map<String, Object> serialize(Authentication auth) {
            Map<String, Object> principalData = new LinkedHashMap<>();
            principalData.put("@class", auth.principal().getClass().getSimpleName());
            if (auth.principal() instanceof MyUserDetails details) {
                principalData.put("username", details.username());
                principalData.put("roles", details.roles());
            }
            Map<String, Object> result = new LinkedHashMap<>();
            result.put("principal", principalData);
            result.put("authorities", auth.authorities());
            result.put("authenticated", auth.authenticated());
            return result;
        }

        @SuppressWarnings("unchecked")
        Authentication deserialize(Map<String, Object> data) {
            Map<String, Object> principalData = (Map<String, Object>) data.get("principal");
            String type = (String) principalData.get("@class");

            // SAFETY CHECK: only reconstruct types this mapper was explicitly configured to trust
            if (!allowedPrincipalTypes.contains(type)) {
                throw new UntrustedTypeException("refusing to deserialize untrusted/unregistered type: " + type);
            }

            Principal principal = new MyUserDetails((String) principalData.get("username"),
                    (Set<String>) principalData.get("roles"));
            return new Authentication(principal, (Set<String>) data.get("authorities"), (boolean) data.get("authenticated"));
        }
    }

    public static void main(String[] args) {
        SecurityAwareObjectMapper mapper = new SecurityAwareObjectMapper(Set.of("MyUserDetails"));

        Authentication original = new Authentication(
                new MyUserDetails("alice", Set.of("ROLE_USER")), Set.of("ROLE_USER"), true);

        Map<String, Object> serialized = mapper.serialize(original);
        Authentication restored = mapper.deserialize(serialized);
        System.out.println("round-tripped: " + restored);

        // simulate a TAMPERED or malicious payload naming a type this mapper never agreed to trust
        Map<String, Object> maliciousPrincipal = new LinkedHashMap<>();
        maliciousPrincipal.put("@class", "some.malicious.RemoteCodeExecutionGadget");
        Map<String, Object> maliciousData = new LinkedHashMap<>();
        maliciousData.put("principal", maliciousPrincipal);
        maliciousData.put("authorities", Set.of("ROLE_ADMIN"));
        maliciousData.put("authenticated", true);

        try {
            mapper.deserialize(maliciousData);
        } catch (UntrustedTypeException e) {
            System.out.println("malicious payload rejected: " + e.getMessage());
        }
    }
}
```

**How to run:** save as `JacksonSupportLevel3.java`, run `java JacksonSupportLevel3.java` (JDK 17+ runs single files directly).

Expected output:
```
round-tripped: Authentication[principal=MyUserDetails[username=alice, roles=[ROLE_USER]], authorities=[ROLE_USER], authenticated=true]
malicious payload rejected: refusing to deserialize untrusted/unregistered type: some.malicious.RemoteCodeExecutionGadget
```

What changed: `SecurityAwareObjectMapper` now maintains an explicit allowlist of trusted principal types and refuses to deserialize anything outside it — this mirrors why Spring Security's Jackson modules register mixins for specific, known types rather than enabling Jackson's fully general "deserialize any class named in the JSON" default typing, which is a well-known vector for deserialization-based remote code execution if an attacker can ever influence the JSON being deserialized (a poisoned cache entry, a tampered session store record).

## 6. Walkthrough

Trace alice's `Authentication` round-tripping through a distributed session store, tying it to a real Spring Session + Redis deployment.

**Step 1 — alice authenticates**, and a `SecurityContext` wrapping her `Authentication` (principal: her `UserDetails` implementation, authorities: her granted roles) is populated in `SecurityContextHolder`, exactly as every earlier authentication card in this course describes.

**Step 2 — Spring Session persists the session, including this `SecurityContext`, to Redis.** Internally, this requires converting the Java objects to a serialized form — commonly JSON, via an `ObjectMapper` that (if correctly configured per this card) has `SecurityJackson2Modules.getModules(...)` registered. This corresponds to `mapper.serialize(original)` in Level 3, producing a JSON-equivalent structure carrying an explicit `"@class"` marker for the principal.

**Step 3 — a *different* application instance in the cluster later receives a request carrying alice's session cookie.** It looks up the session data from Redis and must reconstruct the `SecurityContext` from the serialized JSON — this corresponds to `mapper.deserialize(serialized)`.

**Step 4 — the type marker is checked against the allowlist.** `principalData.get("@class")` is `"MyUserDetails"`, which is present in `allowedPrincipalTypes`, so deserialization proceeds, reconstructing the *exact* original `MyUserDetails` object — not a generic map, not a different or wrong type.

**Step 5 — the reconstructed `Authentication` is placed back into `SecurityContextHolder`** for this new request, and everything downstream (an `@AuthenticationPrincipal MyUserDetails user` controller parameter, an authorization check reading `getAuthorities()`) works exactly as if the request had been served by the original instance — this is precisely the point of getting serialization right: statelessness across a cluster, from the application's point of view, looks identical to a single, long-lived in-memory session.

**Contrast — the malicious payload.** If an attacker somehow influenced the stored session data (a poisoned cache, a compromised Redis instance, or a bug elsewhere allowing arbitrary write access) to name an unexpected class, `deserialize`'s allowlist check catches it — `"some.malicious.RemoteCodeExecutionGadget"` is not in `allowedPrincipalTypes`, so `UntrustedTypeException` is thrown, and no attempt is ever made to instantiate that unknown class.

```
alice's SecurityContext -> serialized with "@class": MyUserDetails -> stored in Redis
        |
        v (a DIFFERENT instance handles her next request)
Redis lookup -> deserialize -> "@class" checked against allowlist -> MATCH -> reconstructed correctly

tampered payload -> "@class": some.malicious.Gadget -> NOT in allowlist -> REJECTED, nothing instantiated
```

## 7. Gotchas & takeaways

> **Gotcha:** enabling Jackson's fully general "default typing" (accepting and instantiating whatever class name appears in an `@class`-style field, unrestricted) rather than registering Spring Security's specific, curated mixins is a well-documented deserialization vulnerability class — an attacker who can influence the serialized data (a poisoned cache, a tampered cookie, a compromised backing store) could potentially name an arbitrary class on the classpath, triggering unintended (and in the worst case, exploitable) construction. Always prefer the specific, allowlisted modules Spring Security provides over Jackson's unrestricted default typing.

- Spring Security's own types (`SecurityContext`, `Authentication` implementations, `UserDetails`, `OAuth2User`) need explicit Jackson support because their generically-typed fields (`Object principal`, `Object credentials`) lose concrete type information under Jackson's default, reflection-based serialization.
- `SecurityJackson2Modules.getModules(classLoader)` registers curated mixins per feature area — core types, Servlet-specific details, OAuth2 client types, CAS types — each telling Jackson exactly how to serialize and, critically, how to safely deserialize back to the correct concrete class.
- The single most common reason this matters in practice is a distributed session store (Spring Session + Redis or similar) needing to persist and reconstruct a `SecurityContext` across application instances in a cluster.
- The explicit type marker these mixins add is what preserves round-trip fidelity — without it, a deserialized principal degrades to a generic map rather than the original typed object, breaking any code that expects a specific class.
- Restricting deserialization to a known, curated set of trusted types (rather than Jackson's fully general default typing) is a deliberate security measure, not an incidental implementation detail — it closes a real deserialization-based attack vector that broader, unrestricted typing would otherwise open.

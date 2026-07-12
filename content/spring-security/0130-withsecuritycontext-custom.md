---
card: spring-security
gi: 130
slug: withsecuritycontext-custom
title: "@WithSecurityContext (custom)"
---

## 1. What it is

`@WithSecurityContext` is the general-purpose extension point underlying both `@WithMockUser` and `@WithUserDetails` — neither of those annotations is magic; each is itself meta-annotated with `@WithSecurityContext(factory = ...)`, pointing at a `WithSecurityContextFactory<A>` implementation responsible for building the actual `SecurityContext` from the annotation's attributes. Building a genuinely custom test annotation — one tailored to an application's own `Authentication` type, a specific OAuth2 principal shape, or any authentication scheme this course has covered that the built-in annotations don't model — means writing a custom annotation meta-annotated with `@WithSecurityContext` and a corresponding factory class.

```java
@Retention(RetentionPolicy.RUNTIME)
@WithSecurityContext(factory = WithMockCustomUser.Factory.class)
public @interface WithMockCustomUser {
    String username() default "alice";
    long tenantId() default 1L;

    class Factory implements WithSecurityContextFactory<WithMockCustomUser> {
        public SecurityContext createSecurityContext(WithMockCustomUser annotation) {
            CustomPrincipal principal = new CustomPrincipal(annotation.username(), annotation.tenantId());
            Authentication auth = new TestingAuthenticationToken(principal, null, "ROLE_USER");
            SecurityContext context = SecurityContextHolder.createEmptyContext();
            context.setAuthentication(auth);
            return context;
        }
    }
}
```

## 2. Why & when

Cards 0127 and 0129 cover the two built-in cases Spring Security anticipated — a generic mock principal, and a real `UserDetailsService`-backed one — but neither fits every application's authentication model: a multi-tenant application whose principal always carries a `tenantId`, an application authenticating entirely via a custom `Authentication` implementation, or a test needing to simulate a specific OAuth2/OIDC principal shape not directly covered by card 0135's dedicated OAuth2 test support. `@WithSecurityContext` exists precisely so the same declarative testing style — one annotation, applied to a test method, populating the security context automatically — extends to *any* authentication model an application defines, not just the two the framework ships built-in support for.

Reach for a custom `@WithSecurityContext`-based annotation when:

- The application's principal type carries fields neither `@WithMockUser`'s generic mock nor `@WithUserDetails`'s real-service lookup naturally accommodates — a multi-tenant id, a custom claims structure, anything specific to the application's own domain.
- Many tests across the codebase need the same custom authentication shape — writing the factory once and reusing the resulting annotation everywhere is far more maintainable than manually constructing and setting a `SecurityContext` inside every individual test method's body.
- Building reusable test infrastructure for a library or shared module other teams' tests will consume — a well-designed custom annotation is a much better public API than asking every consumer to hand-roll their own `SecurityContext` setup.

## 3. Core concept

```
@WithMockUser and @WithUserDetails are THEMSELVES built this exact way:

    @WithMockUser is meta-annotated:
        @WithSecurityContext(factory = WithMockUserSecurityContextFactory.class)

    @WithUserDetails is meta-annotated:
        @WithSecurityContext(factory = WithUserDetailsSecurityContextFactory.class)

Building a CUSTOM one follows the same two-part recipe:
  1. define a custom annotation, carrying whatever attributes YOUR application's
     authentication model needs (a tenantId, a custom claim, anything at all)
  2. meta-annotate it with @WithSecurityContext(factory = YourFactory.class)
  3. implement WithSecurityContextFactory<YourAnnotation>:
       SecurityContext createSecurityContext(YourAnnotation annotation) {
           // build WHATEVER Authentication/principal your application actually uses
           // return a SecurityContext wrapping it
       }

Spring Security's test infrastructure invokes YOUR factory the SAME WAY it invokes
the built-in ones -- there is no difference in HOW the resulting context gets applied
to a test method; only WHO builds the SecurityContext differs.
```

This is precisely why the two built-in annotations were introduced first in this section — understanding them fully means already understanding the general mechanism this card names explicitly.

## 4. Diagram

<svg viewBox="0 0 640 200" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Diagram showing WithMockUser WithUserDetails and a custom annotation all meta-annotated with WithSecurityContext pointing at their own factory implementation each factory building a different kind of SecurityContext but all installed into a test method the same way">
  <rect x="20" y="20" width="600" height="40" rx="8" fill="#1c2430" stroke="#8b949e" stroke-width="1.3"/>
  <text x="320" y="45" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">@WithSecurityContext(factory = ...) -- the SHARED underlying mechanism</text>

  <line x1="120" y1="60" x2="120" y2="90" stroke="#79c0ff" stroke-width="1.5" marker-end="url(#wsc130)"/>
  <line x1="320" y1="60" x2="320" y2="90" stroke="#6db33f" stroke-width="1.5" marker-end="url(#wsc130b)"/>
  <line x1="520" y1="60" x2="520" y2="90" stroke="#f0883e" stroke-width="1.5" marker-end="url(#wsc130c)"/>

  <rect x="30" y="92" width="180" height="40" rx="6" fill="#1c2430" stroke="#79c0ff" stroke-width="1.2"/>
  <text x="120" y="116" fill="#79c0ff" font-size="9" text-anchor="middle" font-family="sans-serif">@WithMockUser -&gt; its Factory</text>

  <rect x="230" y="92" width="180" height="40" rx="6" fill="#1c2430" stroke="#6db33f" stroke-width="1.2"/>
  <text x="320" y="116" fill="#6db33f" font-size="9" text-anchor="middle" font-family="sans-serif">@WithUserDetails -&gt; its Factory</text>

  <rect x="430" y="92" width="180" height="40" rx="6" fill="#1c2430" stroke="#f0883e" stroke-width="1.2"/>
  <text x="520" y="116" fill="#f0883e" font-size="9" text-anchor="middle" font-family="sans-serif">@WithMockCustomUser -&gt; YOUR Factory</text>

  <line x1="120" y1="132" x2="320" y2="160" stroke="#8b949e" stroke-width="1.4" marker-end="url(#wsc130d)"/>
  <line x1="320" y1="132" x2="320" y2="160" stroke="#8b949e" stroke-width="1.4" marker-end="url(#wsc130d)"/>
  <line x1="520" y1="132" x2="320" y2="160" stroke="#8b949e" stroke-width="1.4" marker-end="url(#wsc130d)"/>

  <rect x="220" y="162" width="200" height="30" rx="6" fill="#1c2430" stroke="#3fb950" stroke-width="1.3"/>
  <text x="320" y="182" fill="#3fb950" font-size="9" text-anchor="middle" font-family="sans-serif">test method's SecurityContext</text>

  <defs>
    <marker id="wsc130" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#79c0ff"/></marker>
    <marker id="wsc130b" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#6db33f"/></marker>
    <marker id="wsc130c" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#f0883e"/></marker>
    <marker id="wsc130d" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#8b949e"/></marker>
  </defs>
</svg>

Three different factories, three different kinds of `SecurityContext` — all installed into a test the exact same way.

## 5. Runnable example

The scenario: model the factory pattern itself, growing from a single custom factory building a tenant-aware principal into multiple custom annotations coexisting, then into a factory that composes existing logic (reusing part of what `@WithUserDetails`-style resolution would do) rather than building everything from scratch.

### Level 1 — Basic

A custom annotation-equivalent and its factory, building a tenant-aware principal.

```java
import java.util.*;

public class WithSecurityContextLevel1 {
    record CustomPrincipal(String username, long tenantId) {}
    record SecurityContext(CustomPrincipal principal, Set<String> authorities) {}

    // mirrors a custom annotation's attributes: @WithMockCustomUser(username = "alice", tenantId = 7)
    record MockCustomUserAnnotation(String username, long tenantId) {}

    // mirrors WithSecurityContextFactory<WithMockCustomUser>
    static class CustomUserSecurityContextFactory {
        SecurityContext createSecurityContext(MockCustomUserAnnotation annotation) {
            CustomPrincipal principal = new CustomPrincipal(annotation.username(), annotation.tenantId());
            return new SecurityContext(principal, Set.of("ROLE_USER"));
        }
    }

    public static void main(String[] args) {
        CustomUserSecurityContextFactory factory = new CustomUserSecurityContextFactory();

        // mirrors: @WithMockCustomUser(username = "alice", tenantId = 7)
        SecurityContext context = factory.createSecurityContext(new MockCustomUserAnnotation("alice", 7L));

        System.out.println("built context: " + context);
    }
}
```

**How to run:** save as `WithSecurityContextLevel1.java`, run `java WithSecurityContextLevel1.java` (JDK 17+ runs single files directly).

Expected output:
```
built context: SecurityContext[principal=CustomPrincipal[username=alice, tenantId=7], authorities=[ROLE_USER]]
```

`CustomUserSecurityContextFactory.createSecurityContext` mirrors exactly what a real `WithSecurityContextFactory<WithMockCustomUser>` implementation does: read the custom annotation's attributes, construct whatever principal type the application actually uses, and hand back a fully-formed `SecurityContext`.

### Level 2 — Intermediate

Two distinct custom annotations coexisting, each with its own factory, both installed the same way — mirroring how `@WithMockUser` and `@WithUserDetails` coexist as siblings under the same shared mechanism.

```java
import java.util.*;

public class WithSecurityContextLevel2 {
    record CustomPrincipal(String username, long tenantId) {}
    record OAuth2StylePrincipal(String subject, String issuer) {}
    record SecurityContext(Object principal, Set<String> authorities) {}

    record MockCustomUserAnnotation(String username, long tenantId) {}
    record MockOAuth2UserAnnotation(String subject, String issuer) {}

    interface SecurityContextFactory<A> { SecurityContext createSecurityContext(A annotation); }

    static class CustomUserFactory implements SecurityContextFactory<MockCustomUserAnnotation> {
        public SecurityContext createSecurityContext(MockCustomUserAnnotation a) {
            return new SecurityContext(new CustomPrincipal(a.username(), a.tenantId()), Set.of("ROLE_USER"));
        }
    }

    static class OAuth2UserFactory implements SecurityContextFactory<MockOAuth2UserAnnotation> {
        public SecurityContext createSecurityContext(MockOAuth2UserAnnotation a) {
            return new SecurityContext(new OAuth2StylePrincipal(a.subject(), a.issuer()), Set.of("SCOPE_read"));
        }
    }

    public static void main(String[] args) {
        CustomUserFactory tenantFactory = new CustomUserFactory();
        OAuth2UserFactory oauth2Factory = new OAuth2UserFactory();

        SecurityContext tenantContext = tenantFactory.createSecurityContext(new MockCustomUserAnnotation("alice", 7L));
        SecurityContext oauth2Context = oauth2Factory.createSecurityContext(
                new MockOAuth2UserAnnotation("109283746", "https://idp.example.com"));

        System.out.println("@WithMockCustomUser -> " + tenantContext);
        System.out.println("@WithMockOAuth2User -> " + oauth2Context);
    }
}
```

**How to run:** save as `WithSecurityContextLevel2.java`, run `java WithSecurityContextLevel2.java` (JDK 17+ runs single files directly).

Expected output:
```
@WithMockCustomUser -> SecurityContext[principal=CustomPrincipal[username=alice, tenantId=7], authorities=[ROLE_USER]]
@WithMockOAuth2User -> SecurityContext[principal=OAuth2StylePrincipal[subject=109283746, issuer=https://idp.example.com], authorities=[SCOPE_read]]
```

What changed: two entirely independent custom annotation/factory pairs now coexist, each producing a completely different principal shape — this mirrors how an application with several distinct authentication models in play (a multi-tenant custom scheme *and* OAuth2 resource server support, for instance) can define one custom testing annotation per model, all following the identical `@WithSecurityContext` pattern.

### Level 3 — Advanced

A factory that composes existing lookup logic — reusing a real user-lookup service (mirroring `@WithUserDetails`'s approach) while still adding application-specific data (`tenantId`) the built-in annotation has no concept of, demonstrating that custom factories aren't limited to building everything from raw annotation attributes alone.

```java
import java.util.*;

public class WithSecurityContextLevel3 {
    record AppUserDetails(String username, Long databaseUserId, Set<String> roles) {}
    record TenantAwarePrincipal(AppUserDetails userDetails, long tenantId) {}
    record SecurityContext(TenantAwarePrincipal principal, Set<String> authorities) {}

    record MockTenantUserAnnotation(String username, long tenantId) {}

    static class RealUserDetailsService {
        private final Map<String, AppUserDetails> usersByUsername = new HashMap<>();
        void register(AppUserDetails user) { usersByUsername.put(user.username(), user); }
        AppUserDetails loadUserByUsername(String username) {
            AppUserDetails user = usersByUsername.get(username);
            if (user == null) throw new NoSuchElementException("UsernameNotFoundException: " + username);
            return user;
        }
    }

    // mirrors a factory that DELEGATES to the real UserDetailsService, then ADDS tenant context on top
    static class TenantAwareUserSecurityContextFactory {
        private final RealUserDetailsService userDetailsService;
        TenantAwareUserSecurityContextFactory(RealUserDetailsService service) { this.userDetailsService = service; }

        SecurityContext createSecurityContext(MockTenantUserAnnotation annotation) {
            AppUserDetails userDetails = userDetailsService.loadUserByUsername(annotation.username()); // REAL lookup
            TenantAwarePrincipal principal = new TenantAwarePrincipal(userDetails, annotation.tenantId());
            Set<String> authorities = new LinkedHashSet<>();
            for (String role : userDetails.roles()) authorities.add("ROLE_" + role);
            return new SecurityContext(principal, authorities);
        }
    }

    public static void main(String[] args) {
        RealUserDetailsService service = new RealUserDetailsService();
        service.register(new AppUserDetails("alice@example.com", 42L, Set.of("USER", "ADMIN")));

        TenantAwareUserSecurityContextFactory factory = new TenantAwareUserSecurityContextFactory(service);

        // mirrors: @WithMockTenantUser(username = "alice@example.com", tenantId = 7)
        SecurityContext context = factory.createSecurityContext(new MockTenantUserAnnotation("alice@example.com", 7L));

        System.out.println("principal's real databaseUserId (from REAL service): " + context.principal().userDetails().databaseUserId());
        System.out.println("principal's tenantId (from the CUSTOM annotation): " + context.principal().tenantId());
        System.out.println("authorities (derived from real UserDetails roles): " + context.authorities());
    }
}
```

**How to run:** save as `WithSecurityContextLevel3.java`, run `java WithSecurityContextLevel3.java` (JDK 17+ runs single files directly).

Expected output:
```
principal's real databaseUserId (from REAL service): 42
principal's tenantId (from the CUSTOM annotation): 7
authorities (derived from real UserDetails roles): [ROLE_USER, ROLE_ADMIN]
```

What changed: `TenantAwareUserSecurityContextFactory` now combines *both* approaches — it delegates to the real `UserDetailsService` for the authentic `databaseUserId` and roles (exactly like `@WithUserDetails` does), while also layering on `tenantId` from the custom annotation's own attribute, something neither built-in annotation alone could express. This demonstrates that a custom factory isn't restricted to building a principal from scratch — it can freely reuse and extend existing application services.

## 6. Walkthrough

Trace the construction of alice's tenant-aware context from Level 3, tying it to how a real custom annotation would be defined and used.

**Step 1 — the custom annotation is defined once, in test support code:**
```java
@Retention(RetentionPolicy.RUNTIME)
@WithSecurityContext(factory = WithMockTenantUser.Factory.class)
public @interface WithMockTenantUser {
    String username();
    long tenantId();

    class Factory implements WithSecurityContextFactory<WithMockTenantUser> {
        @Autowired UserDetailsService userDetailsService; // Spring injects the REAL bean here

        public SecurityContext createSecurityContext(WithMockTenantUser annotation) {
            UserDetails userDetails = userDetailsService.loadUserByUsername(annotation.username());
            TenantAwarePrincipal principal = new TenantAwarePrincipal(userDetails, annotation.tenantId());
            // ... build and return the SecurityContext
        }
    }
}
```

**Step 2 — a test method uses it:**
```java
@Test
@WithMockTenantUser(username = "alice@example.com", tenantId = 7)
void aliceSeesOnlyTenant7Data() throws Exception { ... }
```

**Step 3 — before the test body runs**, Spring Security's test infrastructure detects the `@WithSecurityContext` meta-annotation on `@WithMockTenantUser`, instantiates (and, in a real Spring test context, autowires) the specified `Factory` class, and calls `createSecurityContext(annotation)` — corresponding to `factory.createSecurityContext(new MockTenantUserAnnotation("alice@example.com", 7L))` in Level 3's code.

**Step 4 — the factory delegates to the real service first.** `userDetailsService.loadUserByUsername("alice@example.com")` runs exactly as it would for a genuine login, returning alice's real `AppUserDetails` with `databaseUserId=42` and her real roles.

**Step 5 — the factory layers custom data on top.** `new TenantAwarePrincipal(userDetails, 7L)` combines the real, authentic `UserDetails` with the tenant id supplied by the annotation's own attribute — a piece of context the real `UserDetailsService` has no concept of at all, since tenant scoping for this hypothetical test is a test-specific concern, not necessarily something every login carries.

**Step 6 — the resulting `SecurityContext` is placed into `SecurityContextHolder`**, exactly as for the built-in annotations, and the test body proceeds with a principal that is both authentically sourced (real roles, real database id) and enriched with exactly the extra dimension (`tenantId`) this hypothetical application's authorization logic actually depends on.

```
@WithMockTenantUser(username="alice@example.com", tenantId=7)
        |
        v
Factory.createSecurityContext(annotation)
        |
        +-- delegates: userDetailsService.loadUserByUsername("alice@example.com") -- REAL lookup
        |
        +-- adds: tenantId = 7 -- from the annotation, NOT from the real service
        |
        v
TenantAwarePrincipal(realUserDetails, tenantId=7) -- placed in SecurityContextHolder
```

## 7. Gotchas & takeaways

> **Gotcha:** a custom `WithSecurityContextFactory` implementation that needs to call a Spring-managed bean (a real `UserDetailsService`, as in Level 3) must itself be a Spring-managed component (or otherwise obtain the bean through Spring's test infrastructure) for dependency injection to work — a factory instantiated as a bare `new Factory()` outside Spring's control has no way to have `@Autowired` fields populated, and will fail with a `NullPointerException` the moment it tries to use an uninjected dependency.

- `@WithMockUser` and `@WithUserDetails` are not special framework magic — both are themselves built using the exact `@WithSecurityContext(factory = ...)` mechanism this card describes, which is available to any application wanting to define its own testing annotation.
- Building a custom annotation is a two-part recipe: define the annotation with whatever attributes your model needs, meta-annotate it with `@WithSecurityContext(factory = YourFactory.class)`, and implement `WithSecurityContextFactory<YourAnnotation>` to build the actual `SecurityContext`.
- A custom factory can build a principal entirely from the annotation's own attributes, delegate to existing application services (reusing `UserDetailsService`, for instance), or combine both approaches — there is no restriction on how the resulting `SecurityContext` is constructed.
- Multiple custom annotations, each with its own factory, can coexist freely in the same codebase, covering different authentication models an application might use across different parts of its test suite.
- A factory needing Spring-managed dependencies must itself participate in Spring's dependency injection (typically by being a Spring bean or otherwise resolved through the test context) — instantiating it manually outside that mechanism breaks autowiring.

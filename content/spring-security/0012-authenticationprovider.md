---
card: spring-security
gi: 12
slug: authenticationprovider
title: "AuthenticationProvider"
---

## 1. What it is

`AuthenticationProvider` is the two-method interface (`authenticate(Authentication)`, and `supports(Class<?>)`) that actually implements one specific authentication mechanism's logic — Spring Security ships `DaoAuthenticationProvider` (validates username/password against a `UserDetailsService`-backed store, using a configured `PasswordEncoder`) as the most common built-in implementation, and applications write their own custom `AuthenticationProvider` implementations to support mechanisms Spring Security doesn't provide out of the box, each one registered with a `ProviderManager` (the previous card) to be tried during authentication.

```java
public interface AuthenticationProvider {
    Authentication authenticate(Authentication authentication) throws AuthenticationException;
    boolean supports(Class<?> authentication);
}
```

```java
@Component
class CustomTokenAuthenticationProvider implements AuthenticationProvider {
    public Authentication authenticate(Authentication auth) {
        String token = (String) auth.getCredentials();
        // validate the token against SOME store, produce a fully-populated Authentication if valid
        if (!isValidToken(token)) throw new BadCredentialsException("invalid token");
        return new UsernamePasswordAuthenticationToken(lookupUser(token), null, lookupAuthorities(token));
    }
    public boolean supports(Class<?> authType) { return CustomTokenAuthentication.class.isAssignableFrom(authType); }
}
```

## 2. Why & when

`ProviderManager` (the previous card) provides the dispatch mechanism, but it doesn't itself know how to validate any specific kind of credential — that logic belongs entirely inside individual `AuthenticationProvider` implementations, each one self-contained and responsible for exactly one authentication mechanism. This separation is what lets an application mix built-in mechanisms (`DaoAuthenticationProvider` for username/password) with entirely custom ones (a provider validating a proprietary token format, or checking credentials against an unusual legacy system) side by side, with each provider's internal implementation details completely isolated from, and irrelevant to, how any other registered provider works, or how `ProviderManager` itself dispatches between them.

Reach for writing a custom `AuthenticationProvider` when:

- The application needs to authenticate against a credential type or backing store Spring Security doesn't support out of the box — a legacy authentication system, a proprietary token format, a biometric or hardware-key-based scheme — where the standard `DaoAuthenticationProvider`'s username/password/`UserDetailsService` model doesn't fit.
- Custom authentication logic needs to combine multiple checks in a way not naturally expressible through the standard providers — validating a credential against more than one backing system, or applying business-specific rules (an account lockout policy, a rate-limiting check) as part of the authentication decision itself.
- Understanding how `DaoAuthenticationProvider` itself works (as the reference, most-commonly-used built-in implementation) is a natural first step before writing a custom provider — its own internal shape (delegate to a `UserDetailsService` to load the user, delegate to a `PasswordEncoder` to verify the password) is a useful pattern to follow for a custom provider's own internal structure.

## 3. Core concept

```
 AuthenticationProvider (the INTERFACE):
   supports(Class<?>)  -- "can I handle THIS kind of Authentication object?"
   authenticate(Authentication) -- "given an UNVERIFIED claim, produce a VERIFIED result, or throw"

 DaoAuthenticationProvider (Spring Security's BUILT-IN implementation):
   supports(UsernamePasswordAuthenticationToken.class) -- true
   authenticate(unverified):
     1. userDetailsService.loadUserByUsername(unverified.getName())  -- load the STORED user
     2. passwordEncoder.matches(unverified.getCredentials(), storedUser.getPassword()) -- verify the password
     3. IF matches: return a NEW, fully-populated, verified Authentication (with storedUser's authorities)
     4. IF NOT: throw BadCredentialsException

 a CUSTOM provider follows the SAME shape, but with entirely DIFFERENT internal validation logic
```

Every provider follows the same two-method contract, but each is free to implement `authenticate`'s actual validation logic however that specific mechanism requires.

## 4. Diagram

<svg viewBox="0 0 640 170" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="An unverified UsernamePasswordAuthenticationToken flows into DaoAuthenticationProvider which loads the stored user via UserDetailsService checks the password via PasswordEncoder and produces a fully verified Authentication object with populated authorities">
  <rect x="20" y="60" width="140" height="46" rx="8" fill="#1c2430" stroke="#8b949e" stroke-width="1.2"/>
  <text x="90" y="80" fill="#e6edf3" font-size="7.5" text-anchor="middle" font-family="sans-serif">unverified</text>
  <text x="90" y="93" fill="#e6edf3" font-size="7.5" text-anchor="middle" font-family="sans-serif">Authentication</text>

  <rect x="220" y="20" width="200" height="40" rx="7" fill="#1c2430" stroke="#79c0ff" stroke-width="1.2"/>
  <text x="320" y="44" fill="#79c0ff" font-size="7.5" text-anchor="middle" font-family="sans-serif">UserDetailsService.loadUserByUsername</text>

  <rect x="220" y="70" width="200" height="40" rx="7" fill="#1c2430" stroke="#79c0ff" stroke-width="1.2"/>
  <text x="320" y="94" fill="#79c0ff" font-size="7.5" text-anchor="middle" font-family="sans-serif">PasswordEncoder.matches</text>

  <rect x="480" y="60" width="140" height="46" rx="8" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="550" y="80" fill="#6db33f" font-size="7.5" text-anchor="middle" font-family="sans-serif">verified</text>
  <text x="550" y="93" fill="#e6edf3" font-size="7.5" text-anchor="middle" font-family="sans-serif">Authentication</text>

  <defs><marker id="a12" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#8b949e"/></marker></defs>
  <line x1="160" y1="83" x2="220" y2="40" stroke="#8b949e" stroke-width="1.1" marker-end="url(#a12)"/>
  <line x1="160" y1="83" x2="220" y2="90" stroke="#8b949e" stroke-width="1.1" marker-end="url(#a12)"/>
  <line x1="420" y1="83" x2="480" y2="83" stroke="#8b949e" stroke-width="1.3" marker-end="url(#a12)"/>
</svg>

`DaoAuthenticationProvider`'s internal two-step process — load the stored user, then verify the password — is the reference pattern a custom provider's own `authenticate` method commonly follows for its own mechanism.

## 5. Runnable example

The scenario: model `DaoAuthenticationProvider`'s internal load-then-verify structure directly, then write a custom provider following the same pattern for a different credential type, proving the interface accommodates genuinely different internal logic behind the same contract. Start with a simplified `DaoAuthenticationProvider` model, then add a custom token-based provider alongside it, then register both with a `ProviderManager`-style dispatcher and confirm both work correctly through the same uniform interface.

### Level 1 — Basic

A simplified `DaoAuthenticationProvider`, modeling its load-then-verify internal structure.

```java
import java.util.*;

public class AuthProviderLevel1 {
    record StoredUser(String username, String hashedPassword, Set<String> roles) {}
    record UnverifiedAuth(String username, String rawPassword) {}
    record VerifiedAuth(String username, Set<String> roles) {}

    static Map<String, StoredUser> userStore = Map.of(
            "alice", new StoredUser("alice", "hashed:secret123", Set.of("ROLE_USER"))
    );

    static class DaoAuthenticationProvider {
        VerifiedAuth authenticate(UnverifiedAuth request) {
            StoredUser stored = userStore.get(request.username()); // step 1: LOAD the stored user
            if (stored == null) throw new RuntimeException("user not found: " + request.username());

            String hashedInput = "hashed:" + request.rawPassword(); // simplified "hashing" for this example
            if (!stored.hashedPassword().equals(hashedInput)) { // step 2: VERIFY the password
                throw new RuntimeException("bad credentials");
            }
            return new VerifiedAuth(stored.username(), stored.roles()); // step 3: produce the VERIFIED result
        }
    }

    public static void main(String[] args) {
        DaoAuthenticationProvider provider = new DaoAuthenticationProvider();
        VerifiedAuth result = provider.authenticate(new UnverifiedAuth("alice", "secret123"));
        System.out.println("verified: " + result.username() + " roles=" + result.roles());
    }
}
```

How to run: `java AuthProviderLevel1.java`

`DaoAuthenticationProvider.authenticate` follows the exact two-step pattern the real implementation uses: load the stored user first, then verify the presented credential against it — only upon both steps succeeding does it produce a `VerifiedAuth` result.

### Level 2 — Intermediate

Add a custom provider for an entirely different credential type (a pre-issued API token), following the same two-method contract but with completely different internal logic.

```java
import java.util.*;

public class AuthProviderLevel2 {
    record UnverifiedTokenAuth(String token) {}
    record VerifiedAuth(String username, Set<String> roles) {}

    static Map<String, VerifiedAuth> tokenStore = Map.of(
            "tok-abc123", new VerifiedAuth("bob", Set.of("ROLE_API_CLIENT"))
    );

    interface AuthenticationProvider<T> {
        boolean supports(Class<?> authType);
        VerifiedAuth authenticate(T request);
    }

    static class CustomTokenAuthenticationProvider implements AuthenticationProvider<UnverifiedTokenAuth> {
        public boolean supports(Class<?> authType) { return authType == UnverifiedTokenAuth.class; }
        public VerifiedAuth authenticate(UnverifiedTokenAuth request) {
            VerifiedAuth found = tokenStore.get(request.token()); // COMPLETELY different lookup logic than DaoAuthenticationProvider
            if (found == null) throw new RuntimeException("invalid or unknown token");
            return found;
        }
    }

    public static void main(String[] args) {
        CustomTokenAuthenticationProvider provider = new CustomTokenAuthenticationProvider();

        System.out.println("supports UnverifiedTokenAuth.class? " + provider.supports(UnverifiedTokenAuth.class));

        VerifiedAuth result = provider.authenticate(new UnverifiedTokenAuth("tok-abc123"));
        System.out.println("verified: " + result.username() + " roles=" + result.roles());
    }
}
```

How to run: `java AuthProviderLevel2.java`

`CustomTokenAuthenticationProvider`'s `authenticate` method looks up a token directly in `tokenStore`, an entirely different mechanism from `DaoAuthenticationProvider`'s load-user-then-verify-password approach — yet it implements the exact same `AuthenticationProvider`-shaped contract (`supports` plus `authenticate`), which is what allows it to be registered and dispatched to identically by a `ProviderManager`, exactly as the previous card demonstrated.

### Level 3 — Advanced

Register both providers with a `ProviderManager`-style dispatcher and confirm both authentication mechanisms work correctly, side by side, through the same uniform dispatch mechanism — the practical payoff of the shared interface.

```java
import java.util.*;

public class AuthProviderLevel3 {
    record UnverifiedPasswordAuth(String username, String rawPassword) {}
    record UnverifiedTokenAuth(String token) {}
    record VerifiedAuth(String username, Set<String> roles) {}
    record StoredUser(String username, String hashedPassword, Set<String> roles) {}

    static Map<String, StoredUser> userStore = Map.of("alice", new StoredUser("alice", "hashed:secret123", Set.of("ROLE_USER")));
    static Map<String, VerifiedAuth> tokenStore = Map.of("tok-abc123", new VerifiedAuth("bob", Set.of("ROLE_API_CLIENT")));

    interface AuthenticationProvider {
        boolean supports(Class<?> authType);
        VerifiedAuth authenticate(Object request);
    }

    static class DaoAuthenticationProvider implements AuthenticationProvider {
        public boolean supports(Class<?> authType) { return authType == UnverifiedPasswordAuth.class; }
        public VerifiedAuth authenticate(Object request) {
            UnverifiedPasswordAuth upa = (UnverifiedPasswordAuth) request;
            StoredUser stored = userStore.get(upa.username());
            if (stored == null || !stored.hashedPassword().equals("hashed:" + upa.rawPassword())) {
                throw new RuntimeException("bad credentials");
            }
            return new VerifiedAuth(stored.username(), stored.roles());
        }
    }

    static class CustomTokenAuthenticationProvider implements AuthenticationProvider {
        public boolean supports(Class<?> authType) { return authType == UnverifiedTokenAuth.class; }
        public VerifiedAuth authenticate(Object request) {
            UnverifiedTokenAuth uta = (UnverifiedTokenAuth) request;
            VerifiedAuth found = tokenStore.get(uta.token());
            if (found == null) throw new RuntimeException("invalid token");
            return found;
        }
    }

    static VerifiedAuth dispatch(List<AuthenticationProvider> providers, Object request) {
        for (AuthenticationProvider provider : providers) {
            if (provider.supports(request.getClass())) return provider.authenticate(request);
        }
        throw new RuntimeException("no provider for " + request.getClass());
    }

    public static void main(String[] args) {
        List<AuthenticationProvider> providers = List.of(new DaoAuthenticationProvider(), new CustomTokenAuthenticationProvider());

        VerifiedAuth aliceResult = dispatch(providers, new UnverifiedPasswordAuth("alice", "secret123"));
        System.out.println("dispatched password auth -> " + aliceResult.username() + " " + aliceResult.roles());

        VerifiedAuth bobResult = dispatch(providers, new UnverifiedTokenAuth("tok-abc123"));
        System.out.println("dispatched token auth -> " + bobResult.username() + " " + bobResult.roles());
    }
}
```

How to run: `java AuthProviderLevel3.java`

`dispatch` correctly routes the `UnverifiedPasswordAuth` request to `DaoAuthenticationProvider` and the `UnverifiedTokenAuth` request to `CustomTokenAuthenticationProvider`, purely through each provider's own `supports` check — `dispatch` itself contains zero knowledge of passwords, hashing, or token stores; it only knows how to ask "does this provider support this type" and delegate accordingly, exactly mirroring `ProviderManager`'s own real, generic dispatch logic operating over a genuinely heterogeneous set of registered `AuthenticationProvider` implementations.

## 6. Walkthrough

Trace `dispatch(providers, new UnverifiedTokenAuth("tok-abc123"))` in Level 3.

1. `dispatch` iterates `providers`, starting with `DaoAuthenticationProvider` — `provider.supports(UnverifiedTokenAuth.class)` checks `authType == UnverifiedPasswordAuth.class`, comparing `UnverifiedTokenAuth.class` against `UnverifiedPasswordAuth.class`, which are different `Class` objects, so this returns `false`.
2. The loop continues to the next provider, `CustomTokenAuthenticationProvider` — `provider.supports(UnverifiedTokenAuth.class)` checks `authType == UnverifiedTokenAuth.class`, which is `true` this time (an exact match).
3. Because `supports` returned `true`, `dispatch` calls `provider.authenticate(request)`, dispatching to `CustomTokenAuthenticationProvider.authenticate` — inside, `request` is cast to `UnverifiedTokenAuth`, and `tokenStore.get("tok-abc123")` finds the corresponding `VerifiedAuth("bob", {ROLE_API_CLIENT})` record.
4. Since `found` is non-null, no exception is thrown, and `CustomTokenAuthenticationProvider.authenticate` returns this `VerifiedAuth` object directly.
5. `dispatch` returns this same result to `main`, which prints `"dispatched token auth -> bob [ROLE_API_CLIENT]"` — the entire routing decision was made purely by comparing `Class` objects via each provider's own `supports` method, with `dispatch` never needing to know anything about tokens, passwords, or any other mechanism-specific detail.

```
dispatch(providers, UnverifiedTokenAuth("tok-abc123")):
  DaoAuthenticationProvider.supports(UnverifiedTokenAuth.class) -> false (wrong type) -> skip
  CustomTokenAuthenticationProvider.supports(UnverifiedTokenAuth.class) -> true -> match found
    -> authenticate(request) -> tokenStore.get("tok-abc123") -> VerifiedAuth("bob", {ROLE_API_CLIENT})
  dispatch returns VerifiedAuth("bob", {ROLE_API_CLIENT})
```

## 7. Gotchas & takeaways

> **Gotcha:** a custom `AuthenticationProvider`'s `supports` method must correctly and precisely identify exactly the `Authentication` subtype it's designed to handle — an overly broad `supports` implementation (matching more types than intended, perhaps via an overly permissive `isAssignableFrom` check against a common supertype) risks the provider being invoked for authentication requests it wasn't actually designed to correctly process, potentially producing incorrect authentication decisions for a type of request the provider's author never anticipated or tested against.

- `AuthenticationProvider` is the interface where actual authentication mechanism-specific logic lives — `supports` declares which `Authentication` type a given provider handles, and `authenticate` performs the actual credential validation for that type.
- `DaoAuthenticationProvider`, Spring Security's most common built-in implementation, follows a load-the-stored-user-then-verify-the-credential internal structure (via `UserDetailsService` and `PasswordEncoder`) that's a useful reference pattern when designing a custom provider's own internal logic.
- Multiple `AuthenticationProvider` implementations, each handling a completely different credential type and internal validation mechanism, can coexist and be dispatched to uniformly by a `ProviderManager`, purely because they all share the same two-method contract — this is the direct payoff of the interface-based design covered in this and the previous card.
- This card completes the foundational Architecture & Fundamentals section of this Spring Security series — the filter chain, `SecurityContext`, `Authentication`, `GrantedAuthority`, and the `AuthenticationManager`/`ProviderManager`/`AuthenticationProvider` trio together form the complete structural foundation every later card in this series (covering specific authentication mechanisms, authorization models, and Spring Security's broader ecosystem) builds directly on top of.

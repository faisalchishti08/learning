---
card: spring-security
gi: 11
slug: authenticationmanager-providermanager
title: "AuthenticationManager / ProviderManager"
---

## 1. What it is

`AuthenticationManager` is the single-method interface (`authenticate(Authentication)`, returning a fully-populated `Authentication` or throwing `AuthenticationException`) that actually performs authentication, and `ProviderManager` is Spring Security's standard implementation, which itself delegates to a configured, ordered list of `AuthenticationProvider` beans (the next card), trying each one in turn until one of them successfully handles the given `Authentication` type — this is the component the authentication filter (from the ordered-filter-chain card) actually calls to turn submitted credentials into a verified identity.

```java
public interface AuthenticationManager {
    Authentication authenticate(Authentication authentication) throws AuthenticationException;
}
```

```java
// ProviderManager tries EACH configured AuthenticationProvider in order
ProviderManager manager = new ProviderManager(
    List.of(daoAuthenticationProvider, ldapAuthenticationProvider, customTokenAuthenticationProvider)
);
```

## 2. Why & when

An application commonly needs to support more than one way of proving identity — validating a username/password against a database, checking credentials against an LDAP directory, or validating a pre-issued token — and hardcoding one single authentication mechanism into the filter chain directly would make it awkward to support multiple mechanisms simultaneously or to add a new one without disrupting existing configuration. `ProviderManager` solves this by acting as a dispatcher: it holds an ordered list of `AuthenticationProvider`s, each declaring (via `supports(Class)`) which specific `Authentication` type it knows how to handle, and `ProviderManager.authenticate(...)` simply tries each provider in order until one both supports the given authentication type and successfully authenticates it — new authentication mechanisms are added by registering a new provider, with no change needed to `ProviderManager` itself or to the filter that calls it.

Reach for understanding `AuthenticationManager`/`ProviderManager` directly when:

- An application needs to support multiple authentication mechanisms simultaneously — username/password via one provider, API tokens via a different provider — understanding that `ProviderManager` tries each configured provider in order clarifies how to add, remove, or reorder these mechanisms.
- Debugging why authentication is failing (or succeeding) unexpectedly — knowing that `ProviderManager` tries providers *in order* and stops at the first one that both supports and successfully authenticates the request explains cases where an unintended provider handled a request, or where a correctly-configured provider was never reached because an earlier one already claimed to handle (and then rejected) that authentication type.
- Writing a custom `AuthenticationProvider` (the next card) — understanding it plugs into `ProviderManager`'s dispatch list, rather than needing to be wired into the filter chain directly, clarifies exactly where and how custom authentication logic actually integrates.

## 3. Core concept

```
 authentication filter calls:
   authenticationManager.authenticate(unverifiedAuthenticationRequest)
        |
        v
 ProviderManager.authenticate(...) iterates its configured providers, IN ORDER:
   provider 1: supports(this Authentication's class)?  NO  -> skip
   provider 2: supports(this Authentication's class)?  YES -> attempt authenticate()
                 -- SUCCEEDS -> return the fully-populated, VERIFIED Authentication  (STOP here)
                 -- FAILS (throws) -> depends on configuration: may try the NEXT provider, or propagate the failure
   provider 3: (only reached if provider 2 either didn't support this type, or certain failure-continuation rules apply)

 the FIRST provider that supports AND successfully authenticates WINS -- its result is returned
```

Each provider is independently responsible for one specific authentication mechanism — `ProviderManager`'s job is purely dispatch and ordering, not authentication logic itself.

## 4. Diagram

<svg viewBox="0 0 640 170" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="ProviderManager tries three registered AuthenticationProviders in order the first one does not support this authentication type and is skipped the second supports it and successfully authenticates stopping the chain there without trying the third">
  <rect x="20" y="60" width="140" height="46" rx="8" fill="#1c2430" stroke="#8b949e" stroke-width="1.2"/>
  <text x="90" y="88" fill="#e6edf3" font-size="8" text-anchor="middle" font-family="sans-serif">ProviderManager</text>

  <rect x="220" y="20" width="130" height="40" rx="7" fill="#1c2430" stroke="#8b949e" stroke-width="1.1"/>
  <text x="285" y="38" fill="#e6edf3" font-size="7.5" text-anchor="middle" font-family="sans-serif">provider 1</text>
  <text x="285" y="52" fill="#8b949e" font-size="7" text-anchor="middle" font-family="sans-serif">not supported -- skip</text>

  <rect x="220" y="70" width="130" height="40" rx="7" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="285" y="88" fill="#6db33f" font-size="7.5" text-anchor="middle" font-family="sans-serif">provider 2</text>
  <text x="285" y="102" fill="#e6edf3" font-size="7" text-anchor="middle" font-family="sans-serif">supports + SUCCEEDS</text>

  <rect x="220" y="120" width="130" height="40" rx="7" fill="#1c2430" stroke="#8b949e" stroke-width="1.1"/>
  <text x="285" y="138" fill="#8b949e" font-size="7.5" text-anchor="middle" font-family="sans-serif">provider 3</text>
  <text x="285" y="152" fill="#8b949e" font-size="7" text-anchor="middle" font-family="sans-serif">NEVER REACHED</text>

  <defs><marker id="a11" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#8b949e"/></marker></defs>
  <line x1="160" y1="83" x2="220" y2="40" stroke="#8b949e" stroke-width="1" stroke-dasharray="3,3"/>
  <line x1="160" y1="83" x2="220" y2="90" stroke="#6db33f" stroke-width="1.3" marker-end="url(#a11)"/>
</svg>

Three providers registered, one tried and skipped, one tried and successful, the third never reached because the second already produced a result.

## 5. Runnable example

The scenario: model `ProviderManager`'s dispatch logic directly — a list of providers, each declaring what it supports, tried in order until one both supports and succeeds. Start with a single provider, then add multiple providers with the dispatch loop choosing the right one, then add a failure-and-fallthrough case showing what happens when a supporting provider exists but rejects the specific credentials.

### Level 1 — Basic

A single provider, handling one authentication type directly.

```java
public class AuthManagerLevel1 {
    record UsernamePasswordAuth(String username, String password) {}

    interface AuthenticationProvider {
        boolean supports(Class<?> authType);
        Object authenticate(Object auth);
    }

    static class DaoAuthenticationProvider implements AuthenticationProvider {
        public boolean supports(Class<?> authType) { return authType == UsernamePasswordAuth.class; }
        public Object authenticate(Object auth) {
            UsernamePasswordAuth upa = (UsernamePasswordAuth) auth;
            if ("alice".equals(upa.username()) && "secret123".equals(upa.password())) {
                return "VERIFIED: " + upa.username();
            }
            throw new RuntimeException("bad credentials");
        }
    }

    public static void main(String[] args) {
        AuthenticationProvider provider = new DaoAuthenticationProvider();
        UsernamePasswordAuth request = new UsernamePasswordAuth("alice", "secret123");

        if (provider.supports(request.getClass())) {
            System.out.println(provider.authenticate(request));
        }
    }
}
```

How to run: `java AuthManagerLevel1.java`

`DaoAuthenticationProvider` declares support for `UsernamePasswordAuth` and successfully authenticates the matching request — this is the minimal unit `ProviderManager` orchestrates across potentially many such providers.

### Level 2 — Intermediate

Add `ProviderManager`'s own dispatch loop, trying multiple providers in order and stopping at the first one that supports and succeeds.

```java
import java.util.*;

public class AuthManagerLevel2 {
    record UsernamePasswordAuth(String username, String password) {}
    record ApiTokenAuth(String token) {}

    interface AuthenticationProvider {
        boolean supports(Class<?> authType);
        Object authenticate(Object auth);
    }

    static class DaoAuthenticationProvider implements AuthenticationProvider {
        public boolean supports(Class<?> authType) { return authType == UsernamePasswordAuth.class; }
        public Object authenticate(Object auth) {
            UsernamePasswordAuth upa = (UsernamePasswordAuth) auth;
            if ("alice".equals(upa.username()) && "secret123".equals(upa.password())) return "VERIFIED (dao): " + upa.username();
            throw new RuntimeException("bad credentials");
        }
    }

    static class ApiTokenAuthenticationProvider implements AuthenticationProvider {
        public boolean supports(Class<?> authType) { return authType == ApiTokenAuth.class; }
        public Object authenticate(Object auth) {
            ApiTokenAuth ata = (ApiTokenAuth) auth;
            if ("valid-token-xyz".equals(ata.token())) return "VERIFIED (token): " + ata.token();
            throw new RuntimeException("invalid token");
        }
    }

    static class ProviderManager {
        List<AuthenticationProvider> providers;
        ProviderManager(List<AuthenticationProvider> providers) { this.providers = providers; }

        Object authenticate(Object request) {
            for (AuthenticationProvider provider : providers) {
                if (provider.supports(request.getClass())) {
                    System.out.println("  trying provider: " + provider.getClass().getSimpleName());
                    return provider.authenticate(request); // FIRST supporting provider wins
                }
            }
            throw new RuntimeException("no provider supports " + request.getClass());
        }
    }

    public static void main(String[] args) {
        ProviderManager manager = new ProviderManager(List.of(new DaoAuthenticationProvider(), new ApiTokenAuthenticationProvider()));

        System.out.println("-- username/password request --");
        System.out.println(manager.authenticate(new UsernamePasswordAuth("alice", "secret123")));

        System.out.println("-- API token request --");
        System.out.println(manager.authenticate(new ApiTokenAuth("valid-token-xyz")));
    }
}
```

How to run: `java AuthManagerLevel2.java`

For the `UsernamePasswordAuth` request, `ProviderManager`'s loop skips nothing since `DaoAuthenticationProvider` is checked first and supports it immediately; for the `ApiTokenAuth` request, the loop tries `DaoAuthenticationProvider` first (its `supports` check correctly returns `false` for this type), then reaches `ApiTokenAuthenticationProvider`, which supports and successfully authenticates it — both requests are correctly routed to their respective providers purely through the `supports` check, with `ProviderManager` itself containing zero authentication-mechanism-specific logic.

### Level 3 — Advanced

Add a case where a provider supports the request type but the credentials themselves are invalid, demonstrating that "supports" and "successfully authenticates" are two independent checks, and that a supporting-but-failing provider correctly propagates its failure rather than silently falling through to try other providers that don't even support this type.

```java
import java.util.*;

public class AuthManagerLevel3 {
    record UsernamePasswordAuth(String username, String password) {}
    record ApiTokenAuth(String token) {}

    interface AuthenticationProvider {
        boolean supports(Class<?> authType);
        Object authenticate(Object auth);
    }

    static class DaoAuthenticationProvider implements AuthenticationProvider {
        public boolean supports(Class<?> authType) { return authType == UsernamePasswordAuth.class; }
        public Object authenticate(Object auth) {
            UsernamePasswordAuth upa = (UsernamePasswordAuth) auth;
            if ("alice".equals(upa.username()) && "secret123".equals(upa.password())) return "VERIFIED (dao): " + upa.username();
            throw new RuntimeException("bad credentials for '" + upa.username() + "'");
        }
    }

    static class ApiTokenAuthenticationProvider implements AuthenticationProvider {
        public boolean supports(Class<?> authType) { return authType == ApiTokenAuth.class; }
        public Object authenticate(Object auth) { throw new RuntimeException("token provider unreachable"); }
    }

    static class ProviderManager {
        List<AuthenticationProvider> providers;
        ProviderManager(List<AuthenticationProvider> providers) { this.providers = providers; }

        Object authenticate(Object request) {
            for (AuthenticationProvider provider : providers) {
                if (provider.supports(request.getClass())) {
                    System.out.println("  found SUPPORTING provider: " + provider.getClass().getSimpleName());
                    return provider.authenticate(request); // attempt it -- if this THROWS, the exception propagates, no fallthrough to non-matching providers
                }
            }
            throw new RuntimeException("no provider supports " + request.getClass());
        }
    }

    public static void main(String[] args) {
        ProviderManager manager = new ProviderManager(List.of(new DaoAuthenticationProvider(), new ApiTokenAuthenticationProvider()));

        try {
            // DaoAuthenticationProvider SUPPORTS this type, but the credentials are WRONG
            manager.authenticate(new UsernamePasswordAuth("alice", "wrongpassword"));
        } catch (RuntimeException e) {
            System.out.println("authentication FAILED: " + e.getMessage());
            System.out.println("(note: ApiTokenAuthenticationProvider was NEVER tried -- it doesn't support UsernamePasswordAuth anyway)");
        }
    }
}
```

How to run: `java AuthManagerLevel3.java`

`DaoAuthenticationProvider.supports(UsernamePasswordAuth.class)` returns `true`, so `ProviderManager` calls its `authenticate` method — but the credentials (`"wrongpassword"`) don't match, so it throws `RuntimeException("bad credentials for 'alice'")`, which propagates directly out of `manager.authenticate(...)` and is caught in `main` — critically, `ApiTokenAuthenticationProvider` is never even considered, since the loop found a supporting provider on its very first check and committed to that provider's own success-or-failure outcome, rather than trying every registered provider indiscriminately regardless of type support.

## 6. Walkthrough

Trace `manager.authenticate(new UsernamePasswordAuth("alice", "wrongpassword"))` in Level 3.

1. `authenticate` begins iterating `providers`, starting with `DaoAuthenticationProvider` (the first element in the list).
2. `provider.supports(request.getClass())` checks `DaoAuthenticationProvider.supports(UsernamePasswordAuth.class)` — this returns `true`, since `authType == UsernamePasswordAuth.class` evaluates `true`.
3. Because `supports` returned `true`, the method prints the "found supporting provider" message and immediately calls `provider.authenticate(request)` — this is a `return` statement, so whatever this call produces (a successful result, or a thrown exception) becomes `authenticate`'s own outcome directly; the loop does not continue to the next provider afterward.
4. Inside `DaoAuthenticationProvider.authenticate`, the credential check `"alice".equals(upa.username()) && "secret123".equals(upa.password())` evaluates: `"alice".equals("alice")` is `true`, but `"secret123".equals("wrongpassword")` is `false` — the overall `&&` expression is `false`, so the `if` block is skipped, and the method falls through to `throw new RuntimeException("bad credentials for 'alice'")`.
5. This exception propagates directly out of `DaoAuthenticationProvider.authenticate`, out of the `return provider.authenticate(request)` line in `ProviderManager.authenticate`, and out of `manager.authenticate(...)` itself, to be caught by the `catch (RuntimeException e)` block in `main` — at no point was `ApiTokenAuthenticationProvider` ever consulted, confirming that `ProviderManager`'s loop commits to the first *supporting* provider's outcome rather than trying every provider regardless of whether it declares support for the given authentication type.

```
authenticate(UsernamePasswordAuth("alice", "wrongpassword")):
  loop, i=0: DaoAuthenticationProvider.supports(UsernamePasswordAuth.class) -> true
    -> call DaoAuthenticationProvider.authenticate(request)
       -> credential check fails -> throws RuntimeException("bad credentials for 'alice'")
    -> exception PROPAGATES immediately, loop NEVER reaches ApiTokenAuthenticationProvider
```

## 7. Gotchas & takeaways

> **Gotcha:** the exact behavior when a *supporting* provider throws (whether `ProviderManager` propagates that failure immediately, or continues trying any *remaining* providers that also happen to support the same authentication type) depends on configuration and the specific exception type — Spring Security's real `ProviderManager` has some nuance here for certain exception types and multi-provider-per-type configurations, which is worth consulting the current documentation for in a genuinely multi-provider-per-type setup; the simplified model in this card's examples (immediate propagation on the first supporting provider's failure) captures the common case but not every edge case of the real implementation's configurable behavior.

- `AuthenticationManager` is the interface the authentication filter calls to actually perform authentication; `ProviderManager` is the standard implementation, dispatching to an ordered list of `AuthenticationProvider`s based on which one declares support for the given `Authentication` type.
- Adding support for a new authentication mechanism is a matter of registering a new `AuthenticationProvider` with the `ProviderManager` — no change to `ProviderManager` itself, or to the filter that calls `AuthenticationManager.authenticate(...)`, is needed.
- `supports(Class)` and successfully authenticating are two independent checks — a provider can support a given authentication type but still reject specific, invalid credentials of that type, and that rejection is the outcome `ProviderManager` returns, without falling through to try other, non-supporting providers.
- Provider registration order matters when more than one provider could plausibly support the same authentication type — `ProviderManager` uses the first supporting provider it encounters, so understanding and controlling this order is relevant when multiple providers for the same type are configured.

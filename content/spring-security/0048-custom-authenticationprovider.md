---
card: spring-security
gi: 48
slug: custom-authenticationprovider
title: "Custom AuthenticationProvider"
---

## 1. What it is

A custom `AuthenticationProvider` is a hand-written implementation of the two-method interface (`authenticate(Authentication)`, `supports(Class<?>)`) that this entire section has been building toward — a self-contained unit implementing an authentication mechanism Spring Security doesn't provide out of the box, registered alongside (or instead of) `DaoAuthenticationProvider` in the same `ProviderManager`, following the identical contract every built-in provider follows.

```java
@Component
public class TwoFactorAuthenticationProvider implements AuthenticationProvider {
    private final UserDetailsService userDetailsService;
    private final PasswordEncoder passwordEncoder;
    private final TotpVerifier totpVerifier;

    public Authentication authenticate(Authentication authentication) throws AuthenticationException {
        TwoFactorAuthenticationToken token = (TwoFactorAuthenticationToken) authentication;
        UserDetails user = userDetailsService.loadUserByUsername(token.getName());
        if (!passwordEncoder.matches(token.getPassword(), user.getPassword())) {
            throw new BadCredentialsException("Bad credentials");
        }
        if (!totpVerifier.verify(user.getUsername(), token.getTotpCode())) {
            throw new BadCredentialsException("Invalid two-factor code");
        }
        return new TwoFactorAuthenticationToken(user, null, user.getAuthorities());
    }

    public boolean supports(Class<?> authenticationType) {
        return TwoFactorAuthenticationToken.class.isAssignableFrom(authenticationType);
    }
}
```

## 2. Why & when

Every built-in provider covered in this section — `DaoAuthenticationProvider`, `PreAuthenticatedAuthenticationProvider`, `RememberMeAuthenticationProvider` — solves one specific, common authentication pattern, but a real application's specific requirements (a two-factor code layered on top of a password, a proprietary token format from a legacy internal system, a custom risk-based check combining several signals at once) frequently fall outside what any built-in provider anticipates. A custom `AuthenticationProvider`, following the exact same interface every built-in provider implements, integrates seamlessly into the identical `ProviderManager` dispatch mechanism this whole section has explained — nothing about the surrounding filter chain, `SecurityContextHolder`, or authorization layer needs to know or care that this particular provider's logic is custom rather than built-in.

Reach for writing a custom `AuthenticationProvider` when:

- The required authentication logic combines multiple checks that don't map onto any single built-in provider — a password check *plus* a second factor, a password check *plus* a risk-scoring rule (unusual IP, unusual time of day) that should trigger additional verification.
- A proprietary or legacy credential format needs verifying against an existing system with no off-the-shelf Spring Security integration.
- A custom `Authentication` implementation is typically needed alongside a custom provider whenever the credential shape differs meaningfully from `UsernamePasswordAuthenticationToken` (as in the two-factor example, which needs to carry both a password *and* a TOTP code) — the provider and its paired `Authentication` type are usually designed together.

## 3. Core concept

```
 CustomAuthenticationProvider implements AuthenticationProvider:

   supports(authType):
     return true ONLY for the SPECIFIC Authentication subtype this provider knows how to handle
       (often a matching CUSTOM Authentication implementation, purpose-built alongside this provider)

   authenticate(unverified):
     1. cast/extract whatever credential shape this mechanism actually needs
        (a password AND a TOTP code, a proprietary token, multiple independent signals)
     2. perform ALL necessary verification steps, in whatever order this mechanism requires
     3. IF ANY check fails: throw an AuthenticationException subtype
     4. IF ALL checks pass: return a NEW, fully-populated, verified Authentication

 ProviderManager tries EACH registered provider's supports() in turn --
   ONLY a provider whose supports() returns true is even asked to attempt authenticate()
```

The provider's internal logic can be arbitrarily complex — the *contract* it must satisfy (the two methods, the exception-on-failure convention) never changes.

## 4. Diagram

<svg viewBox="0 0 640 170" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="A custom Authentication token carrying both a password and a TOTP code reaches ProviderManager which checks supports on each registered provider the matching TwoFactorAuthenticationProvider verifies the password then the TOTP code producing a verified Authentication only if both checks pass">
  <rect x="15" y="65" width="170" height="46" rx="8" fill="#1c2430" stroke="#8b949e" stroke-width="1.2"/>
  <text x="100" y="85" fill="#e6edf3" font-size="7.5" text-anchor="middle" font-family="sans-serif">TwoFactorAuthentication</text>
  <text x="100" y="98" fill="#e6edf3" font-size="7" text-anchor="middle" font-family="sans-serif">Token (password + TOTP)</text>

  <rect x="235" y="65" width="150" height="46" rx="8" fill="#1c2430" stroke="#79c0ff" stroke-width="1.4"/>
  <text x="310" y="85" fill="#79c0ff" font-size="7.5" text-anchor="middle" font-family="sans-serif">ProviderManager</text>
  <text x="310" y="98" fill="#e6edf3" font-size="7" text-anchor="middle" font-family="sans-serif">checks supports()</text>

  <rect x="435" y="65" width="180" height="46" rx="8" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="525" y="85" fill="#6db33f" font-size="7.5" text-anchor="middle" font-family="sans-serif">TwoFactorAuthentication</text>
  <text x="525" y="98" fill="#e6edf3" font-size="7" text-anchor="middle" font-family="sans-serif">Provider: verifies BOTH</text>

  <defs><marker id="a48" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#8b949e"/></marker></defs>
  <line x1="185" y1="88" x2="235" y2="88" stroke="#8b949e" stroke-width="1.2" marker-end="url(#a48)"/>
  <line x1="385" y1="88" x2="435" y2="88" stroke="#8b949e" stroke-width="1.2" marker-end="url(#a48)"/>
</svg>

A custom `Authentication` shape flowing through the identical dispatch mechanism every built-in provider uses.

## 5. Runnable example

The scenario: implement a full two-factor `AuthenticationProvider`, register it alongside a standard password-only provider in a `ProviderManager`, and confirm correct dispatch based on `supports()`. Start with the provider verifying both factors, then wire it into a multi-provider manager alongside a plain password provider, then add a risk-based extension requiring the second factor only for logins from an unrecognized location — a realistic production refinement.

### Level 1 — Basic

A minimal two-factor authentication provider verifying both a password and a TOTP code.

```java
import java.util.*;

public class CustomProviderLevel1 {
    record TwoFactorToken(String username, String password, String totpCode) {}
    record UserDetails(String username, String password, String currentTotpCode, Set<String> authorities) {}
    record VerifiedAuth(String principal, Set<String> authorities) {}

    static class AuthenticationException extends RuntimeException { AuthenticationException(String m) { super(m); } }

    static Map<String, UserDetails> userStore = Map.of(
            "alice", new UserDetails("alice", "hashed-hunter2", "123456", Set.of("ROLE_USER"))
    );

    static VerifiedAuth authenticate(TwoFactorToken token) {
        UserDetails user = userStore.get(token.username());
        if (user == null) throw new AuthenticationException("Bad credentials");

        if (!("hashed-" + token.password()).equals(user.password())) throw new AuthenticationException("Bad credentials");
        if (!token.totpCode().equals(user.currentTotpCode())) throw new AuthenticationException("Invalid two-factor code");

        return new VerifiedAuth(user.username(), user.authorities());
    }

    public static void main(String[] args) {
        System.out.println(authenticate(new TwoFactorToken("alice", "hunter2", "123456")));

        try {
            authenticate(new TwoFactorToken("alice", "hunter2", "999999")); // WRONG totp code
        } catch (AuthenticationException ex) {
            System.out.println("rejected: " + ex.getMessage());
        }
    }
}
```

How to run: `java CustomProviderLevel1.java`

`authenticate` checks the password first and, only if that succeeds, checks the TOTP code separately — a correct password with a wrong code is still rejected, since *both* factors must independently succeed for the method to return a `VerifiedAuth`.

### Level 2 — Intermediate

Register this custom provider alongside a plain password-only provider in a shared `ProviderManager`, dispatching correctly based on each provider's `supports()`-style check.

```java
import java.util.*;

public class CustomProviderLevel2 {
    interface Authentication {}
    record PasswordOnlyToken(String username, String password) implements Authentication {}
    record TwoFactorToken(String username, String password, String totpCode) implements Authentication {}

    record UserDetails(String username, String password, String currentTotpCode, Set<String> authorities) {}
    record VerifiedAuth(String principal, Set<String> authorities) {}

    static class AuthenticationException extends RuntimeException { AuthenticationException(String m) { super(m); } }

    interface AuthenticationProvider {
        boolean supports(Class<?> authType);
        VerifiedAuth authenticate(Authentication auth);
    }

    static Map<String, UserDetails> userStore = Map.of(
            "alice", new UserDetails("alice", "hashed-hunter2", "123456", Set.of("ROLE_USER")),
            "service-account", new UserDetails("service-account", "hashed-svcpass", null, Set.of("ROLE_SERVICE"))
    );

    static AuthenticationProvider passwordOnlyProvider = new AuthenticationProvider() {
        public boolean supports(Class<?> authType) { return PasswordOnlyToken.class.isAssignableFrom(authType); }
        public VerifiedAuth authenticate(Authentication auth) {
            PasswordOnlyToken token = (PasswordOnlyToken) auth;
            UserDetails user = userStore.get(token.username());
            if (user == null || !("hashed-" + token.password()).equals(user.password())) throw new AuthenticationException("Bad credentials");
            return new VerifiedAuth(user.username(), user.authorities());
        }
    };

    static AuthenticationProvider twoFactorProvider = new AuthenticationProvider() {
        public boolean supports(Class<?> authType) { return TwoFactorToken.class.isAssignableFrom(authType); }
        public VerifiedAuth authenticate(Authentication auth) {
            TwoFactorToken token = (TwoFactorToken) auth;
            UserDetails user = userStore.get(token.username());
            if (user == null || !("hashed-" + token.password()).equals(user.password())) throw new AuthenticationException("Bad credentials");
            if (!token.totpCode().equals(user.currentTotpCode())) throw new AuthenticationException("Invalid two-factor code");
            return new VerifiedAuth(user.username(), user.authorities());
        }
    };

    static VerifiedAuth dispatch(Authentication auth, List<AuthenticationProvider> providers) {
        for (AuthenticationProvider provider : providers) {
            if (provider.supports(auth.getClass())) return provider.authenticate(auth);
        }
        throw new IllegalStateException("no provider supports " + auth.getClass());
    }

    public static void main(String[] args) {
        List<AuthenticationProvider> providers = List.of(twoFactorProvider, passwordOnlyProvider);

        System.out.println(dispatch(new TwoFactorToken("alice", "hunter2", "123456"), providers));
        System.out.println(dispatch(new PasswordOnlyToken("service-account", "svcpass"), providers));
    }
}
```

How to run: `java CustomProviderLevel2.java`

`dispatch` checks `supports` against each provider in turn: a `TwoFactorToken` is routed to `twoFactorProvider` (the only one whose `supports` accepts that class), while a `PasswordOnlyToken` (used for the service account, which has no TOTP code configured at all) is correctly routed to `passwordOnlyProvider` instead — both authentication shapes coexist correctly in the same `providers` list.

### Level 3 — Advanced

Add a risk-based refinement: require the second factor only when the login originates from an unrecognized location, modeling an adaptive, real-world two-factor policy rather than an unconditional one.

```java
import java.util.*;

public class CustomProviderLevel3 {
    record TwoFactorToken(String username, String password, String totpCode, String sourceIp) {} // totpCode may be null
    record UserDetails(String username, String password, String currentTotpCode, Set<String> knownIps, Set<String> authorities) {}
    record VerifiedAuth(String principal, Set<String> authorities, boolean secondFactorUsed) {}

    static class AuthenticationException extends RuntimeException { AuthenticationException(String m) { super(m); } }

    static Map<String, UserDetails> userStore = Map.of(
            "alice", new UserDetails("alice", "hashed-hunter2", "123456", Set.of("10.0.0.5"), Set.of("ROLE_USER"))
    );

    static VerifiedAuth authenticate(TwoFactorToken token) {
        UserDetails user = userStore.get(token.username());
        if (user == null || !("hashed-" + token.password()).equals(user.password())) throw new AuthenticationException("Bad credentials");

        boolean fromKnownLocation = user.knownIps().contains(token.sourceIp());
        if (!fromKnownLocation) {
            // UNRECOGNIZED location -- the second factor is now REQUIRED, regardless of it being optional elsewhere
            if (token.totpCode() == null) throw new AuthenticationException("Two-factor code required from an unrecognized location");
            if (!token.totpCode().equals(user.currentTotpCode())) throw new AuthenticationException("Invalid two-factor code");
            return new VerifiedAuth(user.username(), user.authorities(), true);
        }
        // KNOWN location -- password alone is sufficient, second factor not required (even if supplied)
        return new VerifiedAuth(user.username(), user.authorities(), false);
    }

    public static void main(String[] args) {
        System.out.println("from KNOWN IP, no TOTP supplied: "
                + authenticate(new TwoFactorToken("alice", "hunter2", null, "10.0.0.5")));

        try {
            authenticate(new TwoFactorToken("alice", "hunter2", null, "203.0.113.99")); // UNKNOWN IP, no TOTP
        } catch (AuthenticationException ex) {
            System.out.println("from UNKNOWN IP, no TOTP: rejected -- " + ex.getMessage());
        }

        System.out.println("from UNKNOWN IP, WITH correct TOTP: "
                + authenticate(new TwoFactorToken("alice", "hunter2", "123456", "203.0.113.99")));
    }
}
```

How to run: `java CustomProviderLevel3.java`

Logging in from `10.0.0.5` (alice's known IP) succeeds with just a password, even with no TOTP code supplied; the identical password from `203.0.113.99` (an unrecognized IP) is rejected without a TOTP code, but succeeds once the correct code is added — the same provider adapts its verification requirements based on contextual risk, a realistic refinement over an unconditionally-required second factor.

## 6. Walkthrough

Trace `authenticate(new TwoFactorToken("alice", "hunter2", null, "203.0.113.99"))` — the rejected, unknown-IP-without-TOTP call from Level 3.

1. `user = userStore.get("alice")` retrieves alice's `UserDetails`; `!("hashed-" + "hunter2").equals(user.password())` evaluates `!"hashed-hunter2".equals("hashed-hunter2")`, i.e. `!true = false`, so the initial `BadCredentialsException`-style guard does not trigger — the password itself is correct.
2. `fromKnownLocation = user.knownIps().contains("203.0.113.99")` checks alice's `knownIps` set, `{"10.0.0.5"}`, against this IP — it does not contain `"203.0.113.99"`, so `fromKnownLocation` is `false`.
3. Because `fromKnownLocation` is `false`, the method enters the `if (!fromKnownLocation)` branch; inside, `token.totpCode() == null` checks the token's `totpCode` field, which was passed as `null` for this call — this is `true`, so the method throws `AuthenticationException("Two-factor code required from an unrecognized location")` immediately, before ever checking whether a (non-existent) code would have matched.
4. The `main` method's surrounding try/catch catches this exception and prints the rejection message, confirming the login was denied specifically because a second factor was required but absent — not because the password itself was wrong.
5. Contrast this with the third call in `main`, which supplies `"123456"` as the TOTP code from the same unrecognized IP: step 3's `token.totpCode() == null` check is now `false` (a code was supplied), so the method instead checks `token.totpCode().equals(user.currentTotpCode())`, finds `"123456".equals("123456")` to be `true`, and returns a `VerifiedAuth` with `secondFactorUsed = true` — the login succeeds specifically because the required second factor was correctly supplied this time.

```
from 10.0.0.5 (known):     password OK -> fromKnownLocation=true  -> second factor NOT required -> VERIFIED (secondFactorUsed=false)
from 203.0.113.99, no TOTP: password OK -> fromKnownLocation=false -> totpCode is null -> REJECTED ("two-factor required")
from 203.0.113.99, TOTP OK: password OK -> fromKnownLocation=false -> totpCode matches -> VERIFIED (secondFactorUsed=true)
```

## 7. Gotchas & takeaways

> **Gotcha:** a custom `AuthenticationProvider`'s `supports()` method must be precise about which `Authentication` subtype it accepts — an overly broad `supports()` implementation (accepting a supertype shared by multiple, differently-shaped tokens) risks the provider being asked to `authenticate()` a token shape it doesn't actually know how to handle correctly, typically surfacing as a `ClassCastException` at the cast inside `authenticate()` rather than a clean rejection.

- A custom `AuthenticationProvider` follows the exact same two-method contract every built-in provider does, letting arbitrarily complex, application-specific verification logic integrate seamlessly into the standard `ProviderManager` dispatch mechanism.
- A custom `Authentication` implementation is typically designed alongside a custom provider whenever the credential shape (multiple factors, a proprietary token format) differs from what `UsernamePasswordAuthenticationToken` can represent.
- `supports()` should be narrowly and precisely scoped to exactly the `Authentication` subtype(s) this specific provider knows how to correctly `authenticate()` — imprecise scoping risks runtime cast failures rather than clean provider-selection rejection.
- Risk-based or adaptive verification logic (requiring a second factor only under certain conditions) is a natural extension to build directly into a custom provider's `authenticate()` method, since it has full access to whatever contextual information the custom `Authentication` token carries.

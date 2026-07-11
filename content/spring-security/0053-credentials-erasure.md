---
card: spring-security
gi: 53
slug: credentials-erasure
title: "Credentials erasure"
---

## 1. What it is

Credentials erasure is `ProviderManager`'s default behavior of calling `eraseCredentials()` on both the resulting `Authentication` and the original `UserDetails` immediately after a successful authentication, wiping the raw password (and the `UserDetails`'s stored hash reference, if it implements `CredentialsContainer`) from memory before the `Authentication` object is stored in `SecurityContextHolder` and persisted into the session for the remainder of the request lifecycle and beyond.

```java
public interface CredentialsContainer {
    void eraseCredentials(); // implementations null-out any sensitive field they hold
}

// UsernamePasswordAuthenticationToken implements this:
public void eraseCredentials() {
    super.eraseCredentials(); // clears the generic "credentials" field
    this.password = null;     // AND this subtype's own additional sensitive field
}
```

## 2. Why & when

Once authentication succeeds, the raw password (and even the hashed password from the `UserDetails` used to verify it) has served its entire purpose — nothing later in the request lifecycle, or during however long the resulting `Authentication` sits in `SecurityContextHolder` or a persisted session, legitimately needs it again. Leaving it in memory anyway only widens the window during which a memory-inspection technique (a heap dump, a debugging tool, a memory-disclosure vulnerability elsewhere in the application) could recover it — erasing it immediately after use is a standard "minimize the sensitive data's lifetime" security practice, applied automatically by `ProviderManager` without requiring any explicit action from application code.

Reach for understanding (or correctly implementing) credentials erasure when:

- Writing a custom `Authentication` implementation (paired with a custom `AuthenticationProvider`, from the earlier card) — implementing `CredentialsContainer` correctly ensures any sensitive field this custom type holds is also wiped, matching the built-in types' behavior.
- Debugging why a previously-accessible field on an `Authentication` object (like `getCredentials()`) unexpectedly returns `null` later in the request — this is very likely erasure having already run as designed, not a bug.
- `eraseCredentialsAfterAuthentication` on `ProviderManager` can be set to `false` to disable this behavior — reach for this only in a narrow, well-understood scenario (some legacy code genuinely needing the raw credential later in the same request), since disabling it removes a real, if modest, defense-in-depth measure.

## 3. Core concept

```
 ProviderManager.authenticate(unverified), AFTER a provider successfully authenticates:

   IF eraseCredentialsAfterAuthentication == true (the DEFAULT):
     IF result instanceof CredentialsContainer:
         result.eraseCredentials()   -- wipes the AUTHENTICATION's own sensitive fields

     -- ALSO, separately, if the underlying details/principal (e.g. a UserDetails) implements CredentialsContainer:
         that object's eraseCredentials() is ALSO called

   THEN: this now-erased Authentication is what gets stored in SecurityContextHolder
          and persisted into the session for the rest of the request (and beyond, via SecurityContextRepository)
```

Erasure happens once, automatically, right after a successful authentication — never something application code needs to remember to call itself.

## 4. Diagram

<svg viewBox="0 0 640 170" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Immediately after a successful authentication ProviderManager calls eraseCredentials on the resulting Authentication object wiping the raw password before that object is stored in SecurityContextHolder and persisted for the remainder of the request and session lifetime">
  <rect x="15" y="65" width="150" height="46" rx="8" fill="#1c2430" stroke="#8b949e" stroke-width="1.2"/>
  <text x="90" y="85" fill="#e6edf3" font-size="7.5" text-anchor="middle" font-family="sans-serif">authentication</text>
  <text x="90" y="98" fill="#e6edf3" font-size="7" text-anchor="middle" font-family="sans-serif">succeeds (password still set)</text>

  <rect x="220" y="65" width="170" height="46" rx="8" fill="#1c2430" stroke="#79c0ff" stroke-width="1.4"/>
  <text x="305" y="85" fill="#79c0ff" font-size="7.5" text-anchor="middle" font-family="sans-serif">eraseCredentials()</text>
  <text x="305" y="98" fill="#e6edf3" font-size="7" text-anchor="middle" font-family="sans-serif">password set to null</text>

  <rect x="450" y="65" width="170" height="46" rx="8" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="535" y="85" fill="#6db33f" font-size="7.5" text-anchor="middle" font-family="sans-serif">stored in SecurityContext</text>
  <text x="535" y="98" fill="#e6edf3" font-size="7" text-anchor="middle" font-family="sans-serif">for rest of request/session</text>

  <defs><marker id="a53" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#8b949e"/></marker></defs>
  <line x1="165" y1="88" x2="220" y2="88" stroke="#8b949e" stroke-width="1.2" marker-end="url(#a53)"/>
  <line x1="390" y1="88" x2="450" y2="88" stroke="#8b949e" stroke-width="1.2" marker-end="url(#a53)"/>
</svg>

The raw password exists only briefly, between successful verification and this erasure step — never any longer.

## 5. Runnable example

The scenario: implement `CredentialsContainer`-style erasure on a custom `Authentication` type, wire it into a `ProviderManager`-style post-authentication step, then confirm the erasure genuinely happens automatically and prove what remains accessible (and inaccessible) afterward.

### Level 1 — Basic

A minimal `CredentialsContainer` implementation, erasing a sensitive field on demand.

```java
public class CredentialsErasureLevel1 {
    interface CredentialsContainer { void eraseCredentials(); }

    static class UsernamePasswordAuthenticationToken implements CredentialsContainer {
        private final String principal;
        private String credentials; // the RAW password -- mutable specifically so it CAN be erased later

        UsernamePasswordAuthenticationToken(String principal, String credentials) {
            this.principal = principal;
            this.credentials = credentials;
        }

        String getPrincipal() { return principal; }
        String getCredentials() { return credentials; }

        public void eraseCredentials() { this.credentials = null; }
    }

    public static void main(String[] args) {
        UsernamePasswordAuthenticationToken token = new UsernamePasswordAuthenticationToken("alice", "hunter2");
        System.out.println("before erasure: " + token.getCredentials());

        token.eraseCredentials();
        System.out.println("after erasure: " + token.getCredentials());
        System.out.println("principal still accessible: " + token.getPrincipal());
    }
}
```

How to run: `java CredentialsErasureLevel1.java`

`eraseCredentials` simply sets `this.credentials = null`; calling it makes `getCredentials()` return `null` afterward, while `getPrincipal()` remains entirely unaffected, since erasure targets only the sensitive credential field, never the identity information itself.

### Level 2 — Intermediate

Wire erasure into a `ProviderManager`-style post-authentication step, running automatically right after a successful verification.

```java
public class CredentialsErasureLevel2 {
    interface CredentialsContainer { void eraseCredentials(); }

    static class UsernamePasswordAuthenticationToken implements CredentialsContainer {
        private final String principal;
        private String credentials;
        private boolean authenticated;

        UsernamePasswordAuthenticationToken(String principal, String credentials) {
            this.principal = principal; this.credentials = credentials; this.authenticated = false;
        }

        String getPrincipal() { return principal; }
        String getCredentials() { return credentials; }
        boolean isAuthenticated() { return authenticated; }
        void markAuthenticated() { this.authenticated = true; }
        public void eraseCredentials() { this.credentials = null; }
    }

    static Map<String, String> validCredentials = java.util.Map.of("alice", "hunter2");

    // models ProviderManager.authenticate(...)
    static UsernamePasswordAuthenticationToken authenticate(String username, String rawPassword) {
        UsernamePasswordAuthenticationToken unverified = new UsernamePasswordAuthenticationToken(username, rawPassword);

        boolean matches = rawPassword.equals(validCredentials.get(username));
        if (!matches) throw new RuntimeException("Bad credentials");

        unverified.markAuthenticated();

        // the ERASURE STEP -- happens AUTOMATICALLY, right here, after a SUCCESSFUL authentication
        if (unverified instanceof CredentialsContainer container) {
            container.eraseCredentials();
        }

        return unverified;
    }

    public static void main(String[] args) {
        UsernamePasswordAuthenticationToken result = authenticate("alice", "hunter2");
        System.out.println("authenticated: " + result.isAuthenticated());
        System.out.println("credentials AFTER authenticate() returns: " + result.getCredentials());
    }
}
```

How to run: `java CredentialsErasureLevel2.java`

`authenticate` erases credentials automatically as its final step, before ever returning the result — by the time `main` receives `result`, `getCredentials()` already returns `null`, confirming that nothing external to `authenticate` ever needs to remember to call erasure itself; it's baked into the successful-authentication path.

### Level 3 — Advanced

Extend erasure to also cover a `UserDetails`-style object referenced during authentication (not just the `Authentication` token itself), and confirm a *failed* authentication attempt does *not* trigger erasure — since the raw password may still be relevant to failure-handling logic (like the account-lockout tracker from an earlier card).

```java
import java.util.*;

public class CredentialsErasureLevel3 {
    interface CredentialsContainer { void eraseCredentials(); }

    static class UserDetails implements CredentialsContainer {
        final String username;
        String password; // the STORED hash -- also erased after use, not just the raw submitted credential
        UserDetails(String username, String password) { this.username = username; this.password = password; }
        public void eraseCredentials() { this.password = null; }
    }

    static class UsernamePasswordAuthenticationToken implements CredentialsContainer {
        String principal; // starts as a raw username, becomes the UserDetails object once authenticated
        String credentials;
        UserDetails userDetailsRef; // held so its OWN erasure can also be triggered
        boolean authenticated;

        UsernamePasswordAuthenticationToken(String principal, String credentials) {
            this.principal = principal; this.credentials = credentials; this.authenticated = false;
        }

        public void eraseCredentials() {
            this.credentials = null;
            if (userDetailsRef != null) userDetailsRef.eraseCredentials(); // ALSO erase the UserDetails' own hash
        }
    }

    static Map<String, UserDetails> userStore = new HashMap<>();

    static UsernamePasswordAuthenticationToken authenticate(String username, String rawPassword) {
        UsernamePasswordAuthenticationToken unverified = new UsernamePasswordAuthenticationToken(username, rawPassword);
        UserDetails stored = userStore.get(username);

        boolean matches = stored != null && ("hashed-" + rawPassword).equals(stored.password);
        if (!matches) {
            throw new RuntimeException("Bad credentials"); // NO erasure here -- authentication never succeeded
        }

        unverified.authenticated = true;
        unverified.userDetailsRef = stored;
        unverified.eraseCredentials(); // erases BOTH the token's raw password AND stored's hash reference
        return unverified;
    }

    public static void main(String[] args) {
        userStore.put("alice", new UserDetails("alice", "hashed-hunter2"));

        UsernamePasswordAuthenticationToken result = authenticate("alice", "hunter2");
        System.out.println("token credentials after success: " + result.credentials);
        System.out.println("UserDetails password after success: " + userStore.get("alice").password);

        try {
            authenticate("alice", "wrongpass");
        } catch (RuntimeException ex) {
            System.out.println("failed attempt: " + ex.getMessage() + " (no erasure needed -- nothing succeeded)");
        }
    }
}
```

How to run: `java CredentialsErasureLevel3.java`

After a *successful* authentication, both `result.credentials` (the raw submitted password) and `userStore.get("alice").password` (the stored hash) are `null` — erasure cascaded to both objects; the failed attempt with `"wrongpass"` never reaches the erasure call at all (the exception is thrown first), which is correct, since there is nothing sensitive that successfully authenticated to erase in that case.

## 6. Walkthrough

Trace the successful `authenticate("alice", "hunter2")` call from Level 3.

1. `unverified = new UsernamePasswordAuthenticationToken("alice", "hunter2")` constructs the token, with `credentials = "hunter2"` at this point.
2. `stored = userStore.get("alice")` retrieves `new UserDetails("alice", "hashed-hunter2")`, non-null.
3. `matches = stored != null && ("hashed-" + "hunter2").equals(stored.password)` evaluates `"hashed-hunter2".equals("hashed-hunter2")`, which is `true` — the `if (!matches)` guard does not throw.
4. `unverified.authenticated = true` marks the token as authenticated; `unverified.userDetailsRef = stored` stores a reference to the `UserDetails` object, specifically so its erasure can be triggered later from the token's own `eraseCredentials` method.
5. `unverified.eraseCredentials()` runs: first `this.credentials = null` wipes the token's own raw password field; then, since `userDetailsRef` is non-null, `userDetailsRef.eraseCredentials()` is called, which sets `stored.password = null` — because `stored` is the *same object* referenced by `userStore.get("alice")`, this mutation is visible through that reference too.
6. Back in `main`, `result.credentials` prints as `null` (erased in step 5's first line) and `userStore.get("alice").password` also prints as `null` (erased in step 5's cascaded call) — both the transient authentication attempt's own credential and the durable stored user record's hash have been wiped from memory, even though `userStore` itself is a long-lived, persistent structure that will keep existing for the rest of the program.

```
authenticate("alice", "hunter2"):
  matches -> true
  unverified.eraseCredentials():
    this.credentials = null                    (the RAW submitted password, wiped)
    userDetailsRef.eraseCredentials():
      stored.password = null                    (the STORED HASH, ALSO wiped -- cascades to a second object)

authenticate("alice", "wrongpass"):
  matches -> false -> exception thrown BEFORE eraseCredentials() is ever reached (nothing to erase; nothing succeeded)
```

## 7. Gotchas & takeaways

> **Gotcha:** relying on a custom `Authentication` or `UserDetails` field to still hold a raw or hashed password *after* a successful authentication has already completed (say, for some later logging or auditing step in the same request) is a mistake that directly conflicts with this default erasure behavior — that field will already be `null` by the time such later code runs, unless `eraseCredentialsAfterAuthentication` has been explicitly disabled, which itself removes a genuine security protection. Design any code needing the raw password to run strictly before or during the authentication attempt itself, never after.

- Credentials erasure automatically wipes sensitive fields (the raw submitted password, and the `UserDetails`'s stored hash) from memory immediately after a successful authentication, minimizing how long that sensitive data remains recoverable via memory inspection.
- This is `ProviderManager`'s default behavior, requiring no explicit action from application code — a custom `Authentication` or `UserDetails` implementation should implement `CredentialsContainer` correctly to participate in it.
- Erasure only happens after a *successful* authentication — a failed attempt's exception is thrown before erasure would ever run, which is correct, since nothing sensitive succeeded that would need wiping, and failure-handling logic (an account-lockout tracker) may still need the context of the attempt.
- Erasure can cascade across multiple related objects (a token's own credentials field, plus a referenced `UserDetails`'s stored hash) — a custom implementation holding a reference to another `CredentialsContainer` should call that object's own `eraseCredentials()` too, exactly as shown in Level 3.

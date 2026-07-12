---
card: spring-security
gi: 114
slug: active-directory-authentication
title: "Active Directory authentication"
---

## 1. What it is

`ActiveDirectoryLdapAuthenticationProvider` is a purpose-built `AuthenticationProvider` for authenticating against Microsoft Active Directory specifically, rather than a generic LDAP directory — it exists because AD, while LDAP-compatible at the protocol level, has enough distinctive conventions (its `userPrincipalName` login format, its `memberOf` attribute storing group membership directly on the *user* entry rather than requiring a separate group search, and its numeric error codes embedded inside LDAP exception messages) that using a generic `BindAuthenticator` (card 0111) against it works but misses AD-specific error detail and requires manually replicating conventions this class already encapsulates.

```java
@Bean
public AuthenticationProvider activeDirectoryAuthenticationProvider() {
    ActiveDirectoryLdapAuthenticationProvider provider =
            new ActiveDirectoryLdapAuthenticationProvider("example.com", "ldap://ad.example.com:389");
    provider.setConvertSubErrorCodesToExceptions(true); // surface AD's specific failure reason, not just "auth failed"
    provider.setUseAuthenticationRequestCredentials(true);
    return provider;
}
```

## 2. Why & when

Card 0111's `BindAuthenticator` is protocol-generic — it works against any LDAP-compliant directory, AD included, by resolving a DN pattern and attempting a bind. But Active Directory diverges from that generic model in two practical ways: it strongly prefers login as `username@domain` (a `userPrincipalName`, not a DN built from a fixed pattern), and it encodes *why* a bind failed (expired password, locked account, must-change-password-at-next-logon) as a numeric sub-error code buried inside the bind exception's message text rather than as a distinct, easily-checked field. `ActiveDirectoryLdapAuthenticationProvider` parses that sub-error code and can translate it into specific Spring Security exceptions (`AccountExpiredException`, `LockedException`, `CredentialsExpiredException`), letting the rest of the authentication pipeline (card 0054's account-status handling) react to the *actual* reason without any custom parsing logic in application code.

Reach for `ActiveDirectoryLdapAuthenticationProvider` when:

- The directory being authenticated against is genuinely Microsoft Active Directory, not a different LDAP implementation — using the AD-specific provider against a non-AD directory doesn't make sense, since its error-code parsing assumes AD's specific encoding.
- Users log in with a domain-qualified username (`alice@example.com`) rather than a fixed DN pattern — AD's native login convention, which this provider handles directly rather than requiring a `userDnPatterns` configuration.
- The application needs to distinguish *why* a login failed — account locked versus password expired versus account disabled — in order to show a helpful message or trigger a specific remediation flow, rather than a single generic "authentication failed."
- An organization's identity infrastructure is AD-centric (the overwhelmingly common case in enterprises running Windows-based infrastructure) and no separate SAML/OIDC federation layer sits in front of it for this particular application.

## 3. Core concept

```
ActiveDirectoryLdapAuthenticationProvider.authenticate(username, password):
  1. build the AD-native login identity: username@domain  (e.g. "alice@example.com")
  2. attempt an LDAP bind using that identity + password, against the configured AD server
  3. bind SUCCEEDS -> proceed to fetch attributes (including "memberOf", read DIRECTLY off the user entry)
     bind FAILS    -> AD's LDAP error message embeds a SUB-ERROR CODE, e.g.:
         "... AcceptSecurityContext error, data 532, ..."   -> 532 = password expired
         "... data 775 ..."                                  -> 775 = account locked out
         "... data 533 ..."                                  -> 533 = account disabled
  4. IF setConvertSubErrorCodesToExceptions(true):
         parse that code and throw the SPECIFIC exception (CredentialsExpiredException, LockedException, ...)
     ELSE:
         throw a generic BadCredentialsException regardless of the underlying reason

memberOf attribute (AD-specific): stored DIRECTLY on the user entry, e.g.:
    memberOf: CN=Engineering,OU=Groups,DC=example,DC=com
    memberOf: CN=Admins,OU=Groups,DC=example,DC=com
-- NO separate group search needed, unlike card 0112's generic LDAP group-search pattern
```

The `memberOf`-on-the-user-entry convention is precisely why authorities population against AD is typically simpler than the generic LDAP case: the group membership is already sitting right there in the same entry the bind just succeeded against.

## 4. Diagram

<svg viewBox="0 0 660 220" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Diagram showing a bind attempt against active directory using username at domain format on failure the error message is parsed for a numeric sub error code which is translated into a specific spring security exception like account locked or credentials expired rather than a single generic authentication failure">
  <rect x="20" y="30" width="180" height="50" rx="7" fill="#1c2430" stroke="#79c0ff" stroke-width="1.3"/>
  <text x="110" y="50" fill="#79c0ff" font-size="9.5" text-anchor="middle" font-family="sans-serif">alice@example.com</text>
  <text x="110" y="65" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">+ password</text>

  <line x1="200" y1="55" x2="245" y2="55" stroke="#79c0ff" stroke-width="1.6" marker-end="url(#ad114)"/>

  <rect x="250" y="30" width="180" height="50" rx="7" fill="#1c2430" stroke="#8b949e" stroke-width="1.3"/>
  <text x="340" y="50" fill="#e6edf3" font-size="9.5" text-anchor="middle" font-family="sans-serif">bind attempt vs AD</text>
  <text x="340" y="65" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">ldap://ad.example.com</text>

  <line x1="340" y1="80" x2="340" y2="110" stroke="#8b949e" stroke-width="1.6" marker-end="url(#ad114b)"/>

  <rect x="230" y="112" width="220" height="34" rx="6" fill="#1c2430" stroke="#f0883e" stroke-width="1.3"/>
  <text x="340" y="133" fill="#f0883e" font-size="9" text-anchor="middle" font-family="sans-serif">FAILS: "... data 775 ..."</text>

  <line x1="340" y1="146" x2="340" y2="170" stroke="#f0883e" stroke-width="1.6" marker-end="url(#ad114c)"/>

  <rect x="150" y="172" width="400" height="34" rx="6" fill="#1c2430" stroke="#3fb950" stroke-width="1.4"/>
  <text x="350" y="193" fill="#3fb950" font-size="9.5" text-anchor="middle" font-family="sans-serif">parsed -&gt; LockedException (not a generic BadCredentialsException)</text>

  <defs>
    <marker id="ad114" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#79c0ff"/></marker>
    <marker id="ad114b" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#8b949e"/></marker>
    <marker id="ad114c" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#f0883e"/></marker>
  </defs>
</svg>

AD embeds the real failure reason in its error text; the provider's job is extracting that signal into a distinct, actionable exception type.

## 5. Runnable example

The scenario: model AD-style bind failures with embedded sub-error codes, parse them into specific exceptions, then read the `memberOf` attribute directly off a successful bind's user entry — contrasting it with card 0112's separate group-search approach.

### Level 1 — Basic

A bind that either succeeds or fails with an embedded AD error code.

```java
import java.util.*;

public class ActiveDirectoryLevel1 {
    record AdUserEntry(String userPrincipalName, String password, boolean locked, boolean passwordExpired) {}

    static class ActiveDirectoryServer {
        private final Map<String, AdUserEntry> users = new HashMap<>();
        void addUser(AdUserEntry user) { users.put(user.userPrincipalName(), user); }

        // returns EITHER "success" or an AD-style error message embedding a numeric sub-error code
        String attemptBind(String userPrincipalName, String password) {
            AdUserEntry user = users.get(userPrincipalName);
            if (user == null) return "AcceptSecurityContext error, data 525, v1db1"; // user not found
            if (user.locked()) return "AcceptSecurityContext error, data 775, v1db1"; // account locked out
            if (user.passwordExpired()) return "AcceptSecurityContext error, data 532, v1db1"; // password expired
            if (!user.password().equals(password)) return "AcceptSecurityContext error, data 52e, v1db1"; // bad credentials
            return "success";
        }
    }

    public static void main(String[] args) {
        ActiveDirectoryServer ad = new ActiveDirectoryServer();
        ad.addUser(new AdUserEntry("alice@example.com", "secret123", false, false));

        System.out.println(ad.attemptBind("alice@example.com", "secret123"));
        System.out.println(ad.attemptBind("alice@example.com", "WRONG"));
    }
}
```

**How to run:** save as `ActiveDirectoryLevel1.java`, run `java ActiveDirectoryLevel1.java` (JDK 17+ runs single files directly).

Expected output:
```
success
AcceptSecurityContext error, data 52e, v1db1
```

`attemptBind` mirrors AD's real behavior: a failed bind doesn't return a clean boolean, it returns (or throws, in a real LDAP client) an error message with a specific sub-error code embedded in its text — `ActiveDirectoryLdapAuthenticationProvider`'s job starts with parsing exactly this kind of string.

### Level 2 — Intermediate

Parse the sub-error code into a specific exception type, mirroring `setConvertSubErrorCodesToExceptions(true)`.

```java
import java.util.*;
import java.util.regex.*;

public class ActiveDirectoryLevel2 {
    record AdUserEntry(String userPrincipalName, String password, boolean locked, boolean passwordExpired) {}

    static class BadCredentialsException extends RuntimeException { BadCredentialsException(String m) { super(m); } }
    static class LockedException extends RuntimeException { LockedException(String m) { super(m); } }
    static class CredentialsExpiredException extends RuntimeException { CredentialsExpiredException(String m) { super(m); } }
    static class UsernameNotFoundException extends RuntimeException { UsernameNotFoundException(String m) { super(m); } }

    static class ActiveDirectoryServer {
        private final Map<String, AdUserEntry> users = new HashMap<>();
        void addUser(AdUserEntry user) { users.put(user.userPrincipalName(), user); }

        String attemptBind(String userPrincipalName, String password) {
            AdUserEntry user = users.get(userPrincipalName);
            if (user == null) return "AcceptSecurityContext error, data 525, v1db1";
            if (user.locked()) return "AcceptSecurityContext error, data 775, v1db1";
            if (user.passwordExpired()) return "AcceptSecurityContext error, data 532, v1db1";
            if (!user.password().equals(password)) return "AcceptSecurityContext error, data 52e, v1db1";
            return "success";
        }
    }

    // mirrors ActiveDirectoryLdapAuthenticationProvider's sub-error-code parsing
    static void authenticate(ActiveDirectoryServer ad, String userPrincipalName, String password) {
        String result = ad.attemptBind(userPrincipalName, password);
        if ("success".equals(result)) return;

        Matcher matcher = Pattern.compile("data (\\w+),").matcher(result);
        String code = matcher.find() ? matcher.group(1) : null;

        switch (code) {
            case "525" -> throw new UsernameNotFoundException("no such user: " + userPrincipalName);
            case "775" -> throw new LockedException("account locked out");
            case "532" -> throw new CredentialsExpiredException("password has expired");
            case "52e" -> throw new BadCredentialsException("invalid credentials");
            default -> throw new BadCredentialsException("authentication failed (unrecognized AD error: " + result + ")");
        }
    }

    public static void main(String[] args) {
        ActiveDirectoryServer ad = new ActiveDirectoryServer();
        ad.addUser(new AdUserEntry("alice@example.com", "secret123", false, false));
        ad.addUser(new AdUserEntry("bob@example.com", "hunter2", true, false));       // locked
        ad.addUser(new AdUserEntry("carol@example.com", "oldpass", false, true));     // password expired

        try { authenticate(ad, "alice@example.com", "secret123"); System.out.println("alice: authenticated"); }
        catch (RuntimeException e) { System.out.println("alice: " + e); }

        try { authenticate(ad, "bob@example.com", "hunter2"); }
        catch (RuntimeException e) { System.out.println("bob: " + e.getClass().getSimpleName() + " -- " + e.getMessage()); }

        try { authenticate(ad, "carol@example.com", "oldpass"); }
        catch (RuntimeException e) { System.out.println("carol: " + e.getClass().getSimpleName() + " -- " + e.getMessage()); }
    }
}
```

**How to run:** save as `ActiveDirectoryLevel2.java`, run `java ActiveDirectoryLevel2.java` (JDK 17+ runs single files directly).

Expected output:
```
alice: authenticated
bob: LockedException -- account locked out
carol: CredentialsExpiredException -- password has expired
```

What changed: `authenticate` now parses the numeric sub-error code out of AD's error message and throws a *specific* exception type per code — this is what lets card 0054's account-status handling (locked/expired accounts) react correctly to an AD-backed login exactly as it would to any other `UserDetailsService`-backed one, rather than every AD failure collapsing into one indistinguishable `BadCredentialsException`.

### Level 3 — Advanced

Read the `memberOf` attribute directly off a successfully-bound user entry (AD's convention, no separate group search needed), and contrast the resulting authority-population code with card 0112's generic-LDAP group-search approach.

```java
import java.util.*;
import java.util.regex.*;

public class ActiveDirectoryLevel3 {
    record AdUserEntry(String userPrincipalName, String password, boolean locked, boolean passwordExpired,
                        List<String> memberOf) {} // group DNs, stored DIRECTLY on the user entry

    static class LockedException extends RuntimeException { LockedException(String m) { super(m); } }
    static class CredentialsExpiredException extends RuntimeException { CredentialsExpiredException(String m) { super(m); } }
    static class BadCredentialsException extends RuntimeException { BadCredentialsException(String m) { super(m); } }

    record AdAuthenticationResult(String userPrincipalName, Set<String> authorities) {}

    static class ActiveDirectoryServer {
        private final Map<String, AdUserEntry> users = new HashMap<>();
        void addUser(AdUserEntry user) { users.put(user.userPrincipalName(), user); }

        Object attemptBindAndFetch(String userPrincipalName, String password) {
            AdUserEntry user = users.get(userPrincipalName);
            if (user == null) return "AcceptSecurityContext error, data 525, v1db1";
            if (user.locked()) return "AcceptSecurityContext error, data 775, v1db1";
            if (user.passwordExpired()) return "AcceptSecurityContext error, data 532, v1db1";
            if (!user.password().equals(password)) return "AcceptSecurityContext error, data 52e, v1db1";
            return user; // SUCCESS -- return the entry itself, memberOf already included, no separate search
        }
    }

    static String extractGroupCn(String groupDn) {
        // parses "CN=Engineering,OU=Groups,DC=example,DC=com" -> "Engineering"
        Matcher m = Pattern.compile("CN=([^,]+)").matcher(groupDn);
        return m.find() ? m.group(1) : groupDn;
    }

    static AdAuthenticationResult authenticate(ActiveDirectoryServer ad, String userPrincipalName, String password) {
        Object result = ad.attemptBindAndFetch(userPrincipalName, password);
        if (result instanceof String errorMessage) {
            Matcher matcher = Pattern.compile("data (\\w+),").matcher(errorMessage);
            String code = matcher.find() ? matcher.group(1) : null;
            switch (code) {
                case "775" -> throw new LockedException("account locked out");
                case "532" -> throw new CredentialsExpiredException("password has expired");
                default -> throw new BadCredentialsException("authentication failed");
            }
        }
        AdUserEntry entry = (AdUserEntry) result;
        // memberOf is ALREADY on the entry -- no separate group search needed, unlike generic LDAP (card 0112)
        Set<String> authorities = new LinkedHashSet<>();
        for (String groupDn : entry.memberOf()) {
            authorities.add("ROLE_" + extractGroupCn(groupDn).toUpperCase());
        }
        return new AdAuthenticationResult(entry.userPrincipalName(), authorities);
    }

    public static void main(String[] args) {
        ActiveDirectoryServer ad = new ActiveDirectoryServer();
        ad.addUser(new AdUserEntry("alice@example.com", "secret123", false, false,
                List.of("CN=Engineering,OU=Groups,DC=example,DC=com", "CN=Admins,OU=Groups,DC=example,DC=com")));

        AdAuthenticationResult result = authenticate(ad, "alice@example.com", "secret123");
        System.out.println("authenticated: " + result.userPrincipalName() + " authorities=" + result.authorities());
    }
}
```

**How to run:** save as `ActiveDirectoryLevel3.java`, run `java ActiveDirectoryLevel3.java` (JDK 17+ runs single files directly).

Expected output:
```
authenticated: alice@example.com authorities=[ROLE_ENGINEERING, ROLE_ADMINS]
```

What changed: `attemptBindAndFetch` returns the *entire user entry* on success — including `memberOf`, already populated — so `authenticate` reads group membership directly off that same object with zero additional directory round trips, in sharp contrast to card 0112's `DefaultLdapAuthoritiesPopulator`, which must issue a separate search for group entries referencing the user's DN. This is the concrete payoff of AD's different (user-entry-centric) group-membership modeling.

## 6. Walkthrough

Trace bob's locked-account login attempt from Level 2/3, then alice's successful one from Level 3.

**Step 1 — bob's login attempt:**
```
POST /login HTTP/1.1

username=bob@example.com&password=hunter2
```

**Step 2 — the bind attempt against AD.** `ad.attemptBindAndFetch("bob@example.com", "hunter2")` checks `users.get(...)`, finds bob's entry, and since `user.locked()` is `true`, returns the string `"AcceptSecurityContext error, data 775, v1db1"` — bob's password is actually correct, but the account's locked status is checked (and fails) before password comparison ever matters.

**Step 3 — sub-error code extraction.** `authenticate` sees `result` is a `String` (an error), applies the regex `"data (\\w+),"`, and extracts `"775"`.

**Step 4 — exception mapping.** The `switch` matches `"775"` and throws `LockedException("account locked out")` — a distinct, specific exception, not a generic authentication failure.

**Step 5 — the response, in a real Spring Security application** (following card 0054's account-status handling): the login page can render a specific message — "Your account is locked; contact your administrator" — rather than the generic "Bad credentials" a non-AD-aware provider would show for every kind of failure.

**Contrast — alice's successful login.** `ad.attemptBindAndFetch("alice@example.com", "secret123")` finds her entry, passes every check (`locked=false`, `passwordExpired=false`, password matches), and returns the `AdUserEntry` object itself — not a string. `authenticate`'s `if (result instanceof String errorMessage)` check is `false`, so it casts to `AdUserEntry` and proceeds directly to reading `entry.memberOf()`.

**Step 6 — group extraction, no separate search.** `entry.memberOf()` is already `["CN=Engineering,...", "CN=Admins,..."]` — `extractGroupCn` regex-extracts each `CN` value, and both become `ROLE_`-prefixed authorities.

```
bob:   bind checks locked FIRST -> "data 775" -> LockedException -- password never even compared
alice: bind checks pass entirely -> returns FULL entry (memberOf included) -> authorities read with ZERO extra queries
```

## 7. Gotchas & takeaways

> **Gotcha:** AD's sub-error codes are embedded as substrings inside a larger diagnostic message whose exact wording can vary slightly across AD versions and configurations — parsing them with a narrow, version-specific regex risks silently falling through to a generic failure for a code format that shifted slightly. `ActiveDirectoryLdapAuthenticationProvider`'s built-in parsing is more robust than a hand-rolled regex; prefer it over reimplementing this parsing yourself unless you have a very specific reason to.

- `ActiveDirectoryLdapAuthenticationProvider` exists because Active Directory's login conventions (`userPrincipalName`) and error reporting (numeric sub-error codes embedded in bind failure messages) diverge enough from generic LDAP that a purpose-built provider is worth using instead of `BindAuthenticator`.
- Enabling sub-error-code parsing turns AD's opaque bind failures into specific, actionable exceptions (`LockedException`, `CredentialsExpiredException`) that the rest of the authentication pipeline (card 0054) already knows how to handle.
- AD stores group membership directly on the user entry via `memberOf`, eliminating the separate group-search step that generic LDAP's `LdapAuthoritiesPopulator` (card 0112) requires — a meaningful simplification and a performance win (one directory round trip instead of two).
- Account-status checks (locked, expired, disabled) should be evaluated before password comparison matters for the user's experience — a locked account with the *correct* password should still be told "your account is locked," not "bad credentials."
- This provider is specific to Active Directory; using it against a non-AD LDAP server produces meaningless error-code parsing, since the codes and their meanings are an AD-specific convention, not a general LDAP standard.

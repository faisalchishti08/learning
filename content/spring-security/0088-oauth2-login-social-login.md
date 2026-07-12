---
card: spring-security
gi: 88
slug: oauth2-login-social-login
title: "OAuth2 Login (social login)"
---

## 1. What it is

`oauth2Login()` is the `HttpSecurity` DSL method that wires an entire "Login with Google" / "Login with GitHub" flow into a `SecurityFilterChain` — delegating the actual authentication decision to an external OAuth2 or OpenID Connect provider instead of checking a username/password against your own database. Under the hood it registers `OAuth2LoginAuthenticationFilter`, which listens for the provider's callback (by default any path matching `/login/oauth2/code/*`), drives the authorization-code-for-token exchange, fetches the user's profile from the provider, and — on success — wraps that profile as an `OAuth2User` (or `OidcUser` when the provider also issues an OpenID Connect ID token) and hands it to the `AuthenticationManager`. The resulting `Authentication` is what ends up in `SecurityContextHolder`, exactly like a form-login `Authentication` would, so the rest of the application (`@AuthenticationPrincipal`, `SecurityContext`-based authorization) doesn't need to know or care that the credential check happened on someone else's server.

```java
@Bean
public SecurityFilterChain filterChain(HttpSecurity http) throws Exception {
    http
        .authorizeHttpRequests(auth -> auth
            .requestMatchers("/", "/error", "/login/**").permitAll()
            .anyRequest().authenticated())
        .oauth2Login(oauth2 -> oauth2
            .loginPage("/login") // a custom page listing "Login with GitHub" / "Login with Google" links
            .userInfoEndpoint(userInfo -> userInfo.userAuthoritiesMapper(this::mapAuthorities)));
    return http.build();
}
```

This card is the entry point for the whole OAuth2/OpenID Connect section: it gives the end-to-end picture at a high level. The next two cards go deep on the two pieces this one only gestures at — `ClientRegistration`/`ClientRegistrationRepository` (the per-provider connection details) and the Authorization Code grant itself (the exact redirect-and-exchange protocol).

## 2. Why & when

Every prior card in this course assumed *your* application owns the credential check — a `UserDetailsService`, a `PasswordEncoder`, a database of hashed passwords. Social login exists because that ownership is often a liability rather than an asset: storing passwords means being responsible for hashing them correctly, rotating them, defending against credential-stuffing, and handling resets, and users increasingly distrust yet another site asking them to create yet another password. Delegating authentication to Google, GitHub, Microsoft, or a corporate identity provider (Okta, Azure AD) moves that liability to an organization whose entire job is running that infrastructure securely, and gives users a one-click login using an account they already trust and already have open in another tab.

Reach for `oauth2Login()` when:

- Building a consumer-facing product where reducing signup friction matters — "Continue with Google" converts better than a fresh registration form.
- Building an internal or B2B application that should authenticate against a company's existing identity provider via OpenID Connect (Okta, Azure AD, Auth0) rather than maintaining a separate user store.
- You want to avoid ever touching a user's raw password — with social login, the password never crosses your servers at all, only an authorization code and, later, tokens.
- You still need a *local* account concept afterward (e.g., to store application-specific preferences) — `oauth2Login()` authenticates the person, but linking that identity to your own user table (by email, or by provider + subject id) is your application's job, not Spring Security's.

It's not exclusive of other authentication methods — `oauth2Login()` and `formLogin()` can be configured side by side, letting users choose either path to the same authenticated `SecurityContext`.

## 3. Core concept

```
oauth2Login() registers OAuth2LoginAuthenticationFilter and wires it against every configured ClientRegistration.

High-level steps for ONE provider (say "github"):
  1. Browser asks the client app to start login       -> GET /oauth2/authorization/github
  2. Client app redirects the browser to the provider  -> 302 to https://github.com/login/oauth/authorize?...
  3. User authenticates + consents AT THE PROVIDER      -> outside Spring Security's code entirely
  4. Provider redirects the browser back with a CODE    -> 302 to /login/oauth2/code/github?code=...&state=...
  5. OAuth2LoginAuthenticationFilter catches that callback path, and SERVER-TO-SERVER (no browser involved):
       a. exchanges the code for an access token (and ID token, for OIDC) at the provider's /token endpoint
       b. calls the provider's user-info endpoint with that access token to fetch the profile
  6. Filter wraps the profile as an OAuth2User/OidcUser -> AuthenticationManager -> SecurityContextHolder

Steps 1-4 are the ClientRegistration's job to describe correctly (card 0089).
Steps 4-5's exact protocol is the Authorization Code grant (card 0090).
This card only needs step 6 in detail: what comes OUT of a successful login.
```

Everything downstream of step 6 — `@PreAuthorize`, `@AuthenticationPrincipal OAuth2User`, `SecurityContextHolder.getContext().getAuthentication()` — behaves exactly as it would for any other authentication mechanism covered earlier in this course.

## 4. Diagram

<svg viewBox="0 0 680 320" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Sequence diagram of OAuth2 login the browser asks the client app to start login the client app redirects the browser to the authorization server the browser authenticates there and is redirected back to the client app with a code the client app then exchanges that code directly with the authorization server server to server for an access token and builds an OAuth2User which is stored in the security context">
  <text x="90" y="28" fill="#6db33f" font-size="12" text-anchor="middle" font-family="sans-serif">Client App</text>
  <text x="340" y="28" fill="#79c0ff" font-size="12" text-anchor="middle" font-family="sans-serif">Browser</text>
  <text x="590" y="28" fill="#8b949e" font-size="12" text-anchor="middle" font-family="sans-serif">Authorization Server</text>

  <line x1="90" y1="40" x2="90" y2="300" stroke="#6db33f" stroke-width="1" stroke-dasharray="3,3"/>
  <line x1="340" y1="40" x2="340" y2="300" stroke="#79c0ff" stroke-width="1" stroke-dasharray="3,3"/>
  <line x1="590" y1="40" x2="590" y2="300" stroke="#8b949e" stroke-width="1" stroke-dasharray="3,3"/>

  <line x1="340" y1="65" x2="95" y2="65" stroke="#79c0ff" stroke-width="1.6" marker-end="url(#o1)"/>
  <text x="340" y="58" fill="#e6edf3" font-size="9" text-anchor="end" font-family="sans-serif">1. GET /oauth2/authorization/github</text>

  <line x1="90" y1="95" x2="335" y2="95" stroke="#6db33f" stroke-width="1.6" marker-end="url(#o2)"/>
  <text x="95" y="88" fill="#e6edf3" font-size="9" font-family="sans-serif">2. 302 Location: github.com/.../authorize?...</text>

  <line x1="340" y1="125" x2="585" y2="125" stroke="#79c0ff" stroke-width="1.6" marker-end="url(#o1)"/>
  <text x="345" y="118" fill="#e6edf3" font-size="9" font-family="sans-serif">3. GET /authorize (user logs in + consents)</text>

  <line x1="590" y1="155" x2="345" y2="155" stroke="#8b949e" stroke-width="1.6" marker-end="url(#o3)"/>
  <text x="585" y="148" fill="#e6edf3" font-size="9" text-anchor="end" font-family="sans-serif">4. 302 Location: /login/oauth2/code/github?code=..</text>

  <line x1="340" y1="185" x2="95" y2="185" stroke="#79c0ff" stroke-width="1.6" marker-end="url(#o1)"/>
  <text x="340" y="178" fill="#e6edf3" font-size="9" text-anchor="end" font-family="sans-serif">5. GET /login/oauth2/code/github?code=..</text>

  <line x1="90" y1="215" x2="585" y2="215" stroke="#6db33f" stroke-width="1.6" stroke-dasharray="6,3" marker-end="url(#o2)"/>
  <text x="95" y="208" fill="#6db33f" font-size="9" font-family="sans-serif">6. POST /token (server-to-server, client_secret) -- browser NOT involved</text>

  <line x1="590" y1="245" x2="95" y2="245" stroke="#8b949e" stroke-width="1.6" stroke-dasharray="6,3" marker-end="url(#o3)"/>
  <text x="585" y="238" fill="#e6edf3" font-size="9" text-anchor="end" font-family="sans-serif">7. access_token + user profile</text>

  <rect x="40" y="265" width="220" height="34" rx="6" fill="#1c2430" stroke="#6db33f" stroke-width="1.4"/>
  <text x="150" y="286" fill="#6db33f" font-size="9.5" text-anchor="middle" font-family="sans-serif">8. build OAuth2User -&gt; SecurityContext</text>

  <defs>
    <marker id="o1" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#79c0ff"/></marker>
    <marker id="o2" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#6db33f"/></marker>
    <marker id="o3" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#8b949e"/></marker>
  </defs>
</svg>

Steps 1–5 all bounce through the browser; step 6's code-for-token exchange is the one hop that never touches it.

## 5. Runnable example

The scenario: a small in-memory simulation of `oauth2Login()`'s end result — a fake `AuthorizationServer` standing in for a real provider, and a `login` helper standing in for `OAuth2LoginAuthenticationFilter` — grown from a single provider into multiple providers with per-provider attribute keys, then into realistic failure paths (denied consent, cross-provider account collisions).

### Level 1 — Basic

One provider (GitHub), one user, a successful login that populates a `SecurityContext`-equivalent.

```java
import java.util.*;

public class OAuth2LoginLevel1 {
    // simulates ONE provider's user database -- in reality this lives on GitHub's own servers, never ours
    static class AuthorizationServer {
        final Map<String, Map<String, Object>> users = new LinkedHashMap<>();

        AuthorizationServer() {
            Map<String, Object> octocat = new LinkedHashMap<>();
            octocat.put("login", "octocat");
            octocat.put("id", 1);
            octocat.put("name", "The Octocat");
            users.put("octocat", octocat);
        }

        // simulates the user approving consent at the provider, which then hands back their profile
        Map<String, Object> authenticate(String username) {
            return users.get(username);
        }
    }

    // mirrors Spring Security's OAuth2User: a principal backed by a provider's raw attribute map
    record OAuth2User(String nameAttributeKey, Map<String, Object> attributes) {
        String getName() { return String.valueOf(attributes.get(nameAttributeKey)); }
    }

    // mirrors SecurityContextHolder -- holds "the current authenticated principal"
    static OAuth2User currentPrincipal;

    public static void main(String[] args) {
        AuthorizationServer github = new AuthorizationServer();

        // simulates the browser returning from GitHub's consent screen with an approved login
        Map<String, Object> attributes = github.authenticate("octocat");
        OAuth2User principal = new OAuth2User("login", attributes);

        currentPrincipal = principal; // OAuth2LoginAuthenticationFilter would do this on success

        System.out.println("Authenticated principal: " + currentPrincipal.getName());
        System.out.println("Attributes: " + currentPrincipal.attributes());
    }
}
```

**How to run:** save as `OAuth2LoginLevel1.java`, run `java OAuth2LoginLevel1.java` (JDK 17+ runs single files directly).

Expected output:
```
Authenticated principal: octocat
Attributes: {login=octocat, id=1, name=The Octocat}
```

`nameAttributeKey` is `"login"` here because that's the field GitHub's profile response uses to identify the user — `getName()` looks that key up in the raw attribute map rather than assuming a fixed field name, since every provider calls its identifier something different.

### Level 2 — Intermediate

Real applications register more than one provider. Level 2 adds Google alongside GitHub, each with its own `nameAttributeKey` (GitHub uses `login`, Google uses `sub`), and a `login` helper standing in for `OAuth2LoginAuthenticationFilter` that assigns a default authority to every successful login.

```java
import java.util.*;

public class OAuth2LoginLevel2 {
    static class AuthorizationServer {
        final String registrationId;
        final String nameAttributeKey;
        final Map<String, Map<String, Object>> users = new LinkedHashMap<>();

        AuthorizationServer(String registrationId, String nameAttributeKey) {
            this.registrationId = registrationId;
            this.nameAttributeKey = nameAttributeKey;
        }

        void register(String username, Map<String, Object> attributes) { users.put(username, attributes); }

        Map<String, Object> authenticate(String username) { return users.get(username); }
    }

    record OAuth2User(String registrationId, String nameAttributeKey, Map<String, Object> attributes, Set<String> authorities) {
        String getName() { return String.valueOf(attributes.get(nameAttributeKey)); }
    }

    static OAuth2User currentPrincipal;

    // mirrors OAuth2LoginAuthenticationFilter: given a provider and username, drives the whole login
    static OAuth2User login(AuthorizationServer server, String username) {
        Map<String, Object> attributes = server.authenticate(username);
        if (attributes == null) {
            throw new IllegalStateException("provider denied or unknown user");
        }
        Set<String> authorities = Set.of("ROLE_USER"); // default authority every successful OAuth2 login gets
        return new OAuth2User(server.registrationId, server.nameAttributeKey, attributes, authorities);
    }

    public static void main(String[] args) {
        AuthorizationServer github = new AuthorizationServer("github", "login");
        Map<String, Object> octocatAttrs = new LinkedHashMap<>();
        octocatAttrs.put("login", "octocat");
        octocatAttrs.put("id", 1);
        github.register("octocat", octocatAttrs);

        AuthorizationServer google = new AuthorizationServer("google", "sub");
        Map<String, Object> aliceAttrs = new LinkedHashMap<>();
        aliceAttrs.put("sub", "109283746");
        aliceAttrs.put("email", "alice@example.com");
        google.register("alice", aliceAttrs);

        currentPrincipal = login(github, "octocat");
        System.out.println("[" + currentPrincipal.registrationId() + "] principal=" + currentPrincipal.getName()
                + " authorities=" + currentPrincipal.authorities());

        currentPrincipal = login(google, "alice");
        System.out.println("[" + currentPrincipal.registrationId() + "] principal=" + currentPrincipal.getName()
                + " authorities=" + currentPrincipal.authorities());
    }
}
```

**How to run:** save as `OAuth2LoginLevel2.java`, run `java OAuth2LoginLevel2.java` (JDK 17+ runs single files directly).

Expected output:
```
[github] principal=octocat authorities=[ROLE_USER]
[google] principal=109283746 authorities=[ROLE_USER]
```

What changed: `login` is now generic over *any* `AuthorizationServer`, and each provider carries its own `nameAttributeKey` — GitHub's principal name comes from `login`, Google's comes from `sub`, and neither provider needs to agree with the other on what to call it. This is exactly the piece card 0089's `ClientRegistration.userNameAttributeName` configures explicitly per registration.

### Level 3 — Advanced

Real logins fail, and real users authenticate with the same email through two different providers. Level 3 adds a denied-consent path (mirroring a failed exchange reaching `AuthenticationFailureHandler` instead of success) and a same-email-different-provider collision (mirroring the account-linking decision an application must make itself — Spring Security does not merge accounts across providers automatically).

```java
import java.util.*;

public class OAuth2LoginLevel3 {
    static class AuthorizationServer {
        final String registrationId;
        final String nameAttributeKey;
        final Map<String, Map<String, Object>> users = new LinkedHashMap<>();
        final Set<String> deniedUsers = new HashSet<>();

        AuthorizationServer(String registrationId, String nameAttributeKey) {
            this.registrationId = registrationId;
            this.nameAttributeKey = nameAttributeKey;
        }

        void register(String username, Map<String, Object> attributes) { users.put(username, attributes); }
        void denyConsent(String username) { deniedUsers.add(username); }

        Map<String, Object> authenticate(String username) {
            if (deniedUsers.contains(username)) return null; // user clicked "Cancel" on the consent screen
            return users.get(username);
        }
    }

    record OAuth2User(String registrationId, String nameAttributeKey, Map<String, Object> attributes, Set<String> authorities) {
        String getName() { return String.valueOf(attributes.get(nameAttributeKey)); }
    }

    static class OAuth2AuthenticationException extends RuntimeException {
        OAuth2AuthenticationException(String message) { super(message); }
    }

    static OAuth2User currentPrincipal;
    // tracks which email has already logged in via which provider -- simulates account-linking detection
    static final Map<String, String> emailToRegistrationId = new LinkedHashMap<>();

    static OAuth2User login(AuthorizationServer server, String username) {
        Map<String, Object> attributes = server.authenticate(username);
        if (attributes == null) {
            // mirrors OAuth2LoginAuthenticationFilter's failure path -> AuthenticationFailureHandler
            throw new OAuth2AuthenticationException("access_denied: user did not approve the " + server.registrationId + " consent screen");
        }

        Object email = attributes.get("email");
        if (email != null) {
            String existingProvider = emailToRegistrationId.get(email);
            if (existingProvider != null && !existingProvider.equals(server.registrationId)) {
                System.out.println("WARNING: email " + email + " already linked to provider \"" + existingProvider
                        + "\" -- this login via \"" + server.registrationId + "\" creates a SEPARATE account unless you link them");
            } else {
                emailToRegistrationId.put((String) email, server.registrationId);
            }
        }

        return new OAuth2User(server.registrationId, server.nameAttributeKey, attributes, Set.of("ROLE_USER"));
    }

    static void attemptLogin(AuthorizationServer server, String username) {
        try {
            currentPrincipal = login(server, username);
            System.out.println("[" + server.registrationId + "] SUCCESS principal=" + currentPrincipal.getName());
        } catch (OAuth2AuthenticationException e) {
            currentPrincipal = null; // SecurityContext stays empty -- a failed login never sets a principal
            System.out.println("[" + server.registrationId + "] FAILED: " + e.getMessage());
        }
    }

    public static void main(String[] args) {
        AuthorizationServer github = new AuthorizationServer("github", "login");
        Map<String, Object> octocatAttrs = new LinkedHashMap<>();
        octocatAttrs.put("login", "octocat");
        octocatAttrs.put("email", "octocat@example.com");
        github.register("octocat", octocatAttrs);

        AuthorizationServer google = new AuthorizationServer("google", "sub");
        Map<String, Object> sameEmailAttrs = new LinkedHashMap<>();
        sameEmailAttrs.put("sub", "555000111");
        sameEmailAttrs.put("email", "octocat@example.com"); // SAME email as the GitHub account above
        google.register("octocat.g", sameEmailAttrs);
        google.denyConsent("bob"); // bob will click "Cancel" on Google's consent screen

        attemptLogin(github, "octocat");
        attemptLogin(google, "octocat.g");
        attemptLogin(google, "bob");
    }
}
```

**How to run:** save as `OAuth2LoginLevel3.java`, run `java OAuth2LoginLevel3.java` (JDK 17+ runs single files directly).

Expected output:
```
[github] SUCCESS principal=octocat
WARNING: email octocat@example.com already linked to provider "github" -- this login via "google" creates a SEPARATE account unless you link them
[google] SUCCESS principal=555000111
[google] FAILED: access_denied: user did not approve the google consent screen
```

What changed: `login` can now fail (bob's Google consent was denied, so `authenticate` returns `null` and `login` throws instead of returning a principal — `attemptLogin` catches it and leaves `currentPrincipal` untouched, exactly mirroring how a rejected authorization never reaches `SecurityContextHolder`), and a second, independent success path now detects that two *different* provider identities share the same email address without silently merging them — that decision is left to the application.

## 6. Walkthrough

Trace the first success in Level 3, `attemptLogin(github, "octocat")`, as if it were a real HTTP exchange end to end.

**Step 1 — browser starts the login:**
```
GET /oauth2/authorization/github HTTP/1.1
Host: app.example.com
```
This hits `OAuth2AuthorizationRequestRedirectFilter` (registered automatically by `oauth2Login()`), which builds an authorization request from GitHub's `ClientRegistration` (card 0089) and responds:
```
HTTP/1.1 302 Found
Location: https://github.com/login/oauth/authorize?client_id=abc123&redirect_uri=https%3A%2F%2Fapp.example.com%2Flogin%2Foauth2%2Fcode%2Fgithub&scope=read:user&state=xyz&response_type=code
```

**Step 2 — the browser follows the redirect to GitHub.** The user logs in and clicks "Authorize" — this is entirely outside Spring Security's code, which is why `AuthorizationServer.authenticate("octocat")` in Level 3 just returns a canned attribute map rather than simulating a login form: from the client application's point of view, everything up to this point is a black box it doesn't control.

**Step 3 — GitHub redirects back with a one-time code:**
```
HTTP/1.1 302 Found
Location: https://app.example.com/login/oauth2/code/github?code=SplxlOBeZQQYbYS6WxSbIA&state=xyz
```

**Step 4 — the browser follows that redirect, hitting the callback:**
```
GET /login/oauth2/code/github?code=SplxlOBeZQQYbYS6WxSbIA&state=xyz HTTP/1.1
Host: app.example.com
```
This path matches `OAuth2LoginAuthenticationFilter`'s default pattern (`/login/oauth2/code/*`), so the filter takes over from here.

**Step 5 — server-to-server token exchange (the browser is not involved in this hop at all):**
```
POST /login/oauth/access_token HTTP/1.1
Host: github.com
Content-Type: application/x-www-form-urlencoded

grant_type=authorization_code&code=SplxlOBeZQQYbYS6WxSbIA&redirect_uri=https%3A%2F%2Fapp.example.com%2Flogin%2Foauth2%2Fcode%2Fgithub&client_id=abc123&client_secret=***
```
GitHub responds with an access token; the filter then calls GitHub's user-info endpoint with that token. That whole step corresponds, in the code, to `github.authenticate("octocat")` returning the `attributes` map — the simulation collapses "exchange code for token" and "fetch profile with token" into one method call, since this card's focus is the *result*, not the wire protocol (card 0090 unpacks that exchange in full).

**Step 6 — building the principal:** `login(github, "octocat")` constructs `new OAuth2User("github", "login", attributes, Set.of("ROLE_USER"))`. `currentPrincipal = principal;` mirrors `SecurityContextHolder.getContext().setAuthentication(...)` — from this point on, a controller parameter typed `@AuthenticationPrincipal OAuth2User` resolves to this exact object.

**Step 7 — the client app responds to the browser's step-4 request:**
```
HTTP/1.1 302 Found
Location: https://app.example.com/
Set-Cookie: JSESSIONID=9F6A2B...; HttpOnly; Secure
```
The session cookie is how the browser's *next* request gets recognized as the same authenticated user — `oauth2Login()` still relies on the ordinary HTTP session under the hood, exactly like `formLogin()` does.

The second and third `attemptLogin` calls in Level 3 skip straight to step 6's outcome: `octocat.g`'s login succeeds and prints the account-linking `WARNING` (its `email` collides with `octocat`'s GitHub account, but no code here merges the two), while `bob`'s login never gets past `authenticate` returning `null` — no redirect back with a code would ever have arrived in a real system, so no `SecurityContext` gets populated, and the client would render its configured `failureUrl` instead of a `200 OK`.

## 7. Gotchas & takeaways

> **Gotcha:** `SecurityContextHolder` is only ever populated on a *successful* exchange. A denied consent, a network failure during the token exchange, or a provider outage all leave the context empty — there is no partial or "logged in but unverified" state, so code that assumes `@AuthenticationPrincipal` is non-null on any request reaching an `authenticated()`-protected endpoint is safe, but code that runs *before* authorization is enforced must not assume a principal exists yet.

> **Gotcha:** `OAuth2User` and `OidcUser` are not the same thing. A provider that only implements plain OAuth2 (no OpenID Connect) gives you an `OAuth2User` built purely from the userinfo endpoint's response; a provider that also issues an ID token (Google, and any OIDC-compliant provider) gives you an `OidcUser`, which additionally exposes the ID token's claims (`iss`, `aud`, `exp`, and whatever the provider includes). Code written against `OAuth2User` still works for `OidcUser` (it's a subtype), but code that needs ID-token-specific claims must cast or type against `OidcUser` explicitly.

- `oauth2Login()` wires the entire redirect-callback-exchange-userinfo pipeline automatically for every configured provider — application code only needs to react to the resulting `OAuth2User`/`OidcUser`, not implement any of the protocol steps.
- `OAuth2LoginAuthenticationFilter` intercepts the default `/login/oauth2/code/*` callback pattern; the code-for-token exchange it triggers happens server-to-server, never through the browser.
- A principal only appears in the `SecurityContext` after a *successful* exchange — denied consent, provider errors, and network failures all leave it empty rather than partially populated.
- Linking two different providers' identities to one local account (by matching email, for instance) is entirely the application's responsibility — Spring Security treats `github:octocat` and `google:octocat.g` as two unrelated principals even if their email attributes match.
- Each provider names its stable identifier differently (`login` for GitHub, `sub` for Google) — this is exactly what `ClientRegistration.userNameAttributeName` (card 0089) exists to configure per registration, rather than hard-coding one convention everywhere.

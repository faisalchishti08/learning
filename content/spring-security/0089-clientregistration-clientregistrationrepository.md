---
card: spring-security
gi: 89
slug: clientregistration-clientregistrationrepository
title: "ClientRegistration & ClientRegistrationRepository"
---

## 1. What it is

`ClientRegistration` is the immutable, per-provider configuration object that describes everything Spring Security needs to talk to one specific OAuth2/OIDC provider: its authorization endpoint, its token endpoint, the client id and secret your application was issued, the scopes to request, the redirect URI pattern, and which grant type to use. `ClientRegistrationRepository` is the interface that stores and looks up these registrations by a `registrationId` (the short name — `"github"`, `"google"`, `"okta"` — that appears in URLs like `/oauth2/authorization/github`). When Spring Boot sees `spring.security.oauth2.client.registration.*` properties in `application.yml`, it auto-builds a `ClientRegistration` per configured provider and registers them all in an `InMemoryClientRegistrationRepository` bean automatically — no Java configuration required for the common case.

```yaml
spring:
  security:
    oauth2:
      client:
        registration:
          github:
            client-id: abc123
            client-secret: ${GITHUB_CLIENT_SECRET}
            scope: read:user
        provider:
          github:
            authorization-uri: https://github.com/login/oauth/authorize
            token-uri: https://github.com/login/oauth/access_token
            user-info-uri: https://api.github.com/user
            user-name-attribute: login
```

This single `registration.github` block is everything card 0088's `oauth2Login()` needed to know in order to build the "Login with GitHub" redirect — `ClientRegistrationRepository` is where that block lives once Spring Boot parses it into an object.

## 2. Why & when

The previous card described the OAuth2 login *flow* in the abstract — redirect, code, exchange, profile. That flow is identical in shape for every provider, but the specific URLs, client credentials, and scopes differ completely between GitHub, Google, and a corporate Okta tenant. `ClientRegistration` exists to hold exactly that provider-specific detail in one typed object, so the rest of Spring Security's OAuth2 machinery (`OAuth2AuthorizationRequestRedirectFilter`, `OAuth2LoginAuthenticationFilter`) can be written once, generically, against "a `ClientRegistration`" rather than once per provider. `ClientRegistrationRepository` exists because an application commonly supports more than one provider at a time and needs a way to look one up by the `registrationId` embedded in the incoming request's path.

Reach for this pair when:

- Adding a new OAuth2 provider to an application — in the common case this means adding a new `spring.security.oauth2.client.registration.<id>` block to configuration, not writing Java code.
- Registering with a provider that Spring Boot doesn't have built-in defaults for (only Google, GitHub, Facebook, and Okta ship with sensible `provider.*` defaults) — every endpoint URL must be supplied explicitly, as the YAML above does for GitHub's non-OIDC endpoints.
- Building a `ClientRegistration` programmatically at startup — for example, when registration details come from a database or a secrets manager rather than static configuration — via `ClientRegistration.withRegistrationId(...)` and a custom `ClientRegistrationRepository` implementation.
- Debugging a login that redirects to the wrong URL or fails the token exchange — the first thing to inspect is always the resolved `ClientRegistration` for that `registrationId`, since nearly every OAuth2 login problem traces back to one field in it being wrong (redirect URI mismatch, wrong scope, wrong token endpoint).

## 3. Core concept

```
ClientRegistration (ONE per provider, immutable, built once at startup):
    registrationId          -- "github" -- appears in /oauth2/authorization/{registrationId}
    clientId, clientSecret  -- issued by the provider when you registered your app with them
    authorizationUri        -- where the browser gets redirected to authenticate
    tokenUri                -- where the SERVER exchanges a code for a token
    userInfoUri             -- where the SERVER fetches the user's profile after getting a token
    scopes                  -- what access is being requested (e.g. "read:user")
    redirectUri             -- template; Spring fills in {baseUrl}/login/oauth2/code/{registrationId}
    userNameAttributeName   -- which field in the profile response is the stable identifier
    authorizationGrantType  -- almost always AUTHORIZATION_CODE for user-facing login

ClientRegistrationRepository (lookup service, one method that matters):
    findByRegistrationId(String registrationId) -> ClientRegistration

InMemoryClientRegistrationRepository -- default; built by Spring Boot autoconfiguration
                                         from application.yml, held for the app's lifetime
```

Every step of card 0088's diagram — the redirect URL, the callback path, the token endpoint hit server-to-server — is a template filled in with exactly one `ClientRegistration`'s fields.

## 4. Diagram

<svg viewBox="0 0 640 260" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Application yaml configuration is parsed at startup into ClientRegistration objects held in an InMemoryClientRegistrationRepository keyed by registration id when a request arrives for a given registration id the repository is asked to find that registration and returns the matching object which the login filter then uses to build the correct provider specific redirect and token exchange">
  <rect x="20" y="20" width="180" height="60" rx="7" fill="#1c2430" stroke="#8b949e" stroke-width="1.3"/>
  <text x="110" y="45" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">application.yml</text>
  <text x="110" y="60" fill="#8b949e" font-size="8.5" text-anchor="middle" font-family="sans-serif">registration.github, .google</text>

  <line x1="200" y1="50" x2="250" y2="50" stroke="#8b949e" stroke-width="1.6" marker-end="url(#c89)"/>
  <text x="225" y="42" fill="#8b949e" font-size="8.5" text-anchor="middle" font-family="sans-serif">parsed at startup</text>

  <rect x="255" y="20" width="230" height="60" rx="7" fill="#1c2430" stroke="#6db33f" stroke-width="1.6"/>
  <text x="370" y="45" fill="#6db33f" font-size="10.5" text-anchor="middle" font-family="sans-serif">InMemoryClientRegistrationRepository</text>
  <text x="370" y="60" fill="#8b949e" font-size="8.5" text-anchor="middle" font-family="sans-serif">keyed by registrationId</text>

  <line x1="130" y1="120" x2="130" y2="90" stroke="#79c0ff" stroke-width="1.6" marker-end="url(#c89b)"/>
  <text x="130" y="135" fill="#79c0ff" font-size="9" text-anchor="middle" font-family="sans-serif">GET /oauth2/authorization/github</text>

  <line x1="200" y1="115" x2="360" y2="85" stroke="#79c0ff" stroke-width="1.4" stroke-dasharray="4,3" marker-end="url(#c89)"/>
  <text x="290" y="105" fill="#79c0ff" font-size="8.5" text-anchor="middle" font-family="sans-serif">findByRegistrationId("github")</text>

  <rect x="40" y="150" width="220" height="70" rx="7" fill="#1c2430" stroke="#6db33f" stroke-width="1.4"/>
  <text x="150" y="172" fill="#6db33f" font-size="10" text-anchor="middle" font-family="sans-serif">resolved ClientRegistration</text>
  <text x="150" y="188" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">authorizationUri, clientId,</text>
  <text x="150" y="200" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">scope, redirectUri</text>

  <line x1="370" y1="80" x2="150" y2="150" stroke="#6db33f" stroke-width="1.6" marker-end="url(#c89)"/>

  <rect x="340" y="150" width="260" height="70" rx="7" fill="#1c2430" stroke="#79c0ff" stroke-width="1.3"/>
  <text x="470" y="172" fill="#79c0ff" font-size="10" text-anchor="middle" font-family="sans-serif">redirect built from those fields</text>
  <text x="470" y="188" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">302 to github.com/login/oauth/authorize</text>
  <text x="470" y="200" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">?client_id=...&amp;scope=...&amp;redirect_uri=...</text>

  <line x1="260" y1="185" x2="335" y2="185" stroke="#8b949e" stroke-width="1.6" marker-end="url(#c89)"/>

  <defs>
    <marker id="c89" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#79c0ff"/></marker>
    <marker id="c89b" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#79c0ff"/></marker>
  </defs>
</svg>

Configuration is parsed once into registrations; every login request resolves one registration by id and builds its redirect entirely from that object's fields.

## 5. Runnable example

The scenario: model `ClientRegistration` and an in-memory repository, grow it from one provider into several, then add validation that catches a misconfigured registration (missing redirect URI, provider Spring Boot has no defaults for) before it can cause a confusing runtime failure.

### Level 1 — Basic

One provider, a lookup by registration id.

```java
import java.util.*;

public class ClientRegistrationLevel1 {
    record ClientRegistration(String registrationId, String clientId, String clientSecret,
                               String authorizationUri, String tokenUri, String scope) {}

    static class InMemoryClientRegistrationRepository {
        private final Map<String, ClientRegistration> registrations = new LinkedHashMap<>();

        InMemoryClientRegistrationRepository(ClientRegistration... regs) {
            for (ClientRegistration r : regs) registrations.put(r.registrationId(), r);
        }

        ClientRegistration findByRegistrationId(String registrationId) {
            return registrations.get(registrationId); // null if no such registration was ever configured
        }
    }

    public static void main(String[] args) {
        ClientRegistration github = new ClientRegistration("github", "abc123", "secret-xyz",
                "https://github.com/login/oauth/authorize", "https://github.com/login/oauth/access_token", "read:user");

        InMemoryClientRegistrationRepository repository = new InMemoryClientRegistrationRepository(github);

        ClientRegistration resolved = repository.findByRegistrationId("github");
        System.out.println("resolved: " + resolved.registrationId() + " scope=" + resolved.scope());
        System.out.println("unknown provider: " + repository.findByRegistrationId("bitbucket"));
    }
}
```

**How to run:** save as `ClientRegistrationLevel1.java`, run `java ClientRegistrationLevel1.java` (JDK 17+ runs single files directly).

Expected output:
```
resolved: github scope=read:user
unknown provider: null
```

The repository is nothing more than a map from `registrationId` to a `ClientRegistration` — looking up a provider that was never configured correctly yields `null` rather than throwing, exactly as the real `InMemoryClientRegistrationRepository` behaves.

### Level 2 — Intermediate

Add a second provider (Google) with different endpoints and its own `userNameAttributeName`, and add the `redirectUri` template that gets filled in per-registration.

```java
import java.util.*;

public class ClientRegistrationLevel2 {
    record ClientRegistration(String registrationId, String clientId, String clientSecret,
                               String authorizationUri, String tokenUri, String scope,
                               String redirectUriTemplate, String userNameAttributeName) {

        String buildRedirectUri(String baseUrl) {
            return redirectUriTemplate.replace("{baseUrl}", baseUrl).replace("{registrationId}", registrationId);
        }
    }

    static class InMemoryClientRegistrationRepository {
        private final Map<String, ClientRegistration> registrations = new LinkedHashMap<>();
        InMemoryClientRegistrationRepository(ClientRegistration... regs) {
            for (ClientRegistration r : regs) registrations.put(r.registrationId(), r);
        }
        ClientRegistration findByRegistrationId(String registrationId) { return registrations.get(registrationId); }
    }

    public static void main(String[] args) {
        ClientRegistration github = new ClientRegistration("github", "abc123", "secret-xyz",
                "https://github.com/login/oauth/authorize", "https://github.com/login/oauth/access_token",
                "read:user", "{baseUrl}/login/oauth2/code/{registrationId}", "login");

        ClientRegistration google = new ClientRegistration("google", "def456", "secret-uvw",
                "https://accounts.google.com/o/oauth2/v2/auth", "https://oauth2.googleapis.com/token",
                "openid,profile,email", "{baseUrl}/login/oauth2/code/{registrationId}", "sub");

        InMemoryClientRegistrationRepository repository =
                new InMemoryClientRegistrationRepository(github, google);

        for (String id : List.of("github", "google")) {
            ClientRegistration reg = repository.findByRegistrationId(id);
            System.out.println(id + " -> redirect=" + reg.buildRedirectUri("https://app.example.com")
                    + " nameAttr=" + reg.userNameAttributeName());
        }
    }
}
```

**How to run:** save as `ClientRegistrationLevel2.java`, run `java ClientRegistrationLevel2.java` (JDK 17+ runs single files directly).

Expected output:
```
github -> redirect=https://app.example.com/login/oauth2/code/github nameAttr=login
google -> redirect=https://app.example.com/login/oauth2/code/google nameAttr=sub
```

What changed: `redirectUriTemplate` is now a template string with placeholders, and `buildRedirectUri` fills them in per-registration and per-deployment base URL — this is exactly why the redirect URI registered with a provider's developer console must match `{baseUrl}/login/oauth2/code/{registrationId}` precisely, since a mismatch here is rejected by the provider before Spring Security ever sees the callback.

### Level 3 — Advanced

Real registrations can be misconfigured — a missing endpoint, a registration id that collides, an unrecognized provider with no built-in defaults. Level 3 adds a `validate` step that mirrors the checks Spring Boot's autoconfiguration performs (and fails fast on) before a registration is ever usable.

```java
import java.util.*;

public class ClientRegistrationLevel3 {
    record ClientRegistration(String registrationId, String clientId, String clientSecret,
                               String authorizationUri, String tokenUri, String scope,
                               String redirectUriTemplate, String userNameAttributeName) {}

    static class ClientRegistrationValidationException extends RuntimeException {
        ClientRegistrationValidationException(String message) { super(message); }
    }

    // mirrors the fail-fast checks Spring Boot's OAuth2ClientPropertiesRegistrationAdapter performs
    static void validate(ClientRegistration reg) {
        List<String> problems = new ArrayList<>();
        if (reg.clientId() == null || reg.clientId().isBlank())
            problems.add("clientId is required");
        if (reg.authorizationUri() == null || reg.authorizationUri().isBlank())
            problems.add("authorization-uri is required for provider \"" + reg.registrationId()
                    + "\" (only google/github/facebook/okta have built-in defaults)");
        if (reg.tokenUri() == null || reg.tokenUri().isBlank())
            problems.add("token-uri is required for provider \"" + reg.registrationId() + "\"");
        if (reg.redirectUriTemplate() == null || reg.redirectUriTemplate().isBlank())
            problems.add("redirect-uri is required");
        if (!problems.isEmpty()) {
            throw new ClientRegistrationValidationException(
                    "invalid registration \"" + reg.registrationId() + "\": " + String.join("; ", problems));
        }
    }

    static class InMemoryClientRegistrationRepository {
        private final Map<String, ClientRegistration> registrations = new LinkedHashMap<>();

        InMemoryClientRegistrationRepository(ClientRegistration... regs) {
            for (ClientRegistration r : regs) {
                if (registrations.containsKey(r.registrationId())) {
                    throw new ClientRegistrationValidationException(
                            "duplicate registrationId \"" + r.registrationId() + "\" -- registration ids must be unique");
                }
                validate(r); // fail fast at startup, not on the first login attempt
                registrations.put(r.registrationId(), r);
            }
        }

        ClientRegistration findByRegistrationId(String registrationId) { return registrations.get(registrationId); }
    }

    static void tryBuild(String label, ClientRegistration... regs) {
        try {
            new InMemoryClientRegistrationRepository(regs);
            System.out.println(label + ": OK");
        } catch (ClientRegistrationValidationException e) {
            System.out.println(label + ": REJECTED -- " + e.getMessage());
        }
    }

    public static void main(String[] args) {
        ClientRegistration valid = new ClientRegistration("github", "abc123", "secret-xyz",
                "https://github.com/login/oauth/authorize", "https://github.com/login/oauth/access_token",
                "read:user", "{baseUrl}/login/oauth2/code/{registrationId}", "login");

        // a provider with no built-in defaults, configured without an authorization-uri
        ClientRegistration missingAuthUri = new ClientRegistration("internal-idp", "id-999", "secret-999",
                null, "https://idp.internal.example.com/token",
                "openid", "{baseUrl}/login/oauth2/code/{registrationId}", "sub");

        ClientRegistration duplicateGithub = new ClientRegistration("github", "another-id", "another-secret",
                "https://github.com/login/oauth/authorize", "https://github.com/login/oauth/access_token",
                "read:user", "{baseUrl}/login/oauth2/code/{registrationId}", "login");

        tryBuild("single valid registration", valid);
        tryBuild("missing authorization-uri", missingAuthUri);
        tryBuild("duplicate registrationId", valid, duplicateGithub);
    }
}
```

**How to run:** save as `ClientRegistrationLevel3.java`, run `java ClientRegistrationLevel3.java` (JDK 17+ runs single files directly).

Expected output:
```
single valid registration: OK
missing authorization-uri: REJECTED -- invalid registration "internal-idp": authorization-uri is required for provider "internal-idp" (only google/github/facebook/okta have built-in defaults)
duplicate registrationId: REJECTED -- duplicate registrationId "github" -- registration ids must be unique
```

What changed: registrations are now validated the moment they are added to the repository rather than the moment a login is attempted — this mirrors why a typo in `application.yml`'s provider block surfaces as a startup failure in a real Spring Boot application (a fast, loud signal) instead of a confusing runtime 500 the first time a user clicks "Login with internal-idp."

## 6. Walkthrough

Trace what happens between application startup and the first successful redirect for GitHub, using Level 2's model as the concrete objects involved.

**Step 1 — startup, configuration parsing.** Spring Boot reads `spring.security.oauth2.client.registration.github.*` and `provider.github.*` from `application.yml` and constructs one `ClientRegistration` object — this corresponds to `github` being built in `main` with its `authorizationUri`, `tokenUri`, `scope`, and `redirectUriTemplate` already filled in.

**Step 2 — startup, repository construction.** That `ClientRegistration` (and any others configured) is handed to `new InMemoryClientRegistrationRepository(...)`, which is registered as a singleton bean. This happens exactly once, at application startup, not per-request.

**Step 3 — inbound request:**
```
GET /oauth2/authorization/github HTTP/1.1
Host: app.example.com
```
`OAuth2AuthorizationRequestRedirectFilter` extracts `"github"` from the path and calls `clientRegistrationRepository.findByRegistrationId("github")` — corresponding to `repository.findByRegistrationId("github")` in Level 2, returning the `github` registration.

**Step 4 — building the redirect.** The filter reads `authorizationUri`, `clientId`, `scope`, and calls `buildRedirectUri("https://app.example.com")` (using the request's own scheme/host as the base URL) to compute the callback address the provider must redirect back to. It assembles:
```
HTTP/1.1 302 Found
Location: https://github.com/login/oauth/authorize?response_type=code&client_id=abc123&scope=read:user&state=xyz&redirect_uri=https%3A%2F%2Fapp.example.com%2Flogin%2Foauth2%2Fcode%2Fgithub
```

**Step 5 — the round trip (card 0088's steps 3–6) proceeds using this exact `ClientRegistration`.** When the callback arrives at `/login/oauth2/code/github`, the *same* registration object is looked up again (by the same `registrationId` embedded in the callback path) to find `tokenUri` for the server-to-server exchange, and `userNameAttributeName` (`"login"`) to know which field of GitHub's profile response identifies the user once it comes back.

```
startup:  yml -> ClientRegistration("github", ...) -> stored in repository (once)
request:  /oauth2/authorization/github -> repository.findByRegistrationId("github") -> same object
callback: /login/oauth2/code/github     -> repository.findByRegistrationId("github") -> same object again
```

Every field used across the entire login flow — both directions, both requests — traces back to the one `ClientRegistration` resolved by `registrationId`, built once at startup and never mutated.

## 7. Gotchas & takeaways

> **Gotcha:** `ClientRegistration` is immutable and resolved once per request by `registrationId` — there is no per-user or per-request variation in a registration's configuration. If different tenants need different client ids for the "same" provider (multi-tenant OAuth2), that requires *multiple* registrations (`"okta-tenant-a"`, `"okta-tenant-b"`) or a custom `ClientRegistrationRepository` that resolves registrations dynamically, not a mutation of one shared object.

- `ClientRegistration` is the immutable, per-provider configuration; `ClientRegistrationRepository` is the lookup service that resolves one by `registrationId`.
- Spring Boot autoconfigures an `InMemoryClientRegistrationRepository` from `spring.security.oauth2.client.registration.*` properties — only Google, GitHub, Facebook, and Okta get built-in endpoint defaults; every other provider needs every `provider.*` URI supplied explicitly.
- The `redirectUri` template's placeholders (`{baseUrl}`, `{registrationId}`) must match what was registered in the provider's own developer console exactly, or the provider rejects the callback before Spring Security ever sees it.
- `userNameAttributeName` is provider-specific (`login` for GitHub, `sub` for Google) and is read from this object to build the eventual `OAuth2User`, tying directly back into card 0088's `getName()` behavior.
- Misconfiguration (a missing required URI, a duplicate registration id) is best caught at startup, not on the first login attempt — validating the registration when it's registered, not when it's first used, turns a confusing runtime failure into a clear boot-time error.

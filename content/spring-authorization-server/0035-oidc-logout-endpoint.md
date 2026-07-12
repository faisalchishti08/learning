---
card: spring-authorization-server
gi: 35
slug: oidc-logout-endpoint
title: "OIDC logout endpoint"
---

## 1. What it is

The OIDC RP-Initiated Logout endpoint (`GET/POST /connect/logout` by default) lets a client ("relying party") end the user's session at the authorization server, not just locally in the client's own app. It's implemented internally as `OidcLogoutEndpointFilter`, part of the same OIDC feature set enabled via `.oidc(Customizer.withDefaults())`.

## 2. Why & when

Clearing a client's local session cookie logs the user out of *that one app*, but the authorization server's own session — the thing that let the authorization endpoint (card 0026) silently re-issue codes without re-prompting for a password — is untouched. If a user clicks "log out" in one client but the authorization server session survives, logging into a second client (or the same one again) can silently re-authenticate them without ever showing a login form, which looks like logout didn't work.

Reach for this endpoint when:

- Implementing a genuine "log out" button — sending the user's browser here (not just clearing local state) is what actually ends the server-side session.
- Building single sign-out across multiple clients sharing one authorization server session — ending the server session here is the trigger for it.
- Debugging "I logged out but got logged straight back in" — almost always means the client only cleared its local session and never redirected to this endpoint.

## 3. Core concept

Think of the authorization server session as a building's master keycard system, and each client as a separate office inside that building. Badging out of one office (clearing a client's local cookie) doesn't deactivate your master keycard (the server session) — you can walk right into the next office without badging in again. The logout endpoint is the security desk at the building's exit: hand back your ID token (as `id_token_hint`), and the desk deactivates the master keycard itself, so *every* office now requires fresh badge-in.

```
GET /connect/logout
    ?id_token_hint=eyJhbGciOiJSUzI1NiJ9...
    &post_logout_redirect_uri=https://task-tracker.example.com/logged-out
    &state=abc789
```

## 4. Diagram

<svg viewBox="0 0 640 240" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Client redirects browser to logout endpoint with ID token hint, server ends session, then redirects to post-logout URI">
  <rect x="10" y="90" width="130" height="50" rx="8" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="75" y="120" fill="#e6edf3" font-size="11" text-anchor="middle" font-family="sans-serif">Browser</text>

  <rect x="230" y="90" width="160" height="50" rx="8" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="310" y="113" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">OidcLogoutEndpoint</text>
  <text x="310" y="128" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">Filter</text>

  <rect x="480" y="90" width="140" height="50" rx="8" fill="#1c2430" stroke="#3fb950" stroke-width="1.5"/>
  <text x="550" y="113" fill="#e6edf3" font-size="11" text-anchor="middle" font-family="sans-serif">Server session</text>
  <text x="550" y="128" fill="#e6edf3" font-size="11" text-anchor="middle" font-family="sans-serif">invalidated</text>

  <line x1="140" y1="105" x2="225" y2="105" stroke="#8b949e" stroke-width="1.5"/>
  <text x="182" y="95" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">GET /connect/logout</text>

  <line x1="390" y1="115" x2="475" y2="115" stroke="#3fb950" stroke-width="1.5"/>

  <line x1="310" y1="140" x2="310" y2="180" stroke="#f0883e" stroke-width="1.5" stroke-dasharray="4"/>
  <text x="310" y="195" fill="#f0883e" font-size="10" text-anchor="middle" font-family="sans-serif">302 -&gt; post_logout_redirect_uri?state=...</text>
</svg>

Ending the server session and redirecting back to the client are two separate steps — the redirect only happens after the session is genuinely gone.

## 5. Runnable example

The scenario: enabling the logout endpoint for a client, growing to validate the `post_logout_redirect_uri` against a registered allow-list, and finally to add a confirmation prompt before destroying the session for safety.

### Level 1 — Basic

```java
// LogoutConfig.java
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.core.annotation.Order;
import org.springframework.security.config.annotation.web.builders.HttpSecurity;
import org.springframework.security.oauth2.server.authorization.config.annotation.web.configurers.OAuth2AuthorizationServerConfigurer;
import org.springframework.security.web.SecurityFilterChain;

@Configuration
public class LogoutConfig {

    @Bean
    @Order(1)
    public SecurityFilterChain authorizationServerSecurityFilterChain(HttpSecurity http) throws Exception {
        OAuth2AuthorizationServerConfigurer configurer =
                OAuth2AuthorizationServerConfigurer.authorizationServer();

        http.securityMatcher(configurer.getEndpointsMatcher())
                .with(configurer, authorizationServer -> authorizationServer.oidc(oidc -> {})); // enables /connect/logout

        return http.build();
    }
}
```

**How to run:** add to a Boot project, authenticate a user, then navigate the browser to `http://localhost:8080/connect/logout?id_token_hint=<id_token>&post_logout_redirect_uri=https://task-tracker.example.com/logged-out&state=abc789`. Expected behavior: the server session is destroyed and the browser is redirected to the given URI.

### Level 2 — Intermediate

An open `post_logout_redirect_uri` is an open redirect vulnerability — anyone crafting a logout link could redirect a just-logged-out user anywhere. Production validates it against URIs the client actually registered.

```java
import org.springframework.security.oauth2.server.authorization.client.RegisteredClient;
import org.springframework.security.oauth2.server.authorization.client.RegisteredClientRepository;

public class PostLogoutUriValidator {

    private final RegisteredClientRepository clientRepository;

    public PostLogoutUriValidator(RegisteredClientRepository clientRepository) {
        this.clientRepository = clientRepository;
    }

    public boolean isAllowed(String clientId, String postLogoutRedirectUri) {
        RegisteredClient client = clientRepository.findByClientId(clientId);
        if (client == null) {
            return false;
        }
        return client.getPostLogoutRedirectUris().contains(postLogoutRedirectUri);
    }
}
```

**How to run:** the library performs this exact check internally once `postLogoutRedirectUris` are set on the `RegisteredClient` (via `RegisteredClient.builder().postLogoutRedirectUri(...)`, card 0010) — this class demonstrates the logic being applied. Register `https://task-tracker.example.com/logged-out` on the client, then retry the Level 1 request with an unregistered URI like `https://evil.example.com`. Expected behavior: the session still ends (the ID token hint alone is enough to identify and end it), but the browser is *not* redirected to the unregistered URI — the library instead shows a simple logout confirmation page.

What changed: unregistered redirect targets are silently ignored rather than trusted, closing the open-redirect surface while still honoring the logout itself.

### Level 3 — Advanced

Production also guards against CSRF-style forced logouts — a malicious page embedding `<img src="https://auth.example.com/connect/logout?...">` shouldn't be able to silently log a user out without their knowledge, so a confirmation step (or at minimum, requiring `id_token_hint` to match the current session) is enforced before destroying state.

```java
import jakarta.servlet.http.HttpServletRequest;
import jakarta.servlet.http.HttpSession;

public class LogoutSessionGuard {

    public boolean matchesCurrentSession(HttpServletRequest request, String idTokenHintSubject) {
        HttpSession session = request.getSession(false);
        if (session == null) {
            return false; // nothing to log out of; treat as already logged out
        }
        Object currentSubject = session.getAttribute("authenticated_subject");
        return idTokenHintSubject != null && idTokenHintSubject.equals(currentSubject);
    }
}
```

**How to run:** wire this guard to run before `OidcLogoutEndpointFilter` invalidates the session — if the `id_token_hint`'s subject doesn't match the browser's actual current session, treat the request as already-logged-out rather than blindly invalidating whatever session cookie the browser happens to present. Test by sending a logout request with an `id_token_hint` for a different user than the one currently logged into the browser: expect the guard to reject the invalidation attempt rather than tearing down an unrelated session.

What changed and why it's production-flavored: this closes a subtle trust gap — an `id_token_hint` alone identifies *which* session the caller claims to be ending, but the library still needs the caller's browser to actually be carrying that session's cookie for the action to be legitimate.

## 6. Walkthrough

Tracing a complete logout request, in execution order:

1. The client renders a "Log out" link or button pointing at `GET /connect/logout?id_token_hint=<id_token>&post_logout_redirect_uri=https://task-tracker.example.com/logged-out&state=abc789`, using the ID token it received at login time (card 0027) as the hint.
2. The browser navigates there, carrying its existing session cookie for the authorization server.
3. `OidcLogoutEndpointFilter` parses and validates the `id_token_hint` — decoding and verifying its signature — to determine which client and which subject requested the logout.
4. The filter checks (Level 3) that the hinted subject matches the browser's actual current session before proceeding, preventing a forged logout link from tearing down an unrelated user's session.
5. It looks up the `client_id` embedded in the `id_token_hint` and validates `post_logout_redirect_uri` against that client's registered `postLogoutRedirectUris` (Level 2) — an unregistered URI is dropped, not followed.
6. Assuming validation passes, the filter invalidates the authorization server's session (typically via `SecurityContextLogoutHandler` and `HttpSessionInvalidator` under the hood) — any silent re-authentication the authorization endpoint (card 0026) would otherwise perform now requires a fresh login.
7. The filter responds `302 Found` with `Location: https://task-tracker.example.com/logged-out?state=abc789`, letting the client show its own "you're logged out" confirmation.

```
GET /connect/logout?id_token_hint=...&post_logout_redirect_uri=...&state=abc789
   |
validate id_token_hint signature --fail--> error, no session change
   |  pass
session guard: hint subject == current session? --no--> treat as already logged out
   |  yes
validate post_logout_redirect_uri against client's registered list --unregistered--> confirmation page, no redirect
   |  registered
invalidate server session
   |
302 Found -> Location: <post_logout_redirect_uri>?state=abc789
```

Concrete request and response:

```
GET /connect/logout?id_token_hint=eyJhbGciOiJSUzI1NiJ9...&post_logout_redirect_uri=https%3A%2F%2Ftask-tracker.example.com%2Flogged-out&state=abc789 HTTP/1.1
Cookie: JSESSIONID=9F8E7D6C5B4A

HTTP/1.1 302 Found
Location: https://task-tracker.example.com/logged-out?state=abc789
Set-Cookie: JSESSIONID=; Max-Age=0
```

## 7. Gotchas & takeaways

> A logout endpoint that redirects to *any* URI supplied in the query string, without checking it against the client's registered `postLogoutRedirectUris`, is an open redirect — the exact same class of vulnerability as an unvalidated `redirect_uri` on the authorization endpoint (card 0014), just triggered at the end of the session instead of the start.

- Logging out of a client locally (clearing its cookie) is not the same as ending the authorization server session — genuine logout requires redirecting the browser to this endpoint, not just clearing client-side state.
- `id_token_hint` should be the *ID* token, not the access token — passing an access token here will fail validation, since the endpoint expects the ID token's specific claim structure (`iss`, `aud` matching the client, etc.).
- `post_logout_redirect_uri` must exactly match one of the client's registered URIs — there's no wildcard matching, same as `redirect_uri` on the authorization endpoint (card 0014).
- If `post_logout_redirect_uri` is omitted or doesn't validate, the library shows a bare logout-confirmation page instead of erroring outright — don't mistake that for a broken logout; the session was still ended.
- Single sign-out across multiple simultaneously-open clients (notifying every other client's backend that the user logged out) requires additional infrastructure beyond this endpoint (e.g. back-channel logout) — RP-Initiated Logout alone only guarantees the *authorization server's* session ends, not that every open client tab immediately reflects it.

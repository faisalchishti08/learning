---
card: spring-authorization-server
gi: 42
slug: customizing-form-login-federated-identity
title: "Customizing form login / federated identity"
---

## 1. What it is

The authorization server's login page is ordinary Spring Security — the same `formLogin()` and OAuth2 login client configuration used in any Spring Security app — applied to the *second* `SecurityFilterChain` bean (the one that isn't matched to `/oauth2/**`, `/connect/**`). "Federated identity" here means letting users authenticate at this server by signing in through an external identity provider (Google, GitHub, a corporate Okta tenant) instead of typing a local username and password.

## 2. Why & when

Everything covered in cards 0007 and 0026 assumes *some* authentication mechanism exists to satisfy the "is the user logged in?" check before issuing an authorization code — but Spring Authorization Server itself has no opinion on how that login happens. That's deliberate separation of concerns: the authorization server issues OAuth2/OIDC tokens, and ordinary Spring Security handles authenticating the human. This card is about actually building that login experience — custom branding, or delegating entirely to an upstream identity provider.

Reach for this customization when:

- Replacing the default (functional but unstyled) login form with a branded page matching the product's design.
- Building an authorization server that acts as a *broker* — users authenticate via Google or a corporate SSO, and this server subsequently issues its own tokens to downstream clients (a common pattern for "sign in with your company account" across a suite of internal apps).
- Debugging "the login page looks wrong" or "I want Google as a login option" — both live entirely in the non-`/oauth2/**` `SecurityFilterChain`, not in `OAuth2AuthorizationServerConfigurer` itself.

## 3. Core concept

Think of the authorization server as a large office building with two separate systems: the OAuth2/OIDC protocol machinery (card 0007) is the building's automated badge-access turnstiles — precise, protocol-driven, not customizable in how they check a badge. The lobby staff who verify your identity *before* handing you that badge, though, is a completely separate desk — and that desk can be run however the building wants: an in-house receptionist checking ID (local form login), or a policy of "if you already work at Partner Corp, just show your Partner Corp badge and we'll trust it" (federated login via OAuth2 client / SAML). Card 0007 built the turnstiles; this card is about staffing and running the front desk.

```
SecurityFilterChain #1 (@Order 1): matches /oauth2/**, /connect/**  <- protocol endpoints (cards 0007, 0026-0041)
SecurityFilterChain #2 (@Order 2): matches everything else          <- THIS card: login page, federated identity
```

## 4. Diagram

<svg viewBox="0 0 680 260" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Unauthenticated user hits authorization endpoint, is redirected to the second filter chain's login page, which may itself federate to an external identity provider">
  <rect x="20" y="20" width="160" height="46" rx="8" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="100" y="48" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">/oauth2/authorize</text>

  <rect x="260" y="20" width="160" height="46" rx="8" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="340" y="42" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">not authenticated</text>
  <text x="340" y="56" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">-&gt; redirect /login</text>

  <line x1="180" y1="43" x2="255" y2="43" stroke="#8b949e" stroke-width="1.5"/>

  <rect x="500" y="20" width="160" height="46" rx="8" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="580" y="48" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">Chain #2 login page</text>

  <line x1="420" y1="43" x2="495" y2="43" stroke="#8b949e" stroke-width="1.5"/>

  <rect x="380" y="140" width="150" height="50" rx="8" fill="#1c2430" stroke="#f0883e" stroke-width="1.5"/>
  <text x="455" y="163" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">"Sign in with</text>
  <text x="455" y="178" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">Google" button</text>

  <line x1="580" y1="66" x2="455" y2="135" stroke="#f0883e" stroke-width="1.5"/>

  <rect x="380" y="220" width="150" height="30" rx="6" fill="#1c2430" stroke="#8b949e" stroke-width="1.5"/>
  <text x="455" y="240" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">Google OIDC login</text>
  <line x1="455" y1="190" x2="455" y2="215" stroke="#f0883e" stroke-width="1.5"/>
</svg>

Once federated login completes, control returns to the original `/oauth2/authorize` request, which now sees an authenticated session and proceeds normally.

## 5. Runnable example

The scenario: building a form-login page for the authorization server, growing to add "Sign in with Google" as a federated option, and finally to map the federated identity's claims onto the server's own internal user representation.

### Level 1 — Basic

```java
// LoginConfig.java
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.core.annotation.Order;
import org.springframework.security.config.annotation.web.builders.HttpSecurity;
import org.springframework.security.web.SecurityFilterChain;

import static org.springframework.security.config.Customizer.withDefaults;

@Configuration
public class LoginConfig {

    @Bean
    @Order(2)
    public SecurityFilterChain defaultSecurityFilterChain(HttpSecurity http) throws Exception {
        http.authorizeHttpRequests(authorize -> authorize.anyRequest().authenticated())
                .formLogin(form -> form.loginPage("/login")); // custom branded template

        return http.build();
    }
}
```

**How to run:** add this alongside the authorization-server filter chain (card 0007) in the same Boot app, plus a `/login` controller returning a custom Thymeleaf template. Visit `http://localhost:8080/oauth2/authorize?...`: expect a redirect to the custom `/login` page instead of Spring Security's default generated form.

### Level 2 — Intermediate

Adding federated login means registering an OAuth2 client for the external identity provider and enabling `oauth2Login()` alongside (or instead of) `formLogin()`.

```java
import org.springframework.security.config.annotation.web.builders.HttpSecurity;
import org.springframework.security.web.SecurityFilterChain;

public class LoginConfig {

    public SecurityFilterChain configure(HttpSecurity http) throws Exception {
        http.authorizeHttpRequests(authorize -> authorize.anyRequest().authenticated())
                .formLogin(form -> form.loginPage("/login"))
                .oauth2Login(oauth2 -> oauth2.loginPage("/login")); // same page offers both options

        return http.build();
    }
}
```

```properties
# application.properties
spring.security.oauth2.client.registration.google.client-id=<google-client-id>
spring.security.oauth2.client.registration.google.client-secret=<google-client-secret>
spring.security.oauth2.client.registration.google.scope=openid,profile,email
```

**How to run:** with the Google client registration configured, the `/login` template adds a "Sign in with Google" link pointing at `/oauth2/authorization/google` (the standard Spring Security OAuth2 client login-initiation path). Clicking it redirects to Google, and on return the user lands back at the original `/oauth2/authorize` request, now authenticated.

What changed: the authorization server now supports two independent ways to establish the "is this user logged in" fact — a local password and delegated Google login — both converging on the same authenticated session the OAuth2/OIDC protocol layer (chain #1) checks.

### Level 3 — Advanced

Production needs to reconcile the federated identity with this server's own concept of a user — Google's `sub` claim isn't this server's user ID, so a custom `OAuth2UserService` maps the federated profile onto (or provisions) a local account, ensuring downstream tokens carry *this server's* stable identifiers, not Google's.

```java
import org.springframework.security.oauth2.client.userinfo.DefaultOAuth2UserService;
import org.springframework.security.oauth2.client.userinfo.OAuth2UserRequest;
import org.springframework.security.oauth2.core.OAuth2AuthenticationException;
import org.springframework.security.oauth2.core.user.DefaultOAuth2User;
import org.springframework.security.oauth2.core.user.OAuth2User;

import java.util.Map;
import java.util.Set;

public class FederatedUserProvisioningService extends DefaultOAuth2UserService {

    // In production, inject a real UserRepository instead of this in-memory stub.
    private final Map<String, String> googleSubToLocalUserId = new java.util.concurrent.ConcurrentHashMap<>();

    @Override
    public OAuth2User loadUser(OAuth2UserRequest userRequest) throws OAuth2AuthenticationException {
        OAuth2User googleUser = super.loadUser(userRequest);
        String googleSub = googleUser.getAttribute("sub");
        String email = googleUser.getAttribute("email");

        String localUserId = googleSubToLocalUserId.computeIfAbsent(googleSub,
                sub -> provisionLocalAccount(sub, email));

        Map<String, Object> attributes = new java.util.HashMap<>(googleUser.getAttributes());
        attributes.put("local_user_id", localUserId); // this is what downstream tokens should use as sub

        return new DefaultOAuth2User(Set.of(() -> "ROLE_USER"), attributes, "local_user_id");
    }

    private String provisionLocalAccount(String googleSub, String email) {
        // Real implementation: look up by email, create a new local user row if none exists,
        // return this server's own stable, internal user identifier.
        return "local-" + googleSub.hashCode();
    }
}
```

**How to run:** register this as the `userInfoEndpoint().userService(...)` customizer on `oauth2Login()`. Log in with a Google account not previously seen by this server: expect a new local account to be provisioned transparently on first login, and the resulting authenticated principal's name to be the *local* user ID, not Google's raw `sub`. Log in again with the same Google account: expect the same local user ID to be reused, not a duplicate account.

What changed and why it's production-flavored: tokens this authorization server subsequently issues (card 0027) now carry a stable identifier this system controls and can look up in its own database, rather than being permanently tied to an external provider's identifier — important if the system ever needs to support additional identity providers for the same underlying user, or if Google login is later disabled.

## 6. Walkthrough

Tracing a full federated login attempt inside an authorization-code flow, in execution order:

1. A client redirects the browser to `GET /oauth2/authorize?...` (card 0026).
2. Chain #1's `OAuth2AuthorizationEndpointFilter` checks authentication and finds none, triggering Spring Security's standard entry point, which redirects to `/login` (chain #2, this card).
3. The `/login` page (Level 1's custom template) offers both a local username/password form and a "Sign in with Google" link.
4. The user clicks Google; the browser is redirected to `/oauth2/authorization/google`, which Spring Security's OAuth2 client support turns into a redirect to Google's own consent screen.
5. The user authenticates with Google and approves; Google redirects back to this server's registered callback (`/login/oauth2/code/google`).
6. Spring Security's OAuth2 client machinery exchanges Google's code for Google's tokens, then calls the configured `userInfoEndpoint().userService(...)` — Level 3's `FederatedUserProvisioningService` — to load (and, if needed, provision) the corresponding local account.
7. A local `Authentication` is established in the session, now backed by `local_user_id`, not Google's `sub`.
8. The browser is redirected back to the *original* `/oauth2/authorize?...` request (Spring Security remembers where the flow was interrupted); this time chain #1 sees an authenticated session and proceeds straight to consent (card 0026) and code issuance.

```
GET /oauth2/authorize?...
   |  not authenticated
redirect /login (chain #2)
   |
user clicks "Sign in with Google"
   |
redirect to Google -> user approves -> redirect back to /login/oauth2/code/google
   |
FederatedUserProvisioningService.loadUser(...) -> resolve/create local_user_id
   |
session authenticated as local_user_id
   |
redirect back to original /oauth2/authorize?...  (chain #1, now authenticated)
   |
consent (card 0026) -> code issued
```

## 7. Gotchas & takeaways

> Enabling `oauth2Login()` on chain #2 configures how *users* authenticate to this server — it is a completely separate concept from this server's own clients authenticating to it as an OAuth2/OIDC provider (chain #1). Mixing these up (e.g. trying to put `oauth2Login()` configuration inside `OAuth2AuthorizationServerConfigurer`) doesn't work, because they're deliberately different filter chains with different responsibilities.

- Always map the federated identity to a stable local identifier (Level 3) before issuing tokens — using an external provider's raw `sub` directly as this server's `sub` claim couples the system permanently to that one provider and complicates ever adding a second identity source for the same user.
- A custom `/login` page must be reachable *without* authentication — forgetting to permit it in `authorizeHttpRequests` creates a redirect loop (unauthenticated request to `/oauth2/authorize` redirects to `/login`, which itself requires authentication, redirecting back to `/login`...).
- Federated login introduces a dependency on the external provider's uptime — if Google is down, any user who only ever signed in via Google is locked out of the authorization server entirely; consider whether a local fallback method should always remain available for critical systems.
- The two-filter-chain separation (protocol endpoints vs. everything else, card 0007) is what makes this customization possible without touching OAuth2/OIDC endpoint behavior at all — resist the temptation to special-case authentication logic inside chain #1.
- When debugging "login works standalone but breaks inside the OAuth2 flow," check that the post-login redirect correctly returns to the original `/oauth2/authorize?...` URL with all its original parameters intact — a login flow that redirects to a fixed home page instead loses the pending authorization request.

---
card: spring-authorization-server
gi: 49
slug: integration-with-social-login-as-identity-provider
title: "Integration with social login as identity provider"
---

## 1. What it is

This is the "identity broker" pattern in full: Spring Authorization Server sits in the middle, delegating actual user authentication to one or more external social identity providers (Google, GitHub, Microsoft) via ordinary Spring Security `oauth2Login()` (card 0042 introduced the mechanics), while still acting as a fully independent OAuth2/OIDC provider to its own downstream clients. The server's own clients never talk to Google directly — they only ever talk to this server, which handles the federation itself.

## 2. Why & when

An organization with many internal applications doesn't want each one independently implementing "Sign in with Google" — that means N separate Google OAuth2 client registrations, N separate places to update if Google changes something, and no single place to enforce policy (like "only accounts from our corporate Google Workspace domain may sign in"). Brokering through one authorization server solves this: internal apps register as clients of *this* server using the standard authorization code flow (card 0038) they'd use for any OAuth2 provider, and this server is the only thing that ever needs to know about Google specifically.

Reach for this pattern when:

- Standardizing "login with X" across many internal applications so they share one federation configuration instead of duplicating it.
- Enforcing organization-wide login policy (domain restrictions, MFA requirements, session timeout rules) in one place rather than per-application.
- Deciding whether brokering is worth the extra hop — for a single application with a single social login need, direct `oauth2Login()` in that one app (skipping this server) is simpler; brokering earns its complexity once multiple internal clients need the same federated identity.

## 3. Core concept

Think of this server as an embassy issuing its own national visas, while accepting several *other* countries' passports as valid proof of identity for the visa application. A traveler (a user) doesn't need a passport from this specific country — they can show up with a Google passport or a GitHub passport, and as long as it's from an accepted country (a configured federated provider), the embassy (this authorization server) verifies it and issues its *own* visa (an access token from this server) that's what the traveler actually uses at their final destination (the downstream internal application). The destination never sees or cares which foreign passport was originally used — only the embassy's own visa matters to them.

```
Internal App --(standard OAuth2 authorization code, card 0038)--> This Authorization Server
                                                                          |
                                                          (broker: delegates login to Google/GitHub)
                                                                          |
This Authorization Server <--(Google/GitHub OAuth2 client login)--> Google / GitHub
```

## 4. Diagram

<svg viewBox="0 0 700 260" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Internal app talks only to the broker authorization server, which itself federates login to external identity providers">
  <rect x="20" y="90" width="140" height="60" rx="8" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="90" y="115" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">Internal App</text>
  <text x="90" y="132" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">(a client of this server)</text>

  <rect x="270" y="90" width="180" height="60" rx="8" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="360" y="112" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">This Authorization</text>
  <text x="360" y="128" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">Server (broker)</text>

  <rect x="540" y="30" width="140" height="46" rx="8" fill="#1c2430" stroke="#3fb950" stroke-width="1.5"/>
  <text x="610" y="58" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">Google OIDC</text>

  <rect x="540" y="164" width="140" height="46" rx="8" fill="#1c2430" stroke="#3fb950" stroke-width="1.5"/>
  <text x="610" y="192" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">GitHub OAuth2</text>

  <line x1="160" y1="120" x2="265" y2="120" stroke="#8b949e" stroke-width="1.5"/>
  <text x="212" y="110" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">standard code flow</text>

  <line x1="450" y1="105" x2="535" y2="60" stroke="#3fb950" stroke-width="1.5"/>
  <line x1="450" y1="135" x2="535" y2="185" stroke="#3fb950" stroke-width="1.5"/>
</svg>

The internal app's own client registration and token exchange never change, regardless of which external provider ultimately authenticated the user.

## 5. Runnable example

The scenario: configuring the broker to accept both Google and GitHub as federated identity sources, growing to enforce a corporate domain restriction so only Google accounts from the company's own Workspace domain can complete login, and finally to record which federated provider was used inside the tokens this server issues to its own downstream clients.

### Level 1 — Basic

```java
// BrokerLoginConfig.java
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.core.annotation.Order;
import org.springframework.security.config.annotation.web.builders.HttpSecurity;
import org.springframework.security.web.SecurityFilterChain;

@Configuration
public class BrokerLoginConfig {

    @Bean
    @Order(2) // the non-protocol-endpoints chain, see card 0042
    public SecurityFilterChain defaultSecurityFilterChain(HttpSecurity http) throws Exception {
        http.authorizeHttpRequests(authorize -> authorize.anyRequest().authenticated())
                .oauth2Login(oauth2 -> oauth2.loginPage("/login"));

        return http.build();
    }
}
```

```properties
spring.security.oauth2.client.registration.google.client-id=<google-client-id>
spring.security.oauth2.client.registration.google.client-secret=<google-client-secret>
spring.security.oauth2.client.registration.google.scope=openid,profile,email

spring.security.oauth2.client.registration.github.client-id=<github-client-id>
spring.security.oauth2.client.registration.github.client-secret=<github-client-secret>
```

**How to run:** register an internal app as a `RegisteredClient` of this server (card 0010) with a normal authorization code + PKCE flow (card 0038). Have it redirect the user to this server's `/oauth2/authorize`; expect the `/login` page to offer both "Sign in with Google" and "Sign in with GitHub." Completing either federated login lands the user back at the internal app's callback with a code issued by *this* server, not by Google or GitHub.

### Level 2 — Intermediate

Some organizations only want *their own* Google Workspace accounts to be able to log in via the Google option, rejecting personal Gmail accounts even though they're technically valid Google logins.

```java
import org.springframework.security.oauth2.client.userinfo.DefaultOAuth2UserService;
import org.springframework.security.oauth2.client.userinfo.OAuth2UserRequest;
import org.springframework.security.oauth2.core.OAuth2AuthenticationException;
import org.springframework.security.oauth2.core.OAuth2Error;
import org.springframework.security.oauth2.core.user.OAuth2User;

public class DomainRestrictedGoogleUserService extends DefaultOAuth2UserService {

    private static final String ALLOWED_DOMAIN = "example.com";

    @Override
    public OAuth2User loadUser(OAuth2UserRequest userRequest) throws OAuth2AuthenticationException {
        OAuth2User user = super.loadUser(userRequest);

        boolean isGoogle = "google".equals(userRequest.getClientRegistration().getRegistrationId());
        String hostedDomain = user.getAttribute("hd"); // Google's "hosted domain" claim for Workspace accounts

        if (isGoogle && !ALLOWED_DOMAIN.equals(hostedDomain)) {
            throw new OAuth2AuthenticationException(
                    new OAuth2Error("domain_not_allowed",
                            "Only " + ALLOWED_DOMAIN + " Google Workspace accounts may sign in", null));
        }
        return user;
    }
}
```

**How to run:** register as `userInfoEndpoint().userService(new DomainRestrictedGoogleUserService())` on `oauth2Login()`. Attempt login with a personal `@gmail.com` account: expect rejection with a clear error page. Attempt with an `@example.com` Workspace account: expect normal success.

What changed: the broker now enforces organizational policy centrally — every internal app automatically inherits this domain restriction without needing any awareness of it, since the restriction lives entirely in the broker, not in each downstream client.

### Level 3 — Advanced

Downstream internal apps sometimes need to know which identity provider actually authenticated the user (for audit logging, or to vary behavior for GitHub-authenticated developer accounts versus Google-authenticated general staff) — this is recorded as a custom claim (card 0044) on the tokens this server itself issues, sourced from the OAuth2 client login's `registrationId`.

```java
import org.springframework.security.oauth2.core.OAuth2AuthenticatedPrincipal;
import org.springframework.security.oauth2.server.authorization.token.JwtEncodingContext;
import org.springframework.security.oauth2.server.authorization.token.OAuth2TokenCustomizer;

public class FederatedProviderClaimCustomizer implements OAuth2TokenCustomizer<JwtEncodingContext> {

    @Override
    public void customize(JwtEncodingContext context) {
        Object principal = context.getPrincipal().getPrincipal();
        if (principal instanceof org.springframework.security.oauth2.core.user.OAuth2User oauth2User) {
            String provider = resolveProviderFrom(context);
            context.getClaims().claim("idp", provider); // "google" or "github"
        }
    }

    private String resolveProviderFrom(JwtEncodingContext context) {
        // In a real implementation, this is captured from the OAuth2AuthenticationToken's
        // authorizedClientRegistrationId at the point the session was first established,
        // and threaded through to token issuance via the stored OAuth2Authorization (card 0016).
        return context.getAuthorization() != null
                ? context.getAuthorization().getAttribute("federated_idp")
                : "unknown";
    }
}
```

**How to run:** log in via Google, complete the flow to an internal app, and decode the access token this server issued to that app. Expected output: an `idp` claim with value `google`. Repeat via GitHub: expect `idp: github`. Internal apps can now branch logic (or just log) based on which identity source ultimately vouched for the user, without ever having spoken to Google or GitHub themselves.

What changed and why it's production-flavored: the identity of the *originating* federated provider survives the brokering hop and becomes visible to downstream applications through this server's own tokens — necessary for audit trails ("which login method was used for this session") that would otherwise be lost the moment the broker abstracts the federation away.

## 6. Walkthrough

Tracing a complete brokered login from an internal app's perspective, in execution order:

1. `internal-app` redirects the user to this server's `GET /oauth2/authorize?client_id=internal-app&...` — a completely standard authorization code + PKCE request (card 0038), with no awareness that federation is involved at all.
2. Unauthenticated, the user is redirected to this server's `/login` (card 0042), showing both federated login options (Level 1).
3. The user selects Google; standard `oauth2Login()` machinery redirects to Google, the user authenticates, and Google redirects back to this server.
4. `DomainRestrictedGoogleUserService.loadUser(...)` (Level 2) checks the returned `hd` claim against the allowed domain — a personal account is rejected right here, before any local session is ever established.
5. Assuming the domain check passes, this server establishes its own authenticated session for the user, tagging the stored session/authorization with which provider (`google`) was actually used.
6. Control returns to the original `/oauth2/authorize?...` request; this server now sees an authenticated session and proceeds through consent (card 0026) as normal.
7. The authorization code is issued and exchanged at the token endpoint (card 0027); during token construction, `FederatedProviderClaimCustomizer` (Level 3) adds `idp: google` to the access token.
8. `internal-app` receives its access token — issued by, and only ever communicated with, this server — carrying `idp: google` as durable evidence of which upstream identity source ultimately authenticated this session.

```
internal-app -> GET /oauth2/authorize (standard, card 0038)
   |  not authenticated
/login -> user picks "Sign in with Google"
   |
redirect to Google -> user authenticates -> redirect back
   |
DomainRestrictedGoogleUserService: hd == "example.com"? --no--> reject, no session
   |  yes
establish local session, record federated_idp = "google"
   |
redirect back to original /oauth2/authorize -> consent -> code issued
   |
POST /oauth2/token -> FederatedProviderClaimCustomizer adds idp claim
   |
internal-app receives access_token{..., idp: "google"}
```

## 7. Gotchas & takeaways

> The domain restriction (Level 2) must be enforced inside the broker's own `OAuth2UserService`, not left to each downstream internal app to check independently — if enforcement is left to individual apps, a single app that forgets the check becomes an open door for any Google account, personal or corporate, defeating the entire point of centralizing this policy in the broker.

- Downstream internal apps should never be given direct knowledge of, or credentials for, Google or GitHub — the whole value of brokering is that adding, removing, or reconfiguring a federated provider is a change made in exactly one place (this server), not N places.
- Google and GitHub each expose different claims in different shapes (`hd` for Google Workspace domain, no equivalent concept for GitHub) — any policy logic (Level 2) needs to be provider-aware rather than assuming a uniform claim set across all federated sources.
- Recording which federated provider authenticated a session (Level 3) should happen at the point of *login*, not be re-derived later at token issuance from unreliable signals — thread it through the stored authorization state deliberately, since by the time a token is being built, the original federated login interaction is long over.
- A broker introduces a new single point of failure for login across every internal app it serves — if this server or its connection to Google/GitHub is down, every downstream app relying on it for login is affected simultaneously; weigh this operational concentration against the administrative benefits of centralization.
- When a user reports being unable to log in via a specific provider, check first whether that provider's specific claim-based policy check (Level 2) is the cause before assuming a broader authorization server outage — provider-specific rejections often look identical to generic failures from the end user's point of view but have very different causes.

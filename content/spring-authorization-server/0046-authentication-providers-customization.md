---
card: spring-authorization-server
gi: 46
slug: authentication-providers-customization
title: "Authentication providers customization"
---

## 1. What it is

Every protocol endpoint in Spring Authorization Server (authorize, token, introspection, revocation, and so on) is backed internally by one or more `AuthenticationProvider` implementations that do the actual validation work. Customizing them means either replacing the library's default provider for a given step with a custom implementation, or wrapping it to add behavior before/after — done via the various `...AuthenticationProvider` or `...Customizer` hooks each endpoint configurer exposes.

## 2. Why & when

The previous card (0045) covered adding an entirely *new* grant type from scratch. This card is about the more common case: an existing, standard grant type mostly does what's needed, but one specific validation rule needs to change or be added — extra checks before a code is exchanged, additional audit logging around client authentication, or replacing exactly how a `RegisteredClient`'s secret gets compared. Reaching for a full custom grant type (card 0045) for this kind of narrower need is overkill; customizing the existing provider is the right-sized tool.

Reach for authentication provider customization when:

- Adding an extra validation rule to a standard flow — e.g. rejecting authorization code exchanges from an unexpected IP range, or requiring an additional header on client authentication.
- Needing detailed audit logging or metrics around a specific authentication step (every client authentication attempt, every code exchange) without touching the underlying protocol logic.
- Deciding between this and card 0045's approach — if the `grant_type` value itself and the wire format of the request are unchanged, customize the existing provider; only build an entirely new grant type when the request shape itself is genuinely new.

## 3. Core concept

Think of each protocol endpoint's default `AuthenticationProvider` as a factory's standard quality-control inspector, following a fixed checklist. Customizing it is like adding an extra inspection step to that same checklist — say, an additional barcode scan before an item passes — without replacing the entire inspection line. The new inspector still does everything the standard one did (all the OAuth2 spec-required checks), it just also does one more thing the standard checklist doesn't cover, specific to this particular factory's own requirements.

```java
public class AuditingClientAuthenticationProvider implements AuthenticationProvider {
    private final AuthenticationProvider delegate; // the library's standard provider

    public Authentication authenticate(Authentication authentication) {
        Authentication result = delegate.authenticate(authentication); // do everything standard first
        auditLog(result); // then add the extra behavior
        return result;
    }
    // ...
}
```

## 4. Diagram

<svg viewBox="0 0 640 220" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="A decorator wraps the standard provider, delegating to it and adding extra behavior before or after">
  <rect x="20" y="80" width="150" height="60" rx="8" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="95" y="105" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">Incoming</text>
  <text x="95" y="120" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">Authentication</text>

  <rect x="230" y="60" width="200" height="100" rx="10" fill="#1c2430" stroke="#f0883e" stroke-width="1.5"/>
  <text x="330" y="80" fill="#f0883e" font-size="10" text-anchor="middle" font-family="sans-serif">Custom decorator</text>
  <rect x="250" y="95" width="160" height="45" rx="6" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="330" y="115" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">delegate.authenticate(...)</text>
  <text x="330" y="128" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">(standard library logic)</text>

  <rect x="480" y="80" width="140" height="60" rx="8" fill="#1c2430" stroke="#3fb950" stroke-width="1.5"/>
  <text x="550" y="105" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">Result + extra</text>
  <text x="550" y="120" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">behavior applied</text>

  <line x1="170" y1="110" x2="225" y2="110" stroke="#8b949e" stroke-width="1.5"/>
  <line x1="430" y1="110" x2="475" y2="110" stroke="#3fb950" stroke-width="1.5"/>
</svg>

The decorator pattern keeps 100% of the spec-mandated logic intact while layering in exactly the additional behavior needed.

## 5. Runnable example

The scenario: adding audit logging around client authentication, growing to add a custom IP allow-list check for a specific high-privilege client, and finally to make the customization fail closed (deny by default) if the extra check itself errors, rather than silently allowing through.

### Level 1 — Basic

```java
// AuditingAuthenticationProvider.java
import org.springframework.security.authentication.AuthenticationProvider;
import org.springframework.security.core.Authentication;
import org.springframework.security.core.AuthenticationException;

import java.time.Instant;

public class AuditingAuthenticationProvider implements AuthenticationProvider {

    private final AuthenticationProvider delegate;

    public AuditingAuthenticationProvider(AuthenticationProvider delegate) {
        this.delegate = delegate;
    }

    @Override
    public Authentication authenticate(Authentication authentication) throws AuthenticationException {
        try {
            Authentication result = delegate.authenticate(authentication);
            System.out.printf("[%s] client authentication SUCCESS: %s%n", Instant.now(), result.getName());
            return result;
        } catch (AuthenticationException e) {
            System.out.printf("[%s] client authentication FAILURE: %s%n", Instant.now(), e.getMessage());
            throw e;
        }
    }

    @Override
    public boolean supports(Class<?> authentication) {
        return delegate.supports(authentication);
    }
}
```

**How to run:** wrap the library's default client authentication provider by registering this decorator via `.clientAuthentication(clientAuth -> clientAuth.authenticationProviders(providers -> providers.replaceAll(AuditingAuthenticationProvider::new)))`, then attempt both a valid and an invalid client authentication. Expected console output: one `SUCCESS` line per valid attempt, one `FAILURE` line (with the underlying error) per invalid attempt.

### Level 2 — Intermediate

A specific high-privilege client (say, an internal admin tool) should only ever authenticate from known internal IP ranges — this check is orthogonal to the standard secret comparison, so it's added as an extra condition inside the same decorator.

```java
import org.springframework.security.authentication.AuthenticationProvider;
import org.springframework.security.core.Authentication;
import org.springframework.security.core.AuthenticationException;
import org.springframework.security.oauth2.core.OAuth2AuthenticationException;
import org.springframework.security.oauth2.core.OAuth2Error;
import org.springframework.security.oauth2.core.OAuth2ErrorCodes;
import org.springframework.security.oauth2.server.authorization.authentication.OAuth2ClientAuthenticationToken;

import java.util.Set;

public class IpRestrictedAuthenticationProvider implements AuthenticationProvider {

    private static final Set<String> RESTRICTED_CLIENT_IDS = Set.of("admin-tool");
    private static final Set<String> ALLOWED_IP_PREFIXES = Set.of("10.0.", "192.168.1.");

    private final AuthenticationProvider delegate;
    private final java.util.function.Supplier<String> currentRequestIp;

    public IpRestrictedAuthenticationProvider(AuthenticationProvider delegate,
            java.util.function.Supplier<String> currentRequestIp) {
        this.delegate = delegate;
        this.currentRequestIp = currentRequestIp;
    }

    @Override
    public Authentication authenticate(Authentication authentication) throws AuthenticationException {
        if (authentication instanceof OAuth2ClientAuthenticationToken clientAuth
                && RESTRICTED_CLIENT_IDS.contains(clientAuth.getPrincipal().toString())) {
            String ip = currentRequestIp.get();
            boolean allowed = ALLOWED_IP_PREFIXES.stream().anyMatch(ip::startsWith);
            if (!allowed) {
                throw new OAuth2AuthenticationException(
                        new OAuth2Error(OAuth2ErrorCodes.UNAUTHORIZED_CLIENT, "Client not permitted from this network", null));
            }
        }
        return delegate.authenticate(authentication);
    }

    @Override
    public boolean supports(Class<?> authentication) {
        return delegate.supports(authentication);
    }
}
```

**How to run:** wrap the standard provider with this decorator, supplying `currentRequestIp` from the current `HttpServletRequest`. Attempt authentication as `admin-tool` from `10.0.5.12` (allowed prefix): expect normal success. Attempt from `203.0.113.9` (not in the allow-list): expect rejection with `unauthorized_client`, even with a completely correct client secret.

What changed: authentication for this one sensitive client now requires *both* correct credentials *and* a trusted network location — a real defense-in-depth measure for a client whose compromise would be especially damaging.

### Level 3 — Advanced

If the IP-lookup logic itself fails (a misconfigured `currentRequestIp` supplier, an unexpected exception), the decorator must fail closed — reject the authentication — rather than let an internal error accidentally fall through to the delegate and grant access.

```java
import org.springframework.security.authentication.AuthenticationProvider;
import org.springframework.security.core.Authentication;
import org.springframework.security.core.AuthenticationException;
import org.springframework.security.oauth2.core.OAuth2AuthenticationException;
import org.springframework.security.oauth2.core.OAuth2Error;
import org.springframework.security.oauth2.core.OAuth2ErrorCodes;

public class FailClosedIpRestrictedProvider implements AuthenticationProvider {

    private final IpRestrictedAuthenticationProvider delegate;

    public FailClosedIpRestrictedProvider(IpRestrictedAuthenticationProvider delegate) {
        this.delegate = delegate;
    }

    @Override
    public Authentication authenticate(Authentication authentication) throws AuthenticationException {
        try {
            return delegate.authenticate(authentication);
        } catch (OAuth2AuthenticationException e) {
            throw e; // a genuine, expected rejection — pass it through as-is
        } catch (RuntimeException unexpected) {
            // Any *other* failure (NPE, IP lookup blew up, etc.) must still deny access,
            // never silently succeed just because the extra check itself broke.
            throw new OAuth2AuthenticationException(
                    new OAuth2Error(OAuth2ErrorCodes.SERVER_ERROR, "Authentication check failed unexpectedly", null),
                    unexpected);
        }
    }

    @Override
    public boolean supports(Class<?> authentication) {
        return delegate.supports(authentication);
    }
}
```

**How to run:** simulate `currentRequestIp` throwing (e.g. the request attribute it reads is unexpectedly absent). Without this wrapper, that exception could propagate in a way that (depending on how the surrounding filter chain handles it) risks unpredictable behavior; with it, expect a clean, deterministic `500`-class `server_error` rejection every time the check itself is broken — never a silent pass-through to the delegate.

What changed and why it's production-flavored: this closes the gap between "the security check said no" and "the security check itself crashed" — both must result in denied access, since a caller shouldn't be able to bypass a restriction merely by triggering a bug in the code that enforces it.

## 6. Walkthrough

Tracing a restricted client's authentication attempt, in execution order:

1. `admin-tool` sends `POST /oauth2/token` with `grant_type=client_credentials` and its client credentials, from IP `203.0.113.9` (outside the allowed ranges).
2. The token endpoint's client authentication filter builds an `OAuth2ClientAuthenticationToken` from the request and passes it to the configured `AuthenticationManager`, which tries each registered provider.
3. `FailClosedIpRestrictedProvider` (Level 3) is reached; it delegates to `IpRestrictedAuthenticationProvider` (Level 2) inside a try/catch.
4. That provider checks whether `admin-tool` is in the IP-restricted set — it is — then checks the current request's IP against the allow-list; `203.0.113.9` doesn't match any prefix.
5. It throws `OAuth2AuthenticationException` with `unauthorized_client` — this is an *expected*, well-formed rejection, so `FailClosedIpRestrictedProvider`'s catch block re-throws it unchanged rather than wrapping it.
6. Because rejection happened before ever reaching the actual secret-comparison delegate, the response reveals nothing about whether the supplied secret was even correct — only that this client isn't permitted from this network.
7. The token endpoint translates the exception into `401 Unauthorized` with the standard OAuth2 error body, and `AuditingAuthenticationProvider` (Level 1, wrapping the whole chain) logs the failure with a timestamp for later review.

```
POST /oauth2/token (client_id=admin-tool, from 203.0.113.9)
   |
FailClosedIpRestrictedProvider.authenticate(...)
   |    try: IpRestrictedAuthenticationProvider.authenticate(...)
   |         is admin-tool? yes -> check IP allow-list -> not allowed
   |         throw OAuth2AuthenticationException(unauthorized_client)
   |    catch OAuth2AuthenticationException -> re-throw as-is (expected rejection)
   |
AuditingAuthenticationProvider logs FAILURE
   |
401 Unauthorized {"error":"unauthorized_client"}
```

## 7. Gotchas & takeaways

> Wrapping (decorating) a provider rather than replacing it outright is almost always the safer approach — replacing the library's default provider entirely means reimplementing every spec-mandated check yourself, and a subtle omission (skipping a timing-safe secret comparison, say) silently reintroduces a vulnerability the library's own implementation already carefully avoided.

- Order matters when multiple decorators wrap the same provider — decide deliberately whether the extra check should run *before* delegating (reject fast, without even attempting secret validation, as shown here) or *after* (only apply the extra check to requests that already passed standard validation) based on what information the extra check needs and what's cheapest to reject early.
- Always fail closed (Level 3) — an exception inside custom validation logic must never be interpreted as "no opinion, allow it" by accident; explicitly catch and convert unexpected errors into a firm rejection.
- Because these providers sit directly in the authentication path for every request of their type, keep them fast and side-effect-light for the common (successful) case — heavy logging or synchronous external calls here add latency to literally every token request.
- Test the failure path as rigorously as the success path — it's easy to verify a correctly configured client authenticates fine and forget to verify that a genuinely malformed or malicious request is actually rejected, not silently passed through by an incompletely wired decorator.
- When several teams need to add their own cross-cutting checks to the same endpoint, prefer composing multiple small, single-purpose decorators over one large provider handling many unrelated concerns — it keeps each check independently testable and easier to reason about in isolation.

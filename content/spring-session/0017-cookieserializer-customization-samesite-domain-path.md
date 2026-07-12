---
card: spring-session
gi: 17
slug: cookieserializer-customization-samesite-domain-path
title: "CookieSerializer customization (SameSite, domain, path)"
---

## 1. What it is

`DefaultCookieSerializer` is the component `CookieHttpSessionIdResolver` (card 0016) delegates to for actually reading and writing the session cookie — controlling its name, domain, path, `SameSite` attribute, `Secure`/`HttpOnly` flags, and max-age. Customizing it is how an application tailors cookie behavior to its specific domain structure and security requirements, beyond Spring Session's sensible defaults.

## 2. Why & when

The default cookie configuration (name `SESSION`, `HttpOnly`, `SameSite=Lax`, no explicit domain, path `/`) works out of the box for a simple single-domain application, but real deployments often need something different: a session cookie shared across multiple subdomains (`app.example.com` and `api.example.com`), a stricter or looser `SameSite` policy depending on whether the app embeds third-party content or is embedded elsewhere, or a specific cookie name to avoid colliding with another cookie already in use.

Reach for `DefaultCookieSerializer` customization when:

- The application spans multiple subdomains that all need to share the same session — this requires explicitly setting the cookie's `domain` attribute, since browsers scope cookies to the exact host by default.
- Embedding the application inside an iframe on a different site, or needing the session cookie sent on cross-site requests for a specific integration — this requires `SameSite=None` (paired with `Secure`, a browser requirement for `SameSite=None` cookies).
- Debugging "the session cookie isn't being sent" on a specific request — often traced back to a `SameSite`, `domain`, or `path` mismatch between where the cookie was set and where it's expected to be sent.

## 3. Core concept

Think of cookie attributes as the address and delivery instructions written on an envelope, not just its contents. The session ID is the letter inside; `domain` is like writing "deliver to any address under this street name" instead of one exact address (letting the cookie reach multiple subdomains); `path` restricts which specific rooms in a building the letter can be delivered to; `SameSite` is an instruction to the postal service about whether to deliver this letter when it's being forwarded on behalf of a *different* sender's request (a cross-site request) or only when the original recipient's own site directly asks for it.

```java
@Bean
public DefaultCookieSerializer cookieSerializer() {
    DefaultCookieSerializer serializer = new DefaultCookieSerializer();
    serializer.setCookieName("APPSESSION");
    serializer.setDomainName(".example.com"); // shared across all subdomains
    serializer.setSameSite("Strict");
    return serializer;
}
```

## 4. Diagram

<svg viewBox="0 0 660 220" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="A cookie set with domain=.example.com is sent by the browser on requests to any subdomain of example.com">
  <rect x="20" y="20" width="200" height="46" rx="8" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="120" y="48" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">Set-Cookie: domain=.example.com</text>

  <rect x="80" y="110" width="150" height="46" rx="8" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="155" y="138" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">app.example.com</text>

  <rect x="260" y="110" width="150" height="46" rx="8" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="335" y="138" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">api.example.com</text>

  <rect x="440" y="110" width="150" height="46" rx="8" fill="#1c2430" stroke="#f0883e" stroke-width="1.5"/>
  <text x="515" y="130" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">evil-example.com</text>
  <text x="515" y="144" fill="#f0883e" font-size="9" text-anchor="middle" font-family="sans-serif">NOT sent here</text>

  <line x1="120" y1="66" x2="155" y2="105" stroke="#3fb950" stroke-width="1.5"/>
  <line x1="120" y1="66" x2="335" y2="105" stroke="#3fb950" stroke-width="1.5"/>
</svg>

Both real subdomains receive the cookie automatically on requests; a similarly-named but unrelated domain never does.

## 5. Runnable example

The scenario: sharing a session cookie across two subdomains of the same application, growing to correctly configure `SameSite=None` for a specific integration that embeds the app in a third-party iframe, and finally to safely roll out a `SameSite` policy change in an existing production application without breaking active user sessions mid-migration.

### Level 1 — Basic

```java
// CrossSubdomainCookieConfig.java
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.session.web.http.DefaultCookieSerializer;

@Configuration
public class CrossSubdomainCookieConfig {

    @Bean
    public DefaultCookieSerializer cookieSerializer() {
        DefaultCookieSerializer serializer = new DefaultCookieSerializer();
        serializer.setDomainName(".example.com"); // leading dot: matches all subdomains
        return serializer;
    }
}
```

**How to run:** deploy this config, log in at `https://app.example.com`, then make a request to `https://api.example.com` with the browser's existing cookies. Expected result: the browser's dev tools show the `SESSION` cookie with `Domain=.example.com`, and the request to `api.example.com` includes it automatically — both subdomains see the same authenticated session.

### Level 2 — Intermediate

An integration that embeds part of the application in an iframe on a completely different site (`partner-site.com`) needs the cookie to be sent even on that cross-site request — which requires `SameSite=None`, and browsers additionally require `Secure` (HTTPS-only) whenever `SameSite=None` is used, or the cookie is rejected outright.

```java
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.session.web.http.DefaultCookieSerializer;

@Configuration
public class IframeEmbedCookieConfig {

    @Bean
    public DefaultCookieSerializer cookieSerializer() {
        DefaultCookieSerializer serializer = new DefaultCookieSerializer();
        serializer.setSameSite("None");
        serializer.setUseSecureCookie(true); // required by browsers whenever SameSite=None is used
        serializer.setCookiePath("/embed/"); // scope the cookie only to the embeddable widget's paths
        return serializer;
    }
}
```

**How to run:** serve the `/embed/widget` page inside an iframe on a test page hosted at a different origin (`https://partner-site.com`), over HTTPS. Expected behavior: the embedded widget's session persists correctly across reloads within the iframe — verify by checking that `Set-Cookie` includes both `SameSite=None` and `Secure`; without `Secure`, most modern browsers silently reject the cookie entirely, and the embedded widget would appear to lose its session on every single request.

What changed: the application now supports being embedded cross-site, a capability `SameSite=Lax` (the default) specifically prevents — but scoped narrowly (via `cookiePath`) to only the embeddable widget's routes, so the rest of the application retains the stricter default `SameSite` protection against CSRF-style attacks that `SameSite=None` would otherwise weaken application-wide.

### Level 3 — Advanced

Changing `SameSite` policy on an already-live application with active user sessions needs care — users with cookies set under the *old* policy don't automatically get the new policy's protections until they receive a fresh `Set-Cookie` response, so a rollout plan needs to account for that transition window rather than assuming the change takes effect for everyone instantly.

```java
import jakarta.servlet.http.HttpServletRequest;
import jakarta.servlet.http.HttpServletResponse;
import org.springframework.session.web.http.CookieHttpSessionIdResolver;
import org.springframework.session.web.http.DefaultCookieSerializer;

public class MigrationAwareCookieResolver extends CookieHttpSessionIdResolver {

    public MigrationAwareCookieResolver() {
        DefaultCookieSerializer serializer = new DefaultCookieSerializer();
        serializer.setSameSite("Strict"); // the new, target policy
        setCookieSerializer(serializer);
    }

    @Override
    public void setSessionId(HttpServletRequest request, HttpServletResponse response, String sessionId) {
        // Every response that touches the session re-issues Set-Cookie with the new policy,
        // so active users are migrated to the stricter SameSite value the next time
        // their session is touched — not instantly for everyone, but within one request cycle
        // of continued activity, without forcing every user to explicitly log in again.
        super.setSessionId(request, response, sessionId);
    }
}
```

**How to run:** deploy this alongside monitoring on authentication failure rates and support tickets mentioning unexpected logouts. Simulate a user with an old-policy cookie (manually set `SameSite=Lax` via browser dev tools) making a request: expect the response to include a freshly issued `Set-Cookie` with `SameSite=Strict`, updating their browser's stored cookie for all future requests without interrupting their currently active session.

What changed and why it's production-flavored: `SameSite` policy changes are a real, occasionally necessary security hardening step (tightening CSRF protection), and rolling them out against an already-live user base with existing sessions requires understanding that the new policy only takes effect cookie-by-cookie, as each session is naturally re-touched — a detail easy to overlook and one that can cause confusing, gradually-resolving symptoms if not anticipated.

## 6. Walkthrough

Tracing a cross-subdomain cookie flow end-to-end, in execution order:

1. A user logs in at `https://app.example.com`; the response includes `Set-Cookie: SESSION=abc123; Domain=.example.com; Path=/; HttpOnly; SameSite=Lax` (or `Strict`, per whatever policy is configured).
2. The browser stores this cookie, scoped to the `.example.com` domain (the leading dot explicitly opts into subdomain matching) rather than the exact host `app.example.com` alone.
3. The same page makes a fetch request to `https://api.example.com/data` — a different subdomain, but still within the `.example.com` domain the cookie was scoped to.
4. Because the request is same-site (both `app.example.com` and `api.example.com` share the registrable domain `example.com`) and the cookie's `Domain` attribute explicitly covers this subdomain, the browser automatically attaches `Cookie: SESSION=abc123` to this cross-subdomain request — no client-side code needed to make this happen.
5. `api.example.com`'s own instance of the application (sharing the same session store, per card 0001's clustering) resolves `abc123` against the shared store and finds the exact same session `app.example.com` created — the user is recognized as already authenticated on the API subdomain, with zero additional login step.
6. Had the cookie's `Domain` been left unset (the default, scoping it strictly to `app.example.com` alone), step 4 would have failed to attach any cookie at all, and `api.example.com` would have seen this as a fresh, unauthenticated request — this is precisely the failure mode `setDomainName(".example.com")` (Level 1) exists to prevent.

```
Login at app.example.com -> Set-Cookie: SESSION=abc123; Domain=.example.com
   |
browser stores cookie, scoped to .example.com (all subdomains)
   |
request to api.example.com/data (same registrable domain)
   |
browser automatically attaches Cookie: SESSION=abc123  (domain match)
   |
api.example.com resolves abc123 against SHARED session store -> same session found
```

## 7. Gotchas & takeaways

> `SameSite=None` cookies are rejected outright by modern browsers unless also marked `Secure` — an application deployed without HTTPS (common in some internal or development environments) that tries to set `SameSite=None` for a cross-site embedding use case will find the cookie simply never gets set at all, with no obvious error surfaced to the application itself; always pair `SameSite=None` with `Secure(true)` and serve over HTTPS.

- A cookie's `Domain` attribute with a leading dot (`.example.com`) matches all subdomains; omitting it (or setting it to the exact host) scopes the cookie strictly to that one host — choose deliberately based on whether cross-subdomain sharing is actually needed, since broader scoping also broadly increases which subdomains could potentially read or be affected by that cookie if any one of them were compromised.
- `cookiePath` narrows which URL paths the cookie is sent on — using this to scope a special-purpose cookie (Level 2's embeddable widget) to only its relevant routes limits the surface area affected by that specific configuration, rather than applying a looser `SameSite` policy application-wide.
- `SameSite` policy changes on a live application affect only cookies issued *after* the change — existing sessions continue operating under whatever policy was in effect when their cookie was last (re-)set, until a subsequent request naturally refreshes it (Level 3); plan rollouts with this gradual transition in mind, not as an instantaneous cutover.
- Always verify cookie behavior directly in browser developer tools (the Application/Storage tab, inspecting actual `Set-Cookie` response headers and stored cookie attributes) rather than assuming configuration took effect — a surprising number of cookie-configuration issues are only obvious once actually inspecting what the browser received and stored.
- `HttpOnly` (preventing JavaScript access to the cookie) should almost always remain enabled for session cookies specifically — it's Spring Session's default and a meaningful XSS mitigation; there's rarely a legitimate reason to disable it for a session-identifying cookie specifically, even when customizing other attributes.

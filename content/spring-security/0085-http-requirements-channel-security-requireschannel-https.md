---
card: spring-security
gi: 85
slug: http-requirements-channel-security-requireschannel-https
title: "HTTP requirements / channel security (requiresChannel HTTPS)"
---

## 1. What it is

**Channel security** is Spring Security's mechanism for enforcing *which transport a request must arrive over* — plain HTTP or encrypted HTTPS — before any authentication or authorization decision is even considered. The `requiresChannel()` DSL method configures it: you pair a request matcher with a channel requirement (`requiresSecure()` for HTTPS-only, or `requiresInsecure()` to explicitly allow plain HTTP), and a `ChannelProcessingFilter` running early in the filter chain inspects every incoming request against those rules. When a request arrives on the wrong channel, the filter doesn't reject it outright — it **redirects** the browser to the equivalent URL on the correct channel (typically an HTTP request to a secure-required path gets a `302` redirect to the `https://` equivalent).

```java
http.requiresChannel(channel -> channel
    .requestMatchers("/login", "/account/**").requiresSecure()   // MUST arrive over HTTPS
    .anyRequest().requiresInsecure()                              // everything else: plain HTTP is fine
);
```

## 2. Why & when

Some parts of an application — login forms, payment pages, account settings — carry credentials or sensitive data that must never travel in plaintext, even accidentally. A developer typing `http://` instead of `https://`, an old bookmark, or a link shared without the `s` would otherwise send that data unencrypted over the wire. `requiresChannel()` closes that gap at the framework level: instead of trusting every link and bookmark to be correct, the server itself notices the mismatch and transparently upgrades the request by redirecting to the secure equivalent, before the request ever reaches a controller.

Reach for `requiresChannel()` when:

- Only *some* URLs need HTTPS (a marketing homepage can stay on HTTP for speed, but `/login` and `/checkout` must not) — a blanket "redirect everything to HTTPS" rule at the load balancer is coarser than per-path control.
- You want the **first** HTTP request to a secure resource to still succeed, just redirected — unlike HSTS (covered two cards back), which relies on the browser already having seen a prior HTTPS response before it will refuse to even attempt HTTP.
- Migrating an application incrementally to HTTPS, where some legacy paths still need to explicitly allow plain HTTP (`requiresInsecure()`) while new sensitive paths are locked to HTTPS.
- Working with the legacy `ChannelDecisionManager`/`SecureChannelProcessor`/`InsecureChannelProcessor` triad in older codebases, since `requiresChannel()` is the modern DSL front end for exactly the same underlying decision-and-redirect mechanism.

The key distinction from HSTS: `requiresChannel()` is a **server-side, per-request, redirect-based** enforcement — the server actively notices the wrong channel and issues a `3xx` redirect to the secure URL, working correctly even on a browser's very first visit. HSTS is a **browser-side, cached** instruction — after the browser has received one HTTPS response with a `Strict-Transport-Security` header, it refuses to even attempt plain HTTP for that host again, rewriting the request internally before it ever leaves the machine. The two complement each other: `requiresChannel()` handles the first visit and any URL the server sees; HSTS handles every visit after that, including ones the server never gets a chance to redirect because the browser blocks the insecure attempt outright.

## 3. Core concept

```
ChannelProcessingFilter (runs EARLY in the filter chain, before authentication)
  for each incoming request:
    1. find the ChannelDecisionManager's applicable ConfigAttribute for this request's matcher
       ("REQUIRES_SECURE_CHANNEL" or "REQUIRES_INSECURE_CHANNEL")
    2. delegate to the matching ChannelProcessor:
         SecureChannelProcessor   -- handles "REQUIRES_SECURE_CHANNEL"
           request.isSecure() == true  -> do nothing, let the request continue
           request.isSecure() == false -> build the https:// equivalent URL, redirect (302), STOP the chain here
         InsecureChannelProcessor -- handles "REQUIRES_INSECURE_CHANNEL"
           request.isSecure() == false -> do nothing, let the request continue
           request.isSecure() == true  -> build the http:// equivalent URL, redirect (302), STOP the chain here

requiresChannel() DSL  ==  modern configuration surface for this SAME ChannelDecisionManager /
                           ChannelProcessor pair -- no behavioral difference, just less XML/bean wiring
```

Because this filter runs before authentication and authorization filters, a request redirected for being on the wrong channel never even reaches the point where credentials would be checked — the channel requirement is satisfied first, independently of who the caller is.

## 4. Diagram

<svg viewBox="0 0 640 260" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="An HTTP request to a secure required path is intercepted by ChannelProcessingFilter before authentication runs the SecureChannelProcessor notices the request is not secure and issues a 302 redirect to the https equivalent URL only once the browser follows the redirect and arrives over HTTPS does the request continue past the filter to authentication and the controller">
  <rect x="20" y="20" width="180" height="50" rx="8" fill="#1c2430" stroke="#8b949e" stroke-width="1.4"/>
  <text x="110" y="42" fill="#e6edf3" font-size="12" text-anchor="middle" font-family="sans-serif">Browser</text>
  <text x="110" y="58" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">GET http://.../account</text>

  <rect x="230" y="20" width="220" height="50" rx="8" fill="#1c2430" stroke="#6db33f" stroke-width="1.6"/>
  <text x="340" y="42" fill="#6db33f" font-size="12" text-anchor="middle" font-family="sans-serif">ChannelProcessingFilter</text>
  <text x="340" y="58" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">(before authentication)</text>

  <rect x="480" y="20" width="140" height="50" rx="8" fill="#1c2430" stroke="#f85149" stroke-width="1.4"/>
  <text x="550" y="42" fill="#f85149" font-size="11" text-anchor="middle" font-family="sans-serif">isSecure()?</text>
  <text x="550" y="58" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">false</text>

  <line x1="200" y1="45" x2="225" y2="45" stroke="#79c0ff" stroke-width="2" marker-end="url(#a85)"/>
  <line x1="450" y1="45" x2="475" y2="45" stroke="#79c0ff" stroke-width="2" marker-end="url(#a85)"/>

  <rect x="230" y="110" width="220" height="56" rx="8" fill="#1c2430" stroke="#f85149" stroke-width="1.6"/>
  <text x="340" y="132" fill="#f85149" font-size="11" text-anchor="middle" font-family="sans-serif">SecureChannelProcessor</text>
  <text x="340" y="148" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">302 redirect -&gt;</text>
  <text x="340" y="160" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">https://.../account</text>

  <line x1="340" y1="70" x2="340" y2="105" stroke="#f85149" stroke-width="2" marker-end="url(#a85)"/>

  <rect x="20" y="200" width="180" height="50" rx="8" fill="#1c2430" stroke="#3fb950" stroke-width="1.6"/>
  <text x="110" y="222" fill="#3fb950" font-size="12" text-anchor="middle" font-family="sans-serif">Browser follows</text>
  <text x="110" y="238" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">GET https://.../account</text>

  <line x1="230" y1="145" x2="200" y2="220" stroke="#3fb950" stroke-width="2" marker-end="url(#a85)"/>
  <text x="220" y="190" fill="#3fb950" font-size="9" text-anchor="middle" font-family="sans-serif">redirect followed</text>

  <rect x="480" y="200" width="140" height="50" rx="8" fill="#1c2430" stroke="#3fb950" stroke-width="1.4"/>
  <text x="550" y="222" fill="#3fb950" font-size="11" text-anchor="middle" font-family="sans-serif">isSecure() = true</text>
  <text x="550" y="238" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">chain continues</text>

  <line x1="200" y1="225" x2="475" y2="225" stroke="#3fb950" stroke-width="2" marker-end="url(#a85)"/>

  <defs><marker id="a85" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#79c0ff"/></marker></defs>
</svg>

The first HTTP request never reaches authentication; only the redirected HTTPS request does.

## 5. Runnable example

The scenario: a small in-memory "channel processing" simulator that mirrors `requiresChannel()`'s real behavior — matching request paths to a required channel, then either letting a request through or producing a redirect — grown across three levels into something handling multiple rules, a redirect loop guard, and X-Forwarded-Proto awareness (for apps behind a TLS-terminating proxy or load balancer).

### Level 1 — Basic

A single rule: `/account/**` requires HTTPS; everything else passes through unchanged.

```java
public class ChannelSecurityLevel1 {
    record Request(String path, boolean secure) {}
    record Result(boolean redirected, String redirectTo, boolean proceeds) {}

    // mirrors requiresChannel(channel -> channel.requestMatchers("/account/**").requiresSecure())
    static Result process(Request req) {
        boolean requiresSecure = req.path().startsWith("/account");
        if (requiresSecure && !req.secure()) {
            String redirectTo = "https://example.com" + req.path();
            return new Result(true, redirectTo, false); // 302 issued, chain stops here
        }
        return new Result(false, null, true); // channel requirement already satisfied, continue
    }

    public static void main(String[] args) {
        Result r1 = process(new Request("/account/settings", false));
        Result r2 = process(new Request("/account/settings", true));
        Result r3 = process(new Request("/home", false));

        System.out.println("HTTP to /account: redirected=" + r1.redirected() + " to=" + r1.redirectTo());
        System.out.println("HTTPS to /account: redirected=" + r2.redirected() + " proceeds=" + r2.proceeds());
        System.out.println("HTTP to /home: redirected=" + r3.redirected() + " proceeds=" + r3.proceeds());
    }
}
```

**How to run:** save as `ChannelSecurityLevel1.java`, run `java ChannelSecurityLevel1.java` (JDK 17+ runs single files directly).

Expected output:
```
HTTP to /account: redirected=true to=https://example.com/account/settings
HTTPS to /account: redirected=false proceeds=true
HTTP to /home: redirected=false proceeds=true
```

`process` models exactly one `ChannelProcessor` decision: a path matching `/account/**` that arrives insecure gets a redirect target built and the chain stops (`proceeds=false`); everything else is left alone.

### Level 2 — Intermediate

Real configurations have *multiple* rules, and some paths deliberately require plain HTTP (`requiresInsecure()`) — e.g., a webhook endpoint behind a network that only speaks HTTP internally. Level 2 adds an ordered rule list, mirroring `requestMatchers(...).requiresSecure()` / `requiresInsecure()` chains, plus an explicit "no rule matched" fallback.

```java
import java.util.*;

public class ChannelSecurityLevel2 {
    enum Requirement { SECURE, INSECURE, ANY }

    record ChannelRule(String pathPrefix, Requirement requirement) {}
    record Request(String path, boolean secure) {}
    record Result(boolean redirected, String redirectTo, boolean proceeds) {}

    static Result process(List<ChannelRule> rules, Request req) {
        for (ChannelRule rule : rules) {
            if (!req.path().startsWith(rule.pathPrefix())) continue; // this rule doesn't apply -- try the next

            return switch (rule.requirement()) {
                case SECURE -> req.secure()
                        ? new Result(false, null, true)
                        : new Result(true, "https://example.com" + req.path(), false);
                case INSECURE -> !req.secure()
                        ? new Result(false, null, true)
                        : new Result(true, "http://example.com" + req.path(), false);
                case ANY -> new Result(false, null, true);
            };
        }
        return new Result(false, null, true); // no rule matched at all -- anyRequest().requiresInsecure()-style default
    }

    public static void main(String[] args) {
        List<ChannelRule> rules = List.of(
                new ChannelRule("/account", Requirement.SECURE),
                new ChannelRule("/login", Requirement.SECURE),
                new ChannelRule("/internal/webhook", Requirement.INSECURE),
                new ChannelRule("/", Requirement.ANY)
        );

        Result account = process(rules, new Request("/account/profile", false));
        Result webhook = process(rules, new Request("/internal/webhook", true));
        Result home = process(rules, new Request("/home", false));

        System.out.println("HTTP /account/profile -> redirected=" + account.redirected() + " to=" + account.redirectTo());
        System.out.println("HTTPS /internal/webhook -> redirected=" + webhook.redirected() + " to=" + webhook.redirectTo());
        System.out.println("HTTP /home (ANY rule) -> redirected=" + home.redirected() + " proceeds=" + home.proceeds());
    }
}
```

**How to run:** save as `ChannelSecurityLevel2.java`, run `java ChannelSecurityLevel2.java` (JDK 17+ runs single files directly).

Expected output:
```
HTTP /account/profile -> redirected=true to=https://example.com/account/profile
HTTPS /internal/webhook -> redirected=true to=http://example.com/internal/webhook
HTTP /home (ANY rule) -> redirected=false proceeds=true
```

What changed: rules are now an **ordered list**, matched by prefix, mirroring how `requestMatchers()` calls stack in the real DSL — the first matching rule decides the outcome, just like `Acl` entry evaluation in card 74. The webhook case shows `requiresInsecure()` actively redirecting an *HTTPS* request back down to plain HTTP, the mirror image of the account case — a reminder that channel security is bidirectional, not just an HTTPS-upgrade tool.

### Level 3 — Advanced

Production systems almost always sit behind a TLS-terminating load balancer or reverse proxy: the request arrives at the application server as plain HTTP, but the *original* client connection to the proxy was HTTPS. Spring Security (via `ForwardedHeaderFilter` in real deployments) must trust an `X-Forwarded-Proto: https` header to know the original channel was secure — otherwise every request looks insecure to the app and gets redirect-looped forever. Level 3 adds proxy-header awareness and a redirect-loop guard.

```java
import java.util.*;

public class ChannelSecurityLevel3 {
    enum Requirement { SECURE, INSECURE, ANY }
    record ChannelRule(String pathPrefix, Requirement requirement) {}
    record Request(String path, boolean rawSecure, String forwardedProto, int redirectCount) {}
    record Result(boolean redirected, String redirectTo, boolean proceeds, String reason) {}

    static final int MAX_REDIRECTS = 3; // guards against a misconfigured proxy causing infinite redirects

    // resolves the EFFECTIVE channel: trust X-Forwarded-Proto if present, else the raw connection
    static boolean effectiveSecure(Request req) {
        if (req.forwardedProto() != null) {
            return req.forwardedProto().equalsIgnoreCase("https");
        }
        return req.rawSecure();
    }

    static Result process(List<ChannelRule> rules, Request req) {
        if (req.redirectCount() >= MAX_REDIRECTS) {
            return new Result(false, null, false, "redirect loop guard tripped -- refusing to redirect again");
        }

        boolean secure = effectiveSecure(req);

        for (ChannelRule rule : rules) {
            if (!req.path().startsWith(rule.pathPrefix())) continue;

            return switch (rule.requirement()) {
                case SECURE -> secure
                        ? new Result(false, null, true, "already secure (effective)")
                        : new Result(true, "https://example.com" + req.path(), false, "upgrading to https");
                case INSECURE -> !secure
                        ? new Result(false, null, true, "already insecure (effective)")
                        : new Result(true, "http://example.com" + req.path(), false, "downgrading to http");
                case ANY -> new Result(false, null, true, "no channel requirement");
            };
        }
        return new Result(false, null, true, "no rule matched -- default allow");
    }

    public static void main(String[] args) {
        List<ChannelRule> rules = List.of(
                new ChannelRule("/account", Requirement.SECURE),
                new ChannelRule("/", Requirement.ANY)
        );

        // Case A: raw HTTP at the app, but the proxy terminated TLS and says so via the header
        Request behindProxy = new Request("/account/settings", false, "https", 0);
        Result a = process(rules, behindProxy);
        System.out.println("Behind TLS-terminating proxy: redirected=" + a.redirected() + " reason=" + a.reason());

        // Case B: genuinely plain HTTP, no proxy header at all
        Request plainHttp = new Request("/account/settings", false, null, 0);
        Result b = process(rules, plainHttp);
        System.out.println("Genuinely plain HTTP: redirected=" + b.redirected() + " to=" + b.redirectTo());

        // Case C: a misbehaving client/proxy keeps re-requesting insecurely -- loop guard trips
        Request loopy = new Request("/account/settings", false, null, MAX_REDIRECTS);
        Result c = process(rules, loopy);
        System.out.println("Redirect loop guard: redirected=" + c.redirected() + " reason=" + c.reason());
    }
}
```

**How to run:** save as `ChannelSecurityLevel3.java`, run `java ChannelSecurityLevel3.java` (JDK 17+ runs single files directly).

Expected output:
```
Behind TLS-terminating proxy: redirected=false reason=already secure (effective)
Genuinely plain HTTP: redirected=true to=https://example.com/account/settings
Redirect loop guard: redirected=false reason=redirect loop guard tripped -- refusing to redirect again
```

`effectiveSecure` prefers `X-Forwarded-Proto` when present — exactly what a real deployment must do, since the raw servlet-level connection to the app server is HTTP even though the original client-to-proxy hop was HTTPS; trusting the raw connection alone in that topology would incorrectly and endlessly redirect every request. The loop guard demonstrates why this header must come from a *trusted* proxy only — blindly trusting a client-supplied `X-Forwarded-Proto` would let anyone claim their request was secure and bypass the requirement entirely, which is why real deployments only honor this header from a known reverse-proxy hop.

## 6. Walkthrough

Trace an end-to-end request using Level 3's logic, in a deployment *without* a trusted proxy in front (the "genuinely plain HTTP" case), through to the resulting HTTP response.

**Request the browser sends:**
```
GET /account/settings HTTP/1.1
Host: example.com
```
(plain HTTP, port 80, no `X-Forwarded-Proto` header — there is no proxy in this trace)

1. The request reaches `ChannelProcessingFilter` (modeled by `process`) before any authentication filter runs — channel security is checked first, regardless of who the caller claims to be.
2. `req.redirectCount()` is `0`, well under `MAX_REDIRECTS`, so the loop guard does not trip.
3. `effectiveSecure(req)` is evaluated: `req.forwardedProto()` is `null` (no proxy header present), so the method falls through to `req.rawSecure()`, which is `false` — the effective channel is insecure.
4. The `for` loop checks each `ChannelRule` in order against `req.path()` (`/account/settings`): the first rule, `ChannelRule("/account", SECURE)`, matches via `startsWith`.
5. Because the rule's requirement is `SECURE` and `secure` is `false`, the `switch` branch builds a redirect target, `"https://example.com/account/settings"`, and returns `new Result(true, ..., false, "upgrading to https")` — `proceeds=false` means the filter chain stops here; no authentication or controller code runs for this request.
6. The `ChannelProcessingFilter` translates that `Result` into an actual HTTP response.

**HTTP response the server sends back:**
```
HTTP/1.1 302 Found
Location: https://example.com/account/settings
Content-Length: 0
```

7. The browser receives the `302` and, per standard HTTP redirect handling, automatically issues a brand-new request to the `Location` URL — this time over HTTPS.

**The browser's follow-up request:**
```
GET /account/settings HTTP/1.1
Host: example.com
```
(this time over a genuine TLS connection, port 443)

8. This second request re-enters `ChannelProcessingFilter`. This time, `req.rawSecure()` is `true` (a real HTTPS connection), so `effectiveSecure` returns `true`.
9. The same rule matches, but since `secure` is now `true`, the branch returns `new Result(false, null, true, "already secure (effective)")` — `proceeds=true`, so the request is allowed to continue past channel security into authentication, authorization, and finally the controller.
10. Assuming the caller is authenticated and authorized for `/account/settings`, the controller runs normally and returns its actual response — e.g. `200 OK` with the account settings page — this time delivered entirely over the encrypted channel the original insecure request never had.

```
Client              ChannelProcessingFilter        Later filters / controller
  | GET http://.../account/settings                 |
  |------------------->|                             |
  |   302 Location: https://.../account/settings      |
  |<--------------------|                             |
  | GET https://.../account/settings                  |
  |------------------->| effectiveSecure=true -> pass |
  |                     |---------------------------->|
  |                     |     200 OK (account page)   |
  |<---------------------------------------------------|
```

## 7. Gotchas & takeaways

> **Gotcha:** `requiresChannel()` only *redirects* — it never rejects outright the way `HttpFirewall` (next card) or an authorization denial does. A request on the wrong channel always gets a `3xx` toward the correct one, which means an attacker can still observe that the resource exists (just not access it without the right channel *and* the right credentials). Don't rely on channel security alone to hide the existence of sensitive endpoints.

> **Gotcha:** behind a load balancer or reverse proxy that terminates TLS, the servlet container sees every request as plain HTTP unless the proxy's `X-Forwarded-Proto` (or similar) header is forwarded *and* explicitly trusted — otherwise every request looks insecure to `requiresChannel()`, triggering an infinite redirect loop exactly like Level 3's guard case demonstrates, except with no guard the real filter would keep redirecting forever.

- `requiresChannel()` is the modern DSL for the legacy `ChannelDecisionManager` / `SecureChannelProcessor` / `InsecureChannelProcessor` trio — same redirect-based enforcement, less manual bean wiring.
- It runs via `ChannelProcessingFilter`, early in the filter chain, before authentication — a channel mismatch is caught and redirected before credentials are ever considered.
- `requiresSecure()` upgrades HTTP to HTTPS with a redirect; `requiresInsecure()` does the mirror-image downgrade — both are available, since some internal or legacy endpoints deliberately require plain HTTP.
- It complements, not replaces, **HSTS** (card 0081): `requiresChannel()` handles the server-side redirect on first contact and for any request the server actually receives; HSTS handles every subsequent visit by having the *browser itself* refuse to attempt HTTP at all, without needing a round trip to the server.
- Behind a TLS-terminating proxy, trust `X-Forwarded-Proto` only from a known, trusted proxy hop — never from an arbitrary client — or channel security becomes either bypassable or an infinite-redirect trap.

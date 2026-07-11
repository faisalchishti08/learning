---
card: spring-security
gi: 81
slug: http-strict-transport-security
title: "HTTP Strict Transport Security"
---

## 1. What it is

**HTTP Strict Transport Security (HSTS)** is a response header, `Strict-Transport-Security`, that instructs a browser to only ever connect to a given domain over HTTPS for a specified period of time — even if the user types a plain `http://` URL, clicks an `http://` link, or has an old bookmark pointing at the insecure scheme. The header carries two key directives: `max-age`, the number of seconds the browser should remember and enforce this rule, and the optional `includeSubDomains`, which extends the same enforcement to every subdomain of the current one. Spring Security enables HSTS by default through `HttpSecurity`'s `hsts()` DSL, sending `Strict-Transport-Security: max-age=31536000 ; includeSubDomains` (roughly one year) on every HTTPS response, with no extra configuration required.

```java
http.headers(headers -> headers
    .httpStrictTransportSecurity(hsts -> hsts
        .includeSubDomains(true)
        .maxAgeInSeconds(31536000) // one year, the default
    )
);
```

## 2. Why & when

HSTS exists to close a gap that plain HTTPS, on its own, cannot close: a user typing `example.com` into the address bar, or following an old plain `http://` link, sends that very first request over unencrypted HTTP by default, before any redirect to HTTPS has a chance to happen. An attacker positioned on the network (a hostile Wi-Fi hotspot, a compromised router) can intercept that first plaintext request and either serve a convincing fake page directly or silently proxy the real site while reading and altering everything in between — a **downgrade** or **SSL-stripping** attack. Once a browser has seen a domain's HSTS header even once, it rewrites every subsequent attempt to reach that domain, including ones typed as `http://`, into `https://` internally, before a single insecure packet is sent, closing the gap for every visit after the first.

Reach for HSTS when:

- Your application is always served over HTTPS and you want to guarantee browsers never fall back to plaintext HTTP for it, even by accident or via an old link.
- You want to protect users from downgrade attacks on untrusted networks, where an attacker actively tries to intercept the very first, unprotected request to your domain.
- You control an entire domain hierarchy and want subdomains protected too — `includeSubDomains` extends the guarantee without needing the header repeated on every subdomain's own responses.
- You're prepared to commit to HTTPS for the full `max-age` duration, since a misconfigured or prematurely-removed HTTPS deployment during that window leaves returning users unable to reach the site at all until the enforcement period expires.

The previous cards in this series covered `Referrer-Policy`/`Permissions-Policy` and clickjacking protection via frame options; HSTS is unrelated to either — it protects the transport channel itself (ensuring HTTPS is actually used) rather than what leaks through the channel or how the page can be embedded.

## 3. Core concept

```
Strict-Transport-Security: max-age=31536000 ; includeSubDomains

  max-age            -- seconds the browser should enforce HTTPS-only for this domain (31536000 = 1 year)
  includeSubDomains  -- extends enforcement to *.example.com as well as example.com itself

First visit (the "trust on first use" gap):
  user types http://example.com  -> request goes out over PLAIN HTTP  -> attacker CAN intercept here
  server responds (perhaps via redirect) with Strict-Transport-Security header over HTTPS
  browser now REMEMBERS: "always use HTTPS for example.com, for the next max-age seconds"

Every subsequent visit within max-age:
  user types http://example.com  -> browser INTERNALLY rewrites to https://  -> request NEVER sent over HTTP
  -> attacker has NOTHING to intercept -- the insecure request never left the browser

The remaining gap: HSTS preload lists
  browsers ship with a HARDCODED list of domains that are HTTPS-only from the very first visit ever,
  submitted in advance via hstspreload.org -- this eliminates the "first visit" gap entirely,
  at the cost of being essentially permanent and hard to reverse
```

The browser checks its stored HSTS policy for a domain before it sends any request there — if a matching, unexpired policy exists, the browser transparently upgrades the request's scheme to `https://` internally, before any network I/O happens at all, so a network attacker never sees a plaintext request to rewrite or intercept in the first place.

## 4. Diagram

<svg viewBox="0 0 640 280" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="On a first visit a user types http example dot com the request leaves over plain http where an attacker could intercept it the server redirects to https and sends a strict dash transport dash security header the browser stores this policy on every later visit within the max age window the browser rewrites http to https internally before sending anything so the attacker has no plaintext request left to intercept">
  <rect x="20" y="15" width="600" height="95" rx="9" fill="#1c2430" stroke="#f85149" stroke-width="1.5"/>
  <text x="320" y="35" fill="#f85149" font-size="12" text-anchor="middle" font-family="sans-serif">First visit -- the "trust on first use" gap</text>
  <text x="320" y="58" fill="#e6edf3" font-size="11" text-anchor="middle" font-family="sans-serif">user types http://example.com -&gt; request sent over PLAIN HTTP</text>
  <text x="320" y="78" fill="#f85149" font-size="10" text-anchor="middle" font-family="sans-serif">attacker on the network CAN intercept this one request</text>
  <text x="320" y="98" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">server redirects to https and sends Strict-Transport-Security header</text>

  <line x1="320" y1="110" x2="320" y2="135" stroke="#8b949e" stroke-width="1.5" marker-end="url(#a81)"/>
  <text x="320" y="128" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">browser stores the HSTS policy for max-age seconds</text>

  <rect x="20" y="145" width="600" height="120" rx="9" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="320" y="165" fill="#6db33f" font-size="12" text-anchor="middle" font-family="sans-serif">Every later visit within max-age</text>
  <text x="320" y="188" fill="#e6edf3" font-size="11" text-anchor="middle" font-family="sans-serif">user types http://example.com</text>
  <text x="320" y="208" fill="#79c0ff" font-size="11" text-anchor="middle" font-family="sans-serif">browser rewrites to https:// INTERNALLY -- before any network I/O</text>
  <text x="320" y="230" fill="#3fb950" font-size="11" text-anchor="middle" font-family="sans-serif">no plaintext request ever leaves the browser</text>
  <text x="320" y="250" fill="#3fb950" font-size="10" text-anchor="middle" font-family="sans-serif">attacker has nothing left to intercept</text>

  <defs><marker id="a81" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#8b949e"/></marker></defs>
</svg>

The very first request is the only one ever exposed to a downgrade attack; every subsequent request within the policy's lifetime is rewritten to HTTPS before it leaves the browser.

## 5. Runnable example

The scenario: a small in-memory model of a browser's HSTS policy store, starting with a single domain's stored policy rewriting insecure requests, then growing to handle policy expiry and `includeSubDomains`, and finally adding a preload list that eliminates the first-visit gap entirely.

### Level 1 — Basic

A minimal HSTS policy store: once a domain's policy is recorded, rewrite any request to that domain from `http` to `https`.

```java
import java.util.*;

public class HstsLevel1 {

    // the browser's in-memory HSTS policy store: domain -> "policy exists" (ignoring expiry for now)
    static final Set<String> hstsDomains = new HashSet<>();

    // called when a response carries a Strict-Transport-Security header
    static void recordPolicy(String domain) {
        hstsDomains.add(domain);
    }

    // simulates the browser deciding what scheme to actually use for an outgoing request
    static String resolveUrl(String requestedUrl) {
        String scheme = requestedUrl.substring(0, requestedUrl.indexOf("://"));
        String rest = requestedUrl.substring(requestedUrl.indexOf("://") + 3);
        String domain = rest.contains("/") ? rest.substring(0, rest.indexOf("/")) : rest;

        if (scheme.equals("http") && hstsDomains.contains(domain)) {
            return "https://" + rest; // rewritten BEFORE any network request is sent
        }
        return requestedUrl;
    }

    public static void main(String[] args) {
        System.out.println("Before any policy recorded: " + resolveUrl("http://example.com/login"));

        recordPolicy("example.com"); // simulates the browser having seen the HSTS header once already

        System.out.println("After policy recorded: " + resolveUrl("http://example.com/login"));
    }
}
```

**How to run:** save as `HstsLevel1.java`, run `java HstsLevel1.java` (JDK 17+ runs single files directly).

Expected output:
```
Before any policy recorded: http://example.com/login
After policy recorded: https://example.com/login
```

Before `recordPolicy` runs, `resolveUrl` has no stored policy for `example.com` and passes the requested URL through unchanged — this is the exposed first-visit state. After `recordPolicy` runs (simulating the browser having received a `Strict-Transport-Security` header on an earlier response), every later request to that domain is rewritten from `http://` to `https://` internally, before the browser would ever send it over the network.

### Level 2 — Intermediate

Add real policy expiry (`max-age`) and the `includeSubDomains` directive, so a subdomain of a protected domain is covered too.

```java
import java.time.*;
import java.util.*;

public class HstsLevel2 {

    record HstsPolicy(long maxAgeSeconds, boolean includeSubDomains, Instant recordedAt) {
        boolean isExpired(Instant now) {
            return now.isAfter(recordedAt.plusSeconds(maxAgeSeconds));
        }
    }

    static final Map<String, HstsPolicy> hstsPolicies = new HashMap<>();

    static void recordPolicy(String domain, long maxAgeSeconds, boolean includeSubDomains, Instant now) {
        hstsPolicies.put(domain, new HstsPolicy(maxAgeSeconds, includeSubDomains, now));
    }

    // finds an applicable, non-expired policy for a domain, checking the domain itself and
    // then each parent domain (for includeSubDomains) -- e.g. "app.example.com" checks
    // "app.example.com" first, then "example.com"
    static Optional<HstsPolicy> findApplicablePolicy(String domain, Instant now) {
        HstsPolicy exact = hstsPolicies.get(domain);
        if (exact != null && !exact.isExpired(now)) {
            return Optional.of(exact);
        }
        int dot = domain.indexOf('.');
        if (dot == -1) return Optional.empty(); // no parent domain left to check
        String parent = domain.substring(dot + 1);
        HstsPolicy parentPolicy = hstsPolicies.get(parent);
        if (parentPolicy != null && parentPolicy.includeSubDomains() && !parentPolicy.isExpired(now)) {
            return Optional.of(parentPolicy);
        }
        return Optional.empty();
    }

    static String resolveUrl(String requestedUrl, Instant now) {
        String scheme = requestedUrl.substring(0, requestedUrl.indexOf("://"));
        String rest = requestedUrl.substring(requestedUrl.indexOf("://") + 3);
        String domain = rest.contains("/") ? rest.substring(0, rest.indexOf("/")) : rest;

        if (scheme.equals("http") && findApplicablePolicy(domain, now).isPresent()) {
            return "https://" + rest;
        }
        return requestedUrl;
    }

    public static void main(String[] args) {
        Instant t0 = Instant.parse("2026-01-01T00:00:00Z");

        // example.com sets a 1-year policy WITH includeSubDomains
        recordPolicy("example.com", 31_536_000, true, t0);

        System.out.println("app.example.com (covered via includeSubDomains): "
                + resolveUrl("http://app.example.com/dashboard", t0.plusSeconds(10)));

        System.out.println("example.com itself, well within max-age: "
                + resolveUrl("http://example.com/login", t0.plusSeconds(1000)));

        System.out.println("example.com, checked AFTER max-age has elapsed: "
                + resolveUrl("http://example.com/login", t0.plusSeconds(31_536_001)));
    }
}
```

**How to run:** save as `HstsLevel2.java`, run `java HstsLevel2.java` (JDK 17+ runs single files directly).

Expected output:
```
app.example.com (covered via includeSubDomains): https://app.example.com/dashboard
example.com itself, well within max-age: https://example.com/login
example.com, checked AFTER max-age has elapsed: http://example.com/login
```

What changed from Level 1: `HstsPolicy` now tracks `maxAgeSeconds` and `recordedAt`, so `isExpired` can determine whether the browser's remembered policy is still valid, matching how real browsers eventually forget an HSTS policy if the site is never revisited before `max-age` elapses. `findApplicablePolicy` also checks the parent domain when `includeSubDomains` was set, which is why `app.example.com`, which never received its own header, still gets upgraded to HTTPS purely because its parent `example.com` set `includeSubDomains`. Once `max-age` has fully elapsed with no renewal, the policy is treated as expired and the request falls back to plain HTTP — reopening the exact downgrade window HSTS otherwise closes, which is why Spring Security refreshes the header (and thus the expiry clock) on every HTTPS response, not just the first.

### Level 3 — Advanced

Add a hardcoded preload list that protects a domain from its very first visit ever, closing the "trust on first use" gap Levels 1 and 2 both still have, and simulate a full end-to-end request resolution that reports which mechanism protected each request.

```java
import java.time.*;
import java.util.*;

public class HstsLevel3 {

    record HstsPolicy(long maxAgeSeconds, boolean includeSubDomains, Instant recordedAt) {
        boolean isExpired(Instant now) {
            return now.isAfter(recordedAt.plusSeconds(maxAgeSeconds));
        }
    }

    static final Map<String, HstsPolicy> hstsPolicies = new HashMap<>();

    // the browser SHIPS with this list baked in -- no prior visit or header is required at all,
    // closing the first-visit gap entirely for domains that have submitted to a preload list
    static final Set<String> preloadedDomains = Set.of("secure-bank.com");

    static void recordPolicy(String domain, long maxAgeSeconds, boolean includeSubDomains, Instant now) {
        hstsPolicies.put(domain, new HstsPolicy(maxAgeSeconds, includeSubDomains, now));
    }

    static Optional<HstsPolicy> findApplicablePolicy(String domain, Instant now) {
        HstsPolicy exact = hstsPolicies.get(domain);
        if (exact != null && !exact.isExpired(now)) return Optional.of(exact);
        int dot = domain.indexOf('.');
        if (dot == -1) return Optional.empty();
        String parent = domain.substring(dot + 1);
        HstsPolicy parentPolicy = hstsPolicies.get(parent);
        if (parentPolicy != null && parentPolicy.includeSubDomains() && !parentPolicy.isExpired(now)) {
            return Optional.of(parentPolicy);
        }
        return Optional.empty();
    }

    // reports not just the resolved URL but WHY it was resolved that way, for clarity
    record Resolution(String url, String reason) {}

    static Resolution resolveUrl(String requestedUrl, Instant now) {
        String scheme = requestedUrl.substring(0, requestedUrl.indexOf("://"));
        String rest = requestedUrl.substring(requestedUrl.indexOf("://") + 3);
        String domain = rest.contains("/") ? rest.substring(0, rest.indexOf("/")) : rest;

        if (!scheme.equals("http")) {
            return new Resolution(requestedUrl, "already HTTPS, nothing to upgrade");
        }
        if (preloadedDomains.contains(domain)) {
            return new Resolution("https://" + rest, "protected via browser's HARDCODED preload list (first visit safe)");
        }
        Optional<HstsPolicy> policy = findApplicablePolicy(domain, now);
        if (policy.isPresent()) {
            return new Resolution("https://" + rest, "protected via a PREVIOUSLY stored HSTS header, not yet expired");
        }
        return new Resolution(requestedUrl, "NO protection -- this exact request is exposed to a downgrade attack");
    }

    public static void main(String[] args) {
        Instant t0 = Instant.parse("2026-01-01T00:00:00Z");

        // secure-bank.com has NEVER been visited before and has NO stored policy at all --
        // yet it is still protected, because it is on the browser's built-in preload list
        Resolution firstEverVisit = resolveUrl("http://secure-bank.com/account", t0);
        System.out.println("secure-bank.com, first visit ever: " + firstEverVisit.url()
                + " (" + firstEverVisit.reason() + ")");

        // example.com has NOT been preloaded -- its FIRST visit is genuinely exposed
        Resolution exampleFirstVisit = resolveUrl("http://example.com/login", t0);
        System.out.println("example.com, first visit ever: " + exampleFirstVisit.url()
                + " (" + exampleFirstVisit.reason() + ")");

        recordPolicy("example.com", 31_536_000, true, t0);

        Resolution exampleLaterVisit = resolveUrl("http://example.com/login", t0.plusSeconds(500));
        System.out.println("example.com, later visit: " + exampleLaterVisit.url()
                + " (" + exampleLaterVisit.reason() + ")");
    }
}
```

**How to run:** save as `HstsLevel3.java`, run `java HstsLevel3.java` (JDK 17+ runs single files directly).

Expected output:
```
secure-bank.com, first visit ever: https://secure-bank.com/account (protected via browser's HARDCODED preload list (first visit safe))
example.com, first visit ever: http://example.com/login (NO protection -- this exact request is exposed to a downgrade attack)
example.com, later visit: https://example.com/login (protected via a PREVIOUSLY stored HSTS header, not yet expired)
```

`preloadedDomains` models the real HSTS preload list every major browser ships with, built by submitting a domain to `hstspreload.org` in advance — `secure-bank.com`'s very first request in this run is already upgraded to HTTPS, with no stored policy needed at all, because the browser's shipped-in list already knows about it. `example.com`, which was never preloaded, shows the exact gap preload lists exist to close: its genuinely first-ever request goes out over plain HTTP, unprotected, while every later request (once a policy is recorded from an earlier response) is protected exactly as Level 2 demonstrated. The `Resolution` record's `reason` field makes explicit which of the three states — preloaded, previously-recorded, or unprotected — applied to each specific request, mirroring the real distinction a security review of a domain's HSTS posture needs to make.

## 6. Walkthrough

Trace `example.com`'s two requests from Level 3 end-to-end: the exposed first visit, followed by the protected later one.

Example first request (typed directly by the user, before any policy exists):

```
GET /login HTTP/1.1
Host: example.com
```

Because this request goes out over plain HTTP, it is exposed on the network; assume no attacker intervenes and it reaches the real server, which responds:

```
HTTP/1.1 302 Found
Location: https://example.com/login
Strict-Transport-Security: max-age=31536000 ; includeSubDomains
```

1. The browser sends `GET http://example.com/login` because no HSTS policy for `example.com` exists yet in its store — this is modeled by `findApplicablePolicy` returning `Optional.empty()` and `preloadedDomains` not containing `"example.com"`, so `resolveUrl` returns the original, unmodified `http://` URL with the reason `"NO protection"`.
2. The real server, configured with Spring Security's `httpStrictTransportSecurity()` DSL (active by default whenever the app runs behind HTTPS), responds with a redirect to the HTTPS version of the same path, and — critically — includes the `Strict-Transport-Security` header on this very response, even though the response itself arrived over plain HTTP in this first exchange.
3. The browser follows the redirect to `https://example.com/login`, and — because the response that carried the HSTS header is trusted (this detail matters: browsers only honor `Strict-Transport-Security` headers received over a connection that is *itself* already HTTPS, so the header on this specific redirect response would only take effect once the browser is actually on the HTTPS leg) — the browser now calls the equivalent of `recordPolicy("example.com", 31_536_000, true, now)`, storing the policy with today's timestamp as `recordedAt`.
4. Some time later (500 seconds, in the simulation — well within the one-year `max-age`), the user again types `http://example.com/login`. The browser calls `resolveUrl` again; this time `findApplicablePolicy("example.com", now)` finds the stored, non-expired policy, so the URL is rewritten to `https://example.com/login` **before any request is transmitted over the network at all**.
5. Because the rewrite happens client-side, before any DNS lookup or TCP connection for the insecure version is even attempted, there is no plaintext request for a network attacker to intercept on this second visit — the request that actually leaves the machine is `GET /login HTTP/1.1` over a TLS-wrapped connection to `Host: example.com` from the very first packet.
6. The server responds normally over HTTPS, refreshing the `Strict-Transport-Security` header on this response too — Spring Security emits it on every HTTPS response by default, which extends the policy's expiry window forward from `now`, so an actively-visited site's HSTS protection effectively never lapses.

```
visit 1: http:// request SENT (exposed) -> HTTPS redirect + Strict-Transport-Security header -> policy stored
visit 2 (within max-age): http:// request REWRITTEN to https:// BEFORE sending -> attacker sees nothing
```

The header's entire value comes from being present on that very first HTTPS response the browser manages to reach — every visit after that is protected purely by client-side memory, with no server-side involvement needed until the actual HTTPS request arrives.

## 7. Gotchas & takeaways

> **Gotcha:** the very first request to a domain that has never been visited before and is not on a preload list is genuinely unprotected — HSTS is a "trust on first use" mechanism, meaning the first use is exactly the one moment it cannot defend. If that first request is intercepted and downgraded before the `Strict-Transport-Security` header is ever seen, the browser never learns the policy at all. HSTS preload lists exist specifically to eliminate this gap for domains willing to submit in advance, at the cost of being difficult to reverse once a domain is included.

- Spring Security enables HSTS by default with roughly a one-year `max-age` and `includeSubDomains`, so most applications served over HTTPS get this protection with no extra configuration.
- `includeSubDomains` is powerful but also risky: it applies to every current and future subdomain, so a single subdomain that can't yet serve HTTPS will become entirely unreachable over HTTP once the parent's policy is in effect.
- Browsers only honor a `Strict-Transport-Security` header received over an already-HTTPS connection — sending it over plain HTTP has no effect, since the very channel it would need to protect is the one that already succeeded in delivering it insecurely.
- The header must be resent on every HTTPS response to keep the browser's remembered expiry window rolling forward; a site that stops serving HTTPS (or stops sending the header) will have its protection quietly lapse once the last-recorded `max-age` runs out.
- HSTS preload submission (via hstspreload.org) is close to a one-way decision — removal from browsers' shipped lists can take months across release cycles, so only commit a domain (and, if using `includeSubDomains`, every subdomain) once HTTPS support is fully reliable everywhere.

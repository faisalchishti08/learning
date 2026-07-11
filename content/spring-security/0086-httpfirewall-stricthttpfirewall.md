---
card: spring-security
gi: 86
slug: httpfirewall-stricthttpfirewall
title: "HttpFirewall & StrictHttpFirewall"
---

## 1. What it is

`HttpFirewall` is Spring Security's **first line of defense**, wrapping every incoming `HttpServletRequest` and `HttpServletResponse` before they reach `FilterChainProxy`'s own filter chain — before channel security (previous card), before authentication, before any request matcher gets a chance to evaluate the URL at all. Its job is narrow and deliberate: reject requests whose path is malformed or suspicious in ways that could be used to smuggle a different effective URL past the matchers that are about to inspect it — things like encoded path-traversal sequences (`%2e%2e`), semicolons hiding path parameters (`;jsessionid=...` or `/admin;/public`), non-printable/control characters, or duplicated slashes. `StrictHttpFirewall` is the default, hardened implementation Spring Security ships and wires in automatically; it rejects all of the above out of the box and exposes setters (`setAllowedHttpMethods`, `setAllowUrlEncodedSlash`, etc.) to relax specific checks when a legitimate request needs it.

```java
@Bean
public HttpFirewall httpFirewall() {
    StrictHttpFirewall firewall = new StrictHttpFirewall();
    firewall.setAllowUrlEncodedSlash(true); // relax ONE specific check for a known-legitimate need
    return firewall;
}
```

## 2. Why & when

The firewall exists because of a class of real, historical vulnerabilities: **ambiguous URL parsing**. If the security filter chain's request matchers evaluate a URL one way, but the servlet container (or a downstream proxy, or the eventual controller's `@RequestMapping`) parses the *same string* differently, an attacker can craft a single URL that looks safe to the matcher but resolves to something sensitive once it actually gets dispatched. A path like `/admin/../public/../../admin/secret` or `/secret;ignore=1` has tripped up exactly this kind of mismatch in past CVEs — the matcher normalized or tokenized the path one way, the servlet container's dispatch logic did it another way, and the mismatch let a request bypass an authorization rule that should have blocked it. `StrictHttpFirewall` closes this at the earliest possible point: reject anything ambiguous *before* any matcher gets to reason about it, rather than trying to make every matcher perfectly consistent with every possible downstream interpretation.

Reach for understanding (and occasionally customizing) the firewall when:

- Debugging a mysterious `RequestRejectedException` (often surfaced as a `400 Bad Request`) on a request that "looks fine" — a semicolon, encoded slash, or double slash in the path is almost always the cause, rejected before your controller or even your authorization rules ever saw it.
- A legitimate client sends `HTTP` methods beyond the default allow-list (e.g., a `PATCH`-heavy API, or a `TRACE`/custom verb some integration requires) and needs `setAllowedHttpMethods` adjusted.
- A path genuinely needs an encoded slash (`%2F`) or backslash in a path segment — rare, but `setAllowUrlEncodedSlash(true)` / `setAllowBackSlash(true)` exist for that narrow case, understanding that loosening them re-opens exactly the ambiguity class the firewall exists to close.
- Explaining to a teammate why "the security filter chain never even ran" for a rejected request — `HttpFirewall` operates *outside and before* `FilterChainProxy`'s own chain, at the `DelegatingFilterProxy`/`FilterChainProxy.doFilter` boundary, wrapping the request before any `SecurityFilterChain` matcher logic executes.

## 3. Core concept

```
Raw HttpServletRequest arrives at FilterChainProxy.doFilter(...)
   |
   v
FirewalledRequest firewall.getFirewalledRequest(request)   <-- HttpFirewall runs FIRST, before ANY SecurityFilterChain
   |
   +-- StrictHttpFirewall checks (each throws RequestRejectedException on failure):
   |     - contains ".." (encoded or not) in the path              -> REJECT (path traversal attempt)
   |     - contains ";" in the path (unless explicitly allowed)     -> REJECT (path-parameter smuggling)
   |     - contains "//" (duplicate slash, unless allowed)          -> REJECT (ambiguous segment boundary)
   |     - contains a non-printable / control character              -> REJECT (invisible-character smuggling)
   |     - HTTP method not in the allowed-methods list                -> REJECT (unexpected verb)
   |     - contains an encoded slash "%2F" / "%5C" (unless allowed)   -> REJECT (encoded traversal / bypass)
   |
   +-- request PASSES all checks -> wrapped, forwarded into FilterChainProxy's actual SecurityFilterChain list
   |     (channel security, authentication, authorization, ... run AFTER this point, per card 0085 and earlier)
   |
   +-- request FAILS any check -> RequestRejectedException -> translated to 400 Bad Request, chain never runs
```

Every check the firewall performs runs once, up front, against the raw request — no matcher, filter, or controller downstream ever sees a request the firewall rejected.

## 4. Diagram

<svg viewBox="0 0 640 250" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="A raw request first passes through HttpFirewall which is StrictHttpFirewall by default before FilterChainProxy runs any security filter chain a request containing an encoded dot dot sequence is rejected with 400 bad request before any filter runs while a clean request is wrapped and passed through to channel security authentication and authorization filters in order">
  <rect x="15" y="15" width="610" height="220" rx="9" fill="none" stroke="#8b949e" stroke-width="1" stroke-dasharray="4,3"/>
  <text x="320" y="32" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">Servlet container -&gt; FilterChainProxy.doFilter(...)</text>

  <rect x="35" y="50" width="150" height="46" rx="7" fill="#1c2430" stroke="#79c0ff" stroke-width="1.3"/>
  <text x="110" y="70" fill="#79c0ff" font-size="10" text-anchor="middle" font-family="sans-serif">Raw request</text>
  <text x="110" y="84" fill="#8b949e" font-size="8.5" text-anchor="middle" font-family="sans-serif">GET /admin/%2e%2e/secret</text>

  <rect x="230" y="50" width="180" height="46" rx="7" fill="#1c2430" stroke="#6db33f" stroke-width="1.6"/>
  <text x="320" y="70" fill="#6db33f" font-size="11" text-anchor="middle" font-family="sans-serif">StrictHttpFirewall</text>
  <text x="320" y="84" fill="#8b949e" font-size="8.5" text-anchor="middle" font-family="sans-serif">runs BEFORE any filter</text>

  <line x1="185" y1="73" x2="225" y2="73" stroke="#79c0ff" stroke-width="2" marker-end="url(#a86)"/>

  <rect x="450" y="50" width="150" height="46" rx="7" fill="#1c2430" stroke="#f85149" stroke-width="1.6"/>
  <text x="525" y="70" fill="#f85149" font-size="10" text-anchor="middle" font-family="sans-serif">400 Bad Request</text>
  <text x="525" y="84" fill="#8b949e" font-size="8.5" text-anchor="middle" font-family="sans-serif">RequestRejectedException</text>

  <line x1="410" y1="65" x2="445" y2="65" stroke="#f85149" stroke-width="2" marker-end="url(#a86r)"/>
  <text x="428" y="55" fill="#f85149" font-size="8" text-anchor="middle" font-family="sans-serif">rejected</text>

  <rect x="35" y="140" width="150" height="46" rx="7" fill="#1c2430" stroke="#79c0ff" stroke-width="1.3"/>
  <text x="110" y="160" fill="#79c0ff" font-size="10" text-anchor="middle" font-family="sans-serif">Raw request</text>
  <text x="110" y="174" fill="#8b949e" font-size="8.5" text-anchor="middle" font-family="sans-serif">GET /account/settings</text>

  <rect x="230" y="140" width="180" height="46" rx="7" fill="#1c2430" stroke="#6db33f" stroke-width="1.6"/>
  <text x="320" y="160" fill="#6db33f" font-size="11" text-anchor="middle" font-family="sans-serif">StrictHttpFirewall</text>
  <text x="320" y="174" fill="#3fb950" font-size="8.5" text-anchor="middle" font-family="sans-serif">all checks pass</text>

  <line x1="185" y1="163" x2="225" y2="163" stroke="#79c0ff" stroke-width="2" marker-end="url(#a86)"/>

  <rect x="450" y="140" width="150" height="46" rx="7" fill="#1c2430" stroke="#3fb950" stroke-width="1.6"/>
  <text x="525" y="160" fill="#3fb950" font-size="10" text-anchor="middle" font-family="sans-serif">Channel security -&gt;</text>
  <text x="525" y="174" fill="#e6edf3" font-size="8.5" text-anchor="middle" font-family="sans-serif">auth -&gt; controller</text>

  <line x1="410" y1="163" x2="445" y2="163" stroke="#3fb950" stroke-width="2" marker-end="url(#a86g)"/>

  <defs>
    <marker id="a86" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#79c0ff"/></marker>
    <marker id="a86r" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#f85149"/></marker>
    <marker id="a86g" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#3fb950"/></marker>
  </defs>
</svg>

The firewall runs once, ahead of every other filter, and either stops the request cold or lets it proceed unchanged.

## 5. Runnable example

The scenario: a small in-memory `HttpFirewall` simulator that mirrors `StrictHttpFirewall`'s real checks against a raw path string, grown across three levels from a single path-traversal check into a multi-rule firewall with a configurable allow-list, exactly like the real class's setters.

### Level 1 — Basic

Reject any path containing `..` (encoded or literal) — the classic path-traversal check.

```java
public class HttpFirewallLevel1 {
    record Request(String method, String path) {}
    record FirewallResult(boolean allowed, String reason) {}

    // mirrors StrictHttpFirewall's default rejection of ".." sequences, encoded or not
    static FirewallResult check(Request req) {
        String decoded = req.path().replace("%2e", ".").replace("%2E", ".");
        if (decoded.contains("..")) {
            return new FirewallResult(false, "path contains \"..\" -- possible path traversal");
        }
        return new FirewallResult(true, "passed all checks");
    }

    public static void main(String[] args) {
        FirewallResult r1 = check(new Request("GET", "/admin/%2e%2e/secret"));
        FirewallResult r2 = check(new Request("GET", "/account/settings"));

        System.out.println("GET /admin/%2e%2e/secret -> allowed=" + r1.allowed() + " reason=" + r1.reason());
        System.out.println("GET /account/settings -> allowed=" + r2.allowed() + " reason=" + r2.reason());
    }
}
```

**How to run:** save as `HttpFirewallLevel1.java`, run `java HttpFirewallLevel1.java` (JDK 17+ runs single files directly).

Expected output:
```
GET /admin/%2e%2e/secret -> allowed=false reason=path contains ".." -- possible path traversal
GET /account/settings -> allowed=true reason=passed all checks
```

`check` first decodes the specific `%2e`/`%2E` sequences an attacker might use to hide a literal `.` from a naive string search, then looks for `..` in the decoded result — catching both the plain and encoded forms of the same traversal attempt.

### Level 2 — Intermediate

Real `StrictHttpFirewall` checks several distinct things, not just traversal: semicolons (path-parameter smuggling), duplicate slashes, and a restricted HTTP method allow-list. Level 2 adds all three as independent, ordered checks — mirroring how the real class runs each rule and rejects on the first failure.

```java
import java.util.*;

public class HttpFirewallLevel2 {
    record Request(String method, String path) {}
    record FirewallResult(boolean allowed, String reason) {}

    static final Set<String> ALLOWED_METHODS = Set.of("GET", "POST", "PUT", "DELETE", "PATCH", "HEAD", "OPTIONS");

    static FirewallResult check(Request req) {
        if (!ALLOWED_METHODS.contains(req.method())) {
            return new FirewallResult(false, "HTTP method \"" + req.method() + "\" not in allow-list");
        }

        String decoded = req.path().replace("%2e", ".").replace("%2E", ".");
        if (decoded.contains("..")) {
            return new FirewallResult(false, "path contains \"..\" -- possible path traversal");
        }
        if (req.path().contains(";")) {
            return new FirewallResult(false, "path contains \";\" -- possible path-parameter smuggling");
        }
        if (req.path().contains("//")) {
            return new FirewallResult(false, "path contains \"//\" -- ambiguous segment boundary");
        }
        return new FirewallResult(true, "passed all checks");
    }

    public static void main(String[] args) {
        FirewallResult semicolon = check(new Request("GET", "/admin;/public/data"));
        FirewallResult doubleSlash = check(new Request("GET", "//admin/secret"));
        FirewallResult badMethod = check(new Request("TRACE", "/account/settings"));
        FirewallResult clean = check(new Request("POST", "/orders/42"));

        System.out.println("GET /admin;/public/data -> allowed=" + semicolon.allowed() + " reason=" + semicolon.reason());
        System.out.println("GET //admin/secret -> allowed=" + doubleSlash.allowed() + " reason=" + doubleSlash.reason());
        System.out.println("TRACE /account/settings -> allowed=" + badMethod.allowed() + " reason=" + badMethod.reason());
        System.out.println("POST /orders/42 -> allowed=" + clean.allowed() + " reason=" + clean.reason());
    }
}
```

**How to run:** save as `HttpFirewallLevel2.java`, run `java HttpFirewallLevel2.java` (JDK 17+ runs single files directly).

Expected output:
```
GET /admin;/public/data -> allowed=false reason=path contains ";" -- possible path-parameter smuggling
GET //admin/secret -> allowed=false reason=path contains "//" -- ambiguous segment boundary
TRACE /account/settings -> allowed=false reason=HTTP method "TRACE" not in allow-list
POST /orders/42 -> allowed=true reason=passed all checks
```

What changed: `check` now runs an **ordered sequence** of independent rules, the same pattern `StrictHttpFirewall` uses internally — method allow-list first, then path-shape checks — stopping and reporting the first failure it finds, exactly like `ChannelSecurityLevel2`'s ordered rule list from the previous card. The `/admin;/public/data` case is the historically significant one: a security matcher that only looked at `/admin/**` up to the first `;` could be fooled into thinking this path was `/public/data`, while a servlet container's dispatch might route it to `/admin` anyway — the semicolon check exists specifically to prevent that class of mismatch.

### Level 3 — Advanced

Real applications sometimes need to *relax* a specific check for a legitimate reason (an API that legitimately needs encoded slashes in a path segment, for instance) without disabling the whole firewall. Level 3 adds a configurable `FirewallConfig`, mirroring `StrictHttpFirewall`'s real setters (`setAllowUrlEncodedSlash`, `setAllowSemicolon`, `setAllowedHttpMethods`), and demonstrates that relaxing one check narrows the firewall's protection only for that specific pattern, not universally.

```java
import java.util.*;

public class HttpFirewallLevel3 {
    record Request(String method, String path) {}
    record FirewallResult(boolean allowed, String reason) {}

    // mirrors StrictHttpFirewall's configurable setters -- each check can be independently relaxed
    static class FirewallConfig {
        Set<String> allowedMethods = new HashSet<>(Set.of("GET", "POST", "PUT", "DELETE", "PATCH", "HEAD", "OPTIONS"));
        boolean allowSemicolon = false;
        boolean allowUrlEncodedSlash = false;
        boolean allowDuplicateSlash = false;

        void setAllowedHttpMethods(Set<String> methods) { this.allowedMethods = methods; }
        void setAllowSemicolon(boolean allow) { this.allowSemicolon = allow; }
        void setAllowUrlEncodedSlash(boolean allow) { this.allowUrlEncodedSlash = allow; }
    }

    static FirewallResult check(FirewallConfig config, Request req) {
        if (!config.allowedMethods.contains(req.method())) {
            return new FirewallResult(false, "HTTP method \"" + req.method() + "\" not in allow-list");
        }

        String decoded = req.path().replace("%2e", ".").replace("%2E", ".");
        if (decoded.contains("..")) {
            return new FirewallResult(false, "path contains \"..\" -- possible path traversal"); // NEVER relaxable
        }
        if (!config.allowSemicolon && req.path().contains(";")) {
            return new FirewallResult(false, "path contains \";\" -- possible path-parameter smuggling");
        }
        if (!config.allowUrlEncodedSlash && (req.path().contains("%2f") || req.path().contains("%2F"))) {
            return new FirewallResult(false, "path contains encoded slash \"%2F\" -- possible matcher bypass");
        }
        if (!config.allowDuplicateSlash && req.path().contains("//")) {
            return new FirewallResult(false, "path contains \"//\" -- ambiguous segment boundary");
        }
        return new FirewallResult(true, "passed all checks");
    }

    public static void main(String[] args) {
        // strict default config -- everything StrictHttpFirewall rejects out of the box
        FirewallConfig strict = new FirewallConfig();

        // a relaxed config for one legitimate need: a document API stores encoded slashes in filenames
        FirewallConfig relaxed = new FirewallConfig();
        relaxed.setAllowUrlEncodedSlash(true);

        Request encodedSlashPath = new Request("GET", "/files/reports%2Fq3.pdf");
        Request traversalAttempt = new Request("GET", "/files/%2e%2e/%2e%2e/etc/passwd");

        FirewallResult strictOnEncoded = check(strict, encodedSlashPath);
        FirewallResult relaxedOnEncoded = check(relaxed, encodedSlashPath);
        FirewallResult relaxedOnTraversal = check(relaxed, traversalAttempt);

        System.out.println("Strict firewall, encoded-slash path -> allowed=" + strictOnEncoded.allowed() + " reason=" + strictOnEncoded.reason());
        System.out.println("Relaxed firewall, SAME encoded-slash path -> allowed=" + relaxedOnEncoded.allowed() + " reason=" + relaxedOnEncoded.reason());
        System.out.println("Relaxed firewall, traversal attempt -> allowed=" + relaxedOnTraversal.allowed() + " reason=" + relaxedOnTraversal.reason());
    }
}
```

**How to run:** save as `HttpFirewallLevel3.java`, run `java HttpFirewallLevel3.java` (JDK 17+ runs single files directly).

Expected output:
```
Strict firewall, encoded-slash path -> allowed=false reason=path contains encoded slash "%2F" -- possible matcher bypass
Relaxed firewall, SAME encoded-slash path -> allowed=true reason=passed all checks
Relaxed firewall, traversal attempt -> allowed=false reason=path contains ".." -- possible path traversal
```

The key result: relaxing `allowUrlEncodedSlash` lets the *specific* encoded-slash path through on the relaxed config while the strict config still rejects it, but the traversal check is **not** wired to that same flag at all — it has no corresponding setter in this model, exactly mirroring how `StrictHttpFirewall` keeps the most dangerous check (`..` traversal) effectively non-negotiable while exposing narrower, opt-in relaxations for lower-risk patterns like encoded slashes.

## 6. Walkthrough

Trace a concrete end-to-end request using Level 3's `relaxed` configuration, from the raw HTTP request through the firewall to the final HTTP response.

**Request the client sends:**
```
GET /files/reports%2Fq3.pdf HTTP/1.1
Host: example.com
Accept: application/pdf
```

1. The servlet container hands this raw request to `FilterChainProxy.doFilter(...)`, which immediately delegates to the configured `HttpFirewall` (here, the `relaxed` `StrictHttpFirewall`-equivalent) — this happens before any `SecurityFilterChain`, before channel security (card 0085), before authentication.
2. `check(relaxed, req)` runs. First, `config.allowedMethods.contains("GET")` is checked — `GET` is in the default allow-list, so this passes.
3. `decoded` is computed by replacing `%2e`/`%2E` with `.` in the path `/files/reports%2Fq3.pdf` — there is no `%2e` sequence here at all (the encoded character is `%2F`, a slash, not a dot), so `decoded` is unchanged and `decoded.contains("..")` is `false`. The traversal check passes.
4. `config.allowSemicolon` is `false` (never relaxed in this config) and the path contains no `;`, so that check passes regardless.
5. `config.allowUrlEncodedSlash` is `true` on the `relaxed` config, so the entire encoded-slash check is skipped (`!config.allowUrlEncodedSlash` is `false`, short-circuiting the `&&`) — this is the one check this specific configuration deliberately narrows.
6. `config.allowDuplicateSlash` is `false` and the path contains no `//`, so that check passes.
7. All checks pass, so `check` returns `new FirewallResult(true, "passed all checks")` — the firewall wraps the request and forwards it into the actual `SecurityFilterChain` list: channel security next (does this path require HTTPS? assume yes and the connection already is), then authentication, then authorization, then finally the controller mapped to `/files/{name}`.
8. The controller decodes `reports%2Fq3.pdf` back to the literal filename `reports/q3.pdf`, locates that file, and streams it back.

**Response the server sends:**
```
HTTP/1.1 200 OK
Content-Type: application/pdf
Content-Length: 48213

<PDF binary bytes>
```

9. Contrast this with the strict configuration on the *same* request: at step 5, `config.allowUrlEncodedSlash` would be `false`, so the check runs, finds `%2F` in the path, and `check` returns `allowed=false` immediately — the request never reaches step 7, channel security, authentication, or the controller at all.

```
strict config:   request -> HttpFirewall -- REJECTED (encoded slash) --> 400 Bad Request, nothing downstream runs
relaxed config:  request -> HttpFirewall -- passes --> channel security -> auth -> controller -> 200 OK
```

10. This demonstrates the core value of the firewall running first: the *entire* downstream chain — matchers, authentication, business logic — never has to reason about ambiguous encodings at all, because by the time a request reaches any of it, the firewall has already guaranteed the path is unambiguous (or rejected it outright).

## 7. Gotchas & takeaways

> **Gotcha:** a rejected request surfaces as a generic `400 Bad Request` with no security-specific detail by default, precisely so an attacker probing for path-traversal or semicolon-based bypass attempts can't distinguish "the firewall caught this" from "this is just a malformed request" — but that same opacity means legitimate-but-unusual client requests (a URL-encoded slash in a genuinely valid filename, for instance) get rejected with the same unhelpful `400`, which is often mistaken for an application bug rather than a firewall configuration decision.

> **Gotcha:** `HttpFirewall` runs **outside** `FilterChainProxy`'s own `SecurityFilterChain` list entirely — a rejected request never reaches even the *first* `SecurityFilterChain`, meaning per-chain customizations (different rules for different `SecurityFilterChain` beans in a multi-chain setup) cannot override a firewall rejection; the firewall is configured once, globally, typically via a `WebSecurityCustomizer` (card 0021) calling `.httpFirewall(...)`.

- `HttpFirewall`/`StrictHttpFirewall` is the very first checkpoint a request passes through — before channel security, before authentication, before any request matcher — specifically to prevent ambiguous URLs from being interpreted differently by a security matcher than by the eventual servlet dispatch or controller.
- `StrictHttpFirewall` rejects, by default: `..` sequences (encoded or literal), semicolons, encoded slashes/backslashes, duplicate slashes, non-printable characters, and any HTTP method outside its allow-list.
- The historical motivation is concrete: past CVEs exploited exactly this class of matcher-versus-dispatcher parsing mismatch to bypass authorization rules that looked correct on paper.
- Customization exists (`setAllowedHttpMethods`, `setAllowUrlEncodedSlash`, `setAllowSemicolon`, etc.) for narrow, legitimate needs — each setter relaxes exactly one check, not the firewall's other protections, and each relaxation should be a deliberate, documented exception rather than a blanket workaround for a `400` you don't understand yet.
- A rejected request produces a generic `400 Bad Request` via `RequestRejectedException`, deliberately without revealing which specific rule tripped, to avoid giving probing attackers a bypass oracle.

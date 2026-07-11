---
card: spring-security
gi: 78
slug: content-security-policy
title: Content Security Policy
---

## 1. What it is

**Content Security Policy (CSP)** is a single response header, `Content-Security-Policy`, that tells the browser exactly which sources a page is allowed to load resources from and which inline content it's allowed to execute — per resource type. Directives like `default-src`, `script-src`, and `style-src` each take a list of allowed sources (`'self'`, a specific origin, or special keywords like `'unsafe-inline'`); anything the page tries to load or run that isn't on the allowlist is silently blocked by the browser, regardless of how it got into the page. Spring Security exposes this through `ContentSecurityPolicyConfig` inside the `headers{}` DSL, via `contentSecurityPolicy(csp -> csp.policyDirectives("..."))`. A particularly powerful pattern is **nonce-based script allowlisting**: the server generates a fresh random value on every response, includes it in the `script-src` directive as `'nonce-<value>'`, and stamps that same value onto the one `<script>` tag it actually rendered — so that exact tag runs, while any other injected script, lacking the nonce, does not.

```java
http.headers(headers -> headers
    .contentSecurityPolicy(csp -> csp.policyDirectives(
        "default-src 'self'; script-src 'self' 'nonce-" + nonce + "'; style-src 'self' 'unsafe-inline'"
    ))
);
```

## 2. Why & when

The previous card's overview mentioned CSP as one of several defenses; here's why it's the deepest one against XSS specifically. A classic reflected or stored XSS bug lets an attacker get a `<script>` tag into your page's HTML — but *getting the tag onto the page* and *getting the browser to execute it* are two different problems, and CSP attacks the second one directly. Even if an attacker successfully injects `<script>steal(document.cookie)</script>`, a browser enforcing `script-src 'self'` (with no `'unsafe-inline'`) refuses to run that inline script at all, because it isn't loaded from an allowed source and carries no valid nonce. This is defense that survives even when input validation and output encoding both fail somewhere.

Reach for CSP configuration when:

- Hardening against XSS as a second line of defense, on top of (never instead of) proper output encoding.
- Your app needs a few legitimate inline `<script>` or `<style>` tags (server-rendered pages often do) — nonces let you allowlist exactly those, without opening the door to `'unsafe-inline'` for everything.
- Rolling out a new or tightened policy safely — `Content-Security-Policy-Report-Only` enforces nothing but logs what *would* have been blocked, letting you validate against real traffic first.
- Loading resources (scripts, styles, fonts, images, XHR/fetch targets) from specific third-party origins — each gets its own directive (`script-src`, `style-src`, `font-src`, `connect-src`, …) rather than one blanket allowlist.

## 3. Core concept

| Directive | Governs | Falls back to `default-src`? |
|---|---|---|
| `default-src` | Fallback allowlist for any fetch directive not explicitly set | — |
| `script-src` | Which scripts may execute (external `src=`, inline, `eval`) | yes |
| `style-src` | Which stylesheets/inline styles may apply | yes |
| `img-src`, `font-src`, `connect-src`, `media-src` | Images, fonts, `fetch`/XHR targets, audio/video | yes |
| `frame-ancestors` | Who may embed this page in a frame (CSP's answer to `X-Frame-Options`) | **no** — must be set explicitly |
| `form-action` | Where `<form>` submissions may target | **no** — must be set explicitly |
| `base-uri` | Allowed values for a `<base href>` tag | **no** — must be set explicitly |

Nonce mechanic: `script-src 'self' 'nonce-abc123'` allows only inline scripts whose `nonce` attribute equals `abc123` — a fresh value every response, so a script injected via a stored XSS bug from a previous response can never guess the current one.

## 4. Diagram

<svg viewBox="0 0 640 240" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="A page's own inline script carries the nonce embedded in the current response's Content Security Policy header so it is allowed to execute an attacker injected script has no matching nonce so the browser blocks it from running at all">
  <rect x="15" y="15" width="600" height="34" rx="6" fill="#1c2430" stroke="#79c0ff" stroke-width="1.3"/>
  <text x="320" y="37" fill="#79c0ff" font-size="10" text-anchor="middle" font-family="sans-serif">Content-Security-Policy: script-src 'self' 'nonce-r4nd0m=='</text>

  <rect x="40" y="80" width="260" height="90" rx="8" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="170" y="103" fill="#6db33f" font-size="10.5" text-anchor="middle" font-family="sans-serif">&lt;script nonce="r4nd0m=="&gt;</text>
  <text x="170" y="120" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">server-rendered, nonce matches</text>
  <text x="170" y="142" fill="#3fb950" font-size="10" text-anchor="middle" font-family="sans-serif">ALLOWED -&gt; executes</text>

  <rect x="340" y="80" width="260" height="90" rx="8" fill="#1c2430" stroke="#f85149" stroke-width="1.5"/>
  <text x="470" y="103" fill="#f85149" font-size="10.5" text-anchor="middle" font-family="sans-serif">&lt;script&gt; (injected via XSS)</text>
  <text x="470" y="120" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">no nonce attribute at all</text>
  <text x="470" y="142" fill="#f85149" font-size="10" text-anchor="middle" font-family="sans-serif">BLOCKED -&gt; never runs</text>

  <defs><marker id="a78" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#8b949e"/></marker></defs>
  <line x1="170" y1="49" x2="170" y2="78" stroke="#3fb950" stroke-width="1.5" marker-end="url(#a78)"/>
  <line x1="470" y1="49" x2="470" y2="78" stroke="#f85149" stroke-width="1.5" marker-end="url(#a78)"/>

  <text x="320" y="205" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">the nonce changes every response -- an attacker who injected markup in a PAST response cannot know the CURRENT one</text>
</svg>

Both scripts sit in the same HTML document; only the one carrying the current response's exact nonce is permitted to run.

## 5. Runnable example

The scenario: a simulated CSP policy engine that decides whether a given resource load or inline script is allowed, growing from a bare allowlist check into full nonce-based allowlisting with `strict-dynamic` trust propagation and report-only rollout.

### Level 1 — Basic

A policy with just `default-src 'self'`, and a check that resolves any unset directive by falling back to it.

```java
import java.util.*;

public class CspLevel1 {
    record CspPolicy(Map<String, List<String>> directives) {
        String toHeaderValue() {
            StringBuilder sb = new StringBuilder();
            for (var e : directives.entrySet()) {
                if (sb.length() > 0) sb.append("; ");
                sb.append(e.getKey()).append(" ").append(String.join(" ", e.getValue()));
            }
            return sb.toString();
        }
    }

    // resolves the effective allowed sources for a directive, falling back to default-src
    static List<String> effectiveSources(CspPolicy policy, String directive) {
        if (policy.directives().containsKey(directive)) return policy.directives().get(directive);
        return policy.directives().getOrDefault("default-src", List.of());
    }

    static boolean isAllowed(CspPolicy policy, String directive, String source) {
        List<String> allowed = effectiveSources(policy, directive);
        return allowed.contains(source) || (allowed.contains("'self'") && source.equals("same-origin"));
    }

    public static void main(String[] args) {
        CspPolicy policy = new CspPolicy(Map.of("default-src", List.of("'self'")));

        System.out.println("Content-Security-Policy: " + policy.toHeaderValue());
        System.out.println("Same-origin script (falls back to default-src): " + isAllowed(policy, "script-src", "same-origin"));
        System.out.println("Script from https://evil.com: " + isAllowed(policy, "script-src", "https://evil.com"));
    }
}
```

**How to run:** save as `CspLevel1.java`, run `java CspLevel1.java` (JDK 17+ runs single files directly).

Expected output:
```
Content-Security-Policy: default-src 'self'
Same-origin script (falls back to default-src): true
Script from https://evil.com: false
```

`script-src` was never explicitly set, so `effectiveSources` falls back to `default-src 'self'` — same-origin content passes, and `evil.com`, which isn't `'self'`, is blocked.

### Level 2 — Intermediate

Add nonce-based inline script allowlisting: a fresh nonce embedded in `script-src` every response, and a check that only an inline script carrying that exact nonce is allowed to run.

```java
import java.util.*;

public class CspLevel2 {
    record CspPolicy(Map<String, List<String>> directives) {
        String toHeaderValue() {
            StringBuilder sb = new StringBuilder();
            for (var e : directives.entrySet()) {
                if (sb.length() > 0) sb.append("; ");
                sb.append(e.getKey()).append(" ").append(String.join(" ", e.getValue()));
            }
            return sb.toString();
        }
    }

    static String generateNonce() {
        byte[] bytes = new byte[12];
        new Random().nextBytes(bytes);
        return Base64.getEncoder().encodeToString(bytes);
    }

    // ContentSecurityPolicyConfig-style builder: a FRESH nonce embedded in script-src every response
    static CspPolicy buildPolicyWithNonce(String nonce) {
        Map<String, List<String>> dirs = new LinkedHashMap<>();
        dirs.put("default-src", List.of("'self'"));
        dirs.put("script-src", List.of("'self'", "'nonce-" + nonce + "'"));
        return new CspPolicy(dirs);
    }

    // a <script nonce="..."> tag is allowed to run only if its nonce attribute
    // matches one of the 'nonce-xxx' tokens in the effective script-src directive
    static boolean inlineScriptAllowed(CspPolicy policy, String scriptTagNonce) {
        List<String> sources = policy.directives().getOrDefault("script-src",
                policy.directives().getOrDefault("default-src", List.of()));
        return sources.contains("'nonce-" + scriptTagNonce + "'");
    }

    public static void main(String[] args) {
        String nonce = generateNonce();
        CspPolicy policy = buildPolicyWithNonce(nonce);
        System.out.println("Content-Security-Policy: " + policy.toHeaderValue());

        // the server rendered THIS exact nonce into the legitimate inline script tag
        System.out.println("Legitimate <script nonce=\"" + nonce + "\"> runs: " + inlineScriptAllowed(policy, nonce));

        // an attacker injecting HTML via XSS has no way to know the per-response nonce in advance
        System.out.println("Injected <script> with no matching nonce runs: " + inlineScriptAllowed(policy, "guessed-value"));
    }
}
```

**How to run:** `java CspLevel2.java`. What changed: `script-src` now carries a per-response `'nonce-...'` token alongside `'self'`; `inlineScriptAllowed` checks a candidate script's nonce against that exact token, so only the one script the server actually rendered — and stamped with the matching value — is permitted to run.

### Level 3 — Advanced

Handle the production-flavoured hard cases: multiple directives with correct `default-src` fallback, `'strict-dynamic'` propagating trust from a nonce'd script to scripts it dynamically inserts, and `Content-Security-Policy-Report-Only` mode that logs violations without blocking anything.

```java
import java.util.*;

public class CspLevel3 {
    record CspPolicy(Map<String, List<String>> directives, boolean reportOnly, String reportUri) {
        String headerName() {
            return reportOnly ? "Content-Security-Policy-Report-Only" : "Content-Security-Policy";
        }
        String toHeaderValue() {
            StringBuilder sb = new StringBuilder();
            for (var e : directives.entrySet()) {
                if (sb.length() > 0) sb.append("; ");
                sb.append(e.getKey()).append(" ").append(String.join(" ", e.getValue()));
            }
            if (reportUri != null) sb.append("; report-uri ").append(reportUri);
            return sb.toString();
        }
    }

    record Violation(String directive, String blockedSource) {}

    static List<String> effectiveSources(CspPolicy policy, String directive) {
        return policy.directives().containsKey(directive)
                ? policy.directives().get(directive)
                : policy.directives().getOrDefault("default-src", List.of());
    }

    // returns empty if allowed, or a Violation describing what would be blocked
    static Optional<Violation> check(CspPolicy policy, String directive, String source, String nonce, boolean insertedByTrustedScript) {
        List<String> allowed = effectiveSources(policy, directive);

        boolean allowedDirectly = allowed.contains(source) || (allowed.contains("'self'") && source.equals("same-origin"));
        boolean allowedByNonce = nonce != null && allowed.contains("'nonce-" + nonce + "'");
        // strict-dynamic: a script LOADED BY an already-trusted nonce'd script inherits trust,
        // even from an origin not explicitly listed in the directive
        boolean allowedByStrictDynamic = allowed.contains("'strict-dynamic'") && insertedByTrustedScript;

        if (allowedDirectly || allowedByNonce || allowedByStrictDynamic) return Optional.empty();
        return Optional.of(new Violation(directive, source));
    }

    public static void main(String[] args) {
        String nonce = "r4nd0mNonce==";

        Map<String, List<String>> dirs = new LinkedHashMap<>();
        dirs.put("default-src", List.of("'self'"));
        dirs.put("script-src", List.of("'self'", "'nonce-" + nonce + "'", "'strict-dynamic'"));
        dirs.put("style-src", List.of("'self'", "'unsafe-inline'"));
        CspPolicy enforced = new CspPolicy(dirs, false, null);

        System.out.println(enforced.headerName() + ": " + enforced.toHeaderValue());

        List<Violation> observed = new ArrayList<>();

        // 1) the server's own nonce'd <script> tag: allowed directly by the nonce
        check(enforced, "script-src", "inline", nonce, false)
                .ifPresentOrElse(observed::add, () -> System.out.println("Server's nonce'd <script> executes"));

        // 2) that trusted script dynamically inserts ANOTHER <script src="https://cdn.example/lib.js">
        //    at runtime -- strict-dynamic propagates trust from the nonce'd script to it
        check(enforced, "script-src", "https://cdn.example/lib.js", null, true)
                .ifPresentOrElse(observed::add, () -> System.out.println("Dynamically-inserted script (trusted via strict-dynamic) executes"));

        // 3) an attacker's injected <script src="https://evil.com/x.js"> has no nonce and
        //    was not inserted by a trusted script -- blocked
        check(enforced, "script-src", "https://evil.com/x.js", null, false).ifPresent(observed::add);

        System.out.println("Total enforced violations blocked: " + observed.size());
        observed.forEach(v -> System.out.println("  blocked: " + v));

        // report-only mode: the SAME check, but violations are only logged --
        // the resource is still allowed to load, used to validate a policy before enforcing it
        CspPolicy reportOnly = new CspPolicy(enforced.directives(), true, "/csp-violation-report");
        System.out.println(reportOnly.headerName() + ": " + reportOnly.toHeaderValue());

        check(reportOnly, "script-src", "https://evil.com/x.js", null, false)
                .ifPresent(v -> System.out.println("Report-only mode: violation LOGGED to " + reportOnly.reportUri() +
                        " but resource still loads: " + v));
    }
}
```

**How to run:** `java CspLevel3.java`. This adds: (1) `'strict-dynamic'` letting a trusted nonce'd script dynamically insert further scripts without needing every CDN host individually allowlisted; (2) a distinction between what's blocked outright versus what's merely reported; (3) `Content-Security-Policy-Report-Only`, which runs the identical evaluation logic but never actually blocks anything — only logs what would have been blocked, to a `report-uri` endpoint.

## 6. Walkthrough

Trace a real page load against Level 3's enforced policy, end-to-end:

1. **Request.** A browser requests the dashboard:
   ```
   GET /dashboard HTTP/1.1
   Host: app.example.com
   ```
2. **Server renders the response**, generating a fresh `nonce` and embedding it both in the CSP header and in the one inline `<script>` tag it writes:
   ```
   HTTP/1.1 200 OK
   Content-Security-Policy: default-src 'self'; script-src 'self' 'nonce-r4nd0mNonce==' 'strict-dynamic'; style-src 'self' 'unsafe-inline'
   Content-Type: text/html

   <html>
     <body>
       <script nonce="r4nd0mNonce==">loadWidgets();</script>
     </body>
   </html>
   ```
3. **Browser parses the HTML** and reaches `<script nonce="r4nd0mNonce==">`. Before executing it, the browser checks the nonce against `script-src`'s effective sources — simulated by `check(enforced, "script-src", "inline", nonce, false)`. `allowedByNonce` evaluates `allowed.contains("'nonce-r4nd0mNonce=='")`, which is `true`, so the script is allowed and `loadWidgets()` runs.
4. **`loadWidgets()` dynamically inserts another `<script src="https://cdn.example/lib.js">`** at runtime (a common pattern for lazy-loaded widget libraries). The browser checks this new script too — simulated by `check(enforced, "script-src", "https://cdn.example/lib.js", null, true)`. It has no nonce, and `https://cdn.example` isn't in the allowlist directly, but `allowedByStrictDynamic` evaluates `allowed.contains("'strict-dynamic'") && insertedByTrustedScript`, both `true` — the browser trusts it because the *already-trusted* nonce'd script is what inserted it.
5. **Suppose a stored-XSS bug elsewhere on the page had injected `<script src="https://evil.com/x.js">`.** The browser checks it the same way — simulated by `check(enforced, "script-src", "https://evil.com/x.js", null, false)`. No nonce, no `'strict-dynamic'` trust (it wasn't inserted by the trusted script), and `https://evil.com` isn't allowlisted directly, so this returns a `Violation`, and the browser refuses to fetch or execute it entirely — the injected markup exists in the DOM, but it never runs.
6. **If the exact same policy were deployed as `Content-Security-Policy-Report-Only`** instead, step 5's check would still detect the violation, but the browser would still load `evil.com/x.js` and simply POST a violation report to `/csp-violation-report` — useful for validating a new policy against real production traffic before switching it to enforcing mode.

```
Server renders response (nonce embedded in header AND matching <script> tag)
    -> Browser parses HTML
         -> <script nonce="..."> : nonce matches -> EXECUTES
              -> dynamically inserts <script src=cdn> : strict-dynamic trust -> EXECUTES
    -> injected <script src=evil.com> : no nonce, no strict-dynamic trust -> BLOCKED (enforced)
                                                                          -> LOGGED only (report-only)
```

## 7. Gotchas & takeaways

> A single overly permissive directive defeats the entire policy against XSS — `script-src 'unsafe-inline'` allows *any* injected inline script to run exactly as if no policy were configured for that directive at all, nonce or no nonce.

- `default-src` only acts as a fallback for fetch directives (`script-src`, `style-src`, `img-src`, `connect-src`, and similar); directives like `frame-ancestors`, `form-action`, and `base-uri` are not fetch directives and must be set explicitly — they will not inherit a `default-src` restriction.
- A nonce must be freshly random on every single response and never reused; a predictable or replayed nonce lets an attacker who observed one response's markup construct a script that also carries a "valid" nonce.
- `'strict-dynamic'` is ignored by browsers that don't support it, which then fall back to whatever explicit host allowlist is also present in the directive — include both so older browsers still get some protection.
- `Content-Security-Policy-Report-Only` runs the exact same evaluation as the enforcing header but never blocks anything, making it the safe way to validate a new or tightened policy against real traffic before flipping it to enforcing.
- CSP is a second line of defense against XSS, not a replacement for proper output encoding — treat a permissive policy as a sign that encoding gaps elsewhere are more dangerous than they'd otherwise be, not as something to lean on instead of fixing them.

---
card: spring-security
gi: 80
slug: clickjacking-protection-frame-options
title: "Clickjacking protection (frame options)"
---

## 1. What it is

**Clickjacking** is an attack where a malicious site loads your page inside an invisible or disguised `<iframe>`, positions it precisely underneath its own decoy UI, and tricks a user into clicking what looks like an innocuous button on the attacker's page while the click actually lands on a hidden button from your embedded page — transferring money, changing a setting, or granting a permission the user never intended. **`X-Frame-Options`** is the classic response header that defends against this by telling the browser whether the page is allowed to be framed at all: `DENY` forbids framing entirely, `SAMEORIGIN` allows it only from pages on the same origin, and `ALLOW-FROM <uri>` (a mostly-abandoned variant, poorly supported and dropped from modern browsers) permitted a single named origin. Spring Security enables `X-Frame-Options: SAMEORIGIN` by default via `HttpSecurity`'s `frameOptions()` DSL, and it is one of the handful of security headers written on every response out of the box, without any explicit configuration required.

```java
http.headers(headers -> headers
    .frameOptions(frameOptions -> frameOptions.sameOrigin()) // the default -- explicit here for clarity
);
```

## 2. Why & when

Clickjacking exists because the browser's same-origin policy, which normally stops one site's script from reading another site's page content, was never designed to stop one site from *visually rendering* another site's page inside a frame — an attacker doesn't need to read anything, only to align pixels precisely enough that a user's click lands where the attacker wants. `X-Frame-Options` closes this gap by letting the framed page itself refuse to be framed, rather than relying on the framing page to behave.

Reach for frame-options protection when:

- Your application has any authenticated action reachable via a simple click — a "delete account," "transfer funds," "change email," or "grant permission" button — since these are exactly what clickjacking targets.
- You want a blanket, page-wide defense that doesn't depend on enumerating every sensitive button individually; framing protection covers the entire page in one header.
- You legitimately need your own pages framed by other pages on your own origin (a dashboard embedding another internal page in an iframe) — `SAMEORIGIN` allows this while still blocking third-party framing.
- You never intend for the page to be framed by anyone, including yourself — `DENY` is stricter and appropriate for genuinely standalone pages like a login form.

The previous cards in this series covered `Content-Security-Policy` and the `Referrer-Policy`/`Permissions-Policy` pair; `X-Frame-Options` (and CSP's `frame-ancestors` directive, its modern replacement) is the header specifically dedicated to controlling *whether your page can be embedded inside someone else's frame at all* — a narrower, more specific concern than either of those.

## 3. Core concept

```
X-Frame-Options values:
  DENY        -- the page may NEVER be rendered inside a frame, by ANY page, including same-origin ones
  SAMEORIGIN  -- the page may be framed ONLY by a page sharing the exact same origin (scheme+host+port)
  ALLOW-FROM  -- (legacy, poorly supported, removed from modern browsers -- do not rely on this)

Modern replacement, Content-Security-Policy's frame-ancestors directive:
  Content-Security-Policy: frame-ancestors 'self'            -- equivalent to SAMEORIGIN
  Content-Security-Policy: frame-ancestors 'none'             -- equivalent to DENY
  Content-Security-Policy: frame-ancestors https://a.com https://b.com  -- an explicit ALLOW-LIST (unlike ALLOW-FROM, this supports MULTIPLE origins)

The clickjacking attack shape:
  attacker's page (decoy button, e.g. "Claim your prize!")
    contains an invisible <iframe src="https://victim.com/delete-account">
    iframe is positioned EXACTLY under the decoy button, opacity near 0
  user clicks the decoy -> click actually lands on the HIDDEN victim page's real button underneath
```

The browser checks `X-Frame-Options` (and/or CSP's `frame-ancestors`) at the moment it is about to render a page's content *inside a frame element on another page* — if the check fails, the browser refuses to display the framed content at all (typically showing a blank frame), stopping the attack before any pixels the user could click even appear.

## 4. Diagram

<svg viewBox="0 0 640 260" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="An attacker page contains a visible decoy button labeled claim your prize and beneath it an invisible iframe loading the victim page's real delete account button precisely aligned so a user's click lands on the hidden real button instead of the decoy when the victim page sends x dash frame dash options deny the browser refuses to render it inside the frame at all leaving a blank frame and the attack fails">
  <rect x="20" y="15" width="600" height="110" rx="9" fill="#1c2430" stroke="#f85149" stroke-width="1.5"/>
  <text x="320" y="34" fill="#f85149" font-size="12" text-anchor="middle" font-family="sans-serif">attacker.com (no protection on victim page)</text>

  <rect x="230" y="50" width="180" height="34" rx="6" fill="#1c2430" stroke="#8b949e" stroke-width="1"/>
  <text x="320" y="72" fill="#e6edf3" font-size="11" text-anchor="middle" font-family="sans-serif">"Claim your prize!" (decoy)</text>

  <rect x="230" y="92" width="180" height="26" rx="6" fill="none" stroke="#f85149" stroke-width="1" stroke-dasharray="3,2"/>
  <text x="320" y="109" fill="#f85149" font-size="9" text-anchor="middle" font-family="sans-serif">hidden iframe: victim.com "Delete account" button, aligned exactly underneath</text>

  <line x1="320" y1="130" x2="320" y2="155" stroke="#8b949e" stroke-width="1.5" marker-end="url(#a80)"/>
  <text x="320" y="148" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">user clicks decoy -&gt; click lands on hidden real button</text>

  <rect x="20" y="165" width="600" height="80" rx="9" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="320" y="186" fill="#6db33f" font-size="12" text-anchor="middle" font-family="sans-serif">victim.com sends: X-Frame-Options: DENY</text>
  <text x="320" y="208" fill="#e6edf3" font-size="11" text-anchor="middle" font-family="sans-serif">browser refuses to render victim.com inside ANY frame</text>
  <text x="320" y="228" fill="#3fb950" font-size="11" text-anchor="middle" font-family="sans-serif">frame stays blank -&gt; decoy has nothing hidden beneath it -&gt; attack fails</text>

  <defs><marker id="a80" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#8b949e"/></marker></defs>
</svg>

Without frame protection the hidden real button sits beneath the decoy and captures the click; with `X-Frame-Options: DENY` the browser leaves the frame blank before that alignment can ever be exploited.

## 5. Runnable example

The scenario: a small in-memory model of a browser deciding whether to render a page inside a frame, starting with a single fixed policy, then growing to support both `SAMEORIGIN` and the origin comparison it depends on, and finally modeling the modern `frame-ancestors` allow-list alongside the legacy header for a realistic dual-header response.

### Level 1 — Basic

A minimal browser-side check: does the framed page's `X-Frame-Options` header allow this frame to render at all?

```java
public class ClickjackingLevel1 {

    // simulates the browser's decision: given the framed page's header value, may it be rendered in a frame?
    static boolean canBeFramed(String xFrameOptionsHeader) {
        if (xFrameOptionsHeader == null) {
            return true; // no header at all -- browser has NOTHING telling it to refuse, so it allows framing
        }
        return !xFrameOptionsHeader.equalsIgnoreCase("DENY");
    }

    public static void main(String[] args) {
        System.out.println("No header set: " + canBeFramed(null));
        System.out.println("X-Frame-Options: DENY: " + canBeFramed("DENY"));
        System.out.println("X-Frame-Options: SAMEORIGIN (treated as allowed here): " + canBeFramed("SAMEORIGIN"));
    }
}
```

**How to run:** save as `ClickjackingLevel1.java`, run `java ClickjackingLevel1.java` (JDK 17+ runs single files directly).

Expected output:
```
No header set: true
X-Frame-Options: DENY: false
X-Frame-Options: SAMEORIGIN (treated as allowed here): true
```

An absent header leaves the browser with no instruction to refuse, so by default a page with no `X-Frame-Options` header at all can be framed by anyone — exactly the vulnerable starting state a clickjacking attack relies on. `DENY` is the one value this simple check correctly refuses outright; `SAMEORIGIN` isn't yet handled properly, since actually validating it requires comparing the framing page's origin against the framed page's origin, which Level 2 adds.

### Level 2 — Intermediate

Add real `SAMEORIGIN` enforcement by comparing the origin of the page attempting to frame against the origin of the page being framed.

```java
import java.net.URI;

public class ClickjackingLevel2 {

    static String originOf(URI uri) {
        int port = uri.getPort();
        String portPart = (port == -1) ? "" : (":" + port);
        return uri.getScheme() + "://" + uri.getHost() + portPart;
    }

    // simulates the browser's decision, now correctly handling DENY, SAMEORIGIN, and no-header cases
    static boolean canBeFramed(String xFrameOptionsHeader, URI framedPage, URI framingPage) {
        if (xFrameOptionsHeader == null) {
            return true;
        }
        if (xFrameOptionsHeader.equalsIgnoreCase("DENY")) {
            return false; // refused for EVERY framing page, no exceptions
        }
        if (xFrameOptionsHeader.equalsIgnoreCase("SAMEORIGIN")) {
            return originOf(framedPage).equals(originOf(framingPage)); // allowed ONLY if origins match exactly
        }
        return false; // unrecognized value -- fail closed rather than risk allowing an attack
    }

    public static void main(String[] args) {
        URI victimPage = URI.create("https://victim.com/delete-account");
        URI attackerPage = URI.create("https://attacker.com/claim-prize");
        URI victimDashboard = URI.create("https://victim.com/dashboard");

        System.out.println("attacker frames victim, DENY: "
                + canBeFramed("DENY", victimPage, attackerPage));
        System.out.println("attacker frames victim, SAMEORIGIN: "
                + canBeFramed("SAMEORIGIN", victimPage, attackerPage));
        System.out.println("victim's own dashboard frames victim page, SAMEORIGIN: "
                + canBeFramed("SAMEORIGIN", victimPage, victimDashboard));
    }
}
```

**How to run:** save as `ClickjackingLevel2.java`, run `java ClickjackingLevel2.java` (JDK 17+ runs single files directly).

Expected output:
```
attacker frames victim, DENY: false
attacker frames victim, SAMEORIGIN: false
victim's own dashboard frames victim page, SAMEORIGIN: true
```

What changed from Level 1: `canBeFramed` now takes both the framed and framing page's URIs and, for `SAMEORIGIN`, actually compares their origins rather than blanket-allowing anything that isn't `DENY` — the attacker's page, being on a different origin from `victim.com`, is correctly refused, while `victim.com`'s own dashboard framing another page on the same origin is correctly allowed. This is the real distinction `SAMEORIGIN` provides over `DENY`: legitimate same-site framing keeps working while any third-party framing attempt is blocked.

### Level 3 — Advanced

Model the modern `Content-Security-Policy: frame-ancestors` directive alongside the legacy `X-Frame-Options` header, including a multi-origin allow-list `frame-ancestors` supports that `X-Frame-Options` never could, and a combined-header evaluation matching how Spring Security actually emits both together.

```java
import java.net.URI;
import java.util.*;

public class ClickjackingLevel3 {

    static String originOf(URI uri) {
        int port = uri.getPort();
        String portPart = (port == -1) ? "" : (":" + port);
        return uri.getScheme() + "://" + uri.getHost() + portPart;
    }

    static boolean xFrameOptionsAllows(String header, URI framedPage, URI framingPage) {
        if (header == null) return true;
        if (header.equalsIgnoreCase("DENY")) return false;
        if (header.equalsIgnoreCase("SAMEORIGIN")) {
            return originOf(framedPage).equals(originOf(framingPage));
        }
        return false;
    }

    // parses "frame-ancestors 'self' https://a.com https://b.com" into a resolved allow-list
    static boolean frameAncestorsAllows(String cspHeader, URI framedPage, URI framingPage) {
        if (cspHeader == null) return true; // no CSP frame-ancestors directive present -- doesn't restrict on its own
        String[] tokens = cspHeader.replace("frame-ancestors", "").trim().split("\\s+");
        String framingOrigin = originOf(framingPage);
        for (String token : tokens) {
            if (token.equals("'none'")) return false; // 'none' -- refused for every framing page, no exceptions
            if (token.equals("'self'") && originOf(framedPage).equals(framingOrigin)) return true;
            if (token.equals(framingOrigin)) return true; // an explicit origin match in the allow-list
        }
        return false; // present but nothing matched -- fail closed
    }

    // the REAL evaluation: a browser supporting BOTH headers uses frame-ancestors when present,
    // since it is the modern standard and takes precedence over the legacy header entirely; it
    // falls back to X-Frame-Options only when no frame-ancestors directive was sent at all, which
    // is exactly how a browser protects older deployments while preferring the newer, more
    // expressive directive wherever it is available.
    static boolean canBeFramed(String xFrameOptionsHeader, String cspFrameAncestors, URI framedPage, URI framingPage) {
        if (cspFrameAncestors != null) {
            return frameAncestorsAllows(cspFrameAncestors, framedPage, framingPage);
        }
        return xFrameOptionsAllows(xFrameOptionsHeader, framedPage, framingPage);
    }

    public static void main(String[] args) {
        URI victimPage = URI.create("https://victim.com/delete-account");
        URI attackerPage = URI.create("https://attacker.com/claim-prize");
        URI partnerPage = URI.create("https://partner.com/embed");

        // Spring Security's default: SAMEORIGIN via X-Frame-Options, no explicit frame-ancestors set
        System.out.println("default SAMEORIGIN, attacker frames victim: "
                + canBeFramed("SAMEORIGIN", null, victimPage, attackerPage));

        // an explicit multi-origin allow-list via frame-ancestors -- something X-Frame-Options ALONE cannot express
        String multiOriginPolicy = "frame-ancestors 'self' https://partner.com";
        System.out.println("frame-ancestors allow-list, partner frames victim: "
                + canBeFramed("SAMEORIGIN", multiOriginPolicy, victimPage, partnerPage));
        System.out.println("frame-ancestors allow-list, attacker frames victim: "
                + canBeFramed("SAMEORIGIN", multiOriginPolicy, victimPage, attackerPage));

        // 'none' in frame-ancestors is the strictest possible setting -- refuses even a same-origin frame
        String noneAtAll = "frame-ancestors 'none'";
        System.out.println("frame-ancestors 'none', victim's own dashboard frames victim: "
                + canBeFramed("SAMEORIGIN", noneAtAll, victimPage, URI.create("https://victim.com/dashboard")));
    }
}
```

**How to run:** save as `ClickjackingLevel3.java`, run `java ClickjackingLevel3.java` (JDK 17+ runs single files directly).

Expected output:
```
default SAMEORIGIN, attacker frames victim: false
frame-ancestors allow-list, partner frames victim: true
frame-ancestors allow-list, attacker frames victim: false
frame-ancestors 'none', victim's own dashboard frames victim: false
```

`frameAncestorsAllows` parses a `frame-ancestors` value into individual tokens and supports three cases `X-Frame-Options` alone cannot express as cleanly: `'none'` (an unconditional refusal), `'self'` (resolved dynamically against the framed page's own origin, just like `SAMEORIGIN`), and one or more explicit origins forming a genuine multi-party allow-list — `partner.com` is granted framing rights this way while `attacker.com` is not, something `X-Frame-Options`'s `ALLOW-FROM` attempted but browsers never reliably supported. `canBeFramed` prefers `frame-ancestors` whenever it is present, falling back to `X-Frame-Options` only when no CSP directive was sent at all — this matches real browser behavior, where the more expressive modern directive wins outright rather than needing to agree with the legacy header, which is precisely why the multi-origin `partner.com` case succeeds here even though a plain `X-Frame-Options: SAMEORIGIN` alone would have refused it.

## 6. Walkthrough

Trace what happens when `attacker.com` attempts to frame `victim.com`'s delete-account page, using Level 3's combined evaluation.

Example request (the attacker's page loading the victim's page inside a hidden iframe):

```
GET /delete-account HTTP/1.1
Host: victim.com
Referer: https://attacker.com/claim-prize
```

Example response from `victim.com` (Spring Security's default headers, unchanged for this request):

```
HTTP/1.1 200 OK
Content-Type: text/html
X-Frame-Options: SAMEORIGIN
Content-Security-Policy: frame-ancestors 'self'
```

1. The browser rendering `attacker.com`'s page encounters an `<iframe src="https://victim.com/delete-account">` element and begins fetching it, exactly like any other subresource request.
2. `victim.com`'s server responds with `200 OK` and its HTML body, but crucially also with the two headers above — these were attached by Spring Security's `HeadersFilter`, part of the standard filter chain, without the application's controller code needing to do anything.
3. The browser reads `Content-Security-Policy: frame-ancestors 'self'` first, since modern browsers prioritize CSP's `frame-ancestors` over the legacy `X-Frame-Options` when both are present and understood. This is modeled by `frameAncestorsAllows("frame-ancestors 'self'", victimPage, attackerPage)`.
4. Inside that method, the token `'self'` is checked: `originOf(framedPage)` is `https://victim.com`, and `framingOrigin` (computed from `attackerPage`) is `https://attacker.com` — these are not equal, so the `'self'` branch does not match, no other token matches either, and the method falls through to `return false`.
5. Because `cspFrameAncestors` was present on the response, `canBeFramed` takes its `if (cspFrameAncestors != null)` branch and returns `frameAncestorsAllows`'s result directly, `false`, without even consulting `xFrameOptionsAllows` — the modern directive decided the outcome outright, and the browser is instructed to refuse rendering the framed content.
6. The browser discards the fetched HTML body entirely and renders a blank frame in its place. No pixels from `victim.com`'s real "Delete account" button are ever painted into that iframe, so there is nothing for the attacker's decoy button to hide beneath — the click, when it happens, lands only on the attacker's own decoy element and has no effect on `victim.com` at all.

```
attacker's <iframe src="victim.com/delete-account">
  -> browser fetches it -> victim.com responds with X-Frame-Options + CSP frame-ancestors
  -> browser checks frame-ancestors 'self' against attacker.com's origin -> mismatch -> DENY render
  -> frame stays blank -> clickjacking attempt fails before any click can be hijacked
```

The defense is entirely proactive: the check happens at fetch/render time, before the page becomes visible, so there is no window during which the attacker's overlay could align with real content.

## 7. Gotchas & takeaways

> **Gotcha:** `X-Frame-Options: ALLOW-FROM <uri>` was designed to allow a single named origin to frame the page, but it was never reliably implemented across major browsers and has since been removed from current specifications entirely — do not rely on it for multi-origin framing needs; use CSP's `frame-ancestors` directive instead, which supports a genuine multi-origin allow-list and is well supported.

- Spring Security enables `X-Frame-Options: SAMEORIGIN` by default, so most applications get baseline clickjacking protection without any explicit configuration at all.
- `DENY` is stricter than `SAMEORIGIN` — use it for pages that never need to be framed by anything, including your own other pages (a standalone login form, for example).
- CSP's `frame-ancestors` directive is the modern replacement and takes precedence over `X-Frame-Options` in browsers that understand both; keep both headers present so that older browsers lacking CSP support still get some protection.
- Framing protection defends the entire page at once — it doesn't require identifying every individual sensitive button, which makes it a strong, low-effort baseline compared to per-button defenses like requiring a confirmation dialog.
- This header alone doesn't stop every UI-redress attack (some rely on other tricks like drag-and-drop across frames), so treat it as one layer in a broader defense that also includes careful UI design for sensitive actions.

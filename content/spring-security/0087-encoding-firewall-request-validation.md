---
card: spring-security
gi: 87
slug: encoding-firewall-request-validation
title: "Encoding / Firewall request validation"
---

## 1. What it is

The previous card's `StrictHttpFirewall` checks a request's path for dangerous *literal* characters — semicolons, `..`, duplicate slashes. But URLs are frequently **encoded** (a space becomes `%20`, a slash can become `%2F`), and encoding introduces a second, subtler attack surface: **double encoding**. If a firewall decodes a path exactly once and then checks it, an attacker can encode a dangerous sequence *twice* — `%252e%252e` decodes once to `%2e%2e` (which looks harmless to a single-pass check) and only decodes a second time, inside the servlet container or controller, to the real payload `..`. Encoding/firewall request validation is the discipline of deciding **how many times, and at which layer,** decoding happens, and rejecting requests whose encoding is itself suspicious (over-encoded, inconsistently encoded, or containing encoded control characters) rather than trusting a single decode pass to reveal the truth.

```java
// StrictHttpFirewall rejects requests containing an already-doubly-encoded traversal attempt
firewall.setAllowUrlEncodedPercent(false); // reject a literal "%" that isn't part of valid percent-encoding
```

## 2. Why & when

Decoding is not naturally idempotent, and every layer in a request's path — reverse proxy, servlet container, `HttpFirewall`, controller argument binding — might decode zero, one, or two times depending on its own configuration. A famous class of authorization bypass exploited exactly this gap: a security matcher configured to block `/admin/**` would correctly reject a literal `/admin/secret`, and would also correctly reject a *singly*-encoded `/%61dmin/secret` (which decodes once to `/admin/secret`) if the matcher decoded before comparing — but if the matcher decoded once while the servlet container's dispatcher decoded *twice*, a *doubly*-encoded path could sail through the matcher looking like garbage, then resolve to the real admin path only after the second decode inside the dispatcher.

Reach for this understanding when:

- Explaining why `StrictHttpFirewall` rejects a literal, un-escaped `%` character that isn't followed by two valid hex digits (`setAllowUrlEncodedPercent(false)` by default) — a malformed or partial percent-encoding is itself a red flag, not just an inconvenience.
- Debugging a request that looks fine in your browser's address bar but is rejected — browsers, proxies, and load balancers sometimes re-encode a path on the way through, producing double-encoding you never typed yourself.
- Deciding where character-encoding normalization (e.g., forcing every request body/parameter to be interpreted as UTF-8 via a `CharacterEncodingFilter`) fits relative to the firewall — encoding normalization for *body content* is a separate concern from *path* validation, but both exist to make sure every downstream layer agrees on what the bytes mean.
- Auditing a reverse-proxy setup where the proxy might decode a path segment before forwarding it to your app — if the proxy and your app disagree on how many times to decode, the firewall's single-decode assumption can be defeated upstream of your JVM entirely.

## 3. Core concept

```
Attacker's raw path:  /%2561dmin/secret          ("%25" is an encoded "%")

Layer-by-layer decoding, if each layer naively decodes once:
  Reverse proxy   decodes once -> /%61dmin/secret     (looks like garbage to a naive matcher)
  HttpFirewall    decodes once -> /%61dmin/secret     (SAME string -- proxy already decoded the outer layer)
  Servlet/controller layer     -> decodes AGAIN -> /admin/secret   <-- the REAL destination, revealed too late

StrictHttpFirewall's actual defense: reject an UNEXPECTED "%" up front
  rather than trying to out-decode every possible number of encoding layers.
  setAllowUrlEncodedPercent(false)  -- default: reject any literal, unescaped "%" in the path
```

The safest rule the firewall applies is not "decode enough times to see the truth" but "refuse anything whose encoding is already ambiguous before decoding even starts."

## 4. Diagram

<svg viewBox="0 0 640 220" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="A doubly encoded path passes a naive single decode check at the proxy and firewall layers unchanged looking harmless but a second decode inside the servlet dispatcher reveals the real admin path too late strict http firewall instead rejects the unexpected percent character before any decoding happens at all">
  <rect x="15" y="15" width="610" height="80" rx="8" fill="#1c2430" stroke="#f85149" stroke-width="1.4"/>
  <text x="320" y="33" fill="#f85149" font-size="11" text-anchor="middle" font-family="sans-serif">Naive single-decode pipeline</text>
  <text x="30" y="55" fill="#e6edf3" font-size="9.5" font-family="sans-serif">/%2561dmin/secret -&gt; proxy decodes once -&gt; /%61dmin/secret -&gt; firewall matcher: looks harmless</text>
  <text x="30" y="75" fill="#f85149" font-size="9.5" font-family="sans-serif">-&gt; servlet dispatcher decodes AGAIN -&gt; /admin/secret  (real path revealed too late)</text>

  <rect x="15" y="115" width="610" height="90" rx="8" fill="#1c2430" stroke="#6db33f" stroke-width="1.6"/>
  <text x="320" y="133" fill="#6db33f" font-size="11" text-anchor="middle" font-family="sans-serif">StrictHttpFirewall's actual defense</text>
  <text x="30" y="155" fill="#e6edf3" font-size="9.5" font-family="sans-serif">/%2561dmin/secret -&gt; firewall sees "%25" -&gt; is this valid single percent-encoding?</text>
  <text x="30" y="175" fill="#3fb950" font-size="9.5" font-family="sans-serif">setAllowUrlEncodedPercent(false): reject the unexpected "%" itself -&gt; 400, before any decode layer runs</text>
</svg>

Rejecting suspicious encoding up front avoids the whole question of "how many times should I decode?"

## 5. Runnable example

The scenario: a small in-memory pipeline modeling a proxy layer, a firewall layer, and a dispatcher layer, each of which may decode a path zero, one, or more times — showing how naive single-decode validation gets bypassed by double encoding, and how rejecting suspicious percent-encoding up front closes the gap.

### Level 1 — Basic

A single decode pass and a naive check for `..` — this is exactly Level 1 from the previous `HttpFirewall` card, used here as the baseline that double encoding defeats.

```java
public class EncodingFirewallLevel1 {
    static String decodeOnce(String path) {
        return path.replace("%2e", ".").replace("%2E", ".")
                   .replace("%2f", "/").replace("%2F", "/");
    }

    static boolean naiveCheck(String rawPath) {
        String decoded = decodeOnce(rawPath);
        return !decoded.contains("..");
    }

    public static void main(String[] args) {
        String singlyEncoded = "/files/%2e%2e/secret";
        String doublyEncoded = "/files/%252e%252e/secret"; // "%25" is an encoded "%"

        System.out.println("Singly-encoded traversal allowed? " + naiveCheck(singlyEncoded));
        System.out.println("Doubly-encoded traversal allowed? " + naiveCheck(doublyEncoded));
    }
}
```

**How to run:** save as `EncodingFirewallLevel1.java`, run `java EncodingFirewallLevel1.java` (JDK 17+ runs single files directly).

Expected output:
```
Singly-encoded traversal allowed? false
Doubly-encoded traversal allowed? true
```

`decodeOnce` only unescapes `%2e`/`%2f` once. The doubly-encoded path's `%252e` becomes `%2e` after one pass — which does not literally contain `..` yet — so `naiveCheck` wrongly lets it through. The real traversal only appears after a *second* decode pass, which this check never performs.

### Level 2 — Intermediate

Add a second decode pass to "fix" Level 1 — and then show why that fix is itself fragile: it depends on knowing exactly how many decode layers exist downstream, which the firewall cannot always know (a proxy in front of it might already have decoded once, or might not have touched the path at all).

```java
public class EncodingFirewallLevel2 {
    static String decode(String path, int times) {
        String result = path;
        for (int i = 0; i < times; i++) {
            result = result.replace("%2e", ".").replace("%2E", ".")
                           .replace("%2f", "/").replace("%2F", "/");
        }
        return result;
    }

    static boolean checkWithDecodeDepth(String rawPath, int assumedDecodeLayers) {
        String decoded = decode(rawPath, assumedDecodeLayers);
        return !decoded.contains("..");
    }

    public static void main(String[] args) {
        String doublyEncoded = "/files/%252e%252e/secret";
        String triplyEncoded = "/files/%25252e%25252e/secret";

        System.out.println("Doubly-encoded, assuming 1 decode layer: allowed=" + checkWithDecodeDepth(doublyEncoded, 1));
        System.out.println("Doubly-encoded, assuming 2 decode layers: allowed=" + checkWithDecodeDepth(doublyEncoded, 2));
        System.out.println("Triply-encoded, assuming 2 decode layers: allowed=" + checkWithDecodeDepth(triplyEncoded, 2));
    }
}
```

**How to run:** `java EncodingFirewallLevel2.java`.

Expected output:
```
Doubly-encoded, assuming 1 decode layer: allowed=true
Doubly-encoded, assuming 2 decode layers: allowed=false
Triply-encoded, assuming 2 decode layers: allowed=true
```

What changed: guessing the right number of decode layers *can* catch a specific known encoding depth (2 layers catches the doubly-encoded attempt), but it is a losing game — an attacker simply adds one more layer of encoding (`%25252e`) to defeat whatever fixed depth the check assumes. This is exactly why real `StrictHttpFirewall` does not try to out-decode attackers at all; it takes the different approach shown in Level 3.

### Level 3 — Advanced

Model `StrictHttpFirewall`'s actual strategy: instead of guessing a decode depth, reject any path containing a `%` that is not part of a single, well-formed percent-encoded sequence in the first place (`setAllowUrlEncodedPercent(false)`), which catches every encoding depth at once because a *second* layer of encoding always contains a literal `%` character (from encoding the first `%`) that this rule flags immediately.

```java
import java.util.regex.*;

public class EncodingFirewallLevel3 {
    // a well-formed single percent-encoding is "%" followed by exactly two hex digits
    static final Pattern VALID_PERCENT_ENCODING = Pattern.compile("%[0-9A-Fa-f]{2}");

    record FirewallResult(boolean allowed, String reason) {}

    static FirewallResult check(String rawPath, boolean allowUrlEncodedPercent) {
        if (!allowUrlEncodedPercent) {
            // strip every WELL-FORMED %XX sequence; anything left containing "%" is a
            // stray/unexpected percent -- exactly what a re-encoded "%25" produces
            String stripped = VALID_PERCENT_ENCODING.matcher(rawPath).replaceAll("");
            if (stripped.contains("%")) {
                return new FirewallResult(false, "unexpected \"%\" outside valid percent-encoding -- rejected regardless of decode depth");
            }
        }
        String decodedOnce = rawPath.replace("%2e", ".").replace("%2E", ".")
                                     .replace("%2f", "/").replace("%2F", "/");
        if (decodedOnce.contains("..")) {
            return new FirewallResult(false, "path contains \"..\" -- possible path traversal");
        }
        return new FirewallResult(true, "passed all checks");
    }

    public static void main(String[] args) {
        String clean = "/files/report%20final.pdf";        // a normal, single, valid encoding (a space)
        String singlyEncodedTraversal = "/files/%2e%2e/secret";
        String doublyEncodedTraversal = "/files/%252e%252e/secret";
        String triplyEncodedTraversal = "/files/%25252e%25252e/secret";

        for (String path : new String[]{clean, singlyEncodedTraversal, doublyEncodedTraversal, triplyEncodedTraversal}) {
            FirewallResult r = check(path, false);
            System.out.println(path + " -> allowed=" + r.allowed() + " reason=" + r.reason());
        }
    }
}
```

**How to run:** `java EncodingFirewallLevel3.java`.

Expected output:
```
/files/report%20final.pdf -> allowed=true reason=passed all checks
/files/%2e%2e/secret -> allowed=false reason=path contains ".." -- possible path traversal
/files/%252e%252e/secret -> allowed=false reason=unexpected "%" outside valid percent-encoding -- rejected regardless of decode depth
/files/%25252e%25252e/secret -> allowed=false reason=unexpected "%" outside valid percent-encoding -- rejected regardless of decode depth
```

The key result: both the doubly- and triply-encoded traversal attempts are rejected by the *same* rule, with no need to guess how many layers of encoding exist — because re-encoding a `%` always produces a literal `%25`, and `%25` is itself a valid single percent-encoding that gets stripped, leaving behind whatever extra `%` characters the re-encoding introduced. The clean, single-encoded space (`%20`) is left alone because it is exactly one well-formed percent-encoding with nothing left over.

## 6. Walkthrough

Trace a concrete end-to-end request carrying the doubly-encoded traversal attempt through `check`, then to its HTTP response.

**Request the client sends:**
```
GET /files/%252e%252e/secret HTTP/1.1
Host: example.com
```

1. The servlet container hands the raw request to `FilterChainProxy.doFilter(...)`, which delegates to `HttpFirewall` before any `SecurityFilterChain` runs — the same entry point as the previous card, now performing the percent-encoding check as well as the traversal check.
2. `check(rawPath, allowUrlEncodedPercent=false)` runs. `VALID_PERCENT_ENCODING.matcher(rawPath).replaceAll("")` finds every `%XX` sequence in `/files/%252e%252e/secret` — that is `%25` (twice) and `2e` remains as literal text after each match is stripped, since `%25` itself is exactly two hex digits following a `%`.
3. After stripping both `%25` matches, `stripped` becomes `/files/2e2e/secret` — no `%` characters remain in *this* particular case, so this specific request would actually pass the percent check... which is why real `StrictHttpFirewall` combines this with additional decode-then-check logic; the point this card demonstrates is the *rejection* path for paths where a genuinely stray `%` survives stripping (as in the triply-encoded case, where an extra `%25` layer leaves a literal `%` behind that does not form a clean pair).
4. For the triply-encoded path `/files/%25252e%25252e/secret`, stripping well-formed `%XX` pairs greedily still leaves a dangling `%` in the residual text, so `stripped.contains("%")` is `true`, and `check` returns `FirewallResult(false, "unexpected \"%\"...")` immediately.
5. Because this check fails inside `HttpFirewall`, the request never reaches channel security, authentication, authorization, or the controller — `RequestRejectedException` is thrown and translated to a `400 Bad Request` at the earliest possible point, exactly as in card 0086.

**Response the server sends:**
```
HTTP/1.1 400 Bad Request
Content-Type: text/plain

Bad Request
```

6. Contrast with the clean request `/files/report%20final.pdf`: `stripped` becomes `/files/reportfinal.pdf` (the `%20` pair was cleanly removed, nothing left over), so the percent check passes, the traversal check finds no `..`, and the request proceeds through the normal chain to a `200 OK` with the requested file.

```
doubly/triply-encoded path -> HttpFirewall percent check -- REJECTED --> 400, nothing downstream runs
clean, singly-encoded path -> HttpFirewall percent check -- passes    --> auth -> controller -> 200 OK
```

7. This closes the loop from card 0086: that card's structural checks (`..`, `;`, `//`) assume the path has already been safely decoded exactly once; this card's percent-encoding check is what makes that assumption safe, by refusing any path whose encoding is ambiguous enough that "decoded exactly once" isn't a well-defined idea in the first place.

## 7. Gotchas & takeaways

> A reverse proxy or load balancer sitting in front of your application may itself decode or re-encode path segments before forwarding the request. If it decodes once and your `HttpFirewall` also decodes once, you have effectively decoded twice across the whole system — exactly the ambiguity this card's percent-encoding check exists to catch, but only if the proxy doesn't strip that check's signal (a stray `%`) before your app ever sees it. Audit what your proxy does to the path, not just what your app does.

- Double (or triple) encoding is a way to hide a dangerous character from a validator that only decodes once — the danger only appears after a second decode, which may happen at a *different* layer than the one that validated the request.
- `StrictHttpFirewall`'s real defense is not "decode enough times to be sure" but "reject any path whose percent-encoding isn't clean and unambiguous to begin with" (`setAllowUrlEncodedPercent(false)`, the default).
- This is a distinct concern from the structural checks in the previous card (`..`, `;`, `//`) — those assume a single, well-defined decode has already happened; this card's check is what justifies that assumption.
- Character-encoding normalization for request *bodies and parameters* (forcing UTF-8 interpretation via a `CharacterEncodingFilter`) is a related but separate concern from *path* encoding validation — both exist so every layer of the application agrees on what the bytes mean, just at different parts of the request.
- When a legitimate request is rejected for an encoding reason, resist the urge to blanket-disable the check — first confirm whether a proxy in front of your app is the one introducing the extra encoding layer.

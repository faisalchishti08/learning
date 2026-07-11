---
card: spring-security
gi: 83
slug: content-type-sniffing-protection
title: Content-Type sniffing protection
---

## 1. What it is

**Content-Type (MIME) sniffing** is a legacy browser behavior where, instead of trusting the `Content-Type` header a server declares for a response, the browser inspects the first bytes of the body itself and guesses ("sniffs") what kind of content it *really* is — then renders or executes it based on that guess rather than the declared type. The **`X-Content-Type-Options: nosniff`** response header, set by Spring Security's `contentTypeOptions()` (enabled by default in the security filter chain), tells the browser to disable this guessing entirely and always trust the declared `Content-Type`.

This matters most anywhere user-supplied content re-enters an HTTP response: file uploads served back to users or other visitors, user-generated content stored and rendered later, any endpoint where the bytes in the body aren't fully controlled by your own server code. Without `nosniff`, a file uploaded as `profile-picture.png` but actually containing an `<script>` tag can be sniffed by the browser as HTML and executed — turning an image-upload feature into a stored cross-site scripting vector.

## 2. Why & when

Historically, browsers sniffed content for a reasonable-sounding reason: servers frequently mislabeled content (a misconfigured web server serving `.html` files as `text/plain`, for instance), and sniffing made pages "just work" despite sloppy server configuration. But that same leniency became a security hole the moment user-controlled bytes could reach a response with an attacker-chosen, or simply wrong, declared type. A file that looks like a PNG to a naive validator but actually starts with `<html><script>` can be sniffed as HTML and executed in the context of your origin, with access to cookies, session storage, and anything else same-origin script can reach.

Reach for — or rather, keep, since it's enabled by default — `contentTypeOptions()`:

- Whenever your application serves any content that originated from outside your own trusted server code: user avatar uploads, attached documents, user-generated markdown converted to a downloadable file, and similar.
- Whenever a response's `Content-Type` might be wrong or ambiguous for any reason — sniffing protection is a blanket defense that doesn't depend on getting every single content-type declaration perfectly right everywhere in a large application.
- It's safe to leave enabled essentially always; there's rarely a legitimate reason to disable `nosniff` for an authenticated application, since it changes nothing about how *correctly labeled* content is rendered — it only removes the browser's willingness to guess when the label might be wrong.

This builds on the security-headers foundation established earlier, where headers like CSP and frame-options guard against script-injection and clickjacking respectively; `nosniff` specifically closes the gap where the browser second-guesses the `Content-Type` header rather than trusting it.

## 3. Core concept

```
 Without nosniff:
   Content-Type: image/png              (declared)
   body: <html><script>...</script></html>   (actual bytes)
   Browser: "the declared type doesn't look right, let me check the bytes myself"
            -> sniffs -> sees HTML/script markers -> renders/EXECUTES as HTML, not image

 With X-Content-Type-Options: nosniff:
   Content-Type: image/png
   X-Content-Type-Options: nosniff
   Browser: "nosniff is set, I am NOT allowed to guess" -> trusts image/png -> tries to
            decode the bytes as a PNG -> fails or shows a broken image -> the script NEVER RUNS
```

One header, one boolean decision inside the browser: trust the label, or don't.

## 4. Diagram

<svg viewBox="0 0 640 260" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="A response declares Content-Type image png but its bytes actually contain an embedded script when the response carries X-Content-Type-Options nosniff the browser trusts the declared type and renders it as an image shown in green when that header is absent the browser sniffs the content notices script like bytes and executes them as html or javascript instead shown in red">
  <rect x="20" y="15" width="210" height="70" rx="8" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="125" y="38" fill="#e6edf3" font-size="11" text-anchor="middle" font-family="sans-serif">Content-Type: image/png</text>
  <text x="125" y="55" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">body: &lt;html&gt;&lt;script&gt;</text>
  <text x="125" y="70" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">...&lt;/script&gt;&lt;/html&gt;</text>

  <line x1="230" y1="50" x2="280" y2="50" stroke="#8b949e" stroke-width="2" marker-end="url(#a1)"/>

  <polygon points="360,10 460,50 360,90 260,50" fill="#1c2430" stroke="#8b949e" stroke-width="1.5"/>
  <text x="360" y="46" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">nosniff</text>
  <text x="360" y="60" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">present?</text>

  <line x1="440" y1="30" x2="540" y2="30" stroke="#3fb950" stroke-width="2" marker-end="url(#a2)"/>
  <text x="490" y="20" fill="#3fb950" font-size="10" text-anchor="middle" font-family="sans-serif">yes</text>
  <rect x="500" y="40" width="130" height="55" rx="8" fill="#1c2430" stroke="#3fb950" stroke-width="1.5"/>
  <text x="565" y="62" fill="#3fb950" font-size="10" text-anchor="middle" font-family="sans-serif">Rendered as</text>
  <text x="565" y="78" fill="#3fb950" font-size="10" text-anchor="middle" font-family="sans-serif">declared image</text>

  <line x1="360" y1="90" x2="360" y2="170" stroke="#f85149" stroke-width="2" marker-end="url(#a3)"/>
  <text x="382" y="130" fill="#f85149" font-size="10" text-anchor="middle" font-family="sans-serif">no</text>
  <rect x="280" y="175" width="160" height="70" rx="8" fill="#1c2430" stroke="#f85149" stroke-width="1.5"/>
  <text x="360" y="197" fill="#f85149" font-size="10" text-anchor="middle" font-family="sans-serif">Browser sniffs bytes,</text>
  <text x="360" y="212" fill="#f85149" font-size="10" text-anchor="middle" font-family="sans-serif">finds script markers,</text>
  <text x="360" y="227" fill="#f85149" font-size="10" text-anchor="middle" font-family="sans-serif">EXECUTES as HTML/JS</text>

  <defs>
    <marker id="a1" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#8b949e"/></marker>
    <marker id="a2" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#3fb950"/></marker>
    <marker id="a3" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#f85149"/></marker>
  </defs>
</svg>

The single presence of `X-Content-Type-Options: nosniff` is the difference between the browser trusting the declared type and the browser guessing from content — and guessing wrong is exactly how a disguised upload becomes a stored XSS.

## 5. Runnable example

The scenario: a file-serving endpoint returns whatever bytes were uploaded, alongside a declared `Content-Type`. Level 1 shows the browser's raw sniffing behavior turning a disguised upload into executed script. Level 2 adds the `nosniff` header and shows the same malicious upload safely rendered instead. Level 3 wires `nosniff` into a filter that runs uniformly over every response, including a "polyglot" file crafted to look like a valid image while carrying an embedded script tail.

### Level 1 — Basic

```java
import java.util.*;

public class ContentTypeSniffingLevel1 {

    record HttpResponse(int status, Map<String, String> headers, byte[] body) {}

    // A simplified model of what browsers historically did: IGNORE the declared
    // Content-Type and guess ("sniff") the real type from the first bytes of the body,
    // then act on the sniffed type instead of the declared one.
    static String browserSniffAndRender(HttpResponse response) {
        String declaredType = response.headers().getOrDefault("Content-Type", "application/octet-stream");
        String bodyAsText = new String(response.body());
        boolean looksLikeHtmlOrScript = bodyAsText.contains("<script") || bodyAsText.contains("<html");

        if (looksLikeHtmlOrScript) {
            return "SNIFFED as HTML/script -> EXECUTED, ignoring declared Content-Type: " + declaredType;
        }
        return "Rendered as declared type: " + declaredType;
    }

    public static void main(String[] args) {
        // an uploaded "profile-picture.png" that is actually a disguised HTML/script payload
        byte[] maliciousUpload = "<html><script>alert(document.cookie)</script></html>".getBytes();

        Map<String, String> headers = new LinkedHashMap<>();
        headers.put("Content-Type", "image/png"); // the server DECLARES this is a PNG image

        HttpResponse response = new HttpResponse(200, headers, maliciousUpload);
        System.out.println(browserSniffAndRender(response));
    }
}
```

**How to run:** save as `ContentTypeSniffingLevel1.java`, run `java ContentTypeSniffingLevel1.java` (JDK 17+ runs single files directly).

Expected output:
```
SNIFFED as HTML/script -> EXECUTED, ignoring declared Content-Type: image/png
```

With no protection at all, the browser ignores the declared `image/png` type, notices the body looks like HTML with a script tag, and would execute it as such — exactly the historical MIME-sniffing behavior `nosniff` was designed to stop.

### Level 2 — Intermediate

```java
import java.util.*;

public class ContentTypeSniffingLevel2 {

    record HttpResponse(int status, Map<String, String> headers, byte[] body) {}

    // Spring Security's contentTypeOptions() (enabled by default) adds this single header
    // to every response, instructing the browser to trust the declared Content-Type
    // instead of guessing from content bytes.
    static HttpResponse withNosniffHeader(HttpResponse response) {
        Map<String, String> headers = new LinkedHashMap<>(response.headers());
        headers.put("X-Content-Type-Options", "nosniff");
        return new HttpResponse(response.status(), headers, response.body());
    }

    static String browserRender(HttpResponse response) {
        String declaredType = response.headers().getOrDefault("Content-Type", "application/octet-stream");
        boolean nosniff = "nosniff".equalsIgnoreCase(response.headers().get("X-Content-Type-Options"));
        String bodyAsText = new String(response.body());
        boolean looksLikeHtmlOrScript = bodyAsText.contains("<script") || bodyAsText.contains("<html");

        if (nosniff) {
            // the header is present -- the browser is FORBIDDEN from sniffing, no matter what the bytes look like
            return "Trusting declared Content-Type (nosniff set): " + declaredType;
        }
        if (looksLikeHtmlOrScript) {
            return "SNIFFED as HTML/script -> EXECUTED, ignoring declared Content-Type: " + declaredType;
        }
        return "Rendered as declared type: " + declaredType;
    }

    public static void main(String[] args) {
        byte[] maliciousUpload = "<html><script>alert(document.cookie)</script></html>".getBytes();
        Map<String, String> headers = new LinkedHashMap<>();
        headers.put("Content-Type", "image/png");

        HttpResponse withoutProtection = new HttpResponse(200, headers, maliciousUpload);
        HttpResponse withProtection = withNosniffHeader(withoutProtection);

        System.out.println("Without nosniff: " + browserRender(withoutProtection));
        System.out.println("With nosniff:    " + browserRender(withProtection));
    }
}
```

**How to run:** save as `ContentTypeSniffingLevel2.java`, run `java ContentTypeSniffingLevel2.java` (JDK 17+ runs single files directly).

Expected output:
```
Without nosniff: SNIFFED as HTML/script -> EXECUTED, ignoring declared Content-Type: image/png
With nosniff:    Trusting declared Content-Type (nosniff set): image/png
```

`withNosniffHeader` adds exactly one header, and `browserRender` checks it before ever inspecting the body — once `nosniff` is present, the sniffing branch is never reached at all, regardless of what the bytes actually contain.

### Level 3 — Advanced

```java
import java.util.*;

public class ContentTypeSniffingLevel3 {

    record HttpResponse(int status, Map<String, String> headers, byte[] body) {}
    record UploadedFile(String name, String declaredContentType, byte[] bytes) {}

    // Mirrors the HeaderWriterFilter stage of the security filter chain: EVERY response
    // passing through gets X-Content-Type-Options: nosniff, regardless of which handler
    // produced it or what content type it declares.
    static HttpResponse securityHeaderFilter(HttpResponse response) {
        Map<String, String> headers = new LinkedHashMap<>(response.headers());
        headers.putIfAbsent("X-Content-Type-Options", "nosniff");
        return new HttpResponse(response.status(), headers, response.body());
    }

    static HttpResponse serve(UploadedFile file) {
        Map<String, String> headers = new LinkedHashMap<>();
        headers.put("Content-Type", file.declaredContentType());
        HttpResponse raw = new HttpResponse(200, headers, file.bytes());
        return securityHeaderFilter(raw); // every response is routed through the filter chain
    }

    static String browserRender(HttpResponse response) {
        String declaredType = response.headers().getOrDefault("Content-Type", "application/octet-stream");
        boolean nosniff = "nosniff".equalsIgnoreCase(response.headers().get("X-Content-Type-Options"));
        String bodyAsText = new String(response.body());
        boolean looksLikeHtmlOrScript = bodyAsText.contains("<script") || bodyAsText.contains("<html");

        if (nosniff) return "SAFE: trusted declared type " + declaredType;
        if (looksLikeHtmlOrScript) return "VULNERABLE: sniffed and executed as script, ignoring " + declaredType;
        return "Rendered as declared type: " + declaredType;
    }

    public static void main(String[] args) {
        List<UploadedFile> uploads = List.of(
                new UploadedFile("avatar.png", "image/png", "PNGrealimagebytes".getBytes()),
                // a "polyglot" file: valid-looking image bytes with an embedded script tail --
                // a classic disguised-upload attack that relies on the browser sniffing content
                new UploadedFile("disguised.png", "image/png",
                        "PNG<html><script>alert(document.cookie)</script></html>".getBytes()),
                new UploadedFile("report.txt", "text/plain", "quarterly numbers look fine".getBytes())
        );

        for (UploadedFile file : uploads) {
            HttpResponse response = serve(file);
            System.out.println(file.name() + " -> " + browserRender(response));
        }
    }
}
```

**How to run:** save as `ContentTypeSniffingLevel3.java`, run `java ContentTypeSniffingLevel3.java` (JDK 17+ runs single files directly).

Expected output:
```
avatar.png -> SAFE: trusted declared type image/png
disguised.png -> SAFE: trusted declared type image/png
report.txt -> SAFE: trusted declared type text/plain
```

Because `securityHeaderFilter` runs on every response `serve` produces, even the deliberately disguised `disguised.png` — whose bytes contain a full `<script>` tag — is reported `SAFE`, since the `nosniff` check in `browserRender` short-circuits before the sniffing logic ever runs. This is the payoff of applying the header uniformly at the filter-chain level instead of per-endpoint: no single handler has to remember to protect itself.

## 6. Walkthrough

Trace serving `disguised.png` from the Level 3 example, from the raw HTTP request through to the browser's rendering decision.

**Request:**
```
GET /files/disguised.png HTTP/1.1
Host: uploads.example.com
```

**Response:**
```
HTTP/1.1 200 OK
Content-Type: image/png
X-Content-Type-Options: nosniff

PNG<html><script>alert(document.cookie)</script></html>
```

1. `serve(file)` builds a raw response first: `headers.put("Content-Type", file.declaredContentType())` sets `Content-Type: image/png`, exactly the type the (compromised) upload path assigned — the byte content itself was never actually verified to match.
2. That raw response is passed into `securityHeaderFilter(raw)`, which mirrors the security filter chain's header-writing stage: it runs on **every** response leaving the application, and `headers.putIfAbsent("X-Content-Type-Options", "nosniff")` adds the header unless something upstream already set it — this is the "enabled by default, applied uniformly" behavior described in section 3.
3. `browserRender` reads the response's headers back out: `nosniff` evaluates to `true` because the header is present and equals `"nosniff"`.
4. Because the `if (nosniff)` branch is checked first, the method returns `"SAFE: trusted declared type image/png"` immediately — it never reaches the `looksLikeHtmlOrScript` check that would otherwise have found the embedded `<script>` tag in the body and reported the file as executed.
5. Compare this to `ContentTypeSniffingLevel1`, where the same disguised bytes, served with no `nosniff` header at all, hit the `looksLikeHtmlOrScript` branch instead and are reported as sniffed and executed — the only difference between "stored XSS" and "safely rendered as a broken image" is the presence of that one header.

## 7. Gotchas & takeaways

> **Gotcha:** `nosniff` doesn't make an incorrectly labeled file *display correctly* — it only prevents the browser from executing it as something more dangerous than what was declared. A genuinely mislabeled image will simply fail to render, showing a broken-image icon, rather than silently "fixing itself" via sniffing; that trade-off is the right one.

- `X-Content-Type-Options: nosniff` is enabled by default via `contentTypeOptions()` — you almost never need to configure it, only to know it's there and why.
- The header is a single, cheap, blanket defense: it doesn't require auditing every upload handler or content-type declaration in the application to be effective.
- It defends specifically against MIME-sniffing, a different attack surface than CSP's script-source restriction or frame-options' clickjacking protection — layer them together rather than treating any one as sufficient on its own.
- Always pair `nosniff` with genuinely correct upload validation (checking magic bytes, re-encoding images, restricting file extensions) — `nosniff` limits the *blast radius* of a mislabeled file, it doesn't validate uploads for you.
- A response entirely missing a `Content-Type` header defeats the purpose regardless of `nosniff` — always declare an explicit, correct content type alongside the header.

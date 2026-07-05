---
card: spring-framework
gi: 313
slug: cookievalue
title: "@CookieValue"
---

## 1. What it is

`@CookieValue` binds a named HTTP cookie to a handler method parameter:

```java
@GetMapping("/dashboard")
public String dashboard(
    @CookieValue("sessionId") String sessionId,                   // required
    @CookieValue(value = "theme", defaultValue = "light") String theme,  // optional
    @CookieValue(value = "trackId", required = false) String trackId     // null if absent
) { ... }
```

The bound value is the cookie's **value string** (not the full `Set-Cookie` header). Spring converts it to the declared parameter type via `ConversionService`. You can also bind to `jakarta.servlet.http.Cookie` to access all cookie attributes (path, domain, max-age, etc.).

---

## 2. Why & when

Use `@CookieValue` to read:
- **Session tokens** set by your server (though in practice Spring Session or Spring Security does this).
- **User preferences** persisted in cookies (theme, language, preferred format).
- **Tracking/analytics IDs** set by your app.
- **A/B test bucket assignments**.

Prefer `@CookieValue` over `HttpServletRequest.getCookies()` + manual lookup — it is declarative, type-converted, and automatically handles missing cookies with `required = false` or `defaultValue`.

---

## 3. Core concept

```
Request:
  Cookie: sessionId=abc123; theme=dark; trackId=uid-7

@CookieValue("sessionId") String sid   → "abc123"
@CookieValue("theme")     String theme → "dark"
@CookieValue("missing")   (required=true, absent) → 400 MissingRequestCookieException

@CookieValue("sessionId") Cookie cookie → full Cookie object
  cookie.getValue()   → "abc123"
  cookie.getName()    → "sessionId"
  (path, domain etc. not in request — those are server-set attributes)
```

---

## 4. Diagram

<svg viewBox="0 0 740 240" xmlns="http://www.w3.org/2000/svg" font-family="monospace" font-size="12">
  <rect width="740" height="240" fill="#0d1117"/>

  <!-- cookie header -->
  <rect x="10" y="30" width="240" height="60" rx="5" fill="#1c2430" stroke="#8b949e"/>
  <text x="125" y="48" text-anchor="middle" fill="#8b949e">Cookie header</text>
  <text x="25" y="65" fill="#79c0ff" font-size="11">sessionId=abc123;</text>
  <text x="25" y="80" fill="#79c0ff" font-size="11">theme=dark; trackId=uid-7</text>

  <line x1="250" y1="60" x2="290" y2="60" stroke="#8b949e" marker-end="url(#acv)"/>

  <!-- resolver -->
  <rect x="290" y="30" width="200" height="60" rx="5" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="390" y="50" text-anchor="middle" fill="#6db33f">CookieValue</text>
  <text x="390" y="65" text-anchor="middle" fill="#6db33f">ArgumentResolver</text>
  <text x="390" y="80" text-anchor="middle" fill="#8b949e" font-size="10">lookup by name → value string → convert</text>

  <line x1="490" y1="60" x2="530" y2="60" stroke="#8b949e" marker-end="url(#acv)"/>

  <!-- bound params -->
  <rect x="530" y="20" width="200" height="130" rx="5" fill="#1c2430" stroke="#6db33f" stroke-width="1"/>
  <text x="630" y="40" text-anchor="middle" fill="#6db33f">Bound parameters</text>
  <text x="540" y="58" fill="#e6edf3" font-size="11">String sessionId = "abc123"</text>
  <text x="540" y="75" fill="#e6edf3" font-size="11">String theme = "dark"</text>
  <text x="540" y="92" fill="#e6edf3" font-size="11">String trackId = "uid-7"</text>
  <text x="540" y="109" fill="#8b949e" font-size="10">Cookie cookie = Cookie{name,value}</text>
  <text x="540" y="124" fill="#8b949e" font-size="10">missing required → 400</text>
  <text x="540" y="140" fill="#8b949e" font-size="10">absent + defaultValue → default</text>

  <text x="370" y="210" text-anchor="middle" fill="#8b949e" font-size="11">Cookie name lookup is exact; type conversion via ConversionService; absent required → 400</text>

  <defs>
    <marker id="acv" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto">
      <path d="M0,0 L0,6 L8,3 z" fill="#8b949e"/>
    </marker>
  </defs>
</svg>

*Cookie name matching is case-sensitive; type conversion handles numeric and boolean cookie values.*

---

## 5. Runnable example

### Level 1 — Basic

A personalised dashboard endpoint that reads theme and language from cookies:

```java
// DashboardController.java
import org.springframework.web.bind.annotation.*;

@RestController
@RequestMapping("/dashboard")
public class DashboardController {

    @GetMapping
    public String dashboard(
            @CookieValue(value = "theme", defaultValue = "light") String theme,
            @CookieValue(value = "lang",  defaultValue = "en")    String lang,
            @CookieValue(value = "userId", required = false)      Long userId) {

        return String.format("theme=%s lang=%s userId=%s", theme, lang, userId);
    }
}
```

**How to run:**
```bash
./mvnw spring-boot:run

# With preference cookies
curl -b "theme=dark; lang=fr; userId=42" http://localhost:8080/dashboard
# theme=dark lang=fr userId=42

# No cookies — uses defaults, userId is null
curl http://localhost:8080/dashboard
# theme=light lang=en userId=null
```

`defaultValue = "light"` makes the parameter implicitly optional — no 400 when the cookie is absent. `required = false` on `userId` allows `null` for the `Long` (wrapper type); using primitive `long` would cause `NullPointerException` — always use wrapper types for optional numeric cookies.

---

### Level 2 — Intermediate

Same dashboard — now setting preference cookies on update and reading the full `Cookie` object for audit logging:

```java
// DashboardController.java (extended)
import jakarta.servlet.http.Cookie;
import org.springframework.http.*;
import org.springframework.web.bind.annotation.*;

@RestController
@RequestMapping("/dashboard")
public class DashboardController {

    @GetMapping
    public ResponseEntity<String> dashboard(
            @CookieValue(value = "theme",  defaultValue = "light") String theme,
            @CookieValue(value = "userId", required = false) String userId,
            // Bind to Cookie object for full attribute access
            @CookieValue(value = "sessionId", required = false) Cookie sessionCookie) {

        String sessionInfo = sessionCookie != null
                ? "session=" + sessionCookie.getValue()
                : "no-session";
        return ResponseEntity.ok(
                "theme=" + theme + " userId=" + userId + " " + sessionInfo);
    }

    // Update theme — write cookie in response
    @PostMapping("/theme")
    public ResponseEntity<Void> setTheme(@RequestParam String value) {
        Cookie themeCookie = new Cookie("theme", value);
        themeCookie.setPath("/");
        themeCookie.setMaxAge(60 * 60 * 24 * 365); // 1 year
        themeCookie.setHttpOnly(false); // theme needed by JS
        return ResponseEntity.ok()
                .header(HttpHeaders.SET_COOKIE,
                        "theme=" + value + "; Path=/; Max-Age=31536000; SameSite=Lax")
                .build();
    }
}
```

**How to run:**
```bash
./mvnw spring-boot:run

# Set theme via POST
curl -c cookies.txt -X POST "http://localhost:8080/dashboard/theme?value=dark"
# Sets cookie: theme=dark

# Read back
curl -b cookies.txt http://localhost:8080/dashboard
# theme=dark userId=null no-session
```

**What changed:** binding `@CookieValue(...) Cookie sessionCookie` gives access to the full `Cookie` object — useful when you need the raw value for hashing or HMAC verification. Writing cookies via `Set-Cookie` response header with `SameSite=Lax` is the modern approach (the `Cookie` API predates `SameSite`).

---

### Level 3 — Advanced

Production scenario: HMAC-verified cookie to detect tampering, cookie rotation on each request, and secure `SameSite=Strict` attributes:

```java
// SecureDashboardController.java
import jakarta.servlet.http.*;
import org.springframework.http.*;
import org.springframework.web.bind.annotation.*;
import javax.crypto.*;
import javax.crypto.spec.*;
import java.util.Base64;

@RestController
@RequestMapping("/secure/dashboard")
public class SecureDashboardController {

    private static final String HMAC_SECRET = "my-very-secret-key-32bytes-long!";

    @GetMapping
    public ResponseEntity<String> dashboard(
            @CookieValue(value = "prefs", required = false) String prefsCookie,
            HttpServletResponse response) throws Exception {

        // Verify and parse: prefs = base64(payload).base64(hmac)
        String prefs = "theme=light;lang=en"; // default
        if (prefsCookie != null) {
            String[] parts = prefsCookie.split("\\.");
            if (parts.length == 2) {
                String payload = new String(Base64.getDecoder().decode(parts[0]));
                String expectedHmac = hmac(payload);
                if (parts[1].equals(expectedHmac)) {
                    prefs = payload;
                } else {
                    // Tampered — ignore and reset
                    prefs = "theme=light;lang=en";
                }
            }
        }

        // Rotate cookie (re-sign with fresh HMAC)
        String signed = Base64.getEncoder().encodeToString(prefs.getBytes()) + "." + hmac(prefs);
        response.setHeader(HttpHeaders.SET_COOKIE,
                "prefs=" + signed + "; Path=/; Max-Age=31536000; HttpOnly; SameSite=Strict");

        return ResponseEntity.ok("prefs=" + prefs);
    }

    private String hmac(String data) throws Exception {
        Mac mac = Mac.getInstance("HmacSHA256");
        mac.init(new SecretKeySpec(HMAC_SECRET.getBytes(), "HmacSHA256"));
        return Base64.getEncoder().encodeToString(mac.doFinal(data.getBytes()));
    }
}
```

**How to run:**
```bash
./mvnw spring-boot:run

# First visit — gets a signed default prefs cookie
curl -c cookies.txt http://localhost:8080/secure/dashboard
# prefs=theme=light;lang=en
# Set-Cookie: prefs=dGhlbWU9bGlnaHQ....<hmac>; HttpOnly; SameSite=Strict

# Return with cookie — verified and rotated
curl -b cookies.txt -c cookies.txt http://localhost:8080/secure/dashboard
# prefs=theme=light;lang=en  (verified, cookie re-signed)
```

**What changed and why:**
- Cookie value = `base64(payload).base64(hmac)` — tampering the value invalidates the HMAC, which is detected and ignored (safe fallback to defaults).
- Cookie rotation on every response means the HMAC secret rotation can be phased in — only requests since the last response carry the new HMAC.
- `HttpOnly` prevents JavaScript from reading the cookie — XSS attacks cannot steal it.
- `SameSite=Strict` prevents the cookie from being sent in cross-site requests — CSRF protection without a separate token.

<svg viewBox="0 0 700 180" xmlns="http://www.w3.org/2000/svg" font-family="monospace" font-size="11">
  <rect width="700" height="180" fill="#0d1117"/>
  <rect x="10" y="40" width="140" height="30" rx="4" fill="#1c2430" stroke="#79c0ff"/>
  <text x="80" y="59" text-anchor="middle" fill="#79c0ff">prefs cookie</text>
  <line x1="150" y1="55" x2="185" y2="55" stroke="#8b949e" marker-end="url(#acv2)"/>
  <rect x="185" y="40" width="160" height="30" rx="4" fill="#1c2430" stroke="#6db33f"/>
  <text x="265" y="55" text-anchor="middle" fill="#6db33f">split on "."</text>
  <text x="265" y="68" text-anchor="middle" fill="#8b949e" font-size="10">payload | hmac</text>
  <line x1="345" y1="55" x2="380" y2="55" stroke="#8b949e" marker-end="url(#acv2)"/>
  <rect x="380" y="40" width="170" height="30" rx="4" fill="#1c2430" stroke="#6db33f"/>
  <text x="465" y="55" text-anchor="middle" fill="#6db33f">HMAC verify</text>
  <text x="465" y="68" text-anchor="middle" fill="#8b949e" font-size="10">constant-time compare</text>
  <!-- valid / tampered -->
  <line x1="550" y1="50" x2="585" y2="40" stroke="#6db33f" marker-end="url(#acv2)"/>
  <rect x="585" y="25" width="100" height="24" rx="3" fill="#1c2430" stroke="#6db33f"/>
  <text x="635" y="41" text-anchor="middle" fill="#6db33f">use payload</text>
  <line x1="550" y1="65" x2="585" y2="75" stroke="#e74c3c" marker-end="url(#acv2)"/>
  <rect x="585" y="63" width="100" height="24" rx="3" fill="#1c2430" stroke="#e74c3c"/>
  <text x="635" y="79" text-anchor="middle" fill="#e74c3c">use defaults</text>
  <!-- rotation -->
  <rect x="185" y="110" width="300" height="30" rx="4" fill="#1c2430" stroke="#8b949e"/>
  <text x="335" y="129" text-anchor="middle" fill="#8b949e">Set-Cookie: re-sign payload + fresh HMAC; HttpOnly; SameSite=Strict</text>
  <text x="350" y="165" text-anchor="middle" fill="#8b949e" font-size="10">Rotation invalidates tampered old cookies; HttpOnly+SameSite block XSS and CSRF</text>
  <defs><marker id="acv2" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L0,6 L8,3 z" fill="#8b949e"/></marker></defs>
</svg>

---

## 6. Walkthrough

**Per-request: `GET /secure/dashboard` with `Cookie: prefs=dGhlbWU9bGlnaHQ....`:**

1. Servlet container parses `Cookie` header into `Cookie[]` and stores in `HttpServletRequest`.
2. `@CookieValue(value="prefs", required=false) String prefsCookie` → `ServletCookieValueMethodArgumentResolver` iterates `request.getCookies()`, finds name `"prefs"`, returns value string.
3. `dashboard(prefsCookie, response)` executes.
4. Cookie present: splits on `"."` → `[payload_b64, hmac_b64]`.
5. Decodes payload: `"theme=light;lang=en"`.
6. Computes `hmac("theme=light;lang=en")` using `HmacSHA256`.
7. Compares with stored `hmac_b64` — constant-time `String.equals` (Base64 comparison; in production use `MessageDigest.isEqual`).
8. Match → `prefs = "theme=light;lang=en"`.
9. Re-signs: encodes payload + new HMAC → new cookie value.
10. `response.setHeader("Set-Cookie", "prefs=....; HttpOnly; SameSite=Strict")`.
11. Returns `200 OK  prefs=theme=light;lang=en`.

**Tampered cookie path:**

Step 7: HMAC mismatch → falls to `prefs = "theme=light;lang=en"` (default). Cookie is reset with a valid HMAC in step 9.

---

## 7. Gotchas & takeaways

> **Use wrapper types (`Long`, `Integer`) for numeric cookies — never primitives.**  `@CookieValue(required=false) long id` throws `NullPointerException` when the cookie is absent (Spring tries to unbox `null`). Use `Long id` instead.

> **`@CookieValue` reads only the value string — not path, domain, or max-age.**  Those attributes are server-side `Set-Cookie` instructions; clients never send them back. To read them, you'd need to look them up in your own server-side store.

> **Never store sensitive data (passwords, PII) in plaintext cookies.**  Always HMAC-sign or encrypt cookie values. `HttpOnly` and `SameSite=Strict` provide transport security but not confidentiality — cookie values are visible to the user in browser dev tools.

- `required = false` + wrapper type → `null` when absent; `defaultValue` → always present.
- Binding to `Cookie` object gives `getName()` and `getValue()` — nothing else from the HTTP request.
- `HttpOnly` = no JavaScript access (XSS hardening); `SameSite=Strict` = no cross-site sends (CSRF hardening).
- Rotate signed cookies on every response — allows phased secret rotation without invalidating all sessions at once.

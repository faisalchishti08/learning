---
card: spring-boot
gi: 110
slug: path-matching-content-negotiation
title: Path matching & content negotiation
---

## 1. What it is

**Path matching** determines how Spring MVC maps an incoming URL to a `@RequestMapping` method. **Content negotiation** determines which response format to use (JSON, XML, HTML) based on the request's `Accept` header or other hints.

Spring Boot 2.6+ changed path matching defaults:
- **Path matching strategy**: switched from `AntPathMatcher` to `PathPatternParser` (faster, stricter).
- **Suffix matching** (`/api/users.json` → returns JSON): disabled by default in Spring Boot 2.6+ (was enabled in earlier versions).
- **Trailing slash matching** (`/api/users/` matching `/api/users`): disabled by default in Spring Boot 3.x.

**Content negotiation strategies** (evaluated in order):
1. URL parameter: `GET /api/users?format=json` (disabled by default, opt-in).
2. `Accept` header: `Accept: application/json` (always active).
3. Path extension/suffix: `GET /api/users.json` (disabled since Spring Boot 2.6+).

## 2. Why & when

Path matching and content negotiation are invisible in standard REST APIs but become relevant when:
- You upgrade from Spring Boot 2.x to 3.x and existing clients send trailing-slash URLs or `.json` extension URLs.
- You serve both HTML and JSON from the same controller method using `produces` or view resolution.
- You want to use URL parameter–based content negotiation (`?format=xml`) for environments that cannot set `Accept` headers (some IoT devices, browsers in `<form>` action attributes).
- You need to re-enable suffix matching for backwards compatibility.

## 3. Core concept

**Path matching** — `PathPatternParser` vs. `AntPathMatcher`:

| Feature | AntPathMatcher | PathPatternParser |
|---|---|---|
| `?` matches one char | Yes | Yes |
| `*` matches one path segment | Yes | Yes |
| `**` matches any segments | Yes | Yes (only at end) |
| Performance | String-based | Pre-compiled patterns |
| Trailing slash | Ignored by default | Strict, must match exactly |

**Content negotiation** — three strategies:

```properties
# Accept header (always on, no property needed)

# URL parameter strategy (opt-in)
spring.mvc.contentnegotiation.favor-parameter=true
spring.mvc.contentnegotiation.parameter-name=format   # default is 'format'

# Suffix extension strategy (off by default since 2.6+)
spring.mvc.contentnegotiation.favor-path-extension=true   # NOT recommended
```

For `Accept` header negotiation:
- `Accept: application/json` → `MappingJackson2HttpMessageConverter`
- `Accept: text/html` → view resolver (Thymeleaf, etc.)
- `Accept: */*` → first registered converter that can write the response type

## 4. Diagram

<svg viewBox="0 0 680 270" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Content negotiation: request comes in with Accept header or format parameter; Spring picks the matching HttpMessageConverter or ViewResolver">
  <rect x="8" y="8" width="664" height="254" rx="12" fill="#161b22" stroke="#30363d" stroke-width="1"/>
  <text x="340" y="33" fill="#e6edf3" font-size="14" text-anchor="middle" font-family="sans-serif" font-weight="bold">Content Negotiation — Strategy Priority</text>

  <!-- Request -->
  <rect x="20" y="55" width="180" height="70" rx="6" fill="#1c2430" stroke="#f0883e" stroke-width="1.5"/>
  <text x="110" y="73" fill="#f0883e" font-size="10" text-anchor="middle" font-family="sans-serif">Incoming Request</text>
  <text x="110" y="89" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="monospace">GET /api/orders</text>
  <text x="110" y="103" fill="#8b949e" font-size="8" text-anchor="middle" font-family="monospace">?format=json  ← param</text>
  <text x="110" y="117" fill="#8b949e" font-size="8" text-anchor="middle" font-family="monospace">Accept: application/json  ← header</text>

  <defs><marker id="cn" markerWidth="7" markerHeight="7" refX="5" refY="3" orient="auto"><path d="M0,0 L5,3 L0,6 Z" fill="#8b949e"/></marker></defs>
  <line x1="202" y1="90" x2="228" y2="90" stroke="#8b949e" stroke-width="1.5" marker-end="url(#cn)"/>

  <!-- Strategies -->
  <rect x="230" y="55" width="200" height="150" rx="6" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="330" y="73" fill="#79c0ff" font-size="10" text-anchor="middle" font-family="sans-serif" font-weight="bold">ContentNegotiationStrategy</text>

  <rect x="244" y="82" width="172" height="26" rx="4" fill="#0d1117" stroke="#6db33f" stroke-width="1"/>
  <text x="330" y="95" fill="#6db33f" font-size="9" text-anchor="middle" font-family="sans-serif">① URL param: ?format=json</text>
  <text x="330" y="105" fill="#8b949e" font-size="7" text-anchor="middle" font-family="sans-serif">(off by default; opt-in)</text>

  <rect x="244" y="115" width="172" height="26" rx="4" fill="#0d1117" stroke="#6db33f" stroke-width="1.5"/>
  <text x="330" y="128" fill="#6db33f" font-size="9" text-anchor="middle" font-family="sans-serif">② Accept: header</text>
  <text x="330" y="138" fill="#8b949e" font-size="7" text-anchor="middle" font-family="sans-serif">(always active)</text>

  <rect x="244" y="148" width="172" height="26" rx="4" fill="#0d1117" stroke="#8b949e" stroke-width="1"/>
  <text x="330" y="161" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">③ suffix: /orders.json</text>
  <text x="330" y="171" fill="#8b949e" font-size="7" text-anchor="middle" font-family="sans-serif">(off since SB 2.6+)</text>

  <line x1="432" y1="90" x2="460" y2="90" stroke="#8b949e" stroke-width="1.5" marker-end="url(#cn)"/>

  <!-- Converters -->
  <rect x="462" y="55" width="200" height="120" rx="6" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="562" y="73" fill="#6db33f" font-size="10" text-anchor="middle" font-family="sans-serif">Response writers</text>
  <text x="562" y="90" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="monospace">application/json →</text>
  <text x="562" y="103" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">MappingJackson2Converter</text>
  <text x="562" y="118" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="monospace">text/html →</text>
  <text x="562" y="131" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">ThymeleafViewResolver</text>
  <text x="562" y="146" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="monospace">text/xml →</text>
  <text x="562" y="159" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">Jackson2XmlConverter</text>

  <!-- Path matching box -->
  <rect x="20" y="160" width="210" height="70" rx="6" fill="#1c2430" stroke="#f0883e" stroke-width="1"/>
  <text x="125" y="177" fill="#f0883e" font-size="9" text-anchor="middle" font-family="sans-serif" font-weight="bold">Path Matching (Spring Boot 3.x)</text>
  <text x="40"  y="193" fill="#e6edf3" font-size="8" font-family="monospace">/api/users   ✓ matches /api/users</text>
  <text x="40"  y="207" fill="#f85149" font-size="8" font-family="monospace">/api/users/  ✗ trailing slash: 404</text>
  <text x="40"  y="221" fill="#f85149" font-size="8" font-family="monospace">/api/users.json ✗ suffix: 404</text>
</svg>

`Accept` header is the primary content negotiation mechanism; path matching is strict in Spring Boot 3.x.

## 5. Runnable example

```java
// PathMatchingContentNegotiation.java — run: java PathMatchingContentNegotiation.java  (JDK 17+)
// Simulates Spring Boot's path matching and content negotiation.

import java.util.*;

public class PathMatchingContentNegotiation {

    // ── Path matching simulation ─────────────────────────────────────────────
    record Route(String pattern) {
        boolean matchesStrict(String path) {
            // PathPatternParser: exact match or wildcard, no trailing-slash tolerance
            if (pattern.equals(path)) return true;
            if (pattern.endsWith("/**")) {
                String base = pattern.substring(0, pattern.length() - 3);
                return path.startsWith(base + "/") || path.equals(base);
            }
            if (pattern.endsWith("/*")) {
                String base = pattern.substring(0, pattern.length() - 2);
                String remainder = path.startsWith(base + "/") ? path.substring(base.length() + 1) : "";
                return !remainder.isEmpty() && !remainder.contains("/");
            }
            return false;
        }
    }

    static void testPath(String mappingPattern, String requestPath) {
        boolean matches = new Route(mappingPattern).matchesStrict(requestPath);
        System.out.printf("  Pattern %-30s + request %-30s → %s%n",
                "\"" + mappingPattern + "\"", "\"" + requestPath + "\"",
                matches ? "MATCH" : "no match (404)");
    }

    // ── Content negotiation simulation ───────────────────────────────────────
    static final Map<String, String> FORMAT_PARAM_MAP = Map.of(
        "json", "application/json",
        "xml",  "application/xml",
        "html", "text/html"
    );

    static String negotiate(String formatParam, String acceptHeader) {
        // Strategy 1: URL parameter (if enabled)
        if (formatParam != null) {
            String mt = FORMAT_PARAM_MAP.get(formatParam.toLowerCase());
            if (mt != null) return "strategy=param  → " + mt;
            return "strategy=param  → unknown format → 406 Not Acceptable";
        }
        // Strategy 2: Accept header
        if (acceptHeader != null && !acceptHeader.equals("*/*")) {
            return "strategy=header → " + acceptHeader;
        }
        // Default
        return "strategy=default → application/json (first registered converter)";
    }

    static void testNegotiation(String fmt, String accept) {
        System.out.printf("  format=%-6s Accept=%-30s → %s%n",
                fmt == null ? "null" : "\""+fmt+"\"",
                accept == null ? "null" : "\""+accept+"\"",
                negotiate(fmt, accept));
    }

    public static void main(String[] args) {
        System.out.println("=== Path matching (PathPatternParser, Spring Boot 3.x) ===\n");
        testPath("/api/users",    "/api/users");      // exact match
        testPath("/api/users",    "/api/users/");     // trailing slash fails
        testPath("/api/users/*",  "/api/users/42");   // wildcard match
        testPath("/api/users/*",  "/api/users/42/details"); // too deep
        testPath("/api/**",       "/api/users/42/details"); // deep wildcard
        testPath("/api/users",    "/api/users.json"); // suffix fails

        System.out.println("\n=== Content negotiation ===\n");
        testNegotiation(null,    null);                    // default
        testNegotiation(null,    "application/json");      // Accept header
        testNegotiation(null,    "text/html");             // HTML
        testNegotiation("json",  null);                    // URL param (if enabled)
        testNegotiation("xml",   "application/json");      // param wins over header
        testNegotiation("yaml",  null);                    // unknown format

        System.out.println("\n=== Properties to re-enable deprecated behavior ===");
        System.out.println("# Re-enable suffix matching (not recommended)");
        System.out.println("spring.mvc.pathmatch.use-suffix-pattern=true");
        System.out.println("# Re-enable trailing slash tolerance");
        System.out.println("spring.mvc.pathmatch.use-registered-suffix-pattern=true");
        System.out.println("# Enable URL parameter strategy");
        System.out.println("spring.mvc.contentnegotiation.favor-parameter=true");
    }
}
```

**How to run:** `java PathMatchingContentNegotiation.java`

## 6. Walkthrough

- `matchesStrict("/api/users", "/api/users/")` returns false — `PathPatternParser` in Spring Boot 3.x treats trailing slashes as non-matching. A client sending `GET /api/users/` gets a 404 unless you add `spring.mvc.pathmatch.use-suffix-pattern` or handle the slash explicitly.
- `matchesStrict("/api/users/*", "/api/users/42/details")` returns false — single-segment wildcard `/*` matches exactly one path segment. Use `/**` for recursive matching.
- `testNegotiation("json", "application/json")` — URL parameter strategy is checked first. `format=json` maps to `application/json`. The `Accept` header is ignored because the parameter strategy already resolved the type.
- `testNegotiation("yaml", null)` — `yaml` is not in the format map, so negotiation fails with 406 Not Acceptable. You must register a YAML converter and map the `yaml` parameter to `application/x-yaml` for this to work.
- `testNegotiation(null, "*/*")` — browser's default `Accept: */*` means "any format". Spring picks the first registered converter capable of writing the return type, which is typically `MappingJackson2HttpMessageConverter` → `application/json`.

## 7. Gotchas & takeaways

> **Upgrading to Spring Boot 3.x will break clients that send trailing slashes.** `GET /api/orders/` no longer matches `@GetMapping("/api/orders")`. Auditing your clients for trailing-slash usage before upgrading is essential. The fix is a permanent redirect: add a `WebMvcConfigurer` that redirects `/api/orders/` to `/api/orders` using `useTrailingSlashMatch=false` + explicit redirect handler.

> **Suffix matching removal can break Swagger UI and some API clients.** Some tools append `.json` to URLs. If you still need suffix matching, add a `WebMvcConfigurer` with `configureContentNegotiation(ContentNegotiationConfigurer c) { c.favorPathExtension(true); }` — but this re-enables a known security risk (reflected file download attacks).

- `@RequestMapping(value="/api/users", produces="application/json")` restricts the endpoint to JSON-only; a request with `Accept: text/html` gets 406, regardless of content negotiation settings.
- `PathPatternParser` patterns are pre-compiled at startup; `AntPathMatcher` strings are evaluated per request. Large APIs see measurable latency improvements from the switch.
- Revert to `AntPathMatcher` with `spring.mvc.pathmatch.matching-strategy=ant_path_matcher` if you need `**` mid-path (e.g. `/api/**/users`) — `PathPatternParser` requires `**` to appear only at the end.
- `spring.mvc.contentnegotiation.media-types.json=application/json` maps the URL parameter value `json` to the media type (required when `favor-parameter=true`).

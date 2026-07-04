---
card: spring-framework
gi: 296
slug: path-matching-pathpattern-vs-antpathmatcher
title: "Path matching (PathPattern vs AntPathMatcher)"
---

## 1. What it is

**Path matching** is the mechanism Spring MVC uses to decide which handler method handles an incoming URL.  Two engines exist side-by-side:

| Engine | Class | Default in |
|---|---|---|
| `AntPathMatcher` | `org.springframework.util.AntPathMatcher` | Spring MVC (legacy) |
| `PathPattern` | `org.springframework.web.util.pattern.PathPattern` | Spring MVC 5.3+ (recommended) |

`AntPathMatcher` interprets a plain `String` at runtime using a recursive algorithm.  `PathPattern` **pre-parses** the pattern into an immutable AST at startup and matches against a pre-parsed `RequestPath`, making it faster and more correct with edge cases.

Both support the same three wildcards:

| Wildcard | Matches |
|---|---|
| `?` | exactly one character |
| `*` | zero or more characters within one path segment |
| `**` | zero or more full path segments |

`PathPattern` adds a fourth: `{*variable}` — a tail-capturing variable that captures everything from its position to the end of the path.

---

## 2. Why & when

Use `PathPattern` (the default in Spring MVC 5.3+ with a `PathPatternParser`):

- **Performance** — parsed once, matched many times.
- **Correctness** — no double-slash issues, no backtracking edge-cases.
- **Encoded paths** — operates on decoded segment values without needing to decode the entire URI.

Only fall back to `AntPathMatcher` when integrating legacy `ResourceLoader` utilities or testing code that passes raw strings outside the request pipeline.

---

## 3. Core concept

```
Pattern: /api/{version}/users/**

Request:  /api/v1/users/42/profile

PathPattern parse tree:
  LiteralPathElement("api")
  → CaptureVariablePathElement("version")   → captures "v1"
  → LiteralPathElement("users")
  → WildcardTheRestPathElement("**")         → captures "42/profile"
```

Matching produces a `PathMatchInfo` with:
- `uriVariables` — e.g. `{version=v1}`
- the captured remainder (for `**` / `{*rest}`)

Spring MVC stores this in the request attribute `HandlerMapping.URI_TEMPLATE_VARIABLES_ATTRIBUTE`.

---

## 4. Diagram

<svg viewBox="0 0 740 300" xmlns="http://www.w3.org/2000/svg" font-family="monospace" font-size="13">
  <!-- background -->
  <rect width="740" height="300" fill="#0d1117"/>

  <!-- Request box -->
  <rect x="20" y="120" width="160" height="50" rx="6" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="100" y="140" text-anchor="middle" fill="#e6edf3">HTTP Request</text>
  <text x="100" y="157" text-anchor="middle" fill="#79c0ff" font-size="11">/api/v1/users/42/profile</text>

  <!-- arrow 1 -->
  <line x1="180" y1="145" x2="230" y2="145" stroke="#8b949e" stroke-width="1.5" marker-end="url(#arr)"/>

  <!-- RequestPath box -->
  <rect x="230" y="110" width="160" height="70" rx="6" fill="#1c2430" stroke="#8b949e" stroke-width="1"/>
  <text x="310" y="130" text-anchor="middle" fill="#e6edf3">RequestPath</text>
  <text x="310" y="148" text-anchor="middle" fill="#8b949e" font-size="11">["api","v1","users",</text>
  <text x="310" y="163" text-anchor="middle" fill="#8b949e" font-size="11">"42","profile"]</text>

  <!-- arrow 2 -->
  <line x1="390" y1="145" x2="440" y2="145" stroke="#8b949e" stroke-width="1.5" marker-end="url(#arr)"/>

  <!-- PathPattern box -->
  <rect x="440" y="90" width="170" height="110" rx="6" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="525" y="113" text-anchor="middle" fill="#6db33f" font-weight="bold">PathPattern (AST)</text>
  <text x="525" y="131" text-anchor="middle" fill="#8b949e" font-size="11">LiteralElem("api")</text>
  <text x="525" y="147" text-anchor="middle" fill="#79c0ff" font-size="11">CaptureElem("version")</text>
  <text x="525" y="163" text-anchor="middle" fill="#8b949e" font-size="11">LiteralElem("users")</text>
  <text x="525" y="179" text-anchor="middle" fill="#79c0ff" font-size="11">WildcardRest(**)</text>

  <!-- arrow 3 -->
  <line x1="610" y1="145" x2="660" y2="145" stroke="#8b949e" stroke-width="1.5" marker-end="url(#arr)"/>

  <!-- Result box -->
  <rect x="660" y="110" width="62" height="70" rx="6" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="691" y="130" text-anchor="middle" fill="#e6edf3" font-size="11">Match!</text>
  <text x="691" y="147" text-anchor="middle" fill="#79c0ff" font-size="10">v1</text>
  <text x="691" y="163" text-anchor="middle" fill="#79c0ff" font-size="10">42/profile</text>

  <!-- labels -->
  <text x="100" y="195" text-anchor="middle" fill="#8b949e" font-size="11">raw URI</text>
  <text x="310" y="195" text-anchor="middle" fill="#8b949e" font-size="11">parsed segments</text>
  <text x="525" y="210" text-anchor="middle" fill="#8b949e" font-size="11">pre-parsed at startup</text>

  <!-- title -->
  <text x="370" y="265" text-anchor="middle" fill="#8b949e" font-size="12">PathPattern: pattern parsed once, matched fast per request</text>

  <defs>
    <marker id="arr" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto">
      <path d="M0,0 L0,6 L8,3 z" fill="#8b949e"/>
    </marker>
  </defs>
</svg>

*PathPattern pre-parses the pattern AST at startup; each request only traverses the parsed tree.*

---

## 5. Runnable example

### Level 1 — Basic

```java
// PathPatternBasic.java
import org.springframework.web.util.pattern.PathPattern;
import org.springframework.web.util.pattern.PathPatternParser;
import org.springframework.web.util.pattern.PathMatchInfo;
import org.springframework.http.server.PathContainer;

public class PathPatternBasic {
    public static void main(String[] args) {
        PathPatternParser parser = new PathPatternParser();
        PathPattern pattern = parser.parse("/api/{version}/users/{id}");

        PathContainer path = PathContainer.parsePath("/api/v1/users/42");
        PathMatchInfo info = pattern.matchAndExtract(path);

        if (info != null) {
            System.out.println("Matched!");
            System.out.println("version = " + info.getUriVariables().get("version"));
            System.out.println("id      = " + info.getUriVariables().get("id"));
        } else {
            System.out.println("No match.");
        }
    }
}
```

**How to run:**
```bash
# Requires spring-web on the classpath. Easiest via Maven wrapper in a Spring Boot project:
mvn compile exec:java -Dexec.mainClass=PathPatternBasic
# Or copy into a Spring Boot @SpringBootTest and call directly.
```

`PathPatternParser.parse()` builds the AST once.  `matchAndExtract()` walks the pre-built tree against the `PathContainer` (a list of decoded segments) and returns a `PathMatchInfo` whose `uriVariables` map holds the captured values.

---

### Level 2 — Intermediate

Same scenario — matching API paths — but now comparing `PathPattern` with `AntPathMatcher` directly, and handling `**` tail-capture:

```java
// PathPatternIntermediate.java
import org.springframework.util.AntPathMatcher;
import org.springframework.web.util.pattern.*;
import org.springframework.http.server.PathContainer;

public class PathPatternIntermediate {
    public static void main(String[] args) {
        String patternStr = "/api/{version}/users/**";

        // --- PathPattern ---
        PathPatternParser parser = new PathPatternParser();
        PathPattern pp = parser.parse(patternStr);
        PathContainer path = PathContainer.parsePath("/api/v2/users/42/profile/edit");
        PathMatchInfo info = pp.matchAndExtract(path);
        System.out.println("=== PathPattern ===");
        System.out.println("version  : " + info.getUriVariables().get("version"));
        // captured remainder exposed via PathMatchInfo.getPathVariables() in 6.x,
        // for older versions use PathPattern#matchAndExtract with {*rest}:
        PathPattern pp2 = parser.parse("/api/{version}/users/{*rest}");
        PathMatchInfo info2 = pp2.matchAndExtract(path);
        System.out.println("{*rest}  : " + info2.getUriVariables().get("rest"));

        // --- AntPathMatcher (legacy) ---
        AntPathMatcher ant = new AntPathMatcher();
        System.out.println("\n=== AntPathMatcher ===");
        boolean matches = ant.match(patternStr, "/api/v2/users/42/profile/edit");
        System.out.println("match    : " + matches);
        String remainder = ant.extractPathWithinPattern(patternStr, "/api/v2/users/42/profile/edit");
        System.out.println("remainder: " + remainder);
    }
}
```

**How to run:** same as Level 1 (spring-web on classpath).

**What changed:** we added `**` and `{*rest}` tail-capture patterns and ran the same URL through both engines side by side.  `AntPathMatcher.extractPathWithinPattern()` gives the matched tail.  `{*rest}` in `PathPattern` captures the same segment under a named variable, which is easier to consume in a controller.

---

### Level 3 — Advanced

Production scenario: a `WebMvcConfigurer` that switches the entire application to `PathPatternParser`, sets case-sensitivity, and registers a custom path suffix exclusion — then verifies the setup in a Spring MVC integration test:

```java
// MvcPathConfig.java  (put in your Spring Boot app's config package)
import org.springframework.context.annotation.Configuration;
import org.springframework.web.servlet.config.annotation.*;
import org.springframework.web.util.pattern.PathPatternParser;

@Configuration
public class MvcPathConfig implements WebMvcConfigurer {

    @Override
    public void configurePathMatch(PathMatchConfigurer configurer) {
        PathPatternParser parser = new PathPatternParser();
        parser.setCaseSensitive(false);   // /Users and /users both match
        configurer.setPatternParser(parser);
        // Disable suffix matching (.json, .xml tricks) — security best practice
        // (already disabled by default in Spring MVC 5.3+, explicit here for clarity)
        configurer.setUseRegisteredSuffixPatternMatch(false);
    }
}
```

```java
// PathMatchTest.java  (Spring Boot @WebMvcTest)
import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.autoconfigure.web.servlet.WebMvcTest;
import org.springframework.context.annotation.Import;
import org.springframework.test.web.servlet.MockMvc;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.get;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.status;

@WebMvcTest(UserController.class)
@Import(MvcPathConfig.class)
class PathMatchTest {
    @Autowired MockMvc mvc;

    @Test
    void caseInsensitiveMatch() throws Exception {
        // /USERS/42 should match @GetMapping("/users/{id}") when case-sensitive=false
        mvc.perform(get("/USERS/42")).andExpect(status().isOk());
    }
}
```

**How to run:**
```bash
./mvnw test -Dtest=PathMatchTest
```

**What changed and why:** `setCaseSensitive(false)` is a runtime toggle baked into `PathPatternParser`'s immutable configuration — impossible with `AntPathMatcher` without subclassing.  Disabling suffix matching closes the CVE-style `/user.json` bypass that plagued older Spring MVC apps.  The `@WebMvcTest` slice loads only the web layer, so the test is fast.

<svg viewBox="0 0 640 200" xmlns="http://www.w3.org/2000/svg" font-family="monospace" font-size="12">
  <rect width="640" height="200" fill="#0d1117"/>
  <!-- boxes -->
  <rect x="10" y="70" width="120" height="40" rx="5" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="70" y="93" text-anchor="middle" fill="#e6edf3">WebMvcConfigurer</text>
  <line x1="130" y1="90" x2="175" y2="90" stroke="#8b949e" marker-end="url(#a2)"/>
  <rect x="175" y="70" width="145" height="40" rx="5" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="247" y="88" text-anchor="middle" fill="#e6edf3">PathPatternParser</text>
  <text x="247" y="103" text-anchor="middle" fill="#8b949e" font-size="10">caseSensitive=false</text>
  <line x1="320" y1="90" x2="365" y2="90" stroke="#8b949e" marker-end="url(#a2)"/>
  <rect x="365" y="70" width="130" height="40" rx="5" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="430" y="88" text-anchor="middle" fill="#e6edf3">PathMatchConfigurer</text>
  <text x="430" y="103" text-anchor="middle" fill="#8b949e" font-size="10">registered in DispatcherServlet</text>
  <line x1="495" y1="90" x2="540" y2="90" stroke="#8b949e" marker-end="url(#a2)"/>
  <rect x="540" y="70" width="90" height="40" rx="5" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="585" y="88" text-anchor="middle" fill="#e6edf3">HandlerMapping</text>
  <text x="585" y="103" text-anchor="middle" fill="#8b949e" font-size="10">uses parser</text>
  <text x="320" y="165" text-anchor="middle" fill="#8b949e" font-size="11">One-time setup flow: configurer → parser → mapping</text>
  <defs><marker id="a2" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L0,6 L8,3 z" fill="#8b949e"/></marker></defs>
</svg>

---

## 6. Walkthrough

**Entry point: startup**

1. Spring Boot auto-configuration calls `WebMvcAutoConfiguration` → `WebMvcConfigurer.configurePathMatch()`.
2. `MvcPathConfig.configurePathMatch()` creates a `PathPatternParser` with `caseSensitive=false`.
3. `PathMatchConfigurer.setPatternParser(parser)` stores the parser.
4. `RequestMappingHandlerMapping` iterates every `@RequestMapping` annotation at startup and calls `parser.parse(pattern)` for each one, storing the resulting `PathPattern` AST.

**Per-request matching**

5. A `GET /USERS/42` request arrives.
6. `DispatcherServlet.doDispatch()` calls `HandlerMapping.getHandler()`.
7. `RequestMappingHandlerMapping.lookupHandlerMethod()` iterates registered `PathPattern` objects.
8. For each candidate it calls `pattern.matches(requestPath)` — a fast AST traversal over the pre-parsed `RequestPath`.
9. Because `caseSensitive=false`, `USERS` matches the literal element `users`.
10. `matchAndExtract()` returns a `PathMatchInfo`; `{id}` captures `"42"`.
11. Spring stores `{id: "42"}` in `HandlerMapping.URI_TEMPLATE_VARIABLES_ATTRIBUTE`; the `@PathVariable String id` argument resolver reads it from there.

**Request → Response data flow**

```
Request:  GET /USERS/42
  ↓ DispatcherServlet
  ↓ RequestMappingHandlerMapping.lookupHandlerMethod()
      → pattern "/users/{id}".matches("/USERS/42") → true (case-insensitive)
      → uriVariables = {id: "42"}
  ↓ HandlerAdapter invokes UserController.getUser("42")
  ↓ @PathVariable resolved from URI_TEMPLATE_VARIABLES_ATTRIBUTE
Response: 200 OK   {"id":42,"name":"Alice"}
```

---

## 7. Gotchas & takeaways

> **`AntPathMatcher` and `PathPattern` cannot be mixed for the same handler mapping.** Once you call `setPatternParser()`, all patterns in that mapping use `PathPattern`; passing a `null` reverts to `AntPathMatcher`. Mixing causes unpredictable priority ordering.

> **`/**` at the end of a pattern behaves differently in edge cases.** With `AntPathMatcher`, `/api/**` matches `/api` (no trailing slash, zero segments). With `PathPattern`, `/api/**` requires at least the `/api` segment; use `/api{/**}` to also match the bare root.

- `PathPattern` is the default and recommended engine since Spring MVC 5.3 / Spring Boot 2.4.
- Patterns are parsed **once** at startup — placing complex patterns on hot paths costs zero extra per-request CPU.
- `{*variable}` captures the entire remaining path (including slashes) into one variable; `**` discards it.
- Disable suffix-pattern matching (`useRegisteredSuffixPatternMatch=false`) to prevent `/user.json` style bypasses.
- `PathPatternParser.setCaseSensitive(false)` is the clean way to enable case-insensitive routing — no subclassing needed.

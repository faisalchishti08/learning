---
card: spring-framework
gi: 356
slug: resource-resolvers-versioning
title: "Resource resolvers & versioning"
---

## 1. What it is

Resource resolvers are pluggable strategies (`ResourceResolver` implementations) that sit in front of `ResourceHttpRequestHandler`, transforming how static resource URLs are matched and served. `VersionResourceResolver` is the most commonly used one — it embeds a content-derived hash (or a fixed version string) into a resource's URL, so `style.css` becomes `style-a1b2c3d4.css`, letting you set effectively infinite cache lifetimes safely, since any content change produces a *new* URL rather than invalidating a cached old one.

```java
registry.addResourceHandler("/assets/**")
    .addResourceLocations("classpath:/static/assets/")
    .resourceChain(true)
    .addResolver(new VersionResourceResolver().addContentVersionStrategy("/**"));
```

## 2. Why & when

Long `Cache-Control: max-age` values (the previous card) are only safe if the URL is guaranteed to change whenever the content does — otherwise, browsers and CDNs keep serving stale cached content indefinitely, and there's no way to force a refresh short of the cache's own expiry. Cache-busting via versioned URLs solves this at the root: a **content hash** in the filename means the URL itself changes automatically the moment the file's bytes change, so:

- You can set `Cache-Control: max-age=31536000, immutable` (effectively forever) safely, since a stale cache entry for an *old* URL simply becomes irrelevant once your templates/code reference the *new*, hash-updated URL.
- Deployments never require cache-busting query strings (`style.css?v=3`) that some caches handle inconsistently — the version is baked into the path itself.
- You get automatic invalidation for free: change one line of CSS, rebuild, and the resulting URL is guaranteed different, with zero manual version-number bookkeeping.

## 3. Core concept

```
Without versioning:
  /assets/style.css               <- SAME url regardless of content
  Cache-Control: max-age=2592000  <- risky: a stale cached copy could persist for 30 days
                                      after a real content change, with no way to force a refresh

With VersionResourceResolver (content-based hashing):
  /assets/style-a1b2c3d4e5.css    <- hash derived from file CONTENT
  Cache-Control: max-age=31536000, immutable  <- SAFE: this exact URL's content will NEVER change;
                                                   a content change produces a DIFFERENT hash/URL

  Template reference (auto-rewritten by ResourceUrlEncodingFilter / ResourceUrlProvider):
    <link rel="stylesheet" th:href="@{/assets/style.css}">
                     |
                     v (Thymeleaf's @{...} link-building, integrated with Spring's resource resolution)
    <link rel="stylesheet" href="/assets/style-a1b2c3d4e5.css">

Resolver CHAIN (resourceChain(true)):
  EncodedResourceResolver  -> tries pre-compressed .gz/.br variants first
  VersionResourceResolver  -> strips/matches the version hash, locates the REAL file
  PathResourceResolver     -> the base resolver, actually reads bytes from disk/classpath
```

## 4. Diagram

<svg viewBox="0 0 720 220" xmlns="http://www.w3.org/2000/svg" font-family="monospace" font-size="12">
  <rect width="720" height="220" fill="#0d1117"/>
  <text x="360" y="22" text-anchor="middle" fill="#8b949e">Content hash in the URL enables safe, effectively-permanent caching</text>

  <rect x="20" y="50" width="300" height="60" rx="5" fill="#1c2430" stroke="#8b949e"/>
  <text x="170" y="72" text-anchor="middle" fill="#8b949e" font-size="10">style.css content changes</text>
  <text x="170" y="90" text-anchor="middle" fill="#8b949e" font-size="9">(a CSS rule edited)</text>

  <line x1="320" y1="80" x2="380" y2="80" stroke="#8b949e" marker-end="url(#a32)"/>

  <rect x="380" y="50" width="320" height="60" rx="5" fill="#1c2430" stroke="#6db33f"/>
  <text x="540" y="72" text-anchor="middle" fill="#6db33f" font-size="10">hash recomputed on next build</text>
  <text x="540" y="90" text-anchor="middle" fill="#8b949e" font-size="9">style-a1b2c3.css -&gt; style-f9e8d7.css</text>

  <line x1="170" y1="110" x2="170" y2="150" stroke="#8b949e" marker-end="url(#a32)"/>
  <line x1="540" y1="110" x2="540" y2="150" stroke="#6db33f" marker-end="url(#a32)"/>

  <rect x="20" y="150" width="300" height="50" rx="4" fill="#1c2430" stroke="#8b949e" stroke-dasharray="3,3"/>
  <text x="170" y="180" text-anchor="middle" fill="#8b949e" font-size="10">old cached URL: now irrelevant</text>

  <rect x="380" y="150" width="320" height="50" rx="4" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="540" y="180" text-anchor="middle" fill="#e6edf3" font-size="10">new URL: fresh fetch, guaranteed correct content</text>

  <defs>
    <marker id="a32" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto">
      <path d="M0,0 L0,6 L8,3 z" fill="#8b949e"/>
    </marker>
  </defs>
</svg>

*A content-derived hash means the URL always reflects the current content — no manual invalidation needed.*

## 5. Runnable example

### Level 1 — Basic

Content-hash versioning enabled for static assets, with a matching Thymeleaf template using resource-aware link generation:

```java
// WebConfig.java
import org.springframework.context.annotation.Configuration;
import org.springframework.http.CacheControl;
import org.springframework.web.servlet.config.annotation.ResourceHandlerRegistry;
import org.springframework.web.servlet.config.annotation.WebMvcConfigurer;
import org.springframework.web.servlet.resource.VersionResourceResolver;

import java.time.Duration;

@Configuration
public class WebConfig implements WebMvcConfigurer {
    @Override
    public void addResourceHandlers(ResourceHandlerRegistry registry) {
        registry.addResourceHandler("/assets/**")
            .addResourceLocations("classpath:/static/assets/")
            .setCacheControl(CacheControl.maxAge(Duration.ofDays(365)).immutable())
            .resourceChain(true)
            .addResolver(new VersionResourceResolver().addContentVersionStrategy("/**"));
    }
}
```

`templates/home.html`:
```html
<html xmlns:th="http://www.thymeleaf.org">
<head>
  <link rel="stylesheet" th:href="@{/assets/style.css}">
</head>
<body><h1>Home</h1></body>
</html>
```

**How to run:**
```bash
./mvnw spring-boot:run

curl http://localhost:8080/
# <link rel="stylesheet" href="/assets/style-a1b2c3d4e5f6.css">
#   ^ Thymeleaf's @{...} automatically rewrote the URL to include the content hash

curl -i http://localhost:8080/assets/style-a1b2c3d4e5f6.css
# HTTP/1.1 200 OK
# Cache-Control: max-age=31536000, immutable
```

Thymeleaf's `@{...}` link-expression syntax, integrated with Spring's `ResourceUrlProvider`, automatically rewrites `/assets/style.css` to the hash-suffixed real URL at render time — you write the *stable* logical path in your template, and the framework handles injecting the current hash.

### Level 2 — Intermediate

A resolver chain combining pre-compressed variant serving (`EncodedResourceResolver`) with version hashing, for both smaller payloads and safe long-term caching together:

```java
// WebConfig.java (extended)
import org.springframework.context.annotation.Configuration;
import org.springframework.http.CacheControl;
import org.springframework.web.servlet.config.annotation.ResourceHandlerRegistry;
import org.springframework.web.servlet.config.annotation.WebMvcConfigurer;
import org.springframework.web.servlet.resource.EncodedResourceResolver;
import org.springframework.web.servlet.resource.VersionResourceResolver;

import java.time.Duration;

@Configuration
public class WebConfig implements WebMvcConfigurer {
    @Override
    public void addResourceHandlers(ResourceHandlerRegistry registry) {
        registry.addResourceHandler("/assets/**")
            .addResourceLocations("classpath:/static/assets/")
            .setCacheControl(CacheControl.maxAge(Duration.ofDays(365)).immutable())
            .resourceChain(true)
            .addResolver(new EncodedResourceResolver())   // serves style.css.gz / .br if client accepts + file exists
            .addResolver(new VersionResourceResolver().addContentVersionStrategy("/**"));
    }
}
```

Build step produces `style.css` and a pre-compressed `style.css.gz` alongside it in `classpath:/static/assets/`.

**How to run:**
```bash
./mvnw spring-boot:run

curl -i -H "Accept-Encoding: gzip" http://localhost:8080/assets/style-a1b2c3d4e5f6.css
# HTTP/1.1 200 OK
# Content-Encoding: gzip
# Cache-Control: max-age=31536000, immutable
# (gzip-compressed bytes — served from style.css.gz, not the uncompressed original)

curl -i http://localhost:8080/assets/style-a1b2c3d4e5f6.css
# (no Accept-Encoding: gzip) -> Content-Encoding header absent, uncompressed bytes served
```

**What changed:** `EncodedResourceResolver` is added to the chain *before* `VersionResourceResolver` — it checks whether a pre-compressed variant (`.gz`, `.br`) of the requested resource exists and whether the client's `Accept-Encoding` header allows it, serving the smaller compressed file transparently when both conditions hold. The two resolvers compose cleanly: one handles compression negotiation, the other handles version-hash matching, each unaware of the other's specific concern.

### Level 3 — Advanced

Production concern: understanding `addContentVersionStrategy` versus `addFixedVersionStrategy`, and correctly handling the interaction between resource versioning and a CDN/reverse-proxy layer in front of the application:

```java
// WebConfig.java (production version)
import org.springframework.context.annotation.Configuration;
import org.springframework.http.CacheControl;
import org.springframework.web.servlet.config.annotation.ResourceHandlerRegistry;
import org.springframework.web.servlet.config.annotation.WebMvcConfigurer;
import org.springframework.web.servlet.resource.VersionResourceResolver;

import java.time.Duration;

@Configuration
public class WebConfig implements WebMvcConfigurer {
    @Override
    public void addResourceHandlers(ResourceHandlerRegistry registry) {
        registry.addResourceHandler("/assets/**")
            .addResourceLocations("classpath:/static/assets/")
            // .cachePublic() is IMPORTANT here — without it, a CDN or shared reverse proxy in front
            // of the application may treat the response as private (browser-only cacheable) and
            // refuse to cache it at the edge, defeating much of the point of long-lived, versioned URLs.
            .setCacheControl(CacheControl.maxAge(Duration.ofDays(365)).immutable().cachePublic())
            .resourceChain(true)
            // Content-based hashing: the hash is DERIVED FROM THE FILE'S BYTES, so it changes
            // automatically and correctly whenever the content changes — no manual coordination needed.
            .addResolver(new VersionResourceResolver().addContentVersionStrategy("/**"));

        // Third-party vendored assets (e.g. a specific pinned library version) use a FIXED
        // version string instead — content hashing isn't meaningful here since the "version"
        // is a deliberate, human-chosen identifier (the library's release version), not a hash.
        registry.addResourceHandler("/vendor/**")
            .addResourceLocations("classpath:/static/vendor/")
            .setCacheControl(CacheControl.maxAge(Duration.ofDays(365)).immutable().cachePublic())
            .resourceChain(true)
            .addResolver(new VersionResourceResolver().addFixedVersionStrategy("v2.4.1", "/**"));
    }
}
```

**How to run:**
```bash
./mvnw spring-boot:run

curl http://localhost:8080/assets/style.css
# 404 — the UNVERSIONED path is not directly servable once VersionResourceResolver is active;
#       clients (or templates) must reference the version-embedded URL

curl -i http://localhost:8080/assets/style-a1b2c3d4e5f6.css
# HTTP/1.1 200 OK
# Cache-Control: max-age=31536000, immutable, public

curl http://localhost:8080/vendor/v2.4.1/library.js
# 200 OK, served from the SAME classpath location regardless of the "v2.4.1" segment,
# which VersionResourceResolver strips before looking up the real file
```

**What changed and why:**
- `.cachePublic()` explicitly marks these responses as cacheable by *shared* caches (CDNs, corporate proxies), not just the end user's browser — critical for the versioned-URL strategy to deliver its full performance benefit at scale; without it, some intermediate caches would refuse to store the response at all.
- `addContentVersionStrategy` (hash-based) suits build-generated assets where the "version" should track content automatically; `addFixedVersionStrategy` (a literal string you choose) suits vendored/third-party assets where the version is a meaningful, human-assigned identifier (a library release) rather than an opaque hash — both coexist in the same application for different resource handlers.
- Requesting the bare, unversioned `/assets/style.css` now returns `404` — once `VersionResourceResolver` is active for a pattern, only version-embedded URLs resolve successfully by default (the resolver expects and strips the version segment as part of locating the real file), reinforcing that templates must use `@{...}`-style resource-aware link generation rather than hardcoding paths.

## 6. Walkthrough

**Request: `GET /assets/style-a1b2c3d4e5f6.css` (Level 3 code).**

1. `DispatcherServlet` routes the request to `SimpleUrlHandlerMapping`, which matches `/assets/**` and resolves to the configured `ResourceHttpRequestHandler` for that pattern.
2. Because `resourceChain(true)` was configured, the handler doesn't go straight to `PathResourceResolver` (the base resolver that reads raw bytes) — it first passes the request through the configured resolver chain, here just `VersionResourceResolver` (content strategy).
3. `VersionResourceResolver.resolveResourceInternal` inspects the requested path `style-a1b2c3d4e5f6.css`, recognizes the embedded version segment (`a1b2c3d4e5f6`) based on its configured pattern, and **strips** it to derive the *actual* underlying resource path: `style.css`.
4. It delegates to the next resolver in the chain (implicitly, `PathResourceResolver`) with the stripped path `style.css`, which locates and reads the real file from `classpath:/static/assets/style.css`.
5. Before returning the resource, `VersionResourceResolver` **verifies** the version in the request matches the version it would currently compute for that file's actual content (recomputing the content hash) — if a client requested a stale hash from an old deployment, this check would fail and the resolver would report "not found," since a hash mismatch means the content has since changed and this old URL no longer corresponds to any exact current representation.
6. Assuming the hash matches: the raw file bytes are returned up through the chain, and the handler sets `Content-Type: text/css` (from the `.css` extension) and applies the configured `Cache-Control: max-age=31536000, immutable, public` header.
7. Response:
   ```
   HTTP/1.1 200 OK
   Content-Type: text/css
   Cache-Control: max-age=31536000, immutable, public

   body { background: red; }
   ```

**Rendering the page that references this asset — `GET /` (Thymeleaf template with `th:href="@{/assets/style.css}"`).**

1. During template rendering, Thymeleaf's `@{...}` link-builder expression delegates to Spring's `ResourceUrlProvider` (auto-integrated when a `VersionResourceResolver` is registered) to resolve the *logical* path `/assets/style.css` into its *actual*, currently-valid versioned URL.
2. `ResourceUrlProvider` internally asks the same `VersionResourceResolver` chain: "what is the current version-embedded URL for `/assets/style.css`?" — it reads the file's current bytes, computes the content hash (`a1b2c3d4e5f6`, matching step 5 above), and returns `/assets/style-a1b2c3d4e5f6.css`.
3. This resolved URL is written directly into the rendered HTML's `<link>` tag — the browser then requests exactly that hash-embedded URL, triggering the flow described in the first walkthrough above.

## 7. Gotchas & takeaways

> **Once `VersionResourceResolver` is active for a URL pattern, the unversioned/bare path typically no longer resolves** (as shown in the Level 3 example) — any code, template, or external link that hardcodes `/assets/style.css` directly (instead of using `@{...}`/`ResourceUrlProvider`-aware link generation) breaks. Audit all references to versioned resources when introducing this resolver.

> **Rolling back a deployment (or running two application versions simultaneously behind a load balancer during a rolling deploy) can serve mismatched HTML and asset versions** if the HTML from one instance references a hash that only the *other* instance's currently-deployed assets match — usually harmless since old assets remain available until actually removed from the classpath/filesystem, but worth considering for aggressive asset-pruning deployment scripts.

> **`addFixedVersionStrategy` requires you to manually update the version string whenever the underlying vendored asset changes** — unlike content hashing, nothing automatically detects a change; forgetting to bump `"v2.4.1"` to `"v2.5.0"` after actually updating the vendored file means the URL doesn't change even though the content did, silently reintroducing the stale-cache problem this whole mechanism exists to prevent.

- `VersionResourceResolver` embeds a version (content hash or fixed string) into resource URLs, enabling safe, effectively-permanent `Cache-Control: immutable` caching.
- `addContentVersionStrategy` computes hashes automatically from file bytes — ideal for build-generated assets. `addFixedVersionStrategy` uses a manually chosen string — appropriate for vendored/third-party assets with their own meaningful version identifiers.
- Always pair versioned resources with `.cachePublic()` so shared caches (CDNs, proxies) can store them, not just end-user browsers.
- Reference versioned resources through resource-aware link generation (Thymeleaf's `@{...}`, or `ResourceUrlProvider` directly) rather than hardcoded paths, since the bare unversioned URL typically stops resolving once versioning is active.

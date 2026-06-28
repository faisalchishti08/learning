---
card: spring-boot
gi: 109
slug: custom-favicon
title: Custom favicon
---

## 1. What it is

A **favicon** is the small icon displayed in browser tabs, bookmarks, and history entries for your web application. Spring Boot automatically serves a `favicon.ico` file if it finds one in the static resource locations:

```
src/main/resources/static/favicon.ico
src/main/resources/public/favicon.ico
src/main/resources/resources/favicon.ico
src/main/resources/META-INF/resources/favicon.ico
```

Spring Boot 2.2+ also serves a default Spring leaf favicon if no custom one is present (only visible during development; disabled in production by setting `spring.mvc.favicon.enabled=false`, which is now the default in Spring Boot 3.x).

To provide a custom favicon:
1. Create your `favicon.ico` (or `favicon.png`, `favicon.svg`).
2. Place it in `src/main/resources/static/`.
3. That's it — browsers request `/favicon.ico` and Spring Boot's static resource handler serves it.

## 2. Why & when

A favicon is a branding element. Without one, browsers issue a `GET /favicon.ico` that returns 404 — generating an error in your logs for every page load. A custom favicon:
- Eliminates the 404 log noise.
- Brands your application in browser tabs (helps distinguish between multiple local dev servers).
- Is required for PWA (Progressive Web App) configurations.

Modern web practice also includes a full icon set (`apple-touch-icon.png`, `icon-192.png`, `icon-512.png`, `site.webmanifest`) for mobile home-screen icons and PWA support. Spring Boot serves all these as static resources the same way.

## 3. Core concept

`ResourceHttpRequestHandler` handles `GET /favicon.ico` just like any other static file. No special configuration exists for favicons — it's plain static resource serving.

Spring Boot 2.x had a `FaviconAutoConfiguration` that provided a default Spring leaf icon when no custom one existed. This was removed in Spring Boot 3.x. In Spring Boot 3.x, if no `favicon.ico` exists in your static locations, `GET /favicon.ico` returns 404 (browsers handle this gracefully and do not display a tab icon).

To serve a PNG or SVG favicon with modern `<link>` tag syntax:
```html
<!-- In your HTML <head> -->
<link rel="icon" type="image/png" sizes="32x32" href="/favicon-32x32.png">
<link rel="apple-touch-icon" href="/apple-touch-icon.png">
<link rel="manifest" href="/site.webmanifest">
```

Place `favicon-32x32.png`, `apple-touch-icon.png`, and `site.webmanifest` in `src/main/resources/static/`. Spring Boot serves them all.

A minimal `site.webmanifest`:
```json
{
  "name": "My App",
  "short_name": "App",
  "icons": [
    {"src": "/icon-192.png", "sizes": "192x192", "type": "image/png"},
    {"src": "/icon-512.png", "sizes": "512x512", "type": "image/png"}
  ],
  "theme_color": "#6db33f",
  "background_color": "#ffffff",
  "display": "standalone"
}
```

## 4. Diagram

<svg viewBox="0 0 680 240" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Browser requests favicon.ico; Spring Boot static resource handler finds favicon.ico in /static/ and serves it with 200 OK">
  <rect x="8" y="8" width="664" height="224" rx="12" fill="#161b22" stroke="#30363d" stroke-width="1"/>
  <text x="340" y="33" fill="#e6edf3" font-size="14" text-anchor="middle" font-family="sans-serif" font-weight="bold">Custom Favicon — Request Flow</text>

  <!-- Browser -->
  <rect x="20" y="60" width="130" height="60" rx="6" fill="#1c2430" stroke="#f0883e" stroke-width="1.5"/>
  <text x="85" y="78" fill="#f0883e" font-size="10" text-anchor="middle" font-family="sans-serif">Browser</text>
  <text x="85" y="94" fill="#8b949e" font-size="8" text-anchor="middle" font-family="monospace">GET /favicon.ico</text>
  <text x="85" y="108" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">on every page load</text>

  <defs><marker id="fav" markerWidth="7" markerHeight="7" refX="5" refY="3" orient="auto"><path d="M0,0 L5,3 L0,6 Z" fill="#8b949e"/></marker></defs>
  <line x1="152" y1="90" x2="180" y2="90" stroke="#8b949e" stroke-width="1.5" marker-end="url(#fav)"/>

  <!-- ResourceHttpRequestHandler -->
  <rect x="182" y="60" width="230" height="60" rx="6" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="297" y="78" fill="#79c0ff" font-size="10" text-anchor="middle" font-family="sans-serif">ResourceHttpRequestHandler</text>
  <text x="297" y="93" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">searches static locations</text>
  <text x="297" y="107" fill="#e6edf3" font-size="8" text-anchor="middle" font-family="monospace">finds /static/favicon.ico</text>

  <line x1="414" y1="90" x2="440" y2="90" stroke="#8b949e" stroke-width="1.5" marker-end="url(#fav)"/>

  <!-- Response -->
  <rect x="442" y="60" width="210" height="60" rx="6" fill="#1c2430" stroke="#6db33f" stroke-width="2"/>
  <text x="547" y="78" fill="#6db33f" font-size="10" text-anchor="middle" font-family="sans-serif">200 OK</text>
  <text x="547" y="93" fill="#e6edf3" font-size="8" text-anchor="middle" font-family="monospace">Content-Type: image/x-icon</text>
  <text x="547" y="107" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">browser shows icon in tab</text>

  <!-- Modern icon set -->
  <rect x="20" y="148" width="630" height="68" rx="6" fill="#1c2430" stroke="#8b949e" stroke-width="1"/>
  <text x="335" y="164" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif" font-weight="bold">Modern favicon set — place all in src/main/resources/static/</text>
  <text x="40"  y="180" fill="#e6edf3" font-size="8" font-family="monospace">favicon.ico</text>
  <text x="130" y="180" fill="#8b949e" font-size="8" font-family="sans-serif">legacy browsers</text>
  <text x="220" y="180" fill="#e6edf3" font-size="8" font-family="monospace">favicon-32x32.png</text>
  <text x="330" y="180" fill="#8b949e" font-size="8" font-family="sans-serif">modern browsers</text>
  <text x="430" y="180" fill="#e6edf3" font-size="8" font-family="monospace">apple-touch-icon.png</text>
  <text x="555" y="180" fill="#8b949e" font-size="8" font-family="sans-serif">iOS home screen</text>
  <text x="40"  y="196" fill="#e6edf3" font-size="8" font-family="monospace">site.webmanifest</text>
  <text x="130" y="196" fill="#8b949e" font-size="8" font-family="sans-serif">PWA manifest</text>
  <text x="220" y="196" fill="#e6edf3" font-size="8" font-family="monospace">icon-192.png + icon-512.png</text>
  <text x="370" y="196" fill="#8b949e" font-size="8" font-family="sans-serif">Android / PWA install</text>
</svg>

Drop `favicon.ico` into `/static/` — Spring Boot's static resource handler serves it automatically.

## 5. Runnable example

```java
// CustomFavicon.java — run: java CustomFavicon.java  (JDK 17+)
// Shows how Spring Boot serves favicon.ico and what a modern icon setup looks like.

public class CustomFavicon {

    // Simulates how Spring Boot resolves a favicon request
    static String serveFavicon(boolean hasIco, boolean hasController) {
        // Controller takes precedence (unlikely for /favicon.ico, but possible)
        if (hasController) return "controller @GetMapping(\"/favicon.ico\") → custom response";
        // Static resource handler
        if (hasIco) return "static/favicon.ico → 200 OK (image/x-icon)";
        return "not found → 404 (browsers treat this gracefully, show no icon)";
    }

    public static void main(String[] args) {
        System.out.println("=== Favicon resolution ===\n");

        System.out.println("No favicon.ico on classpath:");
        System.out.println("  GET /favicon.ico → " + serveFavicon(false, false));
        System.out.println("  (404 log noise on every browser page load)\n");

        System.out.println("favicon.ico in src/main/resources/static/:");
        System.out.println("  GET /favicon.ico → " + serveFavicon(true, false));

        System.out.println("\n=== Where to put the file ===");
        System.out.println("src/main/resources/static/favicon.ico");
        System.out.println("  → served at http://localhost:8080/favicon.ico");
        System.out.println("  → no Spring configuration needed");

        System.out.println("\n=== Modern complete icon HTML ===");
        System.out.println("""
<link rel="icon" type="image/x-icon"   href="/favicon.ico">
<link rel="icon" type="image/png" sizes="32x32" href="/favicon-32x32.png">
<link rel="icon" type="image/png" sizes="16x16" href="/favicon-16x16.png">
<link rel="apple-touch-icon" sizes="180x180"    href="/apple-touch-icon.png">
<link rel="manifest" href="/site.webmanifest">
""");

        System.out.println("=== site.webmanifest content ===");
        System.out.println("""
{
  "name": "My Spring App",
  "short_name": "Spring App",
  "icons": [
    { "src": "/icon-192.png", "sizes": "192x192", "type": "image/png" },
    { "src": "/icon-512.png", "sizes": "512x512", "type": "image/png" }
  ],
  "theme_color": "#6db33f",
  "background_color": "#ffffff",
  "display": "standalone"
}
""");

        System.out.println("=== Spring Boot version notes ===");
        System.out.println("Spring Boot 2.x: FaviconAutoConfiguration provides Spring leaf icon as default");
        System.out.println("Spring Boot 3.x: no default favicon; missing favicon returns 404 (no auto-config)");
        System.out.println("spring.mvc.favicon.enabled=false: deprecated in 3.x (already off by default)");
    }
}
```

**How to run:** `java CustomFavicon.java`

## 6. Walkthrough

- `serveFavicon(false, false)` — nothing serves `/favicon.ico`, so it returns 404. Every browser page load generates a 404 in logs and a network error in the browser's developer tools. Not a functional problem, but it creates noise.
- `serveFavicon(true, false)` — `favicon.ico` is in `/static/`. The static resource handler finds it, returns it with `Content-Type: image/x-icon`, and the browser shows the icon in the tab.
- **Modern complete icon setup** — `favicon.ico` is the legacy format that works in every browser. `favicon-32x32.png` and `favicon-16x16.png` are used by modern browsers. `apple-touch-icon.png` (180×180 px) is used when an iOS user saves the site to their home screen. `site.webmanifest` declares the PWA manifest — the `icons` array powers the "Add to Home Screen" install prompt on Android and Chrome.
- `site.webmanifest` has `"theme_color": "#6db33f"` — the Spring green. This tints the browser chrome when the PWA is opened in standalone mode. Set it to match your brand colour.
- **Spring Boot 3.x note**: `spring.mvc.favicon.enabled` was a 2.x property that controlled the built-in Spring leaf favicon. The property is silently ignored (no effect) in 3.x because `FaviconAutoConfiguration` was removed entirely.

## 7. Gotchas & takeaways

> **Spring Boot 3.x has no built-in favicon.** If you upgrade from 2.x to 3.x and relied on the Spring leaf favicon in development, you will now see 404 for `/favicon.ico`. Just add your own `favicon.ico` to `/static/` — the file-serving mechanism works identically in both versions.

> **Cache invalidation for favicons is notoriously difficult.** Browsers cache `/favicon.ico` aggressively, often for days, ignoring `Cache-Control` headers. When you change your favicon, some users will continue to see the old one. The only reliable workaround is to switch to `<link rel="icon" href="/favicon-v2.ico">` with a versioned URL.

- Tools for generating the complete icon set: `realfavicongenerator.net` — upload one large image and download the full set with HTML.
- Place all icon files in `src/main/resources/static/` at the root level — `/favicon.ico`, not `/icons/favicon.ico`, since browsers look for `/favicon.ico` by convention even without a `<link>` tag.
- For Thymeleaf templates, use `<link rel="icon" th:href="@{/favicon.ico}">` — the `@{…}` expression resolves the correct path even if a context path is set.
- `site.webmanifest` must be served with `Content-Type: application/manifest+json`. Spring Boot serves it as `application/json` by default; if your PWA install fails, check the MIME type and add a mapping via `spring.mvc.contentnegotiation.media-types.webmanifest=application/manifest+json`.

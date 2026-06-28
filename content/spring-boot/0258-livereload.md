---
card: spring-boot
gi: 258
slug: livereload
title: LiveReload
---

## 1. What it is

**LiveReload** is a browser-refresh protocol that Spring Boot DevTools embeds automatically. When DevTools detects a static resource change (HTML, CSS, JS, template), it sends a signal over a WebSocket to the LiveReload browser extension, which reloads the page — without any JVM restart.

Spring Boot DevTools starts a LiveReload server on port **35729** when the application starts. The browser extension connects to this server and listens for reload signals.

To use it:
1. Add `spring-boot-devtools` to your project.
2. Install the **LiveReload** browser extension (Chrome, Firefox, Safari).
3. Click the LiveReload icon in the browser to connect.
4. Change a template or CSS file — the browser refreshes automatically.

## 2. Why & when

LiveReload solves a different problem than automatic restart. Restart is for Java code changes (beans, logic); LiveReload is for **resource changes** (templates, stylesheets, JavaScript) that don't require a Java restart at all.

Use LiveReload when:
- You're writing Thymeleaf templates and want to see rendered HTML without restart.
- You're tuning CSS and want instant visual feedback.
- You're building JavaScript in the same project (no separate webpack watch server).

Skip LiveReload when:
- You have a separate frontend build (React, Vue, Angular with `npm run dev`) — those tools have their own HMR (hot module replacement).
- You're writing a REST API with no server-side templates.

## 3. Core concept

LiveReload uses a two-part architecture:

1. **DevTools LiveReload server** (embedded in the Spring Boot process) — listens on port 35729, accepts WebSocket connections from browser extensions.
2. **Browser extension** — maintains a WebSocket connection to port 35729 and calls `window.location.reload()` (or a CSS refresh for stylesheet-only changes) when it receives a reload signal.

When DevTools detects a change to an excluded path (like `templates/**`, `static/**`) that would normally not trigger a restart, it instead sends a LiveReload signal. The browser refreshes without the application restarting.

The protocol is simple:
```
Browser → connects to ws://localhost:35729/livereload
DevTools → sends { "command": "reload", "path": "/index.html" }
Browser → window.location.reload()
```

For CSS-only changes, LiveReload can do a **soft reload** — replacing just the stylesheet in the DOM without a full page refresh.

## 4. Diagram

<svg viewBox="0 0 700 230" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="LiveReload architecture: DevTools server sends reload signal to browser extension via WebSocket">
  <defs>
    <marker id="arr" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#6db33f"/></marker>
    <marker id="arr2" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#79c0ff"/></marker>
  </defs>

  <!-- File system -->
  <rect x="10" y="80" width="130" height="70" rx="8" fill="#1c2430" stroke="#8b949e" stroke-width="1.5"/>
  <text x="75" y="105" fill="#e6edf3" font-size="11" text-anchor="middle" font-family="sans-serif">File System</text>
  <text x="75" y="122" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">templates/</text>
  <text x="75" y="138" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">static/css/</text>

  <!-- DevTools server -->
  <rect x="200" y="60" width="180" height="110" rx="8" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="290" y="88" fill="#e6edf3" font-size="11" text-anchor="middle" font-family="sans-serif">Spring Boot Process</text>
  <text x="290" y="108" fill="#6db33f" font-size="10" text-anchor="middle" font-family="sans-serif">DevTools</text>
  <text x="290" y="126" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">LiveReload server</text>
  <text x="290" y="142" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">:35729</text>

  <!-- Browser -->
  <rect x="460" y="60" width="220" height="110" rx="8" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="570" y="88" fill="#e6edf3" font-size="11" text-anchor="middle" font-family="sans-serif">Browser</text>
  <text x="570" y="108" fill="#79c0ff" font-size="10" text-anchor="middle" font-family="sans-serif">LiveReload extension</text>
  <text x="570" y="126" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">WebSocket connected</text>
  <text x="570" y="142" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">→ window.location.reload()</text>
  <text x="570" y="157" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">or CSS soft-reload</text>

  <!-- Arrows -->
  <line x1="140" y1="115" x2="198" y2="115" stroke="#6db33f" stroke-width="1.5" marker-end="url(#arr)"/>
  <text x="169" y="107" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">change</text>

  <!-- WebSocket bidirectional -->
  <line x1="380" y1="105" x2="458" y2="105" stroke="#79c0ff" stroke-width="1.5" marker-end="url(#arr2)"/>
  <text x="419" y="97" fill="#79c0ff" font-size="9" text-anchor="middle" font-family="sans-serif">reload signal</text>
  <line x1="458" y1="125" x2="380" y2="125" stroke="#8b949e" stroke-width="1" stroke-dasharray="4" marker-end="url(#arr)"/>
  <text x="419" y="140" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">WS handshake</text>

  <text x="350" y="210" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">No JVM restart needed — browser refreshes in &lt;500ms for template/CSS changes</text>
</svg>

DevTools signals the browser extension via WebSocket; the browser reloads without any Java process restart.

## 5. Runnable example

```java
// LiveReloadDemo.java — run with: java LiveReloadDemo.java
// Explains LiveReload setup, protocol, and typical use cases.
// Also shows how to embed a livereload.js script instead of using the extension.

public class LiveReloadDemo {

    public static void main(String[] args) {
        System.out.println("=== LiveReload in Spring Boot DevTools ===\n");
        printSetup();
        printProtocol();
        printScriptAlternative();
        printConfigOptions();
    }

    static void printSetup() {
        System.out.println("--- Setup options ---");
        System.out.println("""
            Option A: Browser extension (recommended)
              1. Install 'LiveReload' from Chrome Web Store or Firefox Add-ons
              2. Start Spring Boot app with devtools
              3. Open http://localhost:8080 in browser
              4. Click the LiveReload extension icon to connect
              5. Edit src/main/resources/templates/index.html → browser reloads

            Option B: livereload.js script in HTML (no extension needed)
              Add to your HTML <head> (only in dev profile):
              <script src="http://localhost:35729/livereload.js"></script>
            """);
    }

    static void printProtocol() {
        System.out.println("--- LiveReload WebSocket protocol (simplified) ---");
        System.out.println("""
            Browser connects:
              ws://localhost:35729/livereload

            Handshake (browser → server):
              { "command": "hello",
                "protocols": ["http://livereload.com/protocols/official-7"] }

            Server acknowledges:
              { "command": "hello",
                "protocols": ["http://livereload.com/protocols/official-7"],
                "serverName": "spring-boot-devtools" }

            On file change (server → browser):
              { "command": "reload",
                "path": "templates/index.html",
                "liveCSS": true }

            Browser action:
              if (liveCSS && onlyCSSChanged)  replaceStylesheet()
              else                             window.location.reload()
            """);
    }

    static void printScriptAlternative() {
        System.out.println("--- Thymeleaf template with dev-only livereload.js ---");
        System.out.println("""
            <!-- src/main/resources/templates/layout.html -->
            <!DOCTYPE html>
            <html xmlns:th="http://www.thymeleaf.org">
            <head>
              <title th:text="${title}">App</title>
              <!-- Include only in development (th:if + Spring profile check) -->
              <script th:if="${#strings.equals(activeProfile, 'dev')}"
                      src="http://localhost:35729/livereload.js"
                      defer></script>
            </head>
            <body th:fragment="layout">...</body>
            </html>
            """);
    }

    static void printConfigOptions() {
        System.out.println("--- application.properties LiveReload config ---");
        System.out.println("""
            # Disable LiveReload (keep automatic restart):
            spring.devtools.livereload.enabled=false

            # Change port (if 35729 conflicts with something):
            spring.devtools.livereload.port=35730

            # Files that trigger LiveReload (not restart):
            # DevTools sends LiveReload for paths matching 'exclude' patterns:
            spring.devtools.restart.exclude=static/**,public/**,templates/**
            # Changes to these paths → LiveReload signal, NOT JVM restart
            """);
    }
}
```

**How to run:** `java LiveReloadDemo.java`

## 6. Walkthrough

- **Browser extension vs. script** — the extension approach is cleaner (no template changes needed), but the `<script>` approach works in environments where you can't install extensions (e.g., CI screenshot tests). The Thymeleaf `th:if` guard ensures the script is only included when `activeProfile == 'dev'` — pass this from a controller's model attribute or use a `@Profile("dev")` interceptor.
- **Protocol** — the WebSocket handshake negotiates the protocol version. `liveCSS: true` in the reload command tells the extension it's a CSS-only change; modern LiveReload implementations then swap the stylesheet in the DOM (`link.href = link.href + '?t=' + Date.now()`) without a full page reload. This is instant and preserves JavaScript state (form inputs, scroll position).
- **Exclude patterns feed LiveReload** — the `spring.devtools.restart.exclude` list does double duty: paths matching it don't trigger a JVM restart *and* their changes are routed to LiveReload instead. This is why adding `templates/**` to exclude doesn't mean templates are ignored — they're handled more efficiently via LiveReload.
- **Port 35729** — the LiveReload standard port. If another tool already uses it (e.g., webpack-dev-server with `--live-reload`), change it with `spring.devtools.livereload.port`.

## 7. Gotchas & takeaways

> **LiveReload and the extension must connect to the same host:port.** If you're accessing the app at `http://localhost:8080`, the extension connects to `ws://localhost:35729`. If you're behind a reverse proxy (Nginx) or tunnelling (ngrok), the extension can't reach port 35729 unless you forward it separately.

> **CSS soft-reload requires the LiveReload extension version ≥ 2.1** and the `liveCSS` flag. Older extensions always do a full page reload. Check the extension version if you expected CSS-only updates but are seeing full reloads.

- LiveReload fires for paths in `restart.exclude` (templates, static) — JVM restart fires for everything else.
- You can test LiveReload without a browser: `curl -N -H "Upgrade: websocket" -H "Connection: Upgrade" http://localhost:35729/livereload` — you'll see the handshake JSON.
- Disable LiveReload during integration tests by setting `spring.devtools.livereload.enabled=false` in `application-test.properties`.
- One LiveReload server per Spring Boot process; if you run multiple apps on the same machine, each needs a different port.

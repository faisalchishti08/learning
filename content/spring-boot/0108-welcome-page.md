---
card: spring-boot
gi: 108
slug: welcome-page
title: Welcome page
---

## 1. What it is

Spring Boot automatically serves a **welcome page** when a browser requests the root URL (`/`). It looks for `index.html` in the static resource locations (`/static/`, `/public/`, `/resources/`, `/META-INF/resources/`) and in the configured template directories.

If `index.html` exists in any static location:
- A `WelcomePageHandlerMapping` maps `GET /` to that file.
- The file is served with the standard static resource caching headers.

If a template named `index` exists (e.g. `index.html` in `src/main/resources/templates/` for Thymeleaf):
- Spring Boot routes `GET /` to a view named `"index"`, which the configured template engine renders.

If neither exists, `GET /` falls through to the regular `DispatcherServlet` handler mapping — which returns `404 Not Found` unless a controller handles `/`.

## 2. Why & when

The welcome page is the entry point of any web application. Spring Boot's auto-detection means you don't need a controller that returns `"index"` — just drop `index.html` in `/static/` and the root URL works.

Use the static welcome page when:
- You have a static HTML landing page or a React/Vue SPA entry point.
- You want the simplest possible setup for a front-end served from Spring Boot.

Use a template welcome page when:
- The landing page needs server-side data (the user's name, a list of recent items).
- You render the page through Thymeleaf or another template engine.

Use a controller-based welcome page (`@GetMapping("/")`) when:
- You need redirect logic (`return "redirect:/dashboard"` if logged in, else `"redirect:/login"`).
- You want to add model attributes before rendering.

## 3. Core concept

Spring Boot registers `WelcomePageHandlerMapping` in `WebMvcAutoConfiguration` at a higher priority than `RequestMappingHandlerMapping` (which handles `@Controller` methods). This means an `index.html` in `/static/` takes precedence over a `@GetMapping("/")` method in a controller — only if no forward mapping intervenes.

Resolution order for `GET /`:
```
1. WelcomePageHandlerMapping checks for index.html in static locations → found → serve it
2. WelcomePageHandlerMapping checks for 'index' template → found → delegate to view
3. Falls through to RequestMappingHandlerMapping → @GetMapping("/") if present
4. Falls through to ResourceHttpRequestHandler → 404
```

Template welcome pages work the same way: `templates/index.html` in Thymeleaf is the view name `"index"`, and Spring Boot's `WelcomePageHandlerMapping` routes `GET /` to a view resolution with no controller involved.

## 4. Diagram

<svg viewBox="0 0 680 270" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Welcome page resolution: GET / checks static index.html first, then template index, then controllers, then 404">
  <rect x="8" y="8" width="664" height="254" rx="12" fill="#161b22" stroke="#30363d" stroke-width="1"/>
  <text x="340" y="33" fill="#e6edf3" font-size="14" text-anchor="middle" font-family="sans-serif" font-weight="bold">Welcome Page Resolution — GET /</text>

  <!-- GET / -->
  <rect x="280" y="50" width="120" height="36" rx="5" fill="#1c2430" stroke="#f0883e" stroke-width="1.5"/>
  <text x="340" y="73" fill="#f0883e" font-size="11" text-anchor="middle" font-family="monospace">GET /</text>

  <defs><marker id="wp" markerWidth="7" markerHeight="7" refX="5" refY="3" orient="auto"><path d="M0,0 L5,3 L0,6 Z" fill="#8b949e"/></marker></defs>
  <line x1="340" y1="87" x2="340" y2="105" stroke="#8b949e" stroke-width="1.5" marker-end="url(#wp)"/>

  <!-- Check 1: static index.html -->
  <rect x="160" y="107" width="360" height="36" rx="5" fill="#1c2430" stroke="#6db33f" stroke-width="2"/>
  <text x="340" y="121" fill="#6db33f" font-size="10" text-anchor="middle" font-family="sans-serif">① static/index.html exists?</text>
  <text x="340" y="135" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">checked in /static/, /public/, /resources/, /META-INF/resources/</text>

  <!-- Yes → serve static -->
  <line x1="520" y1="125" x2="570" y2="125" stroke="#6db33f" stroke-width="1.5" marker-end="url(#wp)"/>
  <rect x="572" y="108" width="84" height="34" rx="5" fill="#0d1117" stroke="#6db33f" stroke-width="1.5"/>
  <text x="614" y="123" fill="#6db33f" font-size="9" text-anchor="middle" font-family="sans-serif">Serve file</text>
  <text x="614" y="135" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">200 OK</text>

  <!-- No → check template -->
  <line x1="340" y1="144" x2="340" y2="162" stroke="#8b949e" stroke-width="1" stroke-dasharray="3 2" marker-end="url(#wp)"/>

  <rect x="160" y="164" width="360" height="36" rx="5" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="340" y="178" fill="#79c0ff" font-size="10" text-anchor="middle" font-family="sans-serif">② template 'index' exists?</text>
  <text x="340" y="192" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">Thymeleaf templates/index.html or other engine</text>

  <line x1="520" y1="182" x2="570" y2="182" stroke="#79c0ff" stroke-width="1.5" marker-end="url(#wp)"/>
  <rect x="572" y="165" width="84" height="34" rx="5" fill="#0d1117" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="614" y="180" fill="#79c0ff" font-size="9" text-anchor="middle" font-family="sans-serif">Render view</text>
  <text x="614" y="192" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">'index'</text>

  <!-- No → controller -->
  <line x1="340" y1="201" x2="340" y2="220" stroke="#8b949e" stroke-width="1" stroke-dasharray="3 2" marker-end="url(#wp)"/>

  <rect x="160" y="222" width="360" height="24" rx="5" fill="#1c2430" stroke="#8b949e" stroke-width="1"/>
  <text x="340" y="238" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">③ @GetMapping("/") controller? → handle it   |   else → 404</text>
</svg>

Static `index.html` has highest priority; template `index` is next; then `@Controller`; then 404.

## 5. Runnable example

```java
// WelcomePage.java — run: java WelcomePage.java  (JDK 17+)
// Simulates welcome page resolution logic.

import java.util.*;

public class WelcomePage {

    // Simulates which files / views / controllers exist
    record AppSetup(boolean hasStaticIndex, boolean hasTemplateIndex, boolean hasControllerRoot) {}

    static String resolveRoot(AppSetup setup) {
        // Step 1: WelcomePageHandlerMapping checks static locations
        if (setup.hasStaticIndex()) {
            return "WelcomePageHandlerMapping → serve static/index.html (200 OK)";
        }
        // Step 2: check for template view named 'index'
        if (setup.hasTemplateIndex()) {
            return "WelcomePageHandlerMapping → render template 'index' view (200 OK, server-side data possible)";
        }
        // Step 3: fall through to RequestMappingHandlerMapping
        if (setup.hasControllerRoot()) {
            return "RequestMappingHandlerMapping → @GetMapping(\"/\") controller method";
        }
        // Step 4: 404
        return "No handler found → 404 Not Found";
    }

    static void simulate(String scenario, AppSetup setup) {
        System.out.println("Scenario: " + scenario);
        System.out.printf("  static/index.html: %s | template index: %s | @GetMapping(\"/\"): %s%n",
                setup.hasStaticIndex(), setup.hasTemplateIndex(), setup.hasControllerRoot());
        System.out.println("  GET / → " + resolveRoot(setup));
        System.out.println();
    }

    public static void main(String[] args) {
        simulate("React SPA (index.html in /static/)",
            new AppSetup(true, false, false));

        simulate("Thymeleaf app (templates/index.html)",
            new AppSetup(false, true, false));

        simulate("Both static and template index.html",
            new AppSetup(true, true, false));   // static wins

        simulate("Controller with redirect logic",
            new AppSetup(false, false, true));

        simulate("Nothing configured (API-only service)",
            new AppSetup(false, false, false));

        System.out.println("=== Location of static index.html ===");
        System.out.println("src/main/resources/static/index.html   → served at /");
        System.out.println("src/main/resources/public/index.html   → also works");
        System.out.println();
        System.out.println("=== Thymeleaf template welcome page ===");
        System.out.println("src/main/resources/templates/index.html → rendered by Thymeleaf at /");
        System.out.println("No @Controller needed — WelcomePageHandlerMapping handles the routing");
    }
}
```

**How to run:** `java WelcomePage.java`

## 6. Walkthrough

- `resolveRoot(setup)` checks the three sources in priority order, mirroring `WelcomePageHandlerMapping`'s logic. The static file wins over the template, which wins over the controller.
- **React SPA scenario**: `index.html` in `/static/` contains the entry point for a React bundle. No Spring MVC controller is needed; `GET /` returns the HTML file, and the React router handles sub-paths client-side. Sub-paths like `/app/dashboard` will 404 unless you add a `@RequestMapping("/**")` fallback that returns `index.html`.
- **Thymeleaf scenario**: `templates/index.html` is a Thymeleaf template. Spring Boot routes `GET /` to the view `"index"` — Thymeleaf renders it, potentially with model data if you add a controller. But for a simple landing page with no dynamic data, no controller is needed at all.
- **Both exist**: static wins. If you have both `static/index.html` and `templates/index.html`, the static file is always served. Remove the static file if you want the template to take over.
- **Nothing configured**: an API-only service returns 404 at `/` — expected for a JSON REST service with no HTML front-end.

## 7. Gotchas & takeaways

> **A React SPA that uses client-side routing needs a fallback.** When a user bookmarks `/app/products/42` and loads it directly, Spring Boot looks for a handler for `/app/products/42`, finds none, and returns 404. Solve this with a `@Controller @GetMapping("/**")` that returns `"forward:/index.html"` for all unmatched paths (being careful not to forward `/api/**` requests).

> **If you have both a static `index.html` and a `@GetMapping("/")` controller, the controller is silently ignored.** Spring Boot's `WelcomePageHandlerMapping` runs at a higher priority and intercepts `GET /` before `RequestMappingHandlerMapping` is consulted. The controller will never be called for the root path.

- The welcome page only covers `GET /` — there is no `welcome/page` for `/admin/` or other sub-roots.
- For Thymeleaf, the view name `"index"` maps to `templates/index.html` by default — no explicit mapping needed.
- `spring.web.resources.static-locations` changes where Spring Boot looks for static files, including `index.html`.
- `spring.mvc.static-path-pattern=/ui/**` does NOT affect welcome page resolution — `GET /` is still handled by `WelcomePageHandlerMapping` regardless.
- In production, a CDN or nginx usually serves the actual static files; Spring Boot handles API requests. The welcome page mechanism is most useful in development and monolithic deployments.

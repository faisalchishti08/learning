---
card: spring-boot
gi: 112
slug: template-engines-thymeleaf-freemarker-groovy-mustache
title: Template engines (Thymeleaf, FreeMarker, Groovy, Mustache)
---

## 1. What it is

Spring Boot auto-configures template engine integration when the engine's starter is added to the classpath. Server-side templates render dynamic HTML by combining a template file with data from the Spring MVC `Model`.

Supported engines and their starters:

| Engine | Starter | Template location | Suffix |
|---|---|---|---|
| Thymeleaf | `spring-boot-starter-thymeleaf` | `classpath:/templates/` | `.html` |
| FreeMarker | `spring-boot-starter-freemarker` | `classpath:/templates/` | `.ftlh` |
| Groovy Templates | `spring-boot-starter-groovy-templates` | `classpath:/templates/` | `.tpl` |
| Mustache | `spring-boot-starter-mustache` | `classpath:/templates/` | `.mustache` |

A controller returns a view name (string). Spring MVC routes the name through the appropriate `ViewResolver`, which finds the template file, renders it with the model data, and returns the resulting HTML response.

## 2. Why & when

Use a template engine when:
- You build a server-rendered web application (as opposed to a SPA with a separate front-end).
- You need to embed server-side data in HTML (user names, tables, lists, conditional display).
- You want to use layouts, fragments, and partials to avoid repeating HTML structure.

**Choosing an engine:**
- **Thymeleaf** — most popular in Spring Boot ecosystem. Valid HTML templates work in browsers (natural templates). Rich dialect for security, Spring MVC integration, layout inheritance. Best default.
- **FreeMarker** — mature, fast, good for non-HTML output (emails, reports, text files). Less HTML-natural than Thymeleaf.
- **Groovy Templates** — uses Groovy markup builder syntax; niche. Good if your team is Groovy-first.
- **Mustache** — logic-less templates (no conditionals in template, only in model). Fast, works server-side and client-side. Good for shared templates.

## 3. Core concept

All four engines follow the same Spring MVC lifecycle:

```
@Controller method
  → return "view-name"
  → ViewResolver resolves "view-name" + template directory + suffix
  → Template file rendered with Model data
  → HTML written to response
```

**Thymeleaf example** (`templates/orders.html`):
```html
<!DOCTYPE html>
<html xmlns:th="http://www.thymeleaf.org">
<body>
  <h1 th:text="${title}">Default Title</h1>
  <ul>
    <li th:each="order : ${orders}" th:text="${order.id + ': ' + order.status}">order</li>
  </ul>
</body>
</html>
```

**FreeMarker example** (`templates/orders.ftlh`):
```html
<h1>${title}</h1>
<ul>
  <#list orders as order>
    <li>${order.id}: ${order.status}</li>
  </#list>
</ul>
```

**Mustache example** (`templates/orders.mustache`):
```html
<h1>{{title}}</h1>
<ul>
  {{#orders}}
  <li>{{id}}: {{status}}</li>
  {{/orders}}
</ul>
```

Key Thymeleaf configuration:
```properties
spring.thymeleaf.cache=false           # disable in dev (enable in prod)
spring.thymeleaf.prefix=classpath:/templates/
spring.thymeleaf.suffix=.html
spring.thymeleaf.mode=HTML
spring.thymeleaf.encoding=UTF-8
```

## 4. Diagram

<svg viewBox="0 0 680 260" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Template rendering pipeline: controller adds data to Model, ViewResolver maps name to template file, template engine merges model and template into HTML response">
  <rect x="8" y="8" width="664" height="244" rx="12" fill="#161b22" stroke="#30363d" stroke-width="1"/>
  <text x="340" y="33" fill="#e6edf3" font-size="14" text-anchor="middle" font-family="sans-serif" font-weight="bold">Template Engine Rendering Pipeline</text>

  <!-- Controller -->
  <rect x="20" y="55" width="140" height="55" rx="6" fill="#1c2430" stroke="#6db33f" stroke-width="2"/>
  <text x="90" y="73" fill="#6db33f" font-size="10" text-anchor="middle" font-family="sans-serif">@Controller</text>
  <text x="90" y="88" fill="#e6edf3" font-size="8" text-anchor="middle" font-family="monospace">model.add("orders", …)</text>
  <text x="90" y="101" fill="#8b949e" font-size="8" text-anchor="middle" font-family="monospace">return "orders"</text>

  <defs><marker id="te" markerWidth="7" markerHeight="7" refX="5" refY="3" orient="auto"><path d="M0,0 L5,3 L0,6 Z" fill="#8b949e"/></marker></defs>
  <line x1="162" y1="82" x2="190" y2="82" stroke="#8b949e" stroke-width="1.5" marker-end="url(#te)"/>

  <!-- ViewResolver -->
  <rect x="192" y="55" width="170" height="55" rx="6" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="277" y="73" fill="#79c0ff" font-size="10" text-anchor="middle" font-family="sans-serif">ViewResolver</text>
  <text x="277" y="88" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">"orders" →</text>
  <text x="277" y="101" fill="#e6edf3" font-size="8" text-anchor="middle" font-family="monospace">templates/orders.html</text>

  <line x1="364" y1="82" x2="392" y2="82" stroke="#8b949e" stroke-width="1.5" marker-end="url(#te)"/>

  <!-- Template engine -->
  <rect x="394" y="55" width="160" height="55" rx="6" fill="#1c2430" stroke="#6db33f" stroke-width="2"/>
  <text x="474" y="73" fill="#6db33f" font-size="10" text-anchor="middle" font-family="sans-serif">Template Engine</text>
  <text x="474" y="88" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">merges Model + template</text>
  <text x="474" y="101" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">produces HTML string</text>

  <line x1="556" y1="82" x2="585" y2="82" stroke="#8b949e" stroke-width="1.5" marker-end="url(#te)"/>

  <!-- Response -->
  <rect x="587" y="55" width="80" height="55" rx="6" fill="#1c2430" stroke="#f0883e" stroke-width="1.5"/>
  <text x="627" y="75" fill="#f0883e" font-size="10" text-anchor="middle" font-family="sans-serif">200 OK</text>
  <text x="627" y="90" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">text/html</text>
  <text x="627" y="103" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">HTML body</text>

  <!-- Engine comparison table -->
  <rect x="20" y="135" width="640" height="110" rx="6" fill="#1c2430" stroke="#8b949e" stroke-width="1"/>
  <text x="340" y="153" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif" font-weight="bold">Template Engine Comparison</text>

  <!-- headers -->
  <text x="40" y="170" fill="#79c0ff" font-size="8" font-family="sans-serif">Engine</text>
  <text x="140" y="170" fill="#79c0ff" font-size="8" font-family="sans-serif">Variable syntax</text>
  <text x="280" y="170" fill="#79c0ff" font-size="8" font-family="sans-serif">Loop syntax</text>
  <text x="410" y="170" fill="#79c0ff" font-size="8" font-family="sans-serif">Suffix</text>
  <text x="470" y="170" fill="#79c0ff" font-size="8" font-family="sans-serif">Key feature</text>

  <text x="40"  y="185" fill="#e6edf3" font-size="8" font-family="sans-serif">Thymeleaf</text>
  <text x="140" y="185" fill="#e6edf3" font-size="8" font-family="monospace">th:text="${name}"</text>
  <text x="280" y="185" fill="#e6edf3" font-size="8" font-family="monospace">th:each="x:${xs}"</text>
  <text x="410" y="185" fill="#e6edf3" font-size="8" font-family="monospace">.html</text>
  <text x="470" y="185" fill="#8b949e" font-size="8" font-family="sans-serif">natural HTML, browser preview</text>

  <text x="40"  y="200" fill="#e6edf3" font-size="8" font-family="sans-serif">FreeMarker</text>
  <text x="140" y="200" fill="#e6edf3" font-size="8" font-family="monospace">${name}</text>
  <text x="280" y="200" fill="#e6edf3" font-size="8" font-family="monospace">&lt;#list xs as x&gt;</text>
  <text x="410" y="200" fill="#e6edf3" font-size="8" font-family="monospace">.ftlh</text>
  <text x="470" y="200" fill="#8b949e" font-size="8" font-family="sans-serif">non-HTML output, mature</text>

  <text x="40"  y="215" fill="#e6edf3" font-size="8" font-family="sans-serif">Mustache</text>
  <text x="140" y="215" fill="#e6edf3" font-size="8" font-family="monospace">{{name}}</text>
  <text x="280" y="215" fill="#e6edf3" font-size="8" font-family="monospace">{{#xs}}…{{/xs}}</text>
  <text x="410" y="215" fill="#e6edf3" font-size="8" font-family="monospace">.mustache</text>
  <text x="470" y="215" fill="#8b949e" font-size="8" font-family="sans-serif">logic-less, fast</text>

  <text x="40"  y="230" fill="#e6edf3" font-size="8" font-family="sans-serif">Groovy</text>
  <text x="140" y="230" fill="#e6edf3" font-size="8" font-family="monospace">${name}</text>
  <text x="280" y="230" fill="#e6edf3" font-size="8" font-family="monospace">each(xs) { x -></text>
  <text x="410" y="230" fill="#e6edf3" font-size="8" font-family="monospace">.tpl</text>
  <text x="470" y="230" fill="#8b949e" font-size="8" font-family="sans-serif">Groovy DSL builder</text>
</svg>

All engines share the same controller/model/view-name pattern; only the template syntax differs.

## 5. Runnable example

```java
// TemplateEngines.java — run: java TemplateEngines.java  (JDK 17+)
// Simulates how each template engine renders a model into HTML output.

import java.util.*;

public class TemplateEngines {

    record Order(long id, String status, double total) {}
    record Model(String title, List<Order> orders) {}

    // ── Simulated Thymeleaf rendering ────────────────────────────────────────
    static String renderThymeleaf(Model m) {
        StringBuilder sb = new StringBuilder();
        sb.append("<!-- Thymeleaf output (th:text replaces static content) -->\n");
        sb.append("<h1>").append(m.title()).append("</h1>\n<ul>\n");
        for (Order o : m.orders())
            sb.append("  <li>").append(o.id()).append(": ").append(o.status())
              .append(" — $").append(o.total()).append("</li>\n");
        return sb.append("</ul>").toString();
    }

    // ── Simulated FreeMarker rendering ───────────────────────────────────────
    static String renderFreeMarker(Model m) {
        StringBuilder sb = new StringBuilder();
        sb.append("<!-- FreeMarker output (${expr} and <#list>) -->\n");
        sb.append("<h1>").append(m.title()).append("</h1>\n<ul>\n");
        for (Order o : m.orders())
            sb.append("  <li>").append(o.id()).append(": ").append(o.status())
              .append(" — $").append(o.total()).append("</li>\n");
        return sb.append("</ul>").toString();
    }

    // ── Simulated Mustache rendering ─────────────────────────────────────────
    static String renderMustache(Model m) {
        StringBuilder sb = new StringBuilder();
        sb.append("<!-- Mustache output ({{var}} and {{#list}}…{{/list}}) -->\n");
        sb.append("<h1>").append(m.title()).append("</h1>\n<ul>\n");
        for (Order o : m.orders())
            sb.append("  <li>").append(o.id()).append(": ").append(o.status())
              .append(" — $").append(o.total()).append("</li>\n");
        return sb.append("</ul>").toString();
    }

    public static void main(String[] args) {
        Model model = new Model(
            "Order Report",
            List.of(
                new Order(1001, "SHIPPED", 49.99),
                new Order(1002, "PENDING", 129.50),
                new Order(1003, "DELIVERED", 9.95)
            )
        );

        System.out.println("=== Controller (same for all engines) ===");
        System.out.println("@GetMapping(\"/orders\")");
        System.out.println("public String orders(Model model) {");
        System.out.println("    model.addAttribute(\"title\", \"Order Report\");");
        System.out.println("    model.addAttribute(\"orders\", orderService.findAll());");
        System.out.println("    return \"orders\";  // view name — no extension");
        System.out.println("}");
        System.out.println();

        System.out.println("=== Thymeleaf (templates/orders.html) ===");
        System.out.println(renderThymeleaf(model));

        System.out.println("\n=== FreeMarker (templates/orders.ftlh) ===");
        System.out.println(renderFreeMarker(model));

        System.out.println("\n=== Mustache (templates/orders.mustache) ===");
        System.out.println(renderMustache(model));

        System.out.println("\n=== Caching (performance) ===");
        System.out.println("spring.thymeleaf.cache=false   # dev: reloads templates on change");
        System.out.println("spring.thymeleaf.cache=true    # prod: compiled template cached");
        System.out.println("(same property for freemarker: spring.freemarker.cache=…)");
    }
}
```

**How to run:** `java TemplateEngines.java`

## 6. Walkthrough

- All three `render*` methods receive the same `Model` record (simulating `org.springframework.ui.Model`) and produce the same HTML. In real Spring Boot, the template file holds the syntax; the engine processes it at runtime with model data.
- `return "orders"` in the controller is the view name. Spring's `ThymeleafViewResolver` prepends `classpath:/templates/` and appends `.html`. `FreeMarkerViewResolver` appends `.ftlh`. `MustacheViewResolver` appends `.mustache`. The suffix is configurable.
- `model.addAttribute("title", …)` puts data into the request-scoped `Model`. Thymeleaf accesses it via `${title}`, FreeMarker via `${title}`, Mustache via `{{title}}`. The variable names are the `addAttribute` keys.
- Caching: in development, disable template caching so you can edit templates and refresh the browser without restarting the application. In production, always enable caching — parsing and compiling templates on every request adds significant latency.
- Thymeleaf "natural templates": unlike FreeMarker or Mustache, a Thymeleaf template is valid HTML that renders meaningfully in a browser even without the Spring Boot server. `th:text="${title}"` replaces the static element content, but the static content is still visible when the file is opened directly. This enables design-time preview.

## 7. Gotchas & takeaways

> **Spring Boot does not support multiple template engines for the same view name.** If you add both `spring-boot-starter-thymeleaf` and `spring-boot-starter-mustache`, Spring Boot registers both `ViewResolver` beans. Spring MVC tries each resolver in priority order. `ThymeleafViewResolver` has higher priority, so it always wins for `.html` view names. Keep only one template engine per application unless you intentionally serve different content types from different resolvers.

> **`spring.thymeleaf.cache=false` does NOT enable live reload.** Templates are reloaded from disk on each request, but you still need to copy the file to the classpath (which `spring-boot-devtools` does automatically). Without devtools, changing `src/main/resources/templates/orders.html` while the app is running has no effect until the app restarts (even with `cache=false`), because the classpath resource is loaded from the compiled/packaged output directory.

- Thymeleaf's `@{/css/style.css}` URL expression automatically applies the context path — use it instead of hardcoded paths.
- For email templates (non-HTTP context), use `TemplateEngine.process(templateName, context)` directly — no Spring MVC needed.
- `ITemplateResolver` allows serving templates from a database, a CDN, or any other source — not just the classpath.
- FreeMarker is preferred for code generation or report generation where the output is not HTML (Thymeleaf is HTML-specific).
- Mustache's logic-less design forces clean separation of concerns: complex conditional logic must live in the `@Controller`, not the template.

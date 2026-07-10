---
card: spring-framework
gi: 341
slug: thymeleaf-freemarker-groovy-markup-views
title: "Thymeleaf, FreeMarker, Groovy markup views"
---

## 1. What it is

Thymeleaf, FreeMarker, and Groovy Markup are three interchangeable server-side template engines Spring MVC can use to render HTML views. Each plugs in via its own `ViewResolver`/`View` implementation (see the previous card) and is autoconfigured by Spring Boot the moment the corresponding starter dependency is added — `spring-boot-starter-thymeleaf`, `spring-boot-starter-freemarker`, or `spring-boot-starter-groovy-templates`.

```html
<!-- Thymeleaf: valid HTML, attributes drive templating -->
<h1 th:text="${product.name}">Default</h1>

<!-- FreeMarker: its own directive syntax -->
<h1>${product.name}</h1>

<!-- Groovy Markup: a Groovy DSL, not HTML text at all -->
h1(product.name)
```

## 2. Why & when

All three solve the same problem — turning a `Model` into HTML — but with different tradeoffs:

- **Thymeleaf** is the modern Spring Boot default. Its templates are *valid HTML* even before processing (attributes like `th:text` are ignored by browsers viewing the raw file), so designers can open a template directly in a browser and see realistic markup — a property called "natural templating." This is why it's the recommended default for new Spring Boot projects.
- **FreeMarker** predates Thymeleaf and uses its own directive syntax (`<#if>`, `${...}`) rather than HTML attributes. It's not natural-template-friendly (raw `.ftl` files don't render sensibly in a browser) but is mature, fast, and still common in legacy codebases or teams already invested in FreeMarker elsewhere.
- **Groovy Markup** defines templates as a Groovy DSL (builder syntax), not text-based markup at all — appealing to teams already writing Groovy who want templates as executable Groovy code with full IDE support for the language, at the cost of being unusual for anyone unfamiliar with Groovy.

Choose Thymeleaf for new projects unless there's a specific reason (existing FreeMarker templates, Groovy-heavy team) to pick otherwise.

## 3. Core concept

```
All three plug into the SAME View/ViewResolver contract:

  Controller returns "product-detail"
        |
        v
  [ThymeleafViewResolver | FreeMarkerViewResolver | GroovyMarkupViewResolver]
        |
        v
  resolves to a template file:
    Thymeleaf:      templates/product-detail.html
    FreeMarker:     templates/product-detail.ftl
    Groovy Markup:  templates/product-detail.tpl
        |
        v
  View.render(model, request, response) processes the template,
  substituting model attributes, writes HTML to the response

Thymeleaf template opened raw in a browser:
  <h1 th:text="${product.name}">Default Name</h1>
  -> browser shows "Default Name" (attribute ignored, text content shown)
  -> Spring-rendered version shows "Drill" (attribute processed, content replaced)

FreeMarker template opened raw in a browser:
  <h1>${product.name}</h1>
  -> browser shows literally "${product.name}" (not natural — meaningless unprocessed)
```

## 4. Diagram

<svg viewBox="0 0 740 220" xmlns="http://www.w3.org/2000/svg" font-family="monospace" font-size="12">
  <rect width="740" height="220" fill="#0d1117"/>
  <text x="370" y="22" text-anchor="middle" fill="#8b949e">Three template engines, one View/ViewResolver contract</text>

  <rect x="20" y="50" width="220" height="70" rx="5" fill="#1c2430" stroke="#6db33f"/>
  <text x="130" y="72" text-anchor="middle" fill="#6db33f">Thymeleaf</text>
  <text x="130" y="90" text-anchor="middle" fill="#8b949e" font-size="10">valid HTML + th: attrs</text>
  <text x="130" y="105" text-anchor="middle" fill="#8b949e" font-size="10">"natural templating"</text>

  <rect x="260" y="50" width="220" height="70" rx="5" fill="#1c2430" stroke="#79c0ff"/>
  <text x="370" y="72" text-anchor="middle" fill="#79c0ff">FreeMarker</text>
  <text x="370" y="90" text-anchor="middle" fill="#8b949e" font-size="10">own directive syntax</text>
  <text x="370" y="105" text-anchor="middle" fill="#8b949e" font-size="10">mature, legacy-common</text>

  <rect x="500" y="50" width="220" height="70" rx="5" fill="#1c2430" stroke="#8b949e"/>
  <text x="610" y="72" text-anchor="middle" fill="#8b949e">Groovy Markup</text>
  <text x="610" y="90" text-anchor="middle" fill="#8b949e" font-size="10">Groovy DSL, not text markup</text>

  <line x1="130" y1="120" x2="370" y2="160" stroke="#8b949e" marker-end="url(#a17)"/>
  <line x1="370" y1="120" x2="370" y2="160" stroke="#8b949e" marker-end="url(#a17)"/>
  <line x1="610" y1="120" x2="370" y2="160" stroke="#8b949e" marker-end="url(#a17)"/>

  <rect x="230" y="160" width="280" height="45" rx="4" fill="#1c2430" stroke="#8b949e" stroke-dasharray="3,3"/>
  <text x="370" y="187" text-anchor="middle" fill="#e6edf3" font-size="10">View / ViewResolver contract (rendered HTML out)</text>

  <defs>
    <marker id="a17" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto">
      <path d="M0,0 L0,6 L8,3 z" fill="#8b949e"/>
    </marker>
  </defs>
</svg>

*Different syntax, different tradeoffs, but all three plug into the same `DispatcherServlet` rendering pipeline.*

## 5. Runnable example

### Level 1 — Basic

The same product page rendered with Thymeleaf:

```java
// ProductController.java
import org.springframework.stereotype.Controller;
import org.springframework.ui.Model;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;

@Controller
public class ProductController {

    record Product(long id, String name, double price) {}

    @GetMapping("/products/{id}")
    public String detail(@PathVariable long id, Model model) {
        model.addAttribute("product", new Product(id, "Drill", 29.99));
        return "product-detail";
    }
}
```

`src/main/resources/templates/product-detail.html` (Thymeleaf — with `spring-boot-starter-thymeleaf`):
```html
<!DOCTYPE html>
<html xmlns:th="http://www.thymeleaf.org">
<body>
  <h1 th:text="${product.name}">Default</h1>
  <p th:text="'$' + ${product.price}">$0.00</p>
</body>
</html>
```

**How to run:**
```bash
./mvnw spring-boot:run
curl http://localhost:8080/products/1
# <html>...<h1>Drill</h1><p>$29.99</p>...</html>
```

Open `product-detail.html` directly in a browser (not through Spring) and you'll see `"Default"` and `"$0.00"` — valid, readable HTML even unprocessed, because `th:text` is just an HTML attribute browsers ignore.

### Level 2 — Intermediate

The exact same controller, but rendered with FreeMarker instead — showing the swap requires only a dependency and template file change, not controller code changes:

```xml
<!-- pom.xml: swap Thymeleaf starter for FreeMarker's -->
<dependency>
    <groupId>org.springframework.boot</groupId>
    <artifactId>spring-boot-starter-freemarker</artifactId>
</dependency>
```

`src/main/resources/templates/product-detail.ftl` (FreeMarker):
```html
<!DOCTYPE html>
<html>
<body>
  <h1>${product.name}</h1>
  <p>$${product.price}</p>
  <#if product.price gt 25>
    <p>Premium item</p>
  </#if>
</body>
</html>
```

```java
// ProductController.java — UNCHANGED from Level 1
import org.springframework.stereotype.Controller;
import org.springframework.ui.Model;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;

@Controller
public class ProductController {

    record Product(long id, String name, double price) {}

    @GetMapping("/products/{id}")
    public String detail(@PathVariable long id, Model model) {
        model.addAttribute("product", new Product(id, "Drill", 29.99));
        return "product-detail";      // SAME view name, resolves to .ftl now instead of .html
    }
}
```

**How to run:**
```bash
./mvnw spring-boot:run
curl http://localhost:8080/products/1
# <html>...<h1>Drill</h1><p>$29.99</p><p>Premium item</p>...</html>
```

**What changed:** The controller returns the identical view name `"product-detail"` — it has no idea which template engine is actually rendering it. `FreeMarkerViewResolver` (autoconfigured once `spring-boot-starter-freemarker` is present) resolves `"product-detail"` to `product-detail.ftl` instead of `.html`, using FreeMarker's own `<#if>` directive syntax for the conditional "Premium item" text. This demonstrates the View/ViewResolver contract's payoff: swapping template engines is a configuration and template-file change, not a controller rewrite.

### Level 3 — Advanced

Production concern: mixing Thymeleaf fragments for reusable layout pieces (header/footer) across many pages, plus locale-aware rendering (internationalized text) — the kind of structure a real multi-page application needs, not just a single isolated template:

```html
<!-- templates/fragments/layout.html — reusable fragment -->
<!DOCTYPE html>
<html xmlns:th="http://www.thymeleaf.org">
<body>
  <div th:fragment="header">
    <nav><a href="/">Acme Tools</a></nav>
  </div>
  <div th:fragment="footer">
    <footer th:text="#{footer.copyright(${currentYear})}">© 2026 Acme Tools</footer>
  </div>
</body>
</html>
```

```html
<!-- templates/product-detail.html -->
<!DOCTYPE html>
<html xmlns:th="http://www.thymeleaf.org">
<body>
  <div th:replace="~{fragments/layout :: header}"></div>

  <h1 th:text="${product.name}">Default</h1>
  <p th:text="#{product.price.label(${product.price})}">Price</p>

  <div th:replace="~{fragments/layout :: footer}"></div>
</body>
</html>
```

`src/main/resources/messages.properties` (default locale):
```properties
product.price.label=Price: ${'$'}{0}
footer.copyright=© {0} Acme Tools
```

`src/main/resources/messages_fr.properties` (French):
```properties
product.price.label=Prix : {0} $
footer.copyright=© {0} Acme Tools — tous droits réservés
```

```java
// ProductController.java (production version)
import org.springframework.stereotype.Controller;
import org.springframework.ui.Model;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;

@Controller
public class ProductController {

    record Product(long id, String name, double price) {}

    @GetMapping("/products/{id}")
    public String detail(@PathVariable long id, Model model) {
        model.addAttribute("product", new Product(id, "Drill", 29.99));
        model.addAttribute("currentYear", java.time.Year.now().getValue());
        return "product-detail";
    }
}
```

**How to run:**
```bash
./mvnw spring-boot:run

curl http://localhost:8080/products/1
# English (default): "Price: $29.99" ... "© 2026 Acme Tools"

curl -H "Accept-Language: fr" http://localhost:8080/products/1
# French: "Prix : 29.99 $" ... "© 2026 Acme Tools — tous droits réservés"
```

**What changed and why:**
- `th:replace` pulls in the `header`/`footer` fragments from a separate file — every page needing the same navigation/footer references the fragment instead of duplicating the markup, so a design change to the footer happens in one place.
- `#{...}` (Thymeleaf's message-expression syntax) resolves text through Spring's `MessageSource`, automatically picking `messages_fr.properties` when the request's `Accept-Language` header (or a configured locale resolver) indicates French, and falling back to `messages.properties` otherwise — internationalization without any template duplication per language.
- This mirrors how a real multi-page Spring MVC application is structured: shared fragments for consistent layout, externalized message bundles for translatable text, keeping individual page templates focused on their own unique content.

## 6. Walkthrough

**Request: `GET /products/1` with `Accept-Language: fr` (Level 3 code).**

1. `DispatcherServlet` dispatches to `detail(1, model)`. The handler populates `model` with `product` and `currentYear`, returns `"product-detail"`.
2. `ThymeleafViewResolver` resolves this to `templates/product-detail.html`, producing a `ThymeleafView`.
3. `DispatcherServlet` calls `view.render(model, request, response)`. Before processing the template, Thymeleaf's Spring integration determines the request's `Locale` — Spring's configured `LocaleResolver` reads the `Accept-Language: fr` header and resolves `Locale.FRENCH`.
4. Template processing begins: `<div th:replace="~{fragments/layout :: header}">` is resolved first — Thymeleaf loads `fragments/layout.html`, extracts the `header` fragment, and splices its content in place of the `<div>`.
5. `<h1 th:text="${product.name}">` evaluates the OGNL/SpEL-like expression `${product.name}` against the model → `"Drill"`, replacing the default text.
6. `<p th:text="#{product.price.label(${product.price})}">` evaluates the *inner* expression `${product.price}` first → `29.99`. Then it looks up the message key `product.price.label` in the resolved locale's message bundle — because `Locale.FRENCH` was determined in step 3, Thymeleaf's `MessageSource` integration checks `messages_fr.properties` first, finds `"Prix : {0} $"`, and substitutes the price: `"Prix : 29.99 $"`.
7. The footer fragment is spliced in similarly, with `footer.copyright` resolved from the French bundle and `{0}` substituted with `currentYear` (`2026`).
8. Final assembled HTML is written to the response:
   ```
   HTTP/1.1 200 OK
   Content-Type: text/html;charset=UTF-8

   <html>...<nav>Acme Tools</nav><h1>Drill</h1><p>Prix : 29.99 $</p><footer>© 2026 Acme Tools — tous droits réservés</footer>...</html>
   ```

## 7. Gotchas & takeaways

> **FreeMarker and Groovy Markup templates are not "natural" — opening the raw file in a browser shows meaningless unprocessed syntax**, unlike Thymeleaf's HTML-attribute-driven approach. This matters for designer/developer collaboration workflows where non-developers need to preview templates without running the full application.

> **Switching template engines mid-project is rarely as clean as the Level 2 example suggests** once templates use engine-specific features extensively (Thymeleaf fragments, FreeMarker macros, Groovy DSL blocks) — the `View`/`ViewResolver` abstraction keeps the *controller* code portable, but template *content* itself is not portable between engines without rewriting.

> **Message bundle lookups (`#{...}` in Thymeleaf, similar mechanisms in FreeMarker) silently fall back to the key name itself if no matching entry exists in any bundle** (default or locale-specific) — a missing translation doesn't throw an error, it just displays the raw key, which is easy to miss during manual testing but obvious (and embarrassing) in production if a key like `product.price.label` shows up in the rendered page.

- Thymeleaf is the Spring Boot default and recommended choice for new projects, due to natural templating and strong Spring integration.
- FreeMarker remains common in legacy codebases; Groovy Markup suits teams already invested in Groovy.
- All three implement the same `View`/`ViewResolver` contract, so controller code is engine-agnostic — only the template files and dependency differ.
- Use fragments/macros for shared layout pieces and externalized message bundles for translatable text, regardless of which engine you choose.

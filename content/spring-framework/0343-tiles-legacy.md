---
card: spring-framework
gi: 343
slug: tiles-legacy
title: "Tiles (legacy)"
---

## 1. What it is

Apache Tiles is a templating framework that composes full pages out of reusable layout "tiles" — a page layout definition references named regions (header, body, footer), and each region is filled by a separate JSP/template fragment, all wired together through an XML (or annotation-based) tile definition rather than `<jsp:include>` calls scattered through each page. Spring MVC integrates it via `TilesConfigurer` and `TilesView`/`TilesViewResolver`.

```xml
<!-- tiles.xml -->
<tiles-definitions>
    <definition name="base" template="/WEB-INF/layouts/base.jsp">
        <put-attribute name="header" value="/WEB-INF/jsp/fragments/header.jsp"/>
        <put-attribute name="footer" value="/WEB-INF/jsp/fragments/footer.jsp"/>
    </definition>
    <definition name="product-detail" extends="base">
        <put-attribute name="body" value="/WEB-INF/jsp/product-detail-body.jsp"/>
    </definition>
</tiles-definitions>
```

## 2. Why & when

Before Thymeleaf's fragment mechanism (`th:replace`/`th:fragment`) existed, composing a consistent page layout (shared header, navigation, footer) across dozens of JSP pages meant either duplicating that markup everywhere or using `<jsp:include>` scattered through every page — both error-prone at scale. Tiles solved this by centralizing layout composition into named, inheritable **definitions**: a base layout, extended by page-specific definitions that only supply the parts that differ.

You'll encounter Tiles almost exclusively in:
- Legacy Spring MVC applications built before Thymeleaf became the default (roughly pre-2015 era Spring projects), especially larger enterprise applications with many similarly-laid-out pages.
- Migration work — understanding an existing Tiles-based layout structure well enough to replace it with Thymeleaf fragments.

For any new project, Thymeleaf's built-in fragment/layout support (`th:replace`, `th:fragment`, or the third-party `thymeleaf-layout-dialect` for more elaborate layout inheritance) covers the same use case without an extra framework dependency or XML configuration — Tiles is not recommended for new Spring MVC applications.

## 3. Core concept

```
Tiles definition inheritance:

  "base" definition (template = base.jsp, defines regions: header, body, footer)
      |
      | extends
      v
  "product-detail" definition
      supplies: body = product-detail-body.jsp
      inherits: header, footer from "base"

Request flow:
  Controller returns "product-detail"
        |
        v
  TilesViewResolver resolves "product-detail" to the TILES DEFINITION
  of that name (not directly to a JSP file)
        |
        v
  TilesView renders base.jsp as the outer template,
  which itself references ${header}, ${body}, ${footer}
  region markers — Tiles substitutes each with the
  RENDERED OUTPUT of the corresponding JSP fragment
        |
        v
  Final composed HTML written to response
```

The key structural difference from `<jsp:include>`: Tiles definitions are declared once, in a central place, and reused/extended across many page definitions — not repeated as an include directive inside every individual JSP file.

## 4. Diagram

<svg viewBox="0 0 720 230" xmlns="http://www.w3.org/2000/svg" font-family="monospace" font-size="12">
  <rect width="720" height="230" fill="#0d1117"/>
  <text x="360" y="22" text-anchor="middle" fill="#8b949e">Tiles definition inheritance and region composition</text>

  <rect x="20" y="50" width="200" height="70" rx="5" fill="#1c2430" stroke="#6db33f"/>
  <text x="120" y="72" text-anchor="middle" fill="#6db33f">"base" definition</text>
  <text x="120" y="90" text-anchor="middle" fill="#8b949e" font-size="10">template: base.jsp</text>
  <text x="120" y="105" text-anchor="middle" fill="#8b949e" font-size="10">regions: header, body, footer</text>

  <line x1="220" y1="85" x2="280" y2="85" stroke="#8b949e" marker-end="url(#a19)"/>
  <text x="250" y="78" text-anchor="middle" fill="#8b949e" font-size="9">extends</text>

  <rect x="280" y="50" width="220" height="70" rx="5" fill="#1c2430" stroke="#79c0ff"/>
  <text x="390" y="72" text-anchor="middle" fill="#79c0ff">"product-detail"</text>
  <text x="390" y="90" text-anchor="middle" fill="#8b949e" font-size="10">body = product-detail-body.jsp</text>
  <text x="390" y="105" text-anchor="middle" fill="#8b949e" font-size="10">header/footer INHERITED</text>

  <line x1="120" y1="120" x2="120" y2="160" stroke="#6db33f" marker-end="url(#a19)"/>
  <line x1="390" y1="120" x2="230" y2="160" stroke="#79c0ff" marker-end="url(#a19)"/>

  <rect x="60" y="160" width="500" height="45" rx="4" fill="#1c2430" stroke="#8b949e" stroke-dasharray="3,3"/>
  <text x="310" y="187" text-anchor="middle" fill="#e6edf3" font-size="10">base.jsp renders, substituting header/body/footer region output</text>

  <defs>
    <marker id="a19" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto">
      <path d="M0,0 L0,6 L8,3 z" fill="#8b949e"/>
    </marker>
  </defs>
</svg>

*A child definition inherits unset regions from its parent, supplying only what differs for that specific page.*

## 5. Runnable example

### Level 1 — Basic

A minimal Tiles setup with one base layout and one page definition:

```xml
<!-- pom.xml addition -->
<dependency>
    <groupId>org.apache.tiles</groupId>
    <artifactId>tiles-jsp</artifactId>
    <version>3.0.8</version>
</dependency>
```

```java
// TilesConfig.java
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.web.servlet.view.tiles3.TilesConfigurer;
import org.springframework.web.servlet.view.tiles3.TilesViewResolver;

@Configuration
public class TilesConfig {

    @Bean
    public TilesConfigurer tilesConfigurer() {
        TilesConfigurer configurer = new TilesConfigurer();
        configurer.setDefinitions("/WEB-INF/tiles.xml");
        return configurer;
    }

    @Bean
    public TilesViewResolver tilesViewResolver() {
        return new TilesViewResolver();
    }
}
```

```xml
<!-- WEB-INF/tiles.xml -->
<!DOCTYPE tiles-definitions PUBLIC "-//Apache Software Foundation//DTD Tiles Configuration 3.0//EN"
    "http://tiles.apache.org/dtds/tiles-config_3_0.dtd">
<tiles-definitions>
    <definition name="base" template="/WEB-INF/layouts/base.jsp">
        <put-attribute name="header" value="/WEB-INF/jsp/fragments/header.jsp"/>
        <put-attribute name="body" value=""/>
        <put-attribute name="footer" value="/WEB-INF/jsp/fragments/footer.jsp"/>
    </definition>
    <definition name="product-detail" extends="base">
        <put-attribute name="body" value="/WEB-INF/jsp/product-detail-body.jsp"/>
    </definition>
</tiles-definitions>
```

```jsp
<!-- WEB-INF/layouts/base.jsp -->
<%@ taglib prefix="tiles" uri="http://tiles.apache.org/tags-tiles" %>
<html><body>
  <tiles:insertAttribute name="header"/>
  <tiles:insertAttribute name="body"/>
  <tiles:insertAttribute name="footer"/>
</body></html>
```

```jsp
<!-- WEB-INF/jsp/product-detail-body.jsp -->
<h1>${product.name}</h1>
```

```java
// ProductController.java
import org.springframework.stereotype.Controller;
import org.springframework.ui.Model;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;

@Controller
public class ProductController {

    record Product(long id, String name) {}

    @GetMapping("/products/{id}")
    public String detail(@PathVariable long id, Model model) {
        model.addAttribute("product", new Product(id, "Drill"));
        return "product-detail";     // resolves to the TILES DEFINITION named "product-detail"
    }
}
```

**How to run:**
```bash
./mvnw spring-boot:run
curl http://localhost:8080/products/1
# <html><body><nav>...</nav><h1>Drill</h1><footer>...</footer></body></html>
```

The controller's returned view name `"product-detail"` resolves to a **Tiles definition**, not a JSP file directly — `TilesView` then assembles `base.jsp` with the `header`/`body`/`footer` regions filled in from the definition, `body` coming from `product-detail-body.jsp`.

### Level 2 — Intermediate

Multiple page definitions sharing the base layout, each overriding only the `body` region — showing the reuse payoff as pages multiply:

```xml
<!-- WEB-INF/tiles.xml (extended) -->
<tiles-definitions>
    <definition name="base" template="/WEB-INF/layouts/base.jsp">
        <put-attribute name="header" value="/WEB-INF/jsp/fragments/header.jsp"/>
        <put-attribute name="body" value=""/>
        <put-attribute name="footer" value="/WEB-INF/jsp/fragments/footer.jsp"/>
    </definition>

    <definition name="product-detail" extends="base">
        <put-attribute name="body" value="/WEB-INF/jsp/product-detail-body.jsp"/>
    </definition>

    <definition name="product-list" extends="base">
        <put-attribute name="body" value="/WEB-INF/jsp/product-list-body.jsp"/>
    </definition>

    <definition name="checkout" extends="base">
        <put-attribute name="header" value="/WEB-INF/jsp/fragments/checkout-header.jsp"/>  <!-- OVERRIDES the base header -->
        <put-attribute name="body" value="/WEB-INF/jsp/checkout-body.jsp"/>
    </definition>
</tiles-definitions>
```

```java
// ProductController.java (extended)
import org.springframework.stereotype.Controller;
import org.springframework.ui.Model;
import org.springframework.web.bind.annotation.GetMapping;

import java.util.List;

@Controller
public class ProductController {

    record Product(long id, String name) {}

    @GetMapping("/products")
    public String list(Model model) {
        model.addAttribute("products", List.of(new Product(1, "Drill"), new Product(2, "Hammer")));
        return "product-list";     // different Tiles definition, SAME base layout
    }

    @GetMapping("/checkout")
    public String checkout() {
        return "checkout";         // overrides even the header region for a checkout-specific layout
    }
}
```

**How to run:**
```bash
./mvnw spring-boot:run

curl http://localhost:8080/products
# uses base.jsp + standard header + product-list-body.jsp + standard footer

curl http://localhost:8080/checkout
# uses base.jsp + CHECKOUT-SPECIFIC header + checkout-body.jsp + standard footer
```

**What changed:** Three separate page definitions (`product-detail`, `product-list`, `checkout`) all extend `base` — each only declares the `body` (and, for `checkout`, also the `header`) region that differs, inheriting everything else. Adding a fourth page means one new `<definition>` entry, not a new copy of the header/footer include logic.

### Level 3 — Advanced

Production concern: this same layout-inheritance problem, solved with Thymeleaf instead of Tiles — showing what a modern replacement looks like, since new projects should reach for this instead of introducing Tiles:

```html
<!-- templates/layouts/base.html — Thymeleaf's equivalent to Tiles' base.jsp -->
<!DOCTYPE html>
<html xmlns:th="http://www.thymeleaf.org" xmlns:layout="http://www.ultraq.net.nz/thymeleaf/layout">
<body>
  <nav th:replace="~{fragments/header :: header}"></nav>
  <main layout:fragment="content">
    <!-- page-specific content injected here -->
  </main>
  <footer th:replace="~{fragments/footer :: footer}"></footer>
</body>
</html>
```

```html
<!-- templates/product-detail.html — "extends" base.html via layout:decorate -->
<!DOCTYPE html>
<html xmlns:th="http://www.thymeleaf.org" xmlns:layout="http://www.ultraq.net.nz/thymeleaf/layout"
      layout:decorate="~{layouts/base}">
<body>
  <main layout:fragment="content">
    <h1 th:text="${product.name}">Default</h1>
  </main>
</body>
</html>
```

```java
// ProductController.java — UNCHANGED controller code, only templates/tech differ
import org.springframework.stereotype.Controller;
import org.springframework.ui.Model;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;

@Controller
public class ProductController {

    record Product(long id, String name) {}

    @GetMapping("/products/{id}")
    public String detail(@PathVariable long id, Model model) {
        model.addAttribute("product", new Product(id, "Drill"));
        return "product-detail";
    }
}
```

**How to run:**
```xml
<!-- pom.xml: add layout-dialect instead of Tiles -->
<dependency>
    <groupId>nz.net.ultraq.thymeleaf</groupId>
    <artifactId>thymeleaf-layout-dialect</artifactId>
</dependency>
```
```bash
./mvnw spring-boot:run
curl http://localhost:8080/products/1
# <html><body><nav>...</nav><main><h1>Drill</h1></main><footer>...</footer></body></html>
```

**What changed and why:**
- `layout:decorate="~{layouts/base}"` is Thymeleaf Layout Dialect's equivalent to a Tiles `extends` relationship — `product-detail.html` "decorates" (extends) `base.html`, supplying only the `content` fragment, exactly mirroring the Tiles inheritance model but with no XML configuration file, no `TilesConfigurer` bean, and no separate JSP fragment files.
- The controller code is **identical** to the Tiles version — this reinforces the `View`/`ViewResolver` abstraction's payoff again: swapping the entire templating/layout strategy required zero controller changes.
- For any greenfield Spring Boot project, this is the recommended path — Tiles adds an entire extra framework and XML configuration layer to solve a problem Thymeleaf's layout dialect solves natively, with less ceremony.

## 6. Walkthrough

**Request: `GET /checkout` (Level 2 Tiles code, header override).**

1. `DispatcherServlet` dispatches to `checkout()`, which returns the view name `"checkout"`.
2. `TilesViewResolver` looks up `"checkout"` in the loaded Tiles definitions (parsed from `tiles.xml` at startup by `TilesConfigurer`) — finds the `checkout` definition, which `extends="base"`.
3. Tiles resolves the effective attribute set by merging: start with `base`'s attributes (`header=fragments/header.jsp`, `body=""`, `footer=fragments/footer.jsp`), then overlay `checkout`'s own `<put-attribute>` entries, which override `header` (to `checkout-header.jsp`) and `body` (to `checkout-body.jsp`). `footer` is not overridden, so it remains inherited from `base`.
4. `TilesView.render(...)` begins by processing `base.jsp` (the definition's `template`), which contains `<tiles:insertAttribute name="header"/>`, `name="body"`, `name="footer"` tags.
5. For `<tiles:insertAttribute name="header"/>`: Tiles looks up the *effective* (merged) value for `header` — `checkout-header.jsp`, not the base's default — and performs an internal include of that JSP fragment's rendered output at this point in the page.
6. Similarly, `body` inserts `checkout-body.jsp`'s output, and `footer` inserts the inherited `fragments/footer.jsp`'s output (unchanged from `base`).
7. The fully composed HTML — checkout-specific header, checkout body, standard footer — is written to the response:
   ```
   HTTP/1.1 200 OK
   Content-Type: text/html;charset=UTF-8

   <html><body><nav>Checkout — Step 1</nav><div>...checkout form...</div><footer>...</footer></body></html>
   ```

## 7. Gotchas & takeaways

> **Tiles definitions are parsed once at application startup (from `tiles.xml`), not per-request.** Adding a new page's `<definition>` entry requires an application restart to take effect in most configurations — unlike a JSP or Thymeleaf template file, which can often be edited and picked up without a full restart depending on your dev setup.

> **A typo in a Tiles definition's `extends` attribute, or a missing definition name referenced by a controller's returned view name, produces a runtime error only when that specific page is first requested** — not at startup, even though the XML itself is loaded eagerly. This can hide broken definitions until a rarely-visited page is finally hit in production.

> **Tiles is functionally superseded by Thymeleaf's native fragment/layout support (or the `thymeleaf-layout-dialect` for full layout inheritance) for any new Spring Boot project.** There is essentially no reason to introduce Tiles into a new codebase in 2026 — its value was specific to the JSP era before natural-templating engines with built-in layout composition existed.

- Tiles centralizes page layout composition into inheritable XML definitions — a base layout extended by page-specific definitions supplying only what differs.
- It requires JSP (or another Tiles-supported view technology) underneath and the same WAR-packaging considerations as plain JSP.
- Thymeleaf's layout dialect (`layout:decorate`/`layout:fragment`) solves the identical problem for modern Spring Boot applications without XML configuration or a separate framework dependency.
- Only reach for Tiles knowledge when maintaining or migrating an existing legacy application — never introduce it into new work.

---
card: spring-framework
gi: 342
slug: jsp-jstl
title: "JSP & JSTL"
---

## 1. What it is

JSP (JavaServer Pages) is the original Java web view technology — `.jsp` files mixing HTML with embedded Java (`<% ... %>` scriptlets or, preferably, expression language `${...}`) that the servlet container compiles into a servlet at runtime. JSTL (JSP Standard Tag Library) provides a set of custom tags (`<c:if>`, `<c:forEach>`, `<fmt:formatNumber>`) that let templates express control flow and formatting declaratively instead of embedding raw Java scriptlets.

```jsp
<%@ taglib prefix="c" uri="jakarta.tags.core" %>
<h1>${product.name}</h1>
<c:if test="${product.price > 25}">
    <p>Premium item</p>
</c:if>
```

## 2. Why & when

JSP was Spring MVC's original, and for many years default, view technology. Spring Boot 3 / modern deployments have largely moved away from it because JSP requires deployment as a traditional WAR file to a servlet container with JSP support — it is fundamentally incompatible with Spring Boot's embedded-server, executable-JAR deployment model without extra configuration and caveats (embedded Tomcat needs the Jasper JSP engine added explicitly, and embedded Undertow/Jetty support is weaker).

You'll still encounter JSP when:
- Maintaining or extending a legacy Spring MVC application that predates Spring Boot, deployed as a WAR to an external Tomcat/WebLogic/WebSphere.
- Migrating a legacy JSP application incrementally to Thymeleaf, needing to understand the JSP being replaced.
- Working in an enterprise environment where JSP remains institutionally entrenched.

For any new project, prefer Thymeleaf (see the previous card) — it works seamlessly with Spring Boot's embedded-server model and has no WAR-packaging requirement.

## 3. Core concept

```
Request for a JSP-backed view:

  Controller returns "product-detail"
        |
        v
  InternalResourceViewResolver
    prefix: "/WEB-INF/jsp/"
    suffix: ".jsp"
        |
        v
  Resolves to: /WEB-INF/jsp/product-detail.jsp
        |
        v
  Servlet container's JSP engine (Jasper) compiles the .jsp
  into a servlet class (first request only; cached after)
        |
        v
  That servlet executes, mixing static HTML output with
  JSTL tag processing and EL (${...}) evaluation against the model
        |
        v
  Rendered HTML written to the response

WEB-INF placement matters: JSPs under /WEB-INF/ cannot be requested
directly by URL — only reachable via forward from a controller,
which prevents clients from bypassing your MVC layer.
```

## 4. Diagram

<svg viewBox="0 0 720 210" xmlns="http://www.w3.org/2000/svg" font-family="monospace" font-size="12">
  <rect width="720" height="210" fill="#0d1117"/>
  <text x="360" y="22" text-anchor="middle" fill="#8b949e">JSP resolution: WEB-INF placement prevents direct access</text>

  <rect x="20" y="50" width="180" height="50" rx="5" fill="#1c2430" stroke="#79c0ff"/>
  <text x="110" y="80" text-anchor="middle" fill="#79c0ff" font-size="11">Browser request</text>

  <line x1="200" y1="75" x2="250" y2="75" stroke="#8b949e" marker-end="url(#a18)"/>

  <rect x="250" y="50" width="200" height="50" rx="5" fill="#1c2430" stroke="#6db33f"/>
  <text x="350" y="80" text-anchor="middle" fill="#6db33f" font-size="11">Controller (forwards)</text>

  <line x1="450" y1="75" x2="500" y2="75" stroke="#8b949e" marker-end="url(#a18)"/>

  <rect x="500" y="50" width="200" height="50" rx="5" fill="#1c2430" stroke="#8b949e"/>
  <text x="600" y="72" text-anchor="middle" fill="#8b949e" font-size="10">/WEB-INF/jsp/</text>
  <text x="600" y="88" text-anchor="middle" fill="#8b949e" font-size="10">product-detail.jsp</text>

  <line x1="110" y1="100" x2="110" y2="140" stroke="#e6edf3" stroke-dasharray="3,3" marker-end="url(#a18)"/>
  <text x="110" y="160" text-anchor="middle" fill="#e6edf3" font-size="10">direct URL to</text>
  <text x="110" y="175" text-anchor="middle" fill="#e6edf3" font-size="10">/WEB-INF/... -&gt; 404</text>

  <defs>
    <marker id="a18" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto">
      <path d="M0,0 L0,6 L8,3 z" fill="#8b949e"/>
    </marker>
  </defs>
</svg>

*Placing JSPs under `/WEB-INF/` forces every request through the controller — direct URL access to the raw template is blocked by the servlet container.*

## 5. Runnable example

### Level 1 — Basic

A minimal JSP-backed page, packaged and run as a WAR on embedded Tomcat with Jasper added explicitly:

```xml
<!-- pom.xml -->
<packaging>war</packaging>
<dependencies>
    <dependency>
        <groupId>org.springframework.boot</groupId>
        <artifactId>spring-boot-starter-web</artifactId>
    </dependency>
    <dependency>
        <groupId>org.apache.tomcat.embed</groupId>
        <artifactId>tomcat-embed-jasper</artifactId>
    </dependency>
</dependencies>
```

```properties
# application.properties
spring.mvc.view.prefix=/WEB-INF/jsp/
spring.mvc.view.suffix=.jsp
```

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

`src/main/webapp/WEB-INF/jsp/product-detail.jsp`:
```jsp
<html>
<body>
  <h1>${product.name}</h1>
  <p>$${product.price}</p>
</body>
</html>
```

**How to run:**
```bash
./mvnw spring-boot:run
curl http://localhost:8080/products/1
# <html><body><h1>Drill</h1><p>$29.99</p></body></html>

curl -i http://localhost:8080/WEB-INF/jsp/product-detail.jsp
# 404 — direct access to the raw JSP is blocked
```

`spring.mvc.view.prefix`/`suffix` configure `InternalResourceViewResolver` (autoconfigured by Spring Boot when this pair of properties is set), which resolves `"product-detail"` to the JSP path. `${product.name}` is plain JSP Expression Language, evaluated against the model attributes exposed as request attributes.

### Level 2 — Intermediate

Adding JSTL for control flow and formatting instead of scriptlets:

```xml
<!-- pom.xml addition -->
<dependency>
    <groupId>jakarta.servlet.jsp.jstl</groupId>
    <artifactId>jakarta.servlet.jsp.jstl-api</artifactId>
</dependency>
<dependency>
    <groupId>org.glassfish.web</groupId>
    <artifactId>jakarta.servlet.jsp.jstl</artifactId>
</dependency>
```

```java
// ProductController.java (extended)
import org.springframework.stereotype.Controller;
import org.springframework.ui.Model;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;

import java.util.List;

@Controller
public class ProductController {

    record Product(long id, String name, double price) {}

    @GetMapping("/products")
    public String list(Model model) {
        model.addAttribute("products", List.of(
            new Product(1, "Drill", 29.99),
            new Product(2, "Nail", 0.50),
            new Product(3, "Hammer", 14.99)
        ));
        return "product-list";
    }
}
```

`src/main/webapp/WEB-INF/jsp/product-list.jsp`:
```jsp
<%@ taglib prefix="c" uri="jakarta.tags.core" %>
<%@ taglib prefix="fmt" uri="jakarta.tags.fmt" %>
<html>
<body>
  <ul>
    <c:forEach var="product" items="${products}">
      <li>
        ${product.name} —
        <fmt:formatNumber value="${product.price}" type="currency" currencySymbol="$"/>
        <c:if test="${product.price > 25}"> (premium)</c:if>
      </li>
    </c:forEach>
  </ul>
</body>
</html>
```

**How to run:**
```bash
./mvnw spring-boot:run
curl http://localhost:8080/products
# <html>...<li>Drill — $29.99 (premium)</li><li>Nail — $0.50</li><li>Hammer — $14.99</li>...</html>
```

**What changed:** `<c:forEach>` iterates the `products` list declaratively — no embedded `<% for(...) { %>` scriptlet. `<fmt:formatNumber>` handles currency formatting through JSTL's formatting tag library rather than manual Java string formatting. `<c:if>` provides conditional rendering. This is the entire point of JSTL: keeping JSP templates free of raw Java code, which is both more maintainable and safer (scriptlets can execute arbitrary logic, including things that shouldn't belong in a view layer).

### Level 3 — Advanced

Production concern: a `<jsp:include>`-based reusable header/footer (JSP's older mechanism, predating Thymeleaf fragments) plus explicit XSS-safe output escaping — JSP's `${...}` EL does **not** HTML-escape by default, unlike most modern template engines, making this a genuine, historically significant security gotcha:

```jsp
<!-- WEB-INF/jsp/fragments/header.jsp -->
<nav><a href="/">Acme Tools</a></nav>
```

```jsp
<!-- WEB-INF/jsp/product-detail.jsp (production version) -->
<%@ taglib prefix="c" uri="jakarta.tags.core" %>
<html>
<body>
  <jsp:include page="fragments/header.jsp"/>

  <h1><c:out value="${product.name}"/></h1>
  <p>Review: <c:out value="${userReviewText}" escapeXml="true"/></p>
</body>
</html>
```

```java
// ProductController.java (production version)
import org.springframework.stereotype.Controller;
import org.springframework.ui.Model;
import org.springframework.web.bind.annotation.*;

@Controller
public class ProductController {

    record Product(long id, String name, double price) {}

    @GetMapping("/products/{id}")
    public String detail(@PathVariable long id,
                          @RequestParam(required = false, defaultValue = "") String review,
                          Model model) {
        model.addAttribute("product", new Product(id, "Drill", 29.99));
        model.addAttribute("userReviewText", review);   // untrusted, user-supplied input
        return "product-detail";
    }
}
```

**How to run:**
```bash
./mvnw spring-boot:run

curl "http://localhost:8080/products/1?review=<script>alert(1)</script>"
# <p>Review: &lt;script&gt;alert(1)&lt;/script&gt;</p>
# (c:out escapes it safely — displayed as literal text, script NOT executed in a browser)
```

**What changed and why:**
- `<jsp:include>` pulls in `header.jsp` at request time (not compile time) — JSP's original mechanism for sharing layout fragments across pages, predating both Thymeleaf's `th:replace` and even JSP's own newer tag-file mechanism.
- `<c:out value="...">` HTML-escapes its output by default — critically important because raw `${...}` EL expressions in JSP do **not** escape HTML by default, meaning `${userReviewText}` alone would render a submitted `<script>` tag unescaped, directly enabling a reflected XSS vulnerability. Always wrap any value that could contain user-supplied content in `<c:out>` (or explicitly call a JSTL/EL escaping function) rather than using bare `${...}` for untrusted data.
- This is one of the sharpest differences from Thymeleaf, which HTML-escapes `th:text` output by default — JSP's opposite default (unescaped by default, must opt in to escaping) is a well-known source of legacy JSP application vulnerabilities.

## 6. Walkthrough

**Request: `GET /products/1?review=<script>alert(1)</script>` (Level 3 code).**

1. `DispatcherServlet` dispatches to `detail(1, "<script>alert(1)</script>", model)`. The raw query parameter is decoded and bound to `review` via `@RequestParam`.
2. `model.addAttribute("userReviewText", review)` stores the **unescaped, unmodified** string `<script>alert(1)</script>` into the model — no sanitization happens at this layer; that's deliberately deferred to the view.
3. Handler returns `"product-detail"`. `InternalResourceViewResolver` resolves it to `/WEB-INF/jsp/product-detail.jsp` and produces an internal **forward** (not a redirect — see the next card) to that JSP.
4. The servlet container's JSP engine processes the compiled servlet for `product-detail.jsp`. It reaches `<jsp:include page="fragments/header.jsp"/>` first — this triggers a nested request-dispatcher include, executing `header.jsp`'s compiled servlet and inserting its output (`<nav>...</nav>`) directly into the response stream at this point.
5. Continuing: `<c:out value="${product.name}"/>` evaluates `${product.name}` → `"Drill"` (a trusted, server-generated value with no special characters) and writes it, HTML-escaped (though escaping is a no-op here since there's nothing to escape).
6. `<c:out value="${userReviewText}" escapeXml="true"/>` evaluates `${userReviewText}` → the raw string `<script>alert(1)</script>`. Because `escapeXml="true"` (also the default for `<c:out>`), each special character is converted to its HTML entity: `<` → `&lt;`, `>` → `&gt;`.
7. The final HTML written to the response contains the **escaped** text, not executable markup:
   ```
   HTTP/1.1 200 OK
   Content-Type: text/html;charset=UTF-8

   <html><body><nav>...</nav><h1>Drill</h1><p>Review: &lt;script&gt;alert(1)&lt;/script&gt;</p></body></html>
   ```
8. A browser rendering this response displays the literal text `<script>alert(1)</script>` on the page — it does **not** execute as a script, because the browser sees HTML entities, not an actual `<script>` tag.

If step 6 had instead used bare `${userReviewText}` without `<c:out>`, the raw, unescaped `<script>` tag would have been written directly into the HTML — and a browser rendering that response *would* execute the injected script, a textbook reflected XSS vulnerability.

## 7. Gotchas & takeaways

> **Raw JSP EL (`${...}`) does NOT HTML-escape by default — this is the opposite of Thymeleaf's `th:text`, which escapes by default.** Always use `<c:out>` (or an equivalent explicit escaping mechanism) for any value that could contain user-supplied or otherwise untrusted content. This single difference has caused real production XSS vulnerabilities in legacy JSP applications.

> **JSP requires WAR packaging and a servlet container with JSP support — it does not work cleanly with Spring Boot's default embedded-server, executable-JAR model** without adding `tomcat-embed-jasper` (or equivalent) explicitly, and even then, some embedded servers (Undertow) have incomplete JSP support. This is the primary reason new Spring Boot projects avoid JSP.

> **Placing JSPs anywhere other than `/WEB-INF/` (or another protected location) allows clients to request the raw `.jsp` file directly by URL**, bypassing your controller entirely — this can expose the file's compiled-servlet processing to unauthenticated requests that never went through your intended `@GetMapping` logic, model population, or security filters.

- JSP/JSTL is Spring MVC's original view technology; prefer Thymeleaf for new projects due to embedded-server compatibility and safer default escaping.
- Keep JSPs under `/WEB-INF/` so they're only reachable via a controller forward, never by direct URL.
- Use `<c:out>` (or equivalent) for any value that might contain user input — raw `${...}` does not escape HTML by default.
- JSTL tags (`<c:forEach>`, `<c:if>`, `<fmt:formatNumber>`) replace embedded Java scriptlets, keeping business logic out of the view layer.

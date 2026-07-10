---
card: spring-framework
gi: 354
slug: view-controllers-view-resolvers-config
title: "View controllers & view resolvers config"
---

## 1. What it is

`addViewControllers` and `configureViewResolvers` are `WebMvcConfigurer` overrides for two related but distinct concerns: a **view controller** maps a URL directly to a view name with zero controller code (for pages with no dynamic logic — a static "about" page, a redirect shortcut), while **view resolver configuration** registers and orders the `ViewResolver`s that turn view names into renderable `View` instances application-wide.

```java
@Override
public void addViewControllers(ViewControllerRegistry registry) {
    registry.addViewController("/about").setViewName("about");
}

@Override
public void configureViewResolvers(ViewResolverRegistry registry) {
    registry.jsp("/WEB-INF/jsp/", ".jsp");
}
```

## 2. Why & when

Use a **view controller** when a page needs absolutely no controller logic — just rendering a template with no model data, or a redirect. Writing a full `@Controller` class with an empty method body for a static "terms of service" page is unnecessary ceremony; `addViewController` expresses the same intent in one line of configuration.

Use **view resolver configuration** when:
- Building a plain (non-Boot) Spring MVC application, where view resolvers aren't autoconfigured and must be registered explicitly (as seen in the JSP and Tiles cards).
- You need fine control over resolver ordering, or want to register multiple resolvers with explicit precedence in a Spring Boot application beyond what the autoconfigured Thymeleaf resolver already provides.
- You want to add a resolver for a secondary view technology (e.g. a `BeanNameViewResolver` for document views, as seen in the PDF/Excel card) without disabling Boot's autoconfigured primary resolver.

## 3. Core concept

```
addViewControllers (ViewControllerRegistry):

  registry.addViewController("/about").setViewName("about")
      GET /about  ->  directly resolves view "about"  ->  renders
      NO @Controller class, NO @GetMapping, NO Java method at all

  registry.addRedirectViewController("/old-path", "/new-path")
      GET /old-path  ->  302 redirect to /new-path

  registry.addStatusController("/deprecated", HttpStatus.GONE)
      GET /deprecated  ->  410 Gone, no body

configureViewResolvers (ViewResolverRegistry):

  registry.jsp("/WEB-INF/jsp/", ".jsp")          <- registers InternalResourceViewResolver
  registry.viewResolver(myCustomResolver)         <- registers any custom ViewResolver, in order
  registry.enableContentNegotiation(jsonView)     <- wraps registered resolvers in
                                                      ContentNegotiatingViewResolver

Both are WebMvcConfigurer overrides — additive to Spring Boot's
autoconfiguration (Thymeleaf resolver, etc.), UNLESS
configureViewResolvers explicitly disables autoconfigured ones
via registry.viewResolver(...) ordering considerations.
```

## 4. Diagram

<svg viewBox="0 0 720 210" xmlns="http://www.w3.org/2000/svg" font-family="monospace" font-size="12">
  <rect width="720" height="210" fill="#0d1117"/>
  <text x="360" y="22" text-anchor="middle" fill="#8b949e">View controller: URL to view name, zero Java handler code</text>

  <rect x="20" y="50" width="200" height="50" rx="5" fill="#1c2430" stroke="#79c0ff"/>
  <text x="120" y="80" text-anchor="middle" fill="#79c0ff" font-size="11">GET /about</text>

  <line x1="220" y1="75" x2="280" y2="75" stroke="#8b949e" marker-end="url(#a30)"/>

  <rect x="280" y="50" width="220" height="50" rx="5" fill="#1c2430" stroke="#6db33f"/>
  <text x="390" y="72" text-anchor="middle" fill="#6db33f" font-size="10">ViewControllerRegistry</text>
  <text x="390" y="88" text-anchor="middle" fill="#8b949e" font-size="9">"/about" -&gt; view "about"</text>

  <line x1="500" y1="75" x2="560" y2="75" stroke="#8b949e" marker-end="url(#a30)"/>

  <rect x="560" y="50" width="140" height="50" rx="5" fill="#1c2430" stroke="#8b949e"/>
  <text x="630" y="80" text-anchor="middle" fill="#8b949e" font-size="10">rendered HTML</text>

  <text x="360" y="140" text-anchor="middle" fill="#8b949e" font-size="10">No @Controller class, no @GetMapping method — pure configuration</text>

  <defs>
    <marker id="a30" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto">
      <path d="M0,0 L0,6 L8,3 z" fill="#8b949e"/>
    </marker>
  </defs>
</svg>

*A view controller skips writing a controller class entirely for static, logic-free pages.*

## 5. Runnable example

### Level 1 — Basic

A static "about" page and a legacy-URL redirect, with no controller code:

```java
// WebConfig.java
import org.springframework.context.annotation.Configuration;
import org.springframework.web.servlet.config.annotation.ViewControllerRegistry;
import org.springframework.web.servlet.config.annotation.WebMvcConfigurer;

@Configuration
public class WebConfig implements WebMvcConfigurer {
    @Override
    public void addViewControllers(ViewControllerRegistry registry) {
        registry.addViewController("/about").setViewName("about");
        registry.addRedirectViewController("/old-about", "/about");
    }
}
```

`templates/about.html`:
```html
<html xmlns:th="http://www.thymeleaf.org">
<body><h1>About Acme Tools</h1></body>
</html>
```

**How to run:**
```bash
./mvnw spring-boot:run

curl http://localhost:8080/about
# <html>...<h1>About Acme Tools</h1>...</html>

curl -i http://localhost:8080/old-about
# HTTP/1.1 302 Found
# Location: /about
```

No `@Controller` class was written for either route — `addViewController` and `addRedirectViewController` express both purely as configuration, since neither needs any Java logic beyond "render this view" or "redirect to this URL."

### Level 2 — Intermediate

Explicit JSP view resolver configuration for a plain (non-autoconfigured) setup, plus a status-code-only view controller for a deprecated endpoint:

```java
// WebConfig.java (extended)
import org.springframework.context.annotation.Configuration;
import org.springframework.http.HttpStatus;
import org.springframework.web.servlet.config.annotation.ViewControllerRegistry;
import org.springframework.web.servlet.config.annotation.ViewResolverRegistry;
import org.springframework.web.servlet.config.annotation.WebMvcConfigurer;

@Configuration
public class WebConfig implements WebMvcConfigurer {

    @Override
    public void addViewControllers(ViewControllerRegistry registry) {
        registry.addViewController("/about").setViewName("about");
        registry.addRedirectViewController("/old-about", "/about");
        registry.addStatusController("/legacy-api/v1", HttpStatus.GONE);   // 410: this API version is retired
    }

    @Override
    public void configureViewResolvers(ViewResolverRegistry registry) {
        registry.jsp("/WEB-INF/jsp/", ".jsp");
    }
}
```

**How to run:**
```bash
./mvnw spring-boot:run

curl -i http://localhost:8080/legacy-api/v1
# HTTP/1.1 410 Gone
# (empty body)

curl http://localhost:8080/about
# renders /WEB-INF/jsp/about.jsp, using the explicitly configured JSP resolver
```

**What changed:** `addStatusController` maps a URL directly to a fixed HTTP status with no body and no view rendering at all — perfect for explicitly marking a retired endpoint as `410 Gone` rather than letting it fall through to a generic `404`. `configureViewResolvers` explicitly registers a JSP resolver, needed because this hypothetical setup has no Thymeleaf autoconfiguration doing it implicitly (e.g. a plain, non-Boot Spring MVC application, or one deliberately using JSP instead of Thymeleaf).

### Level 3 — Advanced

Production pattern: layering a `BeanNameViewResolver` (for document views, from the earlier PDF/Excel card) alongside Boot's autoconfigured Thymeleaf resolver, with explicit ordering, plus a view controller for a health-check-style static response used by infrastructure tooling:

```java
// WebConfig.java (production version)
import org.springframework.context.annotation.Configuration;
import org.springframework.http.HttpStatus;
import org.springframework.web.servlet.config.annotation.*;
import org.springframework.web.servlet.view.BeanNameViewResolver;

@Configuration
public class WebConfig implements WebMvcConfigurer {

    @Override
    public void addViewControllers(ViewControllerRegistry registry) {
        registry.addViewController("/about").setViewName("about");
        registry.addRedirectViewController("/old-about", "/about");
        registry.addStatusController("/legacy-api/v1", HttpStatus.GONE);

        // A trivial "am I alive" page, rendered without any controller —
        // useful for a load balancer health check that expects a simple 200 + fixed body,
        // separate from the /actuator/health endpoint which carries richer JSON status.
        registry.addViewController("/ping").setViewName("ping");
    }

    @Override
    public void configureViewResolvers(ViewResolverRegistry registry) {
        // We do NOT call registry.jsp(...) or otherwise replace the resolver chain —
        // Boot's autoconfigured Thymeleaf resolver remains the PRIMARY resolver.
        // We only ADD a secondary resolver for bean-backed document views (PDF/Excel).
        BeanNameViewResolver beanNameViewResolver = new BeanNameViewResolver();
        beanNameViewResolver.setOrder(1);   // checked AFTER Thymeleaf's resolver (order 0, autoconfigured)
        registry.viewResolver(beanNameViewResolver);
    }
}
```

`templates/ping.html`:
```html
<html><body>OK</body></html>
```

**How to run:**
```bash
./mvnw spring-boot:run

curl http://localhost:8080/ping
# <html><body>OK</body></html>

curl http://localhost:8080/about
# renders via the autoconfigured Thymeleaf resolver, UNCHANGED
```

**What changed and why:**
- `registry.viewResolver(beanNameViewResolver)` **adds** a resolver to the chain rather than calling `registry.jsp(...)` or otherwise replacing the primary mechanism — this preserves Spring Boot's autoconfigured Thymeleaf resolver as the first-checked resolver for ordinary page names, while still enabling bean-name-based document views (from the earlier PDF/Excel card) as a fallback for view names that match a registered `View` bean instead of a template file.
- `/ping` is deliberately kept separate from `/actuator/health` (Spring Boot Actuator's richer health endpoint) — some infrastructure health checks specifically want the absolute simplest possible response (fixed `200` + tiny fixed body) with no dependency checks or JSON parsing, and a view controller is the lightest possible way to provide that.
- This pattern — additive `WebMvcConfigurer` overrides layered onto Boot's autoconfiguration — is the theme running through every card in this configuration series: customize incrementally, never disable the framework's sensible defaults wholesale.

## 6. Walkthrough

**Request: `GET /about` (Level 3 code).**

1. `DispatcherServlet` checks its registered handler mappings. View controllers registered via `addViewControllers` are handled by a special, very-low-precedence `HandlerMapping` (`SimpleUrlHandlerMapping`, populated by `ViewControllerRegistry`) — it matches `/about` directly to a pre-configured `ParameterizableViewController` whose fixed view name is `"about"`.
2. Because this "handler" does no real processing (it has no method body to execute — it's a framework-provided object, not user code), `DispatcherServlet` proceeds essentially straight to view resolution with the view name `"about"` and an empty model.
3. View resolution consults the registered resolver chain in order: Thymeleaf's autoconfigured resolver (implicit `order = 0`) is checked first, finds `templates/about.html` exists, and returns a `ThymeleafView`. The explicitly registered `BeanNameViewResolver` (`order = 1`) is never even consulted, since the first resolver already produced a match.
4. `ThymeleafView.render(emptyModel, request, response)` processes the static template (no dynamic model attributes needed, since the page has no dynamic content) and writes the HTML.
5. Response:
   ```
   HTTP/1.1 200 OK
   Content-Type: text/html;charset=UTF-8

   <html>...<h1>About Acme Tools</h1>...</html>
   ```

**Request: a hypothetical `GET /invoices/1/pdf`, where `"invoice-pdf"` is a view name matching a registered `View` bean (from the earlier PDF/Excel card), reached via a REAL controller method rather than a view controller.**

1. `DispatcherServlet` matches this request to an actual `@Controller` method (not a view controller — view controllers only apply to the exact static mappings registered via `addViewControllers`), which returns the view name `"invoice-pdf"`.
2. View resolution checks Thymeleaf's resolver first: it looks for `templates/invoice-pdf.html` — no such file exists, so it returns `null` (the correct "not my concern, try the next resolver" signal from the `View`/`ViewResolver` contract card).
3. The chain proceeds to the explicitly registered `BeanNameViewResolver` (`order = 1`): it checks whether a Spring bean named `"invoice-pdf"` exists — finds the `InvoicePdfView` bean registered elsewhere in the configuration — returns it as the resolved `View`.
4. `InvoicePdfView.render(...)` executes (as detailed in the PDF/Excel card), producing binary PDF output.

This demonstrates exactly why resolver **ordering** matters: Thymeleaf's resolver is checked first (appropriate, since most view names in this application are ordinary templates), and the bean-name resolver only catches the specific cases the primary resolver couldn't — a layered fallback, not a replacement.

## 7. Gotchas & takeaways

> **View controllers bypass any interceptor logic that depends on inspecting a `HandlerMethod`** (see the interceptors config card) — since a view controller's "handler" is a `ParameterizableViewController`, not a `HandlerMethod`, an interceptor checking `handler instanceof HandlerMethod` before applying annotation-driven logic will simply skip view-controller-mapped routes entirely. This is usually fine (view controllers have no logic to protect), but worth knowing if you expect an interceptor's checks to apply universally.

> **Calling `registry.jsp(...)` or otherwise registering a resolver via `configureViewResolvers` in a Spring Boot application does not automatically disable Thymeleaf's autoconfigured resolver** — both coexist in the resolver chain unless you take an additional step to explicitly exclude `ThymeleafAutoConfiguration`. If you intended to fully replace Thymeleaf with JSP, you likely also need to exclude the relevant autoconfiguration class, not just add a competing resolver.

> **`addStatusController` produces a response with NO body at all**, not even an empty JSON object — a client expecting *some* content (even an empty `{}`) at a status-controller-mapped URL will simply get zero bytes past the status line and headers. This is appropriate for `410 Gone`/`404`-style "this doesn't exist, full stop" semantics but can surprise a client library that unconditionally tries to parse a response body.

- `addViewControllers` maps URLs directly to view names (or redirects, or fixed statuses) with zero controller code — ideal for static, logic-free pages.
- `configureViewResolvers` registers/orders `ViewResolver`s; in a Spring Boot application, use it additively alongside autoconfiguration rather than to replace it, unless you explicitly disable the relevant autoconfiguration class too.
- Resolver order determines which resolver gets first chance to claim a view name — a resolver returning `null` (not found) falls through to the next one in the chain.
- View controllers don't participate in `HandlerMethod`-based interceptor logic, since they have no underlying Java method to reflect on.

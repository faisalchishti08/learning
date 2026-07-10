---
card: spring-framework
gi: 340
slug: view-viewresolver-contract
title: "View & ViewResolver contract"
---

## 1. What it is

`View` and `ViewResolver` are the two interfaces underlying every server-rendered response in Spring MVC. A `ViewResolver` takes a **view name** (the `String` a `@Controller` method returns) and resolves it to a `View` instance. A `View` takes the model (a `Map<String, Object>`) and writes the actual response — HTML, PDF, Excel, JSON, whatever that particular `View` implementation produces.

```java
public interface ViewResolver {
    View resolveViewName(String viewName, Locale locale) throws Exception;
}

public interface View {
    void render(Map<String, ?> model, HttpServletRequest request, HttpServletResponse response) throws Exception;
}
```

Thymeleaf, JSP, FreeMarker, PDF/Excel generation — every one of these plugs into Spring MVC by providing implementations of these two interfaces.

## 2. Why & when

You rarely implement `View`/`ViewResolver` yourself — Spring Boot autoconfigures a `ThymeleafViewResolver` (or JSP's `InternalResourceViewResolver`) the moment the relevant starter is on the classpath. Understanding the contract matters when:

- You need to support multiple view technologies in one application (Thymeleaf for most pages, a custom `View` for a PDF export endpoint) and want to understand how they're selected.
- You're debugging "why did my view name resolve to the wrong template" — the answer lives in `ViewResolver` ordering and prefix/suffix configuration.
- You want to build a **custom** `View` — e.g. one that streams a generated file, or renders a response format no off-the-shelf resolver supports.
- You need multiple `ViewResolver`s chained together with explicit precedence (e.g. try Thymeleaf first, fall back to a generic message view).

## 3. Core concept

```
Controller returns "product-detail"
        |
        v
ViewResolverComposite tries each registered ViewResolver in ORDER:
  1. ThymeleafViewResolver     (order=1)  -- checks templates/product-detail.html
  2. InternalResourceViewResolver (order=2) -- checks /WEB-INF/jsp/product-detail.jsp
        |
        v
  First resolver that finds a matching template returns a View instance
        |
        v
  DispatcherServlet calls view.render(model, request, response)
        |
        v
  View implementation writes the actual response bytes
    ThymeleafView       -> processes template, writes HTML
    MappingJackson2JsonView -> serializes model to JSON
    AbstractPdfView      -> generates PDF bytes

If NO resolver finds a match for the view name:
  -> exception (e.g. "Could not resolve view with name 'X'")
```

`ViewResolver`s are tried in ascending `order` until one returns a non-null `View`; if none match, resolution fails.

## 4. Diagram

<svg viewBox="0 0 720 240" xmlns="http://www.w3.org/2000/svg" font-family="monospace" font-size="12">
  <rect width="720" height="240" fill="#0d1117"/>
  <text x="360" y="22" text-anchor="middle" fill="#8b949e">View name -&gt; ViewResolver chain -&gt; View -&gt; response</text>

  <rect x="20" y="50" width="160" height="50" rx="5" fill="#1c2430" stroke="#79c0ff"/>
  <text x="100" y="80" text-anchor="middle" fill="#79c0ff" font-size="11">"product-detail"</text>

  <line x1="180" y1="75" x2="230" y2="75" stroke="#8b949e" marker-end="url(#a16)"/>

  <rect x="230" y="50" width="260" height="90" rx="5" fill="#1c2430" stroke="#8b949e"/>
  <text x="360" y="70" text-anchor="middle" fill="#8b949e" font-size="10">ViewResolver chain (by order)</text>
  <text x="250" y="90" fill="#6db33f" font-size="10">1. ThymeleafViewResolver ✓ found</text>
  <text x="250" y="108" fill="#8b949e" font-size="10">2. InternalResourceViewResolver</text>
  <text x="250" y="126" fill="#8b949e" font-size="10">   (not reached)</text>

  <line x1="490" y1="90" x2="550" y2="90" stroke="#6db33f" marker-end="url(#a16)"/>

  <rect x="550" y="65" width="150" height="50" rx="5" fill="#1c2430" stroke="#6db33f"/>
  <text x="625" y="95" text-anchor="middle" fill="#6db33f" font-size="10">ThymeleafView</text>

  <line x1="625" y1="115" x2="360" y2="170" stroke="#6db33f" marker-end="url(#a16)"/>
  <rect x="200" y="170" width="320" height="45" rx="4" fill="#1c2430" stroke="#8b949e"/>
  <text x="360" y="197" text-anchor="middle" fill="#e6edf3" font-size="10">view.render(model, request, response) -&gt; HTML</text>

  <defs>
    <marker id="a16" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto">
      <path d="M0,0 L0,6 L8,3 z" fill="#8b949e"/>
    </marker>
  </defs>
</svg>

*Resolvers are tried in order; the first one that finds a matching template wins and produces the `View` that renders the response.*

## 5. Runnable example

### Level 1 — Basic

The default, implicit resolution — Thymeleaf autoconfigured by Spring Boot, no manual `ViewResolver` code:

```java
// ProductController.java
import org.springframework.stereotype.Controller;
import org.springframework.ui.Model;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;

@Controller
public class ProductController {

    @GetMapping("/products/{id}")
    public String detail(@PathVariable long id, Model model) {
        model.addAttribute("productName", "Drill");
        return "product-detail";     // view name — resolved by Spring Boot's autoconfigured ThymeleafViewResolver
    }
}
```

`src/main/resources/templates/product-detail.html`:
```html
<!DOCTYPE html>
<html xmlns:th="http://www.thymeleaf.org">
<body><h1 th:text="${productName}">Name</h1></body>
</html>
```

**How to run:**
```bash
./mvnw spring-boot:run
curl http://localhost:8080/products/1
# <html>...<h1>Drill</h1>...</html>
```

Behind the scenes: Spring Boot's autoconfiguration registers a `ThymeleafViewResolver` bean because `spring-boot-starter-thymeleaf` is on the classpath. `"product-detail"` is resolved by prefixing/suffixing to `classpath:/templates/product-detail.html`.

### Level 2 — Intermediate

Two `ViewResolver`s explicitly configured with ordering, plus a custom `View` implementation for a plain-text response format not covered by any template engine:

```java
// PlainTextView.java — a custom View implementation
import org.springframework.web.servlet.View;

import jakarta.servlet.http.HttpServletRequest;
import jakarta.servlet.http.HttpServletResponse;
import java.util.Map;

public class PlainTextView implements View {
    private final String content;
    PlainTextView(String content) { this.content = content; }

    @Override
    public String getContentType() { return "text/plain"; }

    @Override
    public void render(Map<String, ?> model, HttpServletRequest request, HttpServletResponse response) throws Exception {
        response.setContentType(getContentType());
        response.getWriter().write(content + " (product: " + model.get("productName") + ")");
    }
}
```

```java
// TextViewResolver.java — a custom ViewResolver
import org.springframework.core.Ordered;
import org.springframework.web.servlet.View;
import org.springframework.web.servlet.ViewResolver;

import java.util.Locale;

public class TextViewResolver implements ViewResolver, Ordered {
    @Override
    public View resolveViewName(String viewName, Locale locale) {
        if (viewName.startsWith("text:")) {
            return new PlainTextView(viewName.substring("text:".length()));
        }
        return null;   // not our concern — let the chain try the next resolver
    }

    @Override
    public int getOrder() { return Ordered.HIGHEST_PRECEDENCE; }   // try this FIRST
}
```

```java
// WebConfig.java
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.web.servlet.ViewResolver;

@Configuration
public class WebConfig {
    @Bean
    public ViewResolver textViewResolver() { return new TextViewResolver(); }
}
```

```java
// ProductController.java (extended)
import org.springframework.stereotype.Controller;
import org.springframework.ui.Model;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;

@Controller
public class ProductController {

    @GetMapping("/products/{id}")
    public String detail(@PathVariable long id, Model model) {
        model.addAttribute("productName", "Drill");
        return "product-detail";      // resolved by ThymeleafViewResolver
    }

    @GetMapping("/products/{id}/plain")
    public String detailPlain(@PathVariable long id, Model model) {
        model.addAttribute("productName", "Drill");
        return "text:Status OK";      // resolved by our custom TextViewResolver
    }
}
```

**How to run:**
```bash
./mvnw spring-boot:run

curl http://localhost:8080/products/1/plain
# Status OK (product: Drill)
# Content-Type: text/plain

curl http://localhost:8080/products/1
# <html>...Drill...</html>     (falls through TextViewResolver since it returns null for "product-detail",
#                                then matched by ThymeleafViewResolver)
```

**What changed:** `TextViewResolver` returns `null` for any view name not prefixed with `"text:"`, which is the contractual signal to Spring's `ViewResolverComposite` to try the *next* resolver in the chain rather than failing. Setting `getOrder()` to `HIGHEST_PRECEDENCE` ensures this custom resolver is checked before Thymeleaf's, but since it only claims `"text:"`-prefixed names, it never interferes with normal template resolution.

### Level 3 — Advanced

Production pattern: content-negotiating view resolution combining multiple underlying view technologies (Thymeleaf for HTML, Jackson for JSON) behind one `ContentNegotiatingViewResolver`, so the same view name can render as either format depending on the `Accept` header — bridging the `@Controller`/view world with API-style content negotiation:

```java
// WebConfig.java (production version)
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.http.MediaType;
import org.springframework.web.accept.ContentNegotiationManager;
import org.springframework.web.servlet.View;
import org.springframework.web.servlet.ViewResolver;
import org.springframework.web.servlet.view.ContentNegotiatingViewResolver;
import org.springframework.web.servlet.view.json.MappingJackson2JsonView;

import java.util.List;

@Configuration
public class WebConfig {

    @Bean
    public ViewResolver contentNegotiatingViewResolver(ContentNegotiationManager manager,
                                                          List<ViewResolver> delegates) {
        ContentNegotiatingViewResolver resolver = new ContentNegotiatingViewResolver();
        resolver.setContentNegotiationManager(manager);
        resolver.setViewResolvers(delegates);          // delegates to Thymeleaf's resolver for HTML
        resolver.setDefaultViews(List.of(new MappingJackson2JsonView()));   // adds JSON as an option
        resolver.setOrder(0);                            // check this FIRST, before individual resolvers
        return resolver;
    }
}
```

```java
// ProductController.java (production version)
import org.springframework.stereotype.Controller;
import org.springframework.ui.Model;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;

@Controller
public class ProductController {

    @GetMapping("/products/{id}")
    public String detail(@PathVariable long id, Model model) {
        model.addAttribute("id", id);
        model.addAttribute("productName", "Drill");
        return "product-detail";      // SAME view name — format depends on Accept header
    }
}
```

**How to run:**
```bash
./mvnw spring-boot:run

curl -H "Accept: text/html" http://localhost:8080/products/1
# <html>...<h1>Drill</h1>...</html>       (ThymeleafView selected)

curl -H "Accept: application/json" http://localhost:8080/products/1
# {"id":1,"productName":"Drill"}          (MappingJackson2JsonView selected — the WHOLE model serialized)
```

**What changed and why:**
- `ContentNegotiatingViewResolver` doesn't render anything itself — it resolves the view name via each **delegate** resolver (Thymeleaf's, in this case) to find candidate `View`s, then picks the specific candidate whose media type best matches the request's `Accept` header, falling back to `MappingJackson2JsonView` (serializing the whole model as JSON) when HTML isn't acceptable.
- This lets one controller method, with one view name and one `Model`, transparently serve both a browser (HTML) and an API client (JSON) — without `@RestController`, without a separate JSON-specific endpoint, and without any branching logic in the handler itself.
- Setting `resolver.setOrder(0)` ensures the negotiating wrapper is consulted before any individual resolver, since it needs to see the full picture (all delegate resolvers) to make its format decision.

## 6. Walkthrough

**Request: `GET /products/1` with `Accept: application/json` (Level 3 code).**

1. `DispatcherServlet` dispatches to `ProductController.detail(1, model)`. The handler populates `model` with `id=1` and `productName="Drill"`, and returns the view name `"product-detail"`.
2. `DispatcherServlet` asks the registered `ViewResolverComposite` to resolve `"product-detail"`. Because `contentNegotiatingViewResolver` has `order=0` (checked first), it's consulted first.
3. Inside `ContentNegotiatingViewResolver.resolveViewName`: it delegates to its configured `delegates` (Thymeleaf's `ViewResolver`) to resolve `"product-detail"` into a **candidate** `View` — finds `templates/product-detail.html` exists, so Thymeleaf offers a `ThymeleafView` candidate with media type `text/html`.
4. It also considers its configured `defaultViews` — `MappingJackson2JsonView`, offering media type `application/json`.
5. It now has two candidate views: `[ThymeleafView (text/html), MappingJackson2JsonView (application/json)]`. It inspects the request's `Accept: application/json` header and picks the candidate whose media type matches best: `MappingJackson2JsonView`.
6. `DispatcherServlet` calls `view.render(model, request, response)` on the selected `MappingJackson2JsonView`.
7. Inside `render`: Jackson serializes the **entire model map** (`{id: 1, productName: "Drill"}`, minus a few framework-internal attributes it filters out by default) directly to JSON and writes it to the response.
8. Response sent:
   ```
   HTTP/1.1 200 OK
   Content-Type: application/json

   {"id":1,"productName":"Drill"}
   ```

**Same request with `Accept: text/html` instead:** steps 1–4 identical. At step 5, the negotiator picks `ThymeleafView` instead (matching `text/html`). `render` processes the Thymeleaf template, substituting `${productName}`, producing the HTML page instead of JSON.

## 7. Gotchas & takeaways

> **A `ViewResolver` returning `null` (rather than throwing) is the correct way to say "not my view name, try the next resolver."** Throwing an exception instead of returning `null` breaks the fallback chain — the composite resolver treats an exception as a hard failure, not a "keep looking" signal.

> **`ContentNegotiatingViewResolver`'s JSON fallback serializes the ENTIRE model map**, including any attributes you didn't intend to expose (like a `BindingResult` or CSRF token Spring adds automatically). Filter what you put into the model carefully on any controller that might be content-negotiated to JSON — see the `Model`/`ModelMap` card's guidance on only adding what a view actually needs.

> **View resolution order matters, and a resolver with too broad a match (like accidentally handling every view name instead of returning `null` for names it doesn't recognize) can silently shadow other resolvers configured after it.** Always scope a custom resolver's matching logic narrowly, as `TextViewResolver`'s `"text:"` prefix check does.

- `ViewResolver`: view name → `View` instance. `View`: model → rendered response bytes.
- Multiple resolvers chain by `order`; a resolver returns `null` to defer to the next one, not an exception.
- `ContentNegotiatingViewResolver` lets one view name serve multiple formats (HTML, JSON, XML) depending on the request's `Accept` header, by delegating to multiple underlying resolvers/views.
- You rarely write custom `View`/`ViewResolver` implementations — but understanding the contract explains how Thymeleaf, JSP, and content negotiation all plug into the same `DispatcherServlet` rendering pipeline.

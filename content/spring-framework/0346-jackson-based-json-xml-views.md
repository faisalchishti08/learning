---
card: spring-framework
gi: 346
slug: jackson-based-json-xml-views
title: "Jackson-based JSON/XML views"
---

## 1. What it is

`MappingJackson2JsonView` and `MappingJackson2XmlView` are Spring MVC `View` implementations that serialize the model (or a single extracted model attribute) to JSON or XML using Jackson, plugging into the same `View`/`ViewResolver` pipeline used for HTML rendering. They're the concrete view classes behind `ContentNegotiatingViewResolver`'s JSON/XML fallback (seen in the "Content negotiation view resolution" card) and can also be used directly, standalone, without content negotiation.

```java
@Bean
public MappingJackson2JsonView jsonView() {
    MappingJackson2JsonView view = new MappingJackson2JsonView();
    view.setExtractValueFromSingleKeyModel(true);
    return view;
}
```

## 2. Why & when

Most of the time, `@RestController`/`@ResponseBody` is the right tool for JSON output — it's simpler and produces clean, unwrapped serialization. `MappingJackson2JsonView`/`MappingJackson2XmlView` matter specifically when:

- You need JSON/XML as one of several **negotiated formats** for a view-resolution-based controller (the scenario from the previous two cards) — a `@Controller` method that mostly renders HTML but occasionally needs to serve the same data as JSON through the *same* view-resolution pipeline.
- You want fine control over exactly which model attributes get serialized (via `setModelKey`/`setRenderedAttributes`), rather than dumping the entire model.
- You're customizing Jackson's `ObjectMapper` per-view (different serialization settings for one specific view than the application-wide default).

For a pure API surface, prefer `@RestController` — these view classes exist to bridge JSON/XML output into the classic MVC view-resolution model, not to replace `@RestController`'s more direct and idiomatic approach.

## 3. Core concept

```
MappingJackson2JsonView.render(model, request, response):

  By default: serializes the WHOLE model map
    {"invoice": {...}, "currentYear": 2026, "org.springframework...": ...}
    (Spring's own internal model attributes, like BindingResult, are
     filtered out automatically before serialization)

  setExtractValueFromSingleKeyModel(true):
    IF the model (after filtering) has exactly ONE entry,
    serialize just that entry's VALUE, not wrapped under its key
       model = {"invoice": {...}}  ->  {...}   (invoice object directly)

  setModelKey("invoice"):
    serialize ONLY the named attribute, ignoring everything else
       model = {"invoice": {...}, "debug": {...}}  ->  {...}  (invoice only)

  setRenderedAttributes(Set.of("invoice", "total")):
    serialize ONLY these specific attributes (as a filtered map)
```

These configuration options exist specifically to counter the "wrapped in model map" behavior noted as a gotcha in the content-negotiation-view-resolution card — you can shape the output to look like a clean, unwrapped object when that's what you want.

## 4. Diagram

<svg viewBox="0 0 720 210" xmlns="http://www.w3.org/2000/svg" font-family="monospace" font-size="12">
  <rect width="720" height="210" fill="#0d1117"/>
  <text x="360" y="22" text-anchor="middle" fill="#8b949e">Model shaping options before JSON serialization</text>

  <rect x="20" y="50" width="200" height="130" rx="5" fill="#1c2430" stroke="#8b949e"/>
  <text x="120" y="70" text-anchor="middle" fill="#8b949e" font-size="10">model</text>
  <text x="35" y="95" fill="#e6edf3" font-size="10">invoice: {id:1,total:149.99}</text>
  <text x="35" y="113" fill="#e6edf3" font-size="10">currentYear: 2026</text>

  <line x1="220" y1="90" x2="280" y2="90" stroke="#8b949e" marker-end="url(#a22)"/>
  <rect x="280" y="50" width="200" height="60" rx="5" fill="#1c2430" stroke="#6db33f"/>
  <text x="380" y="72" text-anchor="middle" fill="#6db33f" font-size="10">default: whole model</text>
  <text x="380" y="90" text-anchor="middle" fill="#8b949e" font-size="9">{"invoice":{...},"currentYear":2026}</text>

  <line x1="220" y1="150" x2="280" y2="150" stroke="#8b949e" marker-end="url(#a22)"/>
  <rect x="280" y="130" width="200" height="60" rx="5" fill="#1c2430" stroke="#79c0ff"/>
  <text x="380" y="152" text-anchor="middle" fill="#79c0ff" font-size="10">setModelKey("invoice")</text>
  <text x="380" y="170" text-anchor="middle" fill="#8b949e" font-size="9">{"id":1,"total":149.99}</text>

  <defs>
    <marker id="a22" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto">
      <path d="M0,0 L0,6 L8,3 z" fill="#8b949e"/>
    </marker>
  </defs>
</svg>

*`setModelKey` (or `setExtractValueFromSingleKeyModel`) produces a clean, unwrapped serialization instead of the whole model map.*

## 5. Runnable example

### Level 1 — Basic

Default whole-model serialization, standalone (no content negotiation):

```java
// InvoiceController.java
import org.springframework.stereotype.Controller;
import org.springframework.ui.Model;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;

@Controller
public class InvoiceController {

    record Invoice(long id, double total) {}

    @GetMapping("/invoices/{id}/json")
    public String json(@PathVariable long id, Model model) {
        model.addAttribute("invoice", new Invoice(id, 149.99));
        model.addAttribute("generatedAt", "2026-07-10");
        return "jsonView";      // resolves DIRECTLY to a bean named "jsonView"
    }
}
```

```java
// WebConfig.java
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.web.servlet.view.BeanNameViewResolver;
import org.springframework.web.servlet.view.json.MappingJackson2JsonView;

@Configuration
public class WebConfig {

    @Bean
    public BeanNameViewResolver beanNameViewResolver() { return new BeanNameViewResolver(); }

    @Bean(name = "jsonView")
    public MappingJackson2JsonView jsonView() { return new MappingJackson2JsonView(); }
}
```

**How to run:**
```bash
./mvnw spring-boot:run
curl http://localhost:8080/invoices/1/json
# {"invoice":{"id":1,"total":149.99},"generatedAt":"2026-07-10"}
```

By default, `MappingJackson2JsonView` serializes the whole model as-is — every attribute, nested under its own key. `BeanNameViewResolver` locates the `"jsonView"` bean directly (same mechanism as the document views card).

### Level 2 — Intermediate

Cleaning up the output with `setModelKey`, and adding an XML sibling view for the same data:

```java
// WebConfig.java (extended)
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.web.servlet.view.BeanNameViewResolver;
import org.springframework.web.servlet.view.json.MappingJackson2JsonView;
import org.springframework.web.servlet.view.xml.MappingJackson2XmlView;

@Configuration
public class WebConfig {

    @Bean
    public BeanNameViewResolver beanNameViewResolver() { return new BeanNameViewResolver(); }

    @Bean(name = "invoiceJson")
    public MappingJackson2JsonView invoiceJson() {
        MappingJackson2JsonView view = new MappingJackson2JsonView();
        view.setModelKey("invoice");     // serialize ONLY this attribute, unwrapped
        return view;
    }

    @Bean(name = "invoiceXml")
    public MappingJackson2XmlView invoiceXml() {
        MappingJackson2XmlView view = new MappingJackson2XmlView();
        view.setModelKey("invoice");
        return view;
    }
}
```

```java
// InvoiceController.java (extended)
import org.springframework.stereotype.Controller;
import org.springframework.ui.Model;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;

@Controller
public class InvoiceController {

    record Invoice(long id, double total) {}

    @GetMapping("/invoices/{id}/json")
    public String json(@PathVariable long id, Model model) {
        model.addAttribute("invoice", new Invoice(id, 149.99));
        model.addAttribute("generatedAt", "2026-07-10");    // present in model but NOT serialized
        return "invoiceJson";
    }

    @GetMapping("/invoices/{id}/xml")
    public String xml(@PathVariable long id, Model model) {
        model.addAttribute("invoice", new Invoice(id, 149.99));
        return "invoiceXml";
    }
}
```

**How to run:**
```bash
./mvnw spring-boot:run

curl http://localhost:8080/invoices/1/json
# {"id":1,"total":149.99}          <- clean, unwrapped, "generatedAt" excluded

curl http://localhost:8080/invoices/1/xml
# <Invoice><id>1</id><total>149.99</total></Invoice>
```

**What changed:** `setModelKey("invoice")` tells the view to serialize only that one attribute's *value*, not the whole model — `generatedAt` remains in the model (perhaps used by another view for the same controller method in a content-negotiated setup) but is excluded from this view's output entirely. The XML sibling view uses the identical `setModelKey` mechanism, just with Jackson's XML data-format module instead of the default JSON one.

### Level 3 — Advanced

Production concern: a per-view customized `ObjectMapper` (different serialization settings than the application-wide default — e.g. pretty-printing for a debug/admin JSON view, or a specific date format for an external partner integration), and combining this with `ContentNegotiatingViewResolver` for full format negotiation with a clean, unwrapped contract:

```java
// WebConfig.java (production version)
import com.fasterxml.jackson.databind.ObjectMapper;
import com.fasterxml.jackson.databind.SerializationFeature;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.web.accept.ContentNegotiationManager;
import org.springframework.web.servlet.View;
import org.springframework.web.servlet.ViewResolver;
import org.springframework.web.servlet.view.ContentNegotiatingViewResolver;
import org.springframework.web.servlet.view.json.MappingJackson2JsonView;

import java.util.List;

@Configuration
public class WebConfig {

    @Bean
    public MappingJackson2JsonView invoiceJsonView() {
        // A dedicated ObjectMapper for THIS view, independent of the app-wide Jackson config —
        // e.g. a partner integration that specifically requires pretty-printed, ISO-dated JSON.
        ObjectMapper mapper = new ObjectMapper()
            .enable(SerializationFeature.INDENT_OUTPUT)
            .disable(SerializationFeature.WRITE_DATES_AS_TIMESTAMPS);

        MappingJackson2JsonView view = new MappingJackson2JsonView(mapper);
        view.setModelKey("invoice");
        return view;
    }

    @Bean
    public ViewResolver contentNegotiatingViewResolver(ContentNegotiationManager manager,
                                                          MappingJackson2JsonView invoiceJsonView) {
        ContentNegotiatingViewResolver resolver = new ContentNegotiatingViewResolver();
        resolver.setContentNegotiationManager(manager);
        resolver.setDefaultViews(List.of((View) invoiceJsonView));
        return resolver;
    }
}
```

```java
// InvoiceController.java (production version)
import org.springframework.stereotype.Controller;
import org.springframework.ui.Model;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;

import java.time.LocalDate;

@Controller
public class InvoiceController {

    record Invoice(long id, double total, LocalDate issuedOn) {}

    @GetMapping("/invoices/{id}")
    public String view(@PathVariable long id, Model model) {
        model.addAttribute("invoice", new Invoice(id, 149.99, LocalDate.of(2026, 7, 10)));
        return "invoice";     // HTML normally, clean pretty-printed JSON when negotiated
    }
}
```

**How to run:**
```bash
./mvnw spring-boot:run

curl -H "Accept: application/json" http://localhost:8080/invoices/1
# {
#   "id" : 1,
#   "total" : 149.99,
#   "issuedOn" : "2026-07-10"
# }
```

**What changed and why:**
- Passing a custom `ObjectMapper` into `MappingJackson2JsonView`'s constructor isolates this view's serialization rules (pretty-printing, ISO date formatting) from the application's default `ObjectMapper` bean, which might have entirely different settings for its `@RestController` endpoints — useful when a specific consumer (partner integration, debug tooling) has different formatting requirements than the rest of the API.
- `setModelKey("invoice")` combined with `ContentNegotiatingViewResolver` produces a clean, unwrapped, negotiated JSON response from a classic `@Controller`/view-resolution setup — closing the gap noted as a gotcha in the previous card, where the default whole-model wrapping was often undesirable.
- This pattern is genuinely useful for gradually adding a lightweight API surface to an existing server-rendered application without introducing a parallel `@RestController` layer, while still keeping full control over the exact JSON shape produced.

## 6. Walkthrough

**Request: `GET /invoices/1` with `Accept: application/json` (Level 3 code).**

1. `DispatcherServlet` dispatches to `InvoiceController.view(1, model)`. The handler populates `model` with a single `invoice` attribute (an `Invoice` record with a `LocalDate` field) and returns `"invoice"`.
2. `ContentNegotiatingViewResolver` determines the negotiated media type (`application/json`), gathers candidates (Thymeleaf's HTML view for `"invoice"`, plus the configured `invoiceJsonView` default), and selects `invoiceJsonView` as the best match.
3. `invoiceJsonView.render(model, request, response)` executes. Because `setModelKey("invoice")` was configured, it extracts *only* `model.get("invoice")` — the `Invoice` record itself — ignoring any other model attributes that might be present.
4. Serialization uses the view's **dedicated** `ObjectMapper` (not the application's default) — `SerializationFeature.INDENT_OUTPUT` is enabled, so the output is pretty-printed with newlines and indentation; `WRITE_DATES_AS_TIMESTAMPS` is disabled, so `issuedOn` (a `LocalDate`) serializes as the ISO string `"2026-07-10"` rather than a numeric epoch value.
5. The resulting JSON bytes are written directly to the response body:
   ```
   HTTP/1.1 200 OK
   Content-Type: application/json

   {
     "id" : 1,
     "total" : 149.99,
     "issuedOn" : "2026-07-10"
   }
   ```

Contrast with what would happen without `setModelKey`: the output would instead be `{"invoice": {"id":1,"total":149.99,"issuedOn":"2026-07-10"}}` — the extra nesting level under `"invoice"` that `setModelKey` deliberately strips away.

## 7. Gotchas & takeaways

> **Forgetting `setModelKey` (or `setExtractValueFromSingleKeyModel`) means every model attribute gets serialized, nested under its attribute name** — including attributes you never intended to expose, like a `BindingResult` (usually filtered automatically by Spring, but custom attributes are not). Always explicitly scope what a JSON/XML view serializes for anything beyond a quick internal debug view.

> **A per-view `ObjectMapper` is completely independent of the application's globally configured `ObjectMapper` bean** (the one `@RestController` endpoints use via `HttpMessageConverter`). Changing global Jackson settings (e.g. a `Jackson2ObjectMapperBuilderCustomizer`) does **not** automatically affect a `MappingJackson2JsonView` constructed with its own explicit `ObjectMapper` — keep this in mind when debugging "why does this one endpoint format dates differently."

> **`MappingJackson2XmlView` requires the `jackson-dataformat-xml` dependency on the classpath** (the same one used for `@RestController` XML content negotiation) — without it, resolving a view backed by this class fails with a `NoClassDefFoundError` at render time, not at startup, which can be a confusing first encounter with this requirement.

- `MappingJackson2JsonView`/`MappingJackson2XmlView` bridge JSON/XML output into classic view resolution — useful for content-negotiated `@Controller` endpoints, not a replacement for `@RestController`.
- `setModelKey`/`setExtractValueFromSingleKeyModel`/`setRenderedAttributes` control exactly what gets serialized, avoiding an unwanted whole-model dump.
- A view can carry its own dedicated `ObjectMapper`, independent of the application's global Jackson configuration.
- Combine these views with `ContentNegotiatingViewResolver` (previous card) to add a clean, negotiated JSON/XML option to an existing server-rendered resource.

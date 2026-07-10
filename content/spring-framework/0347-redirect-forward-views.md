---
card: spring-framework
gi: 347
slug: redirect-forward-views
title: "Redirect & forward views"
---

## 1. What it is

`RedirectView` and the `"forward:"` view-name prefix are two ways a Spring MVC handler can send the browser somewhere else instead of rendering a template directly. A **redirect** tells the client (via an HTTP `3xx` response and `Location` header) to make a brand new request to a different URL — the browser's address bar changes. A **forward** is entirely server-side: the current request is internally dispatched to a different handler/view within the same server round-trip — the client never knows it happened, and the URL bar doesn't change.

```java
@PostMapping("/products")
public String create(@ModelAttribute Product product) {
    productService.save(product);
    return "redirect:/products/" + product.getId();   // client makes a NEW GET request
}
```

## 2. Why & when

**Redirect** after a state-changing operation (`POST`, `PUT`, `DELETE`) is the standard **Post/Redirect/Get (PRG)** pattern: it prevents a browser refresh from resubmitting the same form data (which would otherwise duplicate the create/update operation), and it gives the resulting URL a bookmarkable, shareable address that reflects the created/updated resource.

**Forward** is appropriate when:
- You want to reuse another handler's rendering logic without a round-trip — e.g. an error page controller forwarding to a shared error-rendering view.
- The target view should render using data already computed in the current request, without losing that data across a redirect (redirects lose request-scoped data unless explicitly passed via flash attributes or query parameters).
- The URL shown to the user should remain the original one, even though different logic actually produced the response (common for form validation failures — stay on the same submit URL, but forward internally to re-render the form with errors).

## 3. Core concept

```
REDIRECT ("redirect:/path" or RedirectView):

  Client -> POST /products (creates product id=5)
  Server -> 302 Found, Location: /products/5           <- response #1, NO body rendered yet
  Client -> GET /products/5  (a BRAND NEW request)      <- response #2, this one renders the view
  Server -> 200 OK, <html>...</html>

  Two full request/response round-trips. Model data from the
  FIRST request does NOT automatically carry to the second
  (unless using RedirectAttributes / flash attributes).

FORWARD ("forward:/path"):

  Client -> POST /products/1/validate (validation fails)
  Server (internally) -> forwards to /products/1/edit-form
                          SAME request, SAME response, SAME model
  Server -> 200 OK, <html>...(edit form, pre-filled, with errors)...</html>

  ONE request/response round-trip. Model data automatically
  available to the forwarded-to handler/view. URL bar shows
  the ORIGINAL /products/1/validate, not /products/1/edit-form.
```

## 4. Diagram

<svg viewBox="0 0 740 240" xmlns="http://www.w3.org/2000/svg" font-family="monospace" font-size="12">
  <rect width="740" height="240" fill="#0d1117"/>
  <text x="370" y="22" text-anchor="middle" fill="#8b949e">Redirect (two round-trips) vs Forward (one round-trip)</text>

  <rect x="20" y="50" width="330" height="150" rx="5" fill="#1c2430" stroke="#79c0ff"/>
  <text x="185" y="70" text-anchor="middle" fill="#79c0ff">Redirect</text>
  <text x="35" y="95" fill="#8b949e" font-size="10">Client -&gt; POST /products</text>
  <text x="35" y="113" fill="#8b949e" font-size="10">Server -&gt; 302 Location: /products/5</text>
  <text x="35" y="135" fill="#6db33f" font-size="10">Client -&gt; GET /products/5 (NEW request)</text>
  <text x="35" y="153" fill="#8b949e" font-size="10">Server -&gt; 200 OK, rendered HTML</text>
  <text x="35" y="178" fill="#8b949e" font-size="9">URL bar changes; model NOT carried over</text>

  <rect x="390" y="50" width="330" height="150" rx="5" fill="#1c2430" stroke="#6db33f"/>
  <text x="555" y="70" text-anchor="middle" fill="#6db33f">Forward</text>
  <text x="405" y="95" fill="#8b949e" font-size="10">Client -&gt; POST /products/1/validate</text>
  <text x="405" y="113" fill="#8b949e" font-size="10">Server -&gt; internally dispatches to</text>
  <text x="405" y="129" fill="#8b949e" font-size="10">          /products/1/edit-form</text>
  <text x="405" y="151" fill="#8b949e" font-size="10">Server -&gt; 200 OK, rendered HTML</text>
  <text x="405" y="178" fill="#8b949e" font-size="9">URL bar unchanged; model automatically carried</text>

  <defs>
    <marker id="a23" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto">
      <path d="M0,0 L0,6 L8,3 z" fill="#8b949e"/>
    </marker>
  </defs>
</svg>

*A redirect involves two separate HTTP exchanges visible to the client; a forward is a single, server-internal dispatch invisible to the client.*

## 5. Runnable example

### Level 1 — Basic

The Post/Redirect/Get pattern after creating a resource:

```java
// ProductController.java
import org.springframework.stereotype.Controller;
import org.springframework.ui.Model;
import org.springframework.web.bind.annotation.*;

import java.util.Map;
import java.util.concurrent.ConcurrentHashMap;
import java.util.concurrent.atomic.AtomicLong;

@Controller
public class ProductController {

    record Product(long id, String name) {}
    private final Map<Long, Product> store = new ConcurrentHashMap<>();
    private final AtomicLong seq = new AtomicLong(1);

    @PostMapping("/products")
    public String create(@RequestParam String name) {
        long id = seq.getAndIncrement();
        store.put(id, new Product(id, name));
        return "redirect:/products/" + id;   // 302 -> client GETs the new resource's URL
    }

    @GetMapping("/products/{id}")
    public String detail(@PathVariable long id, Model model) {
        model.addAttribute("product", store.get(id));
        return "product-detail";
    }
}
```

**How to run:**
```bash
./mvnw spring-boot:run

curl -i -X POST http://localhost:8080/products -d "name=Drill"
# HTTP/1.1 302 Found
# Location: /products/1
# (empty body — the browser would now automatically GET /products/1)

curl -L -X POST http://localhost:8080/products -d "name=Hammer"
# curl's -L follows the redirect automatically:
# <html>...Hammer...</html>   (rendered by the SECOND request, GET /products/2)
```

Without the redirect, a user refreshing the page after the `POST` would resubmit the same form data, potentially creating a duplicate product — the redirect ensures the browser's "current page" after the operation is a `GET`, which is safe to refresh.

### Level 2 — Intermediate

Carrying data across the redirect using flash attributes (since normal model attributes don't survive a redirect's new request), plus a forward for re-displaying a form with validation errors on the *original* URL:

```java
// ProductController.java (extended)
import org.springframework.stereotype.Controller;
import org.springframework.ui.Model;
import org.springframework.web.bind.annotation.*;
import org.springframework.web.servlet.mvc.support.RedirectAttributes;

@Controller
public class ProductController {

    record Product(long id, String name) {}
    private final java.util.Map<Long, Product> store = new java.util.concurrent.ConcurrentHashMap<>();
    private final java.util.concurrent.atomic.AtomicLong seq = new java.util.concurrent.atomic.AtomicLong(1);

    @PostMapping("/products")
    public String create(@RequestParam String name, RedirectAttributes redirectAttributes) {
        if (name.isBlank()) {
            // Validation failed — FORWARD back to the form on the SAME URL, preserving the
            // attempted (invalid) input so the user doesn't have to retype it.
            return "forward:/products/new-form";
        }
        long id = seq.getAndIncrement();
        store.put(id, new Product(id, name));
        redirectAttributes.addFlashAttribute("successMessage", "Product '" + name + "' created!");
        return "redirect:/products/" + id;
    }

    @GetMapping("/products/new-form")
    public String newForm(Model model) {
        if (!model.containsAttribute("name")) model.addAttribute("name", "");
        model.addAttribute("error", "Name is required");
        return "product-form";
    }

    @GetMapping("/products/{id}")
    public String detail(@PathVariable long id, Model model) {
        model.addAttribute("product", store.get(id));
        // "successMessage" flash attribute, if present, is AUTOMATICALLY added to this model
        // by Spring's FlashMap mechanism — no explicit code needed here to retrieve it.
        return "product-detail";
    }
}
```

**How to run:**
```bash
./mvnw spring-boot:run

curl -i -X POST http://localhost:8080/products -d "name="
# HTTP/1.1 200 OK          <- NOT a redirect; forward keeps status 200 and stays on this URL's response
# <html>...Name is required...</html>

curl -i -c cookies.txt -X POST http://localhost:8080/products -d "name=Drill"
# HTTP/1.1 302 Found
# Location: /products/1

curl -b cookies.txt -L -X POST http://localhost:8080/products -d "name=Hammer"
# <html>...Product 'Hammer' created!...Hammer...</html>
```

**What changed:** `RedirectAttributes.addFlashAttribute` stores data in a short-lived server-side `FlashMap` (backed by the session) that survives exactly one redirect — the *next* request (the browser's follow-up `GET`) automatically has it merged into its `Model`, letting a "success" message survive the otherwise-stateless redirect. The `forward:` case, by contrast, needs no flash mechanism at all — because it's the same request, the model data is simply still there.

### Level 3 — Advanced

Production pattern: `RedirectView` with explicit control over relative-vs-absolute URLs and status code (`303 See Other` instead of the default `302`), avoiding common redirect pitfalls (open redirect vulnerability from unvalidated user input, and losing query parameters unintentionally):

```java
// ProductController.java (production version)
import org.springframework.http.HttpStatus;
import org.springframework.stereotype.Controller;
import org.springframework.web.bind.annotation.*;
import org.springframework.web.servlet.mvc.support.RedirectAttributes;
import org.springframework.web.servlet.view.RedirectView;

import java.util.Set;

@Controller
public class ProductController {

    // A closed, known set of internal redirect targets — NEVER redirect to a raw,
    // client-supplied URL without validation (that's an open-redirect vulnerability,
    // usable for phishing: "trusted-site.com/redirect?to=evil.com").
    private static final Set<String> ALLOWED_RETURN_PATHS = Set.of("/products", "/dashboard");

    @PostMapping("/products")
    public RedirectView create(@RequestParam String name,
                                @RequestParam(required = false, defaultValue = "/products") String returnTo,
                                RedirectAttributes redirectAttributes) {
        long id = 42; // saved elsewhere
        redirectAttributes.addFlashAttribute("successMessage", "Created " + name);

        String safeTarget = ALLOWED_RETURN_PATHS.contains(returnTo) ? returnTo : "/products";

        RedirectView redirectView = new RedirectView("/products/" + id);
        redirectView.setStatusCode(HttpStatus.SEE_OTHER);   // 303: explicit "the result is at a new URI, GET it"
        redirectView.setExposeModelAttributes(false);        // don't leak model data as query params
        return redirectView;
    }
}
```

**How to run:**
```bash
./mvnw spring-boot:run

curl -i -X POST http://localhost:8080/products -d "name=Drill&returnTo=https://evil.example.com"
# HTTP/1.1 303 See Other
# Location: /products/42
# (returnTo is validated against ALLOWED_RETURN_PATHS and ignored here since it's not in the allow-list —
#  the attacker-supplied URL never reaches the Location header)
```

**What changed and why:**
- Returning a `RedirectView` object instead of a `"redirect:..."` string gives explicit, type-safe control over the HTTP status code (`303 See Other` is arguably more semantically correct than the default `302 Found` for a post-creation redirect, since it explicitly signals "fetch the result via GET at this new URI") and other redirect behaviors.
- `ALLOWED_RETURN_PATHS` validation against a fixed allow-list is the critical defense against **open redirect** vulnerabilities — if `returnTo` were used unchecked as a redirect target, an attacker could craft a link to your trusted domain that silently redirects victims to a phishing site, exploiting user trust in your domain name.
- `setExposeModelAttributes(false)` prevents `RedirectView`'s legacy behavior (from older Spring versions) of automatically appending primitive model attributes as query parameters on the redirect URL — usually not what you want, and a possible source of accidentally leaking data into browser history/logs via the URL.

## 6. Walkthrough

**Request: `POST /products` with `name=Drill&returnTo=https://evil.example.com` (Level 3 code).**

1. `DispatcherServlet` dispatches to `create("Drill", "https://evil.example.com", redirectAttributes)`.
2. `redirectAttributes.addFlashAttribute("successMessage", "Created Drill")` stores the message in a server-side `FlashMap`, keyed to be retrieved by the *next* request from the same client (matched via session or a request parameter Spring adds automatically).
3. `ALLOWED_RETURN_PATHS.contains("https://evil.example.com")` evaluates to `false` — the attacker-supplied `returnTo` is rejected; `safeTarget` falls back to `"/products"` (though in this particular handler, `safeTarget` isn't even used for the primary redirect — it demonstrates the validation pattern for scenarios where the return path *does* drive the redirect target).
4. A `RedirectView` is constructed pointing to `/products/42` (the newly created resource's own URL — a server-controlled, trusted value, never derived from unchecked client input), with `setStatusCode(SEE_OTHER)`.
5. `DispatcherServlet` calls `redirectView.render(model, request, response)`. This builds and sends the redirect response directly — no template rendering occurs for this response at all.
6. Response sent:
   ```
   HTTP/1.1 303 See Other
   Location: /products/42
   ```
7. The client (a real browser) automatically issues a **new** `GET /products/42` request. Because this is a separate request, Spring's `FlashMapManager` checks for a matching pending `FlashMap` (using a session-associated lookup key established during step 2) and, finding one, merges `successMessage` into this new request's `Model` automatically — before the `detail` handler method even runs.
8. `detail(42, model)` executes, adds `product` to the model. The already-merged `successMessage` flash attribute is also present. The view renders both.
9. Final response for this second request:
   ```
   HTTP/1.1 200 OK
   Content-Type: text/html;charset=UTF-8

   <html>...Created Drill...<h1>Drill</h1>...</html>
   ```

## 7. Gotchas & takeaways

> **Never redirect to a URL taken directly from unvalidated client input** (a query parameter, form field, or header) — this is the open-redirect vulnerability class, frequently used in phishing attacks that abuse a trusted domain's redirect endpoint to send victims to an attacker-controlled site. Always validate against an allow-list of known-safe internal paths, as in the Level 3 example.

> **Model attributes do not automatically survive a redirect** — only flash attributes (`RedirectAttributes.addFlashAttribute`) do, and only for exactly one subsequent request. A common bug is adding data via `model.addAttribute(...)` before returning a `"redirect:..."` view name and being surprised it's gone on the next page — that data was for the (never-rendered) redirect response itself, not the page the browser actually lands on.

> **A `"forward:"` internally dispatches within the same request but does NOT re-run any `@RequestMapping`-level validation, security filters, or interceptors that only apply to the specific mapped path being forwarded from** — depending on filter/interceptor configuration, a forwarded-to path might skip checks you assumed would always run. Verify filter chains handle forwarded dispatches (`DispatcherType.FORWARD`) correctly if security-relevant.

- Redirect (`302`/`303` + `Location` header) is a full round-trip; forward is a single, server-internal dispatch invisible to the client.
- Use the Post/Redirect/Get pattern after any state-changing operation to prevent duplicate submissions on refresh.
- Flash attributes (`RedirectAttributes.addFlashAttribute`) are the mechanism for carrying transient data across exactly one redirect.
- Never build a redirect target from unvalidated client input — always check against a known-safe allow-list to prevent open-redirect vulnerabilities.

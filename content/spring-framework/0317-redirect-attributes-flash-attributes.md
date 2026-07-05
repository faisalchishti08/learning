---
card: spring-framework
gi: 317
slug: redirect-attributes-flash-attributes
title: "Redirect attributes & flash attributes"
---

## 1. What it is

When a controller returns `"redirect:/path"`, the browser issues a new `GET` request — a separate HTTP exchange. Data from the original request is lost. Spring MVC provides two mechanisms to pass data across this gap:

**Redirect attributes** (added via `RedirectAttributes.addAttribute()`) — appended as query parameters to the redirect URL:
```
redirect:/products/list → /products/list?created=true&name=Hammer
```

**Flash attributes** (added via `RedirectAttributes.addFlashAttribute()`) — stored in the HTTP session for exactly one subsequent request, then automatically removed:
```
redirect:/products/list → session stores {msg: "Saved!"} for one GET /products/list
```

Flash attributes do not appear in the URL (no leakage) and survive one redirect — they're consumed and deleted after the redirect target reads them.

---

## 2. Why & when

Use **`addAttribute()`** for:
- Non-sensitive, bookmarkable data (e.g. `?page=1&sort=name`)
- Data the user can see and re-use in the URL

Use **`addFlashAttribute()`** for:
- Success/error messages after form submission (`"Product saved!"`)
- Data that must not appear in the URL (user IDs, status codes)
- One-time notifications that should disappear on refresh

Both follow the **POST/Redirect/GET (PRG)** pattern — POST writes data, redirect to GET prevents form re-submission on browser refresh.

---

## 3. Core concept

```
POST /products  → controller returns "redirect:/products/list"

addAttribute("created", true)
  → Browser follows: GET /products/list?created=true
  → @RequestParam("created") Boolean created = true

addFlashAttribute("message", "Product saved!")
  → Stored in session under FlashMap key
  → Browser follows: GET /products/list  (no query param)
  → FlashMapManager reads session, injects into model: {message: "Product saved!"}
  → After request: flash entry deleted from session

Both can be combined — redirect URL has query params; model has flash attrs.
```

---

## 4. Diagram

<svg viewBox="0 0 740 280" xmlns="http://www.w3.org/2000/svg" font-family="monospace" font-size="12">
  <rect width="740" height="280" fill="#0d1117"/>

  <!-- POST handler -->
  <rect x="10" y="80" width="170" height="70" rx="5" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="95" y="100" text-anchor="middle" fill="#79c0ff">POST /products</text>
  <text x="95" y="116" text-anchor="middle" fill="#8b949e" font-size="10">addAttribute("id",1)</text>
  <text x="95" y="130" text-anchor="middle" fill="#8b949e" font-size="10">addFlashAttribute("msg","Saved!")</text>
  <text x="95" y="144" text-anchor="middle" fill="#8b949e" font-size="10">return "redirect:/products"</text>

  <!-- 302 arrow -->
  <line x1="180" y1="115" x2="230" y2="115" stroke="#8b949e" marker-end="url(#arf)"/>

  <!-- 302 response -->
  <rect x="230" y="90" width="180" height="50" rx="5" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="320" y="110" text-anchor="middle" fill="#6db33f">302 Redirect</text>
  <text x="320" y="126" text-anchor="middle" fill="#8b949e" font-size="10">Location: /products?id=1</text>
  <text x="320" y="139" text-anchor="middle" fill="#8b949e" font-size="10">Session: flash{msg:"Saved!"}</text>

  <!-- GET request -->
  <line x1="410" y1="115" x2="450" y2="115" stroke="#8b949e" marker-end="url(#arf)"/>

  <!-- GET handler -->
  <rect x="450" y="80" width="200" height="80" rx="5" fill="#1c2430" stroke="#79c0ff" stroke-width="1"/>
  <text x="550" y="100" text-anchor="middle" fill="#79c0ff">GET /products?id=1</text>
  <text x="550" y="117" text-anchor="middle" fill="#8b949e" font-size="10">@RequestParam id = 1  (from URL)</text>
  <text x="550" y="132" text-anchor="middle" fill="#8b949e" font-size="10">@ModelAttribute("msg") → "Saved!"</text>
  <text x="550" y="147" text-anchor="middle" fill="#8b949e" font-size="10">(from flash, consumed + deleted)</text>

  <!-- session flash lifecycle -->
  <rect x="230" y="190" width="300" height="60" rx="5" fill="#1c2430" stroke="#8b949e" stroke-dasharray="3,2"/>
  <text x="380" y="210" text-anchor="middle" fill="#8b949e">Flash attribute lifecycle</text>
  <text x="380" y="228" text-anchor="middle" fill="#8b949e" font-size="10">stored in session after POST</text>
  <text x="380" y="244" text-anchor="middle" fill="#8b949e" font-size="10">injected into model on GET → deleted</text>

  <text x="370" y="275" text-anchor="middle" fill="#8b949e" font-size="11">Query params survive bookmarks and refreshes; flash attrs vanish after one redirect</text>

  <defs>
    <marker id="arf" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto">
      <path d="M0,0 L0,6 L8,3 z" fill="#8b949e"/>
    </marker>
  </defs>
</svg>

*`addAttribute` → URL query param; `addFlashAttribute` → session → model → deleted after one use.*

---

## 5. Runnable example

### Level 1 — Basic

A product creation form that uses PRG with a flash success message:

```java
// ProductController.java
import org.springframework.stereotype.Controller;
import org.springframework.ui.Model;
import org.springframework.web.bind.annotation.*;
import org.springframework.web.servlet.mvc.support.RedirectAttributes;

@Controller
@RequestMapping("/products")
public class ProductController {

    @GetMapping
    public String list(
            @ModelAttribute("successMsg") String successMsg,  // consumed from flash
            Model model) {
        model.addAttribute("msg", successMsg);
        return "products/list";
    }

    @PostMapping
    public String create(
            @RequestParam String name,
            RedirectAttributes attrs) {

        long newId = 42L; // simulate save

        // Appears in redirect URL
        attrs.addAttribute("created", newId);
        // One-time session message — NOT in URL
        attrs.addFlashAttribute("successMsg", "Product '" + name + "' created (id=" + newId + ")");

        return "redirect:/products";
    }
}
```

**How to run:**
```bash
./mvnw spring-boot:run

# Submit form
curl -c cookies.txt -b cookies.txt \
     -X POST -d "name=Hammer" http://localhost:8080/products
# 302 Location: /products?created=42

# Follow redirect (browser does this automatically)
curl -b cookies.txt "http://localhost:8080/products?created=42"
# renders list; msg="Product 'Hammer' created (id=42)"
# (flash consumed; next refresh: msg is empty)
```

`addAttribute("created", newId)` appends `?created=42` to the redirect URL — visible and bookmarkable. `addFlashAttribute("successMsg", "...")` stores in the session under `FlashMap`; Spring's `FlashMapManager` injects it into the model for the very next GET, then deletes it. `@ModelAttribute("successMsg")` in the GET handler binds from the model — the value is `""` (not null) on refreshes.

---

### Level 2 — Intermediate

Same product scenario — now adding **error flash attributes** for failed saves, and redirect attributes to restore the form's filter state:

```java
// ProductController.java (extended)
import org.springframework.stereotype.Controller;
import org.springframework.ui.Model;
import org.springframework.web.bind.annotation.*;
import org.springframework.web.servlet.mvc.support.RedirectAttributes;

@Controller
@RequestMapping("/products")
public class ProductController {

    @GetMapping
    public String list(
            @RequestParam(required = false) String category,      // from redirect URL
            @RequestParam(required = false) Integer page,
            @ModelAttribute("successMsg") String successMsg,
            @ModelAttribute("errorMsg")   String errorMsg,
            Model model) {

        model.addAttribute("category", category);
        model.addAttribute("page", page);
        model.addAttribute("success", successMsg);
        model.addAttribute("error", errorMsg);
        return "products/list";
    }

    @PostMapping
    public String create(
            @RequestParam String name,
            @RequestParam String category,
            @RequestParam int page,
            RedirectAttributes attrs) {

        boolean saved = !name.isBlank(); // simulate save result

        // Redirect params — restore list filter state
        attrs.addAttribute("category", category);
        attrs.addAttribute("page", page);

        if (saved) {
            attrs.addFlashAttribute("successMsg", "'" + name + "' saved.");
        } else {
            attrs.addFlashAttribute("errorMsg", "Save failed: name is blank.");
        }

        return "redirect:/products";
    }
}
```

**How to run:**
```bash
./mvnw spring-boot:run

# Successful save — restores category/page filter, shows success flash
curl -c cookies.txt -b cookies.txt \
     -X POST -d "name=Drill&category=tools&page=2" http://localhost:8080/products
# 302 Location: /products?category=tools&page=2

curl -b cookies.txt "http://localhost:8080/products?category=tools&page=2"
# category=tools, page=2; success="'Drill' saved."

# Failed save (blank name) — same redirect with error flash
curl -c cookies.txt -b cookies.txt \
     -X POST -d "name=&category=decor&page=1" http://localhost:8080/products
# 302 Location: /products?category=decor&page=1
curl -b cookies.txt "http://localhost:8080/products?category=decor&page=1"
# error="Save failed: name is blank."
```

**What changed:** redirect attributes preserve the list's filter state (`category`, `page`) so the user lands back on the same filtered view they were on. Flash attributes carry the outcome notification — success green or error red — without cluttering the URL.

---

### Level 3 — Advanced

Production scenario: flash attributes for a multi-step wizard where step completion triggers a redirect with a structured flash object, and a guard that redirects back with error if validation fails mid-wizard:

```java
// CheckoutController.java
import org.springframework.http.*;
import org.springframework.stereotype.Controller;
import org.springframework.web.bind.annotation.*;
import org.springframework.web.servlet.mvc.support.RedirectAttributes;
import java.util.*;

@Controller
@RequestMapping("/checkout")
public class CheckoutController {

    @GetMapping("/confirm")
    public String confirm(
            @ModelAttribute("orderSummary") Map<String, Object> summary,
            @ModelAttribute("validationErrors") List<String> errors,
            org.springframework.ui.Model model) {
        if (!errors.isEmpty()) {
            model.addAttribute("errors", errors);
        }
        model.addAttribute("summary", summary);
        return "checkout/confirm";
    }

    @PostMapping("/step2")
    public String processStep2(
            @RequestParam String cardNumber,
            @RequestParam String shippingAddress,
            RedirectAttributes attrs) {

        List<String> errors = new ArrayList<>();
        if (cardNumber == null || cardNumber.length() < 16) errors.add("Card number invalid");
        if (shippingAddress == null || shippingAddress.isBlank()) errors.add("Address required");

        if (!errors.isEmpty()) {
            // Flash error list — redirect back to confirm with errors
            attrs.addFlashAttribute("validationErrors", errors);
            attrs.addFlashAttribute("orderSummary",
                    Map.of("card", cardNumber, "address", shippingAddress));
            return "redirect:/checkout/confirm";
        }

        // Success — flash the order summary for the success page
        long orderId = System.currentTimeMillis() % 100000;
        attrs.addFlashAttribute("orderSummary", Map.of(
                "orderId",  orderId,
                "card",     "**** **** **** " + cardNumber.substring(Math.max(0, cardNumber.length()-4)),
                "address",  shippingAddress,
                "status",   "CONFIRMED"));
        attrs.addAttribute("orderId", orderId); // also in URL for bookmarking

        return "redirect:/checkout/success";
    }

    @GetMapping("/success")
    public String success(
            @RequestParam long orderId,
            @ModelAttribute("orderSummary") Map<String, Object> summary,
            org.springframework.ui.Model model) {
        model.addAttribute("order", summary);
        return "checkout/success";
    }
}
```

**How to run:**
```bash
./mvnw spring-boot:run

# Invalid input — flashed errors, redirect back to confirm
curl -c cookies.txt -b cookies.txt \
     -X POST -d "cardNumber=123&shippingAddress=" http://localhost:8080/checkout/step2
# 302 → /checkout/confirm  (flash: validationErrors, orderSummary)
curl -b cookies.txt http://localhost:8080/checkout/confirm
# errors=["Card number invalid","Address required"]
# (pre-filled form from orderSummary flash)

# Valid — redirect to success with orderId in URL + rich summary in flash
curl -c cookies.txt -b cookies.txt \
     -X POST -d "cardNumber=4111111111111111&shippingAddress=123+Main+St" \
     http://localhost:8080/checkout/step2
# 302 → /checkout/success?orderId=54321
curl -b cookies.txt "http://localhost:8080/checkout/success?orderId=54321"
# order summary with masked card, address, status=CONFIRMED
```

**What changed and why:**
- Flash object `orderSummary` (a `Map`) carries rich data across the redirect — no URL encoding of complex structures.
- `validationErrors` as a flash list lets the confirm page show inline errors without re-rendering from the POST handler.
- `attrs.addAttribute("orderId", orderId)` places the order ID in the URL so the success page is bookmarkable — but the full order summary is in the flash (not the URL) to avoid leaking card/address details.
- If the user refreshes `/checkout/success?orderId=54321`, the flash is gone — the page renders with an empty `orderSummary`, which the template can handle gracefully (`${summary.orderId ?: orderId}` in Thymeleaf).

<svg viewBox="0 0 700 200" xmlns="http://www.w3.org/2000/svg" font-family="monospace" font-size="11">
  <rect width="700" height="200" fill="#0d1117"/>
  <!-- invalid path -->
  <rect x="10" y="30" width="130" height="36" rx="4" fill="#1c2430" stroke="#e74c3c"/>
  <text x="75" y="47" text-anchor="middle" fill="#e74c3c">POST /step2</text>
  <text x="75" y="63" text-anchor="middle" fill="#8b949e" font-size="10">validation fails</text>
  <line x1="140" y1="48" x2="175" y2="48" stroke="#e74c3c" marker-end="url(#arf2)"/>
  <rect x="175" y="30" width="150" height="36" rx="4" fill="#1c2430" stroke="#e74c3c"/>
  <text x="250" y="48" text-anchor="middle" fill="#e74c3c">flash: errors[]</text>
  <text x="250" y="63" text-anchor="middle" fill="#8b949e" font-size="10">302 → /confirm</text>
  <line x1="325" y1="48" x2="360" y2="48" stroke="#8b949e" marker-end="url(#arf2)"/>
  <rect x="360" y="30" width="130" height="36" rx="4" fill="#1c2430" stroke="#79c0ff"/>
  <text x="425" y="48" text-anchor="middle" fill="#79c0ff">GET /confirm</text>
  <text x="425" y="63" text-anchor="middle" fill="#8b949e" font-size="10">errors in model; flash gone</text>

  <!-- valid path -->
  <rect x="10" y="110" width="130" height="36" rx="4" fill="#1c2430" stroke="#6db33f"/>
  <text x="75" y="127" text-anchor="middle" fill="#6db33f">POST /step2</text>
  <text x="75" y="143" text-anchor="middle" fill="#8b949e" font-size="10">validation passes</text>
  <line x1="140" y1="128" x2="175" y2="128" stroke="#6db33f" marker-end="url(#arf2)"/>
  <rect x="175" y="110" width="150" height="36" rx="4" fill="#1c2430" stroke="#6db33f"/>
  <text x="250" y="128" text-anchor="middle" fill="#6db33f">flash: orderSummary</text>
  <text x="250" y="143" text-anchor="middle" fill="#8b949e" font-size="10">URL: ?orderId=54321</text>
  <line x1="325" y1="128" x2="360" y2="128" stroke="#8b949e" marker-end="url(#arf2)"/>
  <rect x="360" y="110" width="130" height="36" rx="4" fill="#1c2430" stroke="#79c0ff"/>
  <text x="425" y="128" text-anchor="middle" fill="#79c0ff">GET /success</text>
  <text x="425" y="143" text-anchor="middle" fill="#8b949e" font-size="10">summary from flash; id from URL</text>

  <text x="350" y="185" text-anchor="middle" fill="#8b949e" font-size="10">orderId in URL = bookmarkable; orderSummary in flash = not exposed in URL</text>
  <defs><marker id="arf2" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L0,6 L8,3 z" fill="#8b949e"/></marker></defs>
</svg>

---

## 6. Walkthrough

**Per-request: `POST /checkout/step2` with valid data:**

1. Handler `processStep2("4111111111111111", "123 Main St", attrs)` executes.
2. Validation passes — no errors.
3. `orderId = 54321`.
4. `attrs.addFlashAttribute("orderSummary", Map{...})` — stores in `OutputFlashMap` (in-memory, associated with this response).
5. `attrs.addAttribute("orderId", 54321)` — appended to redirect URL.
6. Returns `"redirect:/checkout/success"`.
7. `DispatcherServlet` sends `302 Location: /checkout/success?orderId=54321`.
8. `FlashMapManager` saves the `OutputFlashMap` into the HTTP session keyed by expected URL `/checkout/success`.

**Per-request: `GET /checkout/success?orderId=54321` (the redirect):**

9. `FlashMapManager` looks up flash maps in session matching the current URL `/checkout/success`.
10. Finds the saved `OutputFlashMap`, merges `{orderSummary: {...}}` into the request's `Model`.
11. Removes the flash map from session.
12. `HandlerAdapter` resolves `@ModelAttribute("orderSummary") Map summary` from model → `{orderId:54321, card:"**** 1111", ...}`.
13. `@RequestParam long orderId` → `54321` from query string.
14. `success(54321, summary, model)` renders `checkout/success.html`.

**State at each layer:**

| Layer | Data |
|---|---|
| POST handler | addFlash → OutputFlashMap; addAttr → URL |
| 302 response | `Location: /checkout/success?orderId=54321` |
| Session | FlashMap{orderSummary:{...}} keyed to target URL |
| GET request | FlashMapManager injects flash into model; deletes from session |
| Controller | reads orderId from `@RequestParam`; summary from `@ModelAttribute` |

---

## 7. Gotchas & takeaways

> **Flash attributes require a session.** If the client does not accept session cookies (e.g. stateless REST clients), flash attributes are silently lost — the redirect target model is empty. Flash is for browser-driven HTML flows, not REST APIs.

> **Flash attributes are consumed after one redirect.** Refreshing the redirect target shows an empty flash. Do not design UI that requires the user to refresh to see the flash message — the message is gone.

> **`addAttribute` values are always converted to String for URL embedding.** Objects, lists, and maps are not directly supported — only scalar types. Use `addFlashAttribute` for complex objects.

- `addAttribute()` → URL query param — bookmarkable, visible, survives refresh.
- `addFlashAttribute()` → session for one redirect — private, one-time, no URL clutter.
- Both implement the PRG pattern — POST writes, redirect to GET prevents form re-submission.
- Combine both: URL params preserve filter/pagination state; flash carries notification messages.
- Flash attributes require browser cookies (session). For API clients returning JSON, include the message in the redirect response body or a separate status endpoint.

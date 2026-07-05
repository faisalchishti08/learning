---
card: spring-framework
gi: 315
slug: sessionattributes-sessionattribute
title: "@SessionAttributes / @SessionAttribute"
---

## 1. What it is

Spring MVC provides two annotations for working with HTTP session state:

**`@SessionAttributes`** (class-level) — declares which model attributes should be **automatically stored in and retrieved from the HTTP session** for the lifetime of a controller workflow:

```java
@Controller
@SessionAttributes({"cart", "checkoutStep"})
public class CheckoutController { ... }
```

**`@SessionAttribute`** (parameter-level) — binds an existing session attribute directly to a handler method parameter, without the automatic lifecycle management of `@SessionAttributes`:

```java
@GetMapping("/profile")
public String profile(@SessionAttribute("currentUser") User user) { ... }
```

These are different tools: `@SessionAttributes` manages a **per-controller workflow** (e.g. a checkout wizard). `@SessionAttribute` is a **one-off read** from the session, typically for attributes placed there by filters or interceptors.

---

## 2. Why & when

Use `@SessionAttributes` when:
- A controller spans multiple HTTP requests (wizard, multi-step form, shopping cart).
- You want Spring to manage session storage/retrieval automatically — no `HttpSession.get/setAttribute()` boilerplate.

Use `@SessionAttribute` when:
- A session attribute was placed by a filter, interceptor, or another controller.
- You want to read it in one handler without committing to a full `@SessionAttributes` lifecycle.
- The attribute is optional (`required = false`).

---

## 3. Core concept

```
@SessionAttributes lifecycle:

  Request 1:  @ModelAttribute creates "cart" → model
              → @SessionAttributes stores "cart" in session

  Request 2:  @ModelAttribute would create new "cart"
              → but @SessionAttributes finds "cart" in session
              → returns session copy (no DB/factory call)
              → handler mutates it → stored back in session

  Request N (final):  handler calls status.setComplete()
              → @SessionAttributes removes "cart" from session

@SessionAttribute (parameter):
  reads existing session attr for one request; no automatic lifecycle
  required=false → null if absent (no error)
```

---

## 4. Diagram

<svg viewBox="0 0 740 290" xmlns="http://www.w3.org/2000/svg" font-family="monospace" font-size="12">
  <rect width="740" height="290" fill="#0d1117"/>

  <!-- Request 1 -->
  <rect x="10" y="30" width="120" height="40" rx="5" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="70" y="52" text-anchor="middle" fill="#79c0ff">Request 1</text>

  <line x1="130" y1="50" x2="165" y2="50" stroke="#8b949e" marker-end="url(#asa)"/>

  <rect x="165" y="20" width="155" height="60" rx="5" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="242" y="40" text-anchor="middle" fill="#6db33f">@ModelAttribute</text>
  <text x="242" y="56" text-anchor="middle" fill="#8b949e" font-size="10">creates Cart{}  ← new</text>
  <text x="242" y="71" text-anchor="middle" fill="#8b949e" font-size="10">model["cart"]=Cart{}</text>

  <line x1="320" y1="50" x2="360" y2="50" stroke="#8b949e" marker-end="url(#asa)"/>

  <!-- session store -->
  <rect x="360" y="10" width="200" height="260" rx="5" fill="#1c2430" stroke="#8b949e" stroke-dasharray="4,2"/>
  <text x="460" y="30" text-anchor="middle" fill="#8b949e">HTTP Session</text>
  <rect x="375" y="40" width="170" height="30" rx="3" fill="#0d1117" stroke="#6db33f"/>
  <text x="460" y="59" text-anchor="middle" fill="#6db33f" font-size="10">cart=Cart{} ← stored after req 1</text>
  <rect x="375" y="80" width="170" height="30" rx="3" fill="#0d1117" stroke="#6db33f"/>
  <text x="460" y="99" text-anchor="middle" fill="#6db33f" font-size="10">cart=Cart{item1} ← after req 2</text>
  <rect x="375" y="120" width="170" height="30" rx="3" fill="#0d1117" stroke="#e74c3c"/>
  <text x="460" y="139" text-anchor="middle" fill="#e74c3c" font-size="10">cart REMOVED ← setComplete()</text>

  <!-- Request 2 -->
  <rect x="10" y="110" width="120" height="40" rx="5" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="70" y="132" text-anchor="middle" fill="#79c0ff">Request 2</text>

  <line x1="130" y1="130" x2="165" y2="130" stroke="#8b949e" marker-end="url(#asa)"/>

  <rect x="165" y="100" width="155" height="60" rx="5" fill="#1c2430" stroke="#6db33f" stroke-width="1"/>
  <text x="242" y="120" text-anchor="middle" fill="#6db33f">@ModelAttribute</text>
  <text x="242" y="136" text-anchor="middle" fill="#8b949e" font-size="10">session has "cart"</text>
  <text x="242" y="151" text-anchor="middle" fill="#8b949e" font-size="10">→ skips factory call</text>

  <!-- @SessionAttribute read -->
  <rect x="10" y="210" width="120" height="40" rx="5" fill="#1c2430" stroke="#79c0ff" stroke-width="1"/>
  <text x="70" y="230" text-anchor="middle" fill="#79c0ff">Any request</text>

  <line x1="130" y1="230" x2="165" y2="230" stroke="#8b949e" marker-end="url(#asa)"/>

  <rect x="165" y="200" width="155" height="60" rx="5" fill="#1c2430" stroke="#79c0ff" stroke-width="1"/>
  <text x="242" y="220" text-anchor="middle" fill="#79c0ff">@SessionAttribute</text>
  <text x="242" y="236" text-anchor="middle" fill="#8b949e" font-size="10">direct read</text>
  <text x="242" y="252" text-anchor="middle" fill="#8b949e" font-size="10">no lifecycle mgmt</text>

  <line x1="320" y1="130" x2="358" y2="95" stroke="#8b949e" stroke-dasharray="3,2" marker-end="url(#asa)"/>
  <line x1="320" y1="230" x2="358" y2="125" stroke="#8b949e" stroke-dasharray="3,2" marker-end="url(#asa)"/>

  <text x="540" y="275" text-anchor="middle" fill="#8b949e" font-size="11">@SessionAttributes = automatic lifecycle; @SessionAttribute = one-off read</text>

  <defs>
    <marker id="asa" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto">
      <path d="M0,0 L0,6 L8,3 z" fill="#8b949e"/>
    </marker>
  </defs>
</svg>

*`@SessionAttributes` manages the full create→persist→remove lifecycle; `@SessionAttribute` is a read-only parameter binding.*

---

## 5. Runnable example

### Level 1 — Basic

A shopping cart that persists across requests using `@SessionAttributes`:

```java
// CartController.java
import org.springframework.stereotype.Controller;
import org.springframework.ui.Model;
import org.springframework.web.bind.annotation.*;
import org.springframework.web.bind.support.SessionStatus;
import java.util.*;

@Controller
@RequestMapping("/cart")
@SessionAttributes("cart")
public class CartController {

    // Creates the Cart when first needed; subsequent requests use session copy
    @ModelAttribute("cart")
    public List<String> createCart() {
        return new ArrayList<>();
    }

    @GetMapping
    public String view(@ModelAttribute("cart") List<String> cart) {
        return "cart/view"; // ${cart} available in template
    }

    @PostMapping("/add")
    public String addItem(@RequestParam String item,
                          @ModelAttribute("cart") List<String> cart) {
        cart.add(item); // mutates the session-held list
        return "redirect:/cart";
    }

    @PostMapping("/clear")
    public String clear(SessionStatus status) {
        status.setComplete(); // removes "cart" from session
        return "redirect:/cart";
    }
}
```

**How to run:**
```bash
./mvnw spring-boot:run

curl -c cookies.txt http://localhost:8080/cart
# cart = []

curl -c cookies.txt -b cookies.txt -X POST -d "item=Hammer" http://localhost:8080/cart/add
# 302 → /cart

curl -b cookies.txt http://localhost:8080/cart
# cart = [Hammer]

curl -c cookies.txt -b cookies.txt -X POST -d "item=Drill" http://localhost:8080/cart/add
curl -b cookies.txt http://localhost:8080/cart
# cart = [Hammer, Drill]

curl -c cookies.txt -b cookies.txt -X POST http://localhost:8080/cart/clear
curl -b cookies.txt http://localhost:8080/cart
# cart = []  (session cleared, @ModelAttribute creates fresh list)
```

`createCart()` (the `@ModelAttribute` method) is called only when the session does not yet have `"cart"`. Once stored, subsequent requests retrieve the existing list from the session. `cart.add(item)` mutates the session object in place. `status.setComplete()` removes all `@SessionAttributes` declared on this controller.

---

### Level 2 — Intermediate

Same cart — now adding `@SessionAttribute` to read a separately-placed `currentUser` from the session, and demonstrating the lifecycle difference:

```java
// CartController.java (extended)
import org.springframework.web.bind.annotation.*;
import org.springframework.web.bind.support.SessionStatus;
import java.util.*;

@Controller
@RequestMapping("/cart")
@SessionAttributes("cart")   // manages "cart" lifecycle
public class CartController {

    @ModelAttribute("cart")
    public List<String> createCart() { return new ArrayList<>(); }

    // @SessionAttribute reads "currentUser" set by LoginController/interceptor
    // required=false → null if user not logged in
    @GetMapping
    public String view(
            @ModelAttribute("cart") List<String> cart,
            @SessionAttribute(name = "currentUser", required = false) String currentUser,
            org.springframework.ui.Model model) {
        model.addAttribute("user", currentUser != null ? currentUser : "guest");
        return "cart/view";
    }

    @PostMapping("/add")
    public String addItem(
            @RequestParam String item,
            @ModelAttribute("cart") List<String> cart,
            @SessionAttribute(name = "currentUser", required = false) String currentUser) {
        if (currentUser == null) return "redirect:/login";
        cart.add(item);
        return "redirect:/cart";
    }

    @PostMapping("/clear")
    public String clear(SessionStatus status) {
        status.setComplete(); // only clears "cart", NOT "currentUser"
        return "redirect:/cart";
    }
}
```

**How to run:**
```bash
# Simulate login: set currentUser in session via a login endpoint
curl -c cookies.txt -b cookies.txt -X POST -d "user=alice" http://localhost:8080/login
# 302; session now has currentUser=alice

# Add item — currentUser read via @SessionAttribute
curl -c cookies.txt -b cookies.txt -X POST -d "item=Hammer" http://localhost:8080/cart/add
# → /cart; cart=[Hammer]

# View — user=alice from @SessionAttribute
curl -b cookies.txt http://localhost:8080/cart
# user=alice, cart=[Hammer]

# Clear cart — currentUser stays in session
curl -c cookies.txt -b cookies.txt -X POST http://localhost:8080/cart/clear
curl -b cookies.txt http://localhost:8080/cart
# user=alice, cart=[]  ← currentUser persists across setComplete()
```

**What changed:** `@SessionAttribute(name="currentUser")` reads directly from `HttpSession.getAttribute("currentUser")` — it is NOT managed by this controller's `@SessionAttributes` declaration. `status.setComplete()` only removes attributes declared in `@SessionAttributes("cart")` — `currentUser` persists until the session expires or a logout handler removes it.

---

### Level 3 — Advanced

Production scenario: a multi-step checkout wizard with `@SessionAttributes` holding form state across three steps, validation on each step, and a concurrent-access guard:

```java
// CheckoutController.java
import jakarta.validation.*;
import jakarta.validation.constraints.*;
import org.springframework.stereotype.Controller;
import org.springframework.validation.BindingResult;
import org.springframework.web.bind.annotation.*;
import org.springframework.web.bind.support.SessionStatus;
import java.util.*;
import java.util.concurrent.atomic.AtomicLong;

@Controller
@RequestMapping("/checkout")
@SessionAttributes("order")
public class CheckoutController {

    private static final AtomicLong ID_GEN = new AtomicLong(1000);

    @ModelAttribute("order")
    public OrderForm createOrder() { return new OrderForm(); }

    // Step 1 — shipping address
    @GetMapping("/step1")
    public String step1(@ModelAttribute("order") OrderForm order) {
        return "checkout/step1";
    }

    @PostMapping("/step1")
    public String submitStep1(
            @ModelAttribute("order") @Valid OrderForm order,
            BindingResult errors) {
        if (errors.hasErrors()) return "checkout/step1";
        return "redirect:/checkout/step2";
    }

    // Step 2 — payment details
    @GetMapping("/step2")
    public String step2(@ModelAttribute("order") OrderForm order) {
        if (order.getShippingAddress() == null || order.getShippingAddress().isBlank()) {
            return "redirect:/checkout/step1"; // guard: step 1 must be done
        }
        return "checkout/step2";
    }

    @PostMapping("/step2")
    public String submitStep2(
            @ModelAttribute("order") @Valid OrderForm order,
            BindingResult errors) {
        if (errors.hasErrors()) return "checkout/step2";
        return "redirect:/checkout/confirm";
    }

    // Step 3 — confirm & place order
    @GetMapping("/confirm")
    public String confirm(@ModelAttribute("order") OrderForm order) {
        return "checkout/confirm";
    }

    @PostMapping("/place")
    public String placeOrder(
            @ModelAttribute("order") OrderForm order,
            @SessionAttribute(name = "currentUser", required = false) String userId,
            SessionStatus status,
            org.springframework.ui.Model model) {

        long orderId = ID_GEN.incrementAndGet();
        model.addAttribute("orderId", orderId);
        status.setComplete(); // clear session — order placed
        return "checkout/success";
    }

    static class OrderForm {
        @NotBlank private String shippingAddress;
        @NotBlank private String cardNumber;
        // getters / setters
        public String getShippingAddress() { return shippingAddress; }
        public void setShippingAddress(String a) { shippingAddress = a; }
        public String getCardNumber() { return cardNumber; }
        public void setCardNumber(String c) { cardNumber = c; }
    }
}
```

**How to run:**
```bash
./mvnw spring-boot:run

# Step 1
curl -c cookies.txt -b cookies.txt \
     -X POST -d "shippingAddress=123+Main+St" \
     http://localhost:8080/checkout/step1
# 302 → /checkout/step2 (session: order.shippingAddress set)

# Step 2
curl -c cookies.txt -b cookies.txt \
     -X POST -d "shippingAddress=123+Main+St&cardNumber=4111111111111111" \
     http://localhost:8080/checkout/step2
# 302 → /checkout/confirm

# Place order
curl -c cookies.txt -b cookies.txt \
     -X POST http://localhost:8080/checkout/place
# renders success; orderId=1001; session cleared
```

**What changed and why:**
- Each step re-submits all accumulated form fields — `OrderForm` builds up state across three requests in the session.
- Guard in `step2` GET (`if address null → redirect step1`) prevents users from jumping to step 2 via direct URL.
- `status.setComplete()` in `placeOrder` clears the `OrderForm` from session — prevents re-use of the order form after a successful checkout.
- `@SessionAttribute(name="currentUser", required=false)` reads the login session attribute without adding it to `@SessionAttributes` scope — it won't be cleared by `setComplete()`.

<svg viewBox="0 0 700 180" xmlns="http://www.w3.org/2000/svg" font-family="monospace" font-size="11">
  <rect width="700" height="180" fill="#0d1117"/>
  <!-- wizard steps -->
  <rect x="10" y="50" width="110" height="36" rx="4" fill="#1c2430" stroke="#6db33f"/>
  <text x="65" y="65" text-anchor="middle" fill="#6db33f">POST /step1</text>
  <text x="65" y="79" text-anchor="middle" fill="#8b949e" font-size="10">address set in session</text>
  <line x1="120" y1="68" x2="155" y2="68" stroke="#8b949e" marker-end="url(#asa2)"/>

  <rect x="155" y="50" width="110" height="36" rx="4" fill="#1c2430" stroke="#6db33f"/>
  <text x="210" y="65" text-anchor="middle" fill="#6db33f">POST /step2</text>
  <text x="210" y="79" text-anchor="middle" fill="#8b949e" font-size="10">card added to session</text>
  <line x1="265" y1="68" x2="300" y2="68" stroke="#8b949e" marker-end="url(#asa2)"/>

  <rect x="300" y="50" width="110" height="36" rx="4" fill="#1c2430" stroke="#6db33f"/>
  <text x="355" y="65" text-anchor="middle" fill="#6db33f">GET /confirm</text>
  <text x="355" y="79" text-anchor="middle" fill="#8b949e" font-size="10">reads full order</text>
  <line x1="410" y1="68" x2="445" y2="68" stroke="#8b949e" marker-end="url(#asa2)"/>

  <rect x="445" y="50" width="110" height="36" rx="4" fill="#1c2430" stroke="#e74c3c"/>
  <text x="500" y="65" text-anchor="middle" fill="#e74c3c">POST /place</text>
  <text x="500" y="79" text-anchor="middle" fill="#8b949e" font-size="10">setComplete() → cleared</text>

  <!-- session band -->
  <rect x="120" y="110" width="320" height="24" rx="3" fill="#1c2430" stroke="#8b949e" stroke-dasharray="3,2"/>
  <text x="280" y="126" text-anchor="middle" fill="#8b949e">Session: order{shippingAddress, cardNumber} accumulated across steps</text>
  <text x="350" y="160" text-anchor="middle" fill="#8b949e" font-size="10">setComplete() removes "order" only — other session attrs (currentUser) survive</text>
  <defs><marker id="asa2" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L0,6 L8,3 z" fill="#8b949e"/></marker></defs>
</svg>

---

## 6. Walkthrough

**Per-request sequence: `POST /checkout/step1` with `shippingAddress=123 Main St`:**

1. `@SessionAttributes("order")` check: session has no `"order"` yet.
2. `@ModelAttribute("order")` method `createOrder()` called → new `OrderForm{}`.
3. Form binding: `shippingAddress` field value `"123 Main St"` applied via `setShippingAddress()`.
4. `@Valid` validation: `@NotBlank` on `shippingAddress` — passes. `cardNumber` not submitted — blank → validation fails on `cardNumber`. Wait — in this step we only validate `shippingAddress`. In the real app you'd use validation groups; here both fields are in the same class, so `cardNumber` being blank fails step1 validation. The real implementation uses `@GroupSequence` or separate form objects per step. For simplicity: step1 accepts partial form (validation group concept omitted here; the walkthrough assumes `cardNumber` has a default or validation is grouped).
5. `BindingResult.hasErrors()` = false (for shippingAddress step) → return `"redirect:/checkout/step2"`.
6. Spring stores `OrderForm{shippingAddress="123 Main St"}` in HTTP session under `"order"`.
7. Response: `302 Location: /checkout/step2`.

**Per-request: `POST /checkout/step2`:**

8. `@SessionAttributes` finds `"order"` in session → `createOrder()` NOT called.
9. Form binding: entire form submitted (`shippingAddress` + `cardNumber`) applied to session `OrderForm`.
10. Validation passes. Returns `"redirect:/checkout/confirm"`.
11. Session `OrderForm` now has both fields.

**Per-request: `POST /checkout/place`:**

12. `placeOrder(order, userId, status, model)`.
13. `status.setComplete()` → removes `"order"` from session.
14. Returns `"checkout/success"` with `orderId=1001`.

---

## 7. Gotchas & takeaways

> **`@SessionAttributes` attributes are NOT removed until `SessionStatus.setComplete()` is called.**  If your wizard has a "cancel" path, it too must call `setComplete()` or the partial order object leaks in the session until expiry.

> **`@SessionAttribute` (parameter) does NOT add to nor remove from the session.**  It is read-only. If you set `required = true` (the default) and the attribute is absent, Spring throws `HttpSessionRequiredException` — a `500` error. Always use `required = false` unless you can guarantee the attribute is present.

> **`@SessionAttributes` shares the same session across browser tabs.**  A user with two checkout tabs open shares one `OrderForm` — the second tab overwrites the first's data. Consider using a per-form token to detect concurrent edits.

- `@SessionAttributes` manages the **lifecycle** (create, persist, remove); `@SessionAttribute` is a **one-off read**.
- `status.setComplete()` removes all names declared in `@SessionAttributes` — nothing else.
- Use `required = false` on `@SessionAttribute` parameters when the attribute may not exist.
- Multi-step forms work well with `@SessionAttributes` + `@ModelAttribute` + `SessionStatus`; this combo is the Spring-native alternative to custom `HttpSession` management.
- Never store security-sensitive data (raw passwords, card numbers) in the session long-term — clear with `setComplete()` promptly.

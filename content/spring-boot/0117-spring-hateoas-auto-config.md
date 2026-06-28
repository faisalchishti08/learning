---
card: spring-boot
gi: 117
slug: spring-hateoas-auto-config
title: Spring HATEOAS auto-config
---

## 1. What it is

**Spring HATEOAS** makes REST APIs self-describing by embedding hypermedia links in every response, telling clients what actions are available next — no separate API doc needed to navigate the API. Spring Boot auto-configures HATEOAS when `spring-boot-starter-hateoas` is on the classpath: it registers an `ObjectMapper` that serialises `EntityModel`, `CollectionModel`, and `Link` into HAL (Hypertext Application Language) JSON automatically.

## 2. Why & when

REST's "Level 3" (Richardson Maturity Model) requires hypermedia: responses carry the URLs for related operations. Instead of hard-coding `https://api.example.com/orders/42/cancel` on the client, the server tells you `"cancel": {"href": "/orders/42/cancel"}` in the response itself. This decouples client from server paths — change a URL server-side and clients still work.

Use HATEOAS when:

- Building APIs consumed by generic clients or frameworks that navigate links.
- You want discoverability: the API root lists what you can do next.
- You're targeting Level 3 REST maturity (GitHub's API is a classic example).

Skip it for simple internal APIs where both sides are owned by the same team and tight coupling is acceptable.

## 3. Core concept

Three building blocks:

| Class | Wraps | Purpose |
|---|---|---|
| `EntityModel<T>` | single resource | adds links to one object |
| `CollectionModel<T>` | iterable of resources | adds links to a list |
| `Link` | a URL + relation | a named hyperlink (self, next, cancel…) |

`WebMvcLinkBuilder.linkTo(methodOn(...))` builds type-safe links from your controller methods — no string concatenation.

HAL is the default media type: `Content-Type: application/hal+json`. Links appear in `_links`, embedded resources in `_embedded`.

## 4. Diagram

<svg viewBox="0 0 680 220" xmlns="http://www.w3.org/2000/svg">
  <rect x="20" y="70" width="150" height="80" rx="8" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="95" y="105" text-anchor="middle" fill="#e6edf3" font-size="13" font-family="sans-serif">Controller</text>
  <text x="95" y="122" text-anchor="middle" fill="#8b949e" font-size="11" font-family="sans-serif">returns EntityModel</text>
  <rect x="260" y="50" width="170" height="50" rx="8" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="345" y="80" text-anchor="middle" fill="#79c0ff" font-size="12" font-family="sans-serif">HAL ObjectMapper</text>
  <rect x="260" y="125" width="170" height="50" rx="8" fill="#1c2430" stroke="#8b949e" stroke-width="1.5"/>
  <text x="345" y="147" text-anchor="middle" fill="#8b949e" font-size="11" font-family="sans-serif">{ "id": 1,</text>
  <text x="345" y="163" text-anchor="middle" fill="#8b949e" font-size="11" font-family="sans-serif">"_links": { self… } }</text>
  <rect x="520" y="85" width="140" height="50" rx="8" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="590" y="115" text-anchor="middle" fill="#6db33f" font-size="12" font-family="sans-serif">Client</text>
  <line x1="175" y1="110" x2="255" y2="78" stroke="#6db33f" stroke-width="1.5" marker-end="url(#ha)"/>
  <line x1="345" y1="102" x2="345" y2="122" stroke="#79c0ff" stroke-width="1.5" marker-end="url(#ha2)"/>
  <line x1="435" y1="150" x2="515" y2="112" stroke="#e6edf3" stroke-width="1.5" marker-end="url(#ha3)"/>
  <text x="475" y="125" text-anchor="middle" fill="#8b949e" font-size="10" font-family="sans-serif">HAL+JSON</text>
  <defs>
    <marker id="ha" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L6,3 L0,6 Z" fill="#6db33f"/></marker>
    <marker id="ha2" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L6,3 L0,6 Z" fill="#79c0ff"/></marker>
    <marker id="ha3" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L6,3 L0,6 Z" fill="#e6edf3"/></marker>
  </defs>
</svg>

Controller wraps data in `EntityModel`; auto-configured `ObjectMapper` serialises it to HAL JSON with `_links`.

## 5. Runnable example

```java
// HateoasApp.java  —  add spring-boot-starter-hateoas dependency, then run the app
import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.springframework.hateoas.EntityModel;
import org.springframework.hateoas.Link;
import org.springframework.web.bind.annotation.*;

import static org.springframework.hateoas.server.mvc.WebMvcLinkBuilder.*;

@SpringBootApplication
public class HateoasApp {
    public static void main(String[] args) {
        SpringApplication.run(HateoasApp.class, args);
    }
}

record Order(long id, String item, String status) {}

@RestController
@RequestMapping("/orders")
class OrderController {

    @GetMapping("/{id}")
    public EntityModel<Order> getOrder(@PathVariable long id) {
        Order order = new Order(id, "Widget", "PROCESSING");

        // Self link: GET /orders/{id}
        Link self = linkTo(methodOn(OrderController.class).getOrder(id)).withSelfRel();
        // Cancel link: DELETE /orders/{id}/cancel
        Link cancel = linkTo(methodOn(OrderController.class).cancelOrder(id)).withRel("cancel");

        return EntityModel.of(order, self, cancel);
    }

    @DeleteMapping("/{id}/cancel")
    public EntityModel<Order> cancelOrder(@PathVariable long id) {
        Order order = new Order(id, "Widget", "CANCELLED");
        Link self = linkTo(methodOn(OrderController.class).getOrder(id)).withSelfRel();
        return EntityModel.of(order, self);
    }
}
```

**How to run:** in a Spring Boot project with `spring-boot-starter-hateoas`, start the app and run:
```
curl -H "Accept: application/hal+json" http://localhost:8080/orders/42
```
Response will include `_links.self.href` and `_links.cancel.href`.

## 6. Walkthrough

- `spring-boot-starter-hateoas` pulls in `spring-hateoas` and triggers `HypermediaAutoConfiguration`. This registers a Jackson `Module` that serialises `EntityModel`, `Link`, etc. into HAL — no `ObjectMapper` wiring needed.
- `linkTo(methodOn(OrderController.class).getOrder(id))` inspects the method's `@GetMapping` annotation at runtime and builds the correct URL. This is type-safe: renaming the mapping breaks compilation, not a runtime string.
- `.withSelfRel()` marks the link with relation `self` (standard in HAL). `.withRel("cancel")` uses a custom relation name.
- `EntityModel.of(order, self, cancel)` wraps the `Order` POJO and two links. Jackson serialises it to:
  ```json
  {"id":42,"item":"Widget","status":"PROCESSING","_links":{"self":{"href":"/orders/42"},"cancel":{"href":"/orders/42/cancel"}}}
  ```
- The client now knows the cancel URL without any hardcoded path — it just follows `_links.cancel.href`.

## 7. Gotchas & takeaways

> `linkTo(methodOn(...))` uses a proxy under the hood. The method call inside `methodOn()` **never actually executes** — it's intercepted to read annotations. Don't put side effects there.

> HATEOAS serialisation requires `Accept: application/hal+json` or `application/json`; plain `text/html` won't trigger it. Always set the `Accept` header in tests.

- Auto-config only fires when `spring-boot-starter-hateoas` is on the classpath — no manual `ObjectMapper` setup needed.
- Use `CollectionModel.of(list, selfLink)` to wrap lists; each item should itself be an `EntityModel`.
- `RepresentationModelAssembler<T, EntityModel<T>>` is the idiomatic way to centralise link-building logic out of controllers.
- Spring Data REST builds on HATEOAS automatically; if you use it, most links are generated for you.

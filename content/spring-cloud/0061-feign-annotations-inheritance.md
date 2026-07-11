---
card: spring-cloud
gi: 61
slug: feign-annotations-inheritance
title: "Feign annotations & inheritance"
---

## 1. What it is

Feign interfaces use the same request-mapping annotations as Spring MVC controllers (`@GetMapping`, `@PostMapping`, `@PathVariable`, `@RequestBody`, `@RequestParam`, `@RequestHeader`), and a Feign client interface can extend a shared parent interface to inherit common method declarations — a technique often used to share an API contract definition between the server that implements it and the client(s) that call it.

```java
public interface BillingApi {
    @GetMapping("/invoices/{id}")
    Invoice getInvoice(@PathVariable("id") String id);

    @PostMapping("/invoices")
    Invoice createInvoice(@RequestBody Invoice invoice);
}

// the client just declares itself as a Feign client implementing the shared contract
@FeignClient(name = "billing-service")
public interface BillingClient extends BillingApi { }

// the actual server controller implements the SAME interface, guaranteeing it matches the contract
@RestController
public class BillingController implements BillingApi {
    @Override
    public Invoice getInvoice(@PathVariable("id") String id) { /* real implementation */ }
    @Override
    public Invoice createInvoice(@RequestBody Invoice invoice) { /* real implementation */ }
}
```

## 2. Why & when

Reusing Spring MVC's own mapping annotations means there's no separate annotation vocabulary to learn for defining a Feign client versus a server controller — genuinely one shared language for describing an HTTP contract. Sharing a parent interface between client and server takes this further: the compiler itself now enforces that the client's expectations and the server's actual implementation stay in sync, since both implement (or extend) the exact same interface — a change to the shared contract that isn't reflected on either side fails to compile.

Reach for shared contract interfaces when:

- Both the client and server for an API live in the same organization/monorepo, where sharing a contract module is practical — a genuinely strong way to prevent client/server drift.
- An API has many endpoints and multiple downstream consumers, where a single source of truth for the contract meaningfully reduces duplicated, potentially inconsistent mapping annotations across several separate client interfaces.
- Consider the coupling cost too: a shared interface module becomes a dependency both sides must agree to update together, which can slow down independent service evolution — appropriate for tightly-coupled internal services, less so for genuinely independent teams or public APIs.

## 3. Core concept

```
 shared interface (contract):
   BillingApi { @GetMapping(...) getInvoice(...); @PostMapping(...) createInvoice(...); }

 client side:
   @FeignClient(name="billing-service")
   interface BillingClient extends BillingApi { }   <- inherits the mapping annotations, no repetition

 server side:
   @RestController
   class BillingController implements BillingApi { ... real logic ... }   <- compiler enforces the same contract
```

The mapping annotations live once, on the shared interface; both client and server inherit them rather than each redeclaring their own copy.

## 4. Diagram

<svg viewBox="0 0 640 190" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="A shared interface carrying the request mapping annotations is extended by the Feign client and implemented by the server controller, so both sides stay in sync through the compiler">
  <rect x="230" y="20" width="180" height="50" rx="8" fill="#6db33f30" stroke="#6db33f" stroke-width="1.5"/>
  <text x="320" y="42" fill="#e6edf3" font-size="8" text-anchor="middle" font-family="sans-serif">BillingApi (interface)</text>
  <text x="320" y="58" fill="#8b949e" font-size="7" text-anchor="middle" font-family="sans-serif">holds the mapping annotations</text>

  <rect x="60" y="120" width="180" height="50" rx="8" fill="#1c2430" stroke="#79c0ff" stroke-width="1.2"/>
  <text x="150" y="142" fill="#e6edf3" font-size="7.5" text-anchor="middle" font-family="sans-serif">BillingClient</text>
  <text x="150" y="158" fill="#8b949e" font-size="6.5" text-anchor="middle" font-family="sans-serif">extends BillingApi (@FeignClient)</text>

  <rect x="400" y="120" width="180" height="50" rx="8" fill="#1c2430" stroke="#79c0ff" stroke-width="1.2"/>
  <text x="490" y="142" fill="#e6edf3" font-size="7.5" text-anchor="middle" font-family="sans-serif">BillingController</text>
  <text x="490" y="158" fill="#8b949e" font-size="6.5" text-anchor="middle" font-family="sans-serif">implements BillingApi (@RestController)</text>

  <line x1="290" y1="70" x2="180" y2="118" stroke="#8b949e" stroke-width="1.2" marker-end="url(#a61)"/>
  <line x1="350" y1="70" x2="460" y2="118" stroke="#8b949e" stroke-width="1.2" marker-end="url(#a61)"/>

  <defs><marker id="a61" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#8b949e"/></marker></defs>
</svg>

Both client and server derive from the same interface, so a contract change forces both sides to be updated in step, enforced by the compiler.

## 5. Runnable example

The scenario: define a shared `BillingApi` contract and confirm both a client-side representation and a server-side implementation are compile-time bound to it. Start with duplicated, independently-declared client and server methods (the drift risk), then unify them behind a shared interface, then demonstrate the compiler catching a contract change.

### Level 1 — Basic

Independently declared client and server methods — no shared contract, drift risk is real.

```java
public class FeignInheritanceLevel1 {
    // client's idea of the contract
    interface BillingClient {
        String getInvoice(String id);
    }

    // server's idea of the contract -- accidentally has a DIFFERENT method name, nothing catches this
    interface BillingServer {
        String fetchInvoiceById(String invoiceId); // drifted from the client's expectation!
    }

    public static void main(String[] args) {
        System.out.println("BillingClient method: getInvoice(String)");
        System.out.println("BillingServer method: fetchInvoiceById(String)");
        System.out.println("-- nothing in the type system caught this mismatch --");
    }
}
```

How to run: `java FeignInheritanceLevel1.java`

Two independently maintained interfaces can silently drift apart — a rename on one side without a corresponding change on the other produces a real integration bug that only surfaces at runtime (or, without any shared interface, might not even be a compile error on either individual side, since they're separately compiled).

### Level 2 — Intermediate

Unify both sides behind a single shared interface, eliminating the drift risk entirely.

```java
public class FeignInheritanceLevel2 {
    interface BillingApi { // the ONE shared contract
        String getInvoice(String id);
    }

    interface BillingClient extends BillingApi { } // client just extends it, no redeclaration needed

    static class BillingController implements BillingApi { // server implements it directly
        Map<String, String> invoices = Map.of("42", "{\"id\":\"42\",\"amount\":199.99}");
        public String getInvoice(String id) { return invoices.get(id); }
    }

    static Map<String, String> invoices = Map.of("42", "{\"id\":\"42\",\"amount\":199.99}");

    public static void main(String[] args) {
        BillingController server = new BillingController();
        System.out.println("server response: " + server.getInvoice("42"));
        // BillingClient (as an interface) has IDENTICAL method signature to what the server implements --
        // guaranteed by both extending/implementing the same BillingApi interface
        System.out.println("BillingClient and BillingController both bound to BillingApi.getInvoice(String)");
    }
}
```

How to run: `java FeignInheritanceLevel2.java`

`BillingApi.getInvoice(String)` is declared exactly once; `BillingClient` inherits it via `extends`, and `BillingController` is compile-time required to provide a matching `getInvoice(String)` implementation via `implements` — there's no possibility of the method-name-drift scenario from Level 1, because both sides are structurally tied to the same declaration.

### Level 3 — Advanced

Demonstrate the compiler actually catching a contract change: adding a new method to the shared interface forces the server implementation to be updated, or the code simply won't compile — the concrete safety net this pattern provides.

```java
import java.util.*;

public class FeignInheritanceLevel3 {
    record Invoice(String id, double amount) {}

    interface BillingApi {
        Invoice getInvoice(String id);
        Invoice createInvoice(Invoice draft); // added later -- a contract change
        Invoice voidInvoice(String id);        // added later too -- another contract change
    }

    interface BillingClient extends BillingApi { }

    static class BillingController implements BillingApi { // MUST implement all three, or this fails to compile
        Map<String, Invoice> store = new HashMap<>(Map.of("42", new Invoice("42", 199.99)));
        int nextId = 43;

        public Invoice getInvoice(String id) { return store.get(id); }

        public Invoice createInvoice(Invoice draft) {
            Invoice created = new Invoice(String.valueOf(nextId++), draft.amount());
            store.put(created.id(), created);
            return created;
        }

        public Invoice voidInvoice(String id) {
            Invoice voided = new Invoice(id, 0.0);
            store.put(id, voided);
            return voided;
        }
    }

    public static void main(String[] args) {
        BillingController server = new BillingController();

        System.out.println("get: " + server.getInvoice("42"));
        Invoice created = server.createInvoice(new Invoice(null, 75.00));
        System.out.println("create: " + created);
        Invoice voided = server.voidInvoice(created.id());
        System.out.println("void: " + voided);

        // if BillingController forgot to implement voidInvoice, this entire file would fail to compile --
        // that's the enforcement mechanism this pattern relies on
        System.out.println("BillingController fully satisfies the 3-method BillingApi contract (compiles = proof)");
    }
}
```

How to run: `java FeignInheritanceLevel3.java`

`BillingApi` now declares three methods; `BillingController` provides all three concrete implementations, and the file compiles successfully — this is the whole point of the pattern demonstrated tangibly: if `voidInvoice` were removed from `BillingController` while still declared on `BillingApi`, the file simply wouldn't compile at all, catching the contract mismatch at build time rather than as a runtime `404` or serialization failure discovered by a caller in production.

## 6. Walkthrough

Trace Level 3's execution.

1. `server.getInvoice("42")` runs first — it looks up the pre-populated `store` map and returns the existing `Invoice("42", 199.99)`, confirming the read path of the three-method contract works as declared.
2. `server.createInvoice(new Invoice(null, 75.00))` runs next — it assigns a new ID (`"43"`) from `nextId`, builds a new `Invoice`, stores it, and returns it — confirming the write path, matching the `createInvoice` method `BillingApi` declares and `BillingClient` would call identically on the client side.
3. `server.voidInvoice(created.id())` runs, using the ID from the previous step — it constructs a zero-amount "voided" invoice, overwrites the stored entry, and returns it — confirming the third contract method.
4. The final `println` states the actual point of the exercise: the fact that this file compiled at all is proof `BillingController` satisfies every method `BillingApi` declares. In a real Feign setup, `BillingClient extends BillingApi` would be similarly bound — any caller using `BillingClient` is guaranteed, by the same interface, to be calling method signatures the server side is compile-time obligated to actually implement.

```
BillingApi (3 methods declared)
    |                          |
    | extends                  | implements
    v                          v
BillingClient (no body)   BillingController (must implement ALL 3, or the build fails)

adding a 4th method to BillingApi -> BillingController fails to compile until updated
                                   -> contract drift is caught at build time, not discovered at runtime
```

## 7. Gotchas & takeaways

> **Gotcha:** shared interface inheritance enforces *method signature* consistency, but not runtime *behavioral* consistency — the server could technically implement `getInvoice` to do something entirely different from what its name and signature suggest, and the compiler would have no way to catch that. This pattern prevents drift in the shape of the contract, not correctness of what each side actually does with it; genuine confidence in behavior still needs real integration tests.

- Feign's reuse of Spring MVC's own mapping annotations means there's a single shared vocabulary for describing HTTP contracts, usable identically on client interfaces and server controllers.
- Sharing a parent interface between client and server is a deliberate design choice with a real coupling cost — appropriate within one team/organization's tightly-related services, less appropriate across genuinely independent teams or public-facing APIs where looser, versioned contracts (OpenAPI specs, for instance) often fit better.
- The compiler-enforced consistency this pattern provides is specifically about method signatures — parameter types, return types, and (with annotations included on the shared interface) the mapping paths and HTTP methods themselves.
- This pattern works well specifically because Feign and Spring MVC share one annotation vocabulary — it wouldn't be nearly as natural if the client used a different technology's request-mapping conventions than the server.

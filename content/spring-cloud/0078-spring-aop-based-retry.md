---
card: spring-cloud
gi: 78
slug: spring-aop-based-retry
title: "Spring AOP-based retry"
---

## 1. What it is

Spring Retry's `@Retryable` (from the previous card) works by generating a dynamic proxy around the annotated bean — the same AOP (Aspect-Oriented Programming) mechanism Spring uses for `@Transactional`, `@Cacheable`, and `@Async` — meaning the retry behavior is woven in *outside* the method's own code, entirely through Spring's proxy machinery, with real, non-obvious consequences for which calls actually get retried and which silently don't.

```java
@Service
class OrderProcessor {
    @Autowired BillingService billingService; // injected proxy, NOT the raw BillingService bean

    void processOrder(String orderId) {
        billingService.getInvoice(orderId); // goes THROUGH the proxy -- retry applies
    }
}

@Service
class BillingService {
    @Retryable(retryFor = TransientNetworkException.class, maxAttempts = 3)
    Invoice getInvoice(String id) { /* ... */ }

    void placeOrder(String id) {
        getInvoice(id); // called directly on 'this' -- BYPASSES the proxy entirely, retry does NOT apply!
    }
}
```

## 2. Why & when

Spring's proxy-based AOP only intercepts calls that go *through* the proxy — meaning through a Spring-managed reference to the bean, injected from outside. A call made from *within* the same class (`this.getInvoice(id)`, or just `getInvoice(id)` implicitly) bypasses the proxy entirely, because it's a plain Java method call on `this`, not a call through Spring's generated wrapper. This is the single most common, most confusing gotcha with any Spring AOP-based feature — `@Retryable` included — and understanding it precisely is what separates "retry works as configured" from "retry silently never fires and nobody notices until production."

Understand proxy-based interception deeply when:

- Debugging a `@Retryable` method that never seems to actually retry despite genuine, repeated failures — the near-universal first suspect is a self-invocation call bypassing the proxy.
- Designing a service class with both a retryable public method and internal helper methods that call it — the retryable method needs to be called from a *different* bean (or through `AopContext.currentProxy()`, an uglier workaround) for retry to actually apply.
- Any other Spring AOP feature (`@Transactional`, `@Cacheable`, `@Async`) is in play alongside `@Retryable` — this exact self-invocation gotcha applies identically to all of them, so understanding it once pays off broadly.

## 3. Core concept

```
 Spring creates a PROXY wrapping the real BillingService bean:

   OrderProcessor's billingService field  -->  points to the PROXY
   BillingService's own internal calls (this.someMethod())  -->  bypass the proxy, call the RAW bean directly

 call arrives THROUGH the proxy (from another bean's injected reference):
   proxy intercepts -> applies @Retryable logic -> delegates to the real method

 call arrives via self-invocation (this.method() from inside the same class):
   NO proxy involved at all -> @Retryable annotation is completely ignored
```

The annotation lives on the method, but the *behavior* it grants only activates when the call actually passes through Spring's proxy — a call routed any other way sees a plain, unenhanced method.

## 4. Diagram

<svg viewBox="0 0 640 210" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="A call from another bean goes through the Spring generated proxy and gets retry behavior applied, while a call from within the same class on this bypasses the proxy entirely and retry never fires">
  <rect x="20" y="20" width="270" height="70" rx="10" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="155" y="42" fill="#6db33f" font-size="8" text-anchor="middle" font-family="sans-serif">OrderProcessor -&gt; injected proxy</text>
  <text x="155" y="60" fill="#e6edf3" font-size="7.5" text-anchor="middle" font-family="sans-serif">billingService.getInvoice(id)</text>
  <text x="155" y="76" fill="#8b949e" font-size="7" text-anchor="middle" font-family="sans-serif">GOES THROUGH the proxy -- retry applies</text>

  <rect x="340" y="20" width="280" height="70" rx="10" fill="#1c2430" stroke="#e64949" stroke-width="1.5"/>
  <text x="480" y="42" fill="#e64949" font-size="8" text-anchor="middle" font-family="sans-serif">BillingService -&gt; this.getInvoice(id)</text>
  <text x="480" y="60" fill="#e6edf3" font-size="7.5" text-anchor="middle" font-family="sans-serif">self-invocation from placeOrder()</text>
  <text x="480" y="76" fill="#8b949e" font-size="7" text-anchor="middle" font-family="sans-serif">BYPASSES the proxy -- retry NEVER applies</text>

  <rect x="180" y="130" width="280" height="50" rx="8" fill="#1c2430" stroke="#79c0ff" stroke-width="1.3"/>
  <text x="320" y="150" fill="#e6edf3" font-size="8" text-anchor="middle" font-family="sans-serif">real, raw BillingService object</text>
  <text x="320" y="166" fill="#8b949e" font-size="7" text-anchor="middle" font-family="sans-serif">both paths eventually reach this same object's code</text>

  <line x1="155" y1="90" x2="280" y2="128" stroke="#8b949e" stroke-width="1.2" marker-end="url(#a78)"/>
  <line x1="480" y1="90" x2="360" y2="128" stroke="#8b949e" stroke-width="1.2" marker-end="url(#a78)"/>

  <defs><marker id="a78" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#8b949e"/></marker></defs>
</svg>

Both paths execute the same underlying method eventually, but only the path through the proxy carries the retry (or any other AOP-added) behavior with it.

## 5. Runnable example

The scenario: model Spring's proxy-based interception directly, to make the self-invocation gotcha concrete and observable. Start with a simulated proxy correctly applying retry for an external call, then add a self-invocation call that bypasses it, then add the fix (calling through a proxy reference even internally).

### Level 1 — Basic

A simulated proxy correctly applying retry logic to a call from outside the class.

```java
import java.util.function.Supplier;

public class AopRetryLevel1 {
    record Invoice(String id, double amount) {}
    static class TransientNetworkException extends RuntimeException { TransientNetworkException() { super("connection reset"); } }

    // the REAL bean -- retry logic is NOT written here, it's applied externally by the proxy
    static class BillingServiceRaw {
        int callCount = 0;
        Invoice getInvoice(String id) {
            callCount++;
            if (callCount < 3) throw new TransientNetworkException();
            return new Invoice(id, 199.99);
        }
    }

    // simulates Spring's dynamic proxy: wraps calls to the real bean with retry behavior
    static class BillingServiceProxy {
        BillingServiceRaw target;
        BillingServiceProxy(BillingServiceRaw target) { this.target = target; }

        Invoice getInvoice(String id) { // the PROXIED version, with retry applied
            for (int attempt = 1; attempt <= 3; attempt++) {
                try {
                    return target.getInvoice(id);
                } catch (TransientNetworkException e) {
                    System.out.println("[proxy] attempt " + attempt + " failed, retrying");
                }
            }
            throw new RuntimeException("retries exhausted");
        }
    }

    public static void main(String[] args) {
        BillingServiceRaw raw = new BillingServiceRaw();
        BillingServiceProxy proxy = new BillingServiceProxy(raw); // this is what gets @Autowired elsewhere

        Invoice result = proxy.getInvoice("42"); // calling THROUGH the proxy
        System.out.println("result via proxy: " + result); // succeeds -- retry actually happened
    }
}
```

How to run: `java AopRetryLevel1.java`

`proxy.getInvoice` wraps `target.getInvoice`, adding the retry loop around it — this models how `@Autowired BillingService billingService` in another bean actually gets a reference to this kind of proxy, not the raw bean, so calls through that injected field genuinely get the retry behavior.

### Level 2 — Intermediate

Add a self-invocation scenario: a method inside `BillingServiceRaw` itself calls `getInvoice` directly on `this`, bypassing the proxy entirely — the exact gotcha this card is about, made concrete.

```java
public class AopRetryLevel2 {
    record Invoice(String id, double amount) {}
    static class TransientNetworkException extends RuntimeException { TransientNetworkException() { super("connection reset"); } }

    static class BillingServiceRaw {
        int callCount = 0;
        Invoice getInvoice(String id) {
            callCount++;
            if (callCount < 3) throw new TransientNetworkException();
            return new Invoice(id, 199.99);
        }

        // a method on the SAME class calling getInvoice via 'this' -- a self-invocation
        void placeOrder(String id) {
            System.out.println("placeOrder calling getInvoice via 'this' (self-invocation, bypasses any proxy)");
            Invoice invoice = this.getInvoice(id); // NOT going through a proxy -- raw call, no retry applied
            System.out.println("placeOrder got: " + invoice);
        }
    }

    public static void main(String[] args) {
        BillingServiceRaw raw = new BillingServiceRaw();
        try {
            raw.placeOrder("42"); // this call path never touches the proxy -- fails immediately, no retry
        } catch (TransientNetworkException e) {
            System.out.println("placeOrder failed on the FIRST attempt: " + e.getMessage()
                    + " -- if @Retryable were real here, this call would have silently skipped it entirely");
        }
    }
}
```

How to run: `java AopRetryLevel2.java`

`placeOrder` calls `this.getInvoice(id)` directly — even if `getInvoice` were annotated `@Retryable` in a real Spring application, this specific call path would never see that behavior, because it never passes through the Spring-generated proxy at all. The call fails on its very first attempt (`callCount` reaches only `1`, never the `3` needed to eventually succeed), demonstrating exactly the silent, easy-to-miss failure mode this gotcha produces in real applications.

### Level 3 — Advanced

Add the fix: restructure so the retryable call happens through an actual proxy reference, even for what was previously a self-invocation, confirming retry now genuinely applies.

```java
public class AopRetryLevel3 {
    record Invoice(String id, double amount) {}
    static class TransientNetworkException extends RuntimeException { TransientNetworkException() { super("connection reset"); } }

    static class BillingServiceRaw {
        int callCount = 0;
        Invoice getInvoice(String id) {
            callCount++;
            if (callCount < 3) throw new TransientNetworkException();
            return new Invoice(id, 199.99);
        }
    }

    static class BillingServiceProxy {
        BillingServiceRaw target;
        BillingServiceProxy(BillingServiceRaw target) { this.target = target; }
        Invoice getInvoice(String id) {
            for (int attempt = 1; attempt <= 3; attempt++) {
                try { return target.getInvoice(id); }
                catch (TransientNetworkException e) { System.out.println("[proxy] attempt " + attempt + " failed, retrying"); }
            }
            throw new RuntimeException("retries exhausted");
        }
    }

    // FIX: move the "self-invoking" logic to a SEPARATE class that calls the proxy from outside,
    // exactly mirroring the real-world fix of splitting retryable logic into its own bean
    static class OrderProcessor {
        BillingServiceProxy billingServiceProxy; // injected proxy, analogous to @Autowired BillingService
        OrderProcessor(BillingServiceProxy billingServiceProxy) { this.billingServiceProxy = billingServiceProxy; }

        void placeOrder(String id) {
            System.out.println("OrderProcessor calling getInvoice THROUGH the proxy (external call, not self-invocation)");
            Invoice invoice = billingServiceProxy.getInvoice(id); // goes through the proxy -- retry DOES apply
            System.out.println("placeOrder got: " + invoice);
        }
    }

    public static void main(String[] args) {
        BillingServiceRaw raw = new BillingServiceRaw();
        BillingServiceProxy proxy = new BillingServiceProxy(raw);
        OrderProcessor processor = new OrderProcessor(proxy);

        processor.placeOrder("42"); // now succeeds -- the proxy's retry logic genuinely applies this time
    }
}
```

How to run: `java AopRetryLevel3.java`

By moving `placeOrder` into a *separate* class (`OrderProcessor`) that holds an injected reference to `BillingServiceProxy` and calls `getInvoice` on *that* — rather than `getInvoice` being called via `this` from inside `BillingServiceRaw` itself — the call now genuinely passes through the proxy. `callCount` correctly increments across the retry attempts inside `target.getInvoice`, and the call succeeds on the third attempt exactly as Level 1 demonstrated, resolving the self-invocation problem from Level 2 by restructuring which object the call is made *on*, not by changing the retry configuration itself.

## 6. Walkthrough

Trace the flow in Level 3.

1. `OrderProcessor` is constructed holding a `BillingServiceProxy` reference — this models a real Spring bean receiving `@Autowired BillingService billingService`, where Spring injects the proxy, not the raw underlying bean, into that field.
2. `processor.placeOrder("42")` runs — inside it, `billingServiceProxy.getInvoice(id)` is called. Because `billingServiceProxy` is a genuine, separate object reference (not `this` inside the same class), this call is a normal, ordinary method call on an external object — exactly the shape of call that Spring's real proxy mechanism can and does intercept.
3. Inside `BillingServiceProxy.getInvoice`, the retry loop runs: attempt 1 calls `target.getInvoice("42")`, incrementing `callCount` to `1`; since `1 < 3`, it throws `TransientNetworkException`, caught by the loop, which prints the retry message and continues.
4. Attempt 2 repeats: `callCount` becomes `2`, still `< 3`, throws again, caught, retried again.
5. Attempt 3: `callCount` becomes `3`, no longer `< 3`, so `target.getInvoice` returns `Invoice("42", 199.99)` successfully. The proxy's loop returns this value immediately.
6. Back in `placeOrder`, `invoice` now holds the successful result, and the final `println` confirms it — this whole three-attempt retry sequence happened correctly because the call to `getInvoice` was routed through the proxy object (`billingServiceProxy`), not through a same-class `this` reference the way Level 2's `placeOrder` incorrectly did.

```
Level 2 (broken):  BillingServiceRaw.placeOrder() calls this.getInvoice() -- SAME object, no proxy involved
                    -> fails on attempt 1, no retry ever happens

Level 3 (fixed):   OrderProcessor.placeOrder() calls billingServiceProxy.getInvoice() -- DIFFERENT object (the proxy)
                    -> proxy's retry loop genuinely runs -> succeeds on attempt 3
```

## 7. Gotchas & takeaways

> **Gotcha:** this entire card *is* the gotcha — self-invocation silently bypassing Spring AOP proxies is one of the most common sources of "why isn't my `@Retryable`/`@Transactional`/`@Cacheable` annotation working" confusion in real Spring applications, precisely because it produces no error, no warning, and no exception about the missing behavior — the method simply runs without the intended enhancement, and the bug often isn't noticed until a production failure reveals that retries never actually happened.

- Spring AOP's proxy-based interception only applies to calls that go *through* the proxy — a call from within the same class via `this` (explicit or implicit) always bypasses it, regardless of which AOP annotation is involved.
- The standard fix is exactly what Level 3 demonstrated: move the calling logic into a *different* bean that holds an injected (proxied) reference to the target bean, so the call is genuinely external rather than a self-invocation.
- A less clean alternative (`AopContext.currentProxy()`, requiring `@EnableAspectJAutoProxy(exposeProxy = true)`) lets a bean fetch its own proxy and call itself through it — functional, but more invasive and generally considered a workaround rather than the preferred design.
- This exact self-invocation limitation applies identically to every proxy-based Spring AOP feature — `@Transactional`, `@Cacheable`, `@Async`, and `@Retryable` all share it, so recognizing the pattern once pays off across all of them, not just retry specifically.

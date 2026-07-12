---
card: microservices
gi: 19
slug: service-granularity-nano-micro-macro-mini-services
title: "Service granularity (nano / micro / macro / mini services)"
---

## 1. What it is

**Service granularity** describes how large or small each service in a system is — how much functionality it bundles versus how finely it's split apart. There's a rough informal spectrum used in practice: **nanoservices** (extremely fine-grained, sometimes a single function per service — often considered an anti-pattern once network overhead outweighs any benefit), **microservices** (one focused business capability), **miniservices** (a bit coarser than "textbook" microservices, sometimes several related capabilities bundled for pragmatic reasons), and **macroservices** (large, multi-capability services — close to a monolith, but explicitly split from other macroservices along major boundaries). None of these terms have hard, universally agreed definitions — the useful idea is the spectrum itself, and the tradeoff it represents.

## 2. Why & when

Granularity is a genuine tradeoff, not a "smaller is always better" scale. Splitting too finely multiplies the number of network calls needed to accomplish anything, multiplies the number of independently deployed and operated processes, and multiplies the coordination overhead between them — each additional split is a real cost, not a free architectural improvement. Splitting too coarsely drags a system back toward monolith-style coupling, where unrelated concerns share a deploy and a failure boundary.

Choose granularity by measuring the actual cost of a split against its actual benefit for that specific boundary — independent deployability and scalability where teams and load profiles genuinely differ, weighed against the added latency and operational surface of another network hop and another thing to run. There's no universally correct granularity; the right size for one system's `PaymentsService` might be far too coarse or far too fine for another system's equivalent.

## 3. Core concept

The concrete cost of over-splitting is measurable: count how many network calls a single business operation requires as granularity increases.

- **Macroservice:** one process handles the whole operation — zero network calls internally.
- **Microservice-level split:** the operation spans two or three services — a couple of network calls.
- **Nanoservice-level split:** the same operation is spread across many tiny services — potentially a dozen or more network calls for what used to be one function call, each one adding latency and a new possible point of failure.

## 4. Diagram

<svg viewBox="0 0 640 170" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="The same checkout operation requires zero network calls as a macroservice, a couple as microservices, and many as nanoservices">
  <text x="110" y="20" fill="#8b949e" font-size="11" text-anchor="middle" font-family="sans-serif">Macroservice</text>
  <rect x="40" y="35" width="140" height="50" rx="6" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="110" y="65" fill="#e6edf3" font-size="8" text-anchor="middle" font-family="sans-serif">checkout() -- 0 network hops</text>

  <text x="330" y="20" fill="#8b949e" font-size="11" text-anchor="middle" font-family="sans-serif">Microservices</text>
  <rect x="250" y="35" width="55" height="45" rx="5" fill="#1c2430" stroke="#79c0ff"/>
  <text x="277" y="60" fill="#e6edf3" font-size="7" text-anchor="middle" font-family="sans-serif">Cart</text>
  <rect x="320" y="35" width="55" height="45" rx="5" fill="#1c2430" stroke="#79c0ff"/>
  <text x="347" y="60" fill="#e6edf3" font-size="7" text-anchor="middle" font-family="sans-serif">Inventory</text>
  <rect x="390" y="35" width="55" height="45" rx="5" fill="#1c2430" stroke="#79c0ff"/>
  <text x="417" y="60" fill="#e6edf3" font-size="7" text-anchor="middle" font-family="sans-serif">Ship</text>
  <text x="347" y="98" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">2 network hops</text>

  <text x="560" y="20" fill="#8b949e" font-size="11" text-anchor="middle" font-family="sans-serif">Nanoservices</text>
  <g fill="#1c2430" stroke="#f0883e">
    <rect x="490" y="35" width="30" height="30" rx="4"/>
    <rect x="525" y="35" width="30" height="30" rx="4"/>
    <rect x="560" y="35" width="30" height="30" rx="4"/>
    <rect x="595" y="35" width="30" height="30" rx="4"/>
    <rect x="490" y="70" width="30" height="30" rx="4"/>
    <rect x="525" y="70" width="30" height="30" rx="4"/>
  </g>
  <text x="560" y="115" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">6+ network hops for one operation</text>
</svg>

The same business operation costs zero, a couple, or many network hops depending on how finely it's split.

## 5. Runnable example

Scenario: a checkout operation, first as one macroservice call, then split into a reasonable microservice granularity, then split so finely (nanoservices) that the overhead becomes visible and measurable.

### Level 1 — Basic

```java
// File: MacroserviceCheckout.java -- ONE process, ZERO internal network calls
public class MacroserviceCheckout {
    static int networkCallCount = 0; // tracked for comparison across levels

    static String checkout(String item) {
        // everything happens as plain, in-process method calls -- no network hop counted
        boolean reserved = true; // reserve stock
        boolean shipped = true;  // schedule shipping
        boolean billed = true;   // charge payment
        return "checkout complete for " + item + " (network calls: " + networkCallCount + ")";
    }

    public static void main(String[] args) {
        System.out.println(checkout("widget"));
    }
}
```

**How to run:** `javac MacroserviceCheckout.java && java MacroserviceCheckout` (JDK 17+).

Expected output:
```
checkout complete for widget (network calls: 0)
```

The entire checkout operation runs as plain method calls within one process. Coarse granularity like this minimizes network overhead, at the cost of coupling every concern (inventory, shipping, billing) into one deployable unit.

### Level 2 — Intermediate

```java
// File: MicroserviceCheckout.java -- split into THREE focused services, a
// reasonable microservice granularity, each call counted as a network hop.
public class MicroserviceCheckout {
    static int networkCallCount = 0;

    static boolean callInventoryService(String item) { networkCallCount++; return true; }
    static boolean callShippingService(String item) { networkCallCount++; return true; }
    static boolean callPaymentService(String item) { networkCallCount++; return true; }

    static String checkout(String item) {
        boolean reserved = callInventoryService(item);
        boolean shipped = callShippingService(item);
        boolean billed = callPaymentService(item);
        return "checkout complete for " + item + " (network calls: " + networkCallCount + ")";
    }

    public static void main(String[] args) {
        System.out.println(checkout("widget"));
    }
}
```

**How to run:** `javac MicroserviceCheckout.java && java MicroserviceCheckout` (JDK 17+).

Expected output:
```
checkout complete for widget (network calls: 3)
```

Three well-chosen boundaries — inventory, shipping, payment — each genuinely independent capabilities worth their own deploy and scale story. Three network hops is a reasonable cost for the independent-deployability benefit gained.

### Level 3 — Advanced

```java
// File: NanoserviceCheckout.java -- split SO finely that even trivial steps
// (validate item name, format currency) become separate network calls.
public class NanoserviceCheckout {
    static int networkCallCount = 0;
    static long simulatedLatencyMs = 0;
    static final long PER_CALL_LATENCY_MS = 15; // a realistic per-hop network latency

    static boolean call(String serviceName) {
        networkCallCount++;
        simulatedLatencyMs += PER_CALL_LATENCY_MS;
        return true;
    }

    static String checkout(String item) {
        call("ValidateItemNameService");     // nano: validating a string is NOT worth its own service
        call("CheckInventoryCountService");
        call("DecrementInventoryService");   // nano: split from the check above for no clear reason
        call("FormatShippingAddressService"); // nano: pure string formatting
        call("ScheduleShippingService");
        call("CalculateTaxService");
        call("ChargePaymentService");
        call("FormatCurrencyService");        // nano: pure formatting again
        call("SendReceiptService");
        return "checkout complete for " + item + " (network calls: " + networkCallCount + ", added latency: " + simulatedLatencyMs + "ms)";
    }

    public static void main(String[] args) {
        System.out.println(checkout("widget"));
        System.out.println("compare: macroservice = 0 calls, 0ms; microservices = 3 calls, " + (3 * PER_CALL_LATENCY_MS) + "ms; nanoservices = " + networkCallCount + " calls, " + simulatedLatencyMs + "ms");
    }
}
```

**How to run:** `javac NanoserviceCheckout.java && java NanoserviceCheckout` (JDK 17+).

Expected output:
```
checkout complete for widget (network calls: 9, added latency: 135ms)
compare: macroservice = 0 calls, 0ms; microservices = 3 calls, 45ms; nanoservices = 9 calls, 135ms
```

The production-flavored cautionary case: several of these "services" — validating a string, formatting currency — are trivial operations that add nothing by being separate network-callable services, yet each one adds a real `15ms` of simulated latency and a new independent point of failure. Nine network calls for one checkout, versus three at a sensible microservice granularity, is exactly the kind of over-splitting that erodes microservices' benefits rather than amplifying them.

## 6. Walkthrough

1. `checkout("widget")` in `NanoserviceCheckout` calls `call(...)` nine separate times in sequence, once for each granular step of the operation.
2. Each `call` invocation increments `networkCallCount` by one and adds `PER_CALL_LATENCY_MS` (`15`) to `simulatedLatencyMs` — modeling the real, unavoidable cost every network hop adds, regardless of how trivial the work behind it is.
3. By the time `checkout` returns, `networkCallCount` is `9` and `simulatedLatencyMs` is `135` — a concrete, measurable cost for what used to be a handful of in-process operations in `MacroserviceCheckout`.
4. The comparison line explicitly recomputes what the microservice-granularity version's cost would have been (`3 * 15 = 45ms`) alongside the actual nanoservice-granularity result (`135ms`) — a threefold latency increase purely from splitting into finer-grained services, without any of those extra splits corresponding to a genuinely independent business capability or team.
5. This is the concrete argument against over-splitting: `ValidateItemNameService` and `FormatCurrencyService` don't need their own deploy pipeline, their own scaling story, or their own on-call rotation — bundling them into whichever service actually owns the surrounding logic would eliminate two network hops (30ms) with no loss of any genuine independent-deployability benefit.

```
Macroservice:    checkout() -----------------------------------> 0 hops,   0ms
Microservices:   Inventory -> Shipping -> Payment ---------------> 3 hops,  45ms
Nanoservices:    Validate -> Check -> Decrement -> Format -> ... -> 9 hops, 135ms
```

## 7. Gotchas & takeaways

> **Gotcha:** the cost of over-splitting isn't just latency — it's also nine separate things to deploy, monitor, version, and keep available, for functionality that provides no independent business value on its own. A `FormatCurrencyService` that's down doesn't represent an independently meaningful outage; it's just needless fragility bolted onto whatever it's formatting for.

- Service granularity ranges informally from nanoservices (too fine, often an anti-pattern) through microservices and miniservices to macroservices (coarse, closer to a monolith) — none of the boundaries are hard or universally agreed.
- Every additional split adds a real, measurable cost: another network hop's latency, another independently deployed process, another point of failure.
- Split a boundary out into its own service only when it carries genuine, independent business value — its own reason to scale, deploy, or be owned separately — not merely because "smaller services" sounds like a universal improvement.
- When evaluating an existing system's granularity, count the network hops a core business operation actually requires — a surprisingly high number is a concrete signal that some of those splits should be reconsidered.

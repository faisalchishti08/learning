---
card: java
gi: 348
slug: exception-chaining-constructors
title: Exception chaining constructors
---

## 1. What it is

`Throwable` (the superclass of all exceptions and errors) defines four standard constructors: no-argument, message-only, message-plus-cause, and cause-only. When you write a custom exception class, providing all four — each simply calling the matching `super(...)` constructor — is what lets *your* exception type participate fully in exception chaining, both as something that can wrap an underlying cause and as something that can itself be thrown standalone with just a message.

```java
public class ExceptionConstructorDemo {
    static class OrderException extends RuntimeException {
        public OrderException() { super(); }
        public OrderException(String message) { super(message); }
        public OrderException(String message, Throwable cause) { super(message, cause); }
        public OrderException(Throwable cause) { super(cause); }
    }

    public static void main(String[] args) {
        try {
            throw new OrderException("Order failed", new IllegalStateException("inventory locked"));
        } catch (OrderException e) {
            System.out.println(e.getMessage() + " caused by " + e.getCause());
        }
    }
}
```

Each of `OrderException`'s four constructors does nothing but forward its arguments to the matching `Throwable` constructor via `super(...)` — this is boilerplate, but it's boilerplate that makes the exception genuinely usable in every calling context: with a message, with a cause, with both, or with neither.

## 2. Why & when

A custom exception that only provides a message-only constructor forces every caller who needs to wrap an underlying cause to either lose that cause entirely, or fall back to a different, less meaningful exception type just to preserve it. Providing the full standard set of constructors means your custom exception type is never the reason a cause gets dropped.

- **Designing a custom exception hierarchy for an application or library** — providing all four standard constructors on each custom exception type ensures it composes correctly with chaining everywhere it's thrown.
- **Wrapping a lower-level exception at an API boundary** — a repository or service layer translating a technology-specific exception (`SQLException`, `IOException`) into a domain-specific one needs the message-plus-cause constructor specifically to preserve the original failure.
- **Rethrowing without a new message** — sometimes you want to change an exception's *type* without adding new message text; the cause-only constructor covers that case, typically producing a message derived from the cause's own `toString()`.

Skipping the message-plus-cause constructor is the single most damaging omission — it's the one used by nearly all real-world exception-translation code, and without it, callers wrapping a cause either can't use your custom exception type at all, or have to work around the gap in some other, less clean way.

## 3. Core concept

```java
public class ExceptionConstructorCore {
    static class ConfigException extends Exception { // checked, unlike the earlier RuntimeException example
        public ConfigException(String message) { super(message); }
        public ConfigException(String message, Throwable cause) { super(message, cause); }
    }

    public static void main(String[] args) {
        try {
            loadConfig();
        } catch (ConfigException e) {
            System.out.println("Message: " + e.getMessage());
            System.out.println("Cause: " + e.getCause());
        }
    }

    static void loadConfig() throws ConfigException {
        try {
            throw new NumberFormatException("bad port value");
        } catch (NumberFormatException e) {
            throw new ConfigException("Could not load configuration", e); // uses the message+cause constructor
        }
    }
}
```

**How to run:** `java ExceptionConstructorCore.java`

`ConfigException` extends the checked `Exception` (rather than `RuntimeException`), so `loadConfig` must declare `throws ConfigException` — the constructor set is the same idea regardless of whether the custom exception is checked or unchecked.

## 4. Diagram

<svg viewBox="0 0 620 160" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="a custom exception class provides four constructors, each forwarding to the matching Throwable constructor via super, covering every combination of message and cause">
  <rect x="8" y="8" width="604" height="144" rx="8" fill="#0d1117"/>
  <text x="20" y="30" fill="#e6edf3" font-size="10">CustomException()                      -&gt; super()</text>
  <text x="20" y="55" fill="#e6edf3" font-size="10">CustomException(String message)         -&gt; super(message)</text>
  <text x="20" y="80" fill="#6db33f" font-size="10">CustomException(String message, Throwable cause) -&gt; super(message, cause)   ← most used for chaining</text>
  <text x="20" y="105" fill="#e6edf3" font-size="10">CustomException(Throwable cause)        -&gt; super(cause)</text>
  <text x="20" y="135" fill="#8b949e" font-size="9">Every constructor simply forwards to the matching Throwable constructor.</text>
</svg>

## 5. Runnable example

Scenario: a small payment-processing exception hierarchy, evolved from a single custom exception with only a message constructor, into one with the full standard constructor set, into a production-style hierarchy with a common base exception and specific subtypes that all correctly support chaining.

### Level 1 — Basic

```java
public class PaymentExceptionBasic {
    static class PaymentException extends RuntimeException {
        public PaymentException(String message) { super(message); } // only ONE constructor
    }

    public static void main(String[] args) {
        try {
            processPayment();
        } catch (PaymentException e) {
            System.out.println("Failed: " + e.getMessage() + ", cause: " + e.getCause());
        }
    }

    static void processPayment() {
        try {
            throw new IllegalStateException("gateway timeout");
        } catch (IllegalStateException original) {
            // Forced to drop the original cause -- PaymentException has no constructor that accepts one!
            throw new PaymentException("Payment failed: " + original.getMessage());
        }
    }
}
```

**How to run:** `java PaymentExceptionBasic.java`

Because `PaymentException` only has a message constructor, the real `IllegalStateException` cause can only be smuggled into the message text as a string — `e.getCause()` prints `null`, and any code trying to programmatically inspect the actual cause (its type, its own stack trace) has no way to do so.

### Level 2 — Intermediate

```java
public class PaymentExceptionIntermediate {
    static class PaymentException extends RuntimeException {
        public PaymentException(String message) { super(message); }
        public PaymentException(String message, Throwable cause) { super(message, cause); } // added
    }

    public static void main(String[] args) {
        try {
            processPayment();
        } catch (PaymentException e) {
            System.out.println("Failed: " + e.getMessage());
            System.out.println("Cause: " + e.getCause());
        }
    }

    static void processPayment() {
        try {
            throw new IllegalStateException("gateway timeout");
        } catch (IllegalStateException original) {
            throw new PaymentException("Payment failed", original); // cause properly preserved now
        }
    }
}
```

**How to run:** `java PaymentExceptionIntermediate.java`

Adding the message-plus-cause constructor lets `processPayment` preserve the real `IllegalStateException` as `PaymentException`'s cause — `e.getCause()` now returns the actual original exception object, not just a string fragment embedded in a message.

### Level 3 — Advanced

```java
public class PaymentExceptionAdvanced {
    static class PaymentException extends RuntimeException {
        public PaymentException() { super(); }
        public PaymentException(String message) { super(message); }
        public PaymentException(String message, Throwable cause) { super(message, cause); }
        public PaymentException(Throwable cause) { super(cause); }
    }

    static class GatewayTimeoutException extends PaymentException {
        public GatewayTimeoutException(String message, Throwable cause) { super(message, cause); }
    }

    static class InsufficientFundsException extends PaymentException {
        public InsufficientFundsException(String message) { super(message); }
    }

    public static void main(String[] args) {
        attemptPayment(true);
        attemptPayment(false);
    }

    static void attemptPayment(boolean simulateTimeout) {
        try {
            processPayment(simulateTimeout);
        } catch (PaymentException e) {
            System.out.println(e.getClass().getSimpleName() + ": " + e.getMessage()
                    + (e.getCause() != null ? " (cause: " + e.getCause() + ")" : " (no cause)"));
        }
    }

    static void processPayment(boolean simulateTimeout) {
        if (simulateTimeout) {
            try {
                throw new IllegalStateException("gateway did not respond in time");
            } catch (IllegalStateException original) {
                throw new GatewayTimeoutException("Payment gateway timed out", original);
            }
        } else {
            throw new InsufficientFundsException("Account balance too low for this transaction");
        }
    }
}
```

**How to run:** `java PaymentExceptionAdvanced.java`

`GatewayTimeoutException` and `InsufficientFundsException` both extend the fully-constructed `PaymentException` base class — one genuinely wraps a lower-level cause (a real timeout exception), the other represents a business-rule failure with no underlying technical cause at all — and because the base class provides the complete standard constructor set, each subclass only needs to expose the specific constructor forms that make sense for how it's actually used.

## 6. Walkthrough

Execution starts in `main`, which calls `attemptPayment(true)` first.

Inside `attemptPayment`, `processPayment(true)` runs: since `simulateTimeout` is `true`, it throws `IllegalStateException("gateway did not respond in time")` and immediately catches it in its own `try/catch`, then throws `new GatewayTimeoutException("Payment gateway timed out", original)`. This calls `GatewayTimeoutException`'s own constructor, which calls `super("Payment gateway timed out", original)` — that's `PaymentException`'s message-plus-cause constructor, which in turn calls `super("Payment gateway timed out", original)` on `RuntimeException`, ultimately reaching `Throwable`'s own message-plus-cause constructor, which stores both fields.

Back in `attemptPayment`'s `catch (PaymentException e)` block — which catches `GatewayTimeoutException` too, since it's a subclass — `e.getClass().getSimpleName()` reports the *actual* runtime type, `"GatewayTimeoutException"`, even though the `catch` clause is typed as the more general `PaymentException`. `e.getCause()` returns the original `IllegalStateException`, which is not `null`, so the method prints `GatewayTimeoutException: Payment gateway timed out (cause: java.lang.IllegalStateException: gateway did not respond in time)`.

`main` then calls `attemptPayment(false)`. This time, `processPayment(false)` directly throws `new InsufficientFundsException("Account balance too low for this transaction")` — no `try/catch` wraps anything here, since this failure isn't a translation of some lower-level technical exception; it's a standalone business-rule violation. `InsufficientFundsException`'s constructor calls `super(message)`, `PaymentException`'s message-only constructor, which calls `Throwable`'s message-only constructor — leaving `cause` as `null`.

Back in `attemptPayment`, `e.getCause()` is `null` this time, so the conditional expression selects `" (no cause)"`, and the method prints `InsufficientFundsException: Account balance too low for this transaction (no cause)`.

<svg viewBox="0 0 640 180" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="two different subclasses use different constructor forms depending on whether they wrap a real underlying cause or represent a standalone business failure">
  <rect x="8" y="8" width="624" height="164" rx="8" fill="#0d1117"/>
  <text x="20" y="30" fill="#79c0ff" font-size="10">attemptPayment(true): IllegalStateException caught -&gt; GatewayTimeoutException(message, original)</text>
  <text x="20" y="52" fill="#79c0ff" font-size="10">  chain: GatewayTimeoutException -&gt; super(msg,cause) -&gt; PaymentException -&gt; super(msg,cause) -&gt; Throwable</text>
  <text x="20" y="74" fill="#6db33f" font-size="10">  caught as PaymentException, getClass() reports GatewayTimeoutException, getCause() = IllegalStateException</text>
  <text x="20" y="107" fill="#f85149" font-size="10">attemptPayment(false): InsufficientFundsException(message) thrown directly, no wrapped cause</text>
  <text x="20" y="129" fill="#f85149" font-size="10">  chain: InsufficientFundsException -&gt; super(msg) -&gt; PaymentException -&gt; super(msg) -&gt; Throwable, cause=null</text>
</svg>

## 7. Gotchas & takeaways

> Forgetting to define the message-plus-cause constructor on a custom exception class is the most common exception-design mistake — it forces every future caller who needs to translate a lower-level exception into yours to either lose the original cause entirely or avoid using your exception type for that purpose.

- Provide all four standard `Throwable` constructor forms (no-arg, message, message+cause, cause) on custom exception classes so they compose correctly with chaining in every situation.
- Each custom constructor should do nothing but forward to the matching `super(...)` call — there's no need (and no benefit) to reimplement what `Throwable` already provides.
- A subclass only needs to expose the specific constructor signatures that make sense for how it's actually thrown — a business-rule exception with no technical cause may only need a message constructor, while a wrapping exception needs the message+cause form.
- `catch (BaseExceptionType e)` catches every subtype too; `e.getClass()` still reports the actual runtime type of whichever subclass was thrown, which is useful for logging or dispatch logic.
- Whether a custom exception extends `RuntimeException` (unchecked) or `Exception` (checked) is a separate design decision from constructor design — both need the same full set of chaining-friendly constructors.

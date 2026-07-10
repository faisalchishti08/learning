---
card: java
gi: 1030
slug: mockito-mock-when-verify
title: "Mockito (mock/when/verify)"
---

## 1. What it is

Mockito is a mocking framework that creates fake implementations of an interface (or class) at runtime — a **mock** — whose method behavior you program explicitly with `when(...).thenReturn(...)`, and whose *interactions* (which methods were called, how many times, with what arguments) you can check afterward with `verify(...)`. It's the practical tool that makes [dependency injection](1014-dependency-injection.md)'s testability payoff concrete: instead of hand-writing a fake implementation class for every interface you want to test against, Mockito generates one on the fly, and lets you script its behavior per test.

## 2. Why & when

Testing a class that depends on a slow, expensive, or hard-to-set-up collaborator (a real payment gateway, a real email service, a real database) either requires that collaborator to genuinely be available during every test run, or requires hand-writing a fake implementation class for every interface under test — both costly. Mockito's `mock(SomeInterface.class)` generates a working fake implementation of any interface instantly, with every method initially doing nothing (returning `null` or a default value); `when(mock.someMethod(args)).thenReturn(value)` then scripts exactly what that mock should return for specific arguments. `verify(mock).someMethod(args)` goes a step further: it doesn't just provide fake data, it *checks* that your code under test actually called the collaborator the way you expected — critical for testing that a class correctly delegates to (or correctly avoids calling) a collaborator, especially for `void` methods with side effects that can't be checked via a return value at all.

Reach for a Mockito mock when a unit test needs to isolate the class under test from a real, slow, or side-effect-having collaborator, and you need to control what that collaborator returns for specific inputs. Reach for `verify` specifically when the *fact that a method was called* (or called a specific number of times, or never called) is itself the behavior being tested — not just what value it returned.

## 3. Core concept

```java
import org.mockito.Mockito;
import static org.mockito.Mockito.*;
import static org.junit.jupiter.api.Assertions.assertEquals;

interface PaymentGateway { boolean charge(double amount); }

class OrderService {
    private final PaymentGateway gateway;
    OrderService(PaymentGateway gateway) { this.gateway = gateway; }
    boolean placeOrder(double amount) { return gateway.charge(amount); }
}

// In a test:
PaymentGateway mockGateway = mock(PaymentGateway.class);       // create a fake implementation
when(mockGateway.charge(19.99)).thenReturn(true);               // script its behavior for a specific input

OrderService service = new OrderService(mockGateway);
boolean result = service.placeOrder(19.99);

assertEquals(true, result);                                     // check the RESULT
verify(mockGateway).charge(19.99);                               // check the INTERACTION actually happened
```

## 4. Diagram

<svg viewBox="0 0 640 190" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="A test scripting a mock PaymentGateway with when-thenReturn, injecting it into OrderService, then verifying afterward that charge was actually called with the expected argument">
  <rect x="30" y="20" width="180" height="34" rx="6" fill="#1c2430" stroke="#79c0ff"/>
  <text x="120" y="41" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">when(mock.charge(19.99))</text>
  <rect x="240" y="20" width="180" height="34" rx="6" fill="#1c2430" stroke="#79c0ff"/>
  <text x="330" y="41" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">.thenReturn(true)</text>

  <rect x="30" y="80" width="230" height="40" rx="8" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="145" y="105" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">OrderService.placeOrder()</text>

  <rect x="30" y="145" width="230" height="34" rx="6" fill="#1c2430" stroke="#f0883e"/>
  <text x="145" y="166" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">verify(mock).charge(19.99)</text>

  <line x1="145" y1="54" x2="145" y2="80" stroke="#79c0ff" marker-end="url(#a)"/>
  <line x1="145" y1="120" x2="145" y2="145" stroke="#f0883e" marker-end="url(#a)"/>
  <defs><marker id="a" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#8b949e"/></marker></defs>
</svg>

The mock is scripted before the test runs; `verify` afterward confirms the code under test actually called it as expected.

## 5. Runnable example

Scenario: testing an `OrderService` that depends on a `PaymentGateway`, evolving from a hand-written fake implementation into Mockito's `mock`/`when`/`verify` used to control and check behavior precisely.

### Level 1 — Basic

```java
// File: src/test/java/OrderServiceBasicTest.java
import org.junit.jupiter.api.Test;
import static org.junit.jupiter.api.Assertions.assertTrue;

interface PaymentGateway { boolean charge(double amount); }

class OrderService {
    private final PaymentGateway gateway;
    OrderService(PaymentGateway gateway) { this.gateway = gateway; }
    boolean placeOrder(double amount) { return gateway.charge(amount); }
}

// A hand-written fake -- works, but every new test scenario means writing
// (or modifying) this fake class directly.
class AlwaysSucceedsGateway implements PaymentGateway {
    public boolean charge(double amount) { return true; }
}

class OrderServiceBasicTest {
    @Test
    void placingOrderSucceedsWhenPaymentSucceeds() {
        OrderService service = new OrderService(new AlwaysSucceedsGateway());
        assertTrue(service.placeOrder(19.99));
    }
}
```

**How to run:** place in a Maven project's test source root, then run `mvn test`.

Expected output:
```
[INFO] Tests run: 1, Failures: 0, Errors: 0, Skipped: 0
```

`AlwaysSucceedsGateway` is a hand-written class dedicated purely to testing — a second test scenario (payment failing, or charging a specific amount) needs either a second hand-written fake class or awkward extra configuration added to this one.

### Level 2 — Intermediate

```java
// File: src/test/java/OrderServiceIntermediateTest.java
import org.junit.jupiter.api.Test;
import static org.junit.jupiter.api.Assertions.assertFalse;
import static org.junit.jupiter.api.Assertions.assertTrue;
import static org.mockito.Mockito.mock;
import static org.mockito.Mockito.when;

interface PaymentGateway { boolean charge(double amount); }

class OrderService {
    private final PaymentGateway gateway;
    OrderService(PaymentGateway gateway) { this.gateway = gateway; }
    boolean placeOrder(double amount) { return gateway.charge(amount); }
}

class OrderServiceIntermediateTest {
    @Test
    void placingOrderSucceedsWhenPaymentSucceeds() {
        PaymentGateway mockGateway = mock(PaymentGateway.class);
        when(mockGateway.charge(19.99)).thenReturn(true);

        OrderService service = new OrderService(mockGateway);
        assertTrue(service.placeOrder(19.99));
    }

    @Test
    void placingOrderFailsWhenPaymentFails() {
        PaymentGateway mockGateway = mock(PaymentGateway.class);
        when(mockGateway.charge(19.99)).thenReturn(false); // a DIFFERENT scripted behavior, no new class needed

        OrderService service = new OrderService(mockGateway);
        assertFalse(service.placeOrder(19.99));
    }
}
```

**How to run:** place in a Maven project's test source root (with `mockito-core` and `mockito-junit-jupiter` on the test classpath — see [Maven dependencies & scopes](1036-maven-dependencies-scopes.md)), then run `mvn test`.

Expected output:
```
[INFO] Tests run: 2, Failures: 0, Errors: 0, Skipped: 0
```

The real-world concern added: both a success case and a failure case are tested by scripting the *same* mocked interface differently per test — no new hand-written class needed for the second scenario, just a different `when(...).thenReturn(...)` line.

### Level 3 — Advanced

```java
// File: src/test/java/OrderServiceAdvancedTest.java
import org.junit.jupiter.api.Test;
import static org.junit.jupiter.api.Assertions.*;
import static org.mockito.Mockito.*;

interface PaymentGateway { boolean charge(double amount); }
interface NotificationService { void notifyCustomer(String message); }

class OrderService {
    private final PaymentGateway gateway;
    private final NotificationService notifications;
    OrderService(PaymentGateway gateway, NotificationService notifications) {
        this.gateway = gateway;
        this.notifications = notifications;
    }

    boolean placeOrder(double amount) {
        boolean success = gateway.charge(amount);
        if (success) {
            notifications.notifyCustomer("Order confirmed for $" + amount);
        }
        return success;
    }
}

class OrderServiceAdvancedTest {
    @Test
    void successfulOrderNotifiesCustomer() {
        PaymentGateway mockGateway = mock(PaymentGateway.class);
        NotificationService mockNotifications = mock(NotificationService.class);
        when(mockGateway.charge(19.99)).thenReturn(true);

        OrderService service = new OrderService(mockGateway, mockNotifications);
        boolean result = service.placeOrder(19.99);

        assertTrue(result);
        // verify: checks the ACTUAL INTERACTION happened -- essential here since
        // notifyCustomer is a void method with no return value to assert on directly.
        verify(mockNotifications).notifyCustomer("Order confirmed for $19.99");
    }

    @Test
    void failedOrderNeverNotifiesCustomer() {
        PaymentGateway mockGateway = mock(PaymentGateway.class);
        NotificationService mockNotifications = mock(NotificationService.class);
        when(mockGateway.charge(19.99)).thenReturn(false);

        OrderService service = new OrderService(mockGateway, mockNotifications);
        boolean result = service.placeOrder(19.99);

        assertFalse(result);
        // verify(..., never()): confirms notifyCustomer was NEVER called on failure --
        // catching a class of bug (notifying on failure by mistake) a plain
        // return-value assertion could never detect.
        verify(mockNotifications, never()).notifyCustomer(anyString());
    }
}
```

**How to run:** place in a Maven project's test source root, then run `mvn test -Dtest=OrderServiceAdvancedTest`.

Expected output:
```
[INFO] Tests run: 2, Failures: 0, Errors: 0, Skipped: 0
```

The production-flavored hard case: `notifyCustomer` is a `void` method — there's no return value at all to assert on directly — so `verify(mockNotifications).notifyCustomer(...)` and `verify(mockNotifications, never()).notifyCustomer(...)` are the *only* way to test that this side-effecting interaction happened (or correctly didn't happen) in each scenario.

## 6. Walkthrough

Tracing `failedOrderNeverNotifiesCustomer` in `OrderServiceAdvancedTest`:

1. `mock(PaymentGateway.class)` and `mock(NotificationService.class)` create two fake implementations — every method on both currently does nothing and returns a default value (`false` for a `boolean` method, in this case, until scripted otherwise).
2. `when(mockGateway.charge(19.99)).thenReturn(false)` scripts the mock: any call to `charge` with the argument `19.99` will return `false`.
3. `service.placeOrder(19.99)` runs `OrderService.placeOrder`: `gateway.charge(19.99)` dispatches to the mocked `PaymentGateway`, matching the scripted call and returning `false`, assigned to `success`.
4. Since `success` is `false`, the `if (success)` block — which would call `notifications.notifyCustomer(...)` — is skipped entirely. `placeOrder` returns `false` directly.
5. `assertFalse(result)` confirms the return value is `false`, as expected.
6. `verify(mockNotifications, never()).notifyCustomer(anyString())` asks Mockito to check its internal record of every call made to `mockNotifications` during this test — since `notifyCustomer` was never actually invoked (confirmed by step 4's skipped `if` block), this verification passes; had `OrderService`'s code contained a bug that called `notifyCustomer` regardless of `success`, this exact `verify` call would fail, loudly catching a bug that a return-value-only test could never have detected.

## 7. Gotchas & takeaways

> **Gotcha:** an *unscripted* mock method doesn't throw an error when called — it silently returns a default value (`null` for objects, `false` for `boolean`, `0` for numeric types) — which means a test that forgets to `when(...)` a method its code under test actually depends on can pass or fail for the wrong reason, with no clear signal that the mock was never configured for that call in the first place.

- `mock(SomeInterface.class)` creates a fake implementation instantly; `when(mock.method(args)).thenReturn(value)` scripts its behavior for specific arguments.
- `verify(mock).method(args)` checks that a specific interaction actually happened — essential for testing `void` methods and side effects that have no return value to assert on directly.
- `verify(mock, never()).method(args)` confirms an interaction did *not* happen — critical for catching bugs where code does something it shouldn't under certain conditions.
- An unscripted mock method silently returns a harmless default rather than failing loudly — be deliberate about which methods actually need `when(...)` configuration for a given test.
- Mocks isolate the class under test from real, slow, or side-effect-having collaborators — see [dependency injection](1014-dependency-injection.md) for why constructor-injected dependencies are what makes substituting a mock possible in the first place.
- See [test doubles (stub/mock/spy/fake)](1031-test-doubles-stub-mock-spy-fake.md) for how Mockito's "mock" relates to (and differs from) the broader vocabulary of stubs, spies, and fakes used in testing generally.

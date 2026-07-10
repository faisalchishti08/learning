---
card: spring-framework
gi: 411
slug: unit-testing-with-mock-objects
title: "Unit testing with mock objects"
---

## 1. What it is

Unit testing with mock objects means replacing a class's real dependencies with fake stand-ins whose behavior you control precisely, so you can test the class's own logic in isolation. Spring itself doesn't provide a mocking library — the ecosystem standard is Mockito — but Spring's design (constructor injection against interfaces) is exactly what makes classes easy to mock in the first place.

```java
@ExtendWith(MockitoExtension.class)
class OrderServiceTest {
    @Mock OrderRepository repository;
    @InjectMocks OrderService service;

    @Test
    void cancelsAPendingOrder() {
        when(repository.findById(1L)).thenReturn(Optional.of(new Order(1, "PENDING")));
        service.cancel(1L);
        verify(repository).save(argThat(o -> o.status().equals("CANCELLED")));
    }
}
```

## 2. Why & when

A `@Service` in a real application typically depends on a `@Repository`, another `@Service`, or an external client — testing it against the *real* versions of those means also standing up a database, a network connection, or another service's behavior, all just to verify a few lines of coordination logic. Mocks remove that overhead: you tell the mock exactly what to return for a given call, and you verify exactly what your class under test called on it, without any of those dependencies actually doing real work.

Use mocks when:

- The class under test's logic is what you want to verify — branching, calculations, orchestration — not the correctness of its dependencies themselves.
- A dependency is slow, external, or has side effects you don't want in a fast test suite (a real HTTP call, a real database write, a real email send).
- You want to test how your code handles a dependency's *failure* modes (a repository throwing, a client timing out) — trivial to simulate with a mock, often awkward or impossible to reliably reproduce with the real thing.

Don't mock everything reflexively — mocking a value object or a class with no meaningful behavior of its own (like a simple record) adds test complexity for no benefit; just construct a real instance.

## 3. Core concept

```
   @Mock OrderRepository repository       <- fake, behavior you control
          |
          | when(repository.findById(1L)).thenReturn(Optional.of(order))
          v
   OrderService service = new OrderService(repository)   <- real class under test
          |
          | service.cancel(1L)  <- calls into repository.findById(1L) internally
          v
   repository returns YOUR configured value, not a real database lookup
          |
          v
   verify(repository).save(...)   <- assert what the class under test DID, not what it returned
```

Two distinct kinds of assertions come out of a mock-based test: `when(...).thenReturn(...)` configures behavior *before* the call, and `verify(...)` checks what interactions actually happened *after* the call — mocks let you assert on both the class's outputs and its side-effecting calls to its dependencies.

## 4. Diagram

<svg viewBox="0 0 640 190" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Test configures a mock, calls the real class under test, then verifies the mock was called correctly">
  <rect x="10" y="20" width="180" height="44" rx="8" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="100" y="47" fill="#e6edf3" font-size="11" text-anchor="middle" font-family="sans-serif">1. when(mock...).thenReturn</text>

  <rect x="230" y="20" width="180" height="44" rx="8" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="320" y="47" fill="#e6edf3" font-size="11" text-anchor="middle" font-family="sans-serif">2. service.cancel(1L)</text>

  <rect x="450" y="20" width="180" height="44" rx="8" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="540" y="47" fill="#e6edf3" font-size="11" text-anchor="middle" font-family="sans-serif">3. verify(mock).save(...)</text>

  <line x1="190" y1="42" x2="225" y2="42" stroke="#8b949e" stroke-width="2" marker-end="url(#a)"/>
  <line x1="410" y1="42" x2="445" y2="42" stroke="#8b949e" stroke-width="2" marker-end="url(#a)"/>

  <text x="320" y="110" fill="#8b949e" font-size="11" text-anchor="middle" font-family="sans-serif">real OrderService, fake OrderRepository</text>
  <defs><marker id="a" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#8b949e"/></marker></defs>
</svg>

Arrange (configure the mock), Act (call the real object), Assert (verify the mock's interactions) — the classic three-phase test structure applied to mocking.

## 5. Runnable example

### Level 1 — Basic

A minimal mock: stub a return value and verify a method was called, using Mockito directly without any test framework annotations, to see the raw API before adding JUnit integration.

```java
import org.mockito.Mockito;

import java.util.Optional;

public class MockingBasic {

    record Order(long id, String status) {}

    interface OrderRepository {
        Optional<Order> findById(long id);
        void save(Order order);
    }

    static class OrderService {
        private final OrderRepository repository;
        OrderService(OrderRepository repository) { this.repository = repository; }

        void cancel(long id) {
            Order order = repository.findById(id).orElseThrow();
            repository.save(new Order(order.id(), "CANCELLED"));
        }
    }

    public static void main(String[] args) {
        OrderRepository mockRepo = Mockito.mock(OrderRepository.class);
        Mockito.when(mockRepo.findById(1L)).thenReturn(Optional.of(new Order(1, "PENDING")));

        new OrderService(mockRepo).cancel(1L);

        Mockito.verify(mockRepo).save(new Order(1, "CANCELLED"));
        System.out.println("Verified: save() called with CANCELLED order -- PASS");
    }
}
```

How to run: add `org.mockito:mockito-core` to the classpath, then `java MockingBasic.java`.

`Mockito.mock(OrderRepository.class)` creates a dynamic proxy implementing the interface with no real behavior by default (every method returns `null`/empty/zero unless stubbed). `when(...).thenReturn(...)` configures exactly one call's response; `verify(...)` asserts, after the fact, that `save` was called with a specific argument — if `cancel` had a bug and never called `save`, or called it with the wrong status, this `verify` call would throw and fail the test.

### Level 2 — Intermediate

Use argument matchers for flexible verification, stub different responses for different arguments, and verify a dependency was *never* called for a code path that shouldn't reach it — common real-world assertions beyond exact-value matching.

```java
import org.mockito.ArgumentMatchers;
import org.mockito.Mockito;

import java.util.Optional;

public class MockingIntermediate {

    record Order(long id, double amount, String status) {}

    interface OrderRepository {
        Optional<Order> findById(long id);
        void save(Order order);
    }

    interface NotificationService {
        void notifyCancelled(long orderId);
    }

    static class OrderService {
        private final OrderRepository repository;
        private final NotificationService notifications;
        OrderService(OrderRepository repository, NotificationService notifications) {
            this.repository = repository;
            this.notifications = notifications;
        }

        void cancel(long id) {
            Order order = repository.findById(id)
                    .orElseThrow(() -> new IllegalArgumentException("not found"));
            if ("SHIPPED".equals(order.status())) {
                return; // silently refuse; no save, no notification
            }
            repository.save(new Order(order.id(), order.amount(), "CANCELLED"));
            notifications.notifyCancelled(id);
        }
    }

    public static void main(String[] args) {
        OrderRepository mockRepo = Mockito.mock(OrderRepository.class);
        NotificationService mockNotifications = Mockito.mock(NotificationService.class);
        OrderService service = new OrderService(mockRepo, mockNotifications);

        // Case 1: pending order — should cancel and notify.
        Mockito.when(mockRepo.findById(1L)).thenReturn(Optional.of(new Order(1, 50.0, "PENDING")));
        service.cancel(1L);
        Mockito.verify(mockRepo).save(ArgumentMatchers.argThat(o -> o.status().equals("CANCELLED")));
        Mockito.verify(mockNotifications).notifyCancelled(1L);
        System.out.println("Pending order: cancelled and notified -- PASS");

        // Case 2: shipped order — should NOT save or notify at all.
        Mockito.when(mockRepo.findById(2L)).thenReturn(Optional.of(new Order(2, 75.0, "SHIPPED")));
        service.cancel(2L);
        Mockito.verify(mockRepo, Mockito.never()).save(ArgumentMatchers.argThat(o -> o.id() == 2));
        Mockito.verify(mockNotifications, Mockito.never()).notifyCancelled(2L);
        System.out.println("Shipped order: correctly left untouched -- PASS");
    }
}
```

How to run: `java MockingIntermediate.java` (same classpath as Level 1).

`argThat(o -> o.status().equals("CANCELLED"))` verifies the *shape* of the saved argument rather than requiring an exact `equals` match, useful when you only care about one field changing. `Mockito.verify(mock, Mockito.never())` proves a negative — that a method was *not* called — which matters here because the shipped-order branch's correctness depends on `save`/`notifyCancelled` being skipped entirely, not just on what they'd be called with if they were.

### Level 3 — Advanced

Simulate a dependency throwing to test error-handling paths, and use an `ArgumentCaptor` to inspect the actual object passed to a mock in detail (beyond what a matcher predicate conveniently expresses) — both common needs once tests move past the happiest of paths.

```java
import org.mockito.ArgumentCaptor;
import org.mockito.Mockito;

import java.util.Optional;

public class MockingAdvanced {

    record Order(long id, double amount, String status) {}

    static class PaymentGatewayException extends RuntimeException {
        PaymentGatewayException(String message) { super(message); }
    }

    interface OrderRepository {
        Optional<Order> findById(long id);
        void save(Order order);
    }

    interface PaymentGateway {
        void refund(long orderId, double amount);
    }

    static class OrderService {
        private final OrderRepository repository;
        private final PaymentGateway paymentGateway;
        OrderService(OrderRepository repository, PaymentGateway paymentGateway) {
            this.repository = repository;
            this.paymentGateway = paymentGateway;
        }

        void cancel(long id) {
            Order order = repository.findById(id).orElseThrow();
            try {
                paymentGateway.refund(id, order.amount());
            } catch (PaymentGatewayException e) {
                // Save as CANCEL_PENDING instead of CANCELLED so a retry job can pick it up later.
                repository.save(new Order(order.id(), order.amount(), "CANCEL_PENDING"));
                throw e; // still surface the failure to the caller
            }
            repository.save(new Order(order.id(), order.amount(), "CANCELLED"));
        }
    }

    public static void main(String[] args) {
        OrderRepository mockRepo = Mockito.mock(OrderRepository.class);
        PaymentGateway mockGateway = Mockito.mock(PaymentGateway.class);
        OrderService service = new OrderService(mockRepo, mockGateway);

        Mockito.when(mockRepo.findById(1L)).thenReturn(Optional.of(new Order(1, 50.0, "PENDING")));
        Mockito.doThrow(new PaymentGatewayException("Gateway timeout"))
                .when(mockGateway).refund(1L, 50.0);

        try {
            service.cancel(1L);
            throw new AssertionError("Expected PaymentGatewayException to propagate");
        } catch (PaymentGatewayException e) {
            System.out.println("Correctly propagated: " + e.getMessage() + " -- PASS");
        }

        ArgumentCaptor<Order> captor = ArgumentCaptor.forClass(Order.class);
        Mockito.verify(mockRepo).save(captor.capture());
        Order saved = captor.getValue();

        System.out.println("Saved order status: " + saved.status());
        if (!"CANCEL_PENDING".equals(saved.status())) throw new AssertionError("Expected CANCEL_PENDING");
        System.out.println("Order correctly marked CANCEL_PENDING for retry -- PASS");
    }
}
```

How to run: `java MockingAdvanced.java` (same classpath as Level 1).

`Mockito.doThrow(...).when(mockGateway).refund(...)` configures the mock to throw instead of return, simulating a real payment gateway failure without needing one to actually be down. `ArgumentCaptor` captures the *actual* `Order` object passed to `save` so the test can inspect it field by field afterward — more flexible than a matcher predicate when you want to make several separate assertions about the captured value, or print it for debugging a failing test.

## 6. Walkthrough

Trace `MockingAdvanced.main`'s exercise of the failure path:

1. **Stub configuration.** `when(mockRepo.findById(1L)).thenReturn(...)` and `doThrow(...).when(mockGateway).refund(1L, 50.0)` set up the scenario: a real pending order exists, but the payment gateway will fail when asked to refund it.
2. **Call under test.** `service.cancel(1L)` runs: it fetches the order (via the stubbed `findById`), then calls `paymentGateway.refund(1L, 50.0)`.
3. **Mock throws.** Because `refund` was stubbed with `doThrow`, calling it doesn't run any real refund logic — it immediately throws `PaymentGatewayException("Gateway timeout")`, exactly as configured, at the exact point `cancel`'s code calls it.
4. **Catch block executes.** `cancel`'s `catch (PaymentGatewayException e)` block runs, calling `repository.save(new Order(1, 50.0, "CANCEL_PENDING"))` — a real method call against the mock `repository`, which (having no stubbed behavior for `save`, since it returns `void`) simply records that it was called with this argument and does nothing else.
5. **Re-throw.** The `catch` block re-throws `e`, propagating the exception out of `cancel` and out to `main`'s `try/catch`, which catches it and prints the success line — confirming the exception genuinely propagated rather than being silently swallowed.
6. **Captor inspection.** `ArgumentCaptor<Order> captor` + `verify(mockRepo).save(captor.capture())` retrieves the actual `Order` object that was passed to `save` during step 4 — `captor.getValue()` returns exactly that object, letting the test assert its `status()` field is `"CANCEL_PENDING"`, confirming the catch block's business logic (marking the order for a later retry rather than fully cancelling) executed correctly.

```
findById(1) -> stubbed -> Order(PENDING)
refund(1, 50.0) -> stubbed to throw -> PaymentGatewayException
   catch block: save(Order(CANCEL_PENDING)) -> mock records the call
   re-throw PaymentGatewayException
main: catches it, confirms propagation
ArgumentCaptor: inspects captured Order -> status == CANCEL_PENDING -> PASS
```

## 7. Gotchas & takeaways

> Gotcha: `verify(mock, never()).someMethod(...)` only proves a *specific* call (matching the given arguments) never happened — it does not prove the mock was never interacted with at all. A method called with different arguments than the ones checked would still pass a narrowly-scoped `never()` verification. Use `verifyNoInteractions(mock)` or `verifyNoMoreInteractions(mock)` when you need a genuinely blanket guarantee that nothing (or nothing beyond what's already been verified) happened on that mock.

- Mocking is most valuable for dependencies that are slow, external, or hard to put into a specific failure state reliably — use it to isolate and thoroughly test the coordinating class's own logic.
- `when(...).thenReturn(...)` configures behavior for query-style calls; `doThrow(...).when(...)` configures a method (especially a `void` one) to throw, simulating failure paths that are otherwise hard to trigger.
- `ArgumentCaptor` is the tool for inspecting exactly what was passed to a mock when a simple matcher predicate isn't expressive enough for the assertions you need to make.
- Don't over-mock: a mocked dependency verifies your code called it correctly, never that the dependency's real implementation is itself correct — pair mock-based unit tests with the integration tests covered in the rest of this section to close that gap.

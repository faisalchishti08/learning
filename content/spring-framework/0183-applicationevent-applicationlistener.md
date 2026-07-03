---
card: spring-framework
gi: 183
slug: applicationevent-applicationlistener
title: ApplicationEvent & ApplicationListener
---

## 1. What it is

Spring's **event system** is a publish/subscribe mechanism built into every `ApplicationContext`. Any bean can publish an event; any bean implementing `ApplicationListener<E>` receives it when the event is published.

```java
// Define an event
class UserRegisteredEvent extends ApplicationEvent {
    private final String username;
    UserRegisteredEvent(Object source, String username) {
        super(source); this.username = username;
    }
    public String getUsername() { return username; }
}

// Publish
applicationEventPublisher.publishEvent(new UserRegisteredEvent(this, "alice"));

// Listen
@Component
class WelcomeEmailSender implements ApplicationListener<UserRegisteredEvent> {
    @Override
    public void onApplicationEvent(UserRegisteredEvent event) {
        System.out.println("Send welcome email to " + event.getUsername());
    }
}
```

Events that don't extend `ApplicationEvent` are wrapped in `PayloadApplicationEvent` automatically since Spring 4.2.

## 2. Why & when

- **Decoupling** — the `UserService` that registers a user doesn't need to know about email sending, audit logging, or analytics. It just publishes an event; other beans react.
- **Single responsibility** — each listener handles one concern; adding new post-registration behaviour doesn't touch `UserService`.
- **Testability** — swap out or remove listeners in test contexts without modifying publishing code.
- **Synchronous by default** — unlike a message queue, the default event dispatch is synchronous: `publishEvent` blocks until all listeners return. This ensures all listeners run within the same transaction if one is active.
- **Use over direct calls** when: (a) multiple independent reactions to one trigger, (b) the publisher shouldn't know about its subscribers, (c) post-processing that may grow over time.
- **Avoid** for cross-process communication (use a message broker) or when you need guaranteed delivery / retry semantics (events are in-process and in-memory only).

## 3. Core concept

`ApplicationContext` extends `ApplicationEventPublisher`. When `publishEvent(event)` is called:

1. Spring iterates all `ApplicationListener<E>` beans where `E` is compatible with the event type.
2. Each listener's `onApplicationEvent(E)` is called in registration order on the **same thread** as the publisher.
3. If a listener throws an unchecked exception, it propagates back to the publisher and subsequent listeners do NOT run (synchronous behaviour).

**Event hierarchy:** listeners for a supertype receive all subtypes. An `ApplicationListener<ApplicationEvent>` receives every event in the context.

**POJO events (Spring 4.2+):** any object can be published; Spring wraps it in `PayloadApplicationEvent<T>`. Listeners can declare `ApplicationListener<PayloadApplicationEvent<MyPojo>>` or use `@EventListener` (next topic).

**Thread model:**
- Default: synchronous, same thread.
- Async: annotate listener method with `@Async` + configure `TaskExecutor` (covered in the `@EventListener` topic).

## 4. Diagram

<svg viewBox="0 0 700 190" xmlns="http://www.w3.org/2000/svg">
  <defs>
    <marker id="eva" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L6,3 L0,6 Z" fill="#6db33f"/></marker>
    <marker id="evb" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L6,3 L0,6 Z" fill="#79c0ff"/></marker>
  </defs>

  <!-- Publisher -->
  <rect x="5" y="70" width="160" height="50" rx="6" fill="#1c2430" stroke="#6db33f" stroke-width="2"/>
  <text x="85" y="89" fill="#6db33f" font-size="10" text-anchor="middle" font-family="sans-serif" font-weight="bold">Publisher</text>
  <text x="85" y="104" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">publishEvent(UserRegisteredEvent)</text>
  <text x="85" y="115" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">via ApplicationEventPublisher</text>

  <!-- ApplicationContext (router) -->
  <rect x="250" y="60" width="200" height="70" rx="6" fill="#6db33f" opacity="0.2" stroke="#6db33f" stroke-width="2"/>
  <text x="350" y="82" fill="#6db33f" font-size="10" text-anchor="middle" font-family="sans-serif" font-weight="bold">ApplicationContext</text>
  <text x="350" y="97" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">finds all listeners for event type</text>
  <text x="350" y="110" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">calls onApplicationEvent() in order</text>
  <text x="350" y="122" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">(same thread — synchronous)</text>

  <line x1="167" y1="95" x2="248" y2="95" stroke="#6db33f" stroke-width="2" marker-end="url(#eva)"/>

  <!-- Listeners -->
  <rect x="505" y="10" width="185" height="30" rx="4" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="597" y="29" fill="#79c0ff" font-size="9" text-anchor="middle" font-family="sans-serif">WelcomeEmailSender</text>
  <line x1="452" y1="82" x2="503" y2="25" stroke="#79c0ff" stroke-width="1.5" marker-end="url(#evb)"/>

  <rect x="505" y="55" width="185" height="30" rx="4" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="597" y="74" fill="#79c0ff" font-size="9" text-anchor="middle" font-family="sans-serif">AuditLogger</text>
  <line x1="452" y1="92" x2="503" y2="70" stroke="#79c0ff" stroke-width="1.5" marker-end="url(#evb)"/>

  <rect x="505" y="100" width="185" height="30" rx="4" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="597" y="119" fill="#79c0ff" font-size="9" text-anchor="middle" font-family="sans-serif">AnalyticsReporter</text>
  <line x1="452" y1="105" x2="503" y2="115" stroke="#79c0ff" stroke-width="1.5" marker-end="url(#evb)"/>

  <rect x="505" y="145" width="185" height="30" rx="4" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="597" y="164" fill="#79c0ff" font-size="9" text-anchor="middle" font-family="sans-serif">SlackNotifier</text>
  <line x1="452" y1="112" x2="503" y2="160" stroke="#79c0ff" stroke-width="1.5" marker-end="url(#evb)"/>

  <text x="350" y="155" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">publisher knows nothing about listeners</text>
  <text x="350" y="168" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">listeners can be added/removed without touching publisher</text>
</svg>

Publisher calls `publishEvent` once; the `ApplicationContext` fans out to all registered listeners. The publisher is completely decoupled from its listeners.

## 5. Runnable example

The scenario is a **user registration system** — one `UserService` publishes a registration event; multiple independent listeners react, growing in complexity.

### Level 1 — Basic

One event, one listener, minimal Spring context.

```java
// AppEventBasic.java
import org.springframework.context.*;
import org.springframework.context.annotation.*;
import org.springframework.stereotype.*;

// --- Event ---
class UserRegisteredEvent extends ApplicationEvent {
    private final String username;
    UserRegisteredEvent(Object source, String username) {
        super(source); this.username = username;
    }
    public String getUsername() { return username; }
}

// --- Publisher ---
@Service
class UserService implements ApplicationContextAware {
    private ApplicationEventPublisher publisher;

    @Override
    public void setApplicationContext(ApplicationContext ctx) {
        this.publisher = ctx;  // ApplicationContext is an ApplicationEventPublisher
    }

    public String register(String username) {
        System.out.println("[UserService] Registering: " + username);
        publisher.publishEvent(new UserRegisteredEvent(this, username));
        System.out.println("[UserService] Event published; registration complete");
        return "User " + username + " registered";
    }
}

// --- Listener ---
@Component
class WelcomeEmailListener implements ApplicationListener<UserRegisteredEvent> {
    @Override
    public void onApplicationEvent(UserRegisteredEvent event) {
        System.out.println("[WelcomeEmail] Sending welcome email to " + event.getUsername());
    }
}

@Configuration
@ComponentScan
class AppEventConfig { }

public class AppEventBasic {
    public static void main(String[] args) {
        var ctx = new AnnotationConfigApplicationContext(AppEventConfig.class);
        var svc = ctx.getBean(UserService.class);
        System.out.println(svc.register("alice"));
        System.out.println(svc.register("bob"));
        ctx.close();
    }
}
```

How to run: `java AppEventBasic.java`

`ApplicationContext` implements `ApplicationEventPublisher`, so injecting it (or acquiring via `ApplicationContextAware`) gives access to `publishEvent`. The listener `WelcomeEmailListener` runs synchronously on the same thread as `register()` — notice the output interleaves: `[UserService] Registering` → `[WelcomeEmail] Sending welcome email` → `[UserService] Event published`. The publisher doesn't know about `WelcomeEmailListener` at all.

### Level 2 — Intermediate

Multiple listeners for the same event; order control with `@Order`; event with more data.

```java
// AppEventIntermediate.java
import org.springframework.context.*;
import org.springframework.context.annotation.*;
import org.springframework.core.annotation.*;
import org.springframework.stereotype.*;

// --- Richer event ---
class UserRegisteredEvent extends ApplicationEvent {
    private final String username;
    private final String email;
    private final boolean vip;
    UserRegisteredEvent(Object src, String u, String e, boolean v) {
        super(src); username=u; email=e; vip=v;
    }
    public String getUsername() { return username; }
    public String getEmail()    { return email; }
    public boolean isVip()      { return vip; }
    public String toString()    { return username + " (VIP=" + vip + ")"; }
}

// --- Listeners with order ---
@Component @Order(1)
class AuditListener implements ApplicationListener<UserRegisteredEvent> {
    @Override
    public void onApplicationEvent(UserRegisteredEvent e) {
        System.out.println("[Audit #1] Logged: " + e);
    }
}

@Component @Order(2)
class WelcomeEmailListener implements ApplicationListener<UserRegisteredEvent> {
    @Override
    public void onApplicationEvent(UserRegisteredEvent e) {
        System.out.println("[WelcomeEmail #2] Sent to " + e.getEmail());
    }
}

@Component @Order(3)
class VipPromoListener implements ApplicationListener<UserRegisteredEvent> {
    @Override
    public void onApplicationEvent(UserRegisteredEvent e) {
        if (e.isVip()) System.out.println("[VipPromo #3] VIP promo sent to " + e.getUsername());
    }
}

// --- Publisher bean using @Autowired ---
@Service
class UserService2 {
    private final ApplicationEventPublisher pub;
    UserService2(ApplicationEventPublisher pub) { this.pub = pub; }

    public void register(String username, String email, boolean vip) {
        System.out.println("[UserService] Registering: " + username);
        pub.publishEvent(new UserRegisteredEvent(this, username, email, vip));
        System.out.println("[UserService] Done");
    }
}

@Configuration @ComponentScan
class Config2 { }

public class AppEventIntermediate {
    public static void main(String[] args) {
        var ctx = new AnnotationConfigApplicationContext(Config2.class);
        var svc = ctx.getBean(UserService2.class);
        svc.register("alice", "alice@ex.com", true);
        System.out.println("---");
        svc.register("bob", "bob@ex.com", false);
        ctx.close();
    }
}
```

How to run: `java AppEventIntermediate.java`

`@Order(1)`, `@Order(2)`, `@Order(3)` control listener dispatch order. `ApplicationEventPublisher` can be injected directly via constructor (cleaner than `ApplicationContextAware`). `VipPromoListener` filters inside `onApplicationEvent` — only acting for VIP users. All three listeners run synchronously in order for each `register` call.

### Level 3 — Advanced

Inject `ApplicationEventPublisher` via constructor; add a sub-event type; demonstrate listener inheritance; close the context cleanly.

```java
// AppEventAdvanced.java
import org.springframework.context.*;
import org.springframework.context.annotation.*;
import org.springframework.core.annotation.*;
import org.springframework.stereotype.*;

// --- Event hierarchy ---
class UserEvent extends ApplicationEvent {
    private final String userId;
    UserEvent(Object src, String uid) { super(src); userId=uid; }
    public String getUserId() { return userId; }
}

class UserRegisteredEvent extends UserEvent {
    private final String email; private final String plan;
    UserRegisteredEvent(Object src, String uid, String e, String p) {
        super(src, uid); email=e; plan=p;
    }
    public String getEmail() { return email; }
    public String getPlan()  { return plan;  }
}

class UserUpgradedEvent extends UserEvent {
    private final String newPlan;
    UserUpgradedEvent(Object src, String uid, String p) { super(src, uid); newPlan=p; }
    public String getNewPlan() { return newPlan; }
}

// Listens to ALL UserEvent subtypes (hierarchy)
@Component @Order(1)
class UniversalAuditListener implements ApplicationListener<UserEvent> {
    @Override
    public void onApplicationEvent(UserEvent e) {
        System.out.println("[AuditAll] " + e.getClass().getSimpleName()
            + " for user=" + e.getUserId());
    }
}

// Listens only to UserRegisteredEvent
@Component @Order(2)
class WelcomeListener implements ApplicationListener<UserRegisteredEvent> {
    @Override
    public void onApplicationEvent(UserRegisteredEvent e) {
        System.out.println("[Welcome] " + e.getUserId()
            + " plan=" + e.getPlan() + " email=" + e.getEmail());
    }
}

// Listens only to UserUpgradedEvent
@Component @Order(2)
class UpgradeListener implements ApplicationListener<UserUpgradedEvent> {
    @Override
    public void onApplicationEvent(UserUpgradedEvent e) {
        System.out.println("[Upgrade] " + e.getUserId() + " → " + e.getNewPlan());
    }
}

@Service
class UserLifecycleService {
    private final ApplicationEventPublisher pub;
    UserLifecycleService(ApplicationEventPublisher pub) { this.pub = pub; }

    public void register(String uid, String email, String plan) {
        pub.publishEvent(new UserRegisteredEvent(this, uid, email, plan));
    }

    public void upgrade(String uid, String newPlan) {
        pub.publishEvent(new UserUpgradedEvent(this, uid, newPlan));
    }
}

@Configuration @ComponentScan
class Config3 { }

public class AppEventAdvanced {
    public static void main(String[] args) {
        var ctx = new AnnotationConfigApplicationContext(Config3.class);
        var svc = ctx.getBean(UserLifecycleService.class);

        System.out.println("=== Register ===");
        svc.register("u1", "alice@ex.com", "basic");

        System.out.println("=== Upgrade ===");
        svc.upgrade("u1", "premium");

        ctx.close();
    }
}
```

How to run: `java AppEventAdvanced.java`

`UniversalAuditListener` implements `ApplicationListener<UserEvent>` — it receives both `UserRegisteredEvent` and `UserUpgradedEvent` because both extend `UserEvent`. `WelcomeListener` and `UpgradeListener` each receive only their specific sub-type. The `@Order(1)` on the universal listener ensures audit always runs before domain-specific reactions.

## 6. Walkthrough

Tracing `svc.register("u1", "alice@ex.com", "basic")` from Level 3 end-to-end:

**Step 1 — `register` called:**
```
UserLifecycleService.register("u1", "alice@ex.com", "basic")
```

**Step 2 — `pub.publishEvent(event)` called:**
- `event = new UserRegisteredEvent(this, "u1", "alice@ex.com", "basic")`
- `pub` is the `ApplicationContext`; it routes the event.

**Step 3 — Context finds applicable listeners:**
- All beans implementing `ApplicationListener<E>` where `E` is `UserRegisteredEvent` or a supertype of it.
- `UniversalAuditListener` implements `ApplicationListener<UserEvent>` — `UserEvent` is a supertype of `UserRegisteredEvent` → **included**.
- `WelcomeListener` implements `ApplicationListener<UserRegisteredEvent>` → **included**.
- `UpgradeListener` implements `ApplicationListener<UserUpgradedEvent>` — `UserUpgradedEvent` is NOT a supertype of `UserRegisteredEvent` → **excluded**.

**Step 4 — Dispatch in `@Order` sequence (same thread):**

| Step | Listener | Method | Prints |
|---|---|---|---|
| 4.1 | UniversalAuditListener @Order(1) | `onApplicationEvent(UserRegisteredEvent)` | `[AuditAll] UserRegisteredEvent for user=u1` |
| 4.2 | WelcomeListener @Order(2) | `onApplicationEvent(UserRegisteredEvent)` | `[Welcome] u1 plan=basic email=alice@ex.com` |

**Step 5 — `publishEvent` returns** — `register` method completes.

**Then `svc.upgrade("u1", "premium")` dispatches `UserUpgradedEvent`:**
- `UniversalAuditListener` receives it (supertype match) → `[AuditAll] UserUpgradedEvent for user=u1`
- `UpgradeListener` receives it → `[Upgrade] u1 → premium`
- `WelcomeListener` does NOT receive it (wrong sub-type).

## 7. Gotchas & takeaways

> **An exception in one listener stops subsequent listeners.** `publishEvent` is synchronous; if `WelcomeListener.onApplicationEvent` throws, `@Order(3)` listeners never run and the exception propagates to `UserLifecycleService.register`. Wrap listener bodies in try/catch if the listeners should be isolated from each other.

> **Listeners on a prototype-scope bean may not be registered.** Spring registers `ApplicationListener` beans discovered during context refresh. A prototype bean is not eagerly created, so its `ApplicationListener` implementation may not be registered at event dispatch time. Use singleton scope for event listeners.

- `ApplicationEventPublisher` can be injected by constructor — prefer this over `ApplicationContextAware` for cleaner code and easier testing.
- POJO events (non-`ApplicationEvent` objects) are wrapped in `PayloadApplicationEvent<T>` automatically; listeners can use `@EventListener` (next topic) to receive them without the wrapper.
- The event system is in-process and in-memory. For cross-service or durable events use a message broker (Spring for Apache Kafka, Spring AMQP).
- `ctx.close()` fires a `ContextClosedEvent`; if your listener reacts to it, ensure idempotency because some containers close the context more than once.
- An `ApplicationListener` for a parent context event is also fired by child context events when the parent context publishes events. Be aware in `@WebMvcTest` or layered context test setups.

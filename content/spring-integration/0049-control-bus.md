---
card: spring-integration
gi: 49
slug: control-bus
title: "Control bus"
---

## 1. What it is

A control bus is a special-purpose channel through which you send commands — expressed as Spring Expression Language (SpEL) strings — that operate *on the flow's own infrastructure itself*, rather than on business data. Sending the string `"@myPoller.stop()"` to a control bus, for instance, invokes `stop()` on the bean named `myPoller`, exactly as if that method had been called directly in code. It's the mechanism for managing a running integration flow's lifecycle (starting/stopping endpoints, adjusting a poller's settings) at runtime, from outside the flow's normal business-data path.

## 2. Why & when

You reach for a control bus specifically when a flow's own infrastructure needs to be managed dynamically, at runtime, rather than only through static startup configuration:

- **An endpoint needs to be paused or resumed based on an operational decision** — temporarily stopping a poller consuming from an overwhelmed downstream system, then resuming it once conditions improve — a control bus command like `"@overloadedConsumer.stop()"` does this without redeploying or restarting the whole application.
- **You want administrative/operational commands to flow through the same messaging infrastructure** as business messages, rather than requiring a separate JMX console, custom REST endpoint, or direct bean manipulation for every management action — a control bus message is just another message, sent through a channel like anything else in this section.
- **You need runtime introspection or adjustment of a running component's state** — checking whether a poller is currently running, adjusting a channel interceptor's configuration — expressed as SpEL against the live bean graph, without needing a dedicated management API written in advance for every possible operation.

## 3. Core concept

Think of a control bus like a building's central intercom system used by facilities staff, as opposed to the building's actual pipes and wiring (the business-data flow) that residents use every day. A resident doesn't page the intercom to ask for water — they just turn on the tap. But facilities staff, wanting to shut off water to one floor for maintenance, use the intercom/control system specifically built for *managing the building's own infrastructure*, separate from and layered above the everyday plumbing residents interact with.

```java
@Bean
public IntegrationFlow controlBusFlow() {
    return IntegrationFlows.from("controlBusChannel")
        .controlBus()
        .get();
}

// elsewhere, sending a command through the control bus:
controlBusGateway.send("@overloadedConsumer.stop()");
// this invokes stop() on the bean named "overloadedConsumer" — NOT a business-data operation at all
```

The command `"@overloadedConsumer.stop()"` is SpEL: `@overloadedConsumer` resolves to the bean of that name in the application context, and `.stop()` is a method call on it — the control bus channel's job is simply to evaluate whatever SpEL expression arrives as its message payload.

## 4. Diagram

<svg viewBox="0 0 640 170" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="A control bus channel receives a SpEL expression as its message payload and evaluates it against the live application context, invoking a method on a named bean such as stopping a poller">
  <rect x="20" y="70" width="150" height="45" rx="6" fill="#1c2430" stroke="#6db33f" stroke-width="2"/>
  <text x="95" y="92" fill="#e6edf3" font-size="8" text-anchor="middle" font-family="sans-serif">"@myPoller.stop()"</text>
  <text x="95" y="105" fill="#8b949e" font-size="6" text-anchor="middle" font-family="sans-serif">SpEL command message</text>

  <line x1="170" y1="92" x2="230" y2="92" stroke="#6db33f" stroke-width="2" marker-end="url(#cb1)"/>

  <rect x="240" y="65" width="160" height="55" rx="8" fill="#1c2430" stroke="#79c0ff" stroke-width="2"/>
  <text x="320" y="88" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">control bus channel</text>
  <text x="320" y="104" fill="#8b949e" font-size="7" text-anchor="middle" font-family="sans-serif">evaluates SpEL</text>

  <line x1="400" y1="92" x2="460" y2="92" stroke="#79c0ff" stroke-width="2" marker-end="url(#cb2)"/>

  <rect x="470" y="70" width="140" height="45" rx="6" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="540" y="92" fill="#e6edf3" font-size="8" text-anchor="middle" font-family="sans-serif">bean: myPoller</text>
  <text x="540" y="105" fill="#8b949e" font-size="6" text-anchor="middle" font-family="sans-serif">.stop() invoked</text>

  <defs>
    <marker id="cb1" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#6db33f"/></marker>
    <marker id="cb2" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#79c0ff"/></marker>
  </defs>
</svg>

The control bus channel's message payload isn't business data at all — it's a command, expressed as SpEL, targeting the running application's own infrastructure.

## 5. Runnable example

The scenario: a poller-driven endpoint that needs to be stopped and restarted based on operational conditions, starting with a basic control bus simulation invoking a method by name, then stopping/restarting an actual running poller, and finally a control bus command that queries live state (rather than just commanding an action).

### Level 1 — Basic

```java
// BasicControlBusDemo.java
// Simulates what a control bus does — evaluating a SpEL-style command against a bean registry —
// using plain reflection, since a real control bus needs a full Spring ApplicationContext and SpEL parser.
import java.util.Map;
import java.lang.reflect.Method;

public class BasicControlBusDemo {
    static class SimplePoller {
        boolean running = true;
        void stop() { running = false; System.out.println("SimplePoller: stop() invoked, running=" + running); }
        void start() { running = true; System.out.println("SimplePoller: start() invoked, running=" + running); }
    }

    // what evaluating a control bus command like "@myPoller.stop()" does for you, via reflection here:
    static void executeControlBusCommand(String command, Map<String, Object> beanRegistry) throws Exception {
        // parse "@myPoller.stop()" into beanName="myPoller", methodName="stop"
        String withoutAt = command.substring(1); // drop leading '@'
        String beanName = withoutAt.substring(0, withoutAt.indexOf('.'));
        String methodName = withoutAt.substring(withoutAt.indexOf('.') + 1, withoutAt.indexOf('('));

        Object bean = beanRegistry.get(beanName);
        Method method = bean.getClass().getMethod(methodName);
        method.invoke(bean);
    }

    public static void main(String[] args) throws Exception {
        SimplePoller myPoller = new SimplePoller();
        Map<String, Object> beanRegistry = Map.of("myPoller", myPoller);

        System.out.println("Sending control bus command: @myPoller.stop()");
        executeControlBusCommand("@myPoller.stop()", beanRegistry);
    }
}
```

How to run: `java BasicControlBusDemo.java`. Expected output: `Sending control bus command: @myPoller.stop()` then `SimplePoller: stop() invoked, running=false` — a plain string command, parsed and evaluated against a bean registry, resulted in an actual method call on a live object, exactly the mechanism a real control bus's SpEL evaluation provides.

### Level 2 — Intermediate

Stopping and restarting an actual running poller (built with the same polling-consumer mechanics from card 0035) via control bus commands shows the realistic operational use case: pausing consumption from a channel, then resuming it later, without redeploying anything.

```java
// PollerLifecycleControlDemo.java
import org.springframework.integration.channel.QueueChannel;
import org.springframework.messaging.Message;
import org.springframework.messaging.support.MessageBuilder;
import java.util.Map;
import java.lang.reflect.Method;
import java.util.concurrent.atomic.AtomicBoolean;

public class PollerLifecycleControlDemo {
    static class ManagedPoller {
        AtomicBoolean running = new AtomicBoolean(true);
        QueueChannel channel;
        ManagedPoller(QueueChannel channel) { this.channel = channel; }
        void stop() { running.set(false); System.out.println("[control bus] poller STOPPED"); }
        void start() { running.set(true); System.out.println("[control bus] poller STARTED"); }
        void pollOnce() {
            if (!running.get()) { System.out.println("[poller] skipped tick — currently stopped"); return; }
            Message<?> m = channel.receive(0);
            System.out.println("[poller] tick: " + (m != null ? "processed " + m.getPayload() : "nothing waiting"));
        }
    }

    static void executeControlBusCommand(String command, Map<String, Object> beanRegistry) throws Exception {
        String withoutAt = command.substring(1);
        String beanName = withoutAt.substring(0, withoutAt.indexOf('.'));
        String methodName = withoutAt.substring(withoutAt.indexOf('.') + 1, withoutAt.indexOf('('));
        Method method = beanRegistry.get(beanName).getClass().getMethod(methodName);
        method.invoke(beanRegistry.get(beanName));
    }

    public static void main(String[] args) throws Exception {
        QueueChannel orders = new QueueChannel();
        ManagedPoller poller = new ManagedPoller(orders);
        Map<String, Object> beanRegistry = Map.of("orderPoller", poller);

        orders.send(MessageBuilder.withPayload("order-1").build());
        poller.pollOnce(); // normal tick, processes order-1

        executeControlBusCommand("@orderPoller.stop()", beanRegistry);
        orders.send(MessageBuilder.withPayload("order-2").build());
        poller.pollOnce(); // skipped — poller is stopped, order-2 stays queued

        executeControlBusCommand("@orderPoller.start()", beanRegistry);
        poller.pollOnce(); // resumed — now picks up order-2
    }
}
```

How to run: `java PollerLifecycleControlDemo.java`. Expected output: `[poller] tick: processed order-1`, then `[control bus] poller STOPPED`, then `[poller] skipped tick — currently stopped` (even though `order-2` was sent and is sitting in the channel), then `[control bus] poller STARTED`, and finally `[poller] tick: processed order-2` — the control bus commands genuinely paused and resumed the poller's actual consumption behavior at runtime.

### Level 3 — Advanced

A control bus command can also be an *expression that returns a value* (querying live state) rather than only a command with a side effect — shown here checking whether a poller is currently running before deciding whether to send a stop command, mirroring how a real control bus can both query and command the running application.

```java
// QueryAndCommandControlBusDemo.java
import java.util.Map;
import java.lang.reflect.Method;
import java.util.concurrent.atomic.AtomicBoolean;

public class QueryAndCommandControlBusDemo {
    static class ManagedPoller {
        AtomicBoolean running = new AtomicBoolean(true);
        boolean isRunning() { return running.get(); } // a QUERY — returns a value, no side effect
        void stop() { running.set(false); }             // a COMMAND — side effect, no return value
    }

    // evaluate EITHER a query (returns a value) or a command (invokes a void method), based on SpEL-style parsing
    static Object executeControlBusExpression(String expression, Map<String, Object> beanRegistry) throws Exception {
        String withoutAt = expression.substring(1);
        String beanName = withoutAt.substring(0, withoutAt.indexOf('.'));
        String methodName = withoutAt.substring(withoutAt.indexOf('.') + 1, withoutAt.indexOf('('));
        Object bean = beanRegistry.get(beanName);
        Method method = bean.getClass().getMethod(methodName);
        return method.invoke(bean); // null for void commands, an actual value for queries
    }

    public static void main(String[] args) throws Exception {
        ManagedPoller poller = new ManagedPoller();
        Map<String, Object> beanRegistry = Map.of("orderPoller", poller);

        // QUERY first: check current state via the control bus, without changing anything
        Object isRunning = executeControlBusExpression("@orderPoller.isRunning()", beanRegistry);
        System.out.println("Control bus QUERY result: orderPoller.isRunning() = " + isRunning);

        if ((boolean) isRunning) {
            System.out.println("It's running — sending stop COMMAND via control bus");
            executeControlBusExpression("@orderPoller.stop()", beanRegistry);
        }

        Object isRunningAfter = executeControlBusExpression("@orderPoller.isRunning()", beanRegistry);
        System.out.println("Control bus QUERY result AFTER stop: orderPoller.isRunning() = " + isRunningAfter);
    }
}
```

How to run: `java QueryAndCommandControlBusDemo.java`. Expected output: `Control bus QUERY result: orderPoller.isRunning() = true`, then `It's running — sending stop COMMAND via control bus`, then `Control bus QUERY result AFTER stop: orderPoller.isRunning() = false` — the same control bus mechanism handled both a value-returning query and a side-effecting command, letting the calling code make a decision based on live application state before issuing a management command.

## 6. Walkthrough

Tracing `QueryAndCommandControlBusDemo` in execution order:

1. `executeControlBusExpression("@orderPoller.isRunning()", beanRegistry)` parses the expression into `beanName="orderPoller"` and `methodName="isRunning"`, looks up the `orderPoller` bean, reflectively finds its `isRunning` method, and invokes it — since `isRunning` has a return type (`boolean`), `method.invoke(...)` returns that boolean value rather than `null`.
2. The returned value (`true`, since the poller starts in a running state) is printed as the "QUERY result" — this expression had zero side effects; it purely read live state.
3. The `if ((boolean) isRunning)` check evaluates `true`, so the code decides to issue a stop command — this decision was made *based on* the control bus query's result, exactly the pattern a real operational script or monitoring system would use before taking a management action.
4. `executeControlBusExpression("@orderPoller.stop()", beanRegistry)` is called next — this time, `stop()` is a `void` method, so `method.invoke(...)` returns `null`, but the actual side effect (setting `running` to `false`) has genuinely happened on the live `poller` object.
5. A second query, `executeControlBusExpression("@orderPoller.isRunning()", beanRegistry)`, is issued to confirm the command's effect — this reflects the exact same live `poller` object's state, now updated.
6. The returned value is now `false`, confirming that the earlier stop command genuinely changed the running application's live state — the control bus mechanism uniformly handled reading state, making a decision based on that state, and then commanding a change to that same state, all through the same expression-evaluation pathway.

```
query:  "@orderPoller.isRunning()" -> reflect: isRunning() -> returns true
decide: true -> issue stop command
command: "@orderPoller.stop()" -> reflect: stop() -> void, but running.set(false) happens
query:  "@orderPoller.isRunning()" -> reflect: isRunning() -> returns false (CONFIRMS the change)
```

## 7. Gotchas & takeaways

> Because a control bus evaluates arbitrary SpEL expressions against the live application context — including invoking essentially any accessible method on any named bean — it is a genuinely powerful, security-sensitive capability. A control bus channel exposed to untrusted input (an unauthenticated HTTP endpoint feeding directly into it, for instance) would let an attacker invoke arbitrary methods on arbitrary beans in the application. Restrict control bus access to trusted, authenticated, internal operational tooling only — never expose it directly to external or untrusted input.

- A control bus is a special channel that evaluates SpEL expressions sent as message payloads against the live application context, letting operational commands manage a running flow's own infrastructure (starting/stopping pollers, adjusting components) at runtime.
- Use it for dynamic, runtime lifecycle management of a flow's infrastructure — pausing/resuming consumption, adjusting settings — without needing a redeploy or a separately-built management API for every possible operation.
- Control bus expressions can be commands (invoking a void method for its side effect) or queries (invoking a method that returns a value), letting operational tooling both read live state and act on it through the same mechanism.
- Because control bus expressions can invoke arbitrary methods on arbitrary beans, restrict access to trusted, authenticated, internal tooling only — never expose a control bus channel to untrusted or external input.
- The control bus is conceptually separate from the flow's business-data channels — it operates on the flow's own infrastructure, not on the business messages (orders, payments, and so on) flowing through the rest of the application.

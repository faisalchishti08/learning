---
card: spring-integration
gi: 28
slug: delayer
title: "Delayer"
---

## 1. What it is

`@Delayer` (via `DelayHandler`) is an endpoint that holds a message for a specified duration before forwarding it to the output channel, rather than dispatching immediately. The delay can be a fixed interval, or computed per-message (e.g., from a header specifying exactly when a particular message should be released) — either way, the sender's `send()` call itself returns immediately; the delay happens asynchronously inside the delayer, backed by a scheduler.

## 2. Why & when

You reach for `Delayer` specifically when a message needs to wait before proceeding, and that wait is itself a deliberate part of the flow's logic:

- **A business process has a genuine time-based rule** — "send a reminder email 24 hours after signup if the user hasn't confirmed," "retry a failed payment after a backoff interval" — a `Delayer` encodes that wait directly in the flow, rather than requiring an external scheduler or cron job to re-trigger something later.
- **You want to throttle or stagger message delivery** without blocking the sender — the sender's `send()` still returns immediately, and the delay is enforced entirely on the delayer's side, using its own scheduling infrastructure rather than the sender's thread.
- **Different messages need different delay durations**, computed from their own content (a header specifying a target release time, or a priority-based delay) rather than one fixed interval applying uniformly to everything passing through.

## 3. Core concept

Think of a `Delayer` like a mail carrier's "hold for later delivery" service — you drop off a letter and walk away immediately (the sender's `send()` returns right away), but the letter itself doesn't reach the recipient's mailbox until the requested future date, held safely by the postal service in the meantime. The letter isn't lost or forgotten; it's simply scheduled to be delivered later, independent of when it was dropped off.

```java
@Bean
@ServiceActivator(inputChannel = "reminders")
public DelayHandler delayHandler() {
    DelayHandler handler = new DelayHandler("reminder-delay-group");
    handler.setDefaultDelay(24 * 60 * 60 * 1000L); // 24 hours, in milliseconds
    handler.setOutputChannel(sendReminderChannel());
    return handler;
}
```

A message sent to `reminders` is accepted immediately (the caller's `send()` returns right away), but doesn't reach `sendReminderChannel` until the configured delay has elapsed — the delayer schedules the release using its own internal machinery, not the caller's thread.

## 4. Diagram

<svg viewBox="0 0 640 170" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Delayer accepts a message immediately, holds it internally for a configured duration, then forwards it to the output channel once the delay elapses">
  <rect x="20" y="60" width="110" height="45" rx="6" fill="#1c2430" stroke="#6db33f" stroke-width="2"/>
  <text x="75" y="87" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">send()</text>

  <line x1="130" y1="82" x2="190" y2="82" stroke="#6db33f" stroke-width="2" marker-end="url(#dl1)"/>
  <text x="160" y="68" fill="#6db33f" font-size="7" text-anchor="middle" font-family="sans-serif">returns instantly</text>

  <rect x="200" y="50" width="180" height="65" rx="8" fill="#1c2430" stroke="#79c0ff" stroke-width="2"/>
  <text x="290" y="75" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">@Delayer</text>
  <text x="290" y="92" fill="#8b949e" font-size="7" text-anchor="middle" font-family="sans-serif">holds until delay elapses</text>
  <text x="290" y="105" fill="#8b949e" font-size="7" text-anchor="middle" font-family="sans-serif">(scheduled, async)</text>

  <line x1="380" y1="82" x2="450" y2="82" stroke="#79c0ff" stroke-width="2" marker-end="url(#dl2)"/>
  <text x="415" y="68" fill="#79c0ff" font-size="7" text-anchor="middle" font-family="sans-serif">after delay</text>

  <rect x="460" y="60" width="150" height="45" rx="6" fill="#1c2430" stroke="#6db33f" stroke-width="2"/>
  <text x="535" y="87" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">output channel</text>

  <defs>
    <marker id="dl1" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#6db33f"/></marker>
    <marker id="dl2" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#79c0ff"/></marker>
  </defs>
</svg>

The sender never blocks waiting for the delay; the delayer's own scheduler handles the wait and the eventual forward.

## 5. Runnable example

The scenario: a reminder-scheduling flow, starting with a basic fixed delay, then a per-message delay computed from a header, and finally cancellation of a scheduled delay when a follow-up event makes it unnecessary.

### Level 1 — Basic

```java
// BasicDelayerDemo.java
import org.springframework.integration.channel.DirectChannel;
import org.springframework.messaging.support.MessageBuilder;
import java.util.concurrent.*;

public class BasicDelayerDemo {
    public static void main(String[] args) throws InterruptedException {
        DirectChannel reminders = new DirectChannel();
        DirectChannel sendReminder = new DirectChannel();
        sendReminder.subscribe(m -> System.out.println("Reminder SENT: " + m.getPayload()
            + " at +" + (System.currentTimeMillis()) + "ms"));

        ScheduledExecutorService scheduler = Executors.newSingleThreadScheduledExecutor();
        long fixedDelayMs = 500;

        // what @Delayer(defaultDelay=500) does for you:
        reminders.subscribe(m -> {
            System.out.println("Accepted (will delay ~" + fixedDelayMs + "ms): " + m.getPayload());
            scheduler.schedule(() -> sendReminder.send(m), fixedDelayMs, TimeUnit.MILLISECONDS);
        });

        long start = System.currentTimeMillis();
        reminders.send(MessageBuilder.withPayload("confirm-your-email").build());
        System.out.println("send() returned immediately, elapsed so far: " + (System.currentTimeMillis() - start) + "ms");

        Thread.sleep(700);
        scheduler.shutdown();
    }
}
```

How to run: `java BasicDelayerDemo.java`. Expected output: `Accepted...` and `send() returned immediately, elapsed so far: ~0ms` print right away, then (roughly 500ms later) `Reminder SENT: confirm-your-email...` — the caller never waited for the delay itself; only the actual forward to `sendReminder` was postponed.

### Level 2 — Intermediate

A delay can be computed per-message from a header (an `@Delayer`'s `delayExpression`) rather than being a single fixed interval — useful when different messages genuinely need different wait times, such as a priority-based reminder schedule.

```java
// PerMessageDelayDemo.java
import org.springframework.integration.channel.DirectChannel;
import org.springframework.messaging.support.MessageBuilder;
import java.util.concurrent.*;

public class PerMessageDelayDemo {
    public static void main(String[] args) throws InterruptedException {
        DirectChannel reminders = new DirectChannel();
        DirectChannel sendReminder = new DirectChannel();
        long start = System.currentTimeMillis();
        sendReminder.subscribe(m -> System.out.println("Reminder SENT: " + m.getPayload()
            + " at +" + (System.currentTimeMillis() - start) + "ms"));

        ScheduledExecutorService scheduler = Executors.newSingleThreadScheduledExecutor();

        // what a delayExpression reading a "delayMs" header does for you:
        reminders.subscribe(m -> {
            long delayMs = (Long) m.getHeaders().get("delayMs"); // PER-MESSAGE delay, not fixed
            scheduler.schedule(() -> sendReminder.send(m), delayMs, TimeUnit.MILLISECONDS);
        });

        reminders.send(MessageBuilder.withPayload("urgent-alert").setHeader("delayMs", 100L).build());
        reminders.send(MessageBuilder.withPayload("routine-digest").setHeader("delayMs", 500L).build());

        Thread.sleep(700);
        scheduler.shutdown();
    }
}
```

How to run: `java PerMessageDelayDemo.java`. Expected output: `Reminder SENT: urgent-alert at +~100ms` prints before `Reminder SENT: routine-digest at +~500ms` — even though `routine-digest` was sent first in code, its longer per-message delay means `urgent-alert` (sent second, but with a shorter delay) is actually forwarded first.

### Level 3 — Advanced

A realistic delayed-reminder flow needs cancellation: if a follow-up event happens before the delay elapses (the user confirms their email before the 24-hour reminder fires), the scheduled delayed message should be cancelled rather than sent anyway — modeled here using each scheduled task's own cancellable `Future`.

```java
// CancellableDelayDemo.java
import org.springframework.integration.channel.DirectChannel;
import org.springframework.messaging.Message;
import org.springframework.messaging.support.MessageBuilder;
import java.util.concurrent.*;

public class CancellableDelayDemo {
    public static void main(String[] args) throws InterruptedException {
        DirectChannel reminders = new DirectChannel();
        DirectChannel sendReminder = new DirectChannel();
        sendReminder.subscribe(m -> System.out.println("Reminder SENT (was NOT cancelled): " + m.getPayload()));

        ScheduledExecutorService scheduler = Executors.newSingleThreadScheduledExecutor();
        ConcurrentHashMap<String, ScheduledFuture<?>> pendingByUser = new ConcurrentHashMap<>();

        reminders.subscribe((Message<?> m) -> {
            String userId = (String) m.getHeaders().get("userId");
            ScheduledFuture<?> future = scheduler.schedule(() -> sendReminder.send(m), 300, TimeUnit.MILLISECONDS);
            pendingByUser.put(userId, future); // remember it so a later event can cancel it
            System.out.println("Scheduled reminder for " + userId);
        });

        reminders.send(MessageBuilder.withPayload("confirm-your-email")
            .setHeader("userId", "user-1").build());
        reminders.send(MessageBuilder.withPayload("confirm-your-email")
            .setHeader("userId", "user-2").build());

        Thread.sleep(100);
        // user-1 confirms their email BEFORE the 300ms delay elapses — cancel their pending reminder
        ScheduledFuture<?> pending = pendingByUser.remove("user-1");
        boolean cancelled = pending.cancel(false);
        System.out.println("user-1 confirmed early — cancelled pending reminder: " + cancelled);

        Thread.sleep(400); // let whatever wasn't cancelled fire
        scheduler.shutdown();
    }
}
```

How to run: `java CancellableDelayDemo.java`. Expected output: two `Scheduled reminder for user-N` lines, then `user-1 confirmed early — cancelled pending reminder: true`, and finally only `Reminder SENT (was NOT cancelled): confirm-your-email` for `user-2` — `user-1`'s reminder never fires, since it was cancelled before its delay elapsed.

## 6. Walkthrough

Tracing `CancellableDelayDemo` in execution order:

1. Both `reminders.send(...)` calls trigger the delayer-shaped subscriber, each scheduling its own message for release 300ms later and storing the resulting `ScheduledFuture` keyed by `userId` — both calls return immediately; nothing has actually been sent to `sendReminder` yet.
2. The main thread sleeps 100ms — well within the 300ms delay window for both scheduled reminders, so neither has fired yet.
3. The main thread simulates `user-1` confirming their email by looking up and removing `user-1`'s pending future, then calling `cancel(false)` on it — this tells the scheduler to abandon that specific scheduled task if it hasn't started running yet.
4. Because 100ms have passed out of the 300ms delay, `user-1`'s task is still pending (not yet executing), so `cancel(false)` succeeds, returning `true`, and prints confirmation.
5. The main thread sleeps another 400ms, well past the original 300ms delay for both users; `user-2`'s task, never cancelled, fires normally at its scheduled time, sending its message to `sendReminder` and triggering the print.
6. `user-1`'s task never fires — it was removed from the scheduler's queue by the cancellation in step 3, so `sendReminder` only ever receives `user-2`'s message, exactly the intended "don't send a reminder for something that already happened" behavior.

```
t=0ms:    schedule user-1 reminder for t=300ms
t=0ms:    schedule user-2 reminder for t=300ms
t=100ms:  user-1 confirms -> cancel(false) on user-1's future -> SUCCESS (task hadn't run yet)
t=300ms:  user-1's task: CANCELLED, never fires
t=300ms:  user-2's task: fires normally -> "Reminder SENT" for user-2
```

## 7. Gotchas & takeaways

> `cancel(false)` only succeeds if the scheduled task hasn't started executing yet — if the cancellation request arrives even slightly after the delay has already elapsed and the task has begun running, `cancel` returns `false` and the message is sent anyway (or, with `cancel(true)`, an already-running task is interrupted mid-execution, which can leave things in a half-done state). Race conditions between "cancel this delayed message" and "the delay just elapsed" are inherent to any delayer-with-cancellation design — don't assume cancellation is guaranteed to win.

- `Delayer` holds a message for a configured duration (fixed or computed per-message) before forwarding it, without blocking the sender — `send()` returns immediately regardless of the delay length.
- Use it to encode genuine time-based business rules (reminders, backoff retries, staggered delivery) directly in a flow, rather than relying on an external scheduler to re-trigger something later.
- A per-message delay (via a `delayExpression` reading a header) lets different messages wait different amounts of time, based on their own content.
- Cancellation of a pending delayed message is possible but inherently race-prone: it only reliably succeeds if requested before the delay has actually elapsed.
- A `Delayer`'s internal scheduling should typically be backed by persistent storage in production (rather than purely in-memory) if a delayed message surviving an application restart matters — an in-memory-only delayer loses all pending delayed messages if the process restarts before they fire.

---
card: spring-integration
gi: 71
slug: xmpp-support
title: "XMPP support"
---

## 1. What it is

XMPP support (`Xmpp.inboundAdapter(...)`/`Xmpp.outboundAdapter(...)`, plus presence-related components) connects a flow to the Extensible Messaging and Presence Protocol — the open, federated protocol behind Jabber and used in many chat and presence systems. Inbound, an adapter receives XMPP chat messages (or presence updates) and turns them into Spring Integration messages; outbound, a message is sent as an XMPP chat message to a specified contact (JID, or Jabber ID).

## 2. Why & when

You reach for XMPP support when the integration point is a chat-style, federated messaging network rather than a broker or HTTP endpoint:

- **A flow needs to notify a human over chat rather than email or a dashboard** — sending an XMPP message to an operator's chat client when an automated process needs attention, similar in spirit to the mail adapter (card 0063) but delivered as an instant chat message instead of an email.
- **Presence information drives flow behavior** — XMPP's presence subsystem reports whether a contact is online, away, or offline; a flow can use presence updates to decide whether to notify a person directly or fall back to another channel when they're offline.
- **Interoperating with an existing XMPP-based system** — some internal chat-ops tools, IoT device fleets, and older federated messaging deployments are built on XMPP; bridging a flow to one of them reuses that existing infrastructure instead of introducing a new protocol just for this one integration.

## 3. Core concept

Think of XMPP as similar to email's addressing model (`user@domain`, called a JID here) but built for live, two-way chat instead of store-and-forward mail — closer to instant messaging with a federated address book than to SMTP. A presence update is like a colleague's status light outside their office: lit green means available now, off means gone for the day — a flow reading that signal can decide whether pinging them directly makes sense or whether it should escalate elsewhere instead.

```java
@Bean
public IntegrationFlow xmppOutboundFlow(XMPPConnection connection) {
    return IntegrationFlow.from("operatorAlerts")
        .handle(Xmpp.outboundAdapter(connection)
            .xmppMessageConverter(new EnrichingXmppMessageConverter()))
        .get();
}
```

A message on `operatorAlerts` is delivered as a chat message to whichever JID the converter resolves from the message headers — an operator sees it appear in their chat client the same way a colleague's message would.

## 4. Diagram

<svg viewBox="0 0 640 160" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="XMPP outbound adapter sends a chat message to a JID; presence updates report whether that contact is online, away, or offline, letting a flow decide whether to notify directly or fall back" >
  <rect x="20" y="20" width="280" height="120" rx="8" fill="#0d1117" stroke="#6db33f" stroke-width="1.5"/>
  <text x="160" y="12" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">Outbound chat message</text>
  <text x="35" y="45" fill="#e6edf3" font-size="8" font-family="monospace">Message -&gt; Xmpp.outboundAdapter</text>
  <text x="35" y="65" fill="#79c0ff" font-size="8" font-family="monospace">to: operator@chat.example.com</text>
  <text x="35" y="100" fill="#8b949e" font-size="7" font-family="sans-serif">appears in operator's chat client</text>

  <rect x="340" y="20" width="280" height="120" rx="8" fill="#0d1117" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="480" y="12" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">Presence updates</text>
  <text x="355" y="45" fill="#6db33f" font-size="8" font-family="monospace">operator: ONLINE</text>
  <text x="355" y="65" fill="#8b949e" font-size="8" font-family="monospace">operator: AWAY</text>
  <text x="355" y="85" fill="#8b949e" font-size="8" font-family="monospace">operator: OFFLINE</text>
  <text x="355" y="110" fill="#8b949e" font-size="7" font-family="sans-serif">flow decides: notify direct or fallback</text>
</svg>

Delivery and presence are separate concerns: one sends the message, the other informs whether sending it there even makes sense right now.

## 5. Runnable example

The scenario: notifying an on-call operator over chat, falling back to another channel if they're offline, simulated with a plain in-memory presence map and message list standing in for a real XMPP connection (no real XMPP server needed to demonstrate the presence-aware routing logic), starting with a basic send, then adding a presence check before sending, then adding a fallback path and retry when the operator later comes online.

### Level 1 — Basic

```java
// XmppAlertDemo.java
public class XmppAlertDemo {
    // Stand-in for Xmpp.outboundAdapter's send: delivers a chat message to a JID.
    static void sendChatMessage(String jid, String body) {
        System.out.println("[chat to " + jid + "] " + body);
    }

    public static void main(String[] args) {
        sendChatMessage("operator@chat.example.com", "ALERT: disk usage above 90%");
    }
}
```

How to run: `java XmppAlertDemo.java`. Expected output: `[chat to operator@chat.example.com] ALERT: disk usage above 90%` — a direct chat send, no presence awareness yet.

### Level 2 — Intermediate

```java
// XmppAlertDemo.java
import java.util.*;

public class XmppAlertDemo {
    enum Presence { ONLINE, AWAY, OFFLINE }

    static void sendChatMessage(String jid, String body) {
        System.out.println("[chat to " + jid + "] " + body);
    }

    // Real-world concern: sending directly to an offline contact wastes the alert -- check
    // presence first and only chat-notify when the contact can actually see it right away.
    static void notifyOperator(String jid, String body, Map<String, Presence> presenceRegistry) {
        Presence presence = presenceRegistry.getOrDefault(jid, Presence.OFFLINE);
        if (presence == Presence.ONLINE) {
            sendChatMessage(jid, body);
        } else {
            System.out.println("Operator " + jid + " is " + presence + ", skipping direct chat notification");
        }
    }

    public static void main(String[] args) {
        Map<String, Presence> presenceRegistry = new HashMap<>();
        presenceRegistry.put("operator@chat.example.com", Presence.ONLINE);
        presenceRegistry.put("backup-operator@chat.example.com", Presence.OFFLINE);

        notifyOperator("operator@chat.example.com", "ALERT: disk usage above 90%", presenceRegistry);
        notifyOperator("backup-operator@chat.example.com", "ALERT: disk usage above 90%", presenceRegistry);
    }
}
```

How to run: `java XmppAlertDemo.java`. Expected output: the online operator receives the chat message directly; the offline backup operator is skipped with a `... skipping direct chat notification` message — the presence check preventing a wasted send to someone who won't see it in time.

### Level 3 — Advanced

```java
// XmppAlertDemo.java
import java.util.*;

public class XmppAlertDemo {
    enum Presence { ONLINE, AWAY, OFFLINE }

    static void sendChatMessage(String jid, String body) {
        System.out.println("[chat to " + jid + "] " + body);
    }

    static void sendEmailFallback(String jid, String body) {
        System.out.println("[email fallback for " + jid + "] " + body);
    }

    // Production concern: if the primary contact is offline, don't drop the alert -- fall back
    // to another channel (mirroring the mail adapter, card 0063) and queue a retry for when
    // presence changes back to ONLINE, rather than silently losing the notification.
    static class PresenceAwareNotifier {
        private final Map<String, Presence> presenceRegistry = new HashMap<>();
        private final List<String> pendingChatRetries = new ArrayList<>();

        void updatePresence(String jid, Presence presence) {
            presenceRegistry.put(jid, presence);
            if (presence == Presence.ONLINE && pendingChatRetries.remove(jid)) {
                sendChatMessage(jid, "(retried) you have pending alerts, check your dashboard");
            }
        }

        void notify(String jid, String body) {
            Presence presence = presenceRegistry.getOrDefault(jid, Presence.OFFLINE);
            if (presence == Presence.ONLINE) {
                sendChatMessage(jid, body);
            } else {
                sendEmailFallback(jid, body);
                pendingChatRetries.add(jid);
            }
        }
    }

    public static void main(String[] args) {
        PresenceAwareNotifier notifier = new PresenceAwareNotifier();
        notifier.updatePresence("operator@chat.example.com", Presence.OFFLINE);

        notifier.notify("operator@chat.example.com", "ALERT: disk usage above 90%");

        System.out.println("-- operator comes back online --");
        notifier.updatePresence("operator@chat.example.com", Presence.ONLINE);
    }
}
```

How to run: `java XmppAlertDemo.java`. Expected output: the initial alert falls back to email since the operator is offline, and gets queued for retry; once presence updates to `ONLINE`, the queued retry fires as a direct chat message — no alert is silently lost regardless of whether the operator was reachable at the moment it was raised.

## 6. Walkthrough

Trace a presence-aware alert end to end.

1. **Alert raised**: an internal monitoring process detects a condition (disk usage crossing a threshold) and hands the alert text to the flow's input channel.
2. **Presence check**: before sending, the flow inspects the operator's current presence, maintained by a presence-listening component subscribed to XMPP presence stanzas for that contact's JID.
3. **Direct path**: if presence is `ONLINE`, `Xmpp.outboundAdapter` sends the alert as a chat message directly to the JID, and the operator sees it appear in their chat client immediately, the same way a colleague's message would.
4. **Fallback path**: if presence is `AWAY` or `OFFLINE`, the flow routes to a different channel entirely (email, via the mail adapter from card 0063, or an on-call paging system), and records that this alert is pending retry once the operator's presence changes.
5. **Presence change reaction**: when a later XMPP presence stanza reports the operator transitioning to `ONLINE`, a presence-update handler checks the pending-retry list and, finding a match, sends the queued chat notification — closing the loop so the operator eventually gets the direct chat notification even though they weren't reachable when it was first raised.

```
alert raised
  -> check current presence for operator JID
       ONLINE  -> Xmpp.outboundAdapter sends chat message directly
       OFFLINE -> fallback channel (email) + queue for retry
                    ...later, presence -> ONLINE...
                    -> queued retry delivered as chat message
```

## 7. Gotchas & takeaways

> **Gotcha:** XMPP presence is inherently eventually-consistent and can lag reality — a contact's client may report `ONLINE` for a short while after they've actually stepped away (until a timeout elapses), so a flow relying on presence for anything time-critical should still have a fallback path rather than trusting presence as an absolute guarantee of reachability.

- XMPP is a federated, open protocol (like email's `user@domain` addressing, but for live chat), which makes it a good fit for bridging across organizational boundaries where both sides already run XMPP infrastructure.
- Presence and messaging are handled by related but distinct parts of the protocol; a flow that only wires up the outbound message adapter gets no presence awareness at all unless it separately subscribes to presence stanzas.
- Always pair a presence-based direct-notification path with a fallback channel — presence tells you whether direct delivery is *likely* to be seen promptly, not a delivery guarantee.
- As with any live-chat-style protocol, message ordering and delivery confirmation are weaker guarantees than a proper message broker offers; treat XMPP notifications as best-effort, human-facing alerts, not as a reliable transport for critical system-to-system data.

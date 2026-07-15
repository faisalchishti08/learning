---
card: spring-integration
gi: 60
slug: mqtt-support
title: "MQTT support"
---

## 1. What it is

MQTT support (`Mqtt.inboundAdapter(...)`/`Mqtt.outboundAdapter(...)`, built on Eclipse Paho) connects a flow to an MQTT broker. MQTT (Message Queuing Telemetry Transport) is a lightweight publish/subscribe protocol purpose-built for constrained devices and unreliable networks — think IoT sensors, mobile devices on flaky cellular connections — distinct from AMQP's rich exchange-routing model (card 0058) or Kafka's durable log (card 0059) in that it prioritizes minimal overhead and small message footprint above almost everything else, while still offering a configurable Quality of Service (QoS) level per message to trade reliability against overhead as needed.

## 2. Why & when

You reach for MQTT support specifically when the integration point is an MQTT broker, or when the protocol's lightweight, device-friendly design fits the actual use case:

- **You're integrating with IoT devices or sensors** — MQTT is the dominant protocol for device-to-cloud telemetry (temperature sensors, industrial equipment monitoring, connected vehicles), designed from the ground up to work well over low-bandwidth, high-latency, or intermittently-connected networks.
- **Minimal protocol overhead genuinely matters** — MQTT's binary header is a few bytes, dramatically smaller than an HTTP request's headers or even AMQP's framing, which matters when devices are sending frequent small readings over metered or constrained connections.
- **Different messages need different delivery guarantees, chosen per-message** — MQTT's three QoS levels (0: at-most-once/fire-and-forget, 1: at-least-once, 2: exactly-once) let a publisher choose the right tradeoff for each specific message type — a routine temperature reading might use QoS 0 (loss is acceptable), while a critical alarm event uses QoS 2 (guaranteed, exactly-once delivery), all on the same connection.

## 3. Core concept

Think of MQTT's QoS levels like different ways of sending a message depending on how much it matters: QoS 0 is like shouting something across a room — quick, cheap, but if nobody happens to be listening at that exact moment, it's simply lost, and you'll never know. QoS 1 is like sending a text message with delivery confirmation — you'll know it arrived, but if the confirmation itself gets lost, you might resend it, and the recipient could see it twice. QoS 2 is like a certified, signed-for letter — genuinely guaranteed to arrive exactly once, but with more back-and-forth handshaking required to achieve that guarantee, at real cost to overhead and latency.

```java
@Bean
public IntegrationFlow mqttOutboundFlow(MqttPahoClientFactory clientFactory) {
    return IntegrationFlow.from("sensorReadings")
        .handle(Mqtt.outboundAdapter(clientFactory, "sensor-publisher")
            .defaultTopic("devices/sensor-42/temperature")
            .defaultQos(0)) // routine readings: fire-and-forget is fine
        .get();
}

@Bean
public IntegrationFlow mqttInboundFlow(MqttPahoClientFactory clientFactory) {
    return IntegrationFlow.from(Mqtt.inboundAdapter(clientFactory, "sensor-subscriber", "devices/+/alarms")
            .qos(2)) // alarm events: guaranteed, exactly-once delivery is worth the overhead
        .handle((String alarmPayload, headers) -> alarmService.handle(alarmPayload))
        .get();
}
```

The `+` in `"devices/+/alarms"` is an MQTT topic wildcard matching exactly one topic level (any device ID), letting one subscription receive alarm events from every device without needing to know each device's specific ID in advance.

## 4. Diagram

<svg viewBox="0 0 640 190" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="MQTT QoS levels trade reliability against overhead: QoS 0 fires and forgets with no confirmation, QoS 1 guarantees at-least-once delivery with possible duplicates, QoS 2 guarantees exactly-once delivery with the most handshaking" >
  <rect x="20" y="20" width="180" height="40" rx="6" fill="#1c2430" stroke="#8b949e" stroke-width="1.5"/>
  <text x="110" y="44" fill="#e6edf3" font-size="8" text-anchor="middle" font-family="sans-serif">QoS 0: fire-and-forget</text>

  <rect x="230" y="20" width="180" height="40" rx="6" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="320" y="44" fill="#e6edf3" font-size="8" text-anchor="middle" font-family="sans-serif">QoS 1: at-least-once</text>

  <rect x="440" y="20" width="180" height="40" rx="6" fill="#1c2430" stroke="#6db33f" stroke-width="2"/>
  <text x="530" y="44" fill="#e6edf3" font-size="8" text-anchor="middle" font-family="sans-serif">QoS 2: exactly-once</text>

  <line x1="30" y1="80" x2="610" y2="80" stroke="#8b949e" stroke-width="1" marker-end="url(#mq1)"/>
  <text x="320" y="100" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">increasing reliability guarantee, increasing protocol overhead / latency</text>

  <text x="110" y="130" fill="#8b949e" font-size="7" text-anchor="middle" font-family="sans-serif">may be LOST silently</text>
  <text x="320" y="130" fill="#8b949e" font-size="7" text-anchor="middle" font-family="sans-serif">may arrive DUPLICATED</text>
  <text x="530" y="130" fill="#8b949e" font-size="7" text-anchor="middle" font-family="sans-serif">guaranteed once, most handshakes</text>

  <defs>
    <marker id="mq1" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#8b949e"/></marker>
  </defs>
</svg>

Each QoS level trades a different amount of reliability for a different amount of protocol overhead — the right choice depends on how much a given message type actually matters.

## 5. Runnable example

The scenario: a sensor telemetry and alarm system choosing different QoS levels per message type, simulated with an in-memory broker standing in for a real MQTT broker (since connecting to one requires external infrastructure), starting with basic QoS 0 fire-and-forget loss simulation, then QoS 1's possible duplicate delivery, and finally topic wildcard subscription matching multiple devices.

### Level 1 — Basic

```java
// Qos0LossDemo.java
// Simulates MQTT's QoS 0 behavior with an in-memory model standing in for a real broker,
// since connecting to an actual MQTT broker requires external infrastructure.
import java.util.*;

public class Qos0LossDemo {
    static List<String> subscriberInbox = new ArrayList<>();
    static boolean subscriberCurrentlyConnected = true;

    static void publishQos0(String topic, String payload) {
        if (!subscriberCurrentlyConnected) {
            System.out.println("QoS 0 publish while subscriber OFFLINE: '" + payload
                + "' is SILENTLY LOST — no delivery guarantee, no error raised");
            return; // genuinely just... gone
        }
        subscriberInbox.add(payload);
        System.out.println("QoS 0 publish delivered: " + payload);
    }

    public static void main(String[] args) {
        publishQos0("devices/sensor-1/temp", "22.5C"); // subscriber connected — delivered

        subscriberCurrentlyConnected = false; // simulate a brief network drop / device sleep
        publishQos0("devices/sensor-1/temp", "22.7C"); // LOST — no one to receive it, no queuing

        subscriberCurrentlyConnected = true;
        System.out.println("Subscriber inbox after reconnecting: " + subscriberInbox
            + " (the 22.7C reading is GONE FOREVER)");
    }
}
```

How to run: `java Qos0LossDemo.java`. Expected output: `QoS 0 publish delivered: 22.5C`, then `QoS 0 publish while subscriber OFFLINE: '22.7C' is SILENTLY LOST...`, then `Subscriber inbox after reconnecting: [22.5C] (the 22.7C reading is GONE FOREVER)` — the second reading, published while the subscriber was momentarily disconnected, is genuinely lost forever under QoS 0, with no retry or queuing mechanism to recover it.

### Level 2 — Intermediate

QoS 1's at-least-once guarantee, where an unacknowledged publish is retried — but the retry itself can result in the subscriber seeing the same logical message twice if the original acknowledgment was simply delayed rather than truly lost.

```java
// Qos1DuplicateDemo.java
import java.util.*;

public class Qos1DuplicateDemo {
    static List<String> subscriberInbox = new ArrayList<>();

    static void publishQos1(String payload, boolean ackArrivesInTime) {
        subscriberInbox.add(payload); // subscriber DOES receive it
        System.out.println("QoS 1: delivered '" + payload + "', waiting for ACK...");

        if (!ackArrivesInTime) {
            // the publisher's ACK-wait TIMES OUT — from the PUBLISHER's perspective, it looks lost, so it RETRIES
            System.out.println("QoS 1: ACK timed out (was just DELAYED, not actually lost) — publisher RETRIES");
            subscriberInbox.add(payload); // the subscriber receives the SAME message AGAIN
            System.out.println("QoS 1: subscriber received a DUPLICATE of: " + payload);
        } else {
            System.out.println("QoS 1: ACK received in time, no retry needed");
        }
    }

    public static void main(String[] args) {
        publishQos1("alarm: high-temperature", true);  // clean, no duplicate
        System.out.println();
        publishQos1("alarm: door-opened", false);       // ACK delayed -> retry -> DUPLICATE

        System.out.println("\nFinal subscriber inbox: " + subscriberInbox);
    }
}
```

How to run: `java Qos1DuplicateDemo.java`. Expected output: the first publish completes cleanly with no duplicate; the second publish's simulated delayed acknowledgment triggers a retry, and the final inbox contains `"alarm: door-opened"` *twice* — QoS 1 guarantees the message is never silently lost (unlike QoS 0), but achieving that guarantee can produce duplicate deliveries, meaning subscriber-side logic must be idempotent (exactly the pattern from card 0047) if duplicate processing would be harmful.

### Level 3 — Advanced

MQTT topic wildcard subscription — a single subscription using the `+` (single-level) wildcard matches alarm events from every device without the subscriber needing to know each device's specific topic in advance, demonstrated with several devices publishing to their own device-specific topics.

```java
// TopicWildcardSubscriptionDemo.java
import java.util.*;
import java.util.regex.*;

public class TopicWildcardSubscriptionDemo {
    static boolean matchesMqttWildcard(String subscriptionPattern, String actualTopic) {
        // '+' matches exactly ONE topic level; converts "devices/+/alarms" into a matching regex
        String regex = "^" + subscriptionPattern.replace("+", "[^/]+") + "$";
        return Pattern.matches(regex, actualTopic);
    }

    static List<String> matchedAlarms = new ArrayList<>();

    static void publish(String topic, String payload, String subscriptionPattern) {
        if (matchesMqttWildcard(subscriptionPattern, topic)) {
            matchedAlarms.add(topic + " -> " + payload);
        }
    }

    public static void main(String[] args) {
        String subscription = "devices/+/alarms"; // ONE subscription, matches ANY device ID

        publish("devices/sensor-1/alarms", "high-temperature", subscription);
        publish("devices/sensor-2/alarms", "door-opened", subscription);
        publish("devices/sensor-1/telemetry", "22.5C", subscription); // does NOT match — different topic suffix

        System.out.println("Subscription '" + subscription + "' matched:");
        matchedAlarms.forEach(a -> System.out.println("  " + a));
    }
}
```

How to run: `java TopicWildcardSubscriptionDemo.java`. Expected output: `Subscription 'devices/+/alarms' matched:` followed by two entries — `devices/sensor-1/alarms -> high-temperature` and `devices/sensor-2/alarms -> door-opened` — the `devices/sensor-1/telemetry` publish is correctly excluded, since its topic doesn't end in `/alarms`; a single wildcard subscription received alarm events from two entirely different devices without needing a separate subscription per device.

## 6. Walkthrough

Tracing `Qos1DuplicateDemo`'s second `publishQos1` call in execution order:

1. `publishQos1("alarm: door-opened", false)` first adds the payload to `subscriberInbox` — this represents the actual MQTT broker delivering the message to the subscriber, which genuinely does happen on the first attempt.
2. The `false` argument simulates the scenario where the acknowledgment (the MQTT protocol's `PUBACK` packet, confirming successful receipt) doesn't reach the publisher in time — perhaps due to network latency or a brief connectivity hiccup, even though the original message itself *did* get through.
3. Because the publisher's perspective is "I never got confirmation," it has no way to distinguish "the message was lost" from "the message arrived but the acknowledgment was delayed/lost" — QoS 1's design deliberately favors safety (assume it might have failed) over precision, so it retries.
4. The retry adds the *same* payload to `subscriberInbox` a second time — from the subscriber's perspective, it has now received two separate `"alarm: door-opened"` messages, even though logically only one alarm event actually occurred.
5. If `alarmService.handle(...)` (the real handler this simulation stands in for) isn't written to be idempotent — recognizing and ignoring a message it has already processed, exactly the pattern from card 0047 — it would incorrectly process this single alarm event twice, potentially triggering a duplicate notification or duplicate automated response.
6. The final printed inbox, containing the door-opened alarm twice, is the concrete, directly observable consequence of QoS 1's at-least-once (rather than exactly-once) guarantee — a tradeoff genuinely worth making for many use cases, but one that shifts real responsibility onto the subscriber to handle duplicates correctly.

```
publishQos1("door-opened", ackArrivesInTime=false):
  deliver to subscriber -> inbox: [door-opened]
  ACK never confirmed in time -> publisher assumes possible loss -> RETRY
  deliver AGAIN -> inbox: [door-opened, door-opened]  <- DUPLICATE, subscriber must handle idempotently
```

## 7. Gotchas & takeaways

> Choosing QoS 2 ("exactly-once") for every message, assuming it's simply "the safest option," ignores its real cost: QoS 2 requires a four-step handshake (compared to QoS 0's single fire-and-forget packet or QoS 1's two-step publish-and-acknowledge), meaningfully increasing latency and network overhead — precisely the resource constraints MQTT was designed to respect in the first place. Match the QoS level to what a given message type genuinely needs; using QoS 2 uniformly for high-frequency routine telemetry can defeat much of the point of choosing MQTT in the first place.

- MQTT support connects a flow to an MQTT broker, a lightweight publish/subscribe protocol purpose-built for constrained devices and unreliable networks, distinct from AMQP's richer routing model (card 0058) or Kafka's durable log (card 0059).
- MQTT's three QoS levels trade reliability against overhead per-message: QoS 0 (fire-and-forget, possible silent loss), QoS 1 (at-least-once, possible duplicates), QoS 2 (exactly-once, most overhead).
- Subscriber-side logic handling QoS 1 messages must be idempotent (mirroring the idempotent receiver pattern from card 0047), since duplicate delivery is an expected, not exceptional, outcome of that QoS level.
- MQTT topic wildcards (`+` for a single level, `#` for multiple trailing levels) let one subscription match many related topics — such as receiving alarm events from every device without a separate subscription per device.
- Choose the QoS level deliberately per message type based on what that specific data actually requires — defaulting to the highest QoS level for everything sacrifices much of MQTT's lightweight, low-overhead design intent.

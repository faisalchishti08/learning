---
card: spring-integration
gi: 73
slug: syslog-support
title: "Syslog support"
---

## 1. What it is

Syslog support (`Syslog.inboundAdapter(...)`, built on TCP/UDP support from card 0053 with a syslog-aware converter) receives syslog messages — the standard log-transport format defined by RFC 3164 and RFC 5424, widely emitted by network devices, Unix/Linux daemons, and infrastructure appliances — and parses each into a Spring Integration message with fields like facility, severity, hostname, and the log text broken out as separate headers.

## 2. Why & when

You reach for syslog support when the integration point is infrastructure or network equipment emitting logs in the syslog format rather than an application-level API:

- **Network devices and appliances only speak syslog** — routers, switches, firewalls, and many embedded systems have no REST API or message-broker client; syslog (over UDP, traditionally, or TCP for reliable delivery) is often the only integration point they expose at all.
- **Centralizing logs from heterogeneous sources into one pipeline** — a flow can receive syslog from many different device types and normalize their facility/severity/hostname fields into one consistent downstream format, feeding a common alerting or storage pipeline regardless of which vendor produced the original message.
- **Severity-based routing without parsing raw text** — syslog's structured facility and severity fields let a flow route `EMERGENCY` and `CRITICAL` messages to an urgent alert channel and demote routine `INFO` messages to bulk storage, without the flow having to regex-parse free-text log lines itself.

## 3. Core concept

Think of syslog as a standardized shipping label attached to every log message: no matter which factory (device) it came from, the label always has the same fields in the same place — who sent it (facility, a coarse category like "kernel" or "auth"), how urgent it is (severity, from `EMERGENCY` down to `DEBUG`), and a timestamp and hostname — followed by the actual message text as the payload of the parcel. A parser that understands this label format can sort parcels from wildly different senders using the exact same rules, rather than needing custom sorting logic for every distinct shipper.

```java
@Bean
public IntegrationFlow syslogInboundFlow() {
    return IntegrationFlow.from(Syslog.inboundAdapter(514))
        .<Map<String, ?>>route(m -> (Integer) m.get(SyslogHeaders.SEVERITY) <= 2, // EMERGENCY/ALERT/CRITICAL
            spec -> spec
                .subFlowMapping(true, sf -> sf.handle(alertService::pageOnCall))
                .subFlowMapping(false, sf -> sf.handle(logStore::archive)))
        .get();
}
```

Every inbound syslog message carries its severity as a plain integer header, letting the flow route on it directly instead of parsing the raw log text.

## 4. Diagram

<svg viewBox="0 0 640 170" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Syslog messages from routers, firewalls, and servers all arrive in the same structured format; a syslog adapter parses facility, severity, hostname, and message uniformly regardless of the source device" >
  <rect x="10" y="20" width="120" height="40" rx="6" fill="#1c2430" stroke="#8b949e" stroke-width="1.5"/>
  <text x="70" y="44" fill="#e6edf3" font-size="8" text-anchor="middle" font-family="sans-serif">Router</text>
  <rect x="140" y="20" width="120" height="40" rx="6" fill="#1c2430" stroke="#8b949e" stroke-width="1.5"/>
  <text x="200" y="44" fill="#e6edf3" font-size="8" text-anchor="middle" font-family="sans-serif">Firewall</text>
  <rect x="270" y="20" width="120" height="40" rx="6" fill="#1c2430" stroke="#8b949e" stroke-width="1.5"/>
  <text x="330" y="44" fill="#e6edf3" font-size="8" text-anchor="middle" font-family="sans-serif">Linux server</text>

  <line x1="70" y1="60" x2="290" y2="100" stroke="#8b949e" stroke-width="1.2"/>
  <line x1="200" y1="60" x2="300" y2="100" stroke="#8b949e" stroke-width="1.2"/>
  <line x1="330" y1="60" x2="310" y2="100" stroke="#8b949e" stroke-width="1.2"/>

  <rect x="220" y="100" width="200" height="55" rx="8" fill="#0d1117" stroke="#6db33f" stroke-width="1.5"/>
  <text x="320" y="122" fill="#e6edf3" font-size="8" text-anchor="middle" font-family="sans-serif">Syslog.inboundAdapter</text>
  <text x="320" y="140" fill="#79c0ff" font-size="7" text-anchor="middle" font-family="sans-serif">facility, severity, host, message</text>

  <line x1="320" y1="155" x2="320" y2="165" stroke="#6db33f" stroke-width="1.5"/>
  <text x="320" y="14" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">Uniform structured fields regardless of source</text>
</svg>

Every source's log line is parsed into the same facility/severity/hostname/message shape, enabling uniform routing.

## 5. Runnable example

The scenario: receiving syslog messages from mixed infrastructure and routing by severity, simulated with plain in-memory syslog-shaped records (no real UDP/TCP listener needed to demonstrate the parsing and routing logic), starting with a basic severity route, then adding per-facility handling, then adding rate-limited alerting so a flapping device doesn't flood the on-call channel.

### Level 1 — Basic

```java
// SyslogRoutingDemo.java
import java.util.*;

public class SyslogRoutingDemo {
    // Stand-in for what Syslog.inboundAdapter parses out of a raw syslog line.
    record SyslogMessage(String host, int facility, int severity, String text) {}

    static void route(SyslogMessage msg) {
        if (msg.severity() <= 2) { // EMERGENCY=0, ALERT=1, CRITICAL=2
            System.out.println("PAGE ON-CALL [" + msg.host() + "]: " + msg.text());
        } else {
            System.out.println("Archived [" + msg.host() + "]: " + msg.text());
        }
    }

    public static void main(String[] args) {
        route(new SyslogMessage("router-1", 4, 2, "interface eth0 down"));
        route(new SyslogMessage("web-3", 1, 6, "request completed in 45ms"));
    }
}
```

How to run: `java SyslogRoutingDemo.java`. Expected output: the router's critical message triggers `PAGE ON-CALL ...`, while the routine web-server info message is `Archived ...` — severity-based routing without any text parsing.

### Level 2 — Intermediate

```java
// SyslogRoutingDemo.java
import java.util.*;

public class SyslogRoutingDemo {
    record SyslogMessage(String host, int facility, int severity, String text) {}

    static final Map<Integer, String> FACILITY_NAMES = Map.of(
        0, "kernel", 1, "user", 4, "auth", 3, "daemon", 16, "local0");

    // Real-world concern: different facilities need different handling even at the same
    // severity -- an auth-facility critical message (a break-in attempt) is more urgent than
    // a routine daemon-facility critical message, so route on both fields together.
    static void route(SyslogMessage msg) {
        String facility = FACILITY_NAMES.getOrDefault(msg.facility(), "unknown");
        if (msg.severity() <= 2 && facility.equals("auth")) {
            System.out.println("SECURITY PAGE [" + msg.host() + "/" + facility + "]: " + msg.text());
        } else if (msg.severity() <= 2) {
            System.out.println("PAGE ON-CALL [" + msg.host() + "/" + facility + "]: " + msg.text());
        } else {
            System.out.println("Archived [" + msg.host() + "/" + facility + "]: " + msg.text());
        }
    }

    public static void main(String[] args) {
        route(new SyslogMessage("gateway-1", 4, 2, "repeated failed login attempts detected"));
        route(new SyslogMessage("router-1", 3, 2, "routing daemon restarted"));
    }
}
```

How to run: `java SyslogRoutingDemo.java`. Expected output: the auth-facility critical message escalates to `SECURITY PAGE ...`, while the daemon-facility critical message goes to the ordinary `PAGE ON-CALL ...` path — facility and severity combined giving finer-grained routing than severity alone.

### Level 3 — Advanced

```java
// SyslogRoutingDemo.java
import java.util.*;

public class SyslogRoutingDemo {
    record SyslogMessage(String host, int facility, int severity, String text) {}

    static final Map<Integer, String> FACILITY_NAMES = Map.of(
        0, "kernel", 1, "user", 4, "auth", 3, "daemon", 16, "local0");

    // Production concern: a flapping device can emit hundreds of critical messages in seconds
    // (a router link bouncing up and down). Paging on-call once per message would flood them --
    // rate-limit alerts per host so a storm of syslog messages produces one page, not hundreds.
    static class RateLimitedRouter {
        private final Map<String, Long> lastPagedAtMillis = new HashMap<>();
        private static final long COOLDOWN_MILLIS = 60_000;

        void route(SyslogMessage msg, long nowMillis) {
            String facility = FACILITY_NAMES.getOrDefault(msg.facility(), "unknown");
            if (msg.severity() > 2) {
                System.out.println("Archived [" + msg.host() + "/" + facility + "]: " + msg.text());
                return;
            }
            Long lastPaged = lastPagedAtMillis.get(msg.host());
            if (lastPaged != null && nowMillis - lastPaged < COOLDOWN_MILLIS) {
                System.out.println("Suppressed duplicate page for " + msg.host() + " (cooldown active)");
                return;
            }
            System.out.println("PAGE ON-CALL [" + msg.host() + "/" + facility + "]: " + msg.text());
            lastPagedAtMillis.put(msg.host(), nowMillis);
        }
    }

    public static void main(String[] args) {
        RateLimitedRouter router = new RateLimitedRouter();
        long now = 0;

        for (int i = 0; i < 3; i++) {
            router.route(new SyslogMessage("router-1", 4, 2, "interface eth0 flapping"), now);
            now += 5_000; // messages arrive 5 seconds apart, well within the cooldown
        }
    }
}
```

How to run: `java SyslogRoutingDemo.java`. Expected output: the first message pages on-call; the next two, arriving within the 60-second cooldown, print `Suppressed duplicate page for router-1 (cooldown active)` — the rate-limiting guard that keeps a flapping device from generating a page-storm.

## 6. Walkthrough

Trace a syslog message from network arrival to alert (or archive).

1. **Message arrives**: a device sends a syslog packet (UDP, or a TCP stream for reliable delivery) to the port `Syslog.inboundAdapter(514)` is listening on.
2. **Parsing**: the adapter parses the message according to RFC 3164 or RFC 5424 framing, extracting facility, severity, timestamp, hostname, and the message text into distinct header fields on a Spring Integration `Message`.
3. **Routing decision**: a `.route(...)` step inspects `SyslogHeaders.SEVERITY` (and, in the more refined version, `SyslogHeaders.FACILITY` too) to decide the message's disposition — urgent page, routine archive, or (in Level 3) suppressed as a duplicate within a rate-limiting cooldown.
4. **Urgent path**: for a message meeting the paging criteria and not currently rate-limited, the flow calls into an alerting service, which notifies on-call staff — the same pattern as the JMX threshold alert (card 0067) or the XMPP presence-aware notifier (card 0071), just triggered by a different inbound source.
5. **Routine path**: for everything else, the message is archived to long-term log storage, where it remains searchable for later incident investigation even though it never triggered an immediate notification.
6. **Rate-limiting bookkeeping**: after paging, the router records the timestamp for that host so a burst of repeated critical messages from the same flapping device within the cooldown window is suppressed rather than generating dozens of redundant pages.

```
syslog packet arrives (UDP/TCP, port 514)
  -> RFC 3164/5424 parse -> Message{facility, severity, host, text}
    -> route on severity (+ facility)
       severity <= CRITICAL, not rate-limited -> page on-call, record timestamp
       severity <= CRITICAL, within cooldown  -> suppressed
       severity  > CRITICAL                  -> archive
```

## 7. Gotchas & takeaways

> **Gotcha:** syslog over UDP (the traditional transport) is fire-and-forget — a lost packet during a network hiccup means a critical alert simply never arrives, with no retransmission and no error visible anywhere; if losing an occasional message is unacceptable, configure the adapter (and the sending devices, if they support it) to use TCP instead, which at least detects a broken connection.

- Facility and severity are numeric codes defined by the syslog RFCs, not free text — always route on the parsed header fields rather than trying to regex-match the message text for words like "critical," since a device's actual text conventions vary widely even when its severity code is set correctly.
- A single misbehaving or flapping device can produce a disproportionate share of total syslog volume; rate-limiting alerts per source (as in Level 3) is a near-mandatory production concern, not an optional refinement.
- RFC 5424 (the newer format) supports structured data fields beyond RFC 3164's plain text message, but not every device emits the newer format — a production adapter configuration should tolerate both, since a fleet of mixed-vintage hardware is the common case, not the exception.
- Centralizing syslog into a Spring Integration flow is a good fit for normalizing and routing alerts across heterogeneous infrastructure, but it is not a substitute for a dedicated log-aggregation and search system for the archived, non-urgent volume — the archive path typically hands off to that kind of system rather than reimplementing log storage and search inside the flow itself.

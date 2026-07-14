---
card: microservices
gi: 458
slug: adapter-pattern-deployment
title: "Adapter pattern (deployment)"
---

## 1. What it is

The **adapter pattern**, in the deployment sense, is a third [sidecar](0456-sidecar-pattern.md) variant: a companion container that sits next to the main application and **standardizes its output** — logs, metrics, health-check format — into whatever shape the rest of the platform expects, without the main application needing to know or care about that shape. Where an [ambassador](0457-ambassador-pattern.md) standardizes *outbound* calls the application makes, an adapter standardizes what the application *emits*.

## 2. Why & when

You reach for a deployment adapter whenever an application's native output doesn't match the platform's expected interface, and you'd rather not touch the application's code to fix that:

- **Legacy or third-party applications emit logs, metrics, or health signals in their own format.** A platform-wide monitoring stack usually expects one consistent format (say, Prometheus metrics or structured JSON logs) — an adapter translates the application's native output into that shape.
- **Different applications, same platform contract.** In a fleet of services written by different teams over different years, an adapter lets each application keep emitting output however it always has, while every application still presents the same interface to the platform.
- **You avoid touching application code you don't own or can't safely change.** Rewriting a legacy application's logging internals is often riskier than wrapping it with a translating sidecar.
- **The translation is narrow and mechanical** — reformatting, relabeling, or reshaping data — as opposed to an ambassador's job of managing an entire outbound connection's resilience.

## 3. Core concept

Think of a physical power adapter: it doesn't change what your laptop does, it just changes the *shape of the plug* so a device built for one socket standard works in a wall built for another. A deployment adapter does the same thing for data shape instead of electrical shape.

Concretely:

1. **The main application writes output the way it always has** — a proprietary log line format, metrics in an old exposition format, whatever its own conventions are. It is not modified.
2. **The adapter, running alongside it in the same Pod, reads that native output** — tailing a log file, scraping a legacy metrics endpoint, or reading from a local socket.
3. **The adapter transforms the output into the platform's standard shape** — parsing the proprietary log line into structured JSON, or converting a legacy metrics format into Prometheus's text format.
4. **The adapter exposes the transformed output** on the interface the platform actually scrapes or collects from, so from the platform's point of view, every application looks uniform — even though what's actually running inside each Pod varies wildly.

## 4. Diagram

<svg viewBox="0 0 640 220" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="A legacy application writes logs in its native format; an adapter sidecar reads them and re-exposes them in the platform's standard format">
  <rect x="30" y="70" width="170" height="60" rx="8" fill="#1c2430" stroke="#f85149" stroke-width="1.5"/>
  <text x="115" y="95" fill="#e6edf3" font-size="11" text-anchor="middle" font-family="sans-serif">legacy-app</text>
  <text x="115" y="112" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">native log format</text>

  <rect x="250" y="70" width="170" height="60" rx="8" fill="#1c2430" stroke="#6db33f" stroke-width="2"/>
  <text x="335" y="95" fill="#e6edf3" font-size="11" text-anchor="middle" font-family="sans-serif">Adapter sidecar</text>
  <text x="335" y="112" fill="#6db33f" font-size="9" text-anchor="middle" font-family="sans-serif">translates format</text>

  <rect x="470" y="70" width="150" height="60" rx="8" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="545" y="95" fill="#e6edf3" font-size="11" text-anchor="middle" font-family="sans-serif">Platform</text>
  <text x="545" y="112" fill="#79c0ff" font-size="9" text-anchor="middle" font-family="sans-serif">standard format</text>

  <line x1="200" y1="100" x2="250" y2="100" stroke="#8b949e" marker-end="url(#a1)"/>
  <line x1="420" y1="100" x2="470" y2="100" stroke="#8b949e" marker-end="url(#a1)"/>

  <text x="335" y="170" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">the legacy app is never modified; only its output's shape changes</text>

  <defs>
    <marker id="a1" markerWidth="8" markerHeight="8" refX="6" refY="4" orient="auto"><path d="M0,0 L8,4 L0,8 z" fill="#8b949e"/></marker>
  </defs>
</svg>

The adapter reads the application's native output and re-exposes it in the platform's expected format, without the application changing.

## 5. Runnable example

Scenario: a legacy `billing-service` writes pipe-delimited log lines. The platform's log collector expects structured JSON. We start with a basic adapter that reformats one line, extend it to handle a stream of varying line shapes, then handle the hard case: malformed lines that must not crash the adapter or silently corrupt the platform's log stream.

### Level 1 — Basic

```java
// File: AdapterBasic.java -- the legacy app emits ONE proprietary log line;
// the adapter reads it and re-emits it as structured JSON. The legacy
// format is fixed and NOT changed.
public class AdapterBasic {
    // The legacy app: emits pipe-delimited lines, its native format.
    static String legacyAppEmitsLogLine() {
        return "2024-01-15T10:00:00|ERROR|payment-failed|order-42";
    }

    // The adapter: reads native output, re-emits platform-standard JSON.
    static String adaptToJson(String nativeLine) {
        String[] parts = nativeLine.split("\\|");
        String timestamp = parts[0], level = parts[1], message = parts[2], orderId = parts[3];
        return String.format(
            "{\"timestamp\":\"%s\",\"level\":\"%s\",\"message\":\"%s\",\"orderId\":\"%s\"}",
            timestamp, level, message, orderId);
    }

    public static void main(String[] args) {
        String nativeLine = legacyAppEmitsLogLine();
        System.out.println("[legacy-app] native output: " + nativeLine);
        String adapted = adaptToJson(nativeLine);
        System.out.println("[adapter] platform-standard output: " + adapted);
    }
}
```

How to run: `java AdapterBasic.java`

`legacyAppEmitsLogLine` stands in for the unmodified legacy application — it produces its native pipe-delimited format regardless of what the rest of the platform expects. `adaptToJson` is the sidecar's job: split the native line on its known delimiter and re-assemble the same information as structured JSON, the shape the platform's collector actually understands.

### Level 2 — Intermediate

```java
// File: AdapterStream.java -- the SAME translation, now applied to a
// STREAM of lines with varying field counts (some lines carry extra
// context). The adapter must handle each line independently and keep
// producing valid JSON for every one, not just a single fixed shape.
import java.util.*;

public class AdapterStream {
    static List<String> legacyAppEmitsLogLines() {
        return List.of(
            "2024-01-15T10:00:00|ERROR|payment-failed|order-42",
            "2024-01-15T10:00:05|INFO|order-shipped|order-17",
            "2024-01-15T10:00:09|WARN|retry-scheduled|order-42|attempt-2"
        );
    }

    static String adaptToJson(String nativeLine) {
        String[] parts = nativeLine.split("\\|");
        StringBuilder json = new StringBuilder("{");
        json.append("\"timestamp\":\"").append(parts[0]).append("\",");
        json.append("\"level\":\"").append(parts[1]).append("\",");
        json.append("\"message\":\"").append(parts[2]).append("\",");
        json.append("\"orderId\":\"").append(parts[3]).append("\"");
        if (parts.length > 4) {
            json.append(",\"extra\":\"").append(parts[4]).append("\"");
        }
        json.append("}");
        return json.toString();
    }

    public static void main(String[] args) {
        for (String nativeLine : legacyAppEmitsLogLines()) {
            System.out.println("[adapter] " + adaptToJson(nativeLine));
        }
    }
}
```

How to run: `java AdapterStream.java`

The legacy app now emits three lines, one of which carries a fifth field (`attempt-2`) the other two don't have. `adaptToJson` checks `parts.length > 4` and only adds the `"extra"` key when that field is actually present, so every output line is valid JSON regardless of how many fields the native line happened to carry — the adapter tolerates the legacy format's own inconsistency.

### Level 3 — Advanced

```java
// File: AdapterRobust.java -- the SAME stream-processing adapter, now
// handling a PRODUCTION-FLAVORED hard case: some native lines are
// MALFORMED (missing fields, garbage data) because the legacy app has its
// own bugs. A crashing adapter would take down log collection for every
// OTHER, well-formed line too -- so malformed lines must be caught,
// reported once, and skipped, without stopping the stream.
import java.util.*;

public class AdapterRobust {
    static List<String> legacyAppEmitsLogLines() {
        return List.of(
            "2024-01-15T10:00:00|ERROR|payment-failed|order-42",
            "GARBAGE-NOT-A-LOG-LINE",
            "2024-01-15T10:00:05|INFO|order-shipped|order-17",
            "2024-01-15T10:00:07|WARN",
            "2024-01-15T10:00:09|WARN|retry-scheduled|order-42|attempt-2"
        );
    }

    static String adaptToJson(String nativeLine) {
        String[] parts = nativeLine.split("\\|");
        if (parts.length < 4) {
            throw new IllegalArgumentException("malformed line, expected >= 4 fields, got " + parts.length);
        }
        StringBuilder json = new StringBuilder("{");
        json.append("\"timestamp\":\"").append(parts[0]).append("\",");
        json.append("\"level\":\"").append(parts[1]).append("\",");
        json.append("\"message\":\"").append(parts[2]).append("\",");
        json.append("\"orderId\":\"").append(parts[3]).append("\"");
        if (parts.length > 4) {
            json.append(",\"extra\":\"").append(parts[4]).append("\"");
        }
        json.append("}");
        return json.toString();
    }

    public static void main(String[] args) {
        List<String> lines = legacyAppEmitsLogLines();
        int adapted = 0, skipped = 0;
        for (String nativeLine : lines) {
            try {
                String json = adaptToJson(nativeLine);
                System.out.println("[adapter] " + json);
                adapted++;
            } catch (IllegalArgumentException e) {
                System.out.println("[adapter] SKIPPING malformed line (" + e.getMessage() + "): " + nativeLine);
                skipped++;
            }
        }
        System.out.println("[adapter] stream done: " + adapted + " adapted, " + skipped + " skipped");
    }
}
```

How to run: `java AdapterRobust.java`

`legacyAppEmitsLogLines` now includes two malformed entries: pure garbage with no delimiters at all, and a truncated line with only two fields. `adaptToJson` validates `parts.length` and throws before building any JSON if the line doesn't meet the minimum shape. The loop in `main` wraps each call in a `try`/`catch`, counting `adapted` and `skipped` separately — one bad line is logged and passed over, but the stream keeps running through every subsequent well-formed line.

## 6. Walkthrough

Trace `AdapterRobust.main` in order. **First**, `legacyAppEmitsLogLines()` returns the fixed list of five lines, mixing well-formed and malformed entries, standing in for a live log stream from the unmodified legacy application.

**Next**, the loop takes the first line — a well-formed four-field entry — and calls `adaptToJson`. `parts.length` is `4`, so the validation passes, the JSON is built and printed, and `adapted` becomes `1`.

**Then**, the loop reaches `"GARBAGE-NOT-A-LOG-LINE"`. Splitting on `\|` yields a single-element array (no delimiter found), so `parts.length < 4` is `true` and `adaptToJson` throws `IllegalArgumentException`. The `catch` block in `main` prints a skip message instead of letting the exception propagate, and `skipped` becomes `1` — critically, the loop continues to its next iteration rather than terminating.

**After that**, the third line (well-formed, `order-shipped`) adapts successfully (`adapted = 2`), the fourth line (truncated, only two fields) is caught and skipped (`skipped = 2`), and the fifth line (well-formed, with the optional fifth field) adapts successfully and includes the `"extra"` key (`adapted = 3`).

**Finally**, the loop ends and `main` prints the summary line, showing `3 adapted, 2 skipped` — every well-formed line reached the platform's collector in the correct format, and every malformed line was reported and discarded, without either group affecting the other.

```
[adapter] {"timestamp":"2024-01-15T10:00:00","level":"ERROR","message":"payment-failed","orderId":"order-42"}
[adapter] SKIPPING malformed line (malformed line, expected >= 4 fields, got 1): GARBAGE-NOT-A-LOG-LINE
[adapter] {"timestamp":"2024-01-15T10:00:05","level":"INFO","message":"order-shipped","orderId":"order-17"}
[adapter] SKIPPING malformed line (malformed line, expected >= 4 fields, got 2): 2024-01-15T10:00:07|WARN
[adapter] {"timestamp":"2024-01-15T10:00:09","level":"WARN","message":"retry-scheduled","orderId":"order-42","extra":"attempt-2"}
[adapter] stream done: 3 adapted, 2 skipped
```

## 7. Gotchas & takeaways

> An adapter that crashes on the first malformed line takes the entire log stream down with it — including every well-formed line the legacy application emits afterward. Isolating failures per line, as `AdapterRobust` does, is what makes the adapter safe to run against an application whose own output you don't fully control.

- An adapter standardizes what the application *emits*; an [ambassador](0457-ambassador-pattern.md) standardizes what the application *calls out to*. Both are sidecars, but they sit on opposite sides of the data flow.
- Keep the transformation narrow and mechanical — reshaping, relabeling, reformatting. If the sidecar starts making retry or failover decisions, it has drifted into ambassador territory.
- Malformed native output should be logged and skipped, never silently dropped without a trace and never allowed to crash the whole adapter process.
- Because the adapter is a separate container, it can be upgraded, patched, or replaced independently of the legacy application it's translating for — a real advantage when the legacy code itself is frozen or unowned.
- Adapters are especially valuable for gradually migrating a fleet of older services onto a new platform-wide observability standard without a coordinated, risky rewrite of every application at once.

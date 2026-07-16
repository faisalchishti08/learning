---
card: spring-integration
gi: 90
slug: jmx-management-endpoints
title: "JMX & management endpoints"
---

## 1. What it is

JMX and management endpoints refers to Spring Integration's built-in exposure of its own runtime components — message channels, endpoints, pollers — as MBeans automatically, alongside Spring Boot Actuator's `integrationgraph` endpoint, giving operators visibility into a running flow's structure and activity without needing to build custom instrumentation. This differs from the JMX support adapter (card 0067), which lets a *flow* consume or invoke arbitrary JMX MBeans; this card is about Spring Integration exposing *itself* as manageable infrastructure.

## 2. Why & when

You reach for these built-in management endpoints whenever visibility into a running flow's health and structure is needed without custom-building it:

- **Operators need to see message counts, error rates, and channel activity in production** — Spring Integration automatically registers MBeans for its channels and handlers exposing send counts, error counts, and active/queued message counts, viewable in `jconsole` or any JMX-aware monitoring tool with zero additional configuration.
- **Understanding a complex flow's actual wiring is hard from source code alone** — the `integrationgraph` Actuator endpoint (or the underlying `IntegrationGraphServer`) produces a structured representation of every channel and endpoint currently wired together, useful both for documentation and for verifying a flow's actual runtime shape matches what was intended.
- **Diagnosing a stuck or slow flow in production** — MBean attributes like a channel's queue size or a poller's active task count can reveal exactly where messages are piling up, turning a vague "something's slow" into a specific, addressable bottleneck.

## 3. Core concept

Think of a flow's source code as an architect's blueprint — it shows what was designed, but not necessarily what's happening inside the building right now. The built-in management endpoints are like sensors already wired throughout that building the moment it's constructed: foot-traffic counters on every doorway (channel send counts), queue-length sensors at bottlenecks (channel queue sizes), and a live floor plan generator (the integration graph) that always reflects the building's actual current layout — all without anyone needing to install a single additional sensor themselves.

```java
// No extra code needed for basic MBean exposure -- Spring Integration registers channels
// and endpoints as MBeans automatically when JMX is enabled in the application.

// Exposing the integration graph via Spring Boot Actuator just needs the dependency and:
// management.endpoints.web.exposure.include=integrationgraph

// Querying it:
// GET /actuator/integrationgraph
// -> { "contentDescriptor": {...}, "nodes": [...], "links": [...] }
```

With Actuator's `integrationgraph` endpoint exposed, a single HTTP GET returns the entire flow's current wiring as structured JSON — no custom introspection code required.

## 4. Diagram

<svg viewBox="0 0 640 150" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Spring Integration automatically exposes its own channels and endpoints as MBeans for JMX tools, and as a structured graph via the Actuator integrationgraph endpoint, without requiring custom instrumentation code" >
  <rect x="20" y="20" width="280" height="110" rx="8" fill="#0d1117" stroke="#6db33f" stroke-width="1.5"/>
  <text x="160" y="12" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">JMX MBeans (automatic)</text>
  <text x="35" y="45" fill="#e6edf3" font-size="7" font-family="monospace">channel: sendCount, errorCount</text>
  <text x="35" y="65" fill="#e6edf3" font-size="7" font-family="monospace">poller: activeCount, queueSize</text>
  <text x="35" y="95" fill="#8b949e" font-size="7" font-family="sans-serif">viewable in jconsole, no extra code</text>

  <rect x="340" y="20" width="280" height="110" rx="8" fill="#0d1117" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="480" y="12" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">Integration graph (Actuator)</text>
  <text x="355" y="45" fill="#e6edf3" font-size="7" font-family="monospace">GET /actuator/integrationgraph</text>
  <text x="355" y="65" fill="#79c0ff" font-size="7" font-family="monospace">-&gt; { nodes: [...], links: [...] }</text>
  <text x="355" y="95" fill="#8b949e" font-size="7" font-family="sans-serif">live, structured flow topology</text>
</svg>

Both sources of visibility come from the framework itself observing its own wiring, not from custom application code.

## 5. Runnable example

The scenario: inspecting a running flow's activity and structure without any custom instrumentation, simulated with a plain in-memory model standing in for Spring Integration's auto-registered MBean attributes and the integration graph (no real JMX MBeanServer or Actuator endpoint needed to demonstrate the self-observability concept), starting with basic channel counters, then adding a structured graph representation, then using both together to pinpoint a bottleneck.

### Level 1 — Basic

```java
// SelfObservabilityDemo.java
import java.util.*;

public class SelfObservabilityDemo {
    // Stand-in for the auto-registered MBean attributes Spring Integration exposes per channel.
    static class ChannelStats {
        int sendCount = 0;
        int errorCount = 0;
        void recordSend() { sendCount++; }
        void recordError() { errorCount++; }
    }

    public static void main(String[] args) {
        ChannelStats orderChannelStats = new ChannelStats();
        orderChannelStats.recordSend();
        orderChannelStats.recordSend();
        orderChannelStats.recordError();

        System.out.println("orderChannel sendCount=" + orderChannelStats.sendCount
            + " errorCount=" + orderChannelStats.errorCount);
    }
}
```

How to run: `java SelfObservabilityDemo.java`. Expected output: `orderChannel sendCount=2 errorCount=1` — exactly the kind of counter Spring Integration's auto-registered channel MBean exposes for free, with no application code specifically instrumenting it.

### Level 2 — Intermediate

```java
// SelfObservabilityDemo.java
import java.util.*;

public class SelfObservabilityDemo {
    static class ChannelStats {
        int sendCount = 0;
        int errorCount = 0;
        int queueSize = 0;
        void recordSend() { sendCount++; }
        void recordError() { errorCount++; }
    }

    // Real-world concern: understanding a flow's actual structure, not just per-channel
    // counters, requires seeing how channels and endpoints connect -- the integration graph's job.
    record GraphNode(String name, String type) {}
    record GraphLink(String from, String to) {}

    static class IntegrationGraph {
        List<GraphNode> nodes = new ArrayList<>();
        List<GraphLink> links = new ArrayList<>();
        void addNode(String name, String type) { nodes.add(new GraphNode(name, type)); }
        void addLink(String from, String to) { links.add(new GraphLink(from, to)); }
    }

    public static void main(String[] args) {
        IntegrationGraph graph = new IntegrationGraph();
        graph.addNode("orderChannel", "channel");
        graph.addNode("validationFilter", "filter");
        graph.addNode("chargeHandler", "service-activator");
        graph.addLink("orderChannel", "validationFilter");
        graph.addLink("validationFilter", "chargeHandler");

        System.out.println("Graph nodes: " + graph.nodes);
        System.out.println("Graph links: " + graph.links);
    }
}
```

How to run: `java SelfObservabilityDemo.java`. Expected output: a printed list of nodes (`orderChannel`, `validationFilter`, `chargeHandler`, each with its type) and links showing how they connect — exactly the structured representation the `integrationgraph` Actuator endpoint would return as JSON for a real flow, letting an operator confirm the actual wiring matches what was intended.

### Level 3 — Advanced

```java
// SelfObservabilityDemo.java
import java.util.*;

public class SelfObservabilityDemo {
    static class ChannelStats {
        int sendCount = 0;
        int errorCount = 0;
        int queueSize = 0;
    }

    record GraphNode(String name, String type) {}
    record GraphLink(String from, String to) {}

    static class IntegrationGraph {
        List<GraphNode> nodes = new ArrayList<>();
        List<GraphLink> links = new ArrayList<>();
        void addNode(String name, String type) { nodes.add(new GraphNode(name, type)); }
        void addLink(String from, String to) { links.add(new GraphLink(from, to)); }
    }

    // Production concern: combine the graph (structure) with per-node stats (activity) to
    // pinpoint a bottleneck -- e.g. a channel with a large queueSize sitting right before a slow
    // downstream endpoint, visible only by correlating both sources of built-in observability.
    static void diagnoseBottleneck(IntegrationGraph graph, Map<String, ChannelStats> statsByChannel) {
        for (GraphNode node : graph.nodes) {
            if (!node.type().equals("channel")) continue;
            ChannelStats stats = statsByChannel.get(node.name());
            if (stats != null && stats.queueSize > 50) {
                System.out.println("BOTTLENECK: channel '" + node.name() + "' has queueSize="
                    + stats.queueSize + " -- messages are piling up here");
                graph.links.stream()
                    .filter(link -> link.from().equals(node.name()))
                    .forEach(link -> System.out.println("  -> feeds into: " + link.to()
                        + " (likely the slow consumer)"));
            }
        }
    }

    public static void main(String[] args) {
        IntegrationGraph graph = new IntegrationGraph();
        graph.addNode("orderChannel", "channel");
        graph.addNode("chargeHandler", "service-activator");
        graph.addLink("orderChannel", "chargeHandler");

        Map<String, ChannelStats> statsByChannel = new HashMap<>();
        ChannelStats orderStats = new ChannelStats();
        orderStats.queueSize = 120; // messages backing up -- chargeHandler can't keep up
        statsByChannel.put("orderChannel", orderStats);

        diagnoseBottleneck(graph, statsByChannel);
    }
}
```

How to run: `java SelfObservabilityDemo.java`. Expected output: `BOTTLENECK: channel 'orderChannel' has queueSize=120 -- messages are piling up here` followed by `-> feeds into: chargeHandler (likely the slow consumer)` — correlating the graph's structural information (what connects to what) with the MBean-exposed queue-size metric to pinpoint exactly which endpoint is the actual bottleneck, without needing any custom instrumentation built specifically for this diagnosis.

## 6. Walkthrough

Trace how an operator diagnoses a slow flow using only Spring Integration's built-in observability.

1. **Symptom noticed**: an operator or monitoring alert flags that order processing has become slow, with no specific indication yet of which part of the flow is responsible.
2. **Query the integration graph**: hitting `GET /actuator/integrationgraph` (or an equivalent JMX query against the `IntegrationGraphServer` MBean) returns the current, actual structure of the running flow — every channel and endpoint, and how they connect — confirming the real wiring rather than relying on possibly-outdated documentation or source code review.
3. **Query per-channel MBean attributes**: for each channel in that graph, the automatically-registered MBean exposes attributes like current queue size, total send count, and error count — no custom counters needed, since Spring Integration instruments this by default.
4. **Correlate structure with activity**: cross-referencing the graph (which channel feeds which endpoint) against the MBean attributes (which channel has an unusually large queue size) pinpoints the exact bottleneck — in the example, `orderChannel`'s large queue reveals that `chargeHandler` is the slow consumer messages are backing up in front of.
5. **Root-cause investigation continues from there**: once the bottleneck endpoint is identified, further investigation (checking `chargeHandler`'s own dependencies, perhaps discovering a slow downstream payment gateway) can proceed with a specific, confirmed starting point rather than guessing across the entire flow.
6. **No redeployment needed for any of this**: because both the graph and the MBean attributes are exposed automatically by the running application, this entire diagnostic process happens against the live system with zero code changes or redeployment required.

```
symptom: "order processing is slow"
  -> GET /actuator/integrationgraph -> confirmed structure: orderChannel -> chargeHandler
    -> query orderChannel MBean -> queueSize = 120 (elevated)
      -> bottleneck pinpointed: chargeHandler can't keep up with orderChannel's inflow
        -> investigate chargeHandler's own dependencies next
```

## 7. Gotchas & takeaways

> **Gotcha:** JMX access to a running application is a privileged operation — exposing MBeans (or the `integrationgraph` Actuator endpoint) without appropriate authentication and network restriction turns useful operational visibility into an information-disclosure risk, potentially revealing internal flow structure and traffic patterns to anyone who can reach the endpoint; secure these endpoints the same way any other sensitive management interface would be secured.

- These built-in endpoints are observability tools, not control tools — they show what's happening but (unlike the JMX support adapter from card 0067, which can invoke operations) don't by themselves let an operator change the flow's behavior through the graph or basic channel MBeans alone.
- The integration graph reflects live, current wiring — genuinely useful for confirming that a flow actually looks the way its source code suggests it should, catching cases where conditional bean configuration produced a different runtime structure than expected.
- Combine structural information (the graph) with activity metrics (MBean attributes) rather than relying on either alone — the graph without metrics shows what's connected but not where the trouble is; metrics without the graph show numbers without the context of what's actually connected to what.
- Because this observability comes essentially for free (automatic MBean registration, an Actuator endpoint away), there's little reason to build custom flow-introspection tooling before first checking what Spring Integration already exposes out of the box.

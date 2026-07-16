---
card: spring-integration
gi: 91
slug: integration-graph-integrationgraphserver
title: "Integration graph (IntegrationGraphServer)"
---

## 1. What it is

`IntegrationGraphServer` is the component that builds the structured graph representation of a running application's Spring Integration configuration — every channel, endpoint, adapter, and the links between them — that both the Actuator `integrationgraph` endpoint (card 0090) and any custom tooling can query. It's the underlying mechanism, distinct from the endpoint that exposes it over HTTP: `IntegrationGraphServer` introspects the application context's beans and assembles the graph model, which `integrationgraph` then simply serializes and serves.

## 2. Why & when

You reach for `IntegrationGraphServer` directly (rather than only through the Actuator endpoint) when the graph needs to be consumed programmatically rather than just viewed:

- **Building custom visualization or monitoring tooling** — a team wanting a bespoke dashboard showing flow topology, rather than relying on generic JSON from the Actuator endpoint, can inject `IntegrationGraphServer` directly and call `getGraph()` to get the same structured model to render however they choose.
- **Automated validation that a flow's runtime structure matches expectations** — a test or a startup health check can call `getGraph()` and assert on its nodes and links, catching cases where conditional configuration (profiles, feature flags) produced an unexpected wiring in a particular environment.
- **Programmatically discovering all channels or endpoints for bulk operations** — code that needs to enumerate every channel in the running context (to attach a wire tap to all of them for a debugging session, for instance) can query the graph rather than needing to know every channel's name in advance.

## 3. Core concept

Think of `IntegrationGraphServer` as a building inspector who walks through a building already fully constructed (the running application context) and produces an accurate floor plan based on what's actually there — not the original blueprint, but a survey of the real, current structure, including anything that ended up different from the plan due to later modifications. That floor plan (the graph) can then be handed to a receptionist to laminate and hang on the wall for visitors to read (the Actuator endpoint), or handed directly to a facilities-management system that uses it programmatically to decide where to route maintenance staff (custom tooling built directly against `IntegrationGraphServer`).

```java
@Autowired
private IntegrationGraphServer graphServer;

@Bean
public ApplicationRunner validateFlowStructure() {
    return args -> {
        Graph graph = graphServer.getGraph();
        boolean hasExpectedChannel = graph.getNodes().stream()
            .anyMatch(node -> node.getName().equals("paymentRequests"));
        if (!hasExpectedChannel) {
            throw new IllegalStateException("Expected channel 'paymentRequests' missing from runtime graph");
        }
    };
}
```

Calling `getGraph()` directly gives programmatic access to the same structured model the Actuator endpoint serializes, letting application code assert on or act on the flow's actual runtime shape.

## 4. Diagram

<svg viewBox="0 0 640 150" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="IntegrationGraphServer introspects the running application context to build a graph model; that model can be consumed either through the Actuator HTTP endpoint or directly by custom application code" >
  <rect x="20" y="20" width="180" height="45" rx="6" fill="#1c2430" stroke="#8b949e" stroke-width="1.5"/>
  <text x="110" y="47" fill="#e6edf3" font-size="8" text-anchor="middle" font-family="sans-serif">Running app context</text>

  <line x1="200" y1="42" x2="270" y2="42" stroke="#6db33f" stroke-width="1.5" marker-end="url(#a7)"/>
  <rect x="270" y="20" width="180" height="45" rx="6" fill="#0d1117" stroke="#6db33f" stroke-width="1.5"/>
  <text x="360" y="47" fill="#e6edf3" font-size="8" text-anchor="middle" font-family="sans-serif">IntegrationGraphServer</text>

  <line x1="360" y1="65" x2="360" y2="95" stroke="#79c0ff" stroke-width="1.5" marker-end="url(#a7)"/>
  <line x1="450" y1="42" x2="530" y2="42" stroke="#79c0ff" stroke-width="1.5" marker-end="url(#a7)"/>

  <rect x="270" y="100" width="180" height="40" rx="6" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="360" y="125" fill="#e6edf3" font-size="8" text-anchor="middle" font-family="sans-serif">Custom code: getGraph()</text>

  <rect x="530" y="20" width="90" height="45" rx="6" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="575" y="47" fill="#e6edf3" font-size="8" text-anchor="middle" font-family="sans-serif">Actuator</text>
</svg>

One graph model, two consumers: the generic Actuator endpoint, or direct programmatic access.

## 5. Runnable example

The scenario: validating that a flow's runtime structure matches expectations at startup, simulated with a plain in-memory graph model standing in for `IntegrationGraphServer.getGraph()` (no real Spring application context needed to demonstrate the introspect-and-validate pattern), starting with a basic graph query, then adding a structural assertion that fails loudly if a channel is missing, then adding a bulk operation across every discovered channel.

### Level 1 — Basic

```java
// GraphServerDemo.java
import java.util.*;

public class GraphServerDemo {
    record GraphNode(String name, String type) {}
    record Graph(List<GraphNode> nodes) {}

    // Stand-in for IntegrationGraphServer.getGraph(): introspects the "running context".
    static Graph buildGraph(List<GraphNode> registeredComponents) {
        return new Graph(new ArrayList<>(registeredComponents));
    }

    public static void main(String[] args) {
        Graph graph = buildGraph(List.of(
            new GraphNode("orderChannel", "channel"),
            new GraphNode("chargeHandler", "service-activator")));

        System.out.println("Discovered nodes: " + graph.nodes());
    }
}
```

How to run: `java GraphServerDemo.java`. Expected output: `Discovered nodes: [GraphNode[name=orderChannel, type=channel], GraphNode[name=chargeHandler, type=service-activator]]` — a basic query of the runtime graph's contents.

### Level 2 — Intermediate

```java
// GraphServerDemo.java
import java.util.*;

public class GraphServerDemo {
    record GraphNode(String name, String type) {}
    record Graph(List<GraphNode> nodes) {}

    static Graph buildGraph(List<GraphNode> registeredComponents) {
        return new Graph(new ArrayList<>(registeredComponents));
    }

    // Real-world concern: conditional bean configuration (profiles, feature flags) can produce
    // a runtime structure that doesn't match what was expected -- validate it explicitly at
    // startup rather than assuming the source code's intent was actually realized.
    static void validateExpectedChannel(Graph graph, String expectedChannelName) {
        boolean found = graph.nodes().stream()
            .anyMatch(n -> n.name().equals(expectedChannelName) && n.type().equals("channel"));
        if (!found) {
            throw new IllegalStateException(
                "Expected channel '" + expectedChannelName + "' missing from runtime graph");
        }
        System.out.println("Validated: channel '" + expectedChannelName + "' is present");
    }

    public static void main(String[] args) {
        Graph graphMissingChannel = buildGraph(List.of(
            new GraphNode("chargeHandler", "service-activator"))); // "paymentRequests" never got wired in

        try {
            validateExpectedChannel(graphMissingChannel, "paymentRequests");
        } catch (IllegalStateException ex) {
            System.out.println("Startup validation FAILED: " + ex.getMessage());
        }
    }
}
```

How to run: `java GraphServerDemo.java`. Expected output: `Startup validation FAILED: Expected channel 'paymentRequests' missing from runtime graph` — catching, right at startup, a case where the expected channel simply never got wired into the running context (perhaps disabled by a profile that wasn't supposed to be active), rather than discovering the gap only when a message silently goes nowhere in production.

### Level 3 — Advanced

```java
// GraphServerDemo.java
import java.util.*;
import java.util.function.*;

public class GraphServerDemo {
    record GraphNode(String name, String type) {}
    record GraphLink(String from, String to) {}
    record Graph(List<GraphNode> nodes, List<GraphLink> links) {}

    static Graph buildGraph(List<GraphNode> nodes, List<GraphLink> links) {
        return new Graph(new ArrayList<>(nodes), new ArrayList<>(links));
    }

    // Production concern: discover every channel programmatically for a bulk operation (e.g.
    // attaching a temporary debug wire tap to all of them) rather than needing to know and list
    // every channel name by hand -- the graph makes this discoverable rather than hardcoded.
    static void attachDebugTapToAllChannels(Graph graph, Consumer<String> tapAttacher) {
        List<String> channelNames = graph.nodes().stream()
            .filter(n -> n.type().equals("channel"))
            .map(GraphNode::name)
            .toList();
        for (String channelName : channelNames) {
            tapAttacher.accept(channelName);
        }
        System.out.println("Attached debug taps to " + channelNames.size() + " channels: " + channelNames);
    }

    public static void main(String[] args) {
        Graph graph = buildGraph(
            List.of(
                new GraphNode("orderChannel", "channel"),
                new GraphNode("validationFilter", "filter"),
                new GraphNode("paymentChannel", "channel"),
                new GraphNode("chargeHandler", "service-activator")),
            List.of(
                new GraphLink("orderChannel", "validationFilter"),
                new GraphLink("validationFilter", "paymentChannel"),
                new GraphLink("paymentChannel", "chargeHandler")));

        attachDebugTapToAllChannels(graph, channelName ->
            System.out.println("  (simulated: WireTap attached to " + channelName + ")"));
    }
}
```

How to run: `java GraphServerDemo.java`. Expected output: two "(simulated: WireTap attached to ...)" lines for `orderChannel` and `paymentChannel`, followed by `Attached debug taps to 2 channels: [orderChannel, paymentChannel]` — the filter and service-activator nodes correctly excluded since only channels were targeted, demonstrating how querying the graph programmatically enables bulk operations across every discovered channel without hardcoding their names anywhere in the debugging code.

## 6. Walkthrough

Trace how the graph is built and then consumed for both validation and bulk tooling.

1. **Application startup**: as the Spring application context initializes, all the beans representing channels, endpoints, and adapters get registered normally, exactly as they would with or without `IntegrationGraphServer` involved at all.
2. **Graph construction on demand**: when `getGraph()` is called (whether from the Actuator endpoint's handler, or directly from application code), `IntegrationGraphServer` introspects the current application context, identifying every relevant bean and the connections between them, and assembles this into a structured `Graph` object of nodes and links.
3. **Startup validation consumption**: an `ApplicationRunner` (or a test) calls `getGraph()` right after startup and asserts on its contents — checking that an expected channel exists, as in Level 2 — failing fast and loudly if the actual runtime structure doesn't match what the deployment expected, rather than discovering the gap later through a silently-dropped message.
4. **Bulk-tooling consumption**: separately, debugging or monitoring code calls `getGraph()` to enumerate every channel (or endpoint of some other specific type) currently present, then performs some bulk action across all of them — attaching a temporary wire tap for a live debugging session, for instance — without needing a hardcoded list of channel names maintained separately from the actual flow configuration.
5. **HTTP consumption (the more common path)**: the Actuator `integrationgraph` endpoint (card 0090) performs essentially the same `getGraph()` call internally and simply serializes the result as JSON for external tools, making this the same underlying mechanism whether accessed via HTTP or directly in code.
6. **Always current**: because the graph is built fresh from the live application context each time `getGraph()` is called, it always reflects whatever the actual current wiring is — including any changes from dynamically added or removed components — rather than a stale snapshot taken once at startup and never refreshed.

```
application starts -> beans registered (channels, endpoints, adapters)
  getGraph() called (Actuator endpoint OR direct application code)
    -> IntegrationGraphServer introspects live context
      -> Graph{nodes, links} assembled fresh, every call
        -> Actuator: serialize as JSON for HTTP consumers
        -> direct code: validate structure / enumerate for bulk operations
```

## 7. Gotchas & takeaways

> **Gotcha:** because `getGraph()` introspects the *live* application context at call time, calling it before all relevant beans have finished initializing (very early in startup, or from within another bean's own constructor) can return an incomplete graph missing components that get registered moments later — call it from a point in the lifecycle (like an `ApplicationRunner`, which runs after the context is fully refreshed) where the full context is guaranteed to be ready.

- `IntegrationGraphServer` is the underlying mechanism; the Actuator `integrationgraph` endpoint (card 0090) is simply one consumer of it exposed over HTTP — reach for direct `IntegrationGraphServer` injection when the graph needs to be consumed programmatically rather than just viewed by a human.
- Startup-time structural validation against the graph catches a class of configuration mistakes (a channel that was supposed to be wired in under certain profiles but wasn't) that unit tests focused on individual components might miss entirely, since those tests typically don't exercise the full assembled context.
- Enumerating channels or endpoints via the graph, rather than maintaining a separately-hardcoded list, keeps debugging or monitoring tooling automatically in sync with the actual flow configuration as it evolves — no risk of the tooling's list silently drifting out of date.
- The graph reflects structure, not live activity — pair it with the MBean-exposed metrics discussed in card 0090 when the question is "what's actually happening right now" rather than "what does the wiring look like."

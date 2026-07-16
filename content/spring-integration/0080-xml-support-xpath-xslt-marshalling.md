---
card: spring-integration
gi: 80
slug: xml-support-xpath-xslt-marshalling
title: "XML support (XPath, XSLT, marshalling)"
---

## 1. What it is

XML support bundles several XML-specific components beyond the basic object-to-XML transformer touched on in card 0078: XPath expression evaluation (`XPathTransformer`, `XPathFilter`, `XPathRouter`) for extracting or routing on values inside an XML payload, XSLT transformation (`XsltPayloadTransformer`) for restructuring one XML document into a different XML shape using a stylesheet, and marshalling/unmarshalling support for converting between XML and Java objects using a pluggable `Marshaller` (JAXB, or others). Together they let a flow work with XML documents at whatever level of abstraction the task needs — raw text, XPath-selected fragments, restructured XML, or fully-typed objects.

## 2. Why & when

You reach for these XML-specific tools when a payload is XML and the task is something more specific than a flat object-to-XML round trip:

- **Only a specific value or fragment inside a larger XML document is needed** — an `XPathTransformer` extracting `/order/customer/@id` avoids fully unmarshalling a large or only-partially-relevant document into a full object graph just to read one field.
- **Routing decisions depend on XML content** — an `XPathRouter` can send a message down different paths in the flow depending on an XPath expression's result (an order's `<priority>` element, for instance), without needing a full object model just to make that one routing decision.
- **The XML shape needs restructuring, not just parsing** — when a partner system's XML schema differs from the flow's internal shape, an `XsltPayloadTransformer` applying a stylesheet can reshape one XML document into another directly, without round-tripping through a Java object model at all.

## 3. Core concept

Think of a large XML document as a filled-out multi-page form. Full marshalling/unmarshalling is like transcribing the entire form into a structured database record — thorough, but overkill if all that's needed is one field. XPath is like using a table of contents to jump straight to one specific field on one specific page without reading the rest. XSLT is like handing the whole form to a clerk with a rulebook (the stylesheet) that rewrites it into an entirely different form layout, field by field, without a human ever needing to read the content in between.

```java
@Bean
public IntegrationFlow xpathRoutingFlow() {
    return IntegrationFlow.from("incomingOrders")
        .route(Xml.xpathRouter("/order/priority/text()"),
            spec -> spec
                .channelMapping("URGENT", "urgentOrdersChannel")
                .channelMapping("STANDARD", "standardOrdersChannel"))
        .get();
}
```

The router reads just the `<priority>` value via XPath to decide the channel, without needing to unmarshal the entire order document into a Java object first.

## 4. Diagram

<svg viewBox="0 0 640 160" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="XPath extracts a single value from an XML document without full parsing; XSLT restructures a whole document into a different XML shape; marshalling converts fully between XML and a Java object" >
  <rect x="10" y="20" width="195" height="120" rx="8" fill="#0d1117" stroke="#6db33f" stroke-width="1.5"/>
  <text x="107" y="12" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">XPath</text>
  <text x="25" y="45" fill="#e6edf3" font-size="7" font-family="monospace">whole XML doc</text>
  <text x="25" y="70" fill="#79c0ff" font-size="7" font-family="monospace">-&gt; one extracted value</text>
  <text x="25" y="100" fill="#8b949e" font-size="7" font-family="sans-serif">no full object needed</text>

  <rect x="222" y="20" width="195" height="120" rx="8" fill="#0d1117" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="319" y="12" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">XSLT</text>
  <text x="237" y="45" fill="#e6edf3" font-size="7" font-family="monospace">XML doc (shape A)</text>
  <text x="237" y="70" fill="#6db33f" font-size="7" font-family="monospace">-&gt; XML doc (shape B)</text>
  <text x="237" y="100" fill="#8b949e" font-size="7" font-family="sans-serif">stays XML throughout</text>

  <rect x="434" y="20" width="195" height="120" rx="8" fill="#0d1117" stroke="#8b949e" stroke-width="1.5"/>
  <text x="531" y="12" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">Marshalling</text>
  <text x="449" y="45" fill="#e6edf3" font-size="7" font-family="monospace">XML doc</text>
  <text x="449" y="70" fill="#79c0ff" font-size="7" font-family="monospace">-&gt; full Java object</text>
  <text x="449" y="100" fill="#8b949e" font-size="7" font-family="sans-serif">full round trip, both ways</text>
</svg>

Three tools, three levels of engagement with an XML document: a peek, a reshape, or a full translation.

## 5. Runnable example

The scenario: routing orders by priority read from XML, then restructuring the accepted ones into a partner's expected shape, simulated with simple string-based XML handling standing in for real XPath/XSLT processors (no real XML parser or XSLT engine needed to demonstrate the extract-then-route-then-restructure pattern), starting with a basic XPath-style extraction, then adding routing based on the extracted value, then adding a restructuring step for the routed message.

### Level 1 — Basic

```java
// XmlToolsDemo.java
public class XmlToolsDemo {
    // Stand-in for an XPathTransformer reading "/order/priority/text()".
    static String extractPriority(String orderXml) {
        return orderXml.replaceAll(".*<priority>([^<]+)</priority>.*", "$1");
    }

    public static void main(String[] args) {
        String orderXml = "<order><id>1</id><priority>URGENT</priority></order>";
        String priority = extractPriority(orderXml);
        System.out.println("Extracted priority: " + priority);
    }
}
```

How to run: `java XmlToolsDemo.java`. Expected output: `Extracted priority: URGENT` — a single value pulled out of the larger document without touching anything else in it.

### Level 2 — Intermediate

```java
// XmlToolsDemo.java
public class XmlToolsDemo {
    static String extractPriority(String orderXml) {
        return orderXml.replaceAll(".*<priority>([^<]+)</priority>.*", "$1");
    }

    // Real-world concern: the extracted value drives a routing decision, without ever needing
    // to unmarshal the full order into a Java object just to make that one decision.
    static void routeByPriority(String orderXml) {
        String priority = extractPriority(orderXml);
        switch (priority) {
            case "URGENT" -> System.out.println("Routed to urgentOrdersChannel: " + orderXml);
            case "STANDARD" -> System.out.println("Routed to standardOrdersChannel: " + orderXml);
            default -> System.out.println("Unknown priority '" + priority + "', routed to errorChannel");
        }
    }

    public static void main(String[] args) {
        routeByPriority("<order><id>1</id><priority>URGENT</priority></order>");
        routeByPriority("<order><id>2</id><priority>STANDARD</priority></order>");
        routeByPriority("<order><id>3</id><priority>UNKNOWN_VALUE</priority></order>");
    }
}
```

How to run: `java XmlToolsDemo.java`. Expected output: the first two orders route to their respective named channels; the third, with an unrecognized priority value, routes to `errorChannel` — the router handling an unexpected value explicitly rather than crashing or silently defaulting somewhere unnoticed.

### Level 3 — Advanced

```java
// XmlToolsDemo.java
public class XmlToolsDemo {
    static String extractPriority(String orderXml) {
        return orderXml.replaceAll(".*<priority>([^<]+)</priority>.*", "$1");
    }

    static String extractId(String orderXml) {
        return orderXml.replaceAll(".*<id>([^<]+)</id>.*", "$1");
    }

    // Stand-in for an XsltPayloadTransformer: reshapes internal XML into a partner's expected
    // schema (different element names, different nesting) without going through a Java object.
    static String restructureForPartner(String orderXml) {
        String id = extractId(orderXml);
        String priority = extractPriority(orderXml);
        return "<PartnerOrder><OrderRef>" + id + "</OrderRef><Urgency>"
            + (priority.equals("URGENT") ? "1" : "5") + "</Urgency></PartnerOrder>";
    }

    // Production concern: only urgent orders get forwarded to the partner system (which charges
    // per urgent-order notification), so route first, then restructure only what's routed.
    static void routeAndForward(String orderXml) {
        String priority = extractPriority(orderXml);
        if (priority.equals("URGENT")) {
            String partnerXml = restructureForPartner(orderXml);
            System.out.println("Forwarded to partner: " + partnerXml);
        } else {
            System.out.println("Not urgent, archived internally: " + orderXml);
        }
    }

    public static void main(String[] args) {
        routeAndForward("<order><id>1</id><priority>URGENT</priority></order>");
        routeAndForward("<order><id>2</id><priority>STANDARD</priority></order>");
    }
}
```

How to run: `java XmlToolsDemo.java`. Expected output: the urgent order prints `Forwarded to partner: <PartnerOrder><OrderRef>1</OrderRef><Urgency>1</Urgency></PartnerOrder>` — reshaped into the partner's element names and a coded urgency value — while the standard order is archived internally without ever being restructured, demonstrating XPath-based routing deciding which documents even need the XSLT-style restructuring step at all.

## 6. Walkthrough

Trace an order through extraction, routing, and conditional restructuring.

1. **Message arrives**: an XML order document enters the flow's input channel from an upstream source (an HTTP gateway, a file adapter, a JMS listener).
2. **XPath extraction for routing**: rather than fully unmarshalling the document, an `XPathRouter` (or, as modeled here, a plain extraction function) reads just the `<priority>` value to decide which channel the message should go to next.
3. **Branch: standard priority**: for a standard-priority order, the flow archives it internally, with the XML payload untouched — no restructuring needed since it isn't going anywhere requiring a different shape.
4. **Branch: urgent priority**: for an urgent order, the flow applies an XSLT-style restructuring step, transforming the internal XML shape into the partner system's expected schema — different element names, a coded urgency value instead of a text label — entirely within the XML domain, with no intermediate Java object needed.
5. **Forward to partner**: the restructured XML document is sent onward to the partner system, which reads it as though it had been generated natively in that shape all along.
6. **Where full marshalling fits**: if a later step in either branch needed to run business logic against multiple fields of the order (not just read one value or reshape the document), a marshalling step (JAXB-based `Marshaller`/`Unmarshaller`) would convert the XML into a fully-typed Java object at that point — used only where the task genuinely needs the full object graph, not by default for every XML-touching step.

```
XML order arrives
  -> XPathRouter reads /order/priority/text()
       STANDARD -> archive as-is (XML untouched)
       URGENT   -> XSLT-style restructure -> partner's XML schema
                     -> forward to partner system
```

## 7. Gotchas & takeaways

> **Gotcha:** an XPath expression written against one XML namespace or schema version silently returns nothing (rather than erroring) if the incoming document uses a different namespace or a renamed element — always validate that an XPath-based router or transformer has an explicit "no match" branch, since a document that simply doesn't have the expected element can otherwise fail silently rather than loudly.

- Reach for XPath specifically when only a fragment of a document is needed, not as a lightweight substitute for full parsing when the flow actually needs to work with many fields — a router or filter needing several fields is often a sign full marshalling is the more maintainable choice.
- XSLT restructuring keeps everything in the XML domain and can be more efficient than round-tripping through a Java object model purely to reshape a document, but stylesheets themselves can become complex and hard to test compared to equivalent code operating on typed objects.
- Full marshalling/unmarshalling via JAXB or another `Marshaller` is the right tool when the flow's logic genuinely needs a typed object graph to work with — validating multiple related fields together, applying business rules that span several elements, or handing the object to non-XML-aware application code.
- All three tools can coexist in the same flow, applied at different points depending on what each step actually needs — extracting with XPath to route, reshaping with XSLT for a partner-facing branch, and fully marshalling only where downstream logic requires a rich object model.

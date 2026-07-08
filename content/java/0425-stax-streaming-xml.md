---
card: java
gi: 425
slug: stax-streaming-xml
title: StAX streaming XML
---

## 1. What it is

StAX (Streaming API for XML, `javax.xml.stream`), added in Java 6, is a **pull-based**, streaming approach to reading and writing XML. Unlike DOM (which loads an entire XML document into memory as a tree before you can touch it) and unlike SAX (which pushes events at your callback whether you're ready or not), StAX lets *your code* pull the next event when it's ready, via `XMLStreamReader.next()` — you stay in control of the loop, and only ever hold as much of the document in memory as you choose to.

## 2. Why & when

DOM is convenient (random access, easy to navigate up and down the tree) but requires holding the *entire* parsed document in memory — for a multi-gigabyte XML file, this can exhaust available memory before parsing even finishes. SAX solves the memory problem (it's event-driven and streaming) but its callback-based model (`startElement`, `characters`, `endElement` methods you override) is awkward for anything requiring state across multiple elements — you end up hand-rolling a state machine with instance fields tracking "where am I in the document."

StAX gets the memory efficiency of SAX with a much more natural programming model: a simple `while (reader.hasNext())` loop that pulls one event at a time, letting you write ordinary imperative code (loops, conditionals, local variables) to track context, rather than scattering state across callback methods. You reach for StAX whenever you need to process large XML documents without loading them entirely into memory, or whenever you're building lower-level XML tooling (as the previous two tutorials did) where DOM's overhead isn't justified.

## 3. Core concept

```java
import javax.xml.stream.*;

// Writing: push events out, one call at a time
XMLStreamWriter writer = XMLOutputFactory.newInstance().createXMLStreamWriter(someWriter);
writer.writeStartElement("order");
writer.writeCharacters("some text");
writer.writeEndElement();

// Reading: pull events in, one call at a time -- YOU control the loop
XMLStreamReader reader = XMLInputFactory.newInstance().createXMLStreamReader(someReader);
while (reader.hasNext()) {
    int event = reader.next(); // advances to the next token: START_ELEMENT, CHARACTERS, END_ELEMENT, etc.
    if (event == XMLStreamConstants.START_ELEMENT) {
        System.out.println("Entering: " + reader.getLocalName());
    }
}
```

The reader never holds the whole document in memory — at any point, it only knows about the current event and whatever your own code chose to remember in local variables.

## 4. Diagram

<svg viewBox="0 0 640 180" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="DOM loads the entire document into a tree in memory before you can use it; StAX pulls one event at a time, only holding the current position, giving constant memory use regardless of document size">
  <rect x="8" y="8" width="624" height="164" rx="8" fill="#0d1117"/>
  <text x="20" y="26" fill="#f85149" font-size="11" font-family="sans-serif">DOM: parse EVERYTHING into a tree first, then read it</text>
  <rect x="30" y="38" width="560" height="26" rx="4" fill="#1c2430" stroke="#f85149"/><text x="310" y="56" fill="#f85149" font-size="9" text-anchor="middle" font-family="sans-serif">entire document in memory as a tree, however large it is</text>

  <text x="20" y="100" fill="#6db33f" font-size="11" font-family="sans-serif">StAX: pull ONE event at a time, discard as you go</text>
  <rect x="30" y="112" width="60" height="26" fill="#1c2430" stroke="#6db33f"/><text x="60" y="130" fill="#6db33f" font-size="9" text-anchor="middle">event 1</text>
  <rect x="100" y="112" width="60" height="26" fill="#1c2430" stroke="#8b949e" stroke-dasharray="3,2"/><text x="130" y="130" fill="#8b949e" font-size="9" text-anchor="middle">event 2</text>
  <rect x="170" y="112" width="60" height="26" fill="#1c2430" stroke="#8b949e" stroke-dasharray="3,2"/><text x="200" y="130" fill="#8b949e" font-size="9" text-anchor="middle">event N</text>
  <text x="320" y="155" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">Memory use stays roughly constant, regardless of document size.</text>
</svg>

DOM trades memory for convenience; StAX trades a small amount of manual state-tracking for constant memory use.

## 5. Runnable example

Scenario: processing a growing order-export document — the same document, evolved from writing a small XML document with StAX, through streaming-reading it back with a pull loop, to handling a larger, more deeply nested document (multiple orders, each with line items) while tracking running totals without ever holding the whole thing in memory as a tree.

### Level 1 — Basic

```java
import javax.xml.stream.*;
import java.io.StringWriter;

public class OrdersXmlWrite {
    public static void main(String[] args) throws Exception {
        StringWriter sw = new StringWriter();
        XMLStreamWriter writer = XMLOutputFactory.newInstance().createXMLStreamWriter(sw);

        writer.writeStartDocument("UTF-8", "1.0");
        writer.writeStartElement("order");
        writer.writeAttribute("id", "1001");
        writer.writeStartElement("customer");
        writer.writeCharacters("Alice");
        writer.writeEndElement();
        writer.writeStartElement("total");
        writer.writeCharacters("59.99");
        writer.writeEndElement();
        writer.writeEndElement();
        writer.writeEndDocument();
        writer.close();

        System.out.println(sw);
    }
}
```

**How to run:** `java OrdersXmlWrite.java`

Each `writeStartElement`/`writeCharacters`/`writeEndElement` call pushes exactly one piece of the document out immediately — there's no in-memory tree being built up first; the `StringWriter` here is just standing in for wherever the XML ultimately needs to go (a file, a network socket).

### Level 2 — Intermediate

```java
import javax.xml.stream.*;
import java.io.StringReader;

public class OrdersXmlRead {
    public static void main(String[] args) throws Exception {
        String xml = "<order id=\"1001\"><customer>Alice</customer><total>59.99</total></order>";

        XMLStreamReader reader = XMLInputFactory.newInstance().createXMLStreamReader(new StringReader(xml));

        String currentElement = null;
        while (reader.hasNext()) {
            int event = reader.next();
            switch (event) {
                case XMLStreamConstants.START_ELEMENT -> {
                    currentElement = reader.getLocalName();
                    if (currentElement.equals("order")) {
                        System.out.println("Order ID (attribute): " + reader.getAttributeValue(null, "id"));
                    }
                }
                case XMLStreamConstants.CHARACTERS -> {
                    String text = reader.getText().trim();
                    if (!text.isEmpty()) System.out.println(currentElement + " = " + text);
                }
                default -> { /* ignore END_ELEMENT, whitespace-only events, etc. for this simple pass */ }
            }
        }
        reader.close();
    }
}
```

**How to run:** `java OrdersXmlRead.java`

The `while (reader.hasNext())` loop pulls events one at a time; ordinary local variables (`currentElement`) track context between iterations — no callback methods, no instance-field state machine, just a normal imperative loop.

### Level 3 — Advanced

```java
import javax.xml.stream.*;
import java.io.StringReader;

public class OrdersXmlAggregate {
    public static void main(String[] args) throws Exception {
        String xml =
            "<orders>" +
            "  <order id=\"1001\"><item qty=\"2\" price=\"10.00\"/><item qty=\"1\" price=\"5.00\"/></order>" +
            "  <order id=\"1002\"><item qty=\"3\" price=\"7.50\"/></order>" +
            "</orders>";

        XMLStreamReader reader = XMLInputFactory.newInstance().createXMLStreamReader(new StringReader(xml));

        String currentOrderId = null;
        double currentOrderTotal = 0;
        double grandTotal = 0;

        while (reader.hasNext()) {
            int event = reader.next();
            if (event == XMLStreamConstants.START_ELEMENT) {
                String name = reader.getLocalName();
                if (name.equals("order")) {
                    currentOrderId = reader.getAttributeValue(null, "id");
                    currentOrderTotal = 0;
                } else if (name.equals("item")) {
                    int qty = Integer.parseInt(reader.getAttributeValue(null, "qty"));
                    double price = Double.parseDouble(reader.getAttributeValue(null, "price"));
                    currentOrderTotal += qty * price; // running total for THIS order, held in a local variable
                }
            } else if (event == XMLStreamConstants.END_ELEMENT && reader.getLocalName().equals("order")) {
                System.out.printf("Order %s total: %.2f%n", currentOrderId, currentOrderTotal);
                grandTotal += currentOrderTotal;
            }
        }
        reader.close();

        System.out.printf("Grand total across all orders: %.2f%n", grandTotal);
    }
}
```

**How to run:** `java OrdersXmlAggregate.java`

Even with nested structure (multiple `<order>` elements, each containing multiple `<item>` elements), the streaming pull loop needs only a handful of local variables (`currentOrderId`, `currentOrderTotal`, `grandTotal`) to track running state — the document could contain a million orders and this code's memory use would stay essentially the same, since it never builds a tree of the whole thing.

## 6. Walkthrough

Execution starts in `main` of the Level 3 example. `reader` streams over the `xml` string containing two `<order>` elements. `currentOrderId`, `currentOrderTotal`, and `grandTotal` all start at their initial values (`null`, `0`, `0`).

The loop's first meaningful `START_ELEMENT` is `"orders"` (the outer wrapper) — neither `"order"` nor `"item"`, so no branch fires. Next is `START_ELEMENT` `"order"` with attribute `id="1001"` — `currentOrderId` becomes `"1001"`, and `currentOrderTotal` resets to `0` for this new order.

Next, `START_ELEMENT` `"item"` with `qty="2"` and `price="10.00"` — `qty * price = 2 * 10.00 = 20.0`, added to `currentOrderTotal`, making it `20.0`. The next `START_ELEMENT` `"item"` (`qty="1"`, `price="5.00"`) adds `1 * 5.00 = 5.0`, bringing `currentOrderTotal` to `25.0`.

`END_ELEMENT` `"order"` fires next (closing the first order): the code prints `"Order 1001 total: 25.00"` and adds `currentOrderTotal` (`25.0`) into `grandTotal`, making it `25.0`.

The second `<order id="1002">` begins: `currentOrderId` becomes `"1002"`, `currentOrderTotal` resets to `0`. Its single `<item qty="3" price="7.50"/>` adds `3 * 7.50 = 22.5`, making `currentOrderTotal = 22.5`. On this order's `END_ELEMENT`, `"Order 1002 total: 22.50"` is printed, and `grandTotal` becomes `25.0 + 22.5 = 47.5`.

After the loop finishes (the closing `</orders>` produces one more `END_ELEMENT` that doesn't match `"order"`, so it's ignored), the final `grandTotal` is printed.

Expected output:
```
Order 1001 total: 25.00
Order 1002 total: 22.50
Grand total across all orders: 47.50
```

## 7. Gotchas & takeaways

> `reader.getText()` for a `CHARACTERS` event can return **whitespace-only** text (indentation and newlines between elements in a pretty-printed document) — always `.trim()` and check `isEmpty()` before treating it as meaningful content, exactly as the Level 2 example does. Forgetting this is one of the most common StAX bugs, producing spurious blank "values" for elements that have none.

- StAX is **pull-based**: your code calls `reader.next()` to advance, staying in control of the loop — unlike SAX's push-based callbacks, which hand control to the parser.
- Memory use stays roughly constant regardless of document size, since only the current parsing position (plus whatever your own local variables track) is held at any moment — unlike DOM, which loads the entire document as an in-memory tree first.
- `XMLStreamWriter` mirrors this on the output side: each `writeStartElement`/`writeCharacters`/`writeEndElement` call emits its piece immediately rather than building up an in-memory structure to serialize later.
- Tracking state across nested elements (like a running per-order total inside a larger `<orders>` document) is done with ordinary local variables reset at the right `START_ELEMENT`/`END_ELEMENT` boundaries — no special StAX feature is needed for this, just careful loop logic.
- StAX is the foundation the earlier JAXB and JAX-WS stand-in examples were built on — understanding it directly demystifies what higher-level XML frameworks are doing underneath.

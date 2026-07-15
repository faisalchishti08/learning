---
card: spring-integration
gi: 56
slug: web-services-ws-support
title: "Web Services (WS) support"
---

## 1. What it is

Web Services support (`SimpleWebServiceInboundGateway`/`SimpleWebServiceOutboundGateway`, built on Spring Web Services) provides gateways for SOAP-based web services — an older, XML-envelope-based, contract-first (typically WSDL-defined) style of HTTP-transported service, distinct from the JSON-over-HTTP REST style the plain HTTP support (card 0054) is usually used for. An inbound WS gateway receives a SOAP request, extracts its content into the flow, and wraps the flow's result back into a SOAP response envelope; an outbound WS gateway does the mirror, constructing a SOAP request to call an external SOAP service and unwrapping its response.

## 2. Why & when

You reach for WS support specifically when the integration point genuinely speaks SOAP rather than plain REST-style HTTP:

- **You're integrating with an older enterprise system or a partner whose only exposed interface is a SOAP web service** — many established enterprise systems (especially in banking, insurance, government, and large legacy ERP deployments) still expose SOAP interfaces, defined by a formal WSDL contract, rather than REST APIs; WS support is what lets a flow speak that specific protocol.
- **A formal, machine-readable service contract (WSDL/XSD) already exists and needs to be honored** — SOAP's contract-first tradition means the message structure is often rigidly specified in advance, and WS support handles the XML envelope construction/parsing needed to conform to that contract.
- **The integration needs SOAP-specific features** — WS-Security headers, SOAP faults (SOAP's structured error-reporting mechanism, distinct from plain HTTP status codes), or other SOAP-stack capabilities not present in plain REST-style HTTP.

## 3. Core concept

Think of a SOAP message like a formal, legally-binding letter sent in a specific, regulation-mandated envelope format — the envelope itself has required sections (a header for metadata, a body for the actual content, a fault section for structured errors), and the letter's exact content must conform to a pre-agreed template (the WSDL contract) both parties have already signed off on. Plain REST-style HTTP (card 0054), by contrast, is more like an informal email — flexible content, no mandated envelope structure, agreed upon loosely between the two parties rather than through a formal, pre-published contract.

```java
@Bean
public IntegrationFlow soapInboundFlow() {
    return IntegrationFlow.from(Ws.simpleInboundGateway())
        .transform(Ws.marshallingTransformer(orderRequestMarshaller())) // XML envelope -> domain object
        .handle((OrderRequest req, headers) -> orderService.process(req)) // returns the domain response object
        .transform(Ws.marshallingTransformer(orderResponseMarshaller())) // domain object -> XML envelope
        .get();
}
```

The flow's own business logic (`orderService.process(req)`) works with plain domain objects — the SOAP-specific XML envelope marshalling/unmarshalling is handled entirely at the boundary, using the same general adapter-vs-channel separation described in card 0018.

## 4. Diagram

<svg viewBox="0 0 640 170" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="A SOAP request's XML envelope is unmarshalled into a domain object for the flow to process; the flow's response domain object is marshalled back into a SOAP response envelope">
  <rect x="20" y="60" width="150" height="50" rx="6" fill="#1c2430" stroke="#8b949e" stroke-width="1.5"/>
  <text x="95" y="82" fill="#e6edf3" font-size="8" text-anchor="middle" font-family="sans-serif">SOAP envelope</text>
  <text x="95" y="97" fill="#8b949e" font-size="6" text-anchor="middle" font-family="sans-serif">Header + Body + Fault</text>

  <line x1="170" y1="85" x2="230" y2="85" stroke="#6db33f" stroke-width="2" marker-end="url(#ws1)"/>
  <text x="200" y="70" fill="#6db33f" font-size="6" text-anchor="middle" font-family="sans-serif">unmarshal</text>

  <rect x="240" y="60" width="150" height="50" rx="6" fill="#1c2430" stroke="#79c0ff" stroke-width="2"/>
  <text x="315" y="88" fill="#e6edf3" font-size="8" text-anchor="middle" font-family="sans-serif">domain object</text>

  <line x1="390" y1="85" x2="450" y2="85" stroke="#79c0ff" stroke-width="2" marker-end="url(#ws2)"/>
  <text x="420" y="70" fill="#79c0ff" font-size="6" text-anchor="middle" font-family="sans-serif">marshal</text>

  <rect x="460" y="60" width="150" height="50" rx="6" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="535" y="82" fill="#e6edf3" font-size="8" text-anchor="middle" font-family="sans-serif">SOAP response</text>
  <text x="535" y="97" fill="#8b949e" font-size="6" text-anchor="middle" font-family="sans-serif">envelope</text>

  <defs>
    <marker id="ws1" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#6db33f"/></marker>
    <marker id="ws2" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#79c0ff"/></marker>
  </defs>
</svg>

XML envelope marshalling/unmarshalling happens entirely at the boundary; the flow's own logic works with plain domain objects throughout.

## 5. Runnable example

The scenario: a legacy order-lookup SOAP service, using plain Java XML processing (genuinely runnable, standing in for Spring WS's marshalling infrastructure), starting with a basic envelope construction/parsing, then unmarshalling into a domain object, and finally a SOAP fault representing a structured error response.

### Level 1 — Basic

```java
// BasicSoapEnvelopeDemo.java
// Uses plain java.xml processing to construct and parse a SOAP-style envelope, standing in for
// Spring WS's marshalling infrastructure, since that requires the full spring-ws dependency.
public class BasicSoapEnvelopeDemo {
    static String buildSoapRequest(String orderId) {
        return """
            <soap:Envelope xmlns:soap="http://schemas.xmlsoap.org/soap/envelope/">
              <soap:Body>
                <GetOrderRequest><orderId>%s</orderId></GetOrderRequest>
              </soap:Body>
            </soap:Envelope>""".formatted(orderId);
    }

    static String extractOrderId(String soapRequest) {
        // what a real WS inbound gateway's XML parsing does for you: pull content OUT of the envelope
        int start = soapRequest.indexOf("<orderId>") + "<orderId>".length();
        int end = soapRequest.indexOf("</orderId>");
        return soapRequest.substring(start, end);
    }

    public static void main(String[] args) {
        String request = buildSoapRequest("ORD-1");
        System.out.println("SOAP request envelope:\n" + request);

        String orderId = extractOrderId(request);
        System.out.println("\nExtracted (unmarshalled) orderId for the FLOW to process: " + orderId);
    }
}
```

How to run: `java BasicSoapEnvelopeDemo.java`. Expected output: the full SOAP envelope XML printed, followed by `Extracted (unmarshalled) orderId for the FLOW to process: ORD-1` — the flow's actual processing logic only ever needs to work with the plain extracted value, never the surrounding XML envelope structure itself.

### Level 2 — Intermediate

Unmarshalling a full SOAP response into a proper domain object (rather than just extracting one field) and marshalling a domain object back into a response envelope — the round trip a real `Ws.marshallingTransformer` pair performs using a proper XML binding library (like JAXB), simplified here with manual string construction/parsing to remain genuinely self-contained.

```java
// DomainObjectRoundTripDemo.java
public class DomainObjectRoundTripDemo {
    record Order(String id, double amount, String status) {}

    static Order unmarshalOrderResponse(String soapResponse) {
        String id = extractTag(soapResponse, "orderId");
        double amount = Double.parseDouble(extractTag(soapResponse, "amount"));
        String status = extractTag(soapResponse, "status");
        return new Order(id, amount, status);
    }

    static String marshalOrderResponse(Order order) {
        return """
            <soap:Envelope xmlns:soap="http://schemas.xmlsoap.org/soap/envelope/">
              <soap:Body>
                <GetOrderResponse>
                  <orderId>%s</orderId><amount>%.2f</amount><status>%s</status>
                </GetOrderResponse>
              </soap:Body>
            </soap:Envelope>""".formatted(order.id(), order.amount(), order.status());
    }

    static String extractTag(String xml, String tag) {
        int start = xml.indexOf("<" + tag + ">") + tag.length() + 2;
        int end = xml.indexOf("</" + tag + ">");
        return xml.substring(start, end);
    }

    public static void main(String[] args) {
        String incomingSoapResponse = """
            <soap:Envelope xmlns:soap="http://schemas.xmlsoap.org/soap/envelope/">
              <soap:Body><GetOrderResponse><orderId>ORD-1</orderId><amount>199.99</amount><status>SHIPPED</status></GetOrderResponse></soap:Body>
            </soap:Envelope>""";

        Order order = unmarshalOrderResponse(incomingSoapResponse);
        System.out.println("Unmarshalled domain object: " + order);

        Order updated = new Order(order.id(), order.amount(), "DELIVERED"); // the FLOW's own logic, plain objects only
        String outgoingSoapResponse = marshalOrderResponse(updated);
        System.out.println("\nMarshalled back to SOAP:\n" + outgoingSoapResponse);
    }
}
```

How to run: `java DomainObjectRoundTripDemo.java`. Expected output: `Unmarshalled domain object: Order[id=ORD-1, amount=199.99, status=SHIPPED]`, then a marshalled SOAP envelope reflecting the updated `status=DELIVERED` — the flow's own logic (updating the status) touched only the plain `Order` record; the XML envelope construction happened entirely before and after that logic ran.

### Level 3 — Advanced

A SOAP fault — SOAP's structured mechanism for reporting errors within the envelope itself, distinct from a plain HTTP status code — shown by constructing and detecting a fault response, mirroring how a WS outbound gateway would need to distinguish a successful response from a fault when calling an external SOAP service.

```java
// SoapFaultHandlingDemo.java
public class SoapFaultHandlingDemo {
    static String buildFaultResponse(String faultCode, String faultMessage) {
        return """
            <soap:Envelope xmlns:soap="http://schemas.xmlsoap.org/soap/envelope/">
              <soap:Body>
                <soap:Fault>
                  <faultcode>%s</faultcode>
                  <faultstring>%s</faultstring>
                </soap:Fault>
              </soap:Body>
            </soap:Envelope>""".formatted(faultCode, faultMessage);
    }

    static void handleSoapResponse(String response) {
        // what a WS outbound gateway needs to check: is this a normal response, or a SOAP FAULT?
        if (response.contains("<soap:Fault>")) {
            String faultCode = extractTag(response, "faultcode");
            String faultMessage = extractTag(response, "faultstring");
            System.out.println("SOAP FAULT received — code=" + faultCode + ", message=" + faultMessage);
            System.out.println("(this must be routed to error handling, NOT treated as a successful response)");
        } else {
            System.out.println("Normal SOAP response received, processing as usual");
        }
    }

    static String extractTag(String xml, String tag) {
        int start = xml.indexOf("<" + tag + ">") + tag.length() + 2;
        int end = xml.indexOf("</" + tag + ">");
        return xml.substring(start, end);
    }

    public static void main(String[] args) {
        String faultResponse = buildFaultResponse("soap:Client", "Order ORD-999 not found");
        System.out.println("Received:\n" + faultResponse + "\n");
        handleSoapResponse(faultResponse);
    }
}
```

How to run: `java SoapFaultHandlingDemo.java`. Expected output: the fault XML envelope printed, followed by `SOAP FAULT received — code=soap:Client, message=Order ORD-999 not found` and the note about routing to error handling — a real `SimpleWebServiceOutboundGateway` recognizes a SOAP fault in the response and typically throws a `SoapFaultClientException`, which needs to be handled distinctly from a normal successful response, exactly like the error-channel routing pattern from card 0044.

## 6. Walkthrough

Tracing `DomainObjectRoundTripDemo` in execution order:

1. `incomingSoapResponse` represents a raw SOAP envelope as it would arrive over the wire from an external SOAP service — a complete XML document with the envelope, body, and the actual `GetOrderResponse` content nested inside.
2. `unmarshalOrderResponse` extracts each individual field (`orderId`, `amount`, `status`) from that XML structure using `extractTag`, then constructs a plain `Order` record from those extracted values — this is the exact role Spring WS's `Ws.marshallingTransformer` (backed by a real XML binding framework like JAXB in a production setup) performs automatically, converting the XML structure into a proper domain object.
3. The resulting `Order` is printed — from this point forward, "the flow" (represented here simply as the code constructing `updated`) works entirely with this plain domain object, never touching XML directly.
4. `new Order(order.id(), order.amount(), "DELIVERED")` represents the flow's own business logic — updating the order's status — operating purely on the plain record, with zero XML or SOAP-specific code involved in this step at all.
5. `marshalOrderResponse(updated)` takes that updated domain object and constructs a fresh SOAP envelope reflecting its current state — this is the mirror operation to step 2, converting a domain object back into the XML shape an external SOAP consumer would expect.
6. The final printed envelope shows `status=DELIVERED`, confirming that the business-logic update made purely to the plain domain object correctly flowed through to the final marshalled XML output — exactly the boundary separation the WS support's marshalling transformers provide: XML concerns confined to the edges, plain objects everywhere in between.

```
incoming SOAP XML --[unmarshal]--> Order(status=SHIPPED) --[flow logic: update]--> Order(status=DELIVERED) --[marshal]--> outgoing SOAP XML
```

## 7. Gotchas & takeaways

> A SOAP fault is not the same thing as an HTTP error status code — a SOAP service commonly returns HTTP 200 (or another "successful" HTTP status) while the response body itself contains a `<soap:Fault>` element describing an application-level error. Code that only checks the HTTP status code (as plain HTTP support, card 0054, might naturally do) can completely miss a SOAP fault and mistakenly treat a failed operation as successful — always inspect the response body for a fault element specifically when integrating with SOAP services, exactly as `SimpleWebServiceOutboundGateway` does internally.

- WS support (`SimpleWebServiceInboundGateway`/`SimpleWebServiceOutboundGateway`) provides gateways for SOAP-based, contract-first web services, distinct from the JSON-over-REST style plain HTTP support (card 0054) typically handles.
- Use it when integrating with a system whose only exposed interface is SOAP, typically defined by a formal WSDL contract, common in older enterprise, banking, insurance, and government systems.
- Marshalling transformers convert between the SOAP XML envelope and plain domain objects at the flow's boundary, keeping the flow's own business logic entirely free of XML/SOAP-specific concerns.
- A SOAP fault is a structured, in-body error mechanism distinct from HTTP status codes — a "successful" HTTP response can still contain a SOAP fault describing an application-level failure, and this must be checked explicitly.
- SOAP faults should be routed to dedicated error handling (mirroring the error-channel pattern from card 0044), never silently treated as a normal successful response just because the HTTP-level status code looked fine.

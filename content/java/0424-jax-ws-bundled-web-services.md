---
card: java
gi: 424
slug: jax-ws-bundled-web-services
title: JAX-WS bundled (web services)
---

## 1. What it is

JAX-WS (Java API for XML Web Services) is a framework for exposing plain Java methods as **SOAP-based web services** and for calling remote web services from Java, using annotations like `@WebService` and `@WebMethod` to mark which classes and methods should be exposed. Like JAXB (which it uses internally to convert method arguments and return values to and from XML), JAX-WS was **bundled directly with the JDK starting in Java 6**, making it possible to publish a working SOAP endpoint with a couple of annotations and one line of code (`Endpoint.publish(...)`), with no external application server required.

## 2. Why & when

Before JAX-WS, building a SOAP web service meant hand-writing WSDL (the XML contract describing the service), manually parsing incoming SOAP envelopes, and manually serializing responses back into the SOAP XML format — a large amount of boilerplate for what's conceptually simple: "let a remote caller invoke this method and get the result back." JAX-WS automated all of it: annotate a class, call `Endpoint.publish(address, serviceImpl)`, and the runtime generates the WSDL, handles incoming SOAP requests, converts XML arguments into Java method parameters (via JAXB), invokes the real method, and converts the return value back into a SOAP XML response — all automatically.

Bundling this with the JDK (Java 6 through 8) meant lightweight, embedded SOAP services needed no external dependencies or application server at all — genuinely useful for internal service-to-service communication in that era. **Like JAXB, JAX-WS was removed from the default JDK modules starting in Java 11** (also moved out during Java 9's modularization) — using it today on a modern JDK requires an external dependency. The runnable examples below build a small, hand-rolled stand-in using `com.sun.net.httpserver.HttpServer` (still bundled) and StAX, demonstrating the same underlying mechanics JAX-WS automated: an incoming request is parsed, dispatched to a real Java method, and the result is serialized back — while being explicit that this is a simplified illustration, not real JAX-WS/SOAP.

## 3. Core concept

```java
// What real JAX-WS looked like when it was bundled (Java 6-8) -- shown for reference, not runnable as-is on 11+:
//
// @WebService
// class CalculatorService {
//     @WebMethod public int add(int a, int b) { return a + b; }
// }
//
// Endpoint.publish("http://localhost:8080/calculator", new CalculatorService());
// // A SOAP client anywhere could now call add(3, 4) over the network and get 7 back,
// // with WSDL, XML marshalling, and dispatch all handled automatically.
```

The runnable examples below replace the SOAP/WSDL machinery with a plain HTTP endpoint (using the JDK's built-in `HttpServer`) and hand-rolled XML request/response bodies (using StAX), to demonstrate the request → dispatch → real method call → response mechanics that a real JAX-WS runtime automates.

## 4. Diagram

<svg viewBox="0 0 640 190" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="An incoming request names a method and its arguments; the service dispatches to the matching real Java method via reflection, then serializes the return value back as the response">
  <rect x="8" y="8" width="624" height="174" rx="8" fill="#0d1117"/>
  <rect x="30" y="30" width="150" height="40" rx="6" fill="#1c2430" stroke="#79c0ff"/><text x="105" y="55" fill="#79c0ff" font-size="10" text-anchor="middle" font-family="sans-serif">Request (XML: method+args)</text>

  <rect x="245" y="30" width="150" height="40" rx="6" fill="#1c2430" stroke="#6db33f"/><text x="320" y="55" fill="#6db33f" font-size="10" text-anchor="middle" font-family="sans-serif">Dispatcher (reflection)</text>

  <rect x="460" y="30" width="150" height="40" rx="6" fill="#1c2430" stroke="#e6edf3"/><text x="535" y="55" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">Real Java method</text>

  <line x1="180" y1="50" x2="240" y2="50" stroke="#8b949e" marker-end="url(#aw1)"/>
  <line x1="395" y1="50" x2="455" y2="50" stroke="#8b949e" marker-end="url(#aw1)"/>

  <rect x="245" y="120" width="150" height="40" rx="6" fill="#1c2430" stroke="#f85149"/><text x="320" y="145" fill="#f85149" font-size="10" text-anchor="middle" font-family="sans-serif">Response (XML: result)</text>
  <line x1="535" y1="70" x2="320" y2="118" stroke="#8b949e" marker-end="url(#aw1)"/>
  <defs><marker id="aw1" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#8b949e"/></marker></defs>
</svg>

Request arrives as data (method name and arguments); the framework's job is turning that data into a real method invocation and back.

## 5. Runnable example

Scenario: exposing a tiny calculator "service" over HTTP — the same service, evolved from a query-parameter endpoint returning plain text, through returning a proper XML response body, to a generic dispatcher that reads a method name and arguments from an XML request body and invokes the matching real Java method via reflection, exactly mirroring what a JAX-WS runtime automates from a SOAP envelope.

### Level 1 — Basic

```java
import com.sun.net.httpserver.*;
import java.io.*;
import java.net.*;
import java.util.concurrent.*;

public class MiniWebServiceBasic {
    static String add(int a, int b) {
        return String.valueOf(a + b);
    }

    public static void main(String[] args) throws Exception {
        HttpServer server = HttpServer.create(new InetSocketAddress(0), 0); // port 0 = pick any free port
        server.createContext("/add", exchange -> {
            String query = exchange.getRequestURI().getQuery(); // e.g. "a=3&b=4"
            int a = 0, b = 0;
            for (String pair : query.split("&")) {
                String[] kv = pair.split("=");
                if (kv[0].equals("a")) a = Integer.parseInt(kv[1]);
                if (kv[0].equals("b")) b = Integer.parseInt(kv[1]);
            }
            String response = add(a, b);
            exchange.sendResponseHeaders(200, response.length());
            try (OutputStream os = exchange.getResponseBody()) {
                os.write(response.getBytes());
            }
        });
        ExecutorService executor = Executors.newSingleThreadExecutor();
        server.setExecutor(executor);
        server.start();

        int port = server.getAddress().getPort();
        HttpURLConnection conn = (HttpURLConnection) URI.create(
            "http://localhost:" + port + "/add?a=3&b=4").toURL().openConnection();
        int status = conn.getResponseCode();
        String body = new String(conn.getInputStream().readAllBytes());
        System.out.println("Status: " + status + ", Body: " + body);

        server.stop(0);
        executor.shutdown(); // without this, the executor's thread can keep the JVM alive
    }
}
```

**How to run:** `java MiniWebServiceBasic.java`

`com.sun.net.httpserver.HttpServer` is a minimal, bundled-with-the-JDK HTTP server — a single `createContext` call exposes `add` at `/add`, taking query parameters and returning a plain-text sum. This is the plumbing layer any web service framework, JAX-WS included, is ultimately built on top of.

### Level 2 — Intermediate

```java
import com.sun.net.httpserver.*;
import javax.xml.stream.*;
import java.io.*;
import java.net.*;
import java.util.concurrent.*;

public class MiniWebServiceXml {
    static int add(int a, int b) {
        return a + b;
    }

    static String buildXmlResponse(String operation, int result) throws Exception {
        StringWriter sw = new StringWriter();
        XMLStreamWriter writer = XMLOutputFactory.newInstance().createXMLStreamWriter(sw);
        writer.writeStartDocument();
        writer.writeStartElement("response");
        writer.writeStartElement("operation");
        writer.writeCharacters(operation);
        writer.writeEndElement();
        writer.writeStartElement("result");
        writer.writeCharacters(String.valueOf(result));
        writer.writeEndElement();
        writer.writeEndElement();
        writer.writeEndDocument();
        writer.close();
        return sw.toString();
    }

    public static void main(String[] args) throws Exception {
        HttpServer server = HttpServer.create(new InetSocketAddress(0), 0);
        server.createContext("/add", exchange -> {
            try {
                String query = exchange.getRequestURI().getQuery();
                int a = 0, b = 0;
                for (String pair : query.split("&")) {
                    String[] kv = pair.split("=");
                    if (kv[0].equals("a")) a = Integer.parseInt(kv[1]);
                    if (kv[0].equals("b")) b = Integer.parseInt(kv[1]);
                }
                String xml = buildXmlResponse("add", add(a, b));
                exchange.getResponseHeaders().add("Content-Type", "application/xml");
                exchange.sendResponseHeaders(200, xml.getBytes().length);
                try (OutputStream os = exchange.getResponseBody()) {
                    os.write(xml.getBytes());
                }
            } catch (Exception e) {
                throw new RuntimeException(e);
            }
        });
        ExecutorService executor = Executors.newSingleThreadExecutor();
        server.setExecutor(executor);
        server.start();

        int port = server.getAddress().getPort();
        HttpURLConnection conn = (HttpURLConnection) URI.create(
            "http://localhost:" + port + "/add?a=10&b=5").toURL().openConnection();
        String body = new String(conn.getInputStream().readAllBytes());
        System.out.println("Response body:\n" + body);

        server.stop(0);
        executor.shutdown();
    }
}
```

**How to run:** `java MiniWebServiceXml.java`

The response is now a genuine, structured XML document built with StAX rather than a bare number — closer to what a real SOAP response body looks like (minus the SOAP envelope wrapper itself), and the `Content-Type: application/xml` header correctly advertises this to any caller.

### Level 3 — Advanced

```java
import com.sun.net.httpserver.*;
import javax.xml.stream.*;
import java.io.*;
import java.net.*;
import java.util.concurrent.*;
import java.util.*;
import java.lang.reflect.Method;

public class MiniWebServiceDispatch {

    // The "service" -- just a plain class with plain methods, like a JAX-WS @WebService-annotated class
    static class CalculatorService {
        public int add(int a, int b) { return a + b; }
        public int multiply(int a, int b) { return a * b; }
    }

    // Parses a request body like: <request><method>add</method><a>3</a><b>4</b></request>
    static Map<String, String> parseRequest(String xml) throws Exception {
        Map<String, String> fields = new LinkedHashMap<>();
        XMLStreamReader reader = XMLInputFactory.newInstance().createXMLStreamReader(new StringReader(xml));
        String currentTag = null;
        while (reader.hasNext()) {
            int event = reader.next();
            if (event == XMLStreamConstants.START_ELEMENT) {
                currentTag = reader.getLocalName();
            } else if (event == XMLStreamConstants.CHARACTERS && currentTag != null) {
                String text = reader.getText().trim();
                if (!text.isEmpty()) fields.put(currentTag, text);
            } else if (event == XMLStreamConstants.END_ELEMENT) {
                currentTag = null;
            }
        }
        reader.close();
        return fields;
    }

    static String buildResponse(Object result) throws Exception {
        StringWriter sw = new StringWriter();
        XMLStreamWriter writer = XMLOutputFactory.newInstance().createXMLStreamWriter(sw);
        writer.writeStartDocument();
        writer.writeStartElement("response");
        writer.writeStartElement("result");
        writer.writeCharacters(String.valueOf(result));
        writer.writeEndElement();
        writer.writeEndElement();
        writer.writeEndDocument();
        writer.close();
        return sw.toString();
    }

    public static void main(String[] args) throws Exception {
        CalculatorService service = new CalculatorService();

        HttpServer server = HttpServer.create(new InetSocketAddress(0), 0);
        server.createContext("/service", exchange -> {
            try {
                String requestBody = new String(exchange.getRequestBody().readAllBytes());
                Map<String, String> fields = parseRequest(requestBody);

                String methodName = fields.remove("method");
                // Dynamic dispatch: find the method by name, then invoke it with the remaining fields as int args --
                // this is exactly what a JAX-WS runtime automates from a SOAP envelope, minus the WSDL/SOAP layer.
                Method method = null;
                for (Method m : CalculatorService.class.getMethods()) {
                    if (m.getName().equals(methodName)) { method = m; break; }
                }
                Object[] argValues = fields.values().stream().map(Integer::parseInt).toArray();
                Object result = method.invoke(service, argValues);

                String xmlResponse = buildResponse(result);
                exchange.getResponseHeaders().add("Content-Type", "application/xml");
                exchange.sendResponseHeaders(200, xmlResponse.getBytes().length);
                try (OutputStream os = exchange.getResponseBody()) {
                    os.write(xmlResponse.getBytes());
                }
            } catch (Exception e) {
                throw new RuntimeException(e);
            }
        });
        ExecutorService executor = Executors.newSingleThreadExecutor();
        server.setExecutor(executor);
        server.start();
        int port = server.getAddress().getPort();

        for (String requestXml : List.of(
                "<request><method>add</method><a>3</a><b>4</b></request>",
                "<request><method>multiply</method><a>3</a><b>4</b></request>")) {
            HttpURLConnection conn = (HttpURLConnection) URI.create(
                "http://localhost:" + port + "/service").toURL().openConnection();
            conn.setRequestMethod("POST");
            conn.setDoOutput(true);
            conn.getOutputStream().write(requestXml.getBytes());
            String responseBody = new String(conn.getInputStream().readAllBytes());
            System.out.println("Request: " + requestXml);
            System.out.println("Response: " + responseBody);
        }

        server.stop(0);
        executor.shutdown();
    }
}
```

**How to run:** `java MiniWebServiceDispatch.java`

This is the real payoff: `CalculatorService` is a plain Java class with **no annotations and no per-method HTTP wiring at all**. The dispatcher reads `<method>` and argument values out of the incoming XML, locates the matching method by name via reflection, invokes it, and serializes the return value — exactly the generic "any method, any service class" dispatch mechanism a real JAX-WS runtime provides automatically from `@WebService`/`@WebMethod` annotations and a SOAP envelope.

## 6. Walkthrough

Execution starts in `main` of the Level 3 example. `service` is a plain `CalculatorService` instance. The HTTP server is started on an OS-assigned free port (`port 0`), and its actual assigned port is read back via `server.getAddress().getPort()`.

**First request:** the client sends `POST /service` with body `<request><method>add</method><a>3</a><b>4</b></request>`.

*Server side:* the context handler reads the full request body as a `String`, then calls `parseRequest(requestBody)`. This walks the XML with a StAX reader: on each `START_ELEMENT`, it remembers the tag name (`currentTag`); on each `CHARACTERS` event, if there's a non-blank text and a current tag, it stores `tag -> text` in `fields`. After parsing, `fields` is `{method=add, a=3, b=4}` (in insertion order, since it's a `LinkedHashMap`).

`fields.remove("method")` extracts `"add"` and leaves `fields` as `{a=3, b=4}`. The code then searches `CalculatorService.class.getMethods()` for one named `"add"`, finding the two-`int`-parameter `add` method. `fields.values().stream().map(Integer::parseInt).toArray()` converts the remaining values (`"3"`, `"4"`) into an `Object[]` of boxed `Integer`s: `{3, 4}`. `method.invoke(service, argValues)` calls `service.add(3, 4)` reflectively, returning `7` (auto-boxed as `Integer`).

`buildResponse(7)` writes `<response><result>7</result></response>`, sent back as the HTTP response body with a 200 status.

*Client side:* the response body is read and printed alongside the original request, showing the correct round trip: `add(3, 4) = 7`.

**Second request:** the same flow repeats for `<request><method>multiply</method><a>3</a><b>4</b></request>` — this time the method lookup finds `multiply` instead, `service.multiply(3, 4)` returns `12`, and the response reflects that.

Expected output:
```
Request: <request><method>add</method><a>3</a><b>4</b></request>
Response: <?xml version="1.0" ?><response><result>7</result></response>
Request: <request><method>multiply</method><a>3</a><b>4</b></request>
Response: <?xml version="1.0" ?><response><result>12</result></response>
```

## 7. Gotchas & takeaways

> Just like JAXB (which it depends on internally), real JAX-WS (`javax.xml.ws`/`jakarta.xml.ws`) is **not available on the default classpath of Java 11 and later** — it was bundled from Java 6 through 8 and fully removed in Java 11's modularization. Code using `@WebService`, `@WebMethod`, or `javax.xml.ws.Endpoint` needs external dependencies to compile and run on a modern JDK.

- JAX-WS automated exposing plain Java methods as SOAP web services (`@WebService`, `@WebMethod`, `Endpoint.publish(...)`) and was bundled with the JDK from Java 6 through 8, alongside JAXB for the XML marshalling.
- The core mechanic any RPC-style web service framework provides is: parse an incoming request into a method name and arguments, dispatch to the real method (often via reflection), and serialize the return value back — exactly what the Level 3 example builds by hand.
- `com.sun.net.httpserver.HttpServer`, used here, remains bundled in modern JDKs and is a genuinely useful lightweight HTTP server for small tools, tests, or embedded endpoints — just without any of JAX-WS's SOAP/WSDL machinery.
- Always shut down any `ExecutorService` you give to `HttpServer.setExecutor(...)` — an un-shut-down executor's non-daemon thread can keep the JVM running even after `server.stop(0)` is called.
- On modern JDKs, prefer a maintained web framework (Spring Boot, a plain servlet container, or a REST-focused library) over trying to resurrect JAX-WS/SOAP for new projects — SOAP itself has also fallen out of favor in most new development in favor of REST or gRPC.

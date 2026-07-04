---
card: spring-framework
gi: 286
slug: object-xml-mapping-oxm-abstraction
title: Object/XML Mapping (OXM) Abstraction
---

## 1. What it is

Spring's **Object/XML Mapping (OXM)** module (`spring-oxm`) provides a uniform abstraction over multiple XML binding frameworks — JAXB 2, Castor, XStream, JiBX — through two simple interfaces:

```java
public interface Marshaller {
    void marshal(Object graph, Result result) throws IOException, XmlMappingException;
    boolean supports(Class<?> clazz);
}

public interface Unmarshaller {
    Object unmarshal(Source source) throws IOException, XmlMappingException;
    boolean supports(Class<?> clazz);
}
```

A single implementation class (e.g., `Jaxb2Marshaller`) typically implements both interfaces. Any component that uses the `Marshaller`/`Unmarshaller` interfaces works transparently with any XML framework.

## 2. Why & when

Without OXM, you call JAXB or XStream APIs directly — your service is coupled to the vendor. Swapping frameworks requires rewriting the marshalling code throughout.

The OXM abstraction means:
- Services accept `Marshaller`/`Unmarshaller` — not `JAXBContext` or `XStream`.
- Configuration is in `@Bean` declarations, not scattered through business logic.
- Spring's MVC, WebSocket, and REST templates use OXM interfaces internally — you swap the backing implementation by swapping the bean.

Use OXM when:
- You need to marshal Java objects to XML (or unmarshal XML back).
- You want to decouple your service from a specific XML library.
- You integrate with SOAP web services or legacy XML feeds.
- You want consistent exception handling (`XmlMappingException` hierarchy).

## 3. Core concept

```
Object graph                      XML string / stream
(POJO with @XmlRootElement)             │
        │                               │
  ┌─────▼─────────────────────┐   ┌────▼──────────────────────┐
  │  Marshaller.marshal(obj,  │   │  Unmarshaller.unmarshal(   │
  │    new StreamResult(os))  │   │    new StreamSource(is))   │
  └─────────────────────────┘   └───────────────────────────┘
        │                               │
  ┌─────▼───────────────────────────────▼─────┐
  │         Jaxb2Marshaller (or other)         │
  │  supports(Class) → true/false              │
  │  delegates to JAXBContext.createMarshaller │
  └─────────────────────────────────────────── ┘
```

Result/Source types (standard JAXP):
- `StreamResult(OutputStream)` / `StreamSource(InputStream)` — byte streams.
- `StringResult` / `StringSource` — for in-memory string.
- `DOMResult(Node)` / `DOMSource(Node)` — for DOM manipulation.

`XmlMappingException` hierarchy (analogous to `DataAccessException` for databases):
```
XmlMappingException
  ├─ MarshallingFailureException
  ├─ UnmarshallingFailureException
  └─ MarshallingException (other sub-types)
```

## 4. Diagram

<svg viewBox="0 0 700 195" xmlns="http://www.w3.org/2000/svg">
  <defs>
    <marker id="arr" markerWidth="8" markerHeight="6" refX="8" refY="3" orient="auto">
      <polygon points="0 0,8 3,0 6" fill="#6db33f"/>
    </marker>
  </defs>

  <!-- Service -->
  <rect x="10" y="70" width="130" height="55" rx="6" fill="#1c2430" stroke="#8b949e" stroke-width="1.5"/>
  <text x="75" y="92" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">OrderService</text>
  <line x1="20" y1="98" x2="130" y2="98" stroke="#8b949e" stroke-width="0.5"/>
  <text x="75" y="115" fill="#8b949e" font-size="8" text-anchor="middle" font-family="monospace">@Autowired Marshaller</text>

  <line x1="142" y1="97" x2="185" y2="97" stroke="#6db33f" stroke-width="1.5" marker-end="url(#arr)"/>

  <!-- OXM Interface -->
  <rect x="187" y="55" width="175" height="80" rx="6" fill="#1c2430" stroke="#6db33f" stroke-width="2"/>
  <text x="274" y="78" fill="#6db33f" font-size="9" text-anchor="middle" font-family="sans-serif">«interface»</text>
  <text x="274" y="92" fill="#6db33f" font-size="9" text-anchor="middle" font-family="sans-serif">Marshaller / Unmarshaller</text>
  <line x1="197" y1="98" x2="352" y2="98" stroke="#8b949e" stroke-width="0.5"/>
  <text x="274" y="114" fill="#8b949e" font-size="8" text-anchor="middle" font-family="monospace">marshal(obj, result)</text>
  <text x="274" y="126" fill="#8b949e" font-size="8" text-anchor="middle" font-family="monospace">unmarshal(source)</text>

  <line x1="364" y1="80" x2="407" y2="65" stroke="#6db33f" stroke-width="1.5" marker-end="url(#arr)"/>
  <line x1="364" y1="110" x2="407" y2="125" stroke="#79c0ff" stroke-width="1.5" marker-end="url(#arr)"/>

  <!-- Jaxb2Marshaller -->
  <rect x="409" y="40" width="165" height="45" rx="6" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="491" y="60" fill="#6db33f" font-size="9" text-anchor="middle" font-family="sans-serif">Jaxb2Marshaller</text>
  <text x="491" y="76" fill="#8b949e" font-size="8" text-anchor="middle" font-family="monospace">contextPath / classes</text>

  <!-- Other -->
  <rect x="409" y="100" width="165" height="45" rx="6" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="491" y="120" fill="#79c0ff" font-size="9" text-anchor="middle" font-family="sans-serif">XStreamMarshaller</text>
  <text x="491" y="136" fill="#8b949e" font-size="8" text-anchor="middle" font-family="monospace">aliases / converters</text>
</svg>

## 5. Runnable example

Scenario: an **invoice service** — marshal/unmarshal `Invoice` objects to/from XML.

### Level 1 — Basic

`Jaxb2Marshaller` marshal + unmarshal to/from a string.

```java
// OxmAbstractionDemo.java
import jakarta.xml.bind.annotation.*;
import org.springframework.context.annotation.*;
import org.springframework.oxm.Marshaller;
import org.springframework.oxm.Unmarshaller;
import org.springframework.oxm.jaxb.Jaxb2Marshaller;
import javax.xml.transform.stream.*;
import java.io.*;

@XmlRootElement(name = "invoice")
@XmlAccessorType(XmlAccessType.FIELD)
class Invoice {
    @XmlElement String id;
    @XmlElement String customer;
    @XmlElement double total;
    public Invoice(){} public Invoice(String i,String c,double t){id=i;customer=c;total=t;}
    public String toString(){return "Invoice["+id+","+customer+","+total+"]";}
}

@Configuration
class AppCfg {
    @Bean Jaxb2Marshaller marshaller() {
        Jaxb2Marshaller m = new Jaxb2Marshaller();
        m.setClassesToBeBound(Invoice.class);  // register the type
        return m;
    }
}

public class OxmAbstractionDemo {
    public static void main(String[] args) throws Exception {
        var ctx = new org.springframework.context.annotation.AnnotationConfigApplicationContext(AppCfg.class);

        // Use OXM interfaces — not JAXB directly
        Marshaller marshaller = ctx.getBean(Marshaller.class);
        Unmarshaller unmarshaller = ctx.getBean(Unmarshaller.class);

        Invoice inv = new Invoice("INV-001", "Alice", 299.99);

        // Marshal to XML string
        StringWriter sw = new StringWriter();
        marshaller.marshal(inv, new StreamResult(sw));
        String xml = sw.toString();
        System.out.println("XML:\n" + xml);

        // Unmarshal back to object
        Invoice restored = (Invoice) unmarshaller.unmarshal(new StreamSource(new StringReader(xml)));
        System.out.println("Restored: " + restored);

        ctx.close();
    }
}
```

How to run: `java -cp spring-context.jar:spring-oxm.jar:jakarta.xml.bind-api.jar:jaxb-impl.jar:. OxmAbstractionDemo.java`

`Jaxb2Marshaller` implements both `Marshaller` and `Unmarshaller`. The service accesses only the interfaces — switching to a different OXM implementation requires only a `@Bean` change, not service code.

---

### Level 2 — Intermediate

Inject `Marshaller`/`Unmarshaller` into a service; marshal to file and back.

```java
// OxmAbstractionDemo.java
import jakarta.xml.bind.annotation.*;
import org.springframework.context.annotation.*;
import org.springframework.oxm.*;
import org.springframework.oxm.jaxb.Jaxb2Marshaller;
import org.springframework.stereotype.Service;
import javax.xml.transform.stream.*;
import java.io.*;
import java.nio.file.*;
import java.util.*;

@XmlRootElement(name="invoices")
@XmlAccessorType(XmlAccessType.FIELD)
class InvoiceList {
    @XmlElement(name="invoice") List<Invoice> items = new ArrayList<>();
    public InvoiceList(){} public InvoiceList(List<Invoice> i){items=i;}
    public List<Invoice> getItems(){return items;}
    public String toString(){return "InvoiceList"+items;}
}

@Service
class InvoiceStore {
    private final Marshaller marshaller;
    private final Unmarshaller unmarshaller;
    InvoiceStore(Marshaller m, Unmarshaller u){ marshaller=m; unmarshaller=u; }

    public void save(String path, InvoiceList list) throws IOException {
        try(var os=new FileOutputStream(path)){
            marshaller.marshal(list, new StreamResult(os));
        }
    }

    public InvoiceList load(String path) throws IOException {
        try(var is=new FileInputStream(path)){
            return (InvoiceList) unmarshaller.unmarshal(new StreamSource(is));
        }
    }
}

@Configuration @ComponentScan
class AppCfg2 {
    @Bean Jaxb2Marshaller marshaller() {
        Jaxb2Marshaller m = new Jaxb2Marshaller();
        m.setClassesToBeBound(Invoice.class, InvoiceList.class); return m;
    }
}

public class OxmAbstractionDemo {
    public static void main(String[] args) throws Exception {
        var ctx = new org.springframework.context.annotation.AnnotationConfigApplicationContext(AppCfg2.class);
        InvoiceStore store = ctx.getBean(InvoiceStore.class);

        InvoiceList list = new InvoiceList(List.of(
            new Invoice("INV-001","Alice",299.99),
            new Invoice("INV-002","Bob",  149.50)
        ));

        String path = "/tmp/invoices.xml";
        store.save(path, list);
        System.out.println("Saved to " + path);

        InvoiceList loaded = store.load(path);
        System.out.println("Loaded: " + loaded);
        ctx.close();
    }
}
```

How to run: same classpath

`InvoiceStore` depends on `Marshaller` and `Unmarshaller` interfaces only. Swapping JAXB for XStream is a one-line config change: replace `Jaxb2Marshaller` bean with `XStreamMarshaller`. The `InvoiceStore` service is unchanged.

---

### Level 3 — Advanced

`Jaxb2Marshaller` with schema validation + custom properties.

```java
// OxmAbstractionDemo.java
import jakarta.xml.bind.annotation.*;
import org.springframework.context.annotation.*;
import org.springframework.core.io.ClassPathResource;
import org.springframework.oxm.*;
import org.springframework.oxm.jaxb.Jaxb2Marshaller;
import javax.xml.transform.stream.*;
import java.io.*;
import java.util.*;

@Service
class ValidatingInvoiceService {
    private final Marshaller marshaller;
    private final Unmarshaller unmarshaller;
    ValidatingInvoiceService(Marshaller m, Unmarshaller u){ marshaller=m; unmarshaller=u; }

    public String toXml(Invoice inv) throws IOException {
        StringWriter sw = new StringWriter();
        marshaller.marshal(inv, new StreamResult(sw));  // schema validation happens here
        return sw.toString();
    }
    public Invoice fromXml(String xml) throws IOException {
        return (Invoice) unmarshaller.unmarshal(new StreamSource(new StringReader(xml)));
    }
}

@Configuration @ComponentScan
class AppCfg3 {
    @Bean Jaxb2Marshaller marshaller() {
        Jaxb2Marshaller m = new Jaxb2Marshaller();
        m.setClassesToBeBound(Invoice.class);

        // Enable pretty-printing
        Map<String,Object> props = new HashMap<>();
        props.put(jakarta.xml.bind.Marshaller.JAXB_FORMATTED_OUTPUT, true);
        props.put(jakarta.xml.bind.Marshaller.JAXB_ENCODING, "UTF-8");
        m.setMarshallerProperties(props);

        // Schema validation (inline schema definition in code for demo)
        // m.setSchema(new ClassPathResource("invoice.xsd"));  // uncomment with real .xsd on classpath

        return m;
    }
}

public class OxmAbstractionDemo {
    public static void main(String[] args) throws Exception {
        var ctx = new org.springframework.context.annotation.AnnotationConfigApplicationContext(AppCfg3.class);
        ValidatingInvoiceService svc = ctx.getBean(ValidatingInvoiceService.class);

        String xml = svc.toXml(new Invoice("INV-003","Carol",499.00));
        System.out.println("Pretty XML:\n" + xml);

        Invoice restored = svc.fromXml(xml);
        System.out.println("Restored: " + restored);

        // Demonstrate XmlMappingException (unmarshal invalid XML)
        try {
            svc.fromXml("<invoice><id>X</id></invoice>");  // missing required customer/total
            System.out.println("Parsed (missing fields become null/0.0 in JAXB)");
        } catch (XmlMappingException e) {
            System.out.println("XmlMappingException: " + e.getClass().getSimpleName());
        }
        ctx.close();
    }
}
```

How to run: same classpath

`setMarshallerProperties()` passes JAXB marshaller properties (formatted output, encoding). `setSchema()` wires an XSD schema for validation — violations throw `MarshallingFailureException`. All Spring OXM exceptions are `XmlMappingException` subclasses (analogous to `DataAccessException` for databases) — catch the hierarchy rather than vendor exceptions.

## 6. Walkthrough

**Level 2 — `store.save()` flow:**

1. `store.save("/tmp/invoices.xml", list)` opens `FileOutputStream`.
2. `marshaller.marshal(list, new StreamResult(os))` → `Jaxb2Marshaller.marshal()`.
3. `Jaxb2Marshaller.supports(InvoiceList.class)` → true (registered in `setClassesToBeBound`).
4. `JAXBContext.newInstance(Invoice.class, InvoiceList.class)` (cached on first call).
5. `context.createMarshaller()` → JAXB marshaller configured with properties.
6. JAXB writes `<invoices><invoice>...</invoice><invoice>...</invoice></invoices>` to `FileOutputStream`.
7. `store.load()`: `FileInputStream` wrapped in `StreamSource`.
8. `unmarshaller.unmarshal(source)` → JAXB unmarshaller reads XML → constructs `InvoiceList` with two `Invoice` objects.

## 7. Gotchas & takeaways

> **`Jaxb2Marshaller.setClassesToBeBound()` vs `setContextPath()`**: `setClassesToBeBound()` is ideal when you explicitly list classes at `@Bean` creation. `setContextPath("com.example.model")` scans a package for `@XmlRootElement` classes — useful for large models but slower to initialise. Only one should be set.

> **`JAXBContext` is thread-safe and expensive to create.** `Jaxb2Marshaller` caches it; the individual `Marshaller`/`Unmarshaller` instances are NOT thread-safe but `Jaxb2Marshaller` creates new ones per call. Safe for Spring singleton beans.

> **Schema validation happens at marshal/unmarshal time**, not at bean creation. A bad XSD path fails silently at startup but throws `MarshallingFailureException` at first use. Verify your XSD path in a test.

- OXM abstraction: `Marshaller` + `Unmarshaller` interfaces decouple from JAXB/XStream/Castor.
- `Jaxb2Marshaller` is the common implementation; declare as `@Bean`, inject by interface.
- `setClassesToBeBound()` or `setContextPath()` — choose one; not both.
- All OXM errors are `XmlMappingException` subclasses — catch by type.
- Schema validation via `setSchema(Resource)` — validates on marshal/unmarshal.

---
card: spring-framework
gi: 287
slug: marshaller-unmarshaller
title: Marshaller & Unmarshaller
---

## 1. What it is

`Marshaller` and `Unmarshaller` are Spring's core OXM interfaces in `spring-oxm`. They convert between Java object graphs and XML using JAXP `Result`/`Source` types:

```java
// org.springframework.oxm.Marshaller
public interface Marshaller {
    boolean supports(Class<?> clazz);
    void marshal(Object graph, Result result) throws IOException, XmlMappingException;
}

// org.springframework.oxm.Unmarshaller
public interface Unmarshaller {
    boolean supports(Class<?> clazz);
    Object unmarshal(Source source) throws IOException, XmlMappingException;
}
```

Standard `Result`/`Source` implementations (from JAXP, not Spring):
- `StreamResult(OutputStream/Writer)` / `StreamSource(InputStream/Reader/String path)` — stream-based.
- `DOMResult(Node)` / `DOMSource(Node)` — DOM node-based.
- `SAXResult(ContentHandler)` / `SAXSource(XMLReader, InputSource)` — SAX-based.

## 2. Why & when

These interfaces are the **only thing your application code should touch** for XML binding. `Jaxb2Marshaller`, `XStreamMarshaller`, and other implementations wire in at configuration time; your services stay portable.

`Marshaller.supports(Class<?>)` guards mismatches — call it to pre-validate before passing an unexpected type to `marshal()`.

Use the interfaces directly when:
- Writing a generic XML utility method that should work with any provider.
- Testing with a mock `Marshaller` — the interface is easily mockable.
- Wiring Spring MVC `MarshallingHttpMessageConverter` (takes a `Marshaller` bean).
- Injecting into Spring Batch item writers that produce XML output.

## 3. Core concept

```java
// Marshalling to a byte array
byte[] toXmlBytes(Marshaller m, Object obj) throws IOException {
    ByteArrayOutputStream baos = new ByteArrayOutputStream();
    m.marshal(obj, new StreamResult(baos));
    return baos.toByteArray();
}

// Unmarshalling from a byte array
Object fromXmlBytes(Unmarshaller u, byte[] xml) throws IOException {
    return u.unmarshal(new StreamSource(new ByteArrayInputStream(xml)));
}
```

`supports()` contract:
```java
// Before marshalling an arbitrary object:
if (!marshaller.supports(obj.getClass())) {
    throw new IllegalArgumentException("Cannot marshal " + obj.getClass());
}
marshaller.marshal(obj, result);
```

`XmlMappingException` is unchecked; `IOException` is checked (thrown on stream errors):
```
try {
    marshaller.marshal(obj, result);
} catch (MarshallingFailureException e) {
    // schema violation, binding error
} catch (IOException e) {
    // stream I/O error
}
```

## 4. Diagram

<svg viewBox="0 0 700 185" xmlns="http://www.w3.org/2000/svg">
  <defs>
    <marker id="arr" markerWidth="8" markerHeight="6" refX="8" refY="3" orient="auto">
      <polygon points="0 0,8 3,0 6" fill="#6db33f"/>
    </marker>
  </defs>

  <!-- Java Object -->
  <rect x="10" y="70" width="120" height="45" rx="6" fill="#1c2430" stroke="#8b949e" stroke-width="1.5"/>
  <text x="70" y="90" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">Java Object</text>
  <text x="70" y="106" fill="#8b949e" font-size="8" text-anchor="middle" font-family="monospace">@XmlRootElement</text>

  <!-- marshal arrow -->
  <line x1="132" y1="92" x2="245" y2="72" stroke="#6db33f" stroke-width="1.5" marker-end="url(#arr)"/>
  <text x="188" y="70" fill="#6db33f" font-size="8" font-family="sans-serif">marshal()</text>

  <!-- unmarshal arrow -->
  <line x1="245" y1="115" x2="132" y2="105" stroke="#79c0ff" stroke-width="1.5" marker-end="url(#arr)"/>
  <text x="155" y="125" fill="#79c0ff" font-size="8" font-family="sans-serif">unmarshal()</text>

  <!-- Marshaller/Unmarshaller -->
  <rect x="247" y="50" width="195" height="85" rx="6" fill="#1c2430" stroke="#6db33f" stroke-width="2"/>
  <text x="344" y="72" fill="#6db33f" font-size="9" text-anchor="middle" font-family="sans-serif">Marshaller / Unmarshaller</text>
  <line x1="257" y1="78" x2="432" y2="78" stroke="#8b949e" stroke-width="0.5"/>
  <text x="344" y="96" fill="#8b949e" font-size="8" text-anchor="middle" font-family="monospace">supports(Class&lt;?&gt;)</text>
  <text x="344" y="110" fill="#8b949e" font-size="8" text-anchor="middle" font-family="monospace">marshal(obj, Result)</text>
  <text x="344" y="124" fill="#8b949e" font-size="8" text-anchor="middle" font-family="monospace">unmarshal(Source)</text>

  <line x1="444" y1="92" x2="487" y2="92" stroke="#6db33f" stroke-width="1.5" marker-end="url(#arr)"/>

  <!-- XML stream -->
  <rect x="489" y="65" width="175" height="55" rx="6" fill="#1c2430" stroke="#8b949e" stroke-width="1.5"/>
  <text x="576" y="88" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">Result / Source</text>
  <text x="576" y="104" fill="#8b949e" font-size="8" text-anchor="middle" font-family="monospace">StreamResult/StreamSource</text>
  <text x="576" y="116" fill="#8b949e" font-size="8" text-anchor="middle" font-family="monospace">DOMResult / SAXResult</text>
</svg>

## 5. Runnable example

Scenario: an **employee directory** — marshal employees to XML and unmarshal back, including nested structures.

### Level 1 — Basic

Marshal/unmarshal a single `Employee` object.

```java
// MarshallerDemo.java
import jakarta.xml.bind.annotation.*;
import org.springframework.context.annotation.*;
import org.springframework.oxm.*;
import org.springframework.oxm.jaxb.Jaxb2Marshaller;
import javax.xml.transform.stream.*;
import java.io.*;

@XmlRootElement(name="employee")
@XmlAccessorType(XmlAccessType.FIELD)
class Employee {
    @XmlElement String id;
    @XmlElement String name;
    @XmlElement String department;
    public Employee(){} public Employee(String i,String n,String d){id=i;name=n;department=d;}
    public String toString(){return "Employee["+id+","+name+","+department+"]";}
}

@Configuration
class AppCfg {
    @Bean Jaxb2Marshaller jaxb2() {
        var m = new Jaxb2Marshaller();
        m.setClassesToBeBound(Employee.class);
        return m;
    }
}

public class MarshallerDemo {
    public static void main(String[] args) throws Exception {
        var ctx = new org.springframework.context.annotation.AnnotationConfigApplicationContext(AppCfg.class);

        Marshaller m = ctx.getBean(Marshaller.class);    // Jaxb2Marshaller via interface
        Unmarshaller u = ctx.getBean(Unmarshaller.class);

        // supports() check
        System.out.println("Supports Employee: " + m.supports(Employee.class));
        System.out.println("Supports String:   " + m.supports(String.class));

        Employee emp = new Employee("E-001", "Alice", "Engineering");

        // Marshal to String
        StringWriter sw = new StringWriter();
        m.marshal(emp, new StreamResult(sw));
        String xml = sw.toString();
        System.out.println("XML: " + xml);

        // Unmarshal from String
        Employee back = (Employee) u.unmarshal(new StreamSource(new StringReader(xml)));
        System.out.println("Restored: " + back);

        ctx.close();
    }
}
```

How to run: `java -cp spring-context.jar:spring-oxm.jar:jakarta.xml.bind-api.jar:jaxb-impl.jar:. MarshallerDemo.java`

`Jaxb2Marshaller` is retrieved as `Marshaller` and `Unmarshaller` — the interface types. `supports()` returns true for registered classes; callers should guard with it before marshalling arbitrary objects.

---

### Level 2 — Intermediate

Nested object graph — `Department` containing a list of `Employee`s.

```java
// MarshallerDemo.java
import jakarta.xml.bind.annotation.*;
import org.springframework.context.annotation.*;
import org.springframework.oxm.*;
import org.springframework.oxm.jaxb.Jaxb2Marshaller;
import javax.xml.transform.stream.*;
import java.io.*;
import java.util.*;

@XmlRootElement(name="department")
@XmlAccessorType(XmlAccessType.FIELD)
class Department {
    @XmlAttribute String name;
    @XmlElement(name="employee") List<Employee> employees = new ArrayList<>();
    public Department(){} public Department(String n, List<Employee> e){name=n;employees=e;}
    public String toString(){return "Department["+name+","+employees+"]";}
}

class XmlConverter {
    private final Marshaller marshaller;
    private final Unmarshaller unmarshaller;
    XmlConverter(Marshaller m, Unmarshaller u){ marshaller=m; unmarshaller=u; }

    public String toXml(Object obj) throws IOException {
        StringWriter sw = new StringWriter();
        marshaller.marshal(obj, new StreamResult(sw));
        return sw.toString();
    }
    @SuppressWarnings("unchecked")
    public <T> T fromXml(String xml, Class<T> type) throws IOException {
        if (!unmarshaller.supports(type))
            throw new IllegalArgumentException("Not supported: " + type);
        return (T) unmarshaller.unmarshal(new StreamSource(new StringReader(xml)));
    }
}

@Configuration
class AppCfg2 {
    @Bean Jaxb2Marshaller jaxb2() {
        var m = new Jaxb2Marshaller();
        m.setClassesToBeBound(Employee.class, Department.class); return m;
    }
    @Bean XmlConverter converter(Jaxb2Marshaller m){ return new XmlConverter(m, m); }
}

public class MarshallerDemo {
    public static void main(String[] args) throws Exception {
        var ctx = new org.springframework.context.annotation.AnnotationConfigApplicationContext(AppCfg2.class);
        XmlConverter conv = ctx.getBean(XmlConverter.class);

        Department dept = new Department("Engineering", List.of(
            new Employee("E-001","Alice","Engineering"),
            new Employee("E-002","Bob",  "Engineering")
        ));

        String xml = conv.toXml(dept);
        System.out.println("Department XML:\n" + xml);

        Department back = conv.fromXml(xml, Department.class);
        System.out.println("Restored: " + back);
        ctx.close();
    }
}
```

How to run: same classpath

The `XmlConverter` utility wraps `Marshaller`/`Unmarshaller`. It calls `supports()` before unmarshalling arbitrary types. Nested objects (`Department` → `Employee` list) serialize naturally with JAXB's `@XmlElement` annotations.

---

### Level 3 — Advanced

Marshal to `DOMResult` for DOM manipulation, then unmarshal from `DOMSource`.

```java
// MarshallerDemo.java
import jakarta.xml.bind.annotation.*;
import org.springframework.context.annotation.*;
import org.springframework.oxm.*;
import org.springframework.oxm.jaxb.Jaxb2Marshaller;
import org.w3c.dom.*;
import javax.xml.parsers.*;
import javax.xml.transform.*;
import javax.xml.transform.dom.*;
import javax.xml.transform.stream.*;
import java.io.*;

// (Employee and Department same as Level 2)

public class MarshallerDemo {
    public static void main(String[] args) throws Exception {
        var ctx = new org.springframework.context.annotation.AnnotationConfigApplicationContext(AppCfg2.class);
        Marshaller m = ctx.getBean(Marshaller.class);
        Unmarshaller u = ctx.getBean(Unmarshaller.class);

        Employee emp = new Employee("E-003","Carol","HR");

        // 1. Marshal to DOM
        Document doc = DocumentBuilderFactory.newInstance()
            .newDocumentBuilder().newDocument();
        DOMResult domResult = new DOMResult(doc);
        m.marshal(emp, domResult);

        // 2. Manipulate DOM — add an attribute programmatically
        Element root = doc.getDocumentElement();
        root.setAttribute("source", "spring-oxm");
        System.out.println("DOM element: " + root.getTagName()
            + " source=" + root.getAttribute("source"));

        // 3. Unmarshal from DOMSource
        Employee back = (Employee) u.unmarshal(new DOMSource(doc));
        System.out.println("Restored: " + back);

        // 4. DOM → XML string (standard JAXP transform)
        StringWriter sw = new StringWriter();
        TransformerFactory.newInstance().newTransformer()
            .transform(new DOMSource(doc), new StreamResult(sw));
        System.out.println("XML with injected attr:\n" + sw);

        ctx.close();
    }
}
```

How to run: same classpath

`DOMResult(Document)` / `DOMSource(Document)` pass a DOM node directly. Marshal writes to the DOM tree; unmarshal reads from it. This is useful when you need to modify the XML structure (add attributes, inject envelope elements) before sending over a SOAP transport or to a legacy system.

## 6. Walkthrough

**Level 2 — `conv.toXml(dept)` execution path:**

1. `conv.toXml(dept)` → `marshaller.marshal(dept, new StreamResult(sw))`.
2. `Jaxb2Marshaller.marshal()`:
   - Checks `dept.getClass()` (Department) is in `classesToBeBound` ✓.
   - Retrieves cached `JAXBContext` (or creates on first call).
   - Creates `jakarta.xml.bind.Marshaller` from context.
   - Calls `jaxbMarshaller.marshal(dept, sw)`.
3. JAXB processes `@XmlRootElement(name="department")` on `Department`, `@XmlAttribute` on `name`, `@XmlElement(name="employee")` on list.
4. Produces:
   ```xml
   <department name="Engineering">
     <employee><id>E-001</id><name>Alice</name>...</employee>
     <employee><id>E-002</id><name>Bob</name>...</employee>
   </department>
   ```
5. `conv.fromXml(xml, Department.class)`:
   - `unmarshaller.supports(Department.class)` → true.
   - `Jaxb2Marshaller.unmarshal(source)` → `jaxbUnmarshaller.unmarshal(source)`.
   - JAXB constructs `Department`, populates `name`, creates two `Employee` objects.

## 7. Gotchas & takeaways

> **`Jaxb2Marshaller` is thread-safe but individual JAXB `Marshaller`/`Unmarshaller` are not.** `Jaxb2Marshaller` creates per-call JAXB instances from a cached `JAXBContext`. Never cache a raw JAXB `Marshaller` as a field — use `Jaxb2Marshaller` instead.

> **`marshal()` throws `IOException` (checked) for stream errors and `XmlMappingException` (unchecked) for binding errors.** Always handle both — the checked `IOException` means stream issues; the unchecked `XmlMappingException` means a schema/binding problem.

> **`StreamSource(String)` takes a SYSTEM ID (URI), not XML content.** `new StreamSource("<?xml...")` silently fails or tries to open a file. Always use `new StreamSource(new StringReader(xmlString))` for in-memory strings.

- Inject `Marshaller`/`Unmarshaller` interfaces — not `Jaxb2Marshaller` directly.
- Call `supports()` before marshalling arbitrary `Object` instances.
- `StreamResult`/`StreamSource` for streams; `DOMResult`/`DOMSource` for DOM manipulation.
- `new StreamSource(new StringReader(xmlString))` — not `new StreamSource(xmlString)`.
- Handle both `IOException` and `XmlMappingException`.

---
card: spring-framework
gi: 288
slug: jaxb-jackson-xml-support
title: "JAXB & Jackson XML Support"
---

## 1. What it is

Spring's OXM module supports two XML binding libraries out of the box:

**JAXB 2** (`Jaxb2Marshaller`): the standard Java XML binding spec. Uses `@XmlRootElement`, `@XmlElement`, `@XmlAttribute` annotations (from `jakarta.xml.bind`). Ships with the JDK through Java 10; add `jakarta.xml.bind-api` + `jaxb-impl` for Java 11+.

**Jackson XML** (`Jackson2ObjectMapperBuilder` with XML module): uses Jackson's `XmlMapper` + `jackson-dataformat-xml` to read/write XML via the familiar Jackson annotations (`@JsonProperty`, `@JacksonXmlRootElement`, `@JacksonXmlElementWrapper`).

```java
// JAXB
@Bean Jaxb2Marshaller jaxbMarshaller() {
    var m = new Jaxb2Marshaller();
    m.setClassesToBeBound(Order.class);
    return m;
}

// Jackson XML
@Bean Jackson2ObjectMapperBuilder xmlMapperBuilder() {
    return Jackson2ObjectMapperBuilder.xml();
}
```

## 2. Why & when

Choose **JAXB** when:
- You work with standard JPA/SOAP/WSDL schemas where `@XmlRootElement` is standard.
- You need namespace support, schema validation, or `xs:type` binding.
- You use Spring WS or JAXB-generated classes from `.xsd`.

Choose **Jackson XML** when:
- Your codebase already uses Jackson for JSON and you want to reuse `@JsonProperty` annotations for XML too.
- You want simpler configuration without `JAXBContext`.
- You need to support both JSON and XML output from the same object model in Spring MVC with content-negotiation.

Both integrate with Spring MVC via `HttpMessageConverter`:
- `MarshallingHttpMessageConverter(jaxb2Marshaller)` — for JAXB.
- `MappingJackson2XmlHttpMessageConverter` — for Jackson XML.

## 3. Core concept

```
JAXB annotations:
  @XmlRootElement(name="order")
  @XmlElement(name="lineItem")
  @XmlAttribute

  Jaxb2Marshaller → JAXBContext → JAXB Marshaller
    → <order><lineItem>...</lineItem></order>

Jackson XML annotations:
  @JacksonXmlRootElement(localName="order")
  @JacksonXmlElementWrapper(localName="lineItems")
  @JacksonXmlProperty(localName="lineItem")
  @JsonProperty("id")

  XmlMapper → XmlMapper.writeValueAsString(obj)
    → <order><lineItems><lineItem>...</lineItem></lineItems></order>
```

Key difference — collections:
- JAXB: `@XmlElementWrapper` wraps a list in an extra XML element.
- Jackson XML: `@JacksonXmlElementWrapper` does the same with more control; `useWrapping=false` inlines the list.

## 4. Diagram

<svg viewBox="0 0 700 185" xmlns="http://www.w3.org/2000/svg">
  <defs>
    <marker id="arr" markerWidth="8" markerHeight="6" refX="8" refY="3" orient="auto">
      <polygon points="0 0,8 3,0 6" fill="#6db33f"/>
    </marker>
  </defs>

  <!-- Object -->
  <rect x="10" y="70" width="115" height="45" rx="6" fill="#1c2430" stroke="#8b949e" stroke-width="1.5"/>
  <text x="62" y="90" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">Order POJO</text>
  <text x="62" y="107" fill="#8b949e" font-size="8" text-anchor="middle" font-family="monospace">@Xml* / @Jackson*</text>

  <line x1="127" y1="92" x2="155" y2="75" stroke="#6db33f" stroke-width="1.5" marker-end="url(#arr)"/>
  <line x1="127" y1="105" x2="155" y2="122" stroke="#79c0ff" stroke-width="1.5" marker-end="url(#arr)"/>

  <!-- JAXB -->
  <rect x="157" y="45" width="170" height="60" rx="6" fill="#1c2430" stroke="#6db33f" stroke-width="2"/>
  <text x="242" y="67" fill="#6db33f" font-size="9" text-anchor="middle" font-family="sans-serif">Jaxb2Marshaller</text>
  <line x1="167" y1="73" x2="317" y2="73" stroke="#8b949e" stroke-width="0.5"/>
  <text x="242" y="89" fill="#8b949e" font-size="8" text-anchor="middle" font-family="monospace">JAXBContext + @XmlRootElement</text>
  <text x="242" y="101" fill="#8b949e" font-size="8" text-anchor="middle" font-family="monospace">schema validation supported</text>

  <!-- Jackson XML -->
  <rect x="157" y="115" width="170" height="60" rx="6" fill="#1c2430" stroke="#79c0ff" stroke-width="2"/>
  <text x="242" y="137" fill="#79c0ff" font-size="9" text-anchor="middle" font-family="sans-serif">XmlMapper (Jackson)</text>
  <line x1="167" y1="143" x2="317" y2="143" stroke="#8b949e" stroke-width="0.5"/>
  <text x="242" y="159" fill="#8b949e" font-size="8" text-anchor="middle" font-family="monospace">@JacksonXml* + Jackson pipeline</text>
  <text x="242" y="171" fill="#8b949e" font-size="8" text-anchor="middle" font-family="monospace">JSON + XML from same annotations</text>

  <line x1="329" y1="75" x2="399" y2="92" stroke="#6db33f" stroke-width="1.5" marker-end="url(#arr)"/>
  <line x1="329" y1="145" x2="399" y2="110" stroke="#79c0ff" stroke-width="1.5" marker-end="url(#arr)"/>

  <rect x="401" y="75" width="280" height="40" rx="6" fill="#1c2430" stroke="#8b949e" stroke-width="1.5"/>
  <text x="541" y="91" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">&lt;order&gt;&lt;id&gt;1&lt;/id&gt;...&lt;/order&gt;</text>
  <text x="541" y="107" fill="#8b949e" font-size="8" text-anchor="middle" font-family="monospace">XML output (Result / String)</text>
</svg>

## 5. Runnable example

Scenario: an **order export service** — marshal orders using JAXB and Jackson XML, then compare outputs.

### Level 1 — Basic

JAXB marshal/unmarshal.

```java
// JaxbJacksonXmlDemo.java
import jakarta.xml.bind.annotation.*;
import org.springframework.context.annotation.*;
import org.springframework.oxm.jaxb.Jaxb2Marshaller;
import javax.xml.transform.stream.*;
import java.io.*;
import java.util.*;

@XmlRootElement(name="order")
@XmlAccessorType(XmlAccessType.FIELD)
class Order {
    @XmlAttribute long id;
    @XmlElement String customer;
    @XmlElement double total;
    @XmlElementWrapper(name="items") @XmlElement(name="item") List<String> items;
    public Order(){} public Order(long i,String c,double t,List<String> its){id=i;customer=c;total=t;items=its;}
    public String toString(){return "Order["+id+","+customer+","+total+","+items+"]";}
}

@Configuration
class AppCfg {
    @Bean Jaxb2Marshaller jaxb2() {
        var m = new Jaxb2Marshaller();
        m.setClassesToBeBound(Order.class);
        java.util.Map<String,Object> props = new java.util.HashMap<>();
        props.put(jakarta.xml.bind.Marshaller.JAXB_FORMATTED_OUTPUT, true);
        m.setMarshallerProperties(props);
        return m;
    }
}

public class JaxbJacksonXmlDemo {
    public static void main(String[] args) throws Exception {
        var ctx = new org.springframework.context.annotation.AnnotationConfigApplicationContext(AppCfg.class);
        var m = ctx.getBean(Jaxb2Marshaller.class);

        Order order = new Order(1L, "Alice", 299.99, List.of("Widget", "Gadget"));

        StringWriter sw = new StringWriter();
        m.marshal(order, new StreamResult(sw));
        System.out.println("JAXB XML:\n" + sw);

        Order back = (Order) m.unmarshal(new StreamSource(new StringReader(sw.toString())));
        System.out.println("Restored: " + back);
        ctx.close();
    }
}
```

How to run: `java -cp spring-context.jar:spring-oxm.jar:jakarta.xml.bind-api.jar:jaxb-impl.jar:. JaxbJacksonXmlDemo.java`

`@XmlElementWrapper(name="items")` wraps the list in `<items>...</items>`. `@XmlElement(name="item")` names each element. JAXB produces standards-compliant XML that can be validated against XSD.

---

### Level 2 — Intermediate

Jackson XML — same object with `@JacksonXml*` annotations.

```java
// JaxbJacksonXmlDemo.java
import com.fasterxml.jackson.dataformat.xml.annotation.*;
import com.fasterxml.jackson.dataformat.xml.*;
import com.fasterxml.jackson.annotation.JsonProperty;
import org.springframework.context.annotation.*;
import java.util.*;

@JacksonXmlRootElement(localName = "order")
class JacksonOrder {
    @JacksonXmlProperty(isAttribute=true) public long id;
    @JsonProperty public String customer;
    @JsonProperty public double total;
    @JacksonXmlElementWrapper(localName="items")
    @JacksonXmlProperty(localName="item")   public List<String> items;
    public JacksonOrder(){} public JacksonOrder(long i,String c,double t,List<String> its){id=i;customer=c;total=t;items=its;}
    public String toString(){return "JacksonOrder["+id+","+customer+","+total+","+items+"]";}
}

@Configuration
class AppCfg2 {
    @Bean XmlMapper xmlMapper() {
        // Jackson XmlMapper — note: NOT an OXM Marshaller but usable directly
        XmlMapper mapper = new XmlMapper();
        mapper.enable(com.fasterxml.jackson.databind.SerializationFeature.INDENT_OUTPUT);
        return mapper;
    }
}

public class JaxbJacksonXmlDemo {
    public static void main(String[] args) throws Exception {
        var ctx = new org.springframework.context.annotation.AnnotationConfigApplicationContext(AppCfg2.class);
        XmlMapper xml = ctx.getBean(XmlMapper.class);

        JacksonOrder order = new JacksonOrder(1L,"Alice",299.99,List.of("Widget","Gadget"));

        String xmlStr = xml.writeValueAsString(order);
        System.out.println("Jackson XML:\n" + xmlStr);

        JacksonOrder back = xml.readValue(xmlStr, JacksonOrder.class);
        System.out.println("Restored: " + back);
        ctx.close();
    }
}
```

How to run: `java -cp spring-context.jar:jackson-databind.jar:jackson-dataformat-xml.jar:. JaxbJacksonXmlDemo.java`

`XmlMapper` is Jackson's XML counterpart to `ObjectMapper`. `@JacksonXmlProperty(isAttribute=true)` writes as an XML attribute; `@JacksonXmlElementWrapper` controls list wrapping. The same annotations work for JSON via `ObjectMapper` if you avoid XML-specific ones.

---

### Level 3 — Advanced

Spring MVC content negotiation: same endpoint returns JSON or XML based on `Accept` header.

```java
// JaxbJacksonXmlDemo.java
import com.fasterxml.jackson.dataformat.xml.annotation.*;
import com.fasterxml.jackson.annotation.*;
import org.springframework.context.annotation.*;
import org.springframework.http.*;
import org.springframework.http.converter.*;
import org.springframework.http.converter.json.*;
import org.springframework.http.converter.xml.*;
import org.springframework.web.bind.annotation.*;
import org.springframework.web.servlet.config.annotation.*;
import java.util.*;

// One model — works for both JSON and XML with Jackson
@JacksonXmlRootElement(localName="product")
class Product {
    @JsonProperty @JacksonXmlProperty(isAttribute=true) public long id;
    @JsonProperty public String name;
    @JsonProperty public double price;
    public Product(){} public Product(long i,String n,double p){id=i;name=n;price=p;}
}

@RestController @RequestMapping("/products")
class ProductController {
    @GetMapping(produces={MediaType.APPLICATION_JSON_VALUE, MediaType.APPLICATION_XML_VALUE})
    public List<Product> list() {
        return List.of(new Product(1L,"Widget",49.99), new Product(2L,"Gadget",99.00));
    }
}

@Configuration @EnableWebMvc @ComponentScan
class WebCfg implements WebMvcConfigurer {
    @Override
    public void configureMessageConverters(List<HttpMessageConverter<?>> converters) {
        // JSON converter
        converters.add(new MappingJackson2HttpMessageConverter());
        // XML converter using Jackson XmlMapper
        converters.add(new MappingJackson2XmlHttpMessageConverter());
    }
}

public class JaxbJacksonXmlDemo {
    public static void main(String[] args) {
        System.out.println("Start embedded Tomcat with DispatcherServlet to test:");
        System.out.println("  GET /products  Accept: application/json  → JSON array");
        System.out.println("  GET /products  Accept: application/xml   → XML");
        System.out.println("Both served from the SAME controller method.");
        System.out.println("Jackson XmlMapper + ObjectMapper handle serialisation.");
    }
}
```

How to run: deploy to embedded Tomcat with spring-webmvc on classpath; or note the output explanation.

`MappingJackson2XmlHttpMessageConverter` is registered alongside `MappingJackson2HttpMessageConverter`. Spring MVC selects the right one based on the `Accept` header. The same `@RestController` method produces either format without any code duplication.

## 6. Walkthrough

**Level 1 — JAXB marshal flow:**

1. `m.marshal(order, new StreamResult(sw))` → `Jaxb2Marshaller.marshal()`.
2. `JAXBContext.newInstance(Order.class)` (cached after first call).
3. `context.createMarshaller()` → JAXB `Marshaller` with `JAXB_FORMATTED_OUTPUT=true`.
4. JAXB processes annotations:
   - `@XmlRootElement(name="order")` → root element `<order>`.
   - `@XmlAttribute long id` → `id="1"` on the root element.
   - `@XmlElement String customer` → `<customer>Alice</customer>`.
   - `@XmlElementWrapper(name="items")` + `@XmlElement(name="item")` → wraps list:
     ```xml
     <items>
       <item>Widget</item>
       <item>Gadget</item>
     </items>
     ```
5. Output written to `StringWriter` `sw`.
6. Unmarshal reverses: `JAXBContext.createUnmarshaller()` reads XML → constructs `Order` with populated fields.

## 7. Gotchas & takeaways

> **JAXB requires a no-arg constructor.** Every `@XmlRootElement` class must have a public or package-private no-arg constructor for JAXB to instantiate it during unmarshalling. Jackson OXM does not have this restriction.

> **`@XmlElementWrapper` is JAXB-only.** Jackson XML uses `@JacksonXmlElementWrapper`. If you try to use JAXB annotations with `XmlMapper`, the list output differs — Jackson by default inlines list items without a wrapper element.

> **`JAXBContext` is expensive to create and thread-safe.** `Jaxb2Marshaller` caches it. Individual `Marshaller`/`Unmarshaller` instances are NOT thread-safe — `Jaxb2Marshaller` creates fresh ones per call. Never store raw JAXB instances as fields in singleton beans.

> **Jackson `XmlMapper` is not a Spring OXM `Marshaller`** — it's a Jackson-native class. For OXM integration, use `MappingJackson2XmlHttpMessageConverter` in Spring MVC, or wrap `XmlMapper` in a custom `Marshaller` adapter.

- JAXB: standard spec, namespace/schema support, `@XmlRootElement`, requires no-arg constructor.
- Jackson XML: familiar Jackson API, JSON/XML from one model, no `JAXBContext` overhead.
- `Jaxb2Marshaller` = Spring OXM `Marshaller`/`Unmarshaller` backed by JAXB.
- `MappingJackson2XmlHttpMessageConverter` = Spring MVC Jackson XML integration.
- Content negotiation: register both JSON + XML converters, use `produces={...}` on `@GetMapping`.

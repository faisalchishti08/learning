---
card: spring-framework
gi: 460
slug: xml-application-context-vs-annotation-driven
title: "XML application context vs annotation-driven"
---

## 1. What it is

Spring supports two fundamentally different ways to describe an application's bean graph: XML configuration (`<beans>`, `<bean>`, and the custom namespaces covered throughout this Appendix — `util`, `aop`, `context`, `jee`, `jms`, `lang`, `task`, `cache`) versus annotation-driven configuration (`@Configuration` classes, `@Component`/`@Service`/`@Repository` plus `@ComponentScan`, `@Bean` methods, and enabling annotations like `@EnableCaching`). Both produce the exact same runtime result — a populated `ApplicationContext` full of wired beans — from two different *sources of truth* about what those beans and their wiring should be.

```java
// Annotation-driven: the class itself declares what it is and what it needs
@Service
public class OrderService {
    private final PaymentGateway gateway;
    public OrderService(PaymentGateway gateway) { this.gateway = gateway; }
}
```
```xml
<!-- XML: wiring lives entirely outside the class -->
<bean id="orderService" class="com.example.OrderService">
    <constructor-arg ref="paymentGateway"/>
</bean>
```

## 2. Why & when

Every Spring application eventually has to answer: where does the description of "what beans exist and how they're wired" live — inside the classes themselves (annotations) or in a separate configuration artifact (XML)? This isn't a technical limitation either way — both are fully supported, and Spring Boot's autoconfiguration is itself built on the annotation-driven model — but the choice has real, lasting consequences for how a codebase reads and evolves.

Choose (or recognize why a codebase already chose) each style based on:

- **Annotation-driven** is the default for new Spring and virtually all Spring Boot applications: wiring lives next to the code it wires, IDEs can navigate `@Autowired` to its target directly, and there's no separate XML file to keep in sync with refactors that rename or move classes.
- **XML** remains relevant when configuration needs to change *without recompiling* — swapping a `<bean class="...">` value to point at a different implementation in a deployed environment, without a rebuild — or when wiring a class you don't control and can't annotate (a third-party library class), or when maintaining a long-lived enterprise codebase where XML is already the established convention and there's no business case for a wholesale migration.
- Both can and do coexist in the same application: `<context:component-scan>` (covered earlier in this Appendix) lets an XML root configuration discover annotation-based beans, and a `@Configuration` class can `@ImportResource` a legacy XML file — migration is almost always incremental, not all-or-nothing.

## 3. Core concept

```
                    Two sources of truth, one runtime result:

  ANNOTATION-DRIVEN                          XML
  ------------------                          ---
  @Component classes                          <bean> elements
  discovered by @ComponentScan                explicitly declared, one per bean
  wiring lives IN the class                    wiring lives OUTSIDE the class
  @Autowired / @Value                          <property>/<constructor-arg> + ${...}
  @Bean methods in @Configuration              <bean class="Factory" factory-method="...">
  requires recompilation to change wiring       can be edited and redeployed without recompiling
                    \                          /
                     v                        v
                  BOTH produce BeanDefinitions
                     |
                     v
              same ApplicationContext, same DefaultListableBeanFactory,
              same bean lifecycle -- the runtime cannot tell which style
              a given bean's definition originally came from
```

Neither style is "more correct" at the framework level — `BeanDefinition` is the common internal representation both compile down to.

## 4. Diagram

<svg viewBox="0 0 640 200" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Annotation-driven and XML configuration both compile down to BeanDefinitions in the same ApplicationContext">
  <rect x="10" y="20" width="220" height="60" rx="8" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="120" y="45" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">@Component + @ComponentScan</text>
  <text x="120" y="63" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">wiring lives in the class</text>

  <rect x="410" y="20" width="220" height="60" rx="8" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="520" y="45" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">&lt;bean&gt; elements in XML</text>
  <text x="520" y="63" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">wiring lives outside the class</text>

  <rect x="180" y="130" width="280" height="55" rx="8" fill="#1c2430" stroke="#8b949e" stroke-width="1.2"/>
  <text x="320" y="153" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">BeanDefinitions in one registry</text>
  <text x="320" y="170" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">same ApplicationContext, same lifecycle</text>

  <line x1="120" y1="80" x2="280" y2="128" stroke="#8b949e" stroke-width="1.5" marker-end="url(#a)"/>
  <line x1="520" y1="80" x2="360" y2="128" stroke="#8b949e" stroke-width="1.5" marker-end="url(#a)"/>
  <defs><marker id="a" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#8b949e"/></marker></defs>
</svg>

Both configuration styles converge on the same internal representation before any bean is instantiated.

## 5. Runnable example

The scenario: an `OrderService` that depends on a `PaymentGateway`. It's built three ways — pure XML, pure annotations, and a mixed setup — each producing the identical wired result, to make the equivalence concrete rather than theoretical.

### Level 1 — Basic

Build the exact same two-bean graph twice: once with an XML `<beans>` file, once with a `@Configuration` class, and confirm both produce a working `OrderService`.

```java
import org.springframework.context.annotation.AnnotationConfigApplicationContext;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.context.support.GenericXmlApplicationContext;
import org.springframework.core.io.ByteArrayResource;

import java.nio.charset.StandardCharsets;

public class XmlVsAnnotationLevel1 {

    public interface PaymentGateway { String charge(int amountCents); }

    public static class StripeGateway implements PaymentGateway {
        public String charge(int amountCents) { return "charged " + amountCents + " cents via Stripe"; }
    }

    public static class OrderService {
        private final PaymentGateway gateway;
        public OrderService(PaymentGateway gateway) { this.gateway = gateway; }
        public String placeOrder(int amountCents) { return gateway.charge(amountCents); }
    }

    @Configuration
    public static class AppConfig {
        @Bean public PaymentGateway paymentGateway() { return new StripeGateway(); }
        @Bean public OrderService orderService(PaymentGateway gateway) { return new OrderService(gateway); }
    }

    public static void main(String[] args) {
        // Annotation-driven
        AnnotationConfigApplicationContext annoCtx = new AnnotationConfigApplicationContext(AppConfig.class);
        OrderService annoService = annoCtx.getBean(OrderService.class);
        String annoResult = annoService.placeOrder(500);
        System.out.println("annotation-driven result = " + annoResult);

        // XML-driven, same shape
        String xml = """
            <?xml version="1.0" encoding="UTF-8"?>
            <beans xmlns="http://www.springframework.org/schema/beans"
                   xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
                   xsi:schemaLocation="http://www.springframework.org/schema/beans
                       https://www.springframework.org/schema/beans/spring-beans.xsd">

                <bean id="paymentGateway" class="XmlVsAnnotationLevel1$StripeGateway"/>
                <bean id="orderService" class="XmlVsAnnotationLevel1$OrderService">
                    <constructor-arg ref="paymentGateway"/>
                </bean>
            </beans>
            """;
        GenericXmlApplicationContext xmlCtx = new GenericXmlApplicationContext();
        xmlCtx.load(new ByteArrayResource(xml.getBytes(StandardCharsets.UTF_8)));
        xmlCtx.refresh();
        OrderService xmlService = xmlCtx.getBean(OrderService.class);
        String xmlResult = xmlService.placeOrder(500);
        System.out.println("XML-driven result = " + xmlResult);

        if (!annoResult.equals(xmlResult))
            throw new AssertionError("Both configuration styles should produce identical behavior");
        System.out.println("Annotation-driven and XML produced identical wiring -- PASS");
        annoCtx.close();
        xmlCtx.close();
    }
}
```

How to run: put `spring-context` on the classpath, then `java XmlVsAnnotationLevel1.java` on JDK 17+.

Both `AppConfig` (a `@Configuration` class with `@Bean` methods) and the XML `<beans>` block declare the exact same two beans and the exact same dependency (`orderService` needs `paymentGateway`) — the identical output string from both contexts is the concrete proof that the runtime behavior doesn't depend on which configuration style produced it.

### Level 2 — Intermediate

Mix the two styles in a single context: an XML root configuration that `<context:component-scan>`s for an `@Service`-annotated `OrderService`, while `PaymentGateway` stays a hand-written XML `<bean>` — the realistic incremental-migration shape.

```java
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.context.support.GenericXmlApplicationContext;
import org.springframework.core.io.ByteArrayResource;
import org.springframework.stereotype.Service;

import java.nio.charset.StandardCharsets;

public class XmlVsAnnotationLevel2 {

    public interface PaymentGateway { String charge(int amountCents); }

    public static class StripeGateway implements PaymentGateway {
        public String charge(int amountCents) { return "charged " + amountCents + " cents via Stripe"; }
    }

    @Service("orderService")
    public static class OrderService {
        private final PaymentGateway gateway;
        @Autowired
        public OrderService(PaymentGateway gateway) { this.gateway = gateway; }
        public String placeOrder(int amountCents) { return gateway.charge(amountCents); }
    }

    public static void main(String[] args) {
        String xml = """
            <?xml version="1.0" encoding="UTF-8"?>
            <beans xmlns="http://www.springframework.org/schema/beans"
                   xmlns:context="http://www.springframework.org/schema/context"
                   xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
                   xsi:schemaLocation="http://www.springframework.org/schema/beans
                       https://www.springframework.org/schema/beans/spring-beans.xsd
                       http://www.springframework.org/schema/context
                       https://www.springframework.org/schema/context/spring-context.xsd">

                <!-- Legacy hand-written bean, not annotated -->
                <bean id="paymentGateway" class="XmlVsAnnotationLevel2$StripeGateway"/>

                <!-- New code discovered via component-scan -->
                <context:component-scan base-package="XmlVsAnnotationLevel2"/>
            </beans>
            """;

        GenericXmlApplicationContext ctx = new GenericXmlApplicationContext();
        ctx.load(new ByteArrayResource(xml.getBytes(StandardCharsets.UTF_8)));
        ctx.refresh();

        OrderService service = ctx.getBean(OrderService.class);
        String result = service.placeOrder(750);
        System.out.println("mixed-config result = " + result);

        if (!result.contains("750"))
            throw new AssertionError("Expected the scanned @Service to receive the XML-defined gateway");
        System.out.println("Scanned @Service was autowired with a hand-written XML bean -- PASS");
        ctx.close();
    }
}
```

How to run: same classpath as Level 1, `java XmlVsAnnotationLevel2.java`.

`paymentGateway` is a plain, unannotated XML `<bean>` — exactly the kind of dependency that might be too risky, too third-party, or simply not yet migrated to annotate. `OrderService` is discovered by `<context:component-scan>` because it's `@Service`-annotated, and its `@Autowired` constructor is satisfied by matching `PaymentGateway` type against the XML-defined bean — Spring's dependency resolution doesn't care which style declared the dependency it's satisfying, only that a bean of the right type (or qualifier) exists in the registry.

### Level 3 — Advanced

Show the same bean graph declared three completely different ways at once being swappable via a runtime flag — proving they really are interchangeable "sources of truth" for the identical result, the kind of check worth writing while migrating a real codebase incrementally.

```java
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.context.ConfigurableApplicationContext;
import org.springframework.context.annotation.AnnotationConfigApplicationContext;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.ComponentScan;
import org.springframework.context.annotation.Configuration;
import org.springframework.context.support.GenericXmlApplicationContext;
import org.springframework.core.io.ByteArrayResource;
import org.springframework.stereotype.Service;

import java.nio.charset.StandardCharsets;
import java.util.List;
import java.util.function.Supplier;

public class XmlVsAnnotationLevel3 {

    public interface PaymentGateway { String charge(int amountCents); }

    public static class StripeGateway implements PaymentGateway {
        public String charge(int amountCents) { return "charged " + amountCents + " cents"; }
    }

    @Service("orderService")
    public static class AnnotatedOrderService {
        private final PaymentGateway gateway;
        @Autowired
        public AnnotatedOrderService(PaymentGateway gateway) { this.gateway = gateway; }
        public String placeOrder(int amountCents) { return gateway.charge(amountCents); }
    }

    public static class PlainOrderService {
        private final PaymentGateway gateway;
        public PlainOrderService(PaymentGateway gateway) { this.gateway = gateway; }
        public String placeOrder(int amountCents) { return gateway.charge(amountCents); }
    }

    @Configuration
    @ComponentScan(basePackageClasses = XmlVsAnnotationLevel3.class)
    public static class PureAnnotationConfig {
        @Bean public PaymentGateway paymentGateway() { return new StripeGateway(); }
    }

    public static void main(String[] args) {
        Supplier<ConfigurableApplicationContext> pureAnnotation = () ->
            new AnnotationConfigApplicationContext(PureAnnotationConfig.class);

        Supplier<ConfigurableApplicationContext> pureXml = () -> {
            String xml = """
                <?xml version="1.0" encoding="UTF-8"?>
                <beans xmlns="http://www.springframework.org/schema/beans"
                       xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
                       xsi:schemaLocation="http://www.springframework.org/schema/beans
                           https://www.springframework.org/schema/beans/spring-beans.xsd">
                    <bean id="paymentGateway" class="XmlVsAnnotationLevel3$StripeGateway"/>
                    <bean id="orderService" class="XmlVsAnnotationLevel3$PlainOrderService">
                        <constructor-arg ref="paymentGateway"/>
                    </bean>
                </beans>
                """;
            GenericXmlApplicationContext ctx = new GenericXmlApplicationContext();
            ctx.load(new ByteArrayResource(xml.getBytes(StandardCharsets.UTF_8)));
            ctx.refresh();
            return ctx;
        };

        Supplier<ConfigurableApplicationContext> mixed = () -> {
            String xml = """
                <?xml version="1.0" encoding="UTF-8"?>
                <beans xmlns="http://www.springframework.org/schema/beans"
                       xmlns:context="http://www.springframework.org/schema/context"
                       xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
                       xsi:schemaLocation="http://www.springframework.org/schema/beans
                           https://www.springframework.org/schema/beans/spring-beans.xsd
                           http://www.springframework.org/schema/context
                           https://www.springframework.org/schema/context/spring-context.xsd">
                    <bean id="paymentGateway" class="XmlVsAnnotationLevel3$StripeGateway"/>
                    <context:component-scan base-package="XmlVsAnnotationLevel3"/>
                </beans>
                """;
            GenericXmlApplicationContext ctx = new GenericXmlApplicationContext();
            ctx.load(new ByteArrayResource(xml.getBytes(StandardCharsets.UTF_8)));
            ctx.refresh();
            return ctx;
        };

        List<String> results = List.of("annotation", "xml", "mixed").stream()
            .map(label -> {
                ConfigurableApplicationContext ctx = switch (label) {
                    case "annotation" -> pureAnnotation.get();
                    case "xml" -> pureXml.get();
                    default -> mixed.get();
                };
                Object service = ctx.containsBean("orderService")
                    ? ctx.getBean("orderService")
                    : ctx.getBean(AnnotatedOrderService.class);
                String result = service instanceof AnnotatedOrderService a
                    ? a.placeOrder(999)
                    : ((PlainOrderService) service).placeOrder(999);
                ctx.close();
                return label + " -> " + result;
            })
            .toList();

        results.forEach(System.out::println);

        boolean allIdenticalCharge = results.stream().allMatch(r -> r.contains("999"));
        if (!allIdenticalCharge)
            throw new AssertionError("All three configuration styles should produce the same charge amount");
        System.out.println("Pure annotation, pure XML, and mixed configuration all converged -- PASS");
    }
}
```

How to run: same classpath as Level 1 and 2, `java XmlVsAnnotationLevel3.java`.

Three completely different `ApplicationContext` construction paths — `AnnotationConfigApplicationContext` with a `@Configuration` class, `GenericXmlApplicationContext` with pure XML, and XML with a `component-scan` mixed in — all produce a bean that charges `999` cents given the same input. The lambda-based `Supplier`s make each context's construction path swappable, mirroring how a real migration might toggle between "old XML config" and "new annotation config" behind a feature flag while verifying behavioral equivalence at each step.

## 6. Walkthrough

Trace what happens for the `"mixed"` case in Level 3, since it's the one most codebases actually go through during a migration.

1. **XML parsing begins**: `GenericXmlApplicationContext.load(...)` parses the `<beans>` root, registering `paymentGateway` as a `BeanDefinition` pointing at `StripeGateway`.
2. **`<context:component-scan>` runs**: it scans `XmlVsAnnotationLevel3`'s package tree, finds `AnnotatedOrderService` (marked `@Service("orderService")`), and registers it as a second `BeanDefinition` — at this point both beans exist in the same registry, one XML-declared, one annotation-discovered.
3. **`ctx.refresh()` instantiates beans**: Spring builds `paymentGateway` first (no dependencies), producing a `StripeGateway` instance.
4. **`AnnotatedOrderService` construction**: Spring sees its constructor is `@Autowired` and needs a `PaymentGateway` — it looks in the *same* bean registry, finds the XML-declared `paymentGateway` bean (by type match, since there's only one `PaymentGateway`), and injects it — the annotation-discovered bean receives a dependency that was declared by hand in XML.
5. **`main` retrieves the service**: since `ctx.containsBean("orderService")` is true (the `@Service("orderService")` name), it fetches by that name and casts based on its runtime type.
6. **`placeOrder(999)` runs**: delegates to `gateway.charge(999)`, returning `"charged 999 cents"`.
7. **Comparison across all three contexts**: the program prints all three results and asserts each contains `"999"`, confirming pure annotation-driven, pure XML, and mixed configuration all wired the same logical dependency correctly, regardless of which style declared which half of the graph.

```
 XML: <bean id="paymentGateway" .../>  --------\
                                                 \
                                                  v
                                          same BeanDefinition registry
                                                  ^
                                                 /
 Annotation: @Service("orderService")  --------/
     @Autowired constructor asks for PaymentGateway
     -> resolved against the registry, finds the XML-declared bean
     -> injected, regardless of its declaration style
```

## 7. Gotchas & takeaways

> **Gotcha:** mixing styles works cleanly for *type-based* autowiring, but bean *names* can silently diverge between the two styles — an XML `<bean id="paymentGateway">` and an annotation-discovered `@Component` both named `"paymentGateway"` would collide (a `BeanDefinitionStoreException` on duplicate bean name) if accidentally declared twice, once in each style, during a migration. Always check for name collisions when adding `component-scan` to an XML file that already declares beans by hand.

- Both configuration styles compile down to the same internal `BeanDefinition` representation before any bean is instantiated — there's no runtime performance or capability difference between "purely annotation-driven" and "purely XML" applications.
- Dependency resolution (autowiring by type, or by name) doesn't care which style declared the bean being resolved — a `@Autowired` field can be satisfied by an XML `<bean>`, and a `<property ref="...">` can point at an annotation-discovered `@Component`, transparently.
- Migration between the two styles is almost always incremental in real codebases — `<context:component-scan>` (bringing annotations into XML) and `@ImportResource` (bringing XML into a `@Configuration` class) are the two on-ramps that make partial migration practical.
- New Spring and Spring Boot applications default to annotation-driven configuration; XML remains a valid, fully supported choice, most defensible today for legacy maintenance, deploy-without-recompiling configuration changes, or wiring classes that genuinely can't be annotated.

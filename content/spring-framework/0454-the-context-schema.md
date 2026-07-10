---
card: spring-framework
gi: 454
slug: the-context-schema
title: "The context schema"
---

## 1. What it is

The `context` namespace (`xmlns:context="http://www.springframework.org/schema/context"`) is the set of XML elements that turn on Spring's annotation-driven features from within XML configuration: `<context:component-scan>` (find `@Component`-annotated classes), `<context:annotation-config>` (activate `@Autowired`/`@Value`/`@PostConstruct` processing), a `${...}`-substitution shorthand that registers a `PropertySourcesPlaceholderConfigurer` bean for resolving values from `.properties` files, and `<context:load-time-weaver>` (enable AspectJ load-time weaving) are its most common members.

```xml
<context:component-scan base-package="com.example.service"/>
<bean class="org.springframework.context.support.PropertySourcesPlaceholderConfigurer">
    <property name="location" value="classpath:app.properties"/>
</bean>
```

## 2. Why & when

XML-based configuration predates annotation-driven configuration, but the two were never mutually exclusive — the `context` schema is the bridge: it lets an XML file declare "also scan this package for `@Component` classes" or "also process `@Autowired` annotations on any bean, including the ones defined right here in XML," so a codebase can mix a handful of hand-written XML `<bean>` definitions with a much larger set of annotation-discovered ones.

Reach for `context` elements specifically when:

- You're working in a codebase that hasn't fully moved to `@Configuration` classes and still has a root XML file, but wants annotation-based component discovery for the bulk of its beans rather than declaring every one by hand.
- You need `${...}` substitution against a `.properties` file inside XML bean definitions — a `PropertySourcesPlaceholderConfigurer` bean is the XML-era equivalent of `@PropertySource` plus Spring Boot's automatic `application.properties` loading.
- You're debugging why `@Autowired` or `@Value` isn't working in an XML-configured bean — the answer is very often a missing `<context:annotation-config>` or `<context:component-scan>` (which implies it).

In `@Configuration`-class-based or Spring Boot applications, these are handled automatically (`@ComponentScan`, `@Value` resolution from `application.properties`) — the `context` schema exists to bring that same behavior into XML.

## 3. Core concept

```
 <context:component-scan base-package="com.example">
        |
        v
 classpath scan finds every @Component/@Service/@Repository/@Controller
        |
        v
 registers each as a BeanDefinition -- AS IF hand-written in this XML file
        |
        v
 implicitly also enables <context:annotation-config/>
   (so @Autowired/@Value/@PostConstruct on those beans, and on hand-written
    XML <bean> definitions too, get processed)

 <bean class="...PropertySourcesPlaceholderConfigurer"><property name="location" .../></bean>
        |
        v
 loads the given .properties file at context-refresh time
        |
        v
 every ${key} in every <bean> definition (XML) or @Value("${key}") (annotations)
 is resolved against that loaded file
```

`component-scan` and the `${...}`-resolving configurer bean are independent, commonly used together, and both operate at context-refresh time, before any bean is actually instantiated.

## 4. Diagram

<svg viewBox="0 0 640 190" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="context:component-scan discovers annotated classes and registers them as bean definitions alongside XML-defined beans">
  <rect x="10" y="20" width="180" height="50" rx="8" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="100" y="42" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">com.example package</text>
  <text x="100" y="58" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">@Service, @Repository classes</text>

  <rect x="240" y="20" width="180" height="50" rx="8" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="330" y="42" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">&lt;context:component-scan&gt;</text>
  <text x="330" y="58" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">classpath scanner</text>

  <rect x="470" y="20" width="160" height="50" rx="8" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="550" y="42" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">bean definitions</text>
  <text x="550" y="58" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">same registry as XML beans</text>

  <rect x="240" y="120" width="180" height="50" rx="8" fill="#1c2430" stroke="#8b949e" stroke-width="1.2"/>
  <text x="330" y="142" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">hand-written &lt;bean&gt;</text>
  <text x="330" y="158" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">also gets @Autowired processing</text>

  <line x1="190" y1="45" x2="235" y2="45" stroke="#8b949e" stroke-width="2" marker-end="url(#a)"/>
  <line x1="420" y1="45" x2="465" y2="45" stroke="#8b949e" stroke-width="2" marker-end="url(#a)"/>
  <line x1="330" y1="70" x2="330" y2="115" stroke="#8b949e" stroke-width="1.5" marker-end="url(#a)"/>
  <defs><marker id="a" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#8b949e"/></marker></defs>
</svg>

`component-scan` merges annotation-discovered beans into the same registry as hand-written XML beans, and turns on `@Autowired` processing for both.

## 5. Runnable example

The scenario: a `GreetingService` discovered by `component-scan`, whose greeting prefix comes from a `${...}` value resolved by a `PropertySourcesPlaceholderConfigurer` — evolving to a scoped scan filter and then to a full mixed XML+annotation setup with `@PostConstruct`.

### Level 1 — Basic

Turn on `component-scan` alone and confirm an `@Component`-annotated class is discovered and registered without any explicit `<bean>` declaration.

```java
import org.springframework.context.support.GenericXmlApplicationContext;
import org.springframework.core.io.ByteArrayResource;
import org.springframework.stereotype.Component;

import java.nio.charset.StandardCharsets;

public class ContextSchemaLevel1 {

    @Component("greetingService")
    public static class GreetingService {
        public String greet(String name) {
            return "Hello, " + name + "!";
        }
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

                <context:component-scan base-package="ContextSchemaLevel1"/>
            </beans>
            """;

        GenericXmlApplicationContext ctx = new GenericXmlApplicationContext();
        ctx.load(new ByteArrayResource(xml.getBytes(StandardCharsets.UTF_8)));
        ctx.refresh();

        GreetingService service = ctx.getBean(GreetingService.class);
        String result = service.greet("Ada");
        System.out.println("result = " + result);

        if (!result.equals("Hello, Ada!"))
            throw new AssertionError("Unexpected greeting: " + result);
        System.out.println("component-scan discovered @Component with zero <bean> declarations -- PASS");
        ctx.close();
    }
}
```

How to run: put `spring-context` on the classpath, then `java ContextSchemaLevel1.java` on JDK 17+.

`base-package="ContextSchemaLevel1"` here scans the nested-static-class's enclosing top-level class as a package root; in a real project it would be a package name like `com.example.service`. No `<bean id="greetingService" .../>` exists anywhere in the XML — the bean is entirely a product of `@Component` plus `component-scan`.

### Level 2 — Intermediate

Add a `PropertySourcesPlaceholderConfigurer` bean so the greeting prefix comes from an externalized `.properties` file, injected via `@Value("${...}")` — showing the two mechanisms most commonly used together.

```java
import org.springframework.beans.factory.annotation.Value;
import org.springframework.context.support.GenericXmlApplicationContext;
import org.springframework.core.io.ByteArrayResource;
import org.springframework.stereotype.Component;

import java.io.File;
import java.io.FileWriter;
import java.io.IOException;
import java.nio.charset.StandardCharsets;

public class ContextSchemaLevel2 {

    @Component("greetingService")
    public static class GreetingService {
        @Value("${greeting.prefix}")
        private String prefix;

        public String greet(String name) {
            return prefix + ", " + name + "!";
        }
    }

    public static void main(String[] args) throws IOException {
        File propsFile = File.createTempFile("greeting", ".properties");
        try (FileWriter w = new FileWriter(propsFile, StandardCharsets.UTF_8)) {
            w.write("greeting.prefix=Howdy\n");
        }

        String xml = """
            <?xml version="1.0" encoding="UTF-8"?>
            <beans xmlns="http://www.springframework.org/schema/beans"
                   xmlns:context="http://www.springframework.org/schema/context"
                   xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
                   xsi:schemaLocation="http://www.springframework.org/schema/beans
                       https://www.springframework.org/schema/beans/spring-beans.xsd
                       http://www.springframework.org/schema/context
                       https://www.springframework.org/schema/context/spring-context.xsd">

                <context:component-scan base-package="ContextSchemaLevel2"/>
                <bean class="org.springframework.context.support.PropertySourcesPlaceholderConfigurer">
                    <property name="location" value="file:%s"/>
                </bean>
            </beans>
            """.formatted(propsFile.getAbsolutePath().replace("\\", "/"));

        GenericXmlApplicationContext ctx = new GenericXmlApplicationContext();
        ctx.load(new ByteArrayResource(xml.getBytes(StandardCharsets.UTF_8)));
        ctx.refresh();

        GreetingService service = ctx.getBean(GreetingService.class);
        String result = service.greet("Ada");
        System.out.println("result = " + result);

        if (!result.equals("Howdy, Ada!"))
            throw new AssertionError("Expected the resolved prefix from the properties file: " + result);
        System.out.println("PropertySourcesPlaceholderConfigurer resolved ${greeting.prefix} into @Value -- PASS");
        ctx.close();
        propsFile.delete();
    }
}
```

How to run: same classpath as Level 1, `java ContextSchemaLevel2.java`.

The `<bean class="...PropertySourcesPlaceholderConfigurer">` registers a bean that reads the given file and resolves any `${key}` it finds — including inside `@Value` annotations on scanned beans, because `component-scan` already implied `<context:annotation-config/>`, which activates `@Value` processing in the first place. Spring's `context` namespace also offers a shorthand form of this exact same registration, commonly seen in older XML configuration, that expands to the identical bean definition shown here explicitly.

### Level 3 — Advanced

Add a scan filter to exclude a class that would otherwise match, and a `@PostConstruct` method that depends on the resolved value already being set — the production-flavored shape of "scan broadly, but exclude test doubles, and validate config at startup."

```java
import jakarta.annotation.PostConstruct;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.context.annotation.ComponentScan;
import org.springframework.context.support.GenericXmlApplicationContext;
import org.springframework.core.io.ByteArrayResource;
import org.springframework.stereotype.Component;

import java.io.File;
import java.io.FileWriter;
import java.io.IOException;
import java.nio.charset.StandardCharsets;

public class ContextSchemaLevel3 {

    @Component("greetingService")
    public static class GreetingService {
        @Value("${greeting.prefix}")
        private String prefix;
        private boolean initialized = false;

        @PostConstruct
        void validate() {
            if (prefix == null || prefix.isBlank()) {
                throw new IllegalStateException("greeting.prefix must be configured");
            }
            initialized = true;
            System.out.println("[startup] GreetingService validated prefix='" + prefix + "'");
        }

        public String greet(String name) {
            if (!initialized) throw new IllegalStateException("Not yet initialized");
            return prefix + ", " + name + "!";
        }
    }

    @Component("fakeGreetingServiceForTests")
    public static class FakeGreetingService {
        public String greet(String name) { return "FAKE: " + name; }
    }

    public static void main(String[] args) throws IOException {
        File propsFile = File.createTempFile("greeting", ".properties");
        try (FileWriter w = new FileWriter(propsFile, StandardCharsets.UTF_8)) {
            w.write("greeting.prefix=Howdy\n");
        }

        String xml = """
            <?xml version="1.0" encoding="UTF-8"?>
            <beans xmlns="http://www.springframework.org/schema/beans"
                   xmlns:context="http://www.springframework.org/schema/context"
                   xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
                   xsi:schemaLocation="http://www.springframework.org/schema/beans
                       https://www.springframework.org/schema/beans/spring-beans.xsd
                       http://www.springframework.org/schema/context
                       https://www.springframework.org/schema/context/spring-context.xsd">

                <context:component-scan base-package="ContextSchemaLevel3">
                    <context:exclude-filter type="regex"
                        expression="ContextSchemaLevel3\\.FakeGreetingService"/>
                </context:component-scan>
                <bean class="org.springframework.context.support.PropertySourcesPlaceholderConfigurer">
                    <property name="location" value="file:%s"/>
                </bean>
            </beans>
            """.formatted(propsFile.getAbsolutePath().replace("\\", "/"));

        GenericXmlApplicationContext ctx = new GenericXmlApplicationContext();
        ctx.load(new ByteArrayResource(xml.getBytes(StandardCharsets.UTF_8)));
        ctx.refresh();

        GreetingService service = ctx.getBean(GreetingService.class);
        System.out.println("result = " + service.greet("Ada"));

        boolean fakeExcluded = !ctx.containsBean("fakeGreetingServiceForTests");
        System.out.println("fakeGreetingServiceForTests excluded? " + fakeExcluded);
        if (!fakeExcluded)
            throw new AssertionError("exclude-filter should have kept FakeGreetingService out");

        System.out.println("exclude-filter + @PostConstruct startup validation -- PASS");
        ctx.close();
        propsFile.delete();
    }
}
```

How to run: same classpath as Level 1 and 2, plus `jakarta.annotation-api` for `@PostConstruct`. Run with `java ContextSchemaLevel3.java`.

`<context:exclude-filter type="regex" expression="...">` narrows what `component-scan` registers, keeping `FakeGreetingService` out of the real context even though it sits in the scanned package — the kind of filter used to keep test doubles or alternate implementations from being picked up in production wiring. `@PostConstruct`'s `validate()` runs after all `@Value` injection is complete (dependency injection happens before any lifecycle callback), which is why it can safely assert `prefix` is already populated.

## 6. Walkthrough

Trace Level 3's context startup and first call.

1. **`ctx.load(...)` + `ctx.refresh()`** begins parsing the XML. The `context` namespace handler processes `<context:component-scan>` first: it scans the `ContextSchemaLevel3` package tree, finds `GreetingService` and `FakeGreetingService` (both `@Component`), applies the `exclude-filter` regex, and drops `FakeGreetingService` from the set — only `GreetingService` is registered as a `BeanDefinition`.
2. **The `PropertySourcesPlaceholderConfigurer` bean** is processed next (order within the file matters for some resolution timing, but both are resolved before bean instantiation completes): it reads the temp properties file into memory.
3. **Bean instantiation begins**: Spring creates the `GreetingService` bean. Because `component-scan` implied `<context:annotation-config/>`, the `@Value("${greeting.prefix}")` field is processed — the configurer bean resolves `${greeting.prefix}` against the loaded file, finds `Howdy`, and injects it into `prefix`.
4. **Lifecycle callback**: after all dependency injection into `GreetingService` completes, Spring calls `@PostConstruct`-annotated `validate()`. At this point `prefix` is already `"Howdy"`, so the null/blank check passes, `initialized` is set `true`, and a startup log line prints.
5. **`main` retrieves the bean** via `ctx.getBean(GreetingService.class)` — already fully constructed and validated.
6. **`service.greet("Ada")`** runs: `initialized` is `true`, so it returns `"Howdy, Ada!"`.
7. **Verification**: the program checks the greeting string, then checks `ctx.containsBean("fakeGreetingServiceForTests")` is `false`, confirming the exclude filter worked, and prints `PASS`.

```
 component-scan finds: GreetingService, FakeGreetingService
        |
        v
 exclude-filter (regex) removes: FakeGreetingService
        |
        v
 remaining: GreetingService  -->  @Value injected via PropertySourcesPlaceholderConfigurer
        |
        v
 @PostConstruct validate() runs (DI already complete) -- initialized = true
        |
        v
 greet("Ada") -> "Howdy, Ada!"
```

## 7. Gotchas & takeaways

> **Gotcha:** `<context:component-scan>` implicitly enables `<context:annotation-config/>` — but if you use `<context:annotation-config/>` *alone*, without `component-scan`, it only activates annotation processing for beans already declared elsewhere (XML `<bean>` tags); it does **not** discover new `@Component` classes on the classpath. The two solve different problems and are easy to confuse.

- `component-scan` and hand-written `<bean>` definitions coexist freely in the same XML file and the same `ApplicationContext` — there's no need to migrate everything to one style at once.
- A `PropertySourcesPlaceholderConfigurer` bean, whether registered by hand or via the `context` namespace's shorthand element, is the direct XML-era ancestor of Spring Boot's automatic `application.properties` loading; understanding one clarifies the other.
- `exclude-filter`/`include-filter` on `component-scan` are the XML equivalent of `@ComponentScan(excludeFilters = ...)` — same filter types (`annotation`, `assignable`, `regex`, `aspectj`), different syntax.
- `@PostConstruct` callbacks always run after dependency injection completes, never before — this ordering guarantee holds regardless of whether the bean was found via `component-scan` or declared by hand in XML.

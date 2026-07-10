---
card: spring-framework
gi: 452
slug: the-util-schema
title: "The util schema"
---

## 1. What it is

The `util` namespace (`xmlns:util="http://www.springframework.org/schema/util"`) is a small set of XML elements — `<util:list>`, `<util:map>`, `<util:set>`, `<util:properties>`, `<util:constant>`, and `<util:property-path>` — that let an XML bean definition build a collection, a `java.util.Properties` object, a reference to a `public static final` constant, or a nested property value, and expose it as a first-class bean that other bean definitions can inject by `ref`, without hand-writing a factory class to do it.

```xml
<beans xmlns="http://www.springframework.org/schema/beans"
       xmlns:util="http://www.springframework.org/schema/util"
       xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
       xsi:schemaLocation="http://www.springframework.org/schema/beans
           https://www.springframework.org/schema/beans/spring-beans.xsd
           http://www.springframework.org/schema/util
           https://www.springframework.org/schema/util/spring-util.xsd">

    <util:list id="allowedRoles">
        <value>ADMIN</value>
        <value>EDITOR</value>
        <value>VIEWER</value>
    </util:list>
</beans>
```

## 2. Why & when

Without the `util` namespace, building a plain `List` or `Map` bean in XML meant reaching for `ListFactoryBean`, `MapFactoryBean`, or `PropertiesFactoryBean` directly — verbose, easy to misconfigure, and not obviously readable at a glance. The `util` schema is a thin, purpose-built wrapper around exactly those factory beans, giving the same capability with syntax that reads the way the data actually looks (a `<util:list>` looks like a list).

Reach for `util` elements specifically when:

- You're maintaining an existing XML-configured Spring application (common in long-lived enterprise codebases) and need to define a reusable collection, constant, or `Properties` object as a shared bean that several other beans reference.
- You want a named, singleton collection bean — for example, a fixed list of allowed roles or a map of feature flags — that is defined once and injected wherever it's needed, rather than duplicated inline inside every bean definition that uses it.
- You're reading legacy XML configuration and need to recognize `<util:constant>` or `<util:property-path>` as ways of pulling a static field or a nested property into the bean graph, rather than mysterious custom tags.

In new code, `@Configuration` classes with plain Java collections (`List.of(...)`, a `@Bean` method returning a `Map`) accomplish the same thing with less ceremony — `util` exists primarily to support and explain XML configuration that already exists.

## 3. Core concept

```
 util:list / util:set / util:map / util:properties
        |
        v
 each expands, at parse time, into the equivalent FactoryBean
   (ListFactoryBean, SetFactoryBean, MapFactoryBean, PropertiesFactoryBean)
        |
        v
 the FactoryBean's getObject() produces a plain java.util.* instance
        |
        v
 registered under the util element's id -- injectable by <ref> like any bean

 util:constant                              util:property-path
   points at a "Class.FIELD" static field     points at "beanName.propertyName"
   -> resolves to the field's value            -> resolves to that nested getter's value
   at context-startup time                     at context-startup time
```

Every `util` element is sugar: it resolves to a real bean in the context, backed by a real `FactoryBean` or resolver class, at the moment the `ApplicationContext` is built — not lazily, not at injection time.

## 4. Diagram

<svg viewBox="0 0 640 200" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="util namespace elements expand into FactoryBeans that produce plain Java collection or value beans, injectable by ref">
  <rect x="10" y="20" width="190" height="50" rx="8" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="105" y="42" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">&lt;util:list id="roles"&gt;</text>
  <text x="105" y="58" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">XML element</text>

  <rect x="250" y="20" width="190" height="50" rx="8" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="345" y="42" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">ListFactoryBean</text>
  <text x="345" y="58" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">parsed equivalent</text>

  <rect x="490" y="20" width="140" height="50" rx="8" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="560" y="42" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">bean "roles"</text>
  <text x="560" y="58" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">a real List&lt;String&gt;</text>

  <rect x="250" y="120" width="190" height="50" rx="8" fill="#1c2430" stroke="#8b949e" stroke-width="1.2"/>
  <text x="345" y="142" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">other &lt;bean&gt; definitions</text>
  <text x="345" y="158" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">&lt;property ref="roles"/&gt;</text>

  <line x1="200" y1="45" x2="245" y2="45" stroke="#8b949e" stroke-width="2" marker-end="url(#a)"/>
  <line x1="440" y1="45" x2="485" y2="45" stroke="#8b949e" stroke-width="2" marker-end="url(#a)"/>
  <line x1="560" y1="70" x2="345" y2="115" stroke="#8b949e" stroke-width="1.5" marker-end="url(#a)"/>
  <defs><marker id="a" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#8b949e"/></marker></defs>
</svg>

An XML `util` tag is parsed into a real `FactoryBean`, which produces a plain Java object that ordinary beans then reference.

## 5. Runnable example

The scenario: a shared list of allowed roles that several services need to reference. The example evolves from loading it via `util:list` directly, to layering in `util:constant` and `util:property-path`, to a full production-flavored setup with `util:properties` loaded from a real file plus `util:map` composing multiple sources.

### Level 1 — Basic

Load a single `<util:list>` from an in-memory XML string and inject it into a plain Java bean, proving the `util` element produces a real, usable `List`.

```java
import org.springframework.context.support.GenericXmlApplicationContext;
import org.springframework.core.io.ByteArrayResource;

import java.nio.charset.StandardCharsets;
import java.util.List;

public class UtilSchemaLevel1 {

    public static void main(String[] args) {
        String xml = """
            <?xml version="1.0" encoding="UTF-8"?>
            <beans xmlns="http://www.springframework.org/schema/beans"
                   xmlns:util="http://www.springframework.org/schema/util"
                   xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
                   xsi:schemaLocation="http://www.springframework.org/schema/beans
                       https://www.springframework.org/schema/beans/spring-beans.xsd
                       http://www.springframework.org/schema/util
                       https://www.springframework.org/schema/util/spring-util.xsd">

                <util:list id="allowedRoles">
                    <value>ADMIN</value>
                    <value>EDITOR</value>
                    <value>VIEWER</value>
                </util:list>
            </beans>
            """;

        GenericXmlApplicationContext ctx = new GenericXmlApplicationContext();
        ctx.load(new ByteArrayResource(xml.getBytes(StandardCharsets.UTF_8)));
        ctx.refresh();

        @SuppressWarnings("unchecked")
        List<String> roles = (List<String>) ctx.getBean("allowedRoles");
        System.out.println("allowedRoles bean = " + roles);
        if (!roles.equals(List.of("ADMIN", "EDITOR", "VIEWER"))) {
            throw new AssertionError("Expected the three configured roles in order");
        }
        System.out.println("util:list produced a real List<String> -- PASS");
        ctx.close();
    }
}
```

How to run: put `spring-context` (and its `spring-beans` XSDs, resolved automatically from the jar) on the classpath, then `java UtilSchemaLevel1.java` on JDK 17+ (or run inside a small Maven/Gradle project with `spring-context` as a dependency).

`GenericXmlApplicationContext.load(...)` parses the in-memory XML exactly as it would parse a file, registering `allowedRoles` as a bean whose class is `java.util.List`. `ctx.getBean("allowedRoles")` returns the actual list, not a wrapper — confirming `util:list` is genuinely a `List` bean, not a special-cased XML construct visible only inside other XML.

### Level 2 — Intermediate

Add `util:constant` (pulling in a `public static final` field from a real class) and `util:property-path` (reading a nested property off another bean), showing the two other common `util` elements used alongside `util:list`.

```java
import org.springframework.context.support.GenericXmlApplicationContext;
import org.springframework.core.io.ByteArrayResource;

import java.nio.charset.StandardCharsets;
import java.util.List;

public class UtilSchemaLevel2 {

    public static final class RoleLimits {
        public static final int MAX_ROLES = 5;
    }

    public static final class RoleConfig {
        private final List<String> roles;
        public RoleConfig(List<String> roles) { this.roles = roles; }
        public int getRoleCount() { return roles.size(); }
    }

    public static void main(String[] args) {
        String xml = """
            <?xml version="1.0" encoding="UTF-8"?>
            <beans xmlns="http://www.springframework.org/schema/beans"
                   xmlns:util="http://www.springframework.org/schema/util"
                   xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
                   xsi:schemaLocation="http://www.springframework.org/schema/beans
                       https://www.springframework.org/schema/beans/spring-beans.xsd
                       http://www.springframework.org/schema/util
                       https://www.springframework.org/schema/util/spring-util.xsd">

                <util:list id="allowedRoles">
                    <value>ADMIN</value>
                    <value>EDITOR</value>
                    <value>VIEWER</value>
                </util:list>

                <util:constant id="maxRoles"
                    static-field="UtilSchemaLevel2$RoleLimits.MAX_ROLES"/>

                <bean id="roleConfig" class="UtilSchemaLevel2$RoleConfig">
                    <constructor-arg ref="allowedRoles"/>
                </bean>

                <util:property-path id="roleCount" path="roleConfig.roleCount"/>
            </beans>
            """;

        GenericXmlApplicationContext ctx = new GenericXmlApplicationContext();
        ctx.load(new ByteArrayResource(xml.getBytes(StandardCharsets.UTF_8)));
        ctx.refresh();

        Integer maxRoles = (Integer) ctx.getBean("maxRoles");
        Integer roleCount = (Integer) ctx.getBean("roleCount");

        System.out.println("maxRoles (from util:constant) = " + maxRoles);
        System.out.println("roleCount (from util:property-path) = " + roleCount);

        if (maxRoles != 5) throw new AssertionError("Expected MAX_ROLES=5 via util:constant");
        if (roleCount != 3) throw new AssertionError("Expected roleCount=3 via util:property-path");
        System.out.println("util:constant and util:property-path resolved correctly -- PASS");
        ctx.close();
    }
}
```

How to run: same classpath as Level 1, `java UtilSchemaLevel2.java`.

`util:constant` reads the static field named in `static-field` reflectively at context-startup and registers its value as a bean — here, `5`. `util:property-path` reads `roleConfig`'s `roleCount` property (via its getter, `getRoleCount()`) the same way a `${...}` SpEL expression would, but as a dedicated element, and registers *that* value (`3`) as its own bean too. Both resolve once, at startup, not on every access.

### Level 3 — Advanced

A production-flavored setup: load `util:properties` from a real classpath `.properties` file (not an inline block), merge it with an XML-defined override map using `util:map`, and use `util:list` with `list-class` to force a specific `List` implementation — mirroring how a real legacy application composes environment-specific configuration from multiple sources.

```java
import org.springframework.context.support.GenericXmlApplicationContext;
import org.springframework.core.io.ByteArrayResource;
import org.springframework.core.io.ClassPathResource;

import java.io.File;
import java.io.FileWriter;
import java.io.IOException;
import java.nio.charset.StandardCharsets;
import java.util.LinkedList;
import java.util.List;
import java.util.Map;
import java.util.Properties;

public class UtilSchemaLevel3 {

    public static void main(String[] args) throws IOException {
        // Simulate a real classpath .properties file by writing one to a temp dir
        // and adding that dir to the classpath resource search via a file: URL context.
        File dir = new File(System.getProperty("java.io.tmpdir"), "util-schema-demo");
        dir.mkdirs();
        File propsFile = new File(dir, "app.properties");
        try (FileWriter w = new FileWriter(propsFile, StandardCharsets.UTF_8)) {
            w.write("service.timeout=3000\nservice.retries=2\n");
        }

        String xml = """
            <?xml version="1.0" encoding="UTF-8"?>
            <beans xmlns="http://www.springframework.org/schema/beans"
                   xmlns:util="http://www.springframework.org/schema/util"
                   xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
                   xsi:schemaLocation="http://www.springframework.org/schema/beans
                       https://www.springframework.org/schema/beans/spring-beans.xsd
                       http://www.springframework.org/schema/util
                       https://www.springframework.org/schema/util/spring-util.xsd">

                <util:properties id="baseProps" location="file:%s"/>

                <util:map id="overrides">
                    <entry key="service.retries" value="5"/>
                    <entry key="service.region" value="eu-west-1"/>
                </util:map>

                <util:list id="allowedRoles" list-class="java.util.LinkedList">
                    <value>ADMIN</value>
                    <value>EDITOR</value>
                    <value>VIEWER</value>
                </util:list>
            </beans>
            """.formatted(propsFile.getAbsolutePath().replace("\\", "/"));

        GenericXmlApplicationContext ctx = new GenericXmlApplicationContext();
        ctx.load(new ByteArrayResource(xml.getBytes(StandardCharsets.UTF_8)));
        ctx.refresh();

        Properties baseProps = (Properties) ctx.getBean("baseProps");
        @SuppressWarnings("unchecked")
        Map<String, String> overrides = (Map<String, String>) ctx.getBean("overrides");
        @SuppressWarnings("unchecked")
        List<String> roles = (List<String>) ctx.getBean("allowedRoles");

        // Merge base + overrides, as a real bootstrap step would.
        Properties merged = new Properties();
        merged.putAll(baseProps);
        merged.putAll(overrides);

        System.out.println("merged config = " + merged);
        System.out.println("roles list implementation = " + roles.getClass().getSimpleName());

        if (!"5".equals(merged.getProperty("service.retries")))
            throw new AssertionError("Override should win: expected retries=5");
        if (!"3000".equals(merged.getProperty("service.timeout")))
            throw new AssertionError("Base value should survive when not overridden");
        if (!(roles instanceof LinkedList))
            throw new AssertionError("Expected list-class=LinkedList to be honored");

        System.out.println("util:properties + util:map merge + util:list list-class -- PASS");
        ctx.close();
        propsFile.delete();
        dir.delete();
    }
}
```

How to run: same classpath as Level 1 and 2, `java UtilSchemaLevel3.java`. The program writes its own temp `.properties` file, so no external setup is required.

`util:properties location="file:..."` loads a real `Properties` object from disk via `PropertiesFactoryBean`, exactly like an application reading an externalized config file at startup. `util:map` builds an override map inline in XML. The Java code then merges base properties with overrides the same way a real bootstrap class would combine defaults with environment-specific values, with later `putAll` calls winning — demonstrating why `service.retries` ends up `5` (from `overrides`) while `service.timeout` stays `3000` (only present in `baseProps`). `list-class="java.util.LinkedList"` shows `util:list` isn't hardcoded to produce an `ArrayList`; it accepts any concrete `List` implementation.

## 6. Walkthrough

Trace Level 3 end-to-end, since it's the most representative of real usage.

1. **Startup, before Spring is involved**: the program writes `app.properties` to a temp file — standing in for a config file that would normally already exist on disk in a deployed application.
2. **XML assembly**: the in-memory XML string declares three `util` beans — `baseProps` (a `Properties` object read from that file), `overrides` (a `Map<String,String>` defined inline), and `allowedRoles` (a `LinkedList<String>`).
3. **Context construction**: `ctx.load(...)` parses the XML into `BeanDefinition`s. Each `util` element is handled by its own `BeanDefinitionParser` (registered by the `util` namespace handler), which translates it into the corresponding `FactoryBean` definition — `PropertiesFactoryBean` for `util:properties`, `MapFactoryBean` for `util:map`, `ListFactoryBean` for `util:list`.
4. **`ctx.refresh()`**: Spring instantiates every bean definition. For `baseProps`, `PropertiesFactoryBean.getObject()` opens `app.properties` and parses it into a `Properties` instance — at this point `service.timeout=3000` and `service.retries=2` exist as real property entries in the bean graph, not text in a file anymore. For `overrides`, `MapFactoryBean.getObject()` produces a `Map` with `service.retries=5` and `service.region=eu-west-1`. For `allowedRoles`, `ListFactoryBean.getObject()` produces a `LinkedList` (honoring `list-class`) containing the three role strings.
5. **Application code (`main`)** retrieves all three beans by name via `getBean(...)` — this is the "request" in a batch/config-loading sense: asking the fully-initialized context for its beans.
6. **Merge logic**: `merged.putAll(baseProps)` then `merged.putAll(overrides)` combines the two — `service.retries` is present in both, so the second `putAll` (from `overrides`) wins, leaving `5`; `service.timeout` is only in `baseProps`, so it survives untouched at `3000`; `service.region` is added fresh from `overrides`.
7. **Output**: the program prints the merged `Properties` and the list's runtime class, then asserts the expected merge outcome and list type, printing `PASS` if both hold, or throwing an `AssertionError` describing exactly which expectation failed.
8. **Cleanup**: `ctx.close()` shuts down the context; the temp file and directory are deleted.

```
 app.properties (disk)  --PropertiesFactoryBean-->  baseProps {timeout=3000, retries=2}
                                                            \
 XML <util:map> inline  --MapFactoryBean-------->  overrides {retries=5, region=eu-west-1}
                                                            \
                                                             v
                                              merged = base, then overrides applied on top
                                              => {timeout=3000, retries=5, region=eu-west-1}
```

## 7. Gotchas & takeaways

> **Gotcha:** `util` beans resolve once, at context-startup — a `util:properties` bean does **not** re-read its source file if it changes later. If you need live-reloading configuration, you need a different mechanism (such as Spring Cloud Config or a custom refresh trigger), not `util:properties`.

- `util` elements are pure XML sugar over existing `FactoryBean` classes (`ListFactoryBean`, `MapFactoryBean`, `SetFactoryBean`, `PropertiesFactoryBean`) — nothing about them is magic or unavailable to plain Java configuration.
- `util:constant` and `util:property-path` are useful specifically for pulling a static field or a nested bean property into the bean graph as its own named, injectable bean — most other collection needs are covered by `util:list`/`util:map`/`util:set` directly.
- In XML-heavy legacy codebases, `util` namespace usage is a strong signal of shared, reusable configuration values — worth tracing back when auditing where a magic constant or list actually comes from.
- In new code written with `@Configuration` classes, prefer plain Java (`List.of(...)`, `Map.of(...)`, a constant referenced directly) — there is no equivalent "why reach for this" for `util` in Java-based configuration; it exists to serve existing XML.

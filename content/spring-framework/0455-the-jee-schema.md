---
card: spring-framework
gi: 455
slug: the-jee-schema
title: "The jee schema"
---

## 1. What it is

The `jee` namespace (`xmlns:jee="http://www.springframework.org/schema/jee"`) is a small set of XML elements for integrating with Java EE (now Jakarta EE) container services from XML configuration — most importantly `<jee:jndi-lookup>`, which looks up a resource (a `DataSource`, a `ConnectionFactory`, an EJB reference) from a JNDI directory and exposes it as an ordinary Spring bean. Older versions also included `<jee:remote-slsb>` and `<jee:local-slsb>` for looking up remote/local stateless session EJBs, both long removed as EJB remoting fell out of use; `jndi-lookup` is the element still commonly seen today.

```xml
<jee:jndi-lookup id="dataSource"
    jndi-name="java:comp/env/jdbc/MyDataSource"
    expected-type="javax.sql.DataSource"/>
```

## 2. Why & when

Application servers (Tomcat, WildFly, WebSphere, and others) traditionally manage certain resources — connection pools, JMS connection factories — themselves, and expose them to deployed applications through JNDI rather than letting the application construct them directly. `<jee:jndi-lookup>` is the bridge: it performs the JNDI lookup once, at context-startup, and registers the result as a normal Spring bean that the rest of the application can inject with `@Autowired` or `ref`, without any code needing to know JNDI exists.

Reach for `jee:jndi-lookup` specifically when:

- Your application is deployed into an application server that provisions a `DataSource` (or similar resource) via JNDI, and your Spring configuration needs to obtain that exact pooled instance rather than creating its own.
- You're maintaining legacy XML configuration in an enterprise codebase where resources were always sourced this way, and need to understand or modify how a given bean's underlying connection pool is obtained.
- You want the container (not your application) to own connection-pool lifecycle and configuration, common in traditional application-server deployments as opposed to Spring Boot's embedded-server, self-configured-`DataSource` model.

In a Spring Boot application with an embedded server, `DataSource` beans are normally auto-configured directly from `application.properties` — `jee:jndi-lookup` exists for the traditional application-server deployment model where Spring Boot's approach doesn't apply.

## 3. Core concept

```
 Application server (e.g. Tomcat, WildFly)
        |
        | provisions and binds a resource under a JNDI name
        v
 JNDI directory:  "java:comp/env/jdbc/MyDataSource"  ->  a real DataSource instance
        |
        | <jee:jndi-lookup jndi-name="java:comp/env/jdbc/MyDataSource"/>
        v
 Spring performs the lookup ONCE at context-refresh time
        |
        v
 registers the looked-up object as bean "dataSource"
        |
        v
 injectable anywhere else in the context, exactly like any other bean
```

The application never calls `InitialContext.lookup(...)` itself — `jee:jndi-lookup` does it once, and the rest of the codebase only ever sees a plain Spring bean.

## 4. Diagram

<svg viewBox="0 0 640 180" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="jee:jndi-lookup resolves a JNDI-bound resource once at startup and exposes it as a plain Spring bean">
  <rect x="10" y="20" width="170" height="50" rx="8" fill="#1c2430" stroke="#8b949e" stroke-width="1.2"/>
  <text x="95" y="42" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">App server</text>
  <text x="95" y="58" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">provisions DataSource</text>

  <rect x="230" y="20" width="180" height="50" rx="8" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="320" y="42" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">JNDI directory</text>
  <text x="320" y="58" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">java:comp/env/jdbc/...</text>

  <rect x="460" y="20" width="170" height="50" rx="8" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="545" y="42" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">bean "dataSource"</text>
  <text x="545" y="58" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">via jee:jndi-lookup</text>

  <line x1="180" y1="45" x2="225" y2="45" stroke="#8b949e" stroke-width="2" marker-end="url(#a)"/>
  <line x1="410" y1="45" x2="455" y2="45" stroke="#8b949e" stroke-width="2" marker-end="url(#a)"/>
  <defs><marker id="a" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#8b949e"/></marker></defs>
</svg>

The lookup happens once, at startup; everything downstream sees only a normal bean.

## 5. Runnable example

Since a real JNDI directory requires an application server, the scenario uses `SimpleNamingContextBuilder`-style manual JNDI binding (the standard way to exercise JNDI lookups in a plain JVM test or demo) to bind a fake `DataSource` and prove `jee:jndi-lookup` resolves it — evolving from a basic lookup, to a typed lookup with `expected-type`, to a full setup with a default fallback value for environments where the resource isn't bound.

### Level 1 — Basic

Bind an object under a JNDI name using `javax.naming` directly, then use `<jee:jndi-lookup>` to retrieve it as a Spring bean.

```java
import org.springframework.context.support.GenericXmlApplicationContext;
import org.springframework.core.io.ByteArrayResource;

import javax.naming.Context;
import javax.naming.InitialContext;
import javax.naming.NamingException;
import javax.naming.spi.InitialContextFactory;
import javax.naming.spi.NamingManager;
import java.nio.charset.StandardCharsets;
import java.util.Hashtable;
import java.util.concurrent.ConcurrentHashMap;
import java.util.Map;

public class JeeSchemaLevel1 {

    // A minimal in-memory JNDI provider so this example needs no real app server.
    public static class InMemoryContextFactory implements InitialContextFactory {
        static final Map<String, Object> BINDINGS = new ConcurrentHashMap<>();
        @Override
        public Context getInitialContext(Hashtable<?, ?> env) {
            return (Context) java.lang.reflect.Proxy.newProxyInstance(
                Context.class.getClassLoader(), new Class[]{Context.class},
                (proxy, method, args) -> {
                    if (method.getName().equals("lookup")) return BINDINGS.get(String.valueOf(args[0]));
                    if (method.getName().equals("bind")) { BINDINGS.put(String.valueOf(args[0]), args[1]); return null; }
                    if (method.getName().equals("close")) return null;
                    throw new UnsupportedOperationException(method.getName());
                });
        }
    }

    public static void main(String[] args) throws NamingException {
        System.setProperty(Context.INITIAL_CONTEXT_FACTORY, InMemoryContextFactory.class.getName());
        Object fakeDataSource = new Object() {
            @Override public String toString() { return "FakeDataSource[pool=5]"; }
        };
        InMemoryContextFactory.BINDINGS.put("java:comp/env/jdbc/MyDataSource", fakeDataSource);

        String xml = """
            <?xml version="1.0" encoding="UTF-8"?>
            <beans xmlns="http://www.springframework.org/schema/beans"
                   xmlns:jee="http://www.springframework.org/schema/jee"
                   xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
                   xsi:schemaLocation="http://www.springframework.org/schema/beans
                       https://www.springframework.org/schema/beans/spring-beans.xsd
                       http://www.springframework.org/schema/jee
                       https://www.springframework.org/schema/jee/spring-jee.xsd">

                <jee:jndi-lookup id="dataSource"
                    jndi-name="java:comp/env/jdbc/MyDataSource"/>
            </beans>
            """;

        GenericXmlApplicationContext ctx = new GenericXmlApplicationContext();
        ctx.load(new ByteArrayResource(xml.getBytes(StandardCharsets.UTF_8)));
        ctx.refresh();

        Object dataSource = ctx.getBean("dataSource");
        System.out.println("dataSource bean = " + dataSource);
        if (dataSource != fakeDataSource)
            throw new AssertionError("Expected the exact bound instance to be returned");
        System.out.println("jee:jndi-lookup resolved the JNDI-bound object -- PASS");
        ctx.close();
    }
}
```

How to run: put `spring-context` on the classpath, then `java JeeSchemaLevel1.java` on JDK 17+.

`InMemoryContextFactory` stands in for a real application server's JNDI provider, letting the lookup mechanism be demonstrated without one. `<jee:jndi-lookup jndi-name="...">` calls `InitialContext.lookup(...)` exactly once, at context-refresh time, and registers whatever it finds as bean `dataSource` — the identity check (`==`) confirms it's the literal bound object, not a copy.

### Level 2 — Intermediate

Add `expected-type` so Spring validates the looked-up object's type at startup, catching a JNDI misconfiguration immediately instead of failing later with a confusing `ClassCastException`.

```java
import org.springframework.context.support.GenericXmlApplicationContext;
import org.springframework.core.io.ByteArrayResource;

import javax.naming.Context;
import javax.naming.NamingException;
import javax.naming.spi.InitialContextFactory;
import java.nio.charset.StandardCharsets;
import java.util.Hashtable;
import java.util.Map;
import java.util.concurrent.ConcurrentHashMap;

public class JeeSchemaLevel2 {

    public interface DataSource {
        String describe();
    }

    public static class InMemoryContextFactory implements InitialContextFactory {
        static final Map<String, Object> BINDINGS = new ConcurrentHashMap<>();
        @Override
        public Context getInitialContext(Hashtable<?, ?> env) {
            return (Context) java.lang.reflect.Proxy.newProxyInstance(
                Context.class.getClassLoader(), new Class[]{Context.class},
                (proxy, method, args) -> {
                    if (method.getName().equals("lookup")) return BINDINGS.get(String.valueOf(args[0]));
                    if (method.getName().equals("close")) return null;
                    throw new UnsupportedOperationException(method.getName());
                });
        }
    }

    public static void main(String[] args) throws NamingException {
        System.setProperty(Context.INITIAL_CONTEXT_FACTORY, InMemoryContextFactory.class.getName());
        // Intentionally bind a String, not a DataSource, to trigger the expected-type check.
        InMemoryContextFactory.BINDINGS.put("java:comp/env/jdbc/MyDataSource", "not-a-datasource");

        String xml = """
            <?xml version="1.0" encoding="UTF-8"?>
            <beans xmlns="http://www.springframework.org/schema/beans"
                   xmlns:jee="http://www.springframework.org/schema/jee"
                   xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
                   xsi:schemaLocation="http://www.springframework.org/schema/beans
                       https://www.springframework.org/schema/beans/spring-beans.xsd
                       http://www.springframework.org/schema/jee
                       https://www.springframework.org/schema/jee/spring-jee.xsd">

                <jee:jndi-lookup id="dataSource"
                    jndi-name="java:comp/env/jdbc/MyDataSource"
                    expected-type="JeeSchemaLevel2$DataSource"/>
            </beans>
            """;

        GenericXmlApplicationContext ctx = new GenericXmlApplicationContext();
        ctx.load(new ByteArrayResource(xml.getBytes(StandardCharsets.UTF_8)));

        try {
            ctx.refresh();
            throw new AssertionError("Expected refresh() to fail on a type mismatch");
        } catch (Exception expected) {
            System.out.println("Startup failed fast as expected: " + expected.getClass().getSimpleName());
            System.out.println("expected-type caught the JNDI misconfiguration at startup -- PASS");
        }
    }
}
```

How to run: same classpath as Level 1, `java JeeSchemaLevel2.java`.

`expected-type="..."` makes `jee:jndi-lookup` verify the looked-up object is assignable to the given type immediately after the lookup, during `ctx.refresh()`. Binding a plain `String` under the JNDI name where a `DataSource` was expected causes context refresh itself to fail with a clear type-mismatch error — far easier to diagnose than a `ClassCastException` deep inside application code the first time the bean is actually used.

### Level 3 — Advanced

Add `default-object`/`default-ref`-style fallback behavior (via `<jee:jndi-lookup>`'s nested `<default-value>` for a `cache-name`-style resource) so the application degrades gracefully in environments (such as local development) where the JNDI resource genuinely isn't bound, rather than failing context startup outright.

```java
import org.springframework.context.support.GenericXmlApplicationContext;
import org.springframework.core.io.ByteArrayResource;

import javax.naming.Context;
import javax.naming.NamingException;
import javax.naming.spi.InitialContextFactory;
import java.nio.charset.StandardCharsets;
import java.util.Hashtable;
import java.util.Map;
import java.util.concurrent.ConcurrentHashMap;

public class JeeSchemaLevel3 {

    public static class InMemoryContextFactory implements InitialContextFactory {
        static final Map<String, Object> BINDINGS = new ConcurrentHashMap<>();
        @Override
        public Context getInitialContext(Hashtable<?, ?> env) {
            return (Context) java.lang.reflect.Proxy.newProxyInstance(
                Context.class.getClassLoader(), new Class[]{Context.class},
                (proxy, method, args) -> {
                    if (method.getName().equals("lookup")) {
                        Object found = BINDINGS.get(String.valueOf(args[0]));
                        if (found == null) throw new javax.naming.NameNotFoundException(String.valueOf(args[0]));
                        return found;
                    }
                    if (method.getName().equals("close")) return null;
                    throw new UnsupportedOperationException(method.getName());
                });
        }
    }

    public static void main(String[] args) throws NamingException {
        System.setProperty(Context.INITIAL_CONTEXT_FACTORY, InMemoryContextFactory.class.getName());
        // Note: nothing is bound under this name, simulating a local dev environment
        // without the app-server-managed resource.

        String xml = """
            <?xml version="1.0" encoding="UTF-8"?>
            <beans xmlns="http://www.springframework.org/schema/beans"
                   xmlns:jee="http://www.springframework.org/schema/jee"
                   xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
                   xsi:schemaLocation="http://www.springframework.org/schema/beans
                       https://www.springframework.org/schema/beans/spring-beans.xsd
                       http://www.springframework.org/schema/jee
                       https://www.springframework.org/schema/jee/spring-jee.xsd">

                <jee:jndi-lookup id="maxPoolSize"
                    jndi-name="java:comp/env/config/maxPoolSize"
                    default-value="10"/>
            </beans>
            """;

        GenericXmlApplicationContext ctx = new GenericXmlApplicationContext();
        ctx.load(new ByteArrayResource(xml.getBytes(StandardCharsets.UTF_8)));
        ctx.refresh();

        Object maxPoolSize = ctx.getBean("maxPoolSize");
        System.out.println("maxPoolSize (unbound, fell back to default) = " + maxPoolSize);
        if (!"10".equals(maxPoolSize))
            throw new AssertionError("Expected default-value fallback of 10");

        // Now bind a real value and rebuild the context to show the JNDI value wins when present.
        InMemoryContextFactory.BINDINGS.put("java:comp/env/config/maxPoolSize", "50");
        GenericXmlApplicationContext ctx2 = new GenericXmlApplicationContext();
        ctx2.load(new ByteArrayResource(xml.getBytes(StandardCharsets.UTF_8)));
        ctx2.refresh();
        Object boundValue = ctx2.getBean("maxPoolSize");
        System.out.println("maxPoolSize (bound in JNDI) = " + boundValue);
        if (!"50".equals(boundValue))
            throw new AssertionError("Expected the actual JNDI-bound value of 50 to win");

        System.out.println("default-value fallback + real JNDI override -- PASS");
        ctx.close();
        ctx2.close();
    }
}
```

How to run: same classpath as Level 1 and 2, `java JeeSchemaLevel3.java`.

`default-value="10"` makes `jee:jndi-lookup` fall back to `"10"` instead of failing context startup when the JNDI name isn't bound — useful for configuration values that have a sane default but may be overridden per-environment via the container's JNDI resources. The second context (`ctx2`), built after binding a real value under the same name, shows the JNDI-bound value takes priority over the default when it actually exists.

## 6. Walkthrough

Trace Level 3's two context builds.

1. **First context (`ctx`)**: no value is bound under `java:comp/env/config/maxPoolSize` in `InMemoryContextFactory.BINDINGS`. During `ctx.refresh()`, Spring's `JndiObjectFactoryBean` (which `jee:jndi-lookup` compiles down to) attempts `InitialContext.lookup("java:comp/env/config/maxPoolSize")`.
2. **Lookup fails**: the fake context throws `NameNotFoundException`, simulating an environment where the resource genuinely isn't provisioned.
3. **Fallback engages**: because `default-value="10"` is set, `JndiObjectFactoryBean` catches the naming failure and uses `"10"` instead of propagating the exception — bean `maxPoolSize` ends up registered with value `"10"`.
4. **`main` retrieves and checks** `maxPoolSize`, confirming it's `"10"`.
5. **Binding changes**: the program binds `"50"` under the same JNDI name — simulating deploying to an environment where the app server *does* provision this resource.
6. **Second context (`ctx2`)** is built from the same XML. This time the lookup succeeds immediately, returning `"50"`; `default-value` is never consulted because it only applies when the lookup itself fails.
7. **Verification**: the program confirms `maxPoolSize` is now `"50"`, proving the JNDI-bound value takes priority whenever it's actually present, and the default is a pure fallback, not an override.

```
 lookup("java:comp/env/config/maxPoolSize")
        |
        +-- not bound --> NameNotFoundException --> use default-value "10"
        |
        +-- bound to "50" --> lookup succeeds --> use "50" (default-value ignored)
```

## 7. Gotchas & takeaways

> **Gotcha:** `<jee:remote-slsb>` and `<jee:local-slsb>` (for looking up EJBs) were removed as EJB remoting fell out of favor — if you see them referenced in old documentation or a very old codebase, treat them as historical; `jndi-lookup` is the element still in active use for resource lookups like `DataSource`s.

- `jee:jndi-lookup` performs its lookup once, at context-refresh time — it does not re-check JNDI on every bean access, so a resource rebound later in the running application server won't be picked up without a context restart.
- `expected-type` turns a potential runtime `ClassCastException` (discovered whenever the bean happens to be used) into an immediate context-startup failure — always set it when the exact type matters.
- `default-value` (or `default-ref` for bean references) is a startup-time fallback used only when the lookup itself fails — it never overrides a value that genuinely exists in JNDI.
- This schema matters most for traditional application-server deployments; Spring Boot applications with embedded servers typically configure resources like `DataSource`s directly rather than through JNDI.

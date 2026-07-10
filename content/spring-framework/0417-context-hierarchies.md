---
card: spring-framework
gi: 417
slug: context-hierarchies
title: "Context hierarchies"
---

## 1. What it is

A context hierarchy is a parent/child relationship between two or more `ApplicationContext` instances: a child context can see and resolve beans from its parent, but the parent has no visibility into the child's beans. This is a real, production feature of Spring — not just a testing construct — most classically seen in traditional Spring MVC web applications, which typically have a **root** `ApplicationContext` (services, repositories, shared infrastructure) and one or more **child** web contexts (one per `DispatcherServlet`, holding controllers and web-specific beans).

```java
// Root context: shared across the whole web application
AnnotationConfigWebApplicationContext rootContext = new AnnotationConfigWebApplicationContext();
rootContext.register(RootConfig.class); // services, repositories

// Child (Servlet-specific) context: web layer only, parent = rootContext
AnnotationConfigWebApplicationContext servletContext = new AnnotationConfigWebApplicationContext();
servletContext.register(WebConfig.class); // controllers
servletContext.setParent(rootContext);
```

## 2. Why & when

A traditional Spring MVC application can have multiple `DispatcherServlet`s (rare, but supported) mapped to different URL patterns, each wanting its own set of controllers and web-specific beans — but all of them needing access to the *same* shared services, repositories, and infrastructure beans. Without a hierarchy, you'd either duplicate the shared beans in each servlet's context (wasteful, and each duplicate would be a *separate* instance — breaking singleton assumptions across servlets) or flatten everything into one giant context (losing the useful separation between "shared business layer" and "this specific servlet's web layer"). A context hierarchy solves this: one root context holds the shared beans once, and each child context adds only what's specific to it, while still being able to resolve the shared beans through parent delegation.

You'll encounter or reach for context hierarchies when:

- Working with (or maintaining) a traditional Spring MVC application using `ContextLoaderListener` (root context) plus `DispatcherServlet` (child context) — this is the classic, most common hierarchy in real deployments, often set up by default without you thinking about it explicitly.
- Running multiple `DispatcherServlet`s in one application that need isolated web-layer beans but shared services.
- Writing integration tests that need to model this exact relationship, to verify your beans are registered at the right level (the previous card's `@ContextHierarchy` example).

Most single-`DispatcherServlet` Spring Boot applications don't need to think about this explicitly — Spring Boot typically uses one flat context — but understanding the hierarchy concept is essential for working with traditional Spring MVC deployments and for correctly diagnosing "why can't my controller see this bean" issues that stem from it.

## 3. Core concept

```
                     Root ApplicationContext
                     (services, repositories,
                      shared infrastructure)
                              ^
                              | parent
                              |
              +---------------+---------------+
              |                               |
     Servlet Context A              Servlet Context B
     (controllers for                (controllers for
      /api/v1/**)                     /api/v2/**)

  Servlet Context A CAN resolve beans from Root (delegation upward)
  Root CANNOT resolve beans from either Servlet Context (no downward visibility)
  Servlet Context A CANNOT resolve beans from Servlet Context B (siblings are isolated)
```

Delegation is strictly one-directional and only along the parent chain — a child asks its immediate parent when it can't satisfy a lookup itself, and that request can chain further up if the parent also has a parent, but never sideways between siblings and never downward from parent to child.

## 4. Diagram

<svg viewBox="0 0 640 210" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Root context with two independent child servlet contexts, each able to see root beans but not each other">
  <rect x="230" y="20" width="180" height="50" rx="8" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="320" y="42" fill="#e6edf3" font-size="11" text-anchor="middle" font-family="sans-serif">Root context</text>
  <text x="320" y="58" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">services, repositories</text>

  <rect x="60" y="130" width="200" height="50" rx="8" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="160" y="152" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">Servlet context A</text>
  <text x="160" y="168" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">controllers /api/v1/**</text>

  <rect x="380" y="130" width="200" height="50" rx="8" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="480" y="152" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">Servlet context B</text>
  <text x="480" y="168" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">controllers /api/v2/**</text>

  <line x1="160" y1="128" x2="290" y2="72" stroke="#3fb950" stroke-width="1.5" marker-end="url(#a)"/>
  <line x1="480" y1="128" x2="350" y2="72" stroke="#3fb950" stroke-width="1.5" marker-end="url(#a)"/>
  <text x="320" y="105" fill="#3fb950" font-size="9" text-anchor="middle" font-family="sans-serif">delegation (upward only)</text>
  <line x1="260" y1="155" x2="380" y2="155" stroke="#8b949e" stroke-width="1" stroke-dasharray="3"/>
  <text x="320" y="196" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">A and B are isolated siblings -- no visibility between them</text>
  <defs><marker id="a" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#3fb950"/></marker></defs>
</svg>

Both children delegate upward to the same shared root; neither can see the other's beans.

## 5. Runnable example

### Level 1 — Basic

Build a minimal two-level context hierarchy programmatically (outside of any Servlet container, to keep the example self-contained) and confirm the child resolves a parent bean via delegation.

```java
import org.springframework.context.annotation.*;
import org.springframework.context.support.AbstractApplicationContext;

public class ContextHierarchiesBasic {

    static class UserRepository {
        String describe() { return "shared UserRepository (root level)"; }
    }

    static class UserController {
        String describe() { return "web-layer UserController (child level)"; }
    }

    @Configuration
    static class RootConfig {
        @Bean UserRepository userRepository() { return new UserRepository(); }
    }

    @Configuration
    static class WebConfig {
        @Bean UserController userController() { return new UserController(); }
    }

    public static void main(String[] args) {
        AnnotationConfigApplicationContext rootContext = new AnnotationConfigApplicationContext();
        rootContext.register(RootConfig.class);
        rootContext.refresh();

        AnnotationConfigApplicationContext childContext = new AnnotationConfigApplicationContext();
        childContext.register(WebConfig.class);
        childContext.setParent(rootContext); // establishes the hierarchy
        childContext.refresh();

        UserController controller = childContext.getBean(UserController.class);
        System.out.println("Child resolved its own bean: " + controller.describe());

        UserRepository repository = childContext.getBean(UserRepository.class); // delegates to parent
        System.out.println("Child resolved parent bean via delegation: " + repository.describe());

        childContext.close();
        rootContext.close();
    }
}
```

How to run: add `spring-context` to the classpath, then `java ContextHierarchiesBasic.java`.

`childContext.setParent(rootContext)` is the entire mechanism — it establishes the delegation relationship before `refresh()` finalizes the child context. `childContext.getBean(UserRepository.class)` succeeds even though `UserRepository` was never registered in `WebConfig`, because the child's bean-resolution logic automatically falls back to asking its parent when a bean isn't found locally.

### Level 2 — Intermediate

Confirm the reverse fails as expected (parent cannot see child beans), and show two sibling child contexts sharing one root while remaining isolated from each other — modeling the two-`DispatcherServlet` scenario from the concept section.

```java
import org.springframework.beans.factory.NoSuchBeanDefinitionException;
import org.springframework.context.annotation.*;

public class ContextHierarchiesIntermediate {

    static class SharedAuthService {
        String describe() { return "shared AuthService"; }
    }

    static class V1Controller { String describe() { return "v1 controller"; } }
    static class V2Controller { String describe() { return "v2 controller"; } }

    @Configuration
    static class RootConfig {
        @Bean SharedAuthService authService() { return new SharedAuthService(); }
    }

    @Configuration
    static class V1WebConfig {
        @Bean V1Controller v1Controller() { return new V1Controller(); }
    }

    @Configuration
    static class V2WebConfig {
        @Bean V2Controller v2Controller() { return new V2Controller(); }
    }

    public static void main(String[] args) {
        AnnotationConfigApplicationContext rootContext = new AnnotationConfigApplicationContext();
        rootContext.register(RootConfig.class);
        rootContext.refresh();

        AnnotationConfigApplicationContext v1Context = new AnnotationConfigApplicationContext();
        v1Context.register(V1WebConfig.class);
        v1Context.setParent(rootContext);
        v1Context.refresh();

        AnnotationConfigApplicationContext v2Context = new AnnotationConfigApplicationContext();
        v2Context.register(V2WebConfig.class);
        v2Context.setParent(rootContext);
        v2Context.refresh();

        System.out.println("v1Context sees shared service: " + v1Context.getBean(SharedAuthService.class).describe());
        System.out.println("v2Context sees shared service: " + v2Context.getBean(SharedAuthService.class).describe());
        System.out.println("Same instance shared across both? "
                + (v1Context.getBean(SharedAuthService.class) == v2Context.getBean(SharedAuthService.class)));

        try {
            v1Context.getBean(V2Controller.class);
            throw new AssertionError("v1Context should NOT see v2Context's beans");
        } catch (NoSuchBeanDefinitionException e) {
            System.out.println("Confirmed: v1Context correctly cannot see V2Controller (sibling isolation) -- PASS");
        }

        try {
            rootContext.getBean(V1Controller.class);
            throw new AssertionError("rootContext should NOT see child beans");
        } catch (NoSuchBeanDefinitionException e) {
            System.out.println("Confirmed: rootContext correctly cannot see V1Controller (no downward visibility) -- PASS");
        }

        v1Context.close(); v2Context.close(); rootContext.close();
    }
}
```

How to run: `java ContextHierarchiesIntermediate.java` (same classpath as Level 1).

Both `v1Context` and `v2Context` resolve `SharedAuthService` to the *exact same instance* (proven by reference equality), because both delegate to the same single `rootContext` — this is precisely the benefit a hierarchy provides over duplicating shared beans in each child: one real singleton, not one per servlet. The two `catch` blocks confirm both isolation rules explicitly: siblings can't see each other, and a parent can't see any child's beans.

### Level 3 — Advanced

Model context-hierarchy-aware lifecycle: closing the root context while children are still active is a real operational hazard (it happens, for example, during certain Servlet container shutdown sequences if listeners aren't ordered correctly) — this demonstrates the failure mode and the correct shutdown order.

```java
import org.springframework.beans.factory.NoSuchBeanDefinitionException;
import org.springframework.context.annotation.*;
import org.springframework.context.event.ContextClosedEvent;
import org.springframework.context.event.EventListener;

public class ContextHierarchiesAdvanced {

    static class DatabaseConnectionPool implements AutoCloseable {
        boolean closed = false;
        void query() {
            if (closed) throw new IllegalStateException("Pool is closed -- cannot query!");
            System.out.println("Query executed successfully");
        }
        @Override public void close() { closed = true; System.out.println("DatabaseConnectionPool closed"); }
    }

    static class ReportingService {
        private final DatabaseConnectionPool pool;
        ReportingService(DatabaseConnectionPool pool) { this.pool = pool; }
        void generateReport() { pool.query(); }
    }

    @Configuration
    static class RootConfig {
        @Bean(destroyMethod = "close")
        DatabaseConnectionPool connectionPool() { return new DatabaseConnectionPool(); }
    }

    @Configuration
    static class ChildConfig {
        @Bean
        ReportingService reportingService(DatabaseConnectionPool pool) { return new ReportingService(pool); }
    }

    public static void main(String[] args) {
        AnnotationConfigApplicationContext rootContext = new AnnotationConfigApplicationContext();
        rootContext.register(RootConfig.class);
        rootContext.refresh();

        AnnotationConfigApplicationContext childContext = new AnnotationConfigApplicationContext();
        childContext.register(ChildConfig.class);
        childContext.setParent(rootContext);
        childContext.refresh();

        ReportingService reportingService = childContext.getBean(ReportingService.class);
        reportingService.generateReport(); // works fine while both contexts are open

        System.out.println("--- Demonstrating the CORRECT shutdown order: child first, then parent ---");
        childContext.close();  // release child-level resources/listeners first
        rootContext.close();   // then release shared infrastructure
        System.out.println("Clean shutdown complete: no active child was left pointing at a closed parent.");

        System.out.println();
        System.out.println("--- Demonstrating the INCORRECT order (parent closed while a child is still active) ---");
        AnnotationConfigApplicationContext root2 = new AnnotationConfigApplicationContext();
        root2.register(RootConfig.class);
        root2.refresh();
        AnnotationConfigApplicationContext child2 = new AnnotationConfigApplicationContext();
        child2.register(ChildConfig.class);
        child2.setParent(root2);
        child2.refresh();

        root2.close(); // WRONG order: parent closed first, destroying the shared connection pool

        ReportingService stillReferenced = child2.getBean(ReportingService.class); // child itself is still open
        try {
            stillReferenced.generateReport(); // but the pool it depends on was already destroyed
            throw new AssertionError("Expected failure due to premature parent shutdown");
        } catch (IllegalStateException e) {
            System.out.println("As expected, using a bean whose dependency lived in a "
                    + "prematurely-closed parent fails: " + e.getMessage());
        }
        child2.close();
    }
}
```

How to run: `java ContextHierarchiesAdvanced.java` (same classpath as Level 1).

The correct shutdown order — children before parent — mirrors how a well-behaved Servlet container tears down `DispatcherServlet`s before the root `ContextLoaderListener`, ensuring nothing still-active is left depending on already-destroyed shared infrastructure. The deliberately incorrect ordering in the second half shows exactly what breaks otherwise: `rootContext.close()` invokes `DatabaseConnectionPool`'s `destroyMethod = "close"`, and any subsequent use of that pool (even indirectly, through a still-open child context's `ReportingService`) fails, because the shared resource the child depends on no longer exists.

## 6. Walkthrough

Trace the "incorrect order" scenario in `ContextHierarchiesAdvanced.main`:

1. **Both contexts start healthy.** `root2` (holding `DatabaseConnectionPool`) and `child2` (holding `ReportingService`, which depends on that pool) are both refreshed and operational; `child2.getBean(ReportingService.class)` would work correctly at this point.
2. **Root closed first (the bug).** `root2.close()` runs Spring's shutdown sequence for the root context: it invokes `destroyMethod = "close"` on `DatabaseConnectionPool`, setting its internal `closed` flag to `true` and printing `"DatabaseConnectionPool closed"`. Critically, `root2.close()` has no awareness that `child2` still exists and still depends on this now-destroyed bean — there is no automatic mechanism ordering child shutdown before parent shutdown; that ordering is the *caller's* responsibility.
3. **Child context is still technically alive.** `child2.getBean(ReportingService.class)` still succeeds — the child context itself was never closed, and `ReportingService` is still a live bean within it, holding a reference to the now-closed `DatabaseConnectionPool` object.
4. **The stale reference fails at use, not at lookup.** Calling `stillReferenced.generateReport()` invokes `pool.query()`, which checks its own `closed` flag (set in step 2) and throws `IllegalStateException("Pool is closed -- cannot query!")` — the failure surfaces only when the stale dependency is actually *used*, not when it was originally injected or when it's merely referenced.
5. **Root cause, restated.** The underlying issue is entirely about shutdown ordering: closing a parent context while children referencing its beans remain open leaves those children holding references to destroyed objects. This is exactly why real Servlet containers are careful to shut down child (Servlet) contexts before the root context — `ContextLoaderListener`'s `contextDestroyed` runs after the Servlet container has already torn down the `DispatcherServlet`s and their child contexts.

```
Correct order:
  child2.close()   -- releases child-level beans/resources first
  root2.close()    -- then releases shared infrastructure -- nothing left depending on it

Incorrect order (this demo):
  root2.close()    -- destroys DatabaseConnectionPool while child2 still holds a reference to it
  child2 still "open" but its ReportingService now depends on a dead pool
  stillReferenced.generateReport() -- fails: IllegalStateException
```

## 7. Gotchas & takeaways

> Gotcha: closing a parent context while a child context built from it is still active does not automatically close or invalidate the child — the child remains technically usable, and beans within it that don't touch the destroyed parent-level beans continue working fine, which can make this class of bug intermittent and confusing (some operations on the "broken" child still succeed) rather than an immediate, obvious failure.

- Context hierarchies are a real production mechanism (not just a testing tool) for sharing one set of infrastructure beans across multiple isolated child contexts — most classically, a Spring MVC root context shared by one or more `DispatcherServlet` child contexts.
- Delegation is strictly upward (child asks parent) and never sideways (between siblings) or downward (parent asking a child) — design your bean placement (which context a bean belongs in) with this one-directional visibility in mind.
- Multiple children sharing one root see the exact same singleton instances from that root, which is the direct benefit over duplicating shared beans into each child separately.
- Always close child contexts before their parent — reversing that order leaves children holding references to already-destroyed parent-level beans, a bug that can be intermittent rather than immediately obvious.

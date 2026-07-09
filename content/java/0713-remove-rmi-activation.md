---
card: java
gi: 713
slug: remove-rmi-activation
title: Remove RMI Activation
---

## 1. What it is

**Java 17** (JEP 407) **removed RMI Activation** entirely from the JDK — the `java.rmi.activation` package, the `rmid` activation daemon executable, and the associated `Activatable` class are all gone. RMI Activation was a mechanism, part of Java Remote Method Invocation (RMI) since Java 1.2, that let a remote object be lazily started ("activated") on demand by a separate daemon process the first time a client tried to invoke a method on it, rather than requiring the object's hosting process to already be running. This is a genuine removal, not a deprecation: code that imports `java.rmi.activation.*` simply fails to compile on Java 17. The mechanism had already been marked deprecated for removal one release earlier, in Java 15 (JEP 385), giving the ecosystem an explicit release's worth of advance warning before this JEP completed the removal.

## 2. Why & when

RMI Activation solved a real problem in the 1990s — letting a remote object come into existence on demand, without a server operator having to keep every possible remote service running continuously — but by the time of its Java 15 deprecation, it had seen essentially no meaningful use for years, while remaining a genuine maintenance burden: it was RMI's most complex feature, its own security model was hard to reason about correctly, and modern service architectures (long-running server processes managed by an orchestrator, on-demand scaling handled at the infrastructure level rather than inside the JVM) solve the same underlying problem in ways that don't require it. Removing it outright (rather than leaving it deprecated indefinitely) let the JDK team simplify RMI's remaining implementation and stop carrying essentially-dead code. If you maintain code from the RMI-Activation era, this JEP means you must migrate off it entirely before upgrading past Java 16 — there is no compatibility flag or opt-in to restore it.

## 3. Core concept

```java
// Java 16 and earlier — compiles and runs (RMI Activation still present):
import java.rmi.activation.Activatable;
import java.rmi.activation.ActivationID;

// Java 17 and later — this import simply fails to compile:
// error: package java.rmi.activation does not exist
```

There is no flag, module option, or compatibility switch to restore the removed package — code depending on it must be rewritten to use ordinary RMI (a continuously running remote object) or another remoting mechanism entirely.

## 4. Diagram

<svg viewBox="0 0 640 200" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="RMI Activation let a remote object be started on demand by a separate rmid daemon; Java 17 removes this mechanism entirely, leaving ordinary always-running RMI remote objects as the supported approach">
  <rect x="20" y="20" width="280" height="160" rx="8" fill="#1c2430" stroke="#8b949e"/>
  <text x="160" y="42" fill="#8b949e" font-size="12" text-anchor="middle" font-family="sans-serif">RMI Activation (through Java 16)</text>
  <text x="160" y="70" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">client calls remote method</text>
  <text x="160" y="95" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">↓ rmid daemon activates object on demand</text>
  <text x="160" y="120" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">object starts, handles the call</text>
  <text x="160" y="150" fill="#f0883e" font-size="9" text-anchor="middle" font-family="sans-serif">removed entirely in Java 17</text>

  <rect x="340" y="20" width="280" height="160" rx="8" fill="#1c2430" stroke="#6db33f"/>
  <text x="480" y="42" fill="#6db33f" font-size="12" text-anchor="middle" font-family="sans-serif">Java 17+</text>
  <text x="480" y="70" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">client calls remote method</text>
  <text x="480" y="95" fill="#3fb950" font-size="10" text-anchor="middle" font-family="sans-serif">object must already be running</text>
  <text x="480" y="120" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">(managed by ordinary RMI, or an</text>
  <text x="480" y="140" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">external process/orchestrator)</text>
</svg>

On-demand activation via a separate daemon process is gone; remote objects must now be started and kept running by ordinary means.

## 5. Runnable example

Scenario: since RMI Activation itself no longer compiles on Java 17, the most faithful runnable example is a small "migration" — showing what a service using the old on-demand-activation model conceptually looked like, then the plain, always-running RMI equivalent that replaces it on Java 17+, then a small "readiness gate" pattern that reproduces the *useful part* of activation (not starting expensive resources until first actually needed) entirely within a single, always-running RMI object, using lazy initialization instead of a separate daemon process.

### Level 1 — Basic

```java
// File: PlainRemoteServer.java
// Ordinary RMI (no activation) — this is the Java 17+ supported approach.
import java.rmi.Remote;
import java.rmi.RemoteException;
import java.rmi.registry.LocateRegistry;
import java.rmi.registry.Registry;
import java.rmi.server.UnicastRemoteObject;

public class PlainRemoteServer {
    interface Greeter extends Remote {
        String greet(String name) throws RemoteException;
    }

    static class GreeterImpl extends UnicastRemoteObject implements Greeter {
        GreeterImpl() throws RemoteException { super(); }
        public String greet(String name) { return "Hello, " + name + "!"; }
    }

    public static void main(String[] args) throws Exception {
        Registry registry = LocateRegistry.createRegistry(1099);
        Greeter greeter = new GreeterImpl();
        registry.rebind("Greeter", greeter);

        // In the same process, act as a client too, for a self-contained runnable demo.
        Greeter stub = (Greeter) registry.lookup("Greeter");
        System.out.println(stub.greet("World"));

        java.rmi.server.UnicastRemoteObject.unexportObject(greeter, true);
    }
}
```

**How to run:**
```
java PlainRemoteServer.java
```

Expected output:
```
Hello, World!
```

### Level 2 — Intermediate

```java
// File: LazyInitRemoteServer.java
// Reproduces activation's *lazy-start* benefit inside one always-running object.
import java.rmi.Remote;
import java.rmi.RemoteException;
import java.rmi.registry.LocateRegistry;
import java.rmi.registry.Registry;
import java.rmi.server.UnicastRemoteObject;
import java.util.concurrent.atomic.AtomicBoolean;

public class LazyInitRemoteServer {
    interface ReportService extends Remote {
        String generateReport() throws RemoteException;
    }

    static class ReportServiceImpl extends UnicastRemoteObject implements ReportService {
        private final AtomicBoolean expensiveResourceLoaded = new AtomicBoolean(false);

        ReportServiceImpl() throws RemoteException { super(); }

        private synchronized void ensureExpensiveResourceLoaded() {
            if (expensiveResourceLoaded.compareAndSet(false, true)) {
                System.out.println("(first call: loading expensive report resources now...)");
            }
        }

        public String generateReport() {
            ensureExpensiveResourceLoaded();
            return "Report generated at " + System.currentTimeMillis();
        }
    }

    public static void main(String[] args) throws Exception {
        Registry registry = LocateRegistry.createRegistry(1099);
        ReportService service = new ReportServiceImpl();
        registry.rebind("ReportService", service);

        ReportService stub = (ReportService) registry.lookup("ReportService");
        System.out.println("Calling generateReport() first time:");
        System.out.println(stub.generateReport());
        System.out.println("Calling generateReport() second time:");
        System.out.println(stub.generateReport());

        UnicastRemoteObject.unexportObject(service, true);
    }
}
```

**How to run:**
```
java LazyInitRemoteServer.java
```

Expected output shape (timestamps vary by run):
```
Calling generateReport() first time:
(first call: loading expensive report resources now...)
Report generated at 1732000000123
Calling generateReport() second time:
Report generated at 1732000000456
```

### Level 3 — Advanced

```java
// File: MultiServiceRegistry.java
// A single always-running process hosting several remote services, each lazily
// initializing its own expensive state independently — the practical replacement
// for what several separately-activatable objects under rmid used to provide.
import java.rmi.Remote;
import java.rmi.RemoteException;
import java.rmi.registry.LocateRegistry;
import java.rmi.registry.Registry;
import java.rmi.server.UnicastRemoteObject;
import java.util.concurrent.ConcurrentHashMap;
import java.util.concurrent.atomic.AtomicInteger;

public class MultiServiceRegistry {
    interface Service extends Remote {
        String handle(String request) throws RemoteException;
    }

    static class LazyService extends UnicastRemoteObject implements Service {
        private final String name;
        private final AtomicInteger callCount = new AtomicInteger(0);
        private volatile boolean initialized = false;

        LazyService(String name) throws RemoteException { super(); this.name = name; }

        private synchronized void initIfNeeded() {
            if (!initialized) {
                System.out.println("[" + name + "] initializing on first use");
                initialized = true;
            }
        }

        public String handle(String request) {
            initIfNeeded();
            int count = callCount.incrementAndGet();
            return "[" + name + "] handled '" + request + "' (call #" + count + ")";
        }
    }

    public static void main(String[] args) throws Exception {
        Registry registry = LocateRegistry.createRegistry(1099);

        String[] serviceNames = { "Billing", "Inventory", "Notifications" };
        for (String name : serviceNames) {
            registry.rebind(name, new LazyService(name));
        }

        for (String name : serviceNames) {
            Service stub = (Service) registry.lookup(name);
            System.out.println(stub.handle("request-1"));
            System.out.println(stub.handle("request-2"));
        }
    }
}
```

**How to run:**
```
java MultiServiceRegistry.java
```

Expected output:
```
[Billing] initializing on first use
[Billing] handled 'request-1' (call #1)
[Billing] handled 'request-2' (call #2)
[Inventory] initializing on first use
[Inventory] handled 'request-1' (call #1)
[Inventory] handled 'request-2' (call #2)
[Notifications] initializing on first use
[Notifications] handled 'request-1' (call #1)
[Notifications] handled 'request-2' (call #2)
```

## 6. Walkthrough

1. `MultiServiceRegistry.main` creates one RMI registry on port `1099` and binds three independent `LazyService` instances into it under different names — all three objects exist and are exported (network-reachable) from the moment they're created, since RMI Activation's "don't even start the object until needed" behavior is no longer available on Java 17+.
2. For each service name, the client-side code (running in the same process here, for a self-contained demo) looks up the remote stub via `registry.lookup(name)` and calls `handle(...)` twice.
3. Inside `handle`, `initIfNeeded()` is called on every invocation, but its body only actually does work the **first** time (guarded by the `initialized` flag) — this is where the *useful* part of activation's design (avoid paying an expensive initialization cost until genuinely needed) is reproduced, just implemented as ordinary lazy initialization inside an object that's already running, rather than as a separate daemon process deciding whether to start the object's containing JVM at all.
4. The distinction matters: RMI Activation could avoid even **starting the JVM process** hosting a remote object until first use; this replacement pattern still requires the process (and the object within it) to already be running and registered — it only defers the *expensive internal setup work*, not the process startup itself. For genuinely avoiding whole-process startup until needed, modern deployments reach for infrastructure-level solutions (an orchestrator scaling a service from zero, or a serverless/function-as-a-service platform), which didn't exist as mainstream options when RMI Activation was originally designed.
5. Each call to `handle` also increments and reports a per-service call counter, showing that after the lazy first-call initialization, subsequent calls proceed normally and repeatedly — exactly the steady-state behavior a remote service should have, whether or not it started via activation historically.

```
registry.bind(name, service)              <- object created & exported immediately (no on-demand start)
        │
client.lookup(name).handle(request)
        │
  first call:  initIfNeeded() does real work, then handles request
  later calls: initIfNeeded() is a no-op, handles request directly
```

## 7. Gotchas & takeaways

> `java.rmi.activation.*` and the `rmid` daemon are **completely absent** from Java 17 and later — this is not a deprecation warning to route around, it is a compile-time and runtime absence. Any code still importing `java.rmi.activation.Activatable` or similar simply will not compile on Java 17+, with no system property or module flag able to restore it.
- This JEP had a full release's advance notice: Java 15 (JEP 385) had already marked RMI Activation deprecated for removal one release before Java 17 actually removed it — the standard two-step "deprecate, then remove" pattern the JDK follows for anything but the most urgent removals.
- If you inherit legacy code using RMI Activation, the practical migration path is almost always toward *ordinary* RMI (a continuously running `UnicastRemoteObject`, as shown here) combined with lazy internal initialization for anything genuinely expensive to set up — or, for cases that truly need "start a whole process on demand," delegating that responsibility to modern infrastructure (a container orchestrator, a process supervisor) rather than to the JVM itself.
- Ordinary RMI (not using activation) is entirely unaffected by this JEP — `UnicastRemoteObject`, `Registry`, and remote interfaces continue to work exactly as before; only the separate activation subsystem and its daemon process are gone.
- This removal reflects a broader pattern across several Java 17 changes ([Remove Applet API](0716-remove-applet-api-deprecated.md), [Remove experimental AOT/JIT (Graal) compiler](0714-remove-experimental-aot-jit-graal-compiler.md)) of the JDK actively shedding long-unused or superseded mechanisms rather than carrying them indefinitely — a maintenance philosophy that keeps the platform's core smaller and easier to evolve.
- Before upgrading any legacy RMI-based system past Java 16, grep the codebase (and its dependencies) for `java.rmi.activation` imports specifically — this is exactly the kind of removal that fails loudly and immediately at compile time rather than causing a subtle runtime surprise, which is preferable but still worth checking for proactively.

---
card: java
gi: 987
slug: instrumentation-api-java-agents
title: Instrumentation API & java agents
---

## 1. What it is

A Java agent is a specially-packaged JAR file containing a class with a `premain` (or `agentmain`) method, loaded by the JVM *before* (or, for `agentmain`, after attaching to an already-running JVM) the application's own `main` method runs, given access to `java.lang.instrument.Instrumentation` — an API that lets the agent register a `ClassFileTransformer`, which is invoked for every single class the JVM loads, given that class's raw bytecode, and allowed to modify it before the JVM actually defines and uses the class. This is a fundamentally more powerful and lower-level mechanism than the [dynamic proxies](0985-dynamic-proxies-java-lang-reflect-proxy.md) or reflection-based approaches covered elsewhere: rather than generating a *new* proxy class implementing an interface, bytecode instrumentation modifies the actual bytecode of *existing* classes as they load, letting an agent inject monitoring, logging, or other behavior directly into methods that were never designed with any such hook in mind.

## 2. Why & when

Java agents are the mechanism behind profilers (async-profiler, JProfiler), Application Performance Monitoring tools (New Relic, Datadog's Java agent, and similar), and code-coverage tools (JaCoCo) — all of which need to observe or modify behavior across an entire application's classes without that application's own source code needing any special hooks, annotations, or awareness that instrumentation is even happening. The `-javaagent:agent.jar` command-line flag attaches an agent at JVM startup (via `premain`), while the `Attach API` allows attaching an agent to an *already-running* JVM (via `agentmain`), which is exactly how tools like VisualVM or a debugger can instrument a live process without having anticipated that need when the process was originally launched. This is genuinely low-level, powerful machinery — modifying bytecode directly requires working with a bytecode manipulation library (ASM, ByteBuddy) in any realistic agent, since hand-writing raw bytecode transformations is impractical — and it's specifically the right tool when you need to observe or modify behavior in code you cannot change (a third-party library, or an application you're monitoring but don't want to modify the source of), which is precisely the situation profiling and APM tools are built around.

## 3. Core concept

```java
// The agent's entry point -- called by the JVM BEFORE the application's own main() runs.
public class MonitoringAgent {
    public static void premain(String agentArgs, Instrumentation inst) {
        inst.addTransformer(new ClassFileTransformer() {
            public byte[] transform(ClassLoader loader, String className, Class<?> classBeingRedefined,
                                     ProtectionDomain domain, byte[] classfileBuffer) {
                if (className.equals("com/example/TargetClass")) {
                    System.out.println("agent observed class loading: " + className);
                    // a real agent would use ASM/ByteBuddy here to actually MODIFY classfileBuffer,
                    // e.g. injecting timing/logging code into specific methods
                }
                return classfileBuffer; // return unmodified bytes if no transformation is needed
            }
        });
    }
}
```

```
META-INF/MANIFEST.MF (inside the agent's JAR):
Premain-Class: MonitoringAgent
```

The manifest's `Premain-Class` entry is what tells the JVM which class's `premain` method to invoke when this JAR is loaded as an agent via `-javaagent`; every class the JVM subsequently loads passes through every registered `ClassFileTransformer`, giving the agent visibility into the entire application's class-loading activity.

## 4. Diagram

<svg viewBox="0 0 640 170" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="The JVM starting up, invoking the agent's premain before the application's main, then routing every subsequently loaded class's bytecode through the agent's registered transformer" >
  <rect x="20" y="30" width="140" height="40" fill="#1c2430" stroke="#6db33f"/>
  <text x="90" y="55" fill="#6db33f" font-size="10" text-anchor="middle" font-family="sans-serif">JVM starts</text>

  <rect x="220" y="30" width="140" height="40" fill="#1c2430" stroke="#f0883e"/>
  <text x="290" y="55" fill="#f0883e" font-size="10" text-anchor="middle" font-family="sans-serif">agent.premain()</text>

  <rect x="420" y="30" width="140" height="40" fill="#1c2430" stroke="#79c0ff"/>
  <text x="490" y="55" fill="#79c0ff" font-size="10" text-anchor="middle" font-family="sans-serif">app's main() runs</text>

  <line x1="160" y1="50" x2="220" y2="50" stroke="#8b949e" marker-end="url(#a)"/>
  <line x1="360" y1="50" x2="420" y2="50" stroke="#8b949e" marker-end="url(#a)"/>

  <rect x="220" y="100" width="340" height="50" fill="#1c2430" stroke="#e6edf3"/>
  <text x="390" y="120" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">EVERY class loaded from here on passes through</text>
  <text x="390" y="135" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">the agent's registered ClassFileTransformer first</text>

  <line x1="290" y1="70" x2="290" y2="100" stroke="#8b949e" stroke-dasharray="3"/>
  <line x1="490" y1="70" x2="490" y2="100" stroke="#8b949e" stroke-dasharray="3"/>
</svg>

*The agent's premain registers a transformer before the application starts; every subsequently loaded class's bytecode passes through it first.*

## 5. Runnable example

Scenario: build and attach a small Java agent that observes class loading, evolving from a basic agent that just logs which classes load, to a realistic agent that measures how many classes a specific package loads, to a more advanced case demonstrating attaching an agent to an already-running JVM via the Attach API rather than at startup.

### Level 1 — Basic

```java
// File: LoggingAgent.java
import java.lang.instrument.*;
import java.security.ProtectionDomain;

public class LoggingAgent {
    public static void premain(String agentArgs, Instrumentation inst) {
        System.out.println("agent attached via premain");
        inst.addTransformer(new ClassFileTransformer() {
            public byte[] transform(ClassLoader loader, String className, Class<?> classBeingRedefined,
                                     ProtectionDomain domain, byte[] classfileBuffer) {
                System.out.println("loading class: " + className);
                return classfileBuffer; // unmodified -- observation only
            }
        });
    }
}
```

```java
// File: TargetApp.java
public class TargetApp {
    public static void main(String[] args) {
        System.out.println("application running");
        new java.util.ArrayList<String>().add("triggers loading java/util/ArrayList");
    }
}
```

**How to run:**
```
javac LoggingAgent.java TargetApp.java
echo "Premain-Class: LoggingAgent" > manifest.txt
jar cfm agent.jar manifest.txt LoggingAgent.class
java -javaagent:agent.jar TargetApp
```
(JDK 17+.)

Expected output shape (many more `loading class:` lines for JDK internal classes will also appear; this is a representative excerpt):
```
agent attached via premain
loading class: java/util/ArrayList
application running
```

`premain` runs and prints its own message *before* `TargetApp.main`'s "application running" line ever executes — confirming the agent genuinely attaches and registers its transformer prior to the application starting, and every subsequently loaded class (including ordinary JDK classes like `ArrayList`, the moment they're first used) passes through the transformer's `transform` method, which here simply logs and returns the bytecode unchanged.

### Level 2 — Intermediate

```java
// File: CountingAgent.java
import java.lang.instrument.*;
import java.security.ProtectionDomain;
import java.util.concurrent.atomic.AtomicInteger;

public class CountingAgent {
    static final AtomicInteger javaUtilClassCount = new AtomicInteger(0);

    public static void premain(String agentArgs, Instrumentation inst) {
        inst.addTransformer(new ClassFileTransformer() {
            public byte[] transform(ClassLoader loader, String className, Class<?> classBeingRedefined,
                                     ProtectionDomain domain, byte[] classfileBuffer) {
                if (className != null && className.startsWith("java/util/")) {
                    int count = javaUtilClassCount.incrementAndGet();
                    System.out.println("java.util class #" + count + " loaded: " + className);
                }
                return classfileBuffer;
            }
        });

        // Register a shutdown hook to print a final summary when the JVM exits.
        Runtime.getRuntime().addShutdownHook(new Thread(() ->
            System.out.println("total java.util classes loaded: " + javaUtilClassCount.get())));
    }
}
```

```java
// File: TargetApp2.java
import java.util.*;

public class TargetApp2 {
    public static void main(String[] args) {
        List<String> list = new ArrayList<>();
        Map<String, Integer> map = new HashMap<>();
        Set<String> set = new HashSet<>();
        list.add("a"); map.put("b", 1); set.add("c");
        System.out.println("application finished using several java.util classes");
    }
}
```

**How to run:**
```
javac CountingAgent.java TargetApp2.java
echo "Premain-Class: CountingAgent" > manifest.txt
jar cfm agent2.jar manifest.txt CountingAgent.class
java -javaagent:agent2.jar TargetApp2
```

Expected output shape (illustrative — exact count and order depend on JVM internals and which `java.util` classes actually get loaded):
```
java.util class #1 loaded: java/util/ArrayList
java.util class #2 loaded: java/util/HashMap
java.util class #3 loaded: java/util/HashSet
application finished using several java.util classes
total java.util classes loaded: 3
```

The real-world concern added: the agent now filters specifically for `java.util` classes and maintains a running count across the *entire* application's lifetime, printing a final summary via a JVM shutdown hook — this is exactly the kind of lightweight, application-wide observability real profiling and monitoring agents provide, aggregating information across every class load event throughout a program's run rather than reacting to just one specific class.

### Level 3 — Advanced

```java
// File: AttachDemoAgent.java
import java.lang.instrument.*;
import java.security.ProtectionDomain;

public class AttachDemoAgent {
    // agentmain (not premain) is the entry point used when ATTACHING to an
    // already-running JVM, rather than being specified at JVM startup.
    public static void agentmain(String agentArgs, Instrumentation inst) {
        System.out.println("agent attached LIVE to an already-running JVM");
        inst.addTransformer(new ClassFileTransformer() {
            public byte[] transform(ClassLoader loader, String className, Class<?> classBeingRedefined,
                                     ProtectionDomain domain, byte[] classfileBuffer) {
                if (className != null && className.contains("Target")) {
                    System.out.println("post-attach: observed class " + className);
                }
                return classfileBuffer;
            }
        });
    }
}
```

```java
// File: LongRunningTarget.java
public class LongRunningTarget {
    public static void main(String[] args) throws InterruptedException {
        System.out.println("PID: " + ProcessHandle.current().pid());
        while (true) {
            Thread.sleep(1000);
        }
    }
}
```

```java
// File: AttachController.java
import com.sun.tools.attach.*;

public class AttachController {
    public static void main(String[] args) throws Exception {
        String targetPid = args[0];
        String agentJarPath = args[1];

        VirtualMachine vm = VirtualMachine.attach(targetPid);
        vm.loadAgent(agentJarPath); // triggers the TARGET JVM's agentmain, live, right now
        vm.detach();
        System.out.println("agent successfully attached to PID " + targetPid);
    }
}
```

**How to run:**
```
javac AttachDemoAgent.java LongRunningTarget.java
echo "Agent-Class: AttachDemoAgent" > manifest.txt
jar cfm attach-agent.jar manifest.txt AttachDemoAgent.class

# In one terminal, start a long-running target process and note the printed PID:
java LongRunningTarget

# In a second terminal, compile and run the attach controller against that PID:
javac --add-exports jdk.attach/com.sun.tools.attach=ALL-UNNAMED AttachController.java
java --add-exports jdk.attach/com.sun.tools.attach=ALL-UNNAMED AttachController <PID> attach-agent.jar
```
(JDK 17+; the Attach API lives in the `jdk.attach` module and requires `--add-exports` to access from ordinary application code.)

Expected output (in the terminal running `AttachController`):
```
agent successfully attached to PID 48213
```
And, in the target process's own output stream, the agent's `agentmain` message appears live, well after that process had already been running.

The production-flavored hard case: `VirtualMachine.attach(targetPid)` connects to an *already-running*, unrelated JVM process purely by its process ID, and `vm.loadAgent(agentJarPath)` triggers that target's `agentmain` method live, at that exact moment — this is precisely how tools like VisualVM, JProfiler, or a debugger can begin instrumenting a process that was started long before, with no `-javaagent` flag ever specified at that process's original launch, entirely different from the `premain`-based approach where instrumentation must be planned for in advance, at startup.

## 6. Walkthrough

Tracing the sequence of events when `java -javaagent:agent2.jar TargetApp2` is launched, in `CountingAgent`'s Level 2 example:

1. The JVM starts up and, before invoking `TargetApp2.main`, reads `agent2.jar`'s manifest, finds `Premain-Class: CountingAgent`, and calls `CountingAgent.premain(agentArgs, inst)` — at this point, `TargetApp2`'s own code has not yet begun executing at all.
2. Inside `premain`, `inst.addTransformer(...)` registers the anonymous `ClassFileTransformer` with the JVM's instrumentation machinery, and a shutdown hook is separately registered to print a final summary whenever the JVM eventually exits.
3. `premain` returns, and the JVM now proceeds to actually start the application, invoking `TargetApp2.main` — as this method executes `new ArrayList<>()` for the first time, the JVM must load the `java.util.ArrayList` class (if it hasn't already been loaded for some other reason), and as part of that loading process, every registered `ClassFileTransformer`'s `transform` method is invoked, being passed `ArrayList`'s raw bytecode.
4. The transformer checks whether `className` starts with `"java/util/"` — since `"java/util/ArrayList"` does, it increments the shared `javaUtilClassCount` and prints a message noting this specific class load, then returns `classfileBuffer` completely unchanged (this particular agent only observes; it doesn't modify anything).
5. This same process repeats independently as `TargetApp2.main` continues, instantiating `HashMap` and `HashSet` in turn — each triggers its own class-loading event, each passing through the identical transformer, each incrementing the shared counter and printing its own message.
6. After `TargetApp2.main` completes and prints its own final message, the JVM begins its normal shutdown sequence — this is when the previously-registered shutdown hook runs, printing the final accumulated count (`3`, reflecting `ArrayList`, `HashMap`, and `HashSet` all having been loaded and observed) — demonstrating that the agent's instrumentation persisted and accumulated state across the *entire* lifetime of the application, from before its `main` method even started to the moment the JVM itself terminated.

## 7. Gotchas & takeaways

> **Gotcha:** a `ClassFileTransformer` that actually *modifies* bytecode (rather than just observing it, as in these examples) must return syntactically and verifiably valid bytecode, or the JVM's bytecode verifier will reject the modified class outright, typically manifesting as a confusing `VerifyError` at class-loading time — real-world agents virtually always use a dedicated bytecode manipulation library (ASM, ByteBuddy) rather than hand-constructing modified bytecode directly, precisely because correctly producing verifiable bytecode by hand is extremely error-prone.

- A Java agent is a JAR with a manifest-declared `Premain-Class` (or `Agent-Class` for attach-based loading), containing a `premain` (or `agentmain`) method invoked by the JVM before (or during, for live attach) an application runs, given access to the `Instrumentation` API.
- A registered `ClassFileTransformer` is invoked for every class the JVM loads from that point forward, receiving that class's raw bytecode and able to modify it before the JVM actually defines and uses the class.
- This mechanism underlies profilers, Application Performance Monitoring tools, and code-coverage tools, letting them observe or modify behavior across an entire application without that application's own source code needing any awareness of instrumentation.
- `-javaagent:agent.jar` attaches an agent at JVM startup via `premain`; the Attach API (`VirtualMachine.attach`, `loadAgent`) allows attaching to an already-running JVM live, via `agentmain`, with no advance planning needed at that process's original launch.
- Real bytecode modification (as opposed to mere observation) virtually always requires a dedicated bytecode manipulation library, since hand-constructing verifiably correct bytecode directly is impractical and error-prone.
- See [dynamic proxies (java.lang.reflect.Proxy)](0985-dynamic-proxies-java-lang-reflect-proxy.md) for a higher-level, less invasive alternative for adding behavior around interface method calls specifically, without needing bytecode-level instrumentation at all.

# JVM Internals

## Overview

The JVM (Java Virtual Machine) executes Java bytecode on any platform. Understanding JVM internals helps write faster, memory-efficient code and diagnose performance issues. Key areas: class loading, runtime data areas, garbage collection, JIT compilation.

---

## 1. JVM Architecture

### Visual Diagram

```
Java Source (.java)
    │  javac
    ▼
Java Bytecode (.class)
    │
    ▼
JVM
┌─────────────────────────────────────────────────┐
│                                                 │
│  Class Loader Subsystem                         │
│  ┌───────────────────────────────────────┐      │
│  │ Bootstrap → Extension → Application  │      │
│  └───────────────────────────────────────┘      │
│                    │                            │
│                    ▼                            │
│  Runtime Data Areas                             │
│  ┌──────────┐  ┌──────────┐  ┌──────────────┐  │
│  │  Heap    │  │  Stack   │  │ Method Area  │  │
│  │(objects) │  │(frames)  │  │(class meta)  │  │
│  └──────────┘  └──────────┘  └──────────────┘  │
│  ┌──────────┐  ┌──────────┐                     │
│  │  PC Reg  │  │ Native   │                     │
│  │ (per thr)│  │  Stack   │                     │
│  └──────────┘  └──────────┘                     │
│                    │                            │
│  Execution Engine                               │
│  ┌─────────────────────────────────────────┐    │
│  │ Interpreter → JIT Compiler → GC         │    │
│  └─────────────────────────────────────────┘    │
└─────────────────────────────────────────────────┘
```

---

## 2. Runtime Data Areas

### Visual Diagram

```
Per-JVM (shared by all threads):
  Heap:
    Young Gen:  Eden + Survivor S0 + Survivor S1   ← new objects
    Old Gen:    Tenured                             ← long-lived objects
    [Metaspace: class metadata, off-heap, Java 8+]

  Method Area (Metaspace in Java 8+):
    Class metadata, field/method descriptors, bytecode
    String pool (interned strings)
    Static variables

Per-Thread:
  JVM Stack:
    Frame per method call: local variables + operand stack + constant pool ref
    Stack frame created on method call, destroyed on return
    StackOverflowError if too deep (infinite recursion)

  PC (Program Counter) Register:
    Current instruction address in bytecode
    undefined for native methods

  Native Stack:
    For JNI (Java Native Interface) calls
```

### Example 1 — Stack vs Heap

```java
public class StackVsHeap {
    // int x = 5 — primitive: VALUE stored on stack
    // String s = "hi" — reference on stack, object in heap (String pool)
    // Person p = new Person() — reference on stack, object in heap

    static class Person {
        String name; // reference in heap, String object in String pool
        int age;     // primitive value in heap (part of Person object)
        Person(String name, int age) { this.name = name; this.age = age; }
    }

    public static void main(String[] args) {
        int x = 5;               // Stack: x=5
        Person p = new Person("Alice", 30); // Stack: p=<ref>, Heap: Person object

        // After method returns:
        // x popped from stack
        // p popped from stack
        // Person object in heap eligible for GC (no more references)
    }
}
```

---

## 3. Class Loading

### Visual Diagram — ClassLoader Hierarchy

```
Bootstrap ClassLoader (C++)
  └── loads: java.lang.*, java.util.*, rt.jar / java.base module
  └── parent: null (root)

Platform ClassLoader (Java 9+) / Extension ClassLoader (Java 8-)
  └── loads: JDK extension modules
  └── parent: Bootstrap

Application (System) ClassLoader
  └── loads: classpath / module-path classes
  └── parent: Platform

Custom ClassLoaders:
  └── hot-deploy, plugin systems, OSGi
  └── parent: Application (by default)

Delegation model (parent-first):
  1. Check if already loaded
  2. Ask parent to load
  3. If parent fails, load self
  This prevents loading java.lang.String from classpath (Bootstrap handles it)
```

### Example 1 — ClassLoader Inspection

```java
public class ClassLoaderDemo {
    public static void main(String[] args) {
        // Application classloader
        ClassLoader appCL = ClassLoaderDemo.class.getClassLoader();
        System.out.println("App CL: " + appCL);
        // jdk.internal.loader.ClassLoaders$AppClassLoader@...

        // Platform classloader
        System.out.println("Parent: " + appCL.getParent());
        // jdk.internal.loader.ClassLoaders$PlatformClassLoader@...

        // Bootstrap (null for native bootstrap)
        System.out.println("Grandparent: " + appCL.getParent().getParent());
        // null (bootstrap = C++ code)

        // String loaded by bootstrap
        System.out.println("String CL: " + String.class.getClassLoader());
        // null (bootstrap)

        // Dynamic class loading
        try {
            Class<?> cls = Class.forName("java.util.ArrayList"); // explicit load
            System.out.println("Loaded: " + cls.getName());
        } catch (ClassNotFoundException e) {
            e.printStackTrace();
        }
    }
}
```

**What this does:** `null` classloader means bootstrap (C++ native). The hierarchy prevents class conflicts — `java.lang.String` always comes from bootstrap, never from a custom classloader.

### Class Loading Phases

```
Loading:    Find binary representation (.class file) and load into memory
Linking:
  Verify:   Check bytecode is structurally correct (VerifyError if fails)
  Prepare:  Allocate static fields, set to JVM defaults (0, null, false)
  Resolve:  Symbolic references → concrete memory references (lazy by default)
Initialization: Run static initializers, set static final fields
```

---

## 4. Garbage Collection

### Visual Diagram — Generational GC

```
Heap layout (HotSpot):
  ┌──────────────────────────────────────────────────────┐
  │                    Young Generation                  │
  │  ┌─────────────────────────┐ ┌───────┐  ┌───────┐   │
  │  │          Eden           │ │  S0   │  │  S1   │   │
  │  │  (new objects here)     │ │(from) │  │  (to) │   │
  │  └─────────────────────────┘ └───────┘  └───────┘   │
  ├──────────────────────────────────────────────────────┤
  │                    Old Generation                    │
  │  ┌──────────────────────────────────────────────┐    │
  │  │              Tenured Space                   │    │
  │  │  (survived many minor GCs — long-lived objs) │    │
  │  └──────────────────────────────────────────────┘    │
  └──────────────────────────────────────────────────────┘

Minor GC (Young Gen collection):
  1. Eden fills up → trigger Minor GC
  2. Live objects in Eden + S0 → copy to S1, increment age
  3. Objects with age > threshold → promote to Old Gen
  4. Eden + S0 cleared (all dead objects collected at once)

Major/Full GC (Old Gen):
  Old Gen fills → Major GC (slower, may Stop-The-World)
```

### Example 1 — GC Logging and Tuning Flags

```bash
# Enable GC logging (Java 9+)
java -Xlog:gc*:file=gc.log:time,uptime:filecount=5,filesize=20m MyApp

# Heap size
java -Xms256m -Xmx2g MyApp     # initial=256MB, max=2GB

# GC algorithm selection
java -XX:+UseG1GC MyApp         # G1 (default since Java 9)
java -XX:+UseZGC MyApp          # ZGC (low-latency, Java 15+ production)
java -XX:+UseShenandoahGC MyApp # Shenandoah (RedHat, concurrent)
java -XX:+UseSerialGC MyApp     # Serial (single-threaded, small apps)
java -XX:+UseParallelGC MyApp   # Parallel (throughput-focused)

# GC tuning
java -XX:NewRatio=2 MyApp       # Old:Young ratio = 2:1
java -XX:SurvivorRatio=8 MyApp  # Eden:Survivor = 8:1
java -XX:MaxGCPauseMillis=200   # Target pause time (G1 hint)
```

### Example 2 — GC-Friendly Code

```java
import java.util.*;

public class GCFriendly {
    // BAD: creates many short-lived String objects
    static String badConcat(List<String> items) {
        String result = "";
        for (String item : items) {
            result += item + ", "; // new String object per iteration
        }
        return result;
    }

    // GOOD: StringBuilder reuses buffer
    static String goodConcat(List<String> items) {
        StringBuilder sb = new StringBuilder();
        for (String item : items) {
            sb.append(item).append(", ");
        }
        return sb.toString(); // one String at end
    }

    // BAD: unnecessary boxing in loop
    static long badSum(int[] nums) {
        Long sum = 0L; // autoboxing every += — creates Long objects!
        for (int n : nums) {
            sum += n; // unbox + add + box
        }
        return sum;
    }

    // GOOD: primitive
    static long goodSum(int[] nums) {
        long sum = 0L; // no boxing
        for (int n : nums) {
            sum += n;
        }
        return sum;
    }

    // Avoid finalizers — unpredictable, delay GC
    // Use try-with-resources instead
}
```

---

## 5. GC Algorithms

### Visual Diagram — GC Comparison

```
Algorithm     | Stop-World | Throughput | Latency | Default
--------------|------------|------------|---------|--------
Serial        | YES (full) | LOW        | HIGH    | tiny apps
Parallel      | YES (full) | HIGH       | HIGH    | Java 8 default
G1            | MOSTLY     | MEDIUM     | MEDIUM  | Java 9+ default
ZGC           | MINIMAL    | HIGH       | <1ms    | Java 15+ option
Shenandoah    | MINIMAL    | HIGH       | <10ms   | OpenJDK option

G1 (Garbage First):
  - Divides heap into equal regions (not fixed young/old split)
  - Concurrent marking, evacuates most profitable regions first
  - Predictable pause time goal
  - Good balance for most applications

ZGC (Z Garbage Collector) [Java 15+]:
  - Load barriers for concurrent relocation
  - Sub-millisecond pauses regardless of heap size
  - Use for latency-sensitive: trading systems, game servers
```

---

## 6. JIT Compilation

### Visual Diagram

```
Interpretation vs JIT:

  First execution:
    Bytecode → Interpreter (slow — ~10x slower than compiled)

  After N executions (threshold ~10,000):
    JIT compiles hot method to native code
    Stored in CodeCache
    Future calls: native code directly (fast)

  Tiered compilation (Java 7+):
    Tier 0: Interpreter
    Tier 1: C1 (quick compile, no opt)   ← first hot
    Tier 2: C1 with light profiling
    Tier 3: C1 with full profiling
    Tier 4: C2 (full optimize)           ← very hot

JIT optimizations:
  - Method inlining: replace call with method body
  - Dead code elimination: remove unreachable code
  - Escape analysis: object doesn't escape method → allocate on stack
  - Loop unrolling: unroll small loops
  - Vectorization: use SIMD instructions
```

### Example 1 — Escape Analysis (Heap Elision)

```java
public class EscapeAnalysis {
    static class Point {
        int x, y;
        Point(int x, int y) { this.x = x; this.y = y; }
    }

    // Point doesn't escape — JIT may allocate it on STACK (no GC pressure)
    static int distance(int x1, int y1, int x2, int y2) {
        Point p1 = new Point(x1, y1); // may NOT go to heap
        Point p2 = new Point(x2, y2); // may NOT go to heap
        int dx = p2.x - p1.x;
        int dy = p2.y - p1.y;
        return dx * dx + dy * dy; // p1, p2 don't escape this method
    }

    // This prevents escape analysis:
    static Point lastPoint; // static reference = escapes!
    static int distanceEscaping(int x1, int y1, int x2, int y2) {
        Point p1 = new Point(x1, y1); // escapes via lastPoint = p1
        lastPoint = p1;
        return x2 - x1;
    }

    public static void main(String[] args) {
        // Warm up JIT (10K+ calls)
        for (int i = 0; i < 100_000; i++) {
            distance(i, i, i+1, i+1);
        }
    }
}
```

**What this does:** If JIT determines an object doesn't escape the method's scope, it may allocate it on the thread stack — no heap allocation, no GC involvement. Returning the object or storing to a field makes it escape.

---

## 7. JVM Flags Reference

```bash
# Memory
-Xms<size>                initial heap size
-Xmx<size>                max heap size
-Xss<size>                thread stack size (default 512KB-1MB)
-XX:MetaspaceSize=<size>   initial metaspace
-XX:MaxMetaspaceSize=<size> max metaspace

# GC
-XX:+UseG1GC              G1 collector
-XX:+UseZGC               ZGC [Java 15+]
-XX:+UseShenandoahGC      Shenandoah
-XX:MaxGCPauseMillis=<ms>  target pause (G1 hint)
-XX:+PrintGCDetails        print GC details (Java 8)
-Xlog:gc*                  GC logging (Java 9+)

# JIT
-XX:+PrintCompilation       print JIT compilation decisions
-XX:+UnlockDiagnosticVMOptions -XX:+PrintInlining  inlining decisions
-XX:CompileThreshold=<n>    method call threshold before JIT (default ~10000)
-XX:-TieredCompilation      disable tiered (go straight to C2)

# Diagnostics
-XX:+HeapDumpOnOutOfMemoryError  dump on OOM
-XX:HeapDumpPath=/tmp/dump.hprof  dump location
-XX:+PrintFlagsFinal | grep GC   see all GC flags
```

---

## Quick Reference

```
Memory areas:
  Heap        shared, GC-managed, objects + arrays
  Stack       per-thread, frames, primitives, refs
  Metaspace   off-heap (Java 8+), class metadata
  Code cache  JIT-compiled native code

GC generations:
  Young (Eden + S0 + S1): new objects, Minor GC
  Old (Tenured):           long-lived, Major GC

ClassLoader hierarchy:
  Bootstrap → Platform → Application → Custom

Class loading phases:
  Load → Verify → Prepare → Resolve → Initialize

JIT tiers:
  Interpreter → C1 (quick) → C2 (optimized)

GC tuning rules:
  More heap = fewer GCs but longer pauses
  G1 for balanced; ZGC for latency-critical
  Avoid finalizers; use try-with-resources
  Minimize allocations in hot loops (reuse objects, primitives > boxed)
```

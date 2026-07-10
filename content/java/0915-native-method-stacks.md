---
card: java
gi: 915
slug: native-method-stacks
title: Native method stacks
---

## 1. What it is

A native method stack is a per-thread runtime data area, separate from the [JVM stack](0913-jvm-stacks-stack-frames.md), used when a thread executes **native** code — methods declared with the `native` keyword in Java, whose actual implementation lives outside the JVM entirely, typically written in C or C++ and invoked through JNI (the Java Native Interface). While the JVM stack tracks ordinary Java method calls using JVM-defined stack frames, a native method's call frame follows whatever convention the native code's own language and platform use (a C stack frame, for instance) — the JVM Specification deliberately leaves the exact implementation of native method stacks up to each JVM implementation, since it's inherently tied to how that JVM interoperates with the host platform's native calling conventions.

## 2. Why & when

You'll encounter native methods (and, indirectly, native method stacks) any time Java code calls into functionality the JDK itself implements natively for performance or platform-access reasons — many low-level I/O operations, certain `Object` methods like `hashCode()` (in some JVM implementations), and any custom JNI code a library or application defines to interface with existing C/C++ code, hardware access, or operating-system APIs unavailable through pure Java. Understanding this separate stack matters specifically when debugging issues that involve native code: a `StackOverflowError` can, in principle, originate from deep native recursion consuming the native stack rather than the ordinary JVM stack (though the exact behavior — a distinct error, or the same `StackOverflowError`, or even a native crash — is JVM- and platform-dependent, since this area is intentionally left to each implementation); and when reasoning about performance or resource usage of JNI-heavy code, since native stack frames follow the host platform's own conventions and constraints, which can differ meaningfully from the JVM's own bytecode-frame model.

## 3. Core concept

```java
public class NativeExample {
    // A native method: no Java method BODY at all -- the implementation lives in
    // a separately-compiled native library, loaded via System.loadLibrary(...).
    native int computeNatively(int input);

    static {
        System.loadLibrary("nativeimpl"); // loads the compiled C/C++ library providing computeNatively
    }
}
// When computeNatively() is called, execution transitions from the JVM stack into
// a NATIVE method stack -- a call frame following the host platform's native calling
// convention (e.g. the standard C calling convention), not the JVM's own frame format.
```

The `native` keyword and a matching `System.loadLibrary` call are what actually engage this whole mechanism — most ordinary Java application code never directly declares a `native` method, though it frequently calls JDK methods that are natively implemented under the hood.

## 4. Diagram

<svg viewBox="0 0 640 170" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="A thread executing ordinary Java code uses its JVM stack; when it calls into a native method via JNI, execution transitions to that thread's separate native method stack, following the host platform's own calling convention, then returns to the JVM stack when the native call completes">
  <rect x="20" y="40" width="230" height="90" rx="10" fill="#1c2430" stroke="#79c0ff" stroke-width="2"/>
  <text x="135" y="60" fill="#79c0ff" font-size="11" text-anchor="middle" font-family="sans-serif">JVM stack</text>
  <rect x="40" y="75" width="190" height="30" rx="6" fill="#1c2430" stroke="#8b949e"/>
  <text x="135" y="95" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">Java method frames</text>

  <rect x="390" y="40" width="230" height="90" rx="10" fill="#1c2430" stroke="#f0883e" stroke-width="2"/>
  <text x="505" y="60" fill="#f0883e" font-size="11" text-anchor="middle" font-family="sans-serif">Native method stack</text>
  <rect x="410" y="75" width="190" height="30" rx="6" fill="#1c2430" stroke="#8b949e"/>
  <text x="505" y="95" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">native (C/C++) call frames</text>

  <line x1="250" y1="85" x2="386" y2="85" stroke="#8b949e" stroke-width="2" marker-end="url(#a43)"/>
  <text x="320" y="75" fill="#8b949e" font-size="9" font-family="sans-serif">calls native method</text>
  <line x1="386" y1="105" x2="250" y2="105" stroke="#8b949e" stroke-width="2" marker-end="url(#a43)"/>
  <text x="320" y="120" fill="#8b949e" font-size="9" font-family="sans-serif">returns to Java</text>
  <defs><marker id="a43" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#8b949e"/></marker></defs>
</svg>

*A thread transitions between its JVM stack and its native method stack as execution crosses the Java/native boundary via JNI, then transitions back on return.*

## 5. Runnable example

Scenario: observing the Java/native boundary through JDK methods that are natively implemented under the hood, growing from identifying such a method, to writing and calling a minimal genuine JNI native method, to observing a stack trace that spans both Java and native frames.

### Level 1 — Basic

```java
public class IdentifyingNativeMethods {
    public static void main(String[] args) throws Exception {
        // Object.hashCode() is `native` in the OpenJDK reference implementation --
        // its actual computation happens in native code, not Java bytecode.
        java.lang.reflect.Method hashCodeMethod = Object.class.getMethod("hashCode");
        System.out.println("Object.hashCode() is native: " + java.lang.reflect.Modifier.isNative(hashCodeMethod.getModifiers()));

        // System.currentTimeMillis() is ALSO native -- it must ask the underlying OS for the time.
        java.lang.reflect.Method currentTimeMillis = System.class.getMethod("currentTimeMillis");
        System.out.println("System.currentTimeMillis() is native: " + java.lang.reflect.Modifier.isNative(currentTimeMillis.getModifiers()));

        Object obj = new Object();
        System.out.println("calling the native hashCode(): " + obj.hashCode());
        System.out.println("(this call transitioned from the JVM stack to a native method stack and back)");
    }
}
```

**How to run:** `java IdentifyingNativeMethods.java` (JDK 17+; exact set of natively-implemented methods can vary somewhat by JDK version/vendor, though `Object.hashCode()` and `System.currentTimeMillis()` are commonly native across mainstream implementations).

Expected output shape:
```
Object.hashCode() is native: true
System.currentTimeMillis() is native: true
calling the native hashCode(): 1554874502
(this call transitioned from the JVM stack to a native method stack and back)
```

Reflection's `Modifier.isNative()` directly confirms these familiar JDK methods are backed by native implementations — every call to them involves exactly the JVM-stack-to-native-stack transition this tutorial describes, even though it's completely invisible from ordinary Java code.

### Level 2 — Intermediate

```c
// NativeAdder.c -- a minimal native implementation, compiled into a shared library
#include <jni.h>

JNIEXPORT jint JNICALL Java_NativeAdder_addNatively(JNIEnv *env, jobject obj, jint a, jint b) {
    return a + b; // this executes on the calling thread's NATIVE method stack
}
```

```java
public class NativeAdder {
    native int addNatively(int a, int b);

    static {
        System.loadLibrary("NativeAdder"); // loads the compiled shared library (.so/.dll/.dylib)
    }

    public static void main(String[] args) {
        NativeAdder adder = new NativeAdder();
        int result = adder.addNatively(3, 4); // JVM stack -> native method stack -> back to JVM stack
        System.out.println("3 + 4 via native method = " + result);
    }
}
```

**How to run:** compile the C file into a shared library matching your platform's naming convention (e.g., on Linux: `gcc -shared -fPIC -I"$JAVA_HOME/include" -I"$JAVA_HOME/include/linux" -o libNativeAdder.so NativeAdder.c`), compile the Java file (`javac NativeAdder.java`), then run with the library on the path: `java -Djava.library.path=. NativeAdder` (JDK 17+; exact compiler flags and library naming vary by OS).

Expected output:
```
3 + 4 via native method = 7
```

The real-world concern added: an actual, genuine native method — implemented in C, compiled into a platform-specific shared library, and invoked via JNI — demonstrating the full real mechanism: the call to `addNatively` transitions the calling thread from its JVM stack into its native method stack (where the C function's own stack frame, following the platform's native calling convention, executes), then transitions back to the JVM stack once the native function returns its result.

### Level 3 — Advanced

```c
// RecursiveNative.c
#include <jni.h>

JNIEXPORT jint JNICALL Java_RecursiveNative_nativeRecurse(JNIEnv *env, jobject obj, jint depth) {
    if (depth <= 0) return 0;
    // Calls BACK into Java from native code, which then may call native again --
    // demonstrating that execution can cross the Java/native boundary repeatedly,
    // interleaving JVM stack frames and native method stack frames for the SAME thread.
    jclass cls = (*env)->GetObjectClass(env, obj);
    jmethodID javaCallback = (*env)->GetMethodID(env, cls, "javaCallback", "(I)I");
    return 1 + (*env)->CallIntMethod(env, obj, javaCallback, depth - 1);
}
```

```java
public class RecursiveNative {
    native int nativeRecurse(int depth);

    int javaCallback(int depth) {
        return nativeRecurse(depth); // calls BACK into native -- interleaving continues
    }

    static {
        System.loadLibrary("RecursiveNative");
    }

    public static void main(String[] args) {
        RecursiveNative r = new RecursiveNative();
        int result = r.nativeRecurse(5);
        System.out.println("interleaved native<->Java recursion result: " + result + " (expected 5)");
        System.out.println("each level alternated between a NATIVE method stack frame and a JVM stack frame,");
        System.out.println("all on the SAME thread, which maintains BOTH kinds of stack simultaneously");
    }
}
```

**How to run:** compile the C file similarly to Level 2 (adjust include paths and library name accordingly), compile the Java file, then `java -Djava.library.path=. RecursiveNative` (JDK 17+; requires a working native toolchain and matching JNI headers for your platform).

Expected output:
```
interleaved native<->Java recursion result: 5 (expected 5)
each level alternated between a NATIVE method stack frame and a JVM stack frame,
all on the SAME thread, which maintains BOTH kinds of stack simultaneously
```

This adds the production-flavored hard case: recursion that **interleaves** native and Java calls — `nativeRecurse` (native) calls back into `javaCallback` (Java), which calls back into `nativeRecurse` (native) again, and so on — demonstrating that a single thread maintains both its JVM stack and its native method stack *simultaneously*, with execution crossing back and forth between the two as the call chain alternates between native and Java frames, rather than using one stack exclusively and switching to the other only once.

## 6. Walkthrough

Tracing `RecursiveNative.main`'s call to `r.nativeRecurse(5)`:

1. `main` (a Java method, JVM stack frame) calls `r.nativeRecurse(5)` — since `nativeRecurse` is declared `native`, this call transitions the current thread's execution from its JVM stack into its native method stack, where the compiled C function `Java_RecursiveNative_nativeRecurse` begins executing, using a native (C-convention) call frame.
2. Inside that native frame, since `depth` (5) is greater than 0, the C code uses JNI functions (`GetObjectClass`, `GetMethodID`, `CallIntMethod`) to look up and invoke `javaCallback(4)` — this call transitions execution *back* from the native method stack into the JVM stack, pushing a new ordinary Java stack frame for `javaCallback`.
3. `javaCallback(4)`, running as an ordinary Java method, calls `nativeRecurse(4)` — transitioning execution back into the native method stack yet again, pushing another native call frame.
4. This pattern repeats, alternating between native and Java frames, for `depth` values 5, 4, 3, 2, 1, until `nativeRecurse(0)` is reached, whose native code immediately returns `0` without any further recursive call (the base case).
5. As each level of this interleaved recursion returns, its result is added to (`1 + ...`) by whichever native frame is currently unwinding, propagating the accumulated count back up through the alternating chain of native and Java frames until the very first, outermost call to `nativeRecurse(5)` returns its final result, `5`, to `main`.
6. Throughout this entire process, only **one** thread is involved — but that single thread simultaneously maintains *both* a JVM stack (holding the `javaCallback` frames) and a native method stack (holding the `nativeRecurse` frames) at the same time, with execution crossing between the two stacks on every call and every return, exactly as the JVM Specification's model of per-thread execution state describes.

## 7. Gotchas & takeaways

> **Gotcha:** because native method stacks follow the host platform's own native calling convention and memory layout — entirely outside the JVM's own bytecode-verification and safety guarantees — a bug in native code (a buffer overflow, an invalid pointer dereference, stack corruption from deep unchecked native recursion) can crash the entire JVM process outright, rather than producing a catchable Java exception the way a bug in pure Java code (even a `StackOverflowError`) generally would.

- A native method stack is a separate, per-thread runtime data area used specifically when a thread executes native (JNI) code, following the host platform's own native calling convention rather than the JVM's own bytecode-frame format.
- The exact implementation details of native method stacks are left to each JVM implementation by the JVM Specification, since they're inherently tied to how that specific JVM interoperates with its host platform.
- Many familiar JDK methods (`Object.hashCode()`, `System.currentTimeMillis()`, and others, depending on JVM implementation) are natively implemented, meaning every call to them involves exactly this JVM-stack-to-native-stack transition, even though it's entirely invisible from ordinary application code.
- A single thread maintains both its JVM stack and its native method stack simultaneously, and execution crosses between the two every time control passes across the Java/native boundary in either direction, as demonstrated by the interleaved recursion example.
- Because native code operates outside the JVM's own safety guarantees, bugs there carry a different (and often more severe) risk profile than equivalent bugs in pure Java code — see [the program counter register](0914-program-counter-pc-register.md) tutorial's note that its value is explicitly undefined during native execution, another reflection of this same boundary.

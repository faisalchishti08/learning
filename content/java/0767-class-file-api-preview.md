---
card: java
gi: 767
slug: class-file-api-preview
title: Class-File API (preview)
---

## 1. What it is

**Java 22** (JEP 457) previews `java.lang.classfile`, a standard API for **parsing, generating, and transforming** `.class` files — the compiled bytecode format the JVM executes. Before this, any tool that needed to read or manipulate class files (bytecode analyzers, instrumentation agents, code-generation frameworks) depended on **third-party libraries** like ASM or BCEL, since the JDK itself had no built-in class-file-manipulation API despite the JDK's own internal tools (the compiler, `javap`, various bytecode-instrumenting agents) needing exactly this capability. The Class-File API gives that capability a standard, first-class home in the JDK, modeled to naturally track each new class file format version the JVM specification introduces going forward. Being a preview feature, it requires `--enable-preview`.

## 2. Why & when

Bytecode manipulation libraries like ASM have served the ecosystem well for two decades, but they exist entirely outside the JDK's own release and versioning process — every time the class file format gains a new feature (as it does regularly, tracking new language and JVM capabilities), external libraries have to catch up on their own schedule, and the JDK's own internal tools historically maintained a private, unsupported, and less capable copy of similar bytecode-handling logic just to keep pace with the JDK's own release cadence, without exposing it as public API. The Class-File API changes this by making bytecode manipulation an official part of the JDK, released and versioned in lockstep with the class file format itself — meaning frameworks doing bytecode generation or analysis (dependency injection frameworks generating proxy classes, mocking libraries generating dynamic subclasses, profilers instrumenting method bodies, static analysis tools) gain a standard, JDK-supported alternative to third-party bytecode libraries, one that's guaranteed to understand the newest class file features the moment a new JDK ships them.

## 3. Core concept

```java
import java.lang.classfile.*;
import java.lang.constant.*;

byte[] classBytes = Files.readAllBytes(Path.of("Example.class"));
ClassModel classModel = ClassFile.of().parse(classBytes);

System.out.println("class: " + classModel.thisClass().asInternalName());
for (MethodModel method : classModel.methods()) {
    System.out.println("  method: " + method.methodName().stringValue()
        + method.methodTypeSymbol().displayDescriptor());
}
```

This reads an existing compiled class file and lists every method it declares — without any third-party bytecode library on the classpath.

## 4. Diagram

<svg viewBox="0 0 640 190" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="The Class-File API parses a compiled class file into a model of its constant pool, fields, and methods, and can also generate new class files from a builder API">
  <rect x="20" y="20" width="180" height="50" rx="8" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="110" y="50" fill="#6db33f" font-size="11" text-anchor="middle" font-family="sans-serif">Example.class (bytes)</text>

  <line x1="200" y1="45" x2="250" y2="45" stroke="#79c0ff" stroke-width="2" marker-end="url(#arrow767)"/>
  <defs><marker id="arrow767" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L6,3 L0,6 Z" fill="#79c0ff"/></marker></defs>

  <rect x="260" y="20" width="160" height="50" rx="8" fill="#0f1620" stroke="#79c0ff"/>
  <text x="340" y="50" fill="#79c0ff" font-size="11" text-anchor="middle" font-family="sans-serif">ClassModel</text>

  <line x1="420" y1="45" x2="470" y2="45" stroke="#79c0ff" stroke-width="2" marker-end="url(#arrow767)"/>

  <rect x="480" y="20" width="140" height="50" rx="8" fill="#0f1620" stroke="#8b949e"/>
  <text x="550" y="45" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">methods, fields, ...</text>

  <text x="320" y="150" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">A standard, JDK-versioned replacement for third-party bytecode libraries like ASM</text>
</svg>

*The API models a class file's structure directly, without a third-party bytecode library.*

## 5. Runnable example

Scenario: a small bytecode inspection and transformation tool, growing from reading method names to adding logging instrumentation to an existing class file.

### Level 1 — Basic

```java
import java.lang.classfile.*;
import java.nio.file.*;

public class ClassInspectorBasic {
    public static void main(String[] args) throws Exception {
        byte[] classBytes = Files.readAllBytes(Path.of("ClassInspectorBasic.class"));
        ClassModel classModel = ClassFile.of().parse(classBytes);

        System.out.println("Class: " + classModel.thisClass().asInternalName());
        for (MethodModel method : classModel.methods()) {
            System.out.println("  Method: " + method.methodName().stringValue());
        }
    }
}
```

**How to run:** `javac --enable-preview --release 22 ClassInspectorBasic.java && java --enable-preview ClassInspectorBasic` (JDK 22+; run after compiling, so the `.class` file to inspect actually exists on disk).

This reads its own compiled `.class` file and lists its declared methods — the simplest possible use of the parsing side of the API.

### Level 2 — Intermediate

```java
import java.lang.classfile.*;
import java.lang.constant.*;
import java.nio.file.*;
import java.util.*;

public class ClassInspectorDetailed {
    public static void main(String[] args) throws Exception {
        byte[] classBytes = Files.readAllBytes(Path.of("ClassInspectorDetailed.class"));
        ClassModel classModel = ClassFile.of().parse(classBytes);

        System.out.println("Class: " + classModel.thisClass().asInternalName());
        System.out.println("Superclass: " + classModel.superclass().map(ClassEntry::asInternalName).orElse("(none)"));

        for (MethodModel method : classModel.methods()) {
            List<String> flags = new ArrayList<>();
            if (method.flags().has(AccessFlag.PUBLIC)) flags.add("public");
            if (method.flags().has(AccessFlag.STATIC)) flags.add("static");
            System.out.println("  " + String.join(" ", flags) + " "
                + method.methodName().stringValue()
                + method.methodTypeSymbol().displayDescriptor());
        }
    }
}
```

**How to run:** `javac --enable-preview --release 22 ClassInspectorDetailed.java && java --enable-preview ClassInspectorDetailed`.

The real-world concern added: inspecting each method's **access flags** (public, static) and full **descriptor** (its parameter and return types), not just its name — the kind of detailed structural information a real bytecode-analysis or instrumentation tool needs to make decisions about what to transform.

### Level 3 — Advanced

```java
import java.lang.classfile.*;
import java.lang.constant.*;
import java.nio.file.*;

public class ClassTransformerAdvanced {
    public static void main(String[] args) throws Exception {
        byte[] originalBytes = Files.readAllBytes(Path.of("Target.class"));

        // Transform: wrap every method body with entry/exit logging via
        // CodeTransform, without hand-writing bytecode instructions directly.
        ClassTransform loggingTransform = ClassTransform.transformingMethodBodies(
            (codeBuilder, codeElement) -> codeBuilder.with(codeElement)
        );

        byte[] transformedBytes = ClassFile.of().transformClass(
            ClassFile.of().parse(originalBytes),
            loggingTransform
        );

        Files.write(Path.of("Target_transformed.class"), transformedBytes);
        System.out.println("wrote transformed class: " + transformedBytes.length + " bytes"
            + " (original: " + originalBytes.length + " bytes)");

        // Verify the transformed class still parses correctly
        ClassModel transformedModel = ClassFile.of().parse(transformedBytes);
        System.out.println("transformed class still valid: " + transformedModel.thisClass().asInternalName());
    }
}
```

**How to run:** first compile a small `Target.java` file to produce `Target.class`, then `javac --enable-preview --release 22 ClassTransformerAdvanced.java && java --enable-preview ClassTransformerAdvanced`.

This adds the production-flavored hard case: actually **transforming** a class file (not just reading it) using `ClassFile.transformClass` with a `ClassTransform`, producing a new, modified `.class` file — the kind of instrumentation-style transformation that frameworks doing bytecode weaving (adding logging, metrics, or AOP-style advice to existing compiled classes) perform, here done through the standard JDK API rather than a third-party bytecode library.

## 6. Walkthrough

Tracing `ClassTransformerAdvanced.main`:

1. `main` reads `Target.class`'s raw bytes from disk into `originalBytes`.
2. `ClassFile.of().parse(originalBytes)` parses those bytes into a `ClassModel` — a structured, navigable representation of the class's constant pool, fields, methods, and their bytecode instructions.
3. `ClassTransform.transformingMethodBodies(...)` builds a transform that will be applied to every method body found in the class; the lambda here is a minimal passthrough (`codeBuilder.with(codeElement)`, copying each instruction unchanged) — a real instrumentation transform would inspect or insert additional instructions at this point (for example, emitting a call to a logging method at the start and end of each method body).
4. `ClassFile.of().transformClass(classModel, loggingTransform)` applies the transform across the entire class, producing a **new** byte array, `transformedBytes`, representing a modified (here, structurally identical but freshly re-emitted) class file.
5. `main` writes `transformedBytes` to `Target_transformed.class` and prints both files' byte sizes for comparison.
6. As a validation step, `main` re-parses `transformedBytes` back into a `ClassModel` and prints its class name — confirming the transformation produced a **structurally valid** class file, not just an arbitrary byte array, since a genuinely broken transformation would either fail to parse here or fail to load if actually run by a JVM.

Expected output shape (sizes vary based on the actual `Target` class's contents):
```
wrote transformed class: 512 bytes (original: 498 bytes)
transformed class still valid: Target
```

## 7. Gotchas & takeaways

> **Gotcha:** this is a preview feature, and bytecode-manipulation APIs are inherently tied to the JVM specification's class file format — code written against `java.lang.classfile` in Java 22 should be expected to need at least minor adjustment as the API itself and the underlying class file format both continue evolving toward eventual standardization.

- Preview feature in Java 22 — requires `--enable-preview` at compile and run time.
- Replaces the need for third-party bytecode libraries (ASM, BCEL) for many common parsing, analysis, and transformation tasks, with an API maintained in lockstep with the JDK's own class file format support.
- `ClassModel` gives structured, navigable access to a class's constant pool, fields, methods, and bytecode — no manual byte-offset parsing required.
- `ClassTransform` (and the related `CodeTransform` for method bodies) support building new, modified class files from existing ones without hand-assembling bytecode instructions directly.
- Best suited for framework and tooling authors (DI containers, mocking libraries, profilers, static analysis tools) rather than typical application code, which rarely needs to read or generate class files directly.

---
card: java
gi: 784
slug: class-file-api-standardized
title: Class-File API — standardized
---

## 1. What it is

**Java 24** (JEP 484) makes `java.lang.classfile` a **permanent, standard part** of the JDK — no `--enable-preview` flag required — after two preview rounds ([Java 22](0767-class-file-api-preview.md), [Java 23](0779-class-file-api-2nd-preview.md)). `ClassFile`, `ClassModel`, `MethodModel`, `ClassTransform`, `CodeTransform`, and the stateful-transform and automatic stack-map-frame-regeneration refinements from the second preview are all stable API: parsing, generating, and transforming `.class` files is now something the JDK supports directly, without any third-party bytecode library and without any preview gate.

## 2. Why & when

The Class-File API's two preview rounds carried unusually high stakes for a "standardize this API" decision, because the JDK's *own internal tools* — `javac`, `javap`, and various bytecode-processing utilities — migrated to use it internally during the preview period, meaning the API had to prove itself capable enough to replace decades of internal, unpublished bytecode-handling logic before it could be trusted as public API. By Java 24, that migration was far enough along, and enough external feedback (particularly around the second preview's stateful transforms and reliable stack-map-frame regeneration) had validated the design, that standardization became the natural next step. For framework and tooling authors — dependency injection containers generating proxy classes, mocking libraries generating dynamic subclasses, profilers and static analysis tools reading or instrumenting bytecode — this removes both the preview-flag requirement and, longer term, one more reason to depend on an external bytecode library like ASM at all.

## 3. Core concept

```java
import java.lang.classfile.*;
import java.nio.file.*;

// No --enable-preview needed anymore — this is standard Java 24 API.
byte[] classBytes = Files.readAllBytes(Path.of("Example.class"));
ClassModel classModel = ClassFile.of().parse(classBytes);

System.out.println("class: " + classModel.thisClass().asInternalName());
for (MethodModel method : classModel.methods()) {
    System.out.println("  method: " + method.methodName().stringValue());
}
```

The same parsing API from both preview rounds, now compiled and run with no special flags.

## 4. Diagram

<svg viewBox="0 0 640 190" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="The Class-File API standardizes after two preview rounds during which the JDK's own internal tools migrated to use it, becoming a permanent replacement for third-party bytecode libraries">
  <rect x="20" y="20" width="600" height="40" rx="8" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="320" y="45" fill="#6db33f" font-size="12" text-anchor="middle" font-family="sans-serif">Java 22 preview -&gt; Java 23 2nd preview -&gt; Java 24 standard</text>

  <rect x="40" y="90" width="260" height="55" rx="8" fill="#0f1620" stroke="#79c0ff"/>
  <text x="170" y="112" fill="#79c0ff" font-size="10" text-anchor="middle" font-family="sans-serif">JDK's own tools (javac, javap)</text>
  <text x="170" y="130" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">migrated internally during preview</text>

  <rect x="340" y="90" width="260" height="55" rx="8" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="470" y="112" fill="#6db33f" font-size="10" text-anchor="middle" font-family="sans-serif">java.lang.classfile</text>
  <text x="470" y="130" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">standard as of Java 24</text>

  <text x="320" y="170" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">Proven internally by the JDK's own tools before becoming public, stable API</text>
</svg>

*The API that now underlies the JDK's own bytecode tooling is available to every application, standard.*

## 5. Runnable example

Scenario: a small bytecode inspection and transformation tool, growing from reading method names into a stateful instrumentation transform — all running as standard Java 24 code with no preview flags.

### Level 1 — Basic

```java
import java.lang.classfile.*;
import java.nio.file.*;

public class ClassFileStandardBasic {
    public static void main(String[] args) throws Exception {
        byte[] classBytes = Files.readAllBytes(Path.of("ClassFileStandardBasic.class"));
        ClassModel classModel = ClassFile.of().parse(classBytes);

        System.out.println("Class: " + classModel.thisClass().asInternalName());
        for (MethodModel method : classModel.methods()) {
            System.out.println("  Method: " + method.methodName().stringValue());
        }
    }
}
```

**How to run:** `javac ClassFileStandardBasic.java && java ClassFileStandardBasic` (JDK 24+, no `--enable-preview` needed).

Reads its own compiled `.class` file and lists its declared methods — the simplest use of the parsing API, now standard.

### Level 2 — Intermediate

```java
import java.lang.classfile.*;
import java.nio.file.*;
import java.util.*;

public class ClassFileStandardDetailed {
    public static void main(String[] args) throws Exception {
        byte[] classBytes = Files.readAllBytes(Path.of("ClassFileStandardDetailed.class"));
        ClassModel classModel = ClassFile.of().parse(classBytes);

        System.out.println("Class: " + classModel.thisClass().asInternalName());
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

**How to run:** `javac ClassFileStandardDetailed.java && java ClassFileStandardDetailed`.

The real-world concern added: inspecting each method's access flags and full descriptor — the same detailed structural information a real bytecode-analysis tool needs, exercised without any preview gate.

### Level 3 — Advanced

```java
import java.lang.classfile.*;
import java.nio.file.*;

public class ClassFileStandardTransform {
    public static void main(String[] args) throws Exception {
        byte[] originalBytes = Files.readAllBytes(Path.of("Target.class"));
        ClassModel classModel = ClassFile.of().parse(originalBytes);

        ClassTransform countingTransform = ClassTransform.transformingMethodBodies(
            () -> new int[]{0}, // stateful transform: standardized behavior from the 2nd preview
            (state, codeBuilder, codeElement) -> {
                state[0]++;
                codeBuilder.with(codeElement);
            }
        );

        byte[] transformed = ClassFile.of().transformClass(classModel, countingTransform);
        Files.write(Path.of("Target_transformed.class"), transformed);

        ClassModel verifyModel = ClassFile.of().parse(transformed);
        System.out.println("transformed class verified OK: " + verifyModel.thisClass().asInternalName());
        System.out.println("original: " + originalBytes.length + " bytes, transformed: " + transformed.length + " bytes");
    }
}
```

**How to run:** first compile a small `Target.java` to produce `Target.class`, then `javac ClassFileStandardTransform.java && java ClassFileStandardTransform`.

This adds the production-flavored hard case: a **stateful transform** with automatic stack-map-frame regeneration — the exact capability the second preview refined — now running as fully standard code, demonstrating that the transform/verification pipeline from the preview rounds carries forward unchanged into Java 24.

## 6. Walkthrough

Tracing `ClassFileStandardTransform.main`:

1. `main` reads `Target.class` and parses it into a `ClassModel`.
2. `ClassTransform.transformingMethodBodies(stateSupplier, callback)` builds a stateful transform — a fresh `int[]{0}` counter per method body — identical in shape to the preview-round example.
3. `ClassFile.of().transformClass(...)` walks the class, incrementing each method's counter per instruction and writing every element through unchanged via `codeBuilder.with(codeElement)`.
4. The resulting byte array has its **stack map frames** automatically regenerated by the API, exactly as in the second preview, and is written to `Target_transformed.class`.
5. `main` re-parses the transformed bytes as a structural sanity check, printing the resulting class name to confirm the output is well-formed.
6. Finally, it prints the byte-size comparison between the original and transformed class files.

Expected output shape (exact sizes depend on `Target`'s contents):
```
transformed class verified OK: Target
original: 498 bytes, transformed: 498 bytes
```

## 7. Gotchas & takeaways

> **Gotcha:** standardization doesn't mean the class file *format* itself stops evolving — new JVM bytecode features in future releases will still extend `java.lang.classfile`'s model to represent them, in a purely additive way. Code depending on this API should still expect to encounter new element kinds appearing in class files compiled by future JDKs, and should be written defensively around unrecognized elements where relevant, exactly as with any format that continues to evolve.

- Standardized in Java 24 (JEP 484) — no `--enable-preview` flag needed; production-ready.
- The API is unchanged from the [second preview](0779-class-file-api-2nd-preview.md), including stateful transforms and automatic stack-map-frame regeneration.
- The JDK's own internal tools (`javac`, `javap`, and others) migrated to this API during the preview period, giving it unusually thorough internal validation before standardization.
- Standard, JDK-maintained bytecode manipulation is now available with no external dependency and no preview flag — a direct, supported alternative to third-party libraries like ASM for many common tasks.
- Best suited to framework and tooling authors; typical application code still rarely needs to read or generate class files directly.

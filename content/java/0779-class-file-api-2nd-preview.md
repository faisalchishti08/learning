---
card: java
gi: 779
slug: class-file-api-2nd-preview
title: Class-File API (2nd preview)
---

## 1. What it is

**Java 23** (JEP 466) is the **second preview** of the [Class-File API](0767-class-file-api-preview.md), continuing from Java 22's first preview. The core model — `ClassFile.of()` as the entry point, `ClassModel`/`MethodModel`/`FieldModel` for parsing, and `ClassTransform`/`CodeTransform` for producing modified class files — carries forward unchanged. This round's refinements focus on **stateful transforms**: applying a transform that needs to track information *across* multiple elements of a method body (not just react to each instruction in isolation) and on more reliable automatic **stack-map-frame** regeneration, so a transformed class file remains verifiable by the JVM without the caller having to hand-manage low-level bytecode verification metadata.

## 2. Why & when

The first preview's examples mostly transformed method bodies element-by-element — copy this instruction, skip that one — which covers plenty of real cases but not all of them. Real instrumentation work often needs **running state across a method body**: counting how many times a particular kind of instruction appears before deciding how to modify a later one, or inserting a single "setup" instruction only once at the very start of a body while still processing every instruction after it normally. The first preview's transform API made this awkward, since each transform callback received an element with no obvious place to keep such state between calls. This round adds a cleaner way to build a transform with associated state, and pairs it with more dependable automatic stack-map-frame recomputation — a notoriously fiddly piece of the class file format that, get it wrong, and the JVM's bytecode verifier rejects the class outright with a `VerifyError`, even if the executable logic itself would have run correctly.

## 3. Core concept

```java
import java.lang.classfile.*;

// A stateful transform: count instructions seen, insert one extra
// instruction only the first time a particular kind is encountered.
ClassFile.of().transformClass(classModel, ClassTransform.transformingMethodBodies(
    () -> new int[]{0}, // fresh state per method body
    (state, codeBuilder, codeElement) -> {
        state[0]++;
        codeBuilder.with(codeElement);
    }
));
```

The state-supplying overload gives each method body its own fresh counter, threaded through every element of that body's transform — something the first preview's stateless callback shape didn't offer directly.

## 4. Diagram

<svg viewBox="0 0 640 190" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="A stateful code transform threads a piece of state through every instruction of a method body, and the API automatically regenerates correct stack map frames for the resulting class" >
  <rect x="20" y="20" width="600" height="36" rx="8" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="320" y="43" fill="#6db33f" font-size="12" text-anchor="middle" font-family="sans-serif">stateful CodeTransform: same state object flows through every instruction</text>

  <rect x="40" y="80" width="130" height="45" rx="6" fill="#0f1620" stroke="#79c0ff"/>
  <text x="105" y="107" fill="#79c0ff" font-size="10" text-anchor="middle" font-family="sans-serif">instr 1 -&gt; state</text>

  <rect x="190" y="80" width="130" height="45" rx="6" fill="#0f1620" stroke="#79c0ff"/>
  <text x="255" y="107" fill="#79c0ff" font-size="10" text-anchor="middle" font-family="sans-serif">instr 2 -&gt; state</text>

  <rect x="340" y="80" width="130" height="45" rx="6" fill="#0f1620" stroke="#79c0ff"/>
  <text x="405" y="107" fill="#79c0ff" font-size="10" text-anchor="middle" font-family="sans-serif">instr 3 -&gt; state</text>

  <rect x="490" y="80" width="130" height="45" rx="6" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="555" y="107" fill="#6db33f" font-size="10" text-anchor="middle" font-family="sans-serif">stack maps regenerated</text>

  <text x="320" y="165" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">State accumulates across a method body; verification metadata is handled automatically</text>
</svg>

*A stateful transform accumulates information across an entire method body without manual bookkeeping outside the API.*

## 5. Runnable example

Scenario: instrumenting method bodies with entry-count logging, growing from the stateless transform style into a stateful transform that inserts a log call only once per method, then verifying the transformed class still passes JVM bytecode verification.

### Level 1 — Basic

```java
import java.lang.classfile.*;
import java.nio.file.*;

public class ClassTransformStateless {
    public static void main(String[] args) throws Exception {
        byte[] originalBytes = Files.readAllBytes(Path.of("ClassTransformStateless.class"));
        ClassModel classModel = ClassFile.of().parse(originalBytes);

        ClassTransform passthrough = ClassTransform.transformingMethodBodies(
            (codeBuilder, codeElement) -> codeBuilder.with(codeElement)
        );

        byte[] transformed = ClassFile.of().transformClass(classModel, passthrough);
        System.out.println("original: " + originalBytes.length + " bytes, transformed: " + transformed.length + " bytes");
    }
}
```

**How to run:** `javac --enable-preview --release 23 ClassTransformStateless.java && java --enable-preview ClassTransformStateless` (JDK 23+).

This is the stateless transform shape from the first preview: every instruction is copied through unchanged, with no memory of what came before it in the same method body.

### Level 2 — Intermediate

```java
import java.lang.classfile.*;
import java.nio.file.*;

public class ClassTransformCounting {
    public static void main(String[] args) throws Exception {
        byte[] originalBytes = Files.readAllBytes(Path.of("ClassTransformCounting.class"));
        ClassModel classModel = ClassFile.of().parse(originalBytes);

        ClassTransform counting = ClassTransform.transformingMethodBodies(
            () -> new int[]{0}, // fresh instruction counter per method body
            (state, codeBuilder, codeElement) -> {
                state[0]++;
                codeBuilder.with(codeElement);
            }
        );

        byte[] transformed = ClassFile.of().transformClass(classModel, counting);
        ClassModel transformedModel = ClassFile.of().parse(transformed);
        System.out.println("transformed class parses OK: " + transformedModel.thisClass().asInternalName());
    }
}
```

**How to run:** `javac --enable-preview --release 23 ClassTransformCounting.java && java --enable-preview ClassTransformCounting`.

The real-world concern added: the stateful overload of `transformingMethodBodies` supplies a **fresh state object per method body** (here, an instruction counter), threaded through every `codeElement` callback for that body — the kind of running state a stateless transform simply has nowhere to hold.

### Level 3 — Advanced

```java
import java.lang.classfile.*;
import java.lang.constant.*;
import java.nio.file.*;

public class ClassTransformInsertOnce {
    public static void main(String[] args) throws Exception {
        byte[] originalBytes = Files.readAllBytes(Path.of("Target.class"));
        ClassModel classModel = ClassFile.of().parse(originalBytes);

        ClassTransform insertOnceLogging = ClassTransform.transformingMethodBodies(
            () -> new boolean[]{false}, // "have we inserted the entry log yet?"
            (state, codeBuilder, codeElement) -> {
                if (!state[0] && codeElement instanceof Instruction) {
                    // Insert a marker exactly once, before the first real instruction.
                    codeBuilder.nop();
                    state[0] = true;
                }
                codeBuilder.with(codeElement);
            }
        );

        byte[] transformed = ClassFile.of().transformClass(classModel, insertOnceLogging);

        Files.write(Path.of("Target_instrumented.class"), transformed);

        // Verification: re-parsing succeeds only if stack map frames stayed consistent.
        ClassModel verifyModel = ClassFile.of().parse(transformed);
        System.out.println("instrumented class verified OK: " + verifyModel.thisClass().asInternalName());
        System.out.println("original: " + originalBytes.length + " bytes, instrumented: " + transformed.length + " bytes");
    }
}
```

**How to run:** first compile a small `Target.java` to produce `Target.class`, then `javac --enable-preview --release 23 ClassTransformInsertOnce.java && java --enable-preview ClassTransformInsertOnce`.

This adds the production-flavored hard case: inserting an **extra instruction** (a `nop`, standing in for a real instrumentation call like a logging invocation) exactly once at the start of every method body, then relying on `ClassFile.of()`'s **automatic stack-map-frame regeneration** so the modified bytecode still passes verification when re-parsed — manually recomputing stack map frames by hand after inserting instructions is one of the most error-prone parts of bytecode manipulation with lower-level tools, and the API handles it transparently here.

## 6. Walkthrough

Tracing `ClassTransformInsertOnce.main`:

1. `main` reads `Target.class` and parses it into a `ClassModel`, giving structured access to its methods and their bytecode.
2. `ClassTransform.transformingMethodBodies(stateSupplier, callback)` is built with a state supplier returning a fresh `boolean[]{false}` **for each method body** the class contains — every method gets its own independent "have I inserted yet?" flag.
3. `ClassFile.of().transformClass(classModel, insertOnceLogging)` walks the class, and for each method body, walks its elements (instructions, labels, and other code elements) in order, invoking the callback once per element with that method's state array.
4. For the **first** real `Instruction` element in each method body, `state[0]` is still `false`, so the callback calls `codeBuilder.nop()` — emitting a single no-op instruction as a stand-in for real instrumentation — and sets `state[0] = true` so no further insertions happen for the rest of that method's body.
5. Every element, including the one that triggered the insertion, is then written to the output via `codeBuilder.with(codeElement)` — so the original instruction stream is fully preserved, just with one extra instruction prepended per method.
6. After all methods are processed, `transformClass` returns a complete, reassembled class file as a byte array — critically, the class file's **stack map frames** (metadata the JVM's verifier uses to check type-safety without doing full dataflow analysis at load time) are recomputed automatically to account for the inserted instructions, rather than needing manual adjustment.
7. `main` writes the result to `Target_instrumented.class`, then immediately re-parses it with `ClassFile.of().parse(transformed)` as a verification step — if the stack map frames were wrong, this re-parse (or, more strictly, actually loading the class into a running JVM) would surface an error; succeeding confirms the transformation produced a structurally sound class file.

Expected output shape (exact byte counts depend on `Target`'s contents):
```
instrumented class verified OK: Target
original: 498 bytes, instrumented: 512 bytes
```

## 7. Gotchas & takeaways

> **Gotcha:** re-parsing a transformed class file with `ClassFile.of().parse(...)` confirms it's **structurally well-formed**, but it does not run the JVM's full bytecode verifier the way actually loading and executing the class would — for high-confidence validation of a transform (especially one inserting or reordering real instructions, not just a `nop`), load the resulting class in an actual JVM and exercise it, rather than trusting successful re-parsing alone.

- Second preview in Java 23 (JEP 466) — refines [the first preview](0767-class-file-api-preview.md)'s transform API with stateful transforms and more reliable automatic stack-map-frame regeneration; still requires `--enable-preview`.
- The state-supplying overload of `transformingMethodBodies` gives each method body its own fresh state object, threaded through every element callback for that body.
- Automatic stack-map-frame regeneration means most instruction-inserting transforms don't need manual bytecode-verification bookkeeping — a major source of bugs in lower-level bytecode tools.
- Re-parsing a transformed class file is a useful sanity check, but actually loading and running it is the stronger verification step before trusting a transform in production.
- As with the first preview, this API targets framework and tooling authors doing bytecode analysis or instrumentation, not typical application code.

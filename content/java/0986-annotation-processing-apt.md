---
card: java
gi: 986
slug: annotation-processing-apt
title: Annotation processing (APT)
---

## 1. What it is

Annotation processing is a compile-time mechanism (the API is `javax.annotation.processing`, commonly still called "APT" after its original standalone tool name) that lets you plug custom code into the Java compiler itself: a class implementing `Processor` (usually by extending the convenience base class `AbstractProcessor`) is invoked by `javac` during compilation, given access to every annotated element in the source being compiled, and can inspect that code, validate it (reporting compile errors for misuse), and — most powerfully — generate entirely new Java source files that are then compiled alongside the original code, in the same build. This is fundamentally different from reading annotations reflectively at *runtime* (`method.getAnnotation(MyAnnotation.class)`): annotation processing runs during compilation, before any `.class` files even exist yet, and its output becomes part of the actual compiled program.

## 2. Why & when

This mechanism is what makes several widely-used, code-generation-based libraries possible: Lombok (generating getters, setters, constructors, and `equals`/`hashCode` from annotations like `@Data`), Dagger (generating entire dependency-injection wiring code from `@Inject`-annotated constructors), and various ORM/mapping libraries (generating type-safe query metaclasses from `@Entity`-annotated classes) all rely on annotation processors to write real, ordinary Java source code during your build, which is then compiled normally — meaning the generated code is fully visible to your IDE, fully debuggable, and imposes zero runtime reflection overhead, since all the "magic" happened once, at compile time, producing perfectly ordinary compiled classes. Reach for writing your own annotation processor specifically when you find yourself wanting to eliminate genuinely repetitive, mechanically-derivable boilerplate from annotated classes — a pattern repeated across many classes that could instead be automatically generated once, correctly, from a shared processor, with the compiler itself catching a wide class of usage mistakes (an annotation applied to the wrong kind of element, missing a required companion annotation) as actual compile errors rather than subtle runtime bugs.

## 3. Core concept

```java
// The annotation itself, with RUNTIME... actually SOURCE retention is enough for
// pure compile-time processing (no runtime reflection needed on this annotation at all):
@Retention(RetentionPolicy.SOURCE)
@Target(ElementType.TYPE)
public @interface GenerateBuilder {}

// The PROCESSOR: registered with javac, invoked automatically during compilation
public class BuilderProcessor extends AbstractProcessor {
    @Override
    public boolean process(Set<? extends TypeElement> annotations, RoundEnvironment env) {
        for (Element element : env.getElementsAnnotatedWith(GenerateBuilder.class)) {
            // ... generate a companion "FooBuilder" class as real Java source,
            //     written via a Filer, compiled alongside the original code ...
        }
        return true;
    }
}
```

The processor runs *during* `javac`'s compilation of your source, with access to the full, unresolved abstract syntax structure of the code being compiled — its generated output becomes additional input to that same compilation round, producing ordinary `.class` files exactly as if you had hand-written that generated source yourself.

## 4. Diagram

<svg viewBox="0 0 640 170" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="The Java compiler invoking a registered annotation processor during compilation, which inspects annotated source, generates new Java source files, and feeds them back into the same compilation to produce ordinary class files" >
  <rect x="20" y="60" width="140" height="40" fill="#1c2430" stroke="#79c0ff"/>
  <text x="90" y="85" fill="#79c0ff" font-size="10" text-anchor="middle" font-family="sans-serif">Your annotated source</text>

  <rect x="220" y="20" width="200" height="40" fill="#1c2430" stroke="#6db33f"/>
  <text x="320" y="45" fill="#6db33f" font-size="10" text-anchor="middle" font-family="sans-serif">javac invokes Processor</text>

  <rect x="220" y="100" width="200" height="40" fill="#1c2430" stroke="#f0883e"/>
  <text x="320" y="125" fill="#f0883e" font-size="10" text-anchor="middle" font-family="sans-serif">Processor GENERATES new .java</text>

  <rect x="480" y="60" width="140" height="40" fill="#1c2430" stroke="#e6edf3"/>
  <text x="550" y="85" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">Compiled .class files</text>

  <line x1="160" y1="70" x2="220" y2="45" stroke="#8b949e" marker-end="url(#a)"/>
  <line x1="320" y1="60" x2="320" y2="100" stroke="#8b949e" marker-end="url(#a)"/>
  <line x1="420" y1="120" x2="480" y2="85" stroke="#8b949e" marker-end="url(#a)"/>
  <line x1="420" y1="40" x2="480" y2="75" stroke="#8b949e" marker-end="url(#a)"/>
</svg>

*The processor inspects annotated source during compilation and generates new source, which is compiled alongside the original into ordinary class files.*

## 5. Runnable example

Scenario: build a small annotation processor that generates a companion "Builder" class for an annotated data class, evolving from a basic processor that only inspects and prints messages, to one that actually generates real Java source code, to a more advanced case adding compile-time validation that rejects misuse as a genuine compiler error.

### Level 1 — Basic

```java
// File: GenerateBuilder.java
import java.lang.annotation.*;

@Retention(RetentionPolicy.SOURCE)
@Target(ElementType.TYPE)
public @interface GenerateBuilder {}
```

```java
// File: InspectingProcessor.java
import javax.annotation.processing.*;
import javax.lang.model.SourceVersion;
import javax.lang.model.element.*;
import java.util.*;

@SupportedAnnotationTypes("GenerateBuilder")
@SupportedSourceVersion(SourceVersion.RELEASE_17)
public class InspectingProcessor extends AbstractProcessor {
    @Override
    public boolean process(Set<? extends TypeElement> annotations, RoundEnvironment env) {
        for (Element element : env.getElementsAnnotatedWith(GenerateBuilder.class)) {
            processingEnv.getMessager().printMessage(
                Diagnostic.Kind.NOTE, "found @GenerateBuilder on: " + element.getSimpleName());
        }
        return true;
    }
}
```

```java
// File: Point.java
@GenerateBuilder
public class Point {
    int x, y;
}
```

**How to run:** `javac InspectingProcessor.java GenerateBuilder.java` (compile the processor first, JDK 17+), then `javac -processor InspectingProcessor Point.java` (compile `Point.java`, explicitly invoking the processor).

Expected output (printed by `javac` itself during the second compile command, to stderr, as a NOTE-level diagnostic):
```
Note: found @GenerateBuilder on: Point
```

The processor runs as part of compiling `Point.java`, inspecting its annotated elements and printing a diagnostic message through the compiler's own `Messager` — no new code is generated yet at this stage, but this confirms the processor is genuinely being invoked during compilation and can see exactly which class was annotated.

### Level 2 — Intermediate

```java
// File: BuilderGeneratingProcessor.java
import javax.annotation.processing.*;
import javax.lang.model.SourceVersion;
import javax.lang.model.element.*;
import javax.tools.*;
import java.io.*;
import java.util.*;

@SupportedAnnotationTypes("GenerateBuilder")
@SupportedSourceVersion(SourceVersion.RELEASE_17)
public class BuilderGeneratingProcessor extends AbstractProcessor {
    @Override
    public boolean process(Set<? extends TypeElement> annotations, RoundEnvironment env) {
        for (Element element : env.getElementsAnnotatedWith(GenerateBuilder.class)) {
            String className = element.getSimpleName().toString();
            String builderName = className + "Builder";
            try {
                JavaFileObject file = processingEnv.getFiler().createSourceFile(builderName);
                try (Writer writer = file.openWriter()) {
                    writer.write("public class " + builderName + " {\n");
                    writer.write("    int x, y;\n");
                    writer.write("    public " + builderName + " x(int x) { this.x = x; return this; }\n");
                    writer.write("    public " + builderName + " y(int y) { this.y = y; return this; }\n");
                    writer.write("    public " + className + " build() {\n");
                    writer.write("        " + className + " p = new " + className + "();\n");
                    writer.write("        p.x = x; p.y = y;\n");
                    writer.write("        return p;\n");
                    writer.write("    }\n");
                    writer.write("}\n");
                }
            } catch (IOException e) {
                processingEnv.getMessager().printMessage(Diagnostic.Kind.ERROR, "failed to generate: " + e.getMessage());
            }
        }
        return true;
    }
}
```

```java
// File: PointUser.java
public class PointUser {
    public static void main(String[] args) {
        Point p = new PointBuilder().x(3).y(4).build(); // PointBuilder does not exist in source --
                                                          // it's GENERATED by the processor at compile time
        System.out.println("built point: (" + p.x + ", " + p.y + ")");
    }
}
```

**How to run:** `javac BuilderGeneratingProcessor.java GenerateBuilder.java` (JDK 17+), then `javac -processor BuilderGeneratingProcessor -d out Point.java PointUser.java` (compiles everything together, generating `PointBuilder.java` automatically as part of this step), then `java -cp out PointUser`.

Expected output:
```
built point: (3, 4)
```

The real-world concern added: `PointBuilder` is never written by hand anywhere — `BuilderGeneratingProcessor` generates its complete source code during the compilation of `Point.java`, and that generated source is compiled *in the same build*, producing an ordinary `PointBuilder.class` that `PointUser.java` can reference and use exactly as if it had been hand-written; this is the genuine code-generation capability annotation processing provides, distinct from merely inspecting or logging during compilation.

### Level 3 — Advanced

```java
// File: ValidatingProcessor.java
import javax.annotation.processing.*;
import javax.lang.model.SourceVersion;
import javax.lang.model.element.*;
import javax.tools.*;
import java.io.*;
import java.util.*;

@SupportedAnnotationTypes("GenerateBuilder")
@SupportedSourceVersion(SourceVersion.RELEASE_17)
public class ValidatingProcessor extends AbstractProcessor {
    @Override
    public boolean process(Set<? extends TypeElement> annotations, RoundEnvironment env) {
        for (Element element : env.getElementsAnnotatedWith(GenerateBuilder.class)) {
            // VALIDATE: @GenerateBuilder must only be applied to a CLASS, not an interface,
            // enum, or method -- report a genuine compile ERROR (not just a note) if misused.
            if (element.getKind() != ElementKind.CLASS) {
                processingEnv.getMessager().printMessage(
                    Diagnostic.Kind.ERROR,
                    "@GenerateBuilder can only be applied to a class, not " + element.getKind(),
                    element
                );
                continue; // skip generating anything for this misused element
            }

            String className = element.getSimpleName().toString();
            String builderName = className + "Builder";
            try {
                JavaFileObject file = processingEnv.getFiler().createSourceFile(builderName);
                try (Writer writer = file.openWriter()) {
                    writer.write("public class " + builderName + " {\n");
                    writer.write("    int x, y;\n");
                    writer.write("    public " + builderName + " x(int x) { this.x = x; return this; }\n");
                    writer.write("    public " + builderName + " y(int y) { this.y = y; return this; }\n");
                    writer.write("    public " + className + " build() {\n");
                    writer.write("        " + className + " p = new " + className + "();\n");
                    writer.write("        p.x = x; p.y = y;\n");
                    writer.write("        return p;\n");
                    writer.write("    }\n");
                    writer.write("}\n");
                }
            } catch (IOException e) {
                processingEnv.getMessager().printMessage(Diagnostic.Kind.ERROR, "failed to generate: " + e.getMessage());
            }
        }
        return true;
    }
}
```

```java
// File: MisusedAnnotation.java
@GenerateBuilder
public interface MisusedAnnotation {} // MISUSE: applied to an interface, not a class
```

**How to run:** `javac ValidatingProcessor.java GenerateBuilder.java` (JDK 17+), then `javac -processor ValidatingProcessor MisusedAnnotation.java` (this compile command is expected to FAIL).

Expected output (a genuine compile-time error, not a runtime exception):
```
MisusedAnnotation.java:1: error: @GenerateBuilder can only be applied to a class, not INTERFACE
@GenerateBuilder
^
1 error
```

The production-flavored hard case: the processor validates that `@GenerateBuilder` is only ever applied to an actual class, and — critically — reports genuine misuse as a real compiler error, pointing directly at the exact annotation usage responsible, rather than either silently doing nothing or generating broken code that would fail mysteriously later; this is exactly the kind of "catch this class of mistake at compile time, for every user of this annotation, automatically" guarantee that makes well-designed annotation processors far safer to depend on than a purely convention-based, undocumented usage pattern.

## 6. Walkthrough

Tracing what happens when `javac -processor ValidatingProcessor MisusedAnnotation.java` is run, step by step:

1. `javac` parses `MisusedAnnotation.java`, discovers it references the `ValidatingProcessor` (explicitly specified via `-processor`), and, before completing the normal compilation, invokes that processor's `process` method, passing it information about every element in this compilation round annotated with any of the processor's declared `@SupportedAnnotationTypes` (here, just `GenerateBuilder`).
2. `env.getElementsAnnotatedWith(GenerateBuilder.class)` returns a set containing exactly one `Element`: the `MisusedAnnotation` interface declaration itself, since it's the one element in this compilation annotated with `@GenerateBuilder`.
3. The processor's validation check, `element.getKind() != ElementKind.CLASS`, evaluates this element's actual kind — since `MisusedAnnotation` is declared as an `interface`, its kind is `ElementKind.INTERFACE`, not `ElementKind.CLASS`, so this condition is `true`.
4. Because the validation failed, the processor calls `processingEnv.getMessager().printMessage(Diagnostic.Kind.ERROR, ..., element)` — passing `Diagnostic.Kind.ERROR` (rather than the earlier example's `NOTE`) specifically tells the compiler this is a genuine compilation failure, not just informational output, and passing `element` as the third argument tells the compiler exactly which source location this error corresponds to, letting it print a precise line-and-column-pointing error message.
5. Because a compile error was reported, `javac` marks the overall compilation as failed — even though the processor's `process` method itself completed normally (it didn't throw an exception; it simply reported an error through the proper diagnostic channel), the compilation as a whole fails, and no `.class` file is produced for `MisusedAnnotation.java` at all.
6. The `continue` statement in the processor's loop ensures that, having already reported the misuse as an error, no attempt is made to generate a companion builder class for this specific misused element — avoiding a secondary, confusing failure (attempting to generate code referencing an interface as if it were a class) on top of the already-reported, primary validation error, keeping the compiler's output focused on the one, genuinely actionable problem.

## 7. Gotchas & takeaways

> **Gotcha:** annotation processors can run in multiple "rounds" — if a processor generates new source files in one round, the compiler performs an additional round specifically to process that newly generated code (which might itself contain annotations needing processing), and a processor's `process` method needs to be written with this multi-round behavior in mind (checking `RoundEnvironment.processingOver()` for cleanup-only logic, for instance) rather than assuming it will only ever be invoked exactly once per compilation.

- Annotation processing runs during compilation (`javac` invokes registered `Processor` implementations), letting a processor inspect annotated source, validate its usage with genuine compile-time errors, and generate entirely new Java source files compiled alongside the original code.
- This is fundamentally different from runtime reflection-based annotation reading — the generated code becomes part of the actual compiled program, fully visible to IDEs and debuggers, with zero runtime reflection overhead for whatever behavior was generated.
- Reporting a validation failure via `Messager.printMessage(Diagnostic.Kind.ERROR, ...)` produces a genuine compiler error pointed at the exact offending source location, catching a whole class of usage mistakes automatically for every user of an annotation.
- Widely-used libraries like Lombok, Dagger, and various ORM code generators are all built on exactly this mechanism, generating real, ordinary Java source rather than relying on runtime reflection or bytecode manipulation.
- Processors can run across multiple compilation rounds, since newly generated source may itself need further processing — well-written processors account for this rather than assuming single-invocation behavior.
- See [Reflection API deep dive](0983-reflection-api-deep-dive.md) for the runtime alternative to reading annotations (distinct from this compile-time mechanism), and [ServiceLoader & SPI](0988-serviceloader-spi.md) for the runtime service-discovery mechanism annotation processors themselves are typically registered with via `META-INF/services`.

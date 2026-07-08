---
card: java
gi: 421
slug: pluggable-annotation-processing-jsr-269-javax-annotation-pro
title: Pluggable annotation processing (JSR 269, javax.annotation.processing)
---

## 1. What it is

JSR 269, added in Java 6 as `javax.annotation.processing`, lets you plug a custom **annotation processor** directly into the compiler itself. A processor (implementing `Processor`, usually via the convenience base class `AbstractProcessor`) runs *during compilation*, inspecting the source being compiled for specific annotations via the `RoundEnvironment` and `Elements`/`TypeElement` model, and can react in three ways: report compiler errors/warnings through `Messager`, or generate **entirely new source files** through `Filer` that the compiler then automatically compiles alongside the original code, in an additional processing round.

## 2. Why & when

Before JSR 269, validating annotation usage or generating boilerplate code from annotations meant either a separate build step (a code generator run before `javac`) or runtime reflection (checking annotations only once the program is already running, too late to catch a mistake at compile time). Annotation processing runs *as part of compilation itself* — a processor can reject invalid annotation usage with a genuine compiler error (the build fails, exactly like a syntax error would), or generate supporting code that the very same compilation picks up and compiles too, with no extra build step required.

This is the mechanism behind tools you've likely used indirectly: Lombok generates getters/setters/constructors from annotations like `@Data`; Dagger and other dependency-injection frameworks generate wiring code from `@Inject`; MapStruct generates mapper implementations. You'd write a custom processor yourself to enforce project-specific annotation rules at compile time, or to eliminate repetitive generated code (DTOs, builders, registries) without a separate code-generation build step.

## 3. Core concept

```java
import javax.annotation.processing.*;
import javax.lang.model.SourceVersion;
import javax.lang.model.element.*;
import java.util.Set;

@SupportedAnnotationTypes("com.example.Loggable")
public class LoggingProcessor extends AbstractProcessor {
    @Override public SourceVersion getSupportedSourceVersion() { return SourceVersion.latestSupported(); }

    @Override
    public boolean process(Set<? extends TypeElement> annotations, RoundEnvironment roundEnv) {
        for (TypeElement annotation : annotations) {
            for (Element element : roundEnv.getElementsAnnotatedWith(annotation)) {
                // element is a compile-time MODEL of an annotated method/class/field -- not a runtime reflection object
                processingEnv.getMessager().printMessage(Diagnostic.Kind.NOTE,
                    "Found annotation on: " + element.getSimpleName());
            }
        }
        return true; // true = these annotations are fully "claimed" by this processor
    }
}
```

Because `java File.java`'s single-file source-launch mode explicitly disables annotation processing on the file being run (per JEP 330), the runnable examples below instead use the Compiler API from the previous tutorial to drive a **nested** compilation — compiling a separate in-memory source with a processor attached — which works from a single, ordinarily-launched file.

## 4. Diagram

<svg viewBox="0 0 640 200" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="During compilation, javac scans for annotations, invokes registered processors with a model of the annotated elements, and processors can emit diagnostics or generate new source files that trigger an additional compilation round">
  <rect x="8" y="8" width="624" height="184" rx="8" fill="#0d1117"/>
  <rect x="30" y="30" width="140" height="34" rx="6" fill="#1c2430" stroke="#79c0ff"/><text x="100" y="52" fill="#79c0ff" font-size="10" text-anchor="middle" font-family="sans-serif">Source (round 1)</text>
  <rect x="250" y="30" width="140" height="34" rx="6" fill="#1c2430" stroke="#6db33f"/><text x="320" y="52" fill="#6db33f" font-size="10" text-anchor="middle" font-family="sans-serif">Your Processor</text>
  <rect x="470" y="15" width="150" height="34" rx="6" fill="#1c2430" stroke="#f85149"/><text x="545" y="37" fill="#f85149" font-size="10" text-anchor="middle" font-family="sans-serif">Messager: errors/notes</text>
  <rect x="470" y="60" width="150" height="34" rx="6" fill="#1c2430" stroke="#e6edf3"/><text x="545" y="82" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">Filer: new .java file</text>

  <line x1="170" y1="47" x2="245" y2="47" stroke="#8b949e" marker-end="url(#ap1)"/>
  <line x1="390" y1="40" x2="465" y2="32" stroke="#8b949e" marker-end="url(#ap1)"/>
  <line x1="390" y1="55" x2="465" y2="77" stroke="#8b949e" marker-end="url(#ap1)"/>

  <rect x="250" y="130" width="140" height="34" rx="6" fill="#1c2430" stroke="#6db33f"/><text x="320" y="152" fill="#6db33f" font-size="10" text-anchor="middle" font-family="sans-serif">Round 2: compiles generated source too</text>
  <line x1="545" y1="94" x2="320" y2="128" stroke="#8b949e" stroke-dasharray="4,3" marker-end="url(#ap1)"/>
  <defs><marker id="ap1" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#8b949e"/></marker></defs>
</svg>

Generated source triggers an automatic follow-up round — the compiler keeps processing until nothing new is generated.

## 5. Runnable example

Scenario: a custom `@Loggable` annotation marking methods that should be tracked — the same processor, evolved from simply detecting and logging annotated methods, through enforcing a compile-time validation rule, to generating an entirely new source file at compile time that lists every annotated method, compiled and run within the same process.

### Level 1 — Basic

```java
import javax.tools.*;
import javax.annotation.processing.*;
import javax.lang.model.SourceVersion;
import javax.lang.model.element.*;
import java.net.URI;
import java.util.*;

public class AnnotationProcessingBasic {

    static class InMemorySource extends SimpleJavaFileObject {
        final String code;
        InMemorySource(String className, String code) {
            super(URI.create("string:///" + className + Kind.SOURCE.extension), Kind.SOURCE);
            this.code = code;
        }
        @Override public CharSequence getCharContent(boolean ignoreEncodingErrors) { return code; }
    }

    @SupportedAnnotationTypes("Loggable")
    static class LoggingProcessor extends AbstractProcessor {
        @Override public SourceVersion getSupportedSourceVersion() { return SourceVersion.latestSupported(); }
        @Override
        public boolean process(Set<? extends TypeElement> annotations, RoundEnvironment roundEnv) {
            for (TypeElement annotation : annotations) {
                for (Element element : roundEnv.getElementsAnnotatedWith(annotation)) {
                    System.out.println("Found @Loggable on: " + element.getSimpleName());
                }
            }
            return true;
        }
    }

    public static void main(String[] args) throws Exception {
        String source =
            "@interface Loggable {}\n" +
            "public class Service {\n" +
            "    @Loggable public void doWork() {}\n" +
            "    @Loggable public void doOther() {}\n" +
            "    public void notAnnotated() {}\n" +
            "}\n";

        JavaCompiler compiler = ToolProvider.getSystemJavaCompiler();
        StandardJavaFileManager fileManager = compiler.getStandardFileManager(null, null, null);

        JavaCompiler.CompilationTask task = compiler.getTask(
            null, fileManager, null, null, null,
            List.of(new InMemorySource("Service", source)));

        task.setProcessors(List.of(new LoggingProcessor())); // attach our custom processor to this compilation
        boolean success = task.call();
        System.out.println("Compilation success: " + success);
    }
}
```

**How to run:** `java AnnotationProcessingBasic.java`

`task.setProcessors(...)` attaches `LoggingProcessor` to this specific compilation; during compilation, `process()` is invoked with a model of every element annotated `@Loggable` — `doWork` and `doOther` are found and logged, while `notAnnotated` (correctly) is not, since annotation processing works on the compiler's semantic model, not runtime reflection.

### Level 2 — Intermediate

```java
import javax.tools.*;
import javax.annotation.processing.*;
import javax.lang.model.SourceVersion;
import javax.lang.model.element.*;
import javax.lang.model.type.TypeKind;
import java.net.URI;
import java.util.*;

public class AnnotationProcessingValidating {

    static class InMemorySource extends SimpleJavaFileObject {
        final String code;
        InMemorySource(String className, String code) {
            super(URI.create("string:///" + className + Kind.SOURCE.extension), Kind.SOURCE);
            this.code = code;
        }
        @Override public CharSequence getCharContent(boolean ignoreEncodingErrors) { return code; }
    }

    @SupportedAnnotationTypes("Loggable")
    static class LoggingProcessor extends AbstractProcessor {
        @Override public SourceVersion getSupportedSourceVersion() { return SourceVersion.latestSupported(); }
        @Override
        public boolean process(Set<? extends TypeElement> annotations, RoundEnvironment roundEnv) {
            for (TypeElement annotation : annotations) {
                for (Element element : roundEnv.getElementsAnnotatedWith(annotation)) {
                    ExecutableElement method = (ExecutableElement) element;
                    if (method.getReturnType().getKind() != TypeKind.VOID) {
                        // A genuine compiler ERROR -- fails the whole build, just like a real javac diagnostic
                        processingEnv.getMessager().printMessage(Diagnostic.Kind.ERROR,
                            "@Loggable methods must return void", element);
                    } else {
                        System.out.println("Valid @Loggable method: " + element.getSimpleName());
                    }
                }
            }
            return true;
        }
    }

    static void compile(String className, String source) throws Exception {
        JavaCompiler compiler = ToolProvider.getSystemJavaCompiler();
        StandardJavaFileManager fileManager = compiler.getStandardFileManager(null, null, null);
        DiagnosticCollector<JavaFileObject> diagnostics = new DiagnosticCollector<>();

        JavaCompiler.CompilationTask task = compiler.getTask(
            null, fileManager, diagnostics, null, null,
            List.of(new InMemorySource(className, source)));
        task.setProcessors(List.of(new LoggingProcessor()));

        boolean success = task.call();
        System.out.println(className + " compiled: " + success);
        for (Diagnostic<? extends JavaFileObject> d : diagnostics.getDiagnostics()) {
            if (d.getKind() == Diagnostic.Kind.ERROR) {
                System.out.println("  ERROR: " + d.getMessage(null));
            }
        }
    }

    public static void main(String[] args) throws Exception {
        String goodSource =
            "@interface Loggable {}\n" +
            "public class GoodService {\n" +
            "    @Loggable public void doWork() {}\n" +
            "}\n";

        String badSource =
            "@interface Loggable {}\n" +
            "public class BadService {\n" +
            "    @Loggable public int doWork() { return 1; }\n" + // violates the void-return rule
            "}\n";

        compile("GoodService", goodSource);
        compile("BadService", badSource);
    }
}
```

**How to run:** `java AnnotationProcessingValidating.java`

`Messager.printMessage(Diagnostic.Kind.ERROR, ...)` doesn't just print a message — it marks the **entire compilation as failed**, exactly as a real syntax error would. `BadService`'s `@Loggable`-annotated method returns `int` instead of `void`, violating the rule this processor enforces, and its compilation correctly fails with the custom error message.

### Level 3 — Advanced

```java
import javax.tools.*;
import javax.annotation.processing.*;
import javax.lang.model.SourceVersion;
import javax.lang.model.element.*;
import java.io.*;
import java.net.*;
import java.util.*;

public class AnnotationProcessingCodeGen {

    static class InMemorySource extends SimpleJavaFileObject {
        final String code;
        InMemorySource(String className, String code) {
            super(URI.create("string:///" + className + Kind.SOURCE.extension), Kind.SOURCE);
            this.code = code;
        }
        @Override public CharSequence getCharContent(boolean ignoreEncodingErrors) { return code; }
    }

    static class InMemoryClassFile extends SimpleJavaFileObject {
        final ByteArrayOutputStream bytes = new ByteArrayOutputStream();
        InMemoryClassFile(String className) {
            super(URI.create("bytes:///" + className + Kind.CLASS.extension), Kind.CLASS);
        }
        @Override public OutputStream openOutputStream() { return bytes; }
        @Override public InputStream openInputStream() { return new ByteArrayInputStream(bytes.toByteArray()); }
        byte[] getBytes() { return bytes.toByteArray(); }
    }

    // Filer.createSourceFile() needs a SOURCE-kind object -- javac reads generated source back as TEXT
    // (getCharContent), not as raw class bytes, so this must be a distinct type from InMemoryClassFile.
    static class InMemoryGeneratedSource extends SimpleJavaFileObject {
        final StringWriter text = new StringWriter();
        InMemoryGeneratedSource(String className) {
            super(URI.create("string:///" + className + Kind.SOURCE.extension), Kind.SOURCE);
        }
        @Override public Writer openWriter() { return text; }
        @Override public CharSequence getCharContent(boolean ignoreEncodingErrors) { return text.toString(); }
    }

    static class InMemoryFileManager extends ForwardingJavaFileManager<StandardJavaFileManager> {
        final Map<String, InMemoryClassFile> classFiles = new HashMap<>();
        InMemoryFileManager(StandardJavaFileManager fm) { super(fm); }
        @Override
        public JavaFileObject getJavaFileForOutput(Location location, String className,
                                                    JavaFileObject.Kind kind, FileObject sibling) {
            if (kind == JavaFileObject.Kind.SOURCE) {
                return new InMemoryGeneratedSource(className); // Filer-generated source, not compiled bytecode
            }
            InMemoryClassFile f = new InMemoryClassFile(className);
            classFiles.put(className, f);
            return f;
        }
    }

    static class InMemoryClassLoader extends ClassLoader {
        final Map<String, InMemoryClassFile> classFiles;
        InMemoryClassLoader(Map<String, InMemoryClassFile> classFiles) { this.classFiles = classFiles; }
        @Override
        protected Class<?> findClass(String name) throws ClassNotFoundException {
            InMemoryClassFile f = classFiles.get(name);
            if (f == null) throw new ClassNotFoundException(name);
            byte[] b = f.getBytes();
            return defineClass(name, b, 0, b.length);
        }
    }

    @SupportedAnnotationTypes("Loggable")
    static class CodeGenProcessor extends AbstractProcessor {
        @Override public SourceVersion getSupportedSourceVersion() { return SourceVersion.latestSupported(); }
        @Override
        public boolean process(Set<? extends TypeElement> annotations, RoundEnvironment roundEnv) {
            if (roundEnv.processingOver()) return false; // don't regenerate on the follow-up round

            List<String> methodNames = new ArrayList<>();
            for (TypeElement annotation : annotations) {
                for (Element element : roundEnv.getElementsAnnotatedWith(annotation)) {
                    methodNames.add(element.getSimpleName().toString());
                }
            }
            if (methodNames.isEmpty()) return true;

            try {
                // Generate a brand-new source file at COMPILE TIME, listing every @Loggable method found
                JavaFileObject generated = processingEnv.getFiler().createSourceFile("ServiceRegistry");
                try (Writer writer = generated.openWriter()) {
                    writer.write("public class ServiceRegistry {\n");
                    writer.write("    public static String describe() {\n");
                    writer.write("        return \"Logged methods: " + String.join(", ", methodNames) + "\";\n");
                    writer.write("    }\n");
                    writer.write("}\n");
                }
            } catch (IOException e) {
                throw new RuntimeException(e);
            }
            return true;
        }
    }

    public static void main(String[] args) throws Exception {
        String source =
            "@interface Loggable {}\n" +
            "public class Service {\n" +
            "    @Loggable public void doWork() {}\n" +
            "    @Loggable public void doOther() {}\n" +
            "}\n";

        JavaCompiler compiler = ToolProvider.getSystemJavaCompiler();
        InMemoryFileManager fileManager = new InMemoryFileManager(
            compiler.getStandardFileManager(null, null, null));

        JavaCompiler.CompilationTask task = compiler.getTask(
            null, fileManager, null, null, null,
            List.of(new InMemorySource("Service", source)));
        task.setProcessors(List.of(new CodeGenProcessor()));

        boolean success = task.call();
        System.out.println("Compilation (with code generation) success: " + success);

        InMemoryClassLoader loader = new InMemoryClassLoader(fileManager.classFiles);
        Class<?> registryClass = Class.forName("ServiceRegistry", true, loader);
        String description = (String) registryClass.getMethod("describe").invoke(null);
        System.out.println(description);
    }
}
```

**How to run:** `java AnnotationProcessingCodeGen.java`

`processingEnv.getFiler().createSourceFile("ServiceRegistry")` generates a brand-new `.java` source file *during compilation*, listing every `@Loggable` method found. The compiler automatically detects this new source and compiles it in an additional round — no separate build step, no manual re-invocation — and the resulting `ServiceRegistry` class is immediately loadable and runnable, right alongside the originally-compiled `Service` class.

## 6. Walkthrough

Execution starts in `main` of the Level 3 example. The `source` string defines `@interface Loggable` and a `Service` class with two `@Loggable`-annotated methods. `task.setProcessors(List.of(new CodeGenProcessor()))` attaches the processor; `task.call()` begins compilation.

**Round 1:** the compiler parses `Service` and detects `@Loggable` on `doWork` and `doOther`. It invokes `CodeGenProcessor.process(...)`. Since `roundEnv.processingOver()` is `false` in this first round, execution proceeds: `methodNames` collects `["doWork", "doOther"]` by iterating `roundEnv.getElementsAnnotatedWith(annotation)`. Since this list isn't empty, `processingEnv.getFiler().createSourceFile("ServiceRegistry")` is called, requesting a new source file from the file manager — this routes through `InMemoryFileManager.getJavaFileForOutput`, which sees `kind == SOURCE` and returns a fresh `InMemoryGeneratedSource`. The processor writes a complete `ServiceRegistry` class definition into it via `openWriter()`, embedding the joined method names directly into a `describe()` method's return statement.

**Round 2:** because a new source file was generated, the compiler automatically schedules another processing round, this time compiling **both** `Service` (already compiled in round 1) and the newly generated `ServiceRegistry` source together. `CodeGenProcessor.process(...)` is invoked again for this round — but this time `roundEnv.processingOver()` is checked at the top: on this final round (no more new files generated), it returns `true`, so the method immediately returns `false` without trying to generate `ServiceRegistry` a second time (which would otherwise cause a duplicate-class error). `ServiceRegistry`'s actual bytecode is produced by the compiler's normal compilation of the generated source (not by the processor itself) and captured via `InMemoryFileManager.getJavaFileForOutput` with `kind == CLASS` this time, landing in `fileManager.classFiles`.

Back in `main`, `task.call()` returns `true` (`success`). `InMemoryClassLoader` is built from `fileManager.classFiles` (which now contains both `Service` and `ServiceRegistry`'s compiled bytecode). `Class.forName("ServiceRegistry", true, loader)` loads the generated class, and `registryClass.getMethod("describe").invoke(null)` calls its static method, returning the string that was embedded at compile time from the annotation-processing pass.

Expected output:
```
Compilation (with code generation) success: true
Logged methods: doWork, doOther
```

## 7. Gotchas & takeaways

> Single-file source-launch (`java MyFile.java`) explicitly **disables annotation processing** on the file being launched directly (per JEP 330) — a processor you register on your own build won't run against code executed this way. This is precisely why the runnable examples above drive a *nested*, in-process compilation via the Compiler API instead: that inner compilation is a full, ordinary `javac` invocation where annotation processing works normally.

- A processor implements `process(Set<? extends TypeElement>, RoundEnvironment)`, examining a compile-time **model** of annotated elements (`Element`, `TypeElement`, `ExecutableElement`) — not runtime reflection objects.
- `Messager.printMessage(Diagnostic.Kind.ERROR, ...)` fails the entire compilation with a custom message, letting a processor enforce project-specific rules as genuine build errors.
- `Filer.createSourceFile(...)` generates new source files at compile time; the compiler automatically schedules an additional round to compile anything newly generated, repeating until a round produces nothing new.
- Always check `roundEnv.processingOver()` before generating files, to avoid regenerating (and duplicate-defining) the same source on the final, no-op round.
- This exact mechanism (detect annotations, validate or generate code, let the compiler pick up generated sources automatically) is what powers real-world tools like Lombok, Dagger, and MapStruct.

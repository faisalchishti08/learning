# Java Annotations

## Overview

Annotations are metadata markers on code elements. They don't change behavior directly — they're signals for the compiler, tools, or runtime processors. Java provides built-in annotations, and you can define custom ones.

---

## 1. Built-in Annotations

### Visual Diagram — Annotation Targets

```
@Target applies to:
  ElementType.TYPE              class, interface, enum, record, annotation
  ElementType.FIELD             field (includes enum constants)
  ElementType.METHOD            method
  ElementType.PARAMETER         method parameter
  ElementType.CONSTRUCTOR       constructor
  ElementType.LOCAL_VARIABLE    local variable
  ElementType.ANNOTATION_TYPE   another annotation (meta-annotation)
  ElementType.PACKAGE           package-info.java
  ElementType.TYPE_PARAMETER    <T> in generic declaration [Java 8+]
  ElementType.TYPE_USE          any type use [Java 8+]
  ElementType.RECORD_COMPONENT  record component [Java 16+]

@Retention controls when annotation is visible:
  RetentionPolicy.SOURCE   compiler only (discarded after compile: @Override, @SuppressWarnings)
  RetentionPolicy.CLASS    in bytecode, not at runtime (default)
  RetentionPolicy.RUNTIME  in bytecode AND accessible via reflection
```

### Example 1 — Built-in Java Annotations

```java
import java.util.*;

public class BuiltInAnnotations {
    // @Override — compiler checks this actually overrides a method
    static class Animal {
        public String speak() { return "..."; }
    }

    static class Dog extends Animal {
        @Override
        public String speak() { return "Woof"; } // compiler error if misspelled

        // @Deprecated — marks method as obsolete
        @Deprecated(since = "2.0", forRemoval = true) // [Java 9+] forRemoval
        public void oldMethod() {}
    }

    // @SuppressWarnings — suppress specific compiler warnings
    @SuppressWarnings("unchecked")
    static void rawTypeExample() {
        List list = new ArrayList(); // raw type — suppressed
        list.add("hello");
    }

    // @FunctionalInterface — compiler enforces exactly one abstract method
    @FunctionalInterface
    interface Transformer<T, R> {
        R transform(T input);
        // default methods OK
        default Transformer<T, R> logged() {
            return input -> {
                R result = this.transform(input);
                System.out.println(input + " → " + result);
                return result;
            };
        }
    }

    // @SafeVarargs — suppresses heap pollution warning for varargs generics
    @SafeVarargs
    static <T> List<T> listOf(T... items) {
        return Arrays.asList(items);
    }

    public static void main(String[] args) {
        Transformer<String, Integer> len = String::length;
        System.out.println(len.transform("hello")); // 5

        Dog d = new Dog();
        d.oldMethod(); // IDE/compiler shows deprecation warning
    }
}
```

**What this does:** `@Override` prevents typo bugs. `@Deprecated` marks obsolete APIs with optional migration info. `@SuppressWarnings` silences specific warning categories. All three are `RetentionPolicy.SOURCE` — erased after compile.

---

## 2. Defining Custom Annotations

### Example 1 — Annotation Syntax

```java
import java.lang.annotation.*;

// Meta-annotations define annotation behavior
@Retention(RetentionPolicy.RUNTIME)    // visible via reflection
@Target({ElementType.METHOD, ElementType.TYPE}) // where it can appear
@Documented                            // include in Javadoc
@Inherited                             // subclasses inherit this annotation on class
public @interface Audit {
    // Elements (like abstract methods in interface)
    String action();                   // required (no default)
    String user() default "system";    // optional with default
    boolean log() default true;
    String[] tags() default {};        // array element
    AuditLevel level() default AuditLevel.INFO; // enum element
    Class<?>[] classes() default {};   // class element

    enum AuditLevel { INFO, WARN, ERROR }
}
```

**What this does:** Annotation elements look like methods but aren't — they're like named parameters. Allowed element types: primitives, String, Class, enum, another annotation, and arrays of any of these.

### Example 2 — Using Custom Annotations

```java
import java.lang.annotation.*;
import java.lang.reflect.*;

public class CustomAnnotationDemo {
    @Retention(RetentionPolicy.RUNTIME)
    @Target(ElementType.METHOD)
    @interface Timed {
        String name() default "";
        long thresholdMs() default 100;
    }

    @Retention(RetentionPolicy.RUNTIME)
    @Target(ElementType.FIELD)
    @interface NotNull {
        String message() default "field must not be null";
    }

    static class UserService {
        @Timed(name = "findUser", thresholdMs = 50)
        public String findUser(int id) {
            return "User-" + id;
        }

        @Timed  // uses defaults
        public void deleteUser(int id) { }
    }

    static class User {
        @NotNull
        String name;

        @NotNull(message = "email is required")
        String email;

        String nickname; // nullable
    }

    // Annotation processor — runs at runtime
    static void validateFields(Object obj) throws Exception {
        for (Field f : obj.getClass().getDeclaredFields()) {
            if (f.isAnnotationPresent(NotNull.class)) {
                f.setAccessible(true);
                if (f.get(obj) == null) {
                    NotNull ann = f.getAnnotation(NotNull.class);
                    throw new IllegalStateException(f.getName() + ": " + ann.message());
                }
            }
        }
        System.out.println("Validation passed");
    }

    public static void main(String[] args) throws Exception {
        // Check method annotations
        for (Method m : UserService.class.getDeclaredMethods()) {
            if (m.isAnnotationPresent(Timed.class)) {
                Timed t = m.getAnnotation(Timed.class);
                System.out.printf("Method: %s, threshold=%dms, name=%s%n",
                    m.getName(), t.thresholdMs(), t.name().isEmpty() ? m.getName() : t.name());
            }
        }

        // Validate fields
        User valid = new User();
        valid.name = "Alice"; valid.email = "alice@example.com";
        validateFields(valid); // Validation passed

        User invalid = new User();
        invalid.name = "Bob"; // email = null
        try {
            validateFields(invalid);
        } catch (IllegalStateException e) {
            System.out.println("Error: " + e.getMessage()); // email: email is required
        }
    }
}
```

**What this does:** This is how Bean Validation (JSR 380 / Hibernate Validator) works — scan fields for constraint annotations at runtime and validate. The annotation is just metadata; the processing logic is separate.

---

## 3. Repeatable Annotations [Java 8+]

### Example 1

```java
import java.lang.annotation.*;

public class RepeatableAnnotations {
    @Retention(RetentionPolicy.RUNTIME)
    @Target(ElementType.METHOD)
    @Repeatable(Roles.class) // container annotation
    @interface Role {
        String value();
    }

    @Retention(RetentionPolicy.RUNTIME)
    @Target(ElementType.METHOD)
    @interface Roles {
        Role[] value(); // container must have value() of array of the repeatable
    }

    static class ApiController {
        @Role("ADMIN")
        @Role("MANAGER")   // repeatable — Java 8+ syntax
        @Role("SUPPORT")
        public void adminEndpoint() {}
    }

    public static void main(String[] args) throws Exception {
        var method = ApiController.class.getMethod("adminEndpoint");

        // getAnnotationsByType handles the container transparently
        Role[] roles = method.getAnnotationsByType(Role.class);
        for (Role r : roles) {
            System.out.println("Required role: " + r.value());
        }
        // Required role: ADMIN
        // Required role: MANAGER
        // Required role: SUPPORT
    }
}
```

**What this does:** `@Repeatable` allows the same annotation to appear multiple times on the same element. The compiler wraps them in the container annotation. `getAnnotationsByType()` unwraps transparently.

---

## 4. Annotation Processing (compile-time)

### What is it

`javax.annotation.processing` allows annotations to generate code/files at compile time. Used by: Lombok (`@Data`, `@Builder`), Dagger (DI), MapStruct, AutoValue, Immutables.

### Visual Diagram

```
Source code with annotations
         │
         ▼
   javac compiler
         │
         ▼
  Annotation Processor  ← runs during compilation
  (AbstractProcessor)
         │
         ▼
  Generated source files → compiled alongside original
         │
         ▼
  Final bytecode (original + generated)

Example: @Data in Lombok
  Input:  class Person { @Data private String name; private int age; }
  Output: generates getters, setters, toString, equals, hashCode source
          at compile time — no runtime overhead
```

### Example 1 — Simple Annotation Processor Structure

```java
import javax.annotation.processing.*;
import javax.lang.model.SourceVersion;
import javax.lang.model.element.*;
import java.util.Set;

// This is a compile-time processor — runs during javac
@SupportedAnnotationTypes("com.example.GenerateToString")
@SupportedSourceVersion(SourceVersion.RELEASE_21)
public class ToStringProcessor extends AbstractProcessor {
    @Override
    public boolean process(Set<? extends TypeElement> annotations,
                           RoundEnvironment roundEnv) {
        for (TypeElement annotation : annotations) {
            for (Element element : roundEnv.getElementsAnnotatedWith(annotation)) {
                // element is the annotated class
                // generate code: write to processingEnv.getFiler()
                System.out.println("Processing: " + element.getSimpleName());
            }
        }
        return true; // annotation claimed, don't pass to other processors
    }
}
```

**What this does:** Compile-time processing generates boilerplate at build time — zero runtime reflection cost. The processor is registered in `META-INF/services/javax.annotation.processing.Processor` and invoked automatically by `javac`.

---

## 5. Common Framework Annotations

### Example 1 — Spring-style Annotations (conceptual)

```java
import java.lang.annotation.*;

// What Spring's @Component means (simplified)
@Retention(RetentionPolicy.RUNTIME)
@Target(ElementType.TYPE)
@interface Component {
    String value() default ""; // bean name
}

@Retention(RetentionPolicy.RUNTIME)
@Target({ElementType.FIELD, ElementType.CONSTRUCTOR, ElementType.METHOD})
@interface Inject {} // like @Autowired

@Retention(RetentionPolicy.RUNTIME)
@Target(ElementType.METHOD)
@interface Transactional {
    boolean readOnly() default false;
    Class<?>[] rollbackFor() default {};
}

// How a DI container discovers beans
public class DIScanner {
    static void scan(String packageName) throws Exception {
        // In reality: scan classpath for classes with @Component
        // Here: demonstrate the concept
        Class<?> cls = Class.forName("MyService");
        if (cls.isAnnotationPresent(Component.class)) {
            Component comp = cls.getAnnotation(Component.class);
            String beanName = comp.value().isEmpty() ?
                cls.getSimpleName().substring(0, 1).toLowerCase() +
                cls.getSimpleName().substring(1) : comp.value();
            System.out.println("Register bean: " + beanName);
        }
    }
}
```

**What this does:** Frameworks like Spring use annotation metadata to automate wiring, transactions, and AOP. The annotation is just a marker; the framework's code reads it and acts accordingly.

---

## 6. Type Annotations [Java 8+]

### Example 1

```java
import java.lang.annotation.*;
import java.util.*;

public class TypeAnnotations {
    @Retention(RetentionPolicy.RUNTIME)
    @Target(ElementType.TYPE_USE) // applies to any use of a type
    @interface NonNull {}

    @Retention(RetentionPolicy.RUNTIME)
    @Target(ElementType.TYPE_USE)
    @interface Positive {}

    // Type annotations can appear anywhere a type is used
    static @NonNull String process(@NonNull String input) {
        return input.trim();
    }

    static List<@NonNull String> getNames() {
        return List.of("Alice", "Bob");
    }

    // Checked at runtime by null-checking tools (Checker Framework, NullAway)
    public static void main(String[] args) {
        @NonNull String result = process("  hello  ");
        System.out.println(result); // hello

        // Map<@NonNull String, @Positive Integer>
        Map<@NonNull String, @Positive Integer> scores = new HashMap<>();
        scores.put("Alice", 95);
    }
}
```

**What this does:** Type-use annotations appear anywhere a type appears — method parameters, return types, generics, local variables. Tools like NullAway use `@NonNull` to find potential NPEs at compile time.

---

## Quick Reference

```
Meta-annotations:
  @Retention(SOURCE|CLASS|RUNTIME)   when annotation is visible
  @Target(ElementType...)            where annotation can appear
  @Documented                        include in Javadoc
  @Inherited                         subclasses inherit (on TYPE only)
  @Repeatable(ContainerType.class)   allow multiple occurrences [Java 8+]

Built-in annotations:
  @Override                          check at compile time
  @Deprecated(since, forRemoval)     mark obsolete
  @SuppressWarnings("unchecked")     suppress warnings
  @FunctionalInterface               enforce single abstract method
  @SafeVarargs                       suppress heap pollution warning

Custom annotation declaration:
  @interface MyAnn { String value() default ""; }
  Allowed element types: primitives, String, Class, enum, annotation, arrays

Reflection access:
  element.isAnnotationPresent(Ann.class)
  element.getAnnotation(Ann.class)
  element.getAnnotationsByType(Ann.class)  handles @Repeatable

Processing timing:
  @Retention(SOURCE):  compile-time only (Lombok-style processing)
  @Retention(RUNTIME): runtime inspection (Spring, Hibernate, JUnit)
```

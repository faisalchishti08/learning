---
card: java
gi: 437
slug: try-with-resources
title: Try-with-resources
---

## 1. What it is

Try-with-resources, added in Java 7, is a `try` statement form that automatically closes one or more resources when the block exits — whether normally or due to an exception — without needing an explicit `finally` block. Any resource declared inside the parentheses, `try (Resource r = ...) { ... }`, must implement `AutoCloseable`; the compiler generates the equivalent of a `finally` block that calls `r.close()`, guaranteed to run no matter how the `try` block exits.

## 2. Why & when

Before Java 7, correctly releasing a resource (a file, a network connection, a lock) required manually writing a `finally` block, and doing it *correctly* was surprisingly fiddly: `close()` itself can throw, and if it does while the `try` block is already unwinding from an exception, naive code can accidentally lose the original exception by letting the one from `close()` replace it. Try-with-resources handles all of this correctly and automatically — you simply declare the resource in the `try(...)` parentheses and never write a manual `finally` block for closing it.

You reach for try-with-resources any time you're working with a resource that needs deterministic cleanup — file handles, database connections, network sockets, locks — which, in practice, is almost always when such a resource is involved. It's the default, idiomatic way to manage `AutoCloseable` resources in modern Java.

## 3. Core concept

```java
// Old style: verbose, and easy to get subtly wrong around exceptions from close()
FileHandle file = new FileHandle("data.txt");
try {
    file.write("...");
} finally {
    file.close(); // you must remember this, and handle it throwing too
}

// Try-with-resources: close() is called automatically, correctly, no matter how the block exits
try (FileHandle file = new FileHandle("data.txt")) {
    file.write("...");
} // file.close() runs here automatically
```

Multiple resources can be declared in one `try(...)`, separated by semicolons — they're closed automatically in the **reverse** of their declaration order, mirroring how you'd naturally want to release layered resources (innermost/last-acquired first).

## 4. Diagram

<svg viewBox="0 0 640 170" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Resources declared in a try-with-resources statement are opened in declaration order and closed automatically in the reverse order, whether the block exits normally or via an exception">
  <rect x="8" y="8" width="624" height="154" rx="8" fill="#0d1117"/>
  <text x="20" y="26" fill="#e6edf3" font-size="11" font-family="sans-serif">try (A a = ...; B b = ...) { ... }</text>

  <rect x="30" y="45" width="120" height="30" rx="4" fill="#1c2430" stroke="#6db33f"/><text x="90" y="65" fill="#6db33f" font-size="10" text-anchor="middle">1. open A</text>
  <rect x="170" y="45" width="120" height="30" rx="4" fill="#1c2430" stroke="#6db33f"/><text x="230" y="65" fill="#6db33f" font-size="10" text-anchor="middle">2. open B</text>
  <rect x="310" y="45" width="120" height="30" rx="4" fill="#1c2430" stroke="#79c0ff"/><text x="370" y="65" fill="#79c0ff" font-size="10" text-anchor="middle">3. run body</text>
  <rect x="450" y="45" width="120" height="30" rx="4" fill="#1c2430" stroke="#f85149"/><text x="510" y="65" fill="#f85149" font-size="10" text-anchor="middle">4. close B</text>
  <rect x="450" y="90" width="120" height="30" rx="4" fill="#1c2430" stroke="#f85149"/><text x="510" y="110" fill="#f85149" font-size="10" text-anchor="middle">5. close A</text>

  <text x="320" y="140" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">Close order is the REVERSE of open order -- B (opened last) closes first.</text>
</svg>

Resources close in the reverse of their opening order, exactly like unwinding a stack.

## 5. Runnable example

Scenario: a simple pair of file-like resources copying data between them — the same resource handling, evolved from a single auto-closed resource, through multiple resources closing in reverse order, to correctly handling a resource that fails to open partway through acquiring several of them.

### Level 1 — Basic

```java
public class ResourceBasic {
    static class FileHandle implements AutoCloseable {
        private final String name;
        FileHandle(String name) {
            this.name = name;
            System.out.println("Opened " + name);
        }
        void write(String data) {
            System.out.println(name + " <- " + data);
        }
        @Override
        public void close() {
            System.out.println("Closed " + name);
        }
    }

    public static void main(String[] args) {
        try (FileHandle file = new FileHandle("report.txt")) {
            file.write("Hello, World!");
        } // file.close() is called automatically here, even without a finally block
        System.out.println("Done.");
    }
}
```

**How to run:** `java ResourceBasic.java`

`file.close()` runs automatically the moment the `try` block finishes — no explicit `finally` block was written, yet `"Closed report.txt"` still prints reliably before `"Done."`.

### Level 2 — Intermediate

```java
public class ResourceMultiple {
    static class FileHandle implements AutoCloseable {
        private final String name;
        FileHandle(String name) {
            this.name = name;
            System.out.println("Opened " + name);
        }
        void write(String data) {
            System.out.println(name + " <- " + data);
        }
        @Override
        public void close() {
            System.out.println("Closed " + name);
        }
    }

    public static void main(String[] args) {
        try (FileHandle input = new FileHandle("input.txt");
             FileHandle output = new FileHandle("output.txt")) {
            output.write("copied from " + "input.txt");
        } // closed in REVERSE order: output first, then input
        System.out.println("Done.");
    }
}
```

**How to run:** `java ResourceMultiple.java`

Both `input` and `output` are opened in declaration order, but closed in the **reverse** order — `output` (opened second) closes first, then `input` — mirroring how layered resources naturally need to be released.

### Level 3 — Advanced

```java
public class ResourceAcquisitionFailure {
    static class FileHandle implements AutoCloseable {
        private final String name;
        FileHandle(String name, boolean failToOpen) {
            if (failToOpen) {
                throw new RuntimeException("Failed to open " + name);
            }
            this.name = name;
            System.out.println("Opened " + name);
        }
        void write(String data) {
            System.out.println(name + " <- " + data);
        }
        @Override
        public void close() {
            System.out.println("Closed " + name);
        }
    }

    public static void main(String[] args) {
        try (FileHandle input = new FileHandle("input.txt", false);
             FileHandle output = new FileHandle("output.txt", true)) { // this one fails to construct
            output.write("never reached");
        } catch (RuntimeException e) {
            System.out.println("Caught: " + e.getMessage());
        }
        System.out.println("Done.");
    }
}
```

**How to run:** `java ResourceAcquisitionFailure.java`

`output`'s constructor throws **before** it's fully constructed — but `input`, which *did* open successfully just before, is still correctly closed. Try-with-resources tracks each resource as it's successfully acquired and guarantees all of them are closed, even if a later resource in the same `try(...)` list fails to open.

## 6. Walkthrough

Execution starts in `main` of the Level 3 example. The `try (...)` statement begins acquiring its resources in declaration order. `new FileHandle("input.txt", false)` runs first: `failToOpen` is `false`, so the constructor completes normally, printing `"Opened input.txt"`, and `input` is now a fully-constructed, tracked resource.

Next, `new FileHandle("output.txt", true)` runs: `failToOpen` is `true`, so the constructor throws `RuntimeException("Failed to open output.txt")` **before** returning — `output` is never successfully constructed, and the `try` block's body (`output.write("never reached")`) never executes at all, since the resource-acquisition phase itself failed.

Because `input` had already been successfully acquired before the failure, the try-with-resources machinery still calls `input.close()` as it unwinds — printing `"Closed input.txt"` — even though the overall `try` statement is failing. This is the key guarantee: **every resource that was successfully opened gets closed**, regardless of what happens to resources declared after it.

The `RuntimeException` from `output`'s failed construction then propagates to the `catch (RuntimeException e)` block, which prints `"Caught: Failed to open output.txt"`. Execution continues normally after the `try`/`catch`, printing `"Done."`.

Expected output:
```
Opened input.txt
Closed input.txt
Caught: Failed to open output.txt
Done.
```

## 7. Gotchas & takeaways

> If a resource's constructor throws partway through acquiring **multiple** resources, only the ones that were **already successfully constructed** get closed — the failing one itself is never added to the list of things to close, since it never finished being created. This is exactly why `input` closes but there's no corresponding "Closed output.txt" line in the example above: `output` never became a real, trackable resource in the first place.

- Any resource declared inside `try(...)` must implement `AutoCloseable`; its `close()` method is called automatically when the block exits, whether normally or via an exception.
- Multiple resources in one `try(...)`, separated by semicolons, are closed in the **reverse** of their declaration order.
- Resources that were successfully constructed are still closed even if a *later* resource in the same `try(...)` list fails to construct — cleanup applies per-resource, not all-or-nothing.
- Try-with-resources eliminates the need for a manual `finally` block dedicated to closing resources, and correctly handles the tricky case of `close()` itself throwing (covered in detail in the suppressed-exceptions tutorial).
- This is the idiomatic, default way to manage any `AutoCloseable` resource in modern Java — file handles, database connections, sockets, and locks should almost always be acquired inside a `try(...)`.

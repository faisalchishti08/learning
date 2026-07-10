---
card: java
gi: 992
slug: solid-interface-segregation
title: SOLID — Interface Segregation
---

## 1. What it is

The **Interface Segregation Principle (ISP)** says clients shouldn't be forced to depend on methods they don't use. In practice: prefer several small, focused interfaces over one large, "fat" interface that bundles unrelated capabilities together. If a class only needs to `print()`, it shouldn't have to implement `scan()` and `fax()` just because they all happened to live on one `MultiFunctionDevice` interface.

## 2. Why & when

A fat interface forces every implementer to deal with methods it has no meaningful behavior for — usually resulting in a method body that throws `UnsupportedOperationException` or silently does nothing, both of which are landmines for whoever calls that method later, trusting the interface's contract. ISP exists to keep interfaces aligned with what specific clients actually need, so implementing one never means faking support for capabilities you don't have.

Reach for ISP when you notice an interface growing methods that only some of its implementers actually use — a `Worker` interface with `work()` and `eat()` that a `RobotWorker` can't meaningfully implement `eat()` for is the classic sign. Split the interface along the lines of what different callers genuinely require. Don't over-split either — an interface with one method per interface, when the methods always travel together, adds ceremony without real benefit.

## 3. Core concept

```
// Violates ISP: RobotWorker is forced to implement eat(), which makes no sense for it
interface Worker {
    void work();
    void eat();
}
class RobotWorker implements Worker {
    public void work() { System.out.println("welding"); }
    public void eat() { throw new UnsupportedOperationException("robots don't eat"); }
}

// Follows ISP: split into focused interfaces; implement only what applies
interface Workable { void work(); }
interface Eatable { void eat(); }
class RobotWorker implements Workable {
    public void work() { System.out.println("welding"); }
}
class HumanWorker implements Workable, Eatable {
    public void work() { System.out.println("coding"); }
    public void eat() { System.out.println("lunch break"); }
}
```

## 4. Diagram

<svg viewBox="0 0 640 200" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="A fat Worker interface forcing RobotWorker to implement eat versus split Workable and Eatable interfaces implemented only where they apply">
  <text x="150" y="24" fill="#8b949e" font-size="12" text-anchor="middle" font-family="sans-serif">Before: fat interface</text>
  <rect x="40" y="40" width="220" height="50" rx="8" fill="#1c2430" stroke="#f0883e" stroke-width="1.5"/>
  <text x="150" y="60" fill="#e6edf3" font-size="11" text-anchor="middle" font-family="sans-serif">Worker: work(), eat()</text>
  <text x="150" y="78" fill="#f0883e" font-size="9" text-anchor="middle" font-family="sans-serif">RobotWorker forced to fake eat()</text>

  <text x="490" y="24" fill="#8b949e" font-size="12" text-anchor="middle" font-family="sans-serif">After: segregated</text>
  <rect x="380" y="40" width="110" height="34" rx="6" fill="#1c2430" stroke="#6db33f"/>
  <text x="435" y="61" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">Workable</text>
  <rect x="500" y="40" width="110" height="34" rx="6" fill="#1c2430" stroke="#79c0ff"/>
  <text x="555" y="61" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">Eatable</text>

  <rect x="380" y="110" width="110" height="34" rx="6" fill="#1c2430" stroke="#8b949e"/>
  <text x="435" y="131" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">RobotWorker</text>
  <rect x="500" y="110" width="110" height="34" rx="6" fill="#1c2430" stroke="#8b949e"/>
  <text x="555" y="131" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">HumanWorker</text>

  <line x1="435" y1="74" x2="435" y2="110" stroke="#6db33f" marker-end="url(#a)"/>
  <line x1="490" y1="60" x2="555" y2="110" stroke="#79c0ff" marker-end="url(#a)"/>
  <defs><marker id="a" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#8b949e"/></marker></defs>
</svg>

`RobotWorker` implements only `Workable`; `HumanWorker` implements both — neither is forced into a method it can't honor.

## 5. Runnable example

Scenario: a printer/scanner device abstraction for an office system, evolving from one fat interface into interfaces segregated by what each device genuinely supports.

### Level 1 — Basic

```java
// File: IspBasic.java
interface MultiFunctionDevice {
    void print(String doc);
    void scan(String doc);
    void fax(String doc);
}

class BasicPrinter implements MultiFunctionDevice {
    public void print(String doc) { System.out.println("printing: " + doc); }
    public void scan(String doc) { throw new UnsupportedOperationException("no scanner hardware"); }
    public void fax(String doc) { throw new UnsupportedOperationException("no fax hardware"); }
}

public class IspBasic {
    public static void main(String[] args) {
        BasicPrinter printer = new BasicPrinter();
        printer.print("report.pdf");
        printer.scan("report.pdf"); // blows up at runtime
    }
}
```

**How to run:** save as `IspBasic.java`, then `javac IspBasic.java && java IspBasic` (JDK 17+).

Expected output:
```
printing: report.pdf
Exception in thread "main" java.lang.UnsupportedOperationException: no scanner hardware
	at BasicPrinter.scan(IspBasic.java:9)
	at IspBasic.main(IspBasic.java:16)
```

`BasicPrinter` is forced to implement `scan` and `fax` even though it has no such hardware — the interface promises capabilities this class can't deliver, and any caller trusting `MultiFunctionDevice`'s contract can be surprised by a runtime exception.

### Level 2 — Intermediate

```java
// File: IspIntermediate.java
interface Printable { void print(String doc); }
interface Scannable { void scan(String doc); }
interface Faxable { void fax(String doc); }

class BasicPrinter implements Printable {
    public void print(String doc) { System.out.println("printing: " + doc); }
}

class AllInOnePrinter implements Printable, Scannable, Faxable {
    public void print(String doc) { System.out.println("printing: " + doc); }
    public void scan(String doc) { System.out.println("scanning: " + doc); }
    public void fax(String doc) { System.out.println("faxing: " + doc); }
}

public class IspIntermediate {
    static void printDocument(Printable device, String doc) {
        device.print(doc);
    }

    public static void main(String[] args) {
        printDocument(new BasicPrinter(), "report.pdf");
        printDocument(new AllInOnePrinter(), "invoice.pdf");
    }
}
```

**How to run:** save as `IspIntermediate.java`, then `javac IspIntermediate.java && java IspIntermediate` (JDK 17+).

Expected output:
```
printing: report.pdf
printing: invoice.pdf
```

The real-world concern added: `BasicPrinter` only implements `Printable` — no fake `scan`/`fax` methods at all. `printDocument` depends only on `Printable`, so it works for both device types without caring whether they support scanning or faxing.

### Level 3 — Advanced

```java
// File: IspAdvanced.java
import java.util.List;
import java.util.Optional;

interface Printable { void print(String doc); }
interface Scannable { void scan(String doc); }

class BasicPrinter implements Printable {
    public void print(String doc) { System.out.println("printing: " + doc); }
}

class AllInOnePrinter implements Printable, Scannable {
    public void print(String doc) { System.out.println("printing: " + doc); }
    public void scan(String doc) { System.out.println("scanning: " + doc); }
}

// Office workflow that tries to use whatever capability a device actually has,
// using instanceof pattern matching instead of assuming every device is an
// AllInOnePrinter -- each device only needs to advertise the interfaces it supports.
class OfficeWorkflow {
    static void processIncoming(Object device, String doc) {
        if (device instanceof Printable p) {
            p.print(doc);
        }
        if (device instanceof Scannable s) {
            s.scan(doc);
        } else {
            System.out.println("(no scan capability for " + doc + ", skipping)");
        }
    }
}

public class IspAdvanced {
    public static void main(String[] args) {
        List<Object> devices = List.of(new BasicPrinter(), new AllInOnePrinter());
        for (Object device : devices) {
            OfficeWorkflow.processIncoming(device, "contract.pdf");
        }
    }
}
```

**How to run:** save as `IspAdvanced.java`, then `javac IspAdvanced.java && java IspAdvanced` (JDK 17+).

Expected output:
```
printing: contract.pdf
(no scan capability for contract.pdf, skipping)
printing: contract.pdf
scanning: contract.pdf
```

The production-flavored hard case: `OfficeWorkflow` handles a mixed fleet of devices — some print-only, some print-and-scan — by checking which segregated interface each device actually implements, rather than requiring every device to implement a fat interface (and fake the parts it doesn't support).

## 6. Walkthrough

Tracing the loop in `IspAdvanced.main`:

1. `devices` holds a `BasicPrinter` and an `AllInOnePrinter`, both typed as plain `Object` — the list doesn't commit to any particular capability set up front.
2. First iteration: `device` is the `BasicPrinter`. `OfficeWorkflow.processIncoming` checks `device instanceof Printable p` — true, since `BasicPrinter implements Printable` — so `p.print("contract.pdf")` runs, printing `"printing: contract.pdf"`.
3. The next check, `device instanceof Scannable s`, is false for `BasicPrinter` (it never implemented `Scannable`), so the `else` branch runs, printing the skip message.
4. Second iteration: `device` is the `AllInOnePrinter`. Both checks succeed this time — `p.print` prints `"printing: contract.pdf"`, then `s.scan` prints `"scanning: contract.pdf"`.
5. No exception is ever thrown and no device had to implement a method it doesn't support — the workflow adapts to each device's actual, advertised capabilities via the segregated interfaces `Printable` and `Scannable`.

## 7. Gotchas & takeaways

> **Gotcha:** the usual telltale sign of an ISP violation in existing code is a method body that's empty, returns a dummy value, or throws `UnsupportedOperationException` — that's a class being forced to "implement" something it fundamentally can't do, because the interface bundled unrelated responsibilities together.

- ISP: prefer several small, focused interfaces over one large interface that forces every implementer to support everything.
- The sign of a violation: an empty method body, a dummy return, or an `UnsupportedOperationException` inside an interface implementation.
- Segregated interfaces let calling code depend on only the capability it actually needs (`Printable`), rather than depending on — and inadvertently requiring — a device to support everything (`MultiFunctionDevice`).
- `instanceof` pattern checks against small interfaces let code adapt gracefully to a mixed set of implementers with different capability sets.
- Don't over-segregate either — if two methods are always implemented together by every class that ever needs either one, keeping them on the same interface is simpler than splitting for its own sake.
- ISP is closely related to [SOLID — Liskov Substitution](0991-solid-liskov-substitution.md): an implementer forced to fake a method it can't honor is also, subtly, breaking substitutability for that interface.

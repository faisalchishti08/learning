---
card: java
gi: 989
slug: solid-single-responsibility
title: SOLID — Single Responsibility
---

## 1. What it is

The **Single Responsibility Principle (SRP)** is the first letter of SOLID. It says a class should have **one reason to change** — one job, one responsibility, one axis along which requirements can shift. If a class handles two unrelated concerns (say, calculating an invoice *and* formatting it as HTML), a change to either concern forces you to touch the same class, and a bug fix in one concern risks breaking the other.

"Responsibility" here doesn't mean "one method." A class can have many methods and still have a single responsibility, as long as they all serve the same purpose and change for the same reason.

## 2. Why & when

Classes that mix responsibilities become fragile: a request to change how an invoice is *taxed* and a request to change how it's *printed* both land in the same file, by different teams, at different times, and now merging those changes is a coordination problem instead of two independent, isolated edits. SRP exists to keep each axis of change isolated so:

- **Testing is focused** — a class that only calculates has no HTML to fake in its tests.
- **Reuse is possible** — the calculation logic can be reused by a PDF exporter without dragging along HTML-rendering code.
- **Changes are localized** — a currency-formatting tweak doesn't risk breaking tax math it never touched.

Apply SRP when a class's methods start falling into two clearly separate groups that depend on different collaborators (one group needs a `TaxRules` object, another needs an `HtmlWriter`) — that's the tell-tale sign of two responsibilities living in one place. Don't over-apply it to the point of creating a separate class per single method; a "responsibility" is a cohesive purpose, not a line count.

## 3. Core concept

```
// Violates SRP: one class, two reasons to change (tax rules AND HTML formatting)
class Invoice {
    double calculateTotal(double amount, double taxRate) { return amount * (1 + taxRate); }
    String toHtml(double total) { return "<p>Total: $" + total + "</p>"; }
}

// Follows SRP: each class has exactly one reason to change
class InvoiceCalculator {
    double calculateTotal(double amount, double taxRate) { return amount * (1 + taxRate); }
}
class InvoiceHtmlFormatter {
    String toHtml(double total) { return "<p>Total: $" + total + "</p>"; }
}
```

A change to tax law now only touches `InvoiceCalculator`. A change to the invoice's look only touches `InvoiceHtmlFormatter`. Neither change risks the other.

## 4. Diagram

<svg viewBox="0 0 640 220" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="One Invoice class mixing two responsibilities versus two classes each with a single responsibility">
  <text x="150" y="24" fill="#8b949e" font-size="12" text-anchor="middle" font-family="sans-serif">Before (mixed)</text>
  <rect x="40" y="40" width="220" height="90" rx="8" fill="#1c2430" stroke="#f0883e" stroke-width="1.5"/>
  <text x="150" y="65" fill="#e6edf3" font-size="13" text-anchor="middle" font-family="sans-serif">Invoice</text>
  <text x="150" y="86" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">calculateTotal()</text>
  <text x="150" y="104" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">toHtml()</text>
  <text x="150" y="122" fill="#f0883e" font-size="9" text-anchor="middle" font-family="sans-serif">2 reasons to change</text>

  <text x="490" y="24" fill="#8b949e" font-size="12" text-anchor="middle" font-family="sans-serif">After (SRP)</text>
  <rect x="360" y="40" width="130" height="70" rx="8" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="425" y="65" fill="#e6edf3" font-size="11" text-anchor="middle" font-family="sans-serif">InvoiceCalculator</text>
  <text x="425" y="85" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">calculateTotal()</text>

  <rect x="500" y="40" width="130" height="70" rx="8" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="565" y="65" fill="#e6edf3" font-size="11" text-anchor="middle" font-family="sans-serif">InvoiceHtmlFormatter</text>
  <text x="565" y="85" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">toHtml()</text>
</svg>

Splitting a class along its independent axes of change turns one fragile class into two stable ones.

## 5. Runnable example

Scenario: an invoice system that calculates a total and renders it, evolving from one tangled class into cleanly separated responsibilities that can each change independently.

### Level 1 — Basic

```java
// File: SrpBasic.java
class Invoice {
    double calculateTotal(double amount, double taxRate) {
        return amount * (1 + taxRate);
    }
    String toHtml(double total) {
        return "<p>Total: $" + total + "</p>";
    }
}

public class SrpBasic {
    public static void main(String[] args) {
        Invoice invoice = new Invoice();
        double total = invoice.calculateTotal(100.0, 0.08);
        System.out.println(invoice.toHtml(total));
    }
}
```

**How to run:** save as `SrpBasic.java`, then `javac SrpBasic.java && java SrpBasic` (JDK 17+).

Expected output:
```
<p>Total: $108.0</p>
```

This works, but `Invoice` already has two reasons to change: a tax-law update and an HTML-formatting update both touch this one class.

### Level 2 — Intermediate

```java
// File: SrpIntermediate.java
class InvoiceCalculator {
    double calculateTotal(double amount, double taxRate) {
        return amount * (1 + taxRate);
    }
}

class InvoiceHtmlFormatter {
    String toHtml(double total) {
        return "<p>Total: $" + total + "</p>";
    }
}

public class SrpIntermediate {
    public static void main(String[] args) {
        InvoiceCalculator calculator = new InvoiceCalculator();
        InvoiceHtmlFormatter formatter = new InvoiceHtmlFormatter();

        double total = calculator.calculateTotal(100.0, 0.08);
        System.out.println(formatter.toHtml(total));
    }
}
```

**How to run:** save as `SrpIntermediate.java`, then `javac SrpIntermediate.java && java SrpIntermediate` (JDK 17+).

Expected output:
```
<p>Total: $108.0</p>
```

The real-world concern added: splitting the class means a tax-rule change (a new `InvoiceCalculator` implementation) never risks breaking the HTML output, and vice versa — each class can be tested, changed, and deployed independently.

### Level 3 — Advanced

```java
// File: SrpAdvanced.java
interface TotalCalculator {
    double calculateTotal(double amount, double taxRate);
}

class StandardTotalCalculator implements TotalCalculator {
    public double calculateTotal(double amount, double taxRate) {
        return amount * (1 + taxRate);
    }
}

interface InvoiceFormatter {
    String format(double total);
}

class HtmlInvoiceFormatter implements InvoiceFormatter {
    public String format(double total) {
        return "<p>Total: $" + String.format("%.2f", total) + "</p>";
    }
}

class PlainTextInvoiceFormatter implements InvoiceFormatter {
    public String format(double total) {
        return "Total: $" + String.format("%.2f", total);
    }
}

// Orchestrator: depends on the two abstractions, not their concrete details.
// Adding a new output format never touches TotalCalculator; adding a new tax
// rule never touches any InvoiceFormatter implementation.
class InvoiceService {
    private final TotalCalculator calculator;
    private final InvoiceFormatter formatter;

    InvoiceService(TotalCalculator calculator, InvoiceFormatter formatter) {
        this.calculator = calculator;
        this.formatter = formatter;
    }

    String renderInvoice(double amount, double taxRate) {
        double total = calculator.calculateTotal(amount, taxRate);
        return formatter.format(total);
    }
}

public class SrpAdvanced {
    public static void main(String[] args) {
        InvoiceService htmlInvoice = new InvoiceService(new StandardTotalCalculator(), new HtmlInvoiceFormatter());
        InvoiceService textInvoice = new InvoiceService(new StandardTotalCalculator(), new PlainTextInvoiceFormatter());

        System.out.println(htmlInvoice.renderInvoice(100.0, 0.08));
        System.out.println(textInvoice.renderInvoice(100.0, 0.08));
    }
}
```

**How to run:** save as `SrpAdvanced.java`, then `javac SrpAdvanced.java && java SrpAdvanced` (JDK 17+).

Expected output:
```
<p>Total: $108.00</p>
Total: $108.00
```

The production-flavored hard case: introducing a second formatter (`PlainTextInvoiceFormatter`) required no change at all to `StandardTotalCalculator` or `InvoiceService` — proof that the two responsibilities (calculation and formatting) are genuinely independent. `InvoiceService` itself has a single responsibility too: coordinating the two, not calculating or formatting anything itself.

## 6. Walkthrough

Tracing `SrpAdvanced.main` end to end:

1. `new StandardTotalCalculator()` and `new HtmlInvoiceFormatter()` are constructed independently — neither knows the other exists.
2. `new InvoiceService(calculator, formatter)` wires them together. `InvoiceService`'s only responsibility is coordination: it holds references to a `TotalCalculator` and an `InvoiceFormatter` and delegates to each in turn.
3. `htmlInvoice.renderInvoice(100.0, 0.08)` calls `calculator.calculateTotal(100.0, 0.08)`, which computes `100.0 * 1.08 = 108.0` — pure tax math, no knowledge of how the result will be displayed.
4. That `108.0` is passed to `formatter.format(108.0)`, which returns `"<p>Total: $108.00</p>"` — pure formatting, no knowledge of how the number was derived.
5. `textInvoice.renderInvoice(100.0, 0.08)` repeats the same calculation (same `StandardTotalCalculator` instance's logic, called again) but hands the result to `PlainTextInvoiceFormatter` instead, producing `"Total: $108.00"`.
6. Both lines print, showing the same calculation feeding two independent output paths — the calculator was never duplicated or modified to support a second format.

## 7. Gotchas & takeaways

> **Gotcha:** SRP is easy to over-apply. Splitting every single method into its own class produces a maze of tiny classes with no cohesion, which is arguably worse than the original problem — the goal is one *reason to change* per class, not one *method* per class.

- SRP: a class should have one reason to change — one axis of responsibility, not necessarily one method.
- The tell-tale sign of an SRP violation is a class whose methods split into groups depending on different, unrelated collaborators.
- Splitting responsibilities makes each piece independently testable, reusable, and safe to change without risking the other.
- Don't confuse "one responsibility" with "one method" — cohesive, related methods can and should live together.
- SRP pairs naturally with [dependency inversion](0993-solid-dependency-inversion.md): once responsibilities are split into separate classes, those classes are usually wired together through interfaces rather than concrete references.

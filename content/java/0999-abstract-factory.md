---
card: java
gi: 999
slug: abstract-factory
title: Abstract Factory
---

## 1. What it is

The **Abstract Factory** pattern provides an interface for creating **families of related objects** without specifying their concrete classes. Where [Factory Method](0998-factory-method.md) creates one product, Abstract Factory creates a *coordinated set* of products that are meant to be used together — a UI toolkit that produces a `Button`, a `Checkbox`, and a `Scrollbar` that all match the same visual theme (dark or light), so you never accidentally end up with a dark-themed button next to a light-themed checkbox.

## 2. Why & when

When related objects must be created consistently as a set — every widget from the same "family" — letting caller code pick each one individually risks mismatches: nothing stops someone from constructing a `DarkButton` alongside a `LightCheckbox`. Abstract Factory exists to make an entire family the unit of choice: you pick *one factory* (dark or light), and every product it hands you is guaranteed to belong to that same family, because the factory itself is the only thing that knows which concrete classes to instantiate.

Reach for Abstract Factory when your code needs to create several different but related objects, and the *set* of concrete classes needs to vary together based on some context (a theme, a target platform, an environment) — never one product varying while the others don't. It's unnecessary machinery when there's only one product to create at a time; that's just [Factory Method](0998-factory-method.md).

## 3. Core concept

```
interface Button { void render(); }
interface Checkbox { void render(); }

class DarkButton implements Button { public void render() { System.out.println("[dark button]"); } }
class DarkCheckbox implements Checkbox { public void render() { System.out.println("[dark checkbox]"); } }
class LightButton implements Button { public void render() { System.out.println("[light button]"); } }
class LightCheckbox implements Checkbox { public void render() { System.out.println("[light checkbox]"); } }

// Abstract Factory: one call site produces a whole MATCHED family
interface UiFactory {
    Button createButton();
    Checkbox createCheckbox();
}
class DarkUiFactory implements UiFactory {
    public Button createButton() { return new DarkButton(); }
    public Checkbox createCheckbox() { return new DarkCheckbox(); }
}
class LightUiFactory implements UiFactory {
    public Button createButton() { return new LightButton(); }
    public Checkbox createCheckbox() { return new LightCheckbox(); }
}
```

## 4. Diagram

<svg viewBox="0 0 640 200" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Choosing DarkUiFactory or LightUiFactory and each producing a matched Button and Checkbox from the same family">
  <rect x="30" y="80" width="130" height="40" rx="6" fill="#1c2430" stroke="#8b949e"/>
  <text x="95" y="105" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">App code</text>

  <rect x="230" y="30" width="150" height="40" rx="6" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="305" y="55" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">DarkUiFactory</text>
  <rect x="230" y="130" width="150" height="40" rx="6" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="305" y="155" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">LightUiFactory</text>

  <rect x="460" y="10" width="150" height="30" rx="6" fill="#1c2430" stroke="#6db33f"/>
  <text x="535" y="30" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">DarkButton + DarkCheckbox</text>
  <rect x="460" y="140" width="150" height="30" rx="6" fill="#1c2430" stroke="#79c0ff"/>
  <text x="535" y="160" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">LightButton + LightCheckbox</text>

  <line x1="160" y1="95" x2="230" y2="55" stroke="#6db33f" marker-end="url(#a)"/>
  <line x1="160" y1="105" x2="230" y2="145" stroke="#79c0ff" marker-end="url(#a)"/>
  <line x1="380" y1="45" x2="460" y2="25" stroke="#6db33f" marker-end="url(#a)"/>
  <line x1="380" y1="145" x2="460" y2="155" stroke="#79c0ff" marker-end="url(#a)"/>
  <defs><marker id="a" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#8b949e"/></marker></defs>
</svg>

Choosing one factory guarantees every product it produces belongs to the same visual family — dark stays with dark, light stays with light.

## 5. Runnable example

Scenario: rendering a themed UI toolkit, evolving from independently-picked widgets (which can mismatch) into an abstract factory that guarantees a consistent family every time.

### Level 1 — Basic

```java
// File: AbstractFactoryBasic.java
interface Button { void render(); }
interface Checkbox { void render(); }

class DarkButton implements Button {
    public void render() { System.out.println("[dark button]"); }
}
class LightCheckbox implements Checkbox {
    public void render() { System.out.println("[light checkbox]"); }
}

public class AbstractFactoryBasic {
    public static void main(String[] args) {
        // Nothing stops mismatching a dark button with a light checkbox.
        Button button = new DarkButton();
        Checkbox checkbox = new LightCheckbox();
        button.render();
        checkbox.render();
    }
}
```

**How to run:** save as `AbstractFactoryBasic.java`, then `javac AbstractFactoryBasic.java && java AbstractFactoryBasic` (JDK 17+).

Expected output:
```
[dark button]
[light checkbox]
```

Nothing in the code prevented pairing a `DarkButton` with a `LightCheckbox` — the two widgets came from mismatched families, and the compiler had no way to catch it.

### Level 2 — Intermediate

```java
// File: AbstractFactoryIntermediate.java
interface Button { void render(); }
interface Checkbox { void render(); }

class DarkButton implements Button { public void render() { System.out.println("[dark button]"); } }
class DarkCheckbox implements Checkbox { public void render() { System.out.println("[dark checkbox]"); } }
class LightButton implements Button { public void render() { System.out.println("[light button]"); } }
class LightCheckbox implements Checkbox { public void render() { System.out.println("[light checkbox]"); } }

interface UiFactory {
    Button createButton();
    Checkbox createCheckbox();
}
class DarkUiFactory implements UiFactory {
    public Button createButton() { return new DarkButton(); }
    public Checkbox createCheckbox() { return new DarkCheckbox(); }
}
class LightUiFactory implements UiFactory {
    public Button createButton() { return new LightButton(); }
    public Checkbox createCheckbox() { return new LightCheckbox(); }
}

public class AbstractFactoryIntermediate {
    static void renderUi(UiFactory factory) {
        factory.createButton().render();
        factory.createCheckbox().render();
    }

    public static void main(String[] args) {
        renderUi(new DarkUiFactory());
        renderUi(new LightUiFactory());
    }
}
```

**How to run:** save as `AbstractFactoryIntermediate.java`, then `javac AbstractFactoryIntermediate.java && java AbstractFactoryIntermediate` (JDK 17+).

Expected output:
```
[dark button]
[dark checkbox]
[light button]
[light checkbox]
```

The real-world concern added: `renderUi` picks a single `UiFactory` and gets both a button and a checkbox from it — the factory itself guarantees the pair always matches; there's no way to accidentally mix a dark button with a light checkbox anymore.

### Level 3 — Advanced

```java
// File: AbstractFactoryAdvanced.java
interface Button { void render(); }
interface Checkbox { void render(); }
interface Scrollbar { void render(); }

class DarkButton implements Button { public void render() { System.out.println("[dark button]"); } }
class DarkCheckbox implements Checkbox { public void render() { System.out.println("[dark checkbox]"); } }
class DarkScrollbar implements Scrollbar { public void render() { System.out.println("[dark scrollbar]"); } }

class LightButton implements Button { public void render() { System.out.println("[light button]"); } }
class LightCheckbox implements Checkbox { public void render() { System.out.println("[light checkbox]"); } }
class LightScrollbar implements Scrollbar { public void render() { System.out.println("[light scrollbar]"); } }

interface UiFactory {
    Button createButton();
    Checkbox createCheckbox();
    Scrollbar createScrollbar();
}
class DarkUiFactory implements UiFactory {
    public Button createButton() { return new DarkButton(); }
    public Checkbox createCheckbox() { return new DarkCheckbox(); }
    public Scrollbar createScrollbar() { return new DarkScrollbar(); } // new product, added to an EXISTING family
}
class LightUiFactory implements UiFactory {
    public Button createButton() { return new LightButton(); }
    public Checkbox createCheckbox() { return new LightCheckbox(); }
    public Scrollbar createScrollbar() { return new LightScrollbar(); }
}

class Dialog {
    private final Button button;
    private final Checkbox checkbox;
    private final Scrollbar scrollbar;

    Dialog(UiFactory factory) {
        this.button = factory.createButton();
        this.checkbox = factory.createCheckbox();
        this.scrollbar = factory.createScrollbar();
    }

    void render() {
        button.render();
        checkbox.render();
        scrollbar.render();
    }
}

public class AbstractFactoryAdvanced {
    static UiFactory resolveFactory(String theme) {
        return switch (theme) {
            case "DARK" -> new DarkUiFactory();
            case "LIGHT" -> new LightUiFactory();
            default -> throw new IllegalArgumentException("unknown theme: " + theme);
        };
    }

    public static void main(String[] args) {
        Dialog dialog = new Dialog(resolveFactory("DARK"));
        dialog.render();
    }
}
```

**How to run:** save as `AbstractFactoryAdvanced.java`, then `javac AbstractFactoryAdvanced.java && java AbstractFactoryAdvanced` (JDK 17+).

Expected output:
```
[dark button]
[dark checkbox]
[dark scrollbar]
```

The production-flavored hard case: `Scrollbar` is a third product added to the family, and `Dialog` composes all three from whatever single factory it's given — adding it required updating both `UiFactory` implementations to add `createScrollbar`, but every consumer of `Dialog` and `UiFactory` (like `resolveFactory` and `main`) needed no changes beyond the interface itself gaining one method.

## 6. Walkthrough

Tracing `new Dialog(resolveFactory("DARK"))` and `dialog.render()`:

1. `resolveFactory("DARK")` evaluates the `switch`, matches `"DARK"`, and returns a new `DarkUiFactory` instance.
2. `new Dialog(factory)` runs `Dialog`'s constructor: `factory.createButton()` dispatches to `DarkUiFactory.createButton`, returning a new `DarkButton`, stored in `this.button`.
3. `factory.createCheckbox()` dispatches to `DarkUiFactory.createCheckbox`, returning a new `DarkCheckbox`, stored in `this.checkbox`.
4. `factory.createScrollbar()` dispatches to `DarkUiFactory.createScrollbar`, returning a new `DarkScrollbar`, stored in `this.scrollbar`. All three fields now hold dark-family widgets — guaranteed, because all three came from the same `factory` reference.
5. `dialog.render()` calls `button.render()` first, printing `"[dark button]"`, then `checkbox.render()`, printing `"[dark checkbox]"`, then `scrollbar.render()`, printing `"[dark scrollbar]"`.
6. If `resolveFactory("LIGHT")` had been used instead, the exact same three lines in `Dialog`'s constructor and `render` method would run unchanged, but every widget produced would belong to the light family instead — `Dialog` itself has no idea which family it's using.

## 7. Gotchas & takeaways

> **Gotcha:** adding a new *product* (like `Scrollbar`) to an existing family means editing the `UiFactory` interface and every concrete factory that implements it — that part is *not* open for extension, unlike adding a new *family* (a new theme), which only requires one new factory class implementing the existing interface.

- Abstract Factory creates a whole family of related objects through one factory, guaranteeing they're always used together consistently.
- Choosing which concrete factory to use (dark vs. light) is the single decision point; every product that factory returns automatically belongs to the same family.
- Adding a new *family* (a new theme) is cheap — one new class implementing the existing `UiFactory` interface. Adding a new *product* to the family (a new widget type) is more invasive — every existing factory implementation needs the new creation method.
- Don't reach for Abstract Factory when there's only one kind of product to create — that's [Factory Method](0998-factory-method.md)'s job, and Abstract Factory's extra interface layer would be unearned complexity.
- Abstract Factory is commonly paired with [dependency inversion](0993-solid-dependency-inversion.md): code that consumes the factory (like `Dialog`) depends only on the `UiFactory` interface, never on a concrete factory class.

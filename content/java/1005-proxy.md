---
card: java
gi: 1005
slug: proxy
title: Proxy
---

## 1. What it is

The **Proxy** pattern provides a stand-in object that implements the same interface as a real object, controlling access to it. Calling code talks to the proxy exactly as if it were the real thing, but the proxy can add behavior around the delegated call — lazily creating the real object only when first needed, checking permissions before allowing access, logging every call, or caching results — all invisibly to the caller.

## 2. Why & when

Sometimes you want to control access to an object without changing how callers use it: delay the expensive cost of creating a real object until it's actually needed (a **virtual proxy**), check whether the caller is even allowed to use it (a **protection proxy**), or transparently add caching or logging around every call (a **caching/logging proxy**). Proxy exists to let all of this happen behind the exact same interface the real object already implements, so callers never need to know whether they're talking to the real thing or a stand-in.

Reach for Proxy when you need to intercept access to an object — deferring expensive construction, enforcing an authorization check, adding a cache in front of an expensive operation — without changing the interface callers already depend on. It's unnecessary when there's nothing to intercept; calling the real object directly is simpler when no lazy-loading, access control, or caching concern actually exists.

## 3. Core concept

```
interface Image { void display(); }

// The real, expensive object
class RealImage implements Image {
    private final String filename;
    RealImage(String filename) {
        this.filename = filename;
        loadFromDisk(); // expensive -- happens at construction time
    }
    private void loadFromDisk() { System.out.println("Loading " + filename + " from disk"); }
    public void display() { System.out.println("Displaying " + filename); }
}

// A virtual proxy: defers the expensive construction until display() is actually called
class ProxyImage implements Image {
    private final String filename;
    private RealImage realImage; // null until first needed

    ProxyImage(String filename) { this.filename = filename; }

    public void display() {
        if (realImage == null) {
            realImage = new RealImage(filename); // the expensive load happens HERE, lazily
        }
        realImage.display();
    }
}

Image image = new ProxyImage("photo.png"); // no disk load yet
image.display(); // NOW it loads, then displays
```

## 4. Diagram

<svg viewBox="0 0 640 160" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Calling code talks to ProxyImage which lazily creates and delegates to RealImage only when display is first called">
  <rect x="30" y="60" width="120" height="40" rx="6" fill="#1c2430" stroke="#8b949e"/>
  <text x="90" y="85" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">Caller</text>

  <rect x="230" y="60" width="150" height="40" rx="6" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="305" y="85" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">ProxyImage</text>

  <rect x="460" y="60" width="150" height="40" rx="6" fill="#1c2430" stroke="#79c0ff" stroke-dasharray="4"/>
  <text x="535" y="85" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">RealImage (lazy)</text>

  <line x1="150" y1="80" x2="230" y2="80" stroke="#8b949e" marker-end="url(#a)"/>
  <line x1="380" y1="80" x2="460" y2="80" stroke="#79c0ff" marker-end="url(#a)"/>
  <text x="305" y="45" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">same Image interface both sides</text>
  <defs><marker id="a" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#8b949e"/></marker></defs>
</svg>

`ProxyImage` implements the same `Image` interface as `RealImage`; the caller can't tell them apart until the proxy decides to create the real one.

## 5. Runnable example

Scenario: an image gallery that loads images from disk, evolving from eager, wasteful loading into a lazy proxy — and then into a protection proxy that also enforces access control.

### Level 1 — Basic

```java
// File: ProxyBasic.java
interface Image {
    void display();
}

class RealImage implements Image {
    private final String filename;
    RealImage(String filename) {
        this.filename = filename;
        System.out.println("Loading " + filename + " from disk");
    }
    public void display() {
        System.out.println("Displaying " + filename);
    }
}

public class ProxyBasic {
    public static void main(String[] args) {
        System.out.println("Gallery created (5 images referenced)");
        Image[] gallery = {
            new RealImage("photo1.png"),
            new RealImage("photo2.png")
        };
        System.out.println("Displaying only photo1:");
        gallery[0].display();
    }
}
```

**How to run:** save as `ProxyBasic.java`, then `javac ProxyBasic.java && java ProxyBasic` (JDK 17+).

Expected output:
```
Gallery created (5 images referenced)
Loading photo1.png from disk
Loading photo2.png from disk
Displaying only photo1:
Displaying photo1.png
```

Both images are loaded from disk immediately at gallery-creation time, even though only `photo1.png` was ever actually displayed — wasted work for `photo2.png`.

### Level 2 — Intermediate

```java
// File: ProxyIntermediate.java
interface Image {
    void display();
}

class RealImage implements Image {
    private final String filename;
    RealImage(String filename) {
        this.filename = filename;
        System.out.println("Loading " + filename + " from disk");
    }
    public void display() {
        System.out.println("Displaying " + filename);
    }
}

class ProxyImage implements Image {
    private final String filename;
    private RealImage realImage;

    ProxyImage(String filename) { this.filename = filename; }

    public void display() {
        if (realImage == null) {
            realImage = new RealImage(filename); // loaded lazily, only when needed
        }
        realImage.display();
    }
}

public class ProxyIntermediate {
    public static void main(String[] args) {
        System.out.println("Gallery created (2 images referenced)");
        Image[] gallery = {
            new ProxyImage("photo1.png"),
            new ProxyImage("photo2.png")
        };
        System.out.println("Displaying only photo1:");
        gallery[0].display();
    }
}
```

**How to run:** save as `ProxyIntermediate.java`, then `javac ProxyIntermediate.java && java ProxyIntermediate` (JDK 17+).

Expected output:
```
Gallery created (2 images referenced)
Displaying only photo1:
Loading photo1.png from disk
Displaying photo1.png
```

The real-world concern added: `photo2.png` is never loaded from disk at all, since `display()` was never called on it — the proxy defers the expensive `RealImage` construction until it's genuinely needed, and `gallery[1]` (photo2) stays a cheap, un-loaded `ProxyImage` for the whole run.

### Level 3 — Advanced

```java
// File: ProxyAdvanced.java
interface Image {
    void display();
}

class RealImage implements Image {
    private final String filename;
    RealImage(String filename) {
        this.filename = filename;
        System.out.println("Loading " + filename + " from disk");
    }
    public void display() {
        System.out.println("Displaying " + filename);
    }
}

class AccessDeniedException extends RuntimeException {
    AccessDeniedException(String message) { super(message); }
}

// A protection proxy: adds an authorization check AND lazy loading,
// stacked on top of the same Image interface, invisible to the caller.
class ProtectedProxyImage implements Image {
    private final String filename;
    private final boolean userIsAuthorized;
    private RealImage realImage;

    ProtectedProxyImage(String filename, boolean userIsAuthorized) {
        this.filename = filename;
        this.userIsAuthorized = userIsAuthorized;
    }

    public void display() {
        if (!userIsAuthorized) {
            throw new AccessDeniedException("not authorized to view " + filename);
        }
        if (realImage == null) {
            realImage = new RealImage(filename);
        }
        realImage.display();
    }
}

public class ProxyAdvanced {
    public static void main(String[] args) {
        Image ownPhoto = new ProtectedProxyImage("my-photo.png", true);
        Image othersPhoto = new ProtectedProxyImage("private-photo.png", false);

        ownPhoto.display();

        try {
            othersPhoto.display();
        } catch (AccessDeniedException e) {
            System.out.println("access denied: " + e.getMessage());
        }
    }
}
```

**How to run:** save as `ProxyAdvanced.java`, then `javac ProxyAdvanced.java && java ProxyAdvanced` (JDK 17+).

Expected output:
```
Loading my-photo.png from disk
Displaying my-photo.png
access denied: not authorized to view private-photo.png
```

The production-flavored hard case: `othersPhoto.display()` is blocked entirely before any disk access happens — the authorization check runs first, and `RealImage` is never even constructed for an unauthorized request, combining both the protection-proxy and virtual-proxy concerns behind one `Image` interface.

## 6. Walkthrough

Tracing `othersPhoto.display()` in `ProxyAdvanced.main`:

1. `othersPhoto` is a `ProtectedProxyImage` constructed with `userIsAuthorized = false`.
2. `othersPhoto.display()` runs `ProtectedProxyImage.display()`: the first check, `if (!userIsAuthorized)`, evaluates `!false`, which is `true`.
3. `throw new AccessDeniedException("not authorized to view private-photo.png")` executes immediately — the method returns (via the exception) right here, before reaching the `if (realImage == null)` check at all.
4. Because the authorization check fails first, `RealImage` is never constructed for `private-photo.png` — no disk-loading message ever prints for it, saving the expensive load for a request that was going to be rejected anyway.
5. The exception propagates up to `main`'s `try`/`catch`, caught by `catch (AccessDeniedException e)`, printing `"access denied: not authorized to view private-photo.png"`.
6. Compare with the earlier `ownPhoto.display()` call: `userIsAuthorized` was `true`, so the authorization check passed silently, `realImage` was `null` (first call), so `new RealImage("my-photo.png")` ran (printing the loading message), and then `realImage.display()` printed the display message — both proxy concerns (protection, then laziness) were satisfied in sequence before the real object's behavior ran.

## 7. Gotchas & takeaways

> **Gotcha:** a proxy that adds a cache in front of an expensive or slow real object needs an invalidation strategy — if the underlying data changes and the proxy keeps returning a stale cached result, callers get silently wrong answers while believing they're talking to the real, up-to-date object.

- Proxy implements the same interface as a real object and controls access to it, so callers can't tell (and shouldn't need to tell) whether they're talking to the proxy or the real thing.
- A **virtual proxy** defers expensive construction until genuinely needed; a **protection proxy** adds an authorization check; a **caching proxy** adds a cache layer — all behind the same interface.
- Multiple proxy concerns (protection and laziness, as in Level 3) can be combined in a single proxy class or stacked, similar to [Decorator](1003-decorator.md).
- The key difference from Decorator: Decorator's purpose is *adding new behavior* the wrapped object doesn't have; Proxy's purpose is *controlling access* to behavior the wrapped object already has — the mechanics (wrap + implement the same interface + delegate) look nearly identical, but the intent differs.
- Don't add a proxy layer when there's no actual access concern to manage — calling the real object directly is simpler and clearer.
- Java's dynamic proxy mechanism (`java.lang.reflect.Proxy`) can generate proxy implementations at runtime for interfaces, commonly used by frameworks for AOP-style cross-cutting concerns like transactions and logging.

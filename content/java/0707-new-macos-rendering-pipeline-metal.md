---
card: java
gi: 707
slug: new-macos-rendering-pipeline-metal
title: New macOS rendering pipeline (Metal)
---

## 1. What it is

**Java 17** shipped a new **Java2D rendering pipeline for macOS built on Apple's Metal graphics API** (JEP 382), replacing the previous pipeline built on OpenGL — which Apple had deprecated across its entire platform in favor of Metal. This is an internal change to how AWT and Swing components are actually drawn on-screen on macOS; it introduces no new Java class or method that application code calls. Existing `Graphics2D`, AWT, and Swing code renders exactly the same way from a Java-source point of view — only the underlying macOS graphics backend translating those drawing calls into pixels on screen changed.

## 2. Why & when

Apple deprecated OpenGL on macOS starting with macOS 10.14 (Mojave), signaling that OpenGL support would eventually stop receiving updates and could be removed from future macOS releases entirely, while Metal became Apple's actively maintained, actively optimized graphics API going forward. Since the JDK's Java2D rendering pipeline on macOS depended on OpenGL, staying on a deprecated, no-longer-improving graphics API risked both a hard removal in some future macOS version and missing out on Metal's better performance and lower overhead on modern Apple hardware. JEP 382 replaced that pipeline with one built on Metal, made it the default starting in Java 17, and kept the OpenGL pipeline available as an opt-in fallback (`-Dsun.java2d.opengl=true`) during the transition period. This change is entirely about *where and how* AWT/Swing rendering happens on macOS specifically — it has no equivalent on Linux or Windows, and it requires no code changes for applications; it only matters when you're diagnosing rendering behavior or performance specifically on macOS.

## 3. Core concept

```bash
# Java 17+ on macOS: Metal pipeline is used by default — no flag needed.
java MySwingApp

# The previous OpenGL pipeline can still be requested explicitly, if needed for comparison/diagnostics:
java -Dsun.java2d.opengl=true MySwingApp

# Diagnostic logging of which pipeline is actually active:
java -Dsun.java2d.trace=log MySwingApp
```

No application code changes — this is purely a system-property-level choice of graphics backend, defaulting to Metal from Java 17 onward.

## 4. Diagram

<svg viewBox="0 0 640 200" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Before Java 17, AWT and Swing rendering on macOS went through Java2D to a deprecated OpenGL pipeline; from Java 17 onward it goes through Java2D to a Metal-based pipeline by default, with the same application-facing Graphics2D API either way">
  <rect x="220" y="15" width="200" height="40" rx="8" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="320" y="40" fill="#6db33f" font-size="12" text-anchor="middle" font-family="sans-serif">AWT / Swing / Graphics2D</text>

  <line x1="290" y1="55" x2="160" y2="100" stroke="#79c0ff" stroke-width="1.5"/>
  <line x1="350" y1="55" x2="480" y2="100" stroke="#79c0ff" stroke-width="1.5"/>

  <rect x="60" y="100" width="200" height="60" rx="8" fill="#161b22" stroke="#8b949e"/>
  <text x="160" y="122" fill="#8b949e" font-size="11" text-anchor="middle" font-family="sans-serif">OpenGL pipeline</text>
  <text x="160" y="140" fill="#f0883e" font-size="9" text-anchor="middle" font-family="sans-serif">deprecated by Apple; opt-in fallback</text>

  <rect x="380" y="100" width="200" height="60" rx="8" fill="#161b22" stroke="#6db33f"/>
  <text x="480" y="122" fill="#6db33f" font-size="11" text-anchor="middle" font-family="sans-serif">Metal pipeline</text>
  <text x="480" y="140" fill="#3fb950" font-size="9" text-anchor="middle" font-family="sans-serif">default from Java 17 onward</text>

  <text x="320" y="185" fill="#8b949e" font-size="9" text-anchor="middle" font-family="sans-serif">Same Java2D/Graphics2D API on top, either way</text>
</svg>

Application-level drawing calls stay identical; only the macOS-specific graphics backend underneath switches from OpenGL to Metal.

## 5. Runnable example

Scenario: a small Swing application drawing shapes to a window — first the basic drawing code exactly as it would look on any platform, then a version that reports which rendering pipeline is actually active via macOS-specific system properties, then a headless-safe benchmark harness that renders many shapes into an off-screen image and times it, illustrating the kind of before/after comparison you would run when evaluating a rendering pipeline change (the on-screen Metal-vs-OpenGL choice itself only applies when an actual window is presented on macOS, so this level uses an off-screen buffer to stay runnable on any platform, with an explicit note about that limitation).

### Level 1 — Basic

```java
// File: ShapeCanvasBasic.java
import javax.swing.*;
import java.awt.*;

public class ShapeCanvasBasic {
    public static void main(String[] args) {
        JFrame frame = new JFrame("Shapes");
        JPanel panel = new JPanel() {
            @Override
            protected void paintComponent(Graphics g) {
                super.paintComponent(g);
                Graphics2D g2 = (Graphics2D) g;
                g2.setColor(Color.BLUE);
                g2.fillOval(20, 20, 100, 100);
                g2.setColor(Color.RED);
                g2.fillRect(150, 20, 100, 100);
            }
        };
        frame.add(panel);
        frame.setSize(300, 200);
        frame.setDefaultCloseOperation(JFrame.EXIT_ON_CLOSE);

        if (GraphicsEnvironment.isHeadless()) {
            System.out.println("Headless environment detected; skipping window display.");
            System.out.println("(On a real desktop, this would open a window with a blue circle and a red square.)");
            return;
        }
        frame.setVisible(true);
    }
}
```

**How to run:**
```
java ShapeCanvasBasic.java
```

Expected output shape (in a headless environment such as a CI server; on a real desktop, a window appears instead):
```
Headless environment detected; skipping window display.
(On a real desktop, this would open a window with a blue circle and a red square.)
```

### Level 2 — Intermediate

```java
// File: PipelineReport.java
public class PipelineReport {
    public static void main(String[] args) {
        String osName = System.getProperty("os.name");
        String openglFlag = System.getProperty("sun.java2d.opengl", "(not set)");
        String metalFlag = System.getProperty("sun.java2d.metal", "(not set, defaults apply)");

        System.out.println("OS: " + osName);
        System.out.println("sun.java2d.opengl: " + openglFlag);
        System.out.println("sun.java2d.metal:  " + metalFlag);

        if (osName.startsWith("Mac")) {
            System.out.println("On Java 17+ macOS, the Metal pipeline is the default rendering backend");
            System.out.println("unless -Dsun.java2d.opengl=true explicitly requests the older OpenGL pipeline.");
        } else {
            System.out.println("This JEP is macOS-specific; it has no effect on this platform.");
        }
    }
}
```

**How to run:**
```
java PipelineReport.java
```

Expected output shape (on macOS, Java 17+, with no explicit flags set):
```
OS: Mac OS X
sun.java2d.opengl: (not set)
sun.java2d.metal:  (not set, defaults apply)
On Java 17+ macOS, the Metal pipeline is the default rendering backend
unless -Dsun.java2d.opengl=true explicitly requests the older OpenGL pipeline.
```

### Level 3 — Advanced

```java
// File: OffscreenRenderBenchmark.java
import java.awt.*;
import java.awt.image.BufferedImage;

public class OffscreenRenderBenchmark {
    static long renderManyShapes(int shapeCount) {
        BufferedImage image = new BufferedImage(800, 600, BufferedImage.TYPE_INT_ARGB);
        Graphics2D g2 = image.createGraphics();

        long start = System.nanoTime();
        for (int i = 0; i < shapeCount; i++) {
            int x = i % 700;
            int y = (i / 700) % 500;
            g2.setColor(new Color((i * 37) % 255, (i * 59) % 255, (i * 83) % 255));
            g2.fillOval(x, y, 20, 20);
        }
        long elapsedNanos = System.nanoTime() - start;
        g2.dispose();
        return elapsedNanos;
    }

    public static void main(String[] args) {
        int shapeCount = 200_000;
        long elapsed = renderManyShapes(shapeCount);
        System.out.println("Rendered " + shapeCount + " shapes into an off-screen buffer in "
                + (elapsed / 1_000_000) + " ms");
        System.out.println("Note: off-screen BufferedImage rendering exercises Java2D's software");
        System.out.println("rasterization path, not the on-screen Metal/OpenGL pipeline directly —");
        System.out.println("a true pipeline comparison requires an actual on-screen window on macOS.");
    }
}
```

**How to run:**
```
java OffscreenRenderBenchmark.java
```

Expected output shape (timing varies by machine; the point is having a runnable, headless-safe rendering workload to reason about):
```
Rendered 200000 shapes into an off-screen buffer in 84 ms
Note: off-screen BufferedImage rendering exercises Java2D's software
rasterization path, not the on-screen Metal/OpenGL pipeline directly —
a true pipeline comparison requires an actual on-screen window on macOS.
```

## 6. Walkthrough

1. `OffscreenRenderBenchmark.main` calls `renderManyShapes(200_000)`, which first creates an in-memory `BufferedImage` (800×600, ARGB) and obtains a `Graphics2D` handle onto it via `image.createGraphics()` — this is an off-screen drawing surface that exists purely in JVM heap memory, not on any actual display.
2. The loop draws `200,000` small filled ovals at positions cycling across the image and colors derived arithmetically from the loop index, timed with `System.nanoTime()` immediately before and after the loop.
3. `g2.dispose()` releases the `Graphics2D` resources once done; the method returns the elapsed time in nanoseconds, which `main` converts to milliseconds for a readable report.
4. The printed note is important context: `BufferedImage`-based rendering goes through Java2D's **software rasterization** path regardless of platform, since there's no on-screen surface for a hardware-accelerated pipeline (OpenGL or Metal) to present to — JEP 382's actual effect is specifically on *on-screen* rendering of live AWT/Swing windows on macOS, which this off-screen benchmark deliberately sidesteps in order to stay runnable and headless-safe on any machine, including CI systems with no display.
5. To observe the real Metal-vs-OpenGL difference in practice, you would run `ShapeCanvasBasic` (Level 1) on an actual macOS desktop with a real window, once with default settings (Metal) and once with `-Dsun.java2d.opengl=true` (forcing the older pipeline), and compare either visual behavior or timing of repeated repaints — a comparison this tutorial's headless-safe examples can describe but cannot themselves execute end-to-end without a real macOS display.

```
Java2D drawing call (fillOval, fillRect, ...)
        │
   On-screen window (macOS) ──► Metal pipeline (default, Java 17+)
                              └─► OpenGL pipeline (opt-in via -Dsun.java2d.opengl=true)
        │
   Off-screen BufferedImage (any platform) ──► software rasterization (this benchmark's path)
```

## 7. Gotchas & takeaways

> This JEP only affects **on-screen** rendering of AWT/Swing components on **macOS** specifically — off-screen rendering to a `BufferedImage` (as in this tutorial's runnable examples) uses Java2D's software path on every platform and isn't a direct stand-in for observing the Metal pipeline itself. To truly compare pipelines, you need an actual macOS machine with a visible window, comparing default behavior against `-Dsun.java2d.opengl=true`.
- The Metal pipeline became the **default** on macOS starting in Java 17 — no application code or system property is required to use it; `-Dsun.java2d.opengl=true` exists specifically to opt back into the older pipeline during the transition period, e.g. if a specific application hit a Metal-pipeline regression.
- This is purely an internal Java2D rendering-backend change — no new `java.awt`/`javax.swing` class or method was added, and existing rendering code needs zero modification to benefit from it.
- Because Apple had already deprecated OpenGL platform-wide, staying on the old pipeline carried real long-term risk (a future macOS release could remove OpenGL support outright) — this JEP addressed that risk proactively rather than reactively.
- If you maintain a Swing/AWT desktop application distributed for macOS, it's worth testing on real Apple hardware after upgrading past Java 17, since rendering-pipeline changes can occasionally surface visual differences (anti-aliasing, font rendering, or specific `Graphics2D` operation edge cases) even when application code is unchanged.
- This JEP pairs naturally with [macOS AArch64 (Apple Silicon) port](0708-macos-aarch64-apple-silicon-port.md), landing in the very same release — both reflect the JDK actively adapting to Apple's evolving native platform (Metal graphics, ARM64 hardware) rather than relying on older, increasingly unsupported technology.

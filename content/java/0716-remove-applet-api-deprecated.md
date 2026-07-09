---
card: java
gi: 716
slug: remove-applet-api-deprecated
title: Remove Applet API (deprecated)
---

## 1. What it is

**Java 17** (JEP 398) **removed the Applet API** — the `java.applet` package (`Applet`, `AppletContext`, `AppletStub`, `AudioClip`) and the applet-related parts of `javax.swing` (`JApplet`) — from the JDK. Applets were small Java programs designed to run embedded inside a web page, executed by a browser plugin. The API had already been marked deprecated for removal back in Java 9 (JEP 289); Java 17 completed that process by deleting the classes entirely. Code that imports `java.applet.Applet` or extends `JApplet` simply fails to compile on Java 17 and later.

## 2. Why & when

Applets required a browser-integrated Java plugin to run — a model that made sense in the mid-to-late 1990s when browsers had no other way to run rich client-side code, but which security concerns (a plugin capable of running arbitrary bytecode inside a browser proved to be a significant, ongoing attack surface across the industry) and the rise of JavaScript as the standard, sandboxed browser scripting language made increasingly untenable. Every major browser vendor removed support for the NPAPI plugin architecture applets depended on years before Java 17 shipped, meaning the Applet API had already been unusable in any modern browser for a long time — it survived in the JDK purely as dead code with no remaining runtime environment to execute in. JEP 398 removed it outright rather than continuing to carry an API for a deployment model that no longer existed anywhere applications actually ran. If you maintain genuinely old applet-based code, the practical migration path (as the JDK itself has long recommended) is toward a full Java desktop application (Swing or JavaFX, packaged and launched normally, e.g. via [jpackage](0037-jpackage-native-installer-packager.md)) or a web-based rewrite using modern browser technologies.

## 3. Core concept

```java
// Java 16 and earlier — compiles (though no browser could actually run it as an applet by then):
import java.applet.Applet;
import java.awt.Graphics;

public class OldApplet extends Applet {
    public void paint(Graphics g) { g.drawString("Hello, applet!", 20, 20); }
}

// Java 17 and later — this simply fails to compile:
// error: package java.applet does not exist
```

There is no compatibility flag to restore the removed package — existing applet source code must be migrated to a standalone desktop application or a web-based equivalent.

## 4. Diagram

<svg viewBox="0 0 640 200" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Applets ran inside a browser via a Java plugin, a model every major browser had already abandoned before Java 17 removed the java.applet API entirely; the supported paths now are standalone Swing/JavaFX desktop applications or modern web technology">
  <rect x="20" y="20" width="280" height="160" rx="8" fill="#1c2430" stroke="#8b949e"/>
  <text x="160" y="42" fill="#8b949e" font-size="12" text-anchor="middle" font-family="sans-serif">Applet model (historical)</text>
  <text x="160" y="70" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">web page</text>
  <text x="160" y="95" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">↓ browser's Java (NPAPI) plugin</text>
  <text x="160" y="120" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">Applet subclass runs embedded</text>
  <text x="160" y="150" fill="#f0883e" font-size="9" text-anchor="middle" font-family="sans-serif">removed: java.applet gone in Java 17</text>

  <rect x="340" y="20" width="280" height="160" rx="8" fill="#1c2430" stroke="#6db33f"/>
  <text x="480" y="42" fill="#6db33f" font-size="12" text-anchor="middle" font-family="sans-serif">Supported paths (Java 17+)</text>
  <text x="480" y="75" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">Standalone Swing/JavaFX app</text>
  <text x="480" y="95" fill="#3fb950" font-size="9" text-anchor="middle" font-family="sans-serif">packaged via jpackage</text>
  <text x="480" y="130" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">Modern web app</text>
  <text x="480" y="150" fill="#3fb950" font-size="9" text-anchor="middle" font-family="sans-serif">HTML/CSS/JavaScript, no plugin</text>
</svg>

The browser-plugin embedding model this API depended on had already disappeared from every major browser before the API itself was removed.

## 5. Runnable example

Scenario: migrating a small applet — first showing what a minimal applet's structure conceptually looked like (as a comment, since it no longer compiles on Java 17), then the equivalent as a standalone Swing desktop application, then a fuller version adding the kind of lifecycle methods (`init`, `start`, `stop`) applets relied on, reimplemented using Swing's own window lifecycle events, demonstrating the concrete shape of the migration this JEP's removal makes necessary.

### Level 1 — Basic

```java
// File: OldAppletForReference.java.txt (NOT valid on Java 17+ — reference only, does not compile)
//
// import java.applet.Applet;
// import java.awt.Graphics;
//
// public class OldAppletForReference extends Applet {
//     public void paint(Graphics g) {
//         g.drawString("Hello from an applet!", 20, 20);
//     }
// }
//
// This is what applet code looked like before Java 9 deprecated the API and
// Java 17 removed it — java.applet.Applet no longer exists to extend.

// File: SwingEquivalentBasic.java — the Java 17+ standalone equivalent
import javax.swing.*;
import java.awt.*;

public class SwingEquivalentBasic {
    public static void main(String[] args) {
        JFrame frame = new JFrame("Hello (formerly an applet)");
        JPanel panel = new JPanel() {
            @Override
            protected void paintComponent(Graphics g) {
                super.paintComponent(g);
                g.drawString("Hello from a standalone Swing app!", 20, 20);
            }
        };
        frame.add(panel);
        frame.setSize(320, 120);
        frame.setDefaultCloseOperation(JFrame.EXIT_ON_CLOSE);

        if (GraphicsEnvironment.isHeadless()) {
            System.out.println("Headless environment detected; skipping window display.");
            System.out.println("(On a real desktop, this would open a small window with the message drawn on it.)");
            return;
        }
        frame.setVisible(true);
    }
}
```

**How to run:**
```
java SwingEquivalentBasic.java
```

Expected output shape (headless environment such as CI; on a real desktop a window opens instead):
```
Headless environment detected; skipping window display.
(On a real desktop, this would open a small window with the message drawn on it.)
```

### Level 2 — Intermediate

```java
// File: LifecycleMigration.java
// Reimplements the classic applet lifecycle (init/start/stop/destroy) using
// Swing's own window and component events — no java.applet involved.
import javax.swing.*;
import java.awt.*;
import java.awt.event.*;

public class LifecycleMigration {
    static void init() { System.out.println("init(): one-time setup (was Applet.init())"); }
    static void start() { System.out.println("start(): resumed / became visible (was Applet.start())"); }
    static void stop() { System.out.println("stop(): paused / hidden (was Applet.stop())"); }
    static void destroy() { System.out.println("destroy(): final cleanup (was Applet.destroy())"); }

    public static void main(String[] args) {
        init();

        JFrame frame = new JFrame("Lifecycle demo");
        frame.setSize(300, 150);
        frame.setDefaultCloseOperation(JFrame.DO_NOTHING_ON_CLOSE);

        frame.addWindowListener(new WindowAdapter() {
            @Override public void windowOpened(WindowEvent e) { start(); }
            @Override public void windowIconified(WindowEvent e) { stop(); }
            @Override public void windowDeiconified(WindowEvent e) { start(); }
            @Override public void windowClosing(WindowEvent e) {
                stop();
                destroy();
                frame.dispose();
            }
        });

        if (GraphicsEnvironment.isHeadless()) {
            System.out.println("Headless environment: simulating the lifecycle directly instead of via window events.");
            start();
            stop();
            destroy();
            return;
        }
        frame.setVisible(true);
    }
}
```

**How to run (headless environment):**
```
java LifecycleMigration.java
```

Expected output:
```
init(): one-time setup (was Applet.init())
Headless environment: simulating the lifecycle directly instead of via window events.
start(): resumed / became visible (was Applet.start())
stop(): paused / hidden (was Applet.stop())
destroy(): final cleanup (was Applet.destroy())
```

### Level 3 — Advanced

```java
// File: FullDesktopMigration.java
// A fuller standalone application: menu, drawing surface, and graceful shutdown,
// replacing the kind of features a browser-hosted applet used to rely on the
// browser page itself (and AppletContext) to provide.
import javax.swing.*;
import java.awt.*;
import java.awt.event.*;

public class FullDesktopMigration {
    static int clickCount = 0;

    public static void main(String[] args) {
        JFrame frame = new JFrame("Migrated Desktop App");
        frame.setDefaultCloseOperation(JFrame.EXIT_ON_CLOSE);
        frame.setSize(400, 200);

        JLabel label = new JLabel("Clicks: 0", SwingConstants.CENTER);
        JButton button = new JButton("Click me");
        button.addActionListener(e -> {
            clickCount++;
            label.setText("Clicks: " + clickCount);
        });

        JMenuBar menuBar = new JMenuBar();
        JMenu fileMenu = new JMenu("File");
        JMenuItem exitItem = new JMenuItem("Exit");
        exitItem.addActionListener(e -> {
            System.out.println("Shutting down cleanly (formerly relied on the browser tearing down the applet).");
            frame.dispose();
        });
        fileMenu.add(exitItem);
        menuBar.add(fileMenu);

        frame.setJMenuBar(menuBar);
        frame.setLayout(new BorderLayout());
        frame.add(label, BorderLayout.CENTER);
        frame.add(button, BorderLayout.SOUTH);

        if (GraphicsEnvironment.isHeadless()) {
            System.out.println("Headless environment: simulating three button clicks directly.");
            for (int i = 0; i < 3; i++) button.doClick();
            System.out.println(label.getText());
            return;
        }
        frame.setVisible(true);
    }
}
```

**How to run (headless environment):**
```
java FullDesktopMigration.java
```

Expected output:
```
Headless environment: simulating three button clicks directly.
Clicks: 3
```

## 6. Walkthrough

1. `FullDesktopMigration.main` builds an ordinary `JFrame` with a menu bar, a label, and a button — every one of these Swing components is unaffected by the Applet API's removal, since Swing itself (`javax.swing`) is a completely separate, actively-supported UI toolkit from the now-removed `java.applet` package; only the applet-specific embedding classes (`Applet`, `JApplet`, `AppletContext`, `AppletStub`) were removed, not Swing.
2. The button's `ActionListener` increments `clickCount` and updates the label's text — this replaces the kind of user-interaction handling an applet's `paint`/event-handling methods used to manage, but expressed through Swing's standard event-listener model instead of applet-specific hooks.
3. The `File > Exit` menu item's action explicitly calls `frame.dispose()` after printing a message — this is the standalone-application equivalent of an applet's `destroy()` lifecycle method, which a browser used to call automatically when navigating away from the page hosting the applet; a standalone application must now manage its own shutdown explicitly, since there's no longer a browser page lifecycle to hook into.
4. Because this tutorial's examples must run in headless CI environments as well as on a real desktop, each one checks `GraphicsEnvironment.isHeadless()` and, if true, simulates the interesting behavior directly (calling `button.doClick()` programmatically three times) rather than displaying an actual window — on a real desktop, removing that headless branch and simply calling `frame.setVisible(true)` shows the genuine interactive window.
5. `LifecycleMigration` (Level 2) demonstrates the more direct lifecycle-method mapping: `WindowListener` callbacks (`windowOpened`, `windowIconified`, `windowDeiconified`, `windowClosing`) are the standalone-application equivalents of an applet's `start()` (resumed/visible), `stop()` (paused/hidden), and `destroy()` (final cleanup) — the *concepts* those lifecycle hooks represented (do something when the user starts interacting, pause work when hidden, clean up when truly done) carry over directly; only the specific API surface generating those callbacks changes, from browser-driven applet callbacks to window-manager-driven Swing events.

```
Applet lifecycle (removed)          Swing / standalone app equivalent
--------------------------          ---------------------------------
Applet.init()                  ->   one-time setup in main(), before showing the window
Applet.start()                 ->   WindowListener.windowOpened / windowDeiconified
Applet.stop()                  ->   WindowListener.windowIconified
Applet.destroy()               ->   WindowListener.windowClosing -> frame.dispose()
```

## 7. Gotchas & takeaways

> `java.applet.*` and `javax.swing.JApplet` are **completely absent** from Java 17 and later — there is no system property, module flag, or compatibility mode to restore them. Any code still importing these classes must be rewritten before it can be compiled on Java 17+, full stop.
- This removal had unusually long advance notice: the Applet API was marked deprecated for removal all the way back in **Java 9** (JEP 289) — eight years and many releases before Java 17 actually completed the removal, reflecting just how thoroughly the browser-plugin deployment model it depended on had already disappeared industry-wide.
- Swing and AWT themselves (`JFrame`, `JPanel`, `Graphics2D`, and the rest) are entirely unaffected by this removal — only the applet-specific embedding and lifecycle classes are gone; a Swing-based desktop application built today uses exactly the same drawing and component APIs an applet used internally.
- The standard, JDK-supported way to package a migrated Swing/JavaFX desktop application for end users is [jpackage](0037-jpackage-native-installer-packager.md), which produces a native, double-click-to-run installer or executable — the modern equivalent of "the user just opens it," without needing a browser or plugin at all.
- If your migration target is a web application rather than a desktop one, the applet's original UI and interaction logic generally needs a full rewrite in HTML/CSS/JavaScript (or a framework built on them) — there's no direct, mechanical translation from applet code to a modern web front end, since the two run in fundamentally different environments.
- This removal is part of the same broader Java 17 cleanup as [Remove RMI Activation](0713-remove-rmi-activation.md) and [Remove experimental AOT/JIT (Graal) compiler](0714-remove-experimental-aot-jit-graal-compiler.md) — all three completed a previously-announced deprecation, reflecting the JDK's consistent pattern of removing dead or superseded functionality only after clear, long-standing advance warning.

---
card: java
gi: 7
slug: javafx-client-side-java
title: JavaFX & client-side Java
---

## 1. What it is

**JavaFX** is Java's modern GUI toolkit for building rich desktop and embedded applications. It replaced the older AWT (Abstract Window Toolkit) and Swing libraries as the recommended client-side Java platform, offering hardware-accelerated graphics via OpenGL/Direct3D, CSS styling, FXML (XML-based UI layouts), built-in media support, WebView (Chromium-based web renderer), and property/binding system for reactive UI updates.

JavaFX was bundled with Oracle JDK 8–10, then separated into an independent open-source project (**OpenJFX**) at [openjfx.io](https://openjfx.io) from Java 11 onwards. Today you add it as a Maven/Gradle dependency.

## 2. Why & when

Client-side Java has a chequered history: applets died with browser plugin support, Swing is legacy maintenance mode, and JavaFX is the modern choice for Java desktop applications. You use JavaFX when:
- Building rich cross-platform desktop tools (IDEs like IntelliJ IDEA use custom Swing, but Gluon/SceneBuilder uses JavaFX).
- Embedded HMI (Human-Machine Interface) applications on Raspberry Pi, kiosks, industrial terminals.
- Enterprise internal tooling where a web frontend is overkill and native-looking UI matters.
- Applications requiring hardware-accelerated 2D/3D graphics, animations, or media playback.

JavaFX applications can also run on iOS/Android via GluonFX (native image compilation), and as browser-hosted apps via JPro.

## 3. Core concept

JavaFX is built around a **scene graph** — a hierarchical tree of `Node` objects that the rendering engine traverses to produce the visual output. This is fundamentally different from Swing's immediate-mode painting (`paintComponent`).

Key constructs:
- **Stage** — the top-level window (analogous to `JFrame`).
- **Scene** — a container for the scene graph; attached to a `Stage`.
- **Node** — every visual element: `Button`, `Label`, `VBox`, `Rectangle`, `Canvas`.
- **Properties and Bindings** — every node attribute is a `Property<T>`; you can bind two properties so changes propagate automatically.
- **Application thread rule** — all UI operations must run on the JavaFX Application Thread (JAT). Background work runs in a `Task<T>` and results are posted back with `Platform.runLater()`.

```
Stage
 └── Scene
      └── Root Node (e.g. VBox)
           ├── Label
           ├── TextField
           └── Button
                └── event handler → updates Label text
```

CSS can style any node: `button.css { -fx-background-color: #6db33f; }` works just like web CSS.

## 4. Diagram

<svg viewBox="0 0 680 240" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="JavaFX scene graph: Stage contains Scene contains Node tree">
  <defs>
    <marker id="afxg" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#6db33f"/></marker>
  </defs>
  <!-- Stage -->
  <rect x="30" y="20" width="620" height="200" rx="10" fill="#0d1117" stroke="#8b949e" stroke-width="1.5" stroke-dasharray="5,3"/>
  <text x="340" y="42" fill="#8b949e" font-size="11" text-anchor="middle" font-family="sans-serif">Stage (window)</text>
  <!-- Scene -->
  <rect x="60" y="52" width="560" height="155" rx="8" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="340" y="72" fill="#6db33f" font-size="11" text-anchor="middle" font-family="sans-serif">Scene</text>
  <!-- Root VBox -->
  <rect x="210" y="82" width="260" height="112" rx="6" fill="#0d1117" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="340" y="100" fill="#79c0ff" font-size="11" text-anchor="middle" font-family="sans-serif">VBox (root node)</text>
  <!-- Children -->
  <rect x="225" y="108" width="100" height="34" rx="4" fill="#1c2430" stroke="#8b949e" stroke-width="1"/>
  <text x="275" y="129" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">Label</text>
  <rect x="345" y="108" width="110" height="34" rx="4" fill="#1c2430" stroke="#8b949e" stroke-width="1"/>
  <text x="400" y="129" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">TextField</text>
  <!-- Button -->
  <rect x="270" y="154" width="140" height="32" rx="4" fill="#1c2430" stroke="#6db33f" stroke-width="1.2"/>
  <text x="340" y="173" fill="#6db33f" font-size="10" text-anchor="middle" font-family="sans-serif">Button → EventHandler</text>
  <!-- Property/binding annotation -->
  <text x="90" y="170" fill="#8b949e" font-size="9" font-family="sans-serif">Properties &amp; Bindings</text>
  <text x="90" y="183" fill="#8b949e" font-size="9" font-family="sans-serif">CSS styling</text>
  <text x="90" y="196" fill="#8b949e" font-size="9" font-family="sans-serif">FXML layout</text>
</svg>

JavaFX's scene graph: `Stage → Scene → root node → child nodes`. Events bubble up; properties bind downward.

## 5. Runnable example

Scenario: a counter application — a button that increments a number, displayed in a label — growing from a minimal UI to a properly styled, thread-safe implementation.

### Level 1 — Basic

```java
// CounterApp.java
import javafx.application.Application;
import javafx.scene.Scene;
import javafx.scene.control.*;
import javafx.scene.layout.VBox;
import javafx.stage.Stage;

public class CounterApp extends Application {
    private int count = 0;

    @Override
    public void start(Stage stage) {
        Label label  = new Label("Count: 0");
        Button button = new Button("Increment");

        button.setOnAction(e -> label.setText("Count: " + (++count)));

        VBox root = new VBox(10, label, button);
        root.setStyle("-fx-padding: 20; -fx-alignment: center;");
        stage.setScene(new Scene(root, 200, 120));
        stage.setTitle("Counter");
        stage.show();
    }

    public static void main(String[] args) { launch(args); }
}
```

**How to run:** `java --module-path /path/to/javafx/lib --add-modules javafx.controls CounterApp.java`

Replace `/path/to/javafx/lib` with your OpenJFX SDK path (download from openjfx.io, or use Maven). `launch(args)` starts the JavaFX Application Thread and calls `start(Stage)`. `setOnAction` registers a lambda that fires on button click — all on the JAT.

### Level 2 — Intermediate

Same counter app extended with **property binding**: the label text is bound directly to an `IntegerProperty`, so the UI updates automatically when the property changes — no manual `setText` needed.

```java
// BoundCounterApp.java
import javafx.application.Application;
import javafx.beans.property.SimpleIntegerProperty;
import javafx.beans.binding.Bindings;
import javafx.scene.Scene;
import javafx.scene.control.*;
import javafx.scene.layout.VBox;
import javafx.stage.Stage;

public class BoundCounterApp extends Application {
    private final SimpleIntegerProperty count = new SimpleIntegerProperty(0);

    @Override
    public void start(Stage stage) {
        Label label  = new Label();
        // Bind label text to count property — updates automatically on every change
        label.textProperty().bind(Bindings.concat("Count: ", count));

        Button incBtn = new Button("Increment");
        Button resBtn = new Button("Reset");
        incBtn.setOnAction(e -> count.set(count.get() + 1));
        resBtn.setOnAction(e -> count.set(0));

        VBox root = new VBox(12, label, incBtn, resBtn);
        root.setStyle("-fx-padding: 20; -fx-alignment: center;");
        stage.setScene(new Scene(root, 220, 140));
        stage.setTitle("Bound Counter");
        stage.show();
    }

    public static void main(String[] args) { launch(args); }
}
```

**How to run:** same `--module-path` / `--add-modules` as Level 1.

`label.textProperty().bind(...)` wires the label to `count`: every time `count.set(n)` is called, the label updates without any extra code. This is JavaFX's reactive programming model.

### Level 3 — Advanced

Same counter, now with a **background task** that auto-increments every second (simulating a live data feed), posting results back to the UI thread via `Platform.runLater()` — the correct pattern for background work in JavaFX.

```java
// LiveCounterApp.java
import javafx.application.Application;
import javafx.application.Platform;
import javafx.beans.property.SimpleIntegerProperty;
import javafx.beans.binding.Bindings;
import javafx.scene.Scene;
import javafx.scene.control.*;
import javafx.scene.layout.VBox;
import javafx.stage.Stage;
import java.util.concurrent.*;
import java.util.concurrent.atomic.AtomicBoolean;

public class LiveCounterApp extends Application {
    private final SimpleIntegerProperty count = new SimpleIntegerProperty(0);
    private ScheduledExecutorService scheduler;
    private final AtomicBoolean paused = new AtomicBoolean(false);

    @Override
    public void start(Stage stage) {
        Label countLabel  = new Label();
        Label statusLabel = new Label("Status: running");
        countLabel.textProperty().bind(Bindings.concat("Count: ", count));
        countLabel.setStyle("-fx-font-size: 18;");

        Button pauseBtn = new Button("Pause");
        Button resetBtn = new Button("Reset");

        pauseBtn.setOnAction(e -> {
            boolean nowPaused = paused.getAndSet(!paused.get());
            pauseBtn.setText(nowPaused ? "Resume" : "Pause");
            statusLabel.setText("Status: " + (nowPaused ? "paused" : "running"));
        });
        resetBtn.setOnAction(e -> Platform.runLater(() -> count.set(0)));

        VBox root = new VBox(12, countLabel, statusLabel, pauseBtn, resetBtn);
        root.setStyle("-fx-padding: 24; -fx-alignment: center;");

        stage.setScene(new Scene(root, 250, 180));
        stage.setTitle("Live Counter");
        stage.setOnCloseRequest(e -> shutdown());
        stage.show();

        // Background thread: auto-increment every second
        scheduler = Executors.newSingleThreadScheduledExecutor(r -> {
            Thread t = new Thread(r, "counter-bg");
            t.setDaemon(true);   // dies with the JVM
            return t;
        });
        scheduler.scheduleAtFixedRate(() -> {
            if (!paused.get()) {
                // MUST post back to JavaFX Application Thread
                Platform.runLater(() -> count.set(count.get() + 1));
            }
        }, 1, 1, TimeUnit.SECONDS);
    }

    private void shutdown() {
        if (scheduler != null) scheduler.shutdownNow();
        Platform.exit();
    }

    public static void main(String[] args) { launch(args); }
}
```

**How to run:** same `--module-path` / `--add-modules javafx.controls` as Level 1.

`Platform.runLater(Runnable)` is the bridge: background threads use it to safely hand off UI mutations to the JAT. Calling `count.set(...)` directly from the `scheduler` thread would violate the JavaFX threading rule and cause unpredictable rendering bugs.

## 6. Walkthrough

Execution for `LiveCounterApp`:

1. **`main`** — calls `Application.launch(args)`. JavaFX starts the JAT, creates a `Stage`, and calls `start(Stage)` on the JAT.

2. **`start(Stage)`** — builds the scene graph: `VBox` → `[countLabel, statusLabel, pauseBtn, resetBtn]`. `countLabel.textProperty().bind(...)` registers an observable listener: whenever `count` property fires a change event, the binding re-evaluates and updates the label text. This happens synchronously on the JAT.

3. **`stage.show()`** — the scene graph is rendered. The rendering pipeline traverses the tree, computes layout, and issues OpenGL/Direct3D draw calls. This is hardware-accelerated via Prism (JavaFX's graphics engine).

4. **Scheduler starts** — `ScheduledExecutorService` fires on a daemon background thread every 1 second. The background thread calls `Platform.runLater(runnable)` — this enqueues the runnable on the JAT's event queue. On the next frame render cycle, the JAT dequeues it, calls `count.set(count.get() + 1)`, which fires the property change listener, which triggers the binding re-evaluation, which calls `label.setText(...)`, which marks the label dirty for re-render.

5. **User clicks Pause** — `setOnAction` fires on the JAT (button events always do). `paused.getAndSet(!paused.get())` atomically flips the flag. The background thread checks `paused.get()` before posting the increment; if `true`, it skips `Platform.runLater` entirely.

6. **Window close** — `setOnCloseRequest` fires on JAT; `shutdown()` calls `scheduler.shutdownNow()` (stops background thread) then `Platform.exit()` (stops JAT). Without this, the scheduler's non-daemon thread would keep the JVM alive after the window closes.

Request flow (button click → label update):
```
User click (OS event) → JAT event queue → button EventHandler
  → count.set(n+1) 
  → SimpleIntegerProperty fires ChangeListeners
  → Binding re-evaluates → label.setText("Count: n+1")
  → Scene marks label dirty
  → next pulse: Prism re-renders label
```

## 7. Gotchas & takeaways

> **Never update UI from a background thread.** Even `label.setText(...)` from a `Thread` other than the JAT causes `IllegalStateException: Not on FX application thread`. Always wrap with `Platform.runLater(...)`.

> **JavaFX is not bundled with JDK 11+.** Add `org.openjfx:javafx-controls:21` (and other modules you need) to your `pom.xml` or `build.gradle`, and supply `--module-path` / `--add-modules` at runtime, or use the JavaFX Maven plugin.

- JavaFX uses a **scene graph** — a retained tree of nodes re-rendered by the Prism engine each pulse.
- The **JavaFX Application Thread (JAT)** is the only thread allowed to touch UI nodes.
- **Property binding** (`property.bind(other)`) is the reactive core: changes propagate automatically, eliminating manual listener wiring.
- `Platform.runLater(Runnable)` is the safe bridge from background threads to the JAT.
- `stage.setOnCloseRequest` + `scheduler.shutdownNow()` + `Platform.exit()` is the correct shutdown sequence for apps with background threads.
- GluonFX extends JavaFX to iOS/Android via native image; JPro runs JavaFX apps in the browser.

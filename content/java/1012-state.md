---
card: java
gi: 1012
slug: state
title: State
---

## 1. What it is

The **State** pattern lets an object change its behavior when its internal state changes, making it *look* as if the object changed its class. Instead of a method riddled with `if`/`switch` branches checking "what state am I in right now?", each state becomes its own class implementing a shared interface, and the object simply delegates to whichever state object it currently holds — swapping that reference is how the object "transitions" between states.

## 2. Why & when

An object with several distinct states (a traffic light: red, yellow, green; an order: pending, paid, shipped, delivered) often ends up with every method riddled with `switch (state) { case RED: ...; case YELLOW: ...; }` branches — and every new state means editing every one of those methods, in every place state-dependent behavior appears. State exists to flip that: each state becomes its own class implementing the shared behavior interface, holding only the logic relevant to *that* state, including which state comes next. The containing object just delegates to "whichever state I'm currently in," and adding a new state means adding one new class, not editing every existing method.

Reach for State when an object's behavior for the *same* method call genuinely differs depending on which of several well-defined states it's currently in, and those states transition among each other in specific, governed ways. It's unnecessary for a simple on/off flag with no more than two behaviors and no complex transition rules — a plain boolean and an `if` covers that.

## 3. Core concept

```
interface TrafficLightState {
    void next(TrafficLight light); // each state decides what comes AFTER it
    String display();
}

class RedState implements TrafficLightState {
    public void next(TrafficLight light) { light.setState(new GreenState()); }
    public String display() { return "RED"; }
}
class GreenState implements TrafficLightState {
    public void next(TrafficLight light) { light.setState(new YellowState()); }
    public String display() { return "GREEN"; }
}
class YellowState implements TrafficLightState {
    public void next(TrafficLight light) { light.setState(new RedState()); }
    public String display() { return "YELLOW"; }
}

class TrafficLight {
    private TrafficLightState state = new RedState();
    void setState(TrafficLightState state) { this.state = state; }
    void advance() { state.next(this); } // TrafficLight itself has NO transition logic
    String display() { return state.display(); }
}
```

## 4. Diagram

<svg viewBox="0 0 640 170" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="A TrafficLight cycling through RedState, GreenState, and YellowState, each state object deciding which state comes next">
  <rect x="30" y="60" width="140" height="50" rx="8" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="100" y="90" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">TrafficLight</text>

  <rect x="260" y="10" width="100" height="34" rx="6" fill="#f0883e" fill-opacity="0.15" stroke="#f0883e"/>
  <text x="310" y="31" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">RedState</text>

  <rect x="260" y="130" width="100" height="34" rx="6" fill="#6db33f" fill-opacity="0.15" stroke="#6db33f"/>
  <text x="310" y="151" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">GreenState</text>

  <rect x="440" y="70" width="120" height="34" rx="6" fill="#79c0ff" fill-opacity="0.15" stroke="#79c0ff"/>
  <text x="500" y="91" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">YellowState</text>

  <line x1="310" y1="44" x2="310" y2="130" stroke="#8b949e" marker-end="url(#a)"/>
  <line x1="360" y1="147" x2="440" y2="95" stroke="#8b949e" marker-end="url(#a)"/>
  <line x1="500" y1="70" x2="360" y2="27" stroke="#8b949e" marker-end="url(#a)"/>
  <defs><marker id="a" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#8b949e"/></marker></defs>
</svg>

`TrafficLight` holds a reference to its current state object; each state decides for itself what the next state should be.

## 5. Runnable example

Scenario: a traffic light cycling through red, green, and yellow, evolving from a branching `switch`-based state machine into a design where each state is its own class governing its own transition.

### Level 1 — Basic

```java
// File: StateBasic.java
class TrafficLight {
    private String state = "RED";

    void advance() {
        switch (state) {
            case "RED" -> state = "GREEN";
            case "GREEN" -> state = "YELLOW";
            case "YELLOW" -> state = "RED";
        }
    }

    String display() { return state; }
}

public class StateBasic {
    public static void main(String[] args) {
        TrafficLight light = new TrafficLight();
        for (int i = 0; i < 4; i++) {
            System.out.println(light.display());
            light.advance();
        }
    }
}
```

**How to run:** save as `StateBasic.java`, then `javac StateBasic.java && java StateBasic` (JDK 17+).

Expected output:
```
RED
GREEN
YELLOW
RED
```

The transition logic lives in one `switch` — fine for three states, but every additional state-dependent method (say, `canPedestriansCross()`) needs its own separate `switch` over the same string, all of which have to be kept consistent by hand.

### Level 2 — Intermediate

```java
// File: StateIntermediate.java
interface TrafficLightState {
    void next(TrafficLight light);
    String display();
}

class RedState implements TrafficLightState {
    public void next(TrafficLight light) { light.setState(new GreenState()); }
    public String display() { return "RED"; }
}
class GreenState implements TrafficLightState {
    public void next(TrafficLight light) { light.setState(new YellowState()); }
    public String display() { return "GREEN"; }
}
class YellowState implements TrafficLightState {
    public void next(TrafficLight light) { light.setState(new RedState()); }
    public String display() { return "YELLOW"; }
}

class TrafficLight {
    private TrafficLightState state = new RedState();
    void setState(TrafficLightState state) { this.state = state; }
    void advance() { state.next(this); }
    String display() { return state.display(); }
}

public class StateIntermediate {
    public static void main(String[] args) {
        TrafficLight light = new TrafficLight();
        for (int i = 0; i < 4; i++) {
            System.out.println(light.display());
            light.advance();
        }
    }
}
```

**How to run:** save as `StateIntermediate.java`, then `javac StateIntermediate.java && java StateIntermediate` (JDK 17+).

Expected output:
```
RED
GREEN
YELLOW
RED
```

The real-world concern added: each state's transition logic lives inside that state's own class. `TrafficLight` itself contains zero transition logic — it just delegates to `state.next(this)`. Adding a state-dependent behavior means adding one method to the `TrafficLightState` interface and implementing it once per state class, not adding a new `switch` everywhere.

### Level 3 — Advanced

```java
// File: StateAdvanced.java
interface TrafficLightState {
    void next(TrafficLight light);
    String display();
    boolean canPedestriansCross(); // a SECOND state-dependent behavior, added cleanly
    default int durationSeconds() { return 30; } // a hook with a sensible default
}

class RedState implements TrafficLightState {
    public void next(TrafficLight light) { light.setState(new GreenState()); }
    public String display() { return "RED"; }
    public boolean canPedestriansCross() { return true; }
    public int durationSeconds() { return 20; } // red is shorter than the default
}
class GreenState implements TrafficLightState {
    public void next(TrafficLight light) { light.setState(new YellowState()); }
    public String display() { return "GREEN"; }
    public boolean canPedestriansCross() { return false; }
}
class YellowState implements TrafficLightState {
    public void next(TrafficLight light) { light.setState(new RedState()); }
    public String display() { return "YELLOW"; }
    public boolean canPedestriansCross() { return false; }
    public int durationSeconds() { return 5; }
}

class TrafficLight {
    private TrafficLightState state = new RedState();
    void setState(TrafficLightState state) { this.state = state; }
    void advance() { state.next(this); }
    String display() { return state.display(); }
    boolean canPedestriansCross() { return state.canPedestriansCross(); }
    int durationSeconds() { return state.durationSeconds(); }
}

public class StateAdvanced {
    public static void main(String[] args) {
        TrafficLight light = new TrafficLight();
        for (int i = 0; i < 4; i++) {
            System.out.println(light.display() + " (" + light.durationSeconds()
                + "s, pedestrians can cross: " + light.canPedestriansCross() + ")");
            light.advance();
        }
    }
}
```

**How to run:** save as `StateAdvanced.java`, then `javac StateAdvanced.java && java StateAdvanced` (JDK 17+).

Expected output:
```
RED (20s, pedestrians can cross: true)
GREEN (30s, pedestrians can cross: false)
YELLOW (5s, pedestrians can cross: false)
RED (20s, pedestrians can cross: true)
```

The production-flavored hard case: a second state-dependent behavior (`canPedestriansCross`) and a `default` hook (`durationSeconds`, only overridden by states that need a non-default duration) were both added purely by extending the `TrafficLightState` interface and each state class — `TrafficLight`'s own methods stayed simple one-line delegations throughout.

## 6. Walkthrough

Tracing the loop in `StateAdvanced.main`:

1. `light` starts with `state = new RedState()`. The first iteration prints `light.display()` (`"RED"`, dispatched to `RedState.display()`), `light.durationSeconds()` (`20`, dispatched to `RedState`'s override), and `light.canPedestriansCross()` (`true`, dispatched to `RedState`'s override).
2. `light.advance()` calls `state.next(this)`, dispatching to `RedState.next`, which calls `light.setState(new GreenState())` — `TrafficLight`'s internal `state` field is now a `GreenState` instance.
3. The second iteration prints `light.display()` (`"GREEN"`), `light.durationSeconds()` — `GreenState` doesn't override `durationSeconds()`, so it falls back to the `default` method on the `TrafficLightState` interface, returning `30` — and `light.canPedestriansCross()` (`false`, from `GreenState`).
4. `light.advance()` again dispatches to `GreenState.next`, transitioning to `new YellowState()`.
5. The third iteration prints `"YELLOW"`, `5` (from `YellowState`'s override), and `false`. `light.advance()` dispatches to `YellowState.next`, transitioning back to `new RedState()`.
6. The fourth and final iteration is back to `"RED", 20, true` — identical to the first iteration's output, confirming the state machine has completed a full cycle: red → green → yellow → red. At no point did `TrafficLight`'s own code branch on which state it was in; every behavior difference came from which state object it currently delegated to.

## 7. Gotchas & takeaways

> **Gotcha:** each state transition here constructs a *brand-new* state object (`new GreenState()`) rather than reusing a shared instance — fine for cheap, stateless state objects like these, but if a state class held its own mutable data or was expensive to construct, sharing singleton instances of each state (one `RedState` object reused every time, rather than a new one per transition) would be the better approach.

- State lets an object's behavior change based on its current internal state, by delegating to a swappable state object rather than branching internally on a status flag.
- Each state class owns its own transition logic (`next()`) and its own behavior for every state-dependent method — adding a new state-dependent behavior means adding one method to the interface and implementing it per state, not adding a new `switch` in every place behavior varies.
- The containing object (`TrafficLight`) stays simple: it holds a reference to the current state and delegates every state-dependent call to it.
- `default` methods on the state interface work well as "hooks" that most states don't need to override, similar to [Template Method](1009-template-method.md)'s hook methods.
- Don't reach for State for a simple two-value flag with trivial, non-diverging behavior — a boolean and an `if` is simpler there.
- State and [Strategy](1007-strategy.md) share the exact same structural shape (an object holding a reference to an interface implementation), but their intent differs: Strategy is chosen by the *caller* to select an algorithm; State is driven by the object's *own* internal transitions, often invisible to and not chosen by the caller at all.

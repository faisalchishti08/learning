---
card: java
gi: 1010
slug: command
title: Command
---

## 1. What it is

The **Command** pattern turns a request or an action into a standalone object, bundling together everything needed to perform it (and, optionally, undo it) behind a common interface — usually a single `execute()` method. Instead of calling a method directly, code constructs a `Command` object representing "what to do" and hands it off, letting the caller queue it, log it, pass it around, or invoke it later without needing to know any details of what it actually does.

## 2. Why & when

Calling a method directly couples the caller tightly to *when* and *how many times* that exact action happens — there's no way to queue several different actions generically, store a history of what was done for undo/redo, or delay execution until later, without writing bespoke logic for each specific action. Command exists to wrap "an action plus its parameters" into one uniform object, so a caller can hold a list of `Command` objects — each representing a completely different underlying action — and treat them all identically: queue them, log them, execute them in a batch, or reverse them.

Reach for Command when you need to queue, log, delay, or undo actions generically — a text editor's undo stack, a task queue processing heterogeneous jobs, a remote-control button that can be reprogrammed to trigger any action. It's unnecessary for a simple, immediate method call with no need to queue, log, or undo it — that's just calling the method.

## 3. Core concept

```
interface Command { void execute(); void undo(); }

class Light {
    boolean isOn = false;
    void turnOn() { isOn = true; System.out.println("Light ON"); }
    void turnOff() { isOn = false; System.out.println("Light OFF"); }
}

class TurnOnCommand implements Command {
    private final Light light;
    TurnOnCommand(Light light) { this.light = light; }
    public void execute() { light.turnOn(); }
    public void undo() { light.turnOff(); } // undo is the inverse action
}

// Caller holds Command objects generically -- it doesn't know or care they control a Light
java.util.List<Command> history = new java.util.ArrayList<>();
Command cmd = new TurnOnCommand(new Light());
cmd.execute();
history.add(cmd); // can be undone later, generically, via cmd.undo()
```

## 4. Diagram

<svg viewBox="0 0 640 170" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="A RemoteControl holding a Command reference, calling execute which delegates to a Light's turnOn method, with the command also stored in a history list for later undo">
  <rect x="30" y="60" width="150" height="50" rx="8" fill="#1c2430" stroke="#8b949e"/>
  <text x="105" y="90" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">RemoteControl</text>

  <rect x="250" y="60" width="150" height="50" rx="8" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="325" y="90" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">TurnOnCommand</text>

  <rect x="470" y="60" width="130" height="50" rx="8" fill="#1c2430" stroke="#79c0ff"/>
  <text x="535" y="90" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">Light</text>

  <line x1="180" y1="85" x2="250" y2="85" stroke="#8b949e" marker-end="url(#a)"/>
  <text x="215" y="75" fill="#8b949e" font-size="8" text-anchor="middle" font-family="sans-serif">execute()</text>
  <line x1="400" y1="85" x2="470" y2="85" stroke="#79c0ff" marker-end="url(#a)"/>
  <text x="435" y="75" fill="#79c0ff" font-size="8" text-anchor="middle" font-family="sans-serif">turnOn()</text>
  <defs><marker id="a" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#8b949e"/></marker></defs>
</svg>

`RemoteControl` calls `execute()` on whatever `Command` it holds; the command itself knows which receiver (`Light`) and which action to invoke.

## 5. Runnable example

Scenario: a smart-home remote control, evolving from direct, hardcoded method calls into a fully generic command system supporting queuing and undo.

### Level 1 — Basic

```java
// File: CommandBasic.java
class Light {
    void turnOn() { System.out.println("Light ON"); }
    void turnOff() { System.out.println("Light OFF"); }
}

public class CommandBasic {
    public static void main(String[] args) {
        Light light = new Light();

        // The "remote control" calls the light directly -- it can't be reprogrammed
        // to control anything else without changing this code.
        light.turnOn();
    }
}
```

**How to run:** save as `CommandBasic.java`, then `javac CommandBasic.java && java CommandBasic` (JDK 17+).

Expected output:
```
Light ON
```

There's no way to queue this action alongside other unrelated actions, log what happened generically, or undo it later — the calling code is hardwired to `Light.turnOn()` specifically.

### Level 2 — Intermediate

```java
// File: CommandIntermediate.java
interface Command {
    void execute();
}

class Light {
    void turnOn() { System.out.println("Light ON"); }
    void turnOff() { System.out.println("Light OFF"); }
}

class TurnOnCommand implements Command {
    private final Light light;
    TurnOnCommand(Light light) { this.light = light; }
    public void execute() { light.turnOn(); }
}

class TurnOffCommand implements Command {
    private final Light light;
    TurnOffCommand(Light light) { this.light = light; }
    public void execute() { light.turnOff(); }
}

class RemoteControl {
    void pressButton(Command command) {
        command.execute(); // has no idea what kind of action this triggers
    }
}

public class CommandIntermediate {
    public static void main(String[] args) {
        Light light = new Light();
        RemoteControl remote = new RemoteControl();

        remote.pressButton(new TurnOnCommand(light));
        remote.pressButton(new TurnOffCommand(light));
    }
}
```

**How to run:** save as `CommandIntermediate.java`, then `javac CommandIntermediate.java && java CommandIntermediate` (JDK 17+).

Expected output:
```
Light ON
Light OFF
```

The real-world concern added: `RemoteControl.pressButton` accepts any `Command` — it could just as easily be handed a command controlling a thermostat or a garage door, with zero changes to `RemoteControl` itself.

### Level 3 — Advanced

```java
// File: CommandAdvanced.java
import java.util.ArrayDeque;
import java.util.Deque;

interface Command {
    void execute();
    void undo();
}

class Light {
    boolean isOn = false;
    void turnOn() { isOn = true; System.out.println("Light ON"); }
    void turnOff() { isOn = false; System.out.println("Light OFF"); }
}

class TurnOnCommand implements Command {
    private final Light light;
    TurnOnCommand(Light light) { this.light = light; }
    public void execute() { light.turnOn(); }
    public void undo() { light.turnOff(); } // the inverse action
}

class TurnOffCommand implements Command {
    private final Light light;
    TurnOffCommand(Light light) { this.light = light; }
    public void execute() { light.turnOff(); }
    public void undo() { light.turnOn(); }
}

// Maintains a history stack, generically -- it never names Light, TurnOnCommand,
// or TurnOffCommand directly, only the shared Command interface.
class RemoteControl {
    private final Deque<Command> history = new ArrayDeque<>();

    void pressButton(Command command) {
        command.execute();
        history.push(command);
    }

    void pressUndo() {
        if (history.isEmpty()) {
            System.out.println("Nothing to undo");
            return;
        }
        Command last = history.pop();
        last.undo();
    }
}

public class CommandAdvanced {
    public static void main(String[] args) {
        Light light = new Light();
        RemoteControl remote = new RemoteControl();

        remote.pressButton(new TurnOnCommand(light));
        remote.pressButton(new TurnOffCommand(light));
        remote.pressUndo(); // undoes TurnOffCommand -> turns light back ON
        remote.pressUndo(); // undoes TurnOnCommand -> turns light back OFF
        remote.pressUndo(); // nothing left to undo
    }
}
```

**How to run:** save as `CommandAdvanced.java`, then `javac CommandAdvanced.java && java CommandAdvanced` (JDK 17+).

Expected output:
```
Light ON
Light OFF
Light ON
Light OFF
Nothing to undo
```

The production-flavored hard case: `RemoteControl` maintains a full undo history using a `Deque<Command>` as a stack, and `pressUndo()` calls `.undo()` on whatever command was most recently executed — entirely generically, without `RemoteControl` ever knowing it's actually turning a `Light` on or off.

## 6. Walkthrough

Tracing the sequence of `pressButton` and `pressUndo` calls in `CommandAdvanced.main`:

1. `remote.pressButton(new TurnOnCommand(light))` calls `TurnOnCommand.execute()`, which calls `light.turnOn()`, printing `"Light ON"` and setting `light.isOn = true`. The command is then pushed onto `history`: `[TurnOnCommand]`.
2. `remote.pressButton(new TurnOffCommand(light))` calls `TurnOffCommand.execute()`, printing `"Light OFF"` and setting `light.isOn = false`. Pushed onto `history`: `[TurnOffCommand, TurnOnCommand]` (most recent on top).
3. `remote.pressUndo()` pops the top of `history`, `TurnOffCommand`, and calls its `.undo()` method — which calls `light.turnOn()`, printing `"Light ON"` again. `history` is now `[TurnOnCommand]`.
4. `remote.pressUndo()` pops `TurnOnCommand` and calls its `.undo()`, which calls `light.turnOff()`, printing `"Light OFF"`. `history` is now empty.
5. `remote.pressUndo()` is called a third time: `history.isEmpty()` is `true`, so it prints `"Nothing to undo"` and returns immediately, without calling any command's `undo()`.
6. Notice that `RemoteControl`'s own code — `pressButton` and `pressUndo` — never once refers to `Light`, `TurnOnCommand`, or `TurnOffCommand` by name; all of that specific knowledge is encapsulated inside each `Command` object itself.

## 7. Gotchas & takeaways

> **Gotcha:** implementing `undo()` correctly requires the command to either know the exact inverse action (as here, `turnOff()` undoes `turnOn()`) or to snapshot enough prior state to restore it — a command that can't cleanly express its own inverse (like "send an email") generally can't support real undo, only a best-effort compensating action.

- Command wraps a request (an action plus its parameters) into a standalone object with a uniform `execute()` (and optionally `undo()`) method.
- This lets calling code queue, log, delay, or reverse heterogeneous actions generically, without hardcoding knowledge of what each action actually does.
- A history stack (`Deque<Command>`) is the standard way to implement undo/redo: push executed commands, pop and call `.undo()` to reverse the most recent one.
- Don't reach for Command when a direct, immediate method call is all that's needed — the extra object and interface layer are unearned complexity there.
- Command is a natural fit for task queues, job schedulers, and macro-recording systems (queue several commands, then replay them all later).
- Command and [Strategy](1007-strategy.md) share a similar shape (an interface wrapping behavior), but Command's focus is on *treating an action as data* — something to queue, log, or undo — while Strategy's focus is on *choosing which algorithm to run right now*.

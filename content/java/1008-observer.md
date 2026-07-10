---
card: java
gi: 1008
slug: observer
title: Observer
---

## 1. What it is

The **Observer** pattern defines a one-to-many dependency between objects: when one object (the **subject**) changes state, all of its registered **observers** are automatically notified and updated, without the subject needing to know any details about who its observers are or what they'll do with the notification. It's the mechanism behind event listeners, publish-subscribe systems, and reactive UI updates — the subject just says "something happened," and each observer decides for itself how to react.

## 2. Why & when

Without Observer, a subject that needs to notify several interested parties about a state change would have to know about each one specifically — hardcoding calls to `updateDashboard()`, `sendEmail()`, `logChange()` directly inside itself, and growing that list every time a new interested party shows up. Observer decouples the subject from its observers: the subject holds a list of a common `Observer` interface and calls one method (`update(...)`) on each, letting any number of observers register or unregister without the subject's own code ever changing.

Reach for Observer when several parts of a system need to react to the same event, and you don't want the event source hardcoded to know about every reactor individually — GUI event handling, notifying multiple subsystems about a data change, or a publish-subscribe messaging setup. It's unnecessary when there's exactly one fixed thing that always needs to happen in response — a direct method call is simpler and clearer there.

## 3. Core concept

```
interface Observer { void update(double temperature); }

class WeatherStation {
    private final java.util.List<Observer> observers = new java.util.ArrayList<>();
    private double temperature;

    void subscribe(Observer observer) { observers.add(observer); }
    void unsubscribe(Observer observer) { observers.remove(observer); }

    void setTemperature(double temperature) {
        this.temperature = temperature;
        for (Observer observer : observers) {
            observer.update(temperature); // subject has NO idea what each observer does
        }
    }
}

class PhoneDisplay implements Observer {
    public void update(double temperature) { System.out.println("Phone: " + temperature + "°"); }
}

WeatherStation station = new WeatherStation();
station.subscribe(new PhoneDisplay());
station.setTemperature(25.0); // "Phone: 25.0°" printed automatically
```

## 4. Diagram

<svg viewBox="0 0 640 190" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="WeatherStation notifying three registered observers -- PhoneDisplay, WebDashboard, and AlertSystem -- whenever its temperature changes">
  <rect x="240" y="70" width="160" height="50" rx="8" fill="#1c2430" stroke="#6db33f" stroke-width="1.5"/>
  <text x="320" y="100" fill="#e6edf3" font-size="11" text-anchor="middle" font-family="sans-serif">WeatherStation</text>

  <rect x="480" y="10" width="140" height="34" rx="6" fill="#1c2430" stroke="#79c0ff"/>
  <text x="550" y="31" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">PhoneDisplay</text>
  <rect x="480" y="80" width="140" height="34" rx="6" fill="#1c2430" stroke="#79c0ff"/>
  <text x="550" y="101" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">WebDashboard</text>
  <rect x="480" y="150" width="140" height="34" rx="6" fill="#1c2430" stroke="#79c0ff"/>
  <text x="550" y="171" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">AlertSystem</text>

  <line x1="400" y1="90" x2="480" y2="27" stroke="#79c0ff" marker-end="url(#a)"/>
  <line x1="400" y1="95" x2="480" y2="97" stroke="#79c0ff" marker-end="url(#a)"/>
  <line x1="400" y1="105" x2="480" y2="167" stroke="#79c0ff" marker-end="url(#a)"/>
  <defs><marker id="a" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#79c0ff"/></marker></defs>
</svg>

`WeatherStation` notifies every registered observer identically; it knows nothing about `PhoneDisplay`, `WebDashboard`, or `AlertSystem` specifically.

## 5. Runnable example

Scenario: a weather station notifying multiple displays of temperature changes, evolving from hardcoded, tightly-coupled notification calls into a fully decoupled subscribe/notify system.

### Level 1 — Basic

```java
// File: ObserverBasic.java
class PhoneDisplay {
    void show(double temperature) { System.out.println("Phone: " + temperature + "°"); }
}
class WebDashboard {
    void render(double temperature) { System.out.println("Web: " + temperature + "°"); }
}

class WeatherStation {
    private final PhoneDisplay phone = new PhoneDisplay();
    private final WebDashboard web = new WebDashboard();

    void setTemperature(double temperature) {
        // Hardcoded: WeatherStation must know about every specific display directly.
        phone.show(temperature);
        web.render(temperature);
    }
}

public class ObserverBasic {
    public static void main(String[] args) {
        WeatherStation station = new WeatherStation();
        station.setTemperature(25.0);
    }
}
```

**How to run:** save as `ObserverBasic.java`, then `javac ObserverBasic.java && java ObserverBasic` (JDK 17+).

Expected output:
```
Phone: 25.0°
Web: 25.0°
```

Adding a third display (say, an alert system) means editing `WeatherStation.setTemperature` directly — `WeatherStation` is tightly coupled to every specific display class it notifies.

### Level 2 — Intermediate

```java
// File: ObserverIntermediate.java
import java.util.ArrayList;
import java.util.List;

interface Observer {
    void update(double temperature);
}

class PhoneDisplay implements Observer {
    public void update(double temperature) { System.out.println("Phone: " + temperature + "°"); }
}
class WebDashboard implements Observer {
    public void update(double temperature) { System.out.println("Web: " + temperature + "°"); }
}

class WeatherStation {
    private final List<Observer> observers = new ArrayList<>();

    void subscribe(Observer observer) { observers.add(observer); }
    void unsubscribe(Observer observer) { observers.remove(observer); }

    void setTemperature(double temperature) {
        for (Observer observer : observers) {
            observer.update(temperature);
        }
    }
}

public class ObserverIntermediate {
    public static void main(String[] args) {
        WeatherStation station = new WeatherStation();
        station.subscribe(new PhoneDisplay());
        station.subscribe(new WebDashboard());

        station.setTemperature(25.0);
    }
}
```

**How to run:** save as `ObserverIntermediate.java`, then `javac ObserverIntermediate.java && java ObserverIntermediate` (JDK 17+).

Expected output:
```
Phone: 25.0°
Web: 25.0°
```

The real-world concern added: `WeatherStation` no longer knows about `PhoneDisplay` or `WebDashboard` by name — it holds a list of `Observer` and notifies whatever's registered. Adding a third display means calling `subscribe(...)` with a new instance; `WeatherStation` itself never changes.

### Level 3 — Advanced

```java
// File: ObserverAdvanced.java
import java.util.ArrayList;
import java.util.List;

interface Observer {
    void update(double temperature);
}

class PhoneDisplay implements Observer {
    public void update(double temperature) { System.out.println("Phone: " + temperature + "°"); }
}
class WebDashboard implements Observer {
    public void update(double temperature) { System.out.println("Web: " + temperature + "°"); }
}

// An observer that unsubscribes ITSELF once its condition is met -- a realistic
// wrinkle: observers can come and go dynamically, even from within a notification.
class OneTimeFreezeAlert implements Observer {
    private final WeatherStation station;
    private boolean fired = false;

    OneTimeFreezeAlert(WeatherStation station) { this.station = station; }

    public void update(double temperature) {
        if (!fired && temperature <= 0) {
            System.out.println("ALERT: freezing temperature detected (" + temperature + "°)");
            fired = true;
            station.unsubscribe(this); // self-unsubscribe after firing once
        }
    }
}

class WeatherStation {
    // Snapshot the list before iterating, so an observer unsubscribing itself
    // mid-notification doesn't throw a ConcurrentModificationException.
    private final List<Observer> observers = new ArrayList<>();

    void subscribe(Observer observer) { observers.add(observer); }
    void unsubscribe(Observer observer) { observers.remove(observer); }

    void setTemperature(double temperature) {
        for (Observer observer : List.copyOf(observers)) {
            observer.update(temperature);
        }
    }
}

public class ObserverAdvanced {
    public static void main(String[] args) {
        WeatherStation station = new WeatherStation();
        station.subscribe(new PhoneDisplay());
        station.subscribe(new WebDashboard());
        station.subscribe(new OneTimeFreezeAlert(station));

        station.setTemperature(25.0);
        System.out.println("---");
        station.setTemperature(-5.0);
        System.out.println("---");
        station.setTemperature(-10.0); // freeze alert already unsubscribed, stays silent
    }
}
```

**How to run:** save as `ObserverAdvanced.java`, then `javac ObserverAdvanced.java && java ObserverAdvanced` (JDK 17+).

Expected output:
```
Phone: 25.0°
Web: 25.0°
---
Phone: -5.0°
Web: -5.0°
ALERT: freezing temperature detected (-5.0°)
---
Phone: -10.0°
Web: -10.0°
```

The production-flavored hard case: `OneTimeFreezeAlert` unsubscribes itself from *inside* its own `update` call — `WeatherStation.setTemperature` iterates over `List.copyOf(observers)`, a snapshot taken before the loop starts, so removing an observer mid-notification doesn't corrupt the iteration or throw a `ConcurrentModificationException`.

## 6. Walkthrough

Tracing `station.setTemperature(-5.0)` in `ObserverAdvanced.main`:

1. `setTemperature(-5.0)` calls `List.copyOf(observers)`, producing a snapshot list containing `PhoneDisplay`, `WebDashboard`, and `OneTimeFreezeAlert` — the *original* `observers` list can be safely modified during iteration because the loop iterates over this separate snapshot.
2. The loop calls `observer.update(-5.0)` on `PhoneDisplay` first, printing `"Phone: -5.0°"`.
3. Next, `WebDashboard.update(-5.0)` prints `"Web: -5.0°"`.
4. Next, `OneTimeFreezeAlert.update(-5.0)` runs: `!fired && temperature <= 0` evaluates `!false && -5.0 <= 0`, which is `true`, so it prints `"ALERT: freezing temperature detected (-5.0°)"`, sets `fired = true`, and calls `station.unsubscribe(this)` — this removes `OneTimeFreezeAlert` from the *original* `observers` list (the one being copied at the start of each `setTemperature` call), but the snapshot list currently being iterated is unaffected.
5. On the next call, `station.setTemperature(-10.0)`, a *new* snapshot is taken via `List.copyOf(observers)` — and since `OneTimeFreezeAlert` was already removed from `observers` in step 4, this new snapshot only contains `PhoneDisplay` and `WebDashboard`.
6. So the third `setTemperature` call only prints `"Phone: -10.0°"` and `"Web: -10.0°"` — the freeze alert stays silent even though the temperature is well below freezing again, because it already unsubscribed itself after firing once.

## 7. Gotchas & takeaways

> **Gotcha:** iterating directly over a mutable observer list while an observer unsubscribes itself (or another observer) during notification throws a `ConcurrentModificationException` in Java's standard collections — iterating over a snapshot (`List.copyOf(observers)`, or an equivalent defensive copy) avoids this, at the cost of a small allocation per notification.

- Observer decouples a subject from its observers: the subject only depends on a shared `Observer` interface, never on specific observer classes.
- Subscribing and unsubscribing can happen dynamically, including from within an observer's own notification callback — which is exactly the case that risks a `ConcurrentModificationException` if not handled with a snapshot or an equivalent safe-iteration strategy.
- This pattern underlies GUI event listeners, publish-subscribe messaging, and reactive/event-driven architectures broadly.
- Don't reach for Observer when there's exactly one fixed reaction to a state change — a direct method call is clearer and has less indirection.
- Java's built-in `java.beans.PropertyChangeListener` and reactive libraries (like Reactive Streams) formalize this same pattern with additional features (filtering, backpressure, thread-safety guarantees).
- Observer is closely related to [Strategy](1007-strategy.md) in mechanics (both hold references to interface implementations), but Observer's intent is *broadcasting an event to many*, while Strategy's is *delegating one piece of work to whichever single algorithm is currently chosen*.

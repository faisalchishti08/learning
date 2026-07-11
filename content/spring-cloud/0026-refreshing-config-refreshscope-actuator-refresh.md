---
card: spring-cloud
gi: 26
slug: refreshing-config-refreshscope-actuator-refresh
title: "Refreshing config (@RefreshScope, /actuator/refresh)"
---

## 1. What it is

This card connects two threads from earlier in this course: the generic `@RefreshScope`/`/actuator/refresh` mechanism (from the Spring Cloud Context cards) and the Config Server/Config Client machinery this section has built up. Together, they form the complete live-configuration-update pipeline: a change committed to the Config Server's backend, fetched by a Config Client instance calling `/actuator/refresh`, and applied to that instance's `@RefreshScope` beans — all without a restart.

```
1. Commit a change to the config repo (e.g. db.pool.size: 50 -> 100)
2. Config Server picks it up on its next backend pull
3. POST /actuator/refresh on a running Config Client instance
4. That instance re-fetches from the Config Server, computes changed keys
5. @RefreshScope beans depending on those keys are recreated, reading the NEW value
```

## 2. Why & when

Every piece of this pipeline was covered separately: Spring Cloud Context explained *how* refresh works mechanically (recreating refresh-scoped bean instances); this Config section explained *where* configuration comes from and how it's resolved. This card is the payoff — putting them together to explain the full, real-world flow a team actually uses: editing a config repo, and having that change take effect on running services without a redeploy.

Reach for this end-to-end refresh flow when:

- A configuration change (a rate limit, a feature flag, a timeout) needs to take effect on already-running service instances, not just newly-started ones.
- You're diagnosing why a config change committed to the repo doesn't seem to be reflected in a running application — the answer is almost always somewhere in this five-step pipeline (Config Server hasn't pulled yet, refresh wasn't triggered, or the affected bean isn't `@RefreshScope`).
- Designing which configuration values genuinely need to be refresh-capable — since every `@RefreshScope` bean pays a re-creation cost on every refresh, this shouldn't be applied indiscriminately.

## 3. Core concept

```
 Config repo:  db.pool.size: 50   -->   COMMIT   -->   db.pool.size: 100

 Config Server: next pull picks up the new value (may take a moment, per the Git backend card)

 Client instance A:  POST /actuator/refresh   -> re-fetches, sees db.pool.size changed, recreates @RefreshScope beans
 Client instance B:  (never refreshed)          -> STILL running with db.pool.size=50, until IT is also refreshed

 Refresh is PER-INSTANCE unless something (the next card, Spring Cloud Bus) broadcasts it to all instances at once.
```

Refresh is inherently a per-instance operation unless something coordinates it across the whole fleet — the gap the next card's Spring Cloud Bus closes.

## 4. Diagram

<svg viewBox="0 0 640 190" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="A config repo change flows through the Config Server to one refreshed instance while another un-refreshed instance keeps stale configuration">
  <rect x="20" y="20" width="180" height="40" rx="8" fill="#1c2430" stroke="#8b949e" stroke-width="1.5"/>
  <text x="110" y="45" fill="#e6edf3" font-size="8.5" text-anchor="middle" font-family="sans-serif">Config repo commit</text>

  <line x1="110" y1="60" x2="110" y2="90" stroke="#8b949e" stroke-width="1.3" marker-end="url(#a46)"/>

  <rect x="20" y="95" width="180" height="40" rx="8" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="110" y="120" fill="#e6edf3" font-size="8.5" text-anchor="middle" font-family="sans-serif">Config Server (pulled)</text>

  <line x1="200" y1="115" x2="280" y2="80" stroke="#6db33f" stroke-width="1.3" marker-end="url(#a46)"/>
  <line x1="200" y1="115" x2="280" y2="150" stroke="#8b949e" stroke-width="1.3" marker-end="url(#a46)"/>

  <rect x="290" y="55" width="200" height="45" rx="8" fill="#6db33f30" stroke="#6db33f" stroke-width="1.5"/>
  <text x="390" y="82" fill="#e6edf3" font-size="8" text-anchor="middle" font-family="sans-serif">Instance A: refreshed, NEW value</text>

  <rect x="290" y="130" width="200" height="45" rx="8" fill="#1c2430" stroke="#8b949e" stroke-width="1.5"/>
  <text x="390" y="157" fill="#e6edf3" font-size="8" text-anchor="middle" font-family="sans-serif">Instance B: not refreshed, STALE</text>

  <defs><marker id="a46" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#8b949e"/></marker></defs>
</svg>

Only the instance that actually triggers `/actuator/refresh` picks up the new value — others remain stale until they do too.

## 5. Runnable example

The scenario: two running instances of the same service sharing a Config Server, evolving from a single-instance refresh flow (config change, then refresh, then updated value), to a two-instance scenario showing the per-instance nature of refresh explicitly, to a scenario demonstrating that a bean NOT marked refresh-scoped never picks up the change regardless of how many times `/actuator/refresh` is called.

### Level 1 — Basic

Model the basic single-instance flow: config change, refresh trigger, updated resolved value.

```java
import java.util.*;

public class RefreshFlowLevel1 {
    public static void main(String[] args) {
        ConfigServer configServer = new ConfigServer();
        configServer.setValue("db.pool.size", "50");

        ServiceInstance instanceA = new ServiceInstance(configServer);
        System.out.println("Instance A initial db.pool.size: " + instanceA.currentPoolSize());

        configServer.setValue("db.pool.size", "100"); // committed to the config repo, picked up by the server
        System.out.println("Before refresh: " + instanceA.currentPoolSize()); // still stale

        instanceA.refresh(); // POST /actuator/refresh
        System.out.println("After refresh: " + instanceA.currentPoolSize());
    }
}

class ConfigServer {
    private final Map<String, String> values = new HashMap<>();
    void setValue(String key, String value) { values.put(key, value); }
    String getValue(String key) { return values.get(key); }
}

class ServiceInstance {
    private final ConfigServer configServer;
    private String cachedPoolSize;
    ServiceInstance(ConfigServer configServer) {
        this.configServer = configServer;
        this.cachedPoolSize = configServer.getValue("db.pool.size"); // fetched once, at startup
    }
    String currentPoolSize() { return cachedPoolSize; }
    void refresh() { cachedPoolSize = configServer.getValue("db.pool.size"); } // re-fetch, mirrors @RefreshScope recreation
}
```

How to run: `java RefreshFlowLevel1.java`

`instanceA.currentPoolSize()` stays `"50"` even after the Config Server's value changes to `"100"`, until `refresh()` is explicitly called — mirroring exactly how a `@RefreshScope` bean's cached instance stays stale until an actual refresh event triggers its recreation.

### Level 2 — Intermediate

Add a second instance to make the per-instance nature of refresh explicit.

```java
import java.util.*;

public class RefreshFlowLevel2 {
    public static void main(String[] args) {
        ConfigServer configServer = new ConfigServer();
        configServer.setValue("db.pool.size", "50");

        ServiceInstance instanceA = new ServiceInstance(configServer);
        ServiceInstance instanceB = new ServiceInstance(configServer);

        configServer.setValue("db.pool.size", "100");

        instanceA.refresh(); // ONLY instance A is refreshed

        System.out.println("Instance A (refreshed): " + instanceA.currentPoolSize());
        System.out.println("Instance B (NOT refreshed): " + instanceB.currentPoolSize());
        // Same fleet, same Config Server, two DIFFERENT effective values right now.
    }
}

class ConfigServer {
    private final Map<String, String> values = new HashMap<>();
    void setValue(String key, String value) { values.put(key, value); }
    String getValue(String key) { return values.get(key); }
}

class ServiceInstance {
    private final ConfigServer configServer;
    private String cachedPoolSize;
    ServiceInstance(ConfigServer configServer) {
        this.configServer = configServer;
        this.cachedPoolSize = configServer.getValue("db.pool.size");
    }
    String currentPoolSize() { return cachedPoolSize; }
    void refresh() { cachedPoolSize = configServer.getValue("db.pool.size"); }
}
```

How to run: `java RefreshFlowLevel2.java`

`instanceA` and `instanceB` both start with the same cached value, but only `instanceA.refresh()` is called — the two instances now genuinely disagree about `db.pool.size` until `instanceB` is *also* refreshed, which is exactly the operational gap that motivates the next card's fleet-wide broadcast mechanism.

### Level 3 — Advanced

Add a bean that's *not* refresh-scoped alongside one that is, showing that calling `/actuator/refresh` any number of times never updates the non-refresh-scoped one — reinforcing the distinction from the earlier `@RefreshScope` card, now in the context of a real Config Server-driven change.

```java
import java.util.*;

public class RefreshFlowLevel3 {
    public static void main(String[] args) {
        ConfigServer configServer = new ConfigServer();
        configServer.setValue("db.pool.size", "50");
        configServer.setValue("startup.buildVersion", "1.0.0"); // deliberately read ONCE, never meant to change

        ServiceInstance instance = new ServiceInstance(configServer);
        System.out.println("Initial: poolSize=" + instance.refreshablePoolSize() + " buildVersion=" + instance.fixedBuildVersion());

        configServer.setValue("db.pool.size", "100");
        configServer.setValue("startup.buildVersion", "2.0.0"); // changes too, but nothing reads THIS refresh-aware

        instance.refresh();

        System.out.println("After refresh: poolSize=" + instance.refreshablePoolSize() + " buildVersion=" + instance.fixedBuildVersion());
        // poolSize picks up the change; buildVersion does NOT -- it was never wired to be refresh-scoped.
    }
}

class ConfigServer {
    private final Map<String, String> values = new HashMap<>();
    void setValue(String key, String value) { values.put(key, value); }
    String getValue(String key) { return values.get(key); }
}

class ServiceInstance {
    private final ConfigServer configServer;
    private String cachedPoolSize;       // @RefreshScope-style: re-read on refresh
    private final String fixedBuildVersion; // plain singleton-style: read ONCE at construction, never again

    ServiceInstance(ConfigServer configServer) {
        this.configServer = configServer;
        this.cachedPoolSize = configServer.getValue("db.pool.size");
        this.fixedBuildVersion = configServer.getValue("startup.buildVersion"); // captured once, permanently
    }
    String refreshablePoolSize() { return cachedPoolSize; }
    String fixedBuildVersion() { return fixedBuildVersion; }
    void refresh() { cachedPoolSize = configServer.getValue("db.pool.size"); } // only touches the refreshable field
}
```

How to run: `java RefreshFlowLevel3.java`

`refresh()` only reassigns `cachedPoolSize` — `fixedBuildVersion` is a value captured once in the constructor and never touched again by `refresh()`, exactly mirroring a plain (non-`@RefreshScope`) Spring bean's `@Value`-injected field: no amount of calling `/actuator/refresh` will ever update it, because nothing in the refresh mechanism was ever told to recreate that particular bean or field.

## 6. Walkthrough

Execution starts in `main` for Level 3. `instance` is constructed reading both `db.pool.size` (`"50"`) and `startup.buildVersion` (`"1.0.0"`) at that moment:

```
Initial: poolSize=50 buildVersion=1.0.0
```

Both values change at the Config Server. `instance.refresh()` runs, and internally only reassigns `cachedPoolSize` — the field backing `fixedBuildVersion` is `final` and was already set in the constructor; nothing in `refresh()` touches it:

```
After refresh: poolSize=100 buildVersion=1.0.0
```

`poolSize` reflects the new value (`"100"`); `buildVersion` remains stuck at its original `"1.0.0"`, even though the Config Server's underlying value did change to `"2.0.0"` — because nothing ever re-reads it. In a real Spring Cloud application, this exact distinction is why choosing which beans to mark `@RefreshScope` matters: a value like a build version, genuinely fixed for the lifetime of a running process, correctly stays a plain singleton; a value like a rate limit or feature flag, meant to be tunable live, needs `@RefreshScope` explicitly, or it will silently behave exactly like `fixedBuildVersion` here — unresponsive to any number of refresh calls.

## 7. Gotchas & takeaways

> Gotcha: it's easy to assume that simply changing a value in the config repository and calling `/actuator/refresh` is sufficient for *any* configuration property to update live — as this card demonstrates, that's only true for beans and fields specifically designed to be refresh-aware (`@RefreshScope`, or components that explicitly re-read configuration on each use); everything else silently keeps its startup-time value regardless of how many refreshes happen.

> Gotcha: the Config Server itself needs to have picked up the underlying change (via its own Git pull, or whichever backend mechanism) *before* a client's `/actuator/refresh` call will see anything new — refreshing a client instance against a Config Server that hasn't yet synced with its backend just re-fetches the same old values, which can be confusing when a change "isn't taking effect" for reasons unrelated to the client at all.

- The full live-refresh pipeline spans two systems covered separately in this course: the Config Server/Client machinery (this section) and the generic `@RefreshScope`/`/actuator/refresh` mechanism (the earlier Spring Cloud Context cards).
- Refresh is inherently per-instance — triggering it on one running instance has no effect on any other instance until each is refreshed individually.
- Only beans and fields explicitly designed to be refresh-aware ever reflect a config change post-startup; plain singleton-scoped values remain fixed regardless of how many refreshes occur.
- A change "not taking effect" can have several distinct causes across this pipeline: the Config Server hasn't synced with its backend yet, the client wasn't refreshed, or the affected value was never wired to be refresh-aware in the first place.

---
card: microservices
gi: 459
slug: init-containers
title: "Init containers"
---

## 1. What it is

An **init container** is a container that runs to completion **before** a Pod's main application containers start, as part of the same Pod. Kubernetes runs each init container in order, one at a time, and only starts the application containers once every init container has exited successfully — giving the Pod a guaranteed, sequential setup phase that the application itself never has to implement.

## 2. Why & when

You reach for init containers whenever a Pod needs guaranteed setup work done before its main process is safe to start:

- **Waiting for a dependency to be ready.** An application that connects to a database on startup can crash-loop if that database isn't reachable yet — an init container can poll until the dependency responds, so the main container only starts once it's actually safe to.
- **One-time setup that shouldn't run inside the long-lived application process.** Cloning a config repository, running a database migration, or generating a file the application needs are all things you want to happen once, cleanly, and separately from the application's own lifecycle and restart behavior.
- **Different tooling or permissions than the main container needs.** An init container can use a different (often heavier, more privileged) image than the lean application image, without that extra tooling ever being present in the running application container.
- **A strict ordering guarantee**, with no extra coordination code: Kubernetes itself enforces that init containers finish, in the order listed, before any application container is even started, let alone receives traffic.

## 3. Core concept

Think of it like a stagehand setting up a theater before the actors go on: the curtains, lighting, and props all have to be in place first, in a defined order, and the audience never sees that setup happen — the play only starts once the stage is actually ready. Init containers are that same guaranteed setup step, run and finished before the main show (the application container) begins.

The mechanics:

1. **A Pod spec lists one or more init containers, in order**, separately from its main (application) containers.
2. **Kubernetes starts the first init container** and waits for it to exit with a success status.
3. **If it fails, Kubernetes restarts it** (subject to the Pod's restart policy) — the Pod does not proceed to the next init container, or to the application containers, until the current one succeeds.
4. **Once every init container has exited successfully, in order**, Kubernetes starts all of the Pod's application containers, which can now safely assume that whatever the init containers set up (files, readiness, migrations) is actually in place.
5. **Init containers do not run again for the life of the Pod** — they run once, at Pod startup, and are not part of the ongoing set of containers that receive traffic or get health-checked while the Pod is running.

## 4. Diagram

<svg viewBox="0 0 640 220" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Init containers run in sequence and must succeed before the main application container starts">
  <rect x="20" y="80" width="140" height="60" rx="8" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="90" y="105" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">init: wait-for-db</text>
  <text x="90" y="122" fill="#79c0ff" font-size="9" text-anchor="middle" font-family="sans-serif">runs, exits 0</text>

  <rect x="190" y="80" width="140" height="60" rx="8" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="260" y="105" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">init: run-migration</text>
  <text x="260" y="122" fill="#79c0ff" font-size="9" text-anchor="middle" font-family="sans-serif">runs, exits 0</text>

  <rect x="380" y="80" width="220" height="60" rx="8" fill="#1c2430" stroke="#6db33f" stroke-width="2"/>
  <text x="490" y="105" fill="#e6edf3" font-size="10" text-anchor="middle" font-family="sans-serif">app container</text>
  <text x="490" y="122" fill="#6db33f" font-size="9" text-anchor="middle" font-family="sans-serif">starts only after both succeed</text>

  <line x1="160" y1="110" x2="190" y2="110" stroke="#8b949e" marker-end="url(#a1)"/>
  <line x1="330" y1="110" x2="380" y2="110" stroke="#8b949e" marker-end="url(#a1)"/>

  <text x="320" y="180" fill="#8b949e" font-size="10" text-anchor="middle" font-family="sans-serif">strictly sequential: each init container must exit 0 before the next one, or the app, starts</text>

  <defs>
    <marker id="a1" markerWidth="8" markerHeight="8" refX="6" refY="4" orient="auto"><path d="M0,0 L8,4 L0,8 z" fill="#8b949e"/></marker>
  </defs>
</svg>

Init containers run one at a time, in order, and the application container waits until all of them exit successfully.

## 5. Runnable example

Scenario: a Pod's application needs a downstream dependency to be reachable before it starts. We start by simulating the basic wait-then-start sequence, extend it with a second, ordered init step (a migration), then handle the hard case: an init step that fails and must retry with backoff rather than immediately failing the whole Pod startup.

### Level 1 — Basic

```java
// File: InitContainerBasic.java -- simulates ONE init container that waits
// for a dependency, then the main application starting only AFTER the
// init step reports success. Models Kubernetes' ordering guarantee.
public class InitContainerBasic {
    // The init container's job: block until the dependency is ready.
    static boolean initWaitForDb() {
        System.out.println("[init: wait-for-db] checking database availability...");
        System.out.println("[init: wait-for-db] database is reachable -- exiting 0");
        return true; // simulates a successful exit code
    }

    // The main application container's job: assumes setup already happened.
    static void mainAppStart() {
        System.out.println("[app] starting -- database already confirmed reachable by init container");
    }

    public static void main(String[] args) {
        boolean initSucceeded = initWaitForDb();
        if (initSucceeded) {
            mainAppStart();
        } else {
            System.out.println("[pod] init container failed -- app container will NOT start");
        }
    }
}
```

How to run: `java InitContainerBasic.java`

`initWaitForDb` represents the init container's entire job: check the dependency, and only report success once it's actually ready. `main` mirrors the Kubernetes Pod-startup contract directly — `mainAppStart()` is only called if `initWaitForDb()` returned `true`, exactly like the application container is only started once the init container exits with status `0`.

### Level 2 — Intermediate

```java
// File: InitContainerOrdered.java -- the SAME wait-then-start idea, now
// with a SECOND init container (a migration step) that must run AFTER the
// first one succeeds and BEFORE the app starts -- modeling Kubernetes'
// strict, ordered execution of multiple init containers.
public class InitContainerOrdered {
    static boolean initWaitForDb() {
        System.out.println("[init 1: wait-for-db] checking database availability...");
        System.out.println("[init 1: wait-for-db] database is reachable -- exiting 0");
        return true;
    }

    static boolean initRunMigration() {
        System.out.println("[init 2: run-migration] applying pending schema migrations...");
        System.out.println("[init 2: run-migration] schema is up to date -- exiting 0");
        return true;
    }

    static void mainAppStart() {
        System.out.println("[app] starting -- database reachable AND schema migrated");
    }

    public static void main(String[] args) {
        // Strict order: init 2 only runs if init 1 succeeded.
        if (!initWaitForDb()) {
            System.out.println("[pod] init 1 failed -- init 2 and app will NOT run");
            return;
        }
        if (!initRunMigration()) {
            System.out.println("[pod] init 2 failed -- app will NOT start");
            return;
        }
        mainAppStart();
    }
}
```

How to run: `java InitContainerOrdered.java`

`main` now enforces two sequential gates instead of one: `initRunMigration()` is only ever called after `initWaitForDb()` has already returned `true`, and `mainAppStart()` is only called after *both* have succeeded. Each `if (!...) return;` mirrors Kubernetes halting the whole Pod-startup sequence the instant any init container in the ordered list fails.

### Level 3 — Advanced

```java
// File: InitContainerRetry.java -- the SAME ordered init sequence, now
// handling a PRODUCTION-FLAVORED hard case: the FIRST init step doesn't
// succeed immediately -- the dependency isn't ready yet, a common reality
// when a database Pod is still starting up elsewhere in the cluster. The
// init container must retry with backoff rather than failing the Pod on
// the first check, exactly like Kubernetes restarts a failed init
// container according to the Pod's restart policy.
public class InitContainerRetry {
    static int dbCheckAttempt = 0;

    // Simulates the dependency becoming ready only on the third check.
    static boolean isDbReachable() {
        dbCheckAttempt++;
        boolean ready = dbCheckAttempt >= 3;
        System.out.println("[init 1: wait-for-db] attempt " + dbCheckAttempt + ": " + (ready ? "reachable" : "not ready yet"));
        return ready;
    }

    static boolean initWaitForDbWithRetry() throws InterruptedException {
        int maxAttempts = 5;
        long backoffMs = 10; // shortened for a runnable demo
        for (int attempt = 1; attempt <= maxAttempts; attempt++) {
            if (isDbReachable()) {
                System.out.println("[init 1: wait-for-db] success on attempt " + attempt + " -- exiting 0");
                return true;
            }
            System.out.println("[init 1: wait-for-db] backing off " + backoffMs + "ms before retry");
            Thread.sleep(backoffMs);
            backoffMs *= 2; // exponential backoff, like a real restart policy would space out retries
        }
        System.out.println("[init 1: wait-for-db] exhausted " + maxAttempts + " attempts -- exiting non-zero");
        return false;
    }

    static boolean initRunMigration() {
        System.out.println("[init 2: run-migration] applying pending schema migrations...");
        System.out.println("[init 2: run-migration] schema is up to date -- exiting 0");
        return true;
    }

    static void mainAppStart() {
        System.out.println("[app] starting -- database reachable AND schema migrated");
    }

    public static void main(String[] args) throws InterruptedException {
        if (!initWaitForDbWithRetry()) {
            System.out.println("[pod] init 1 permanently failed -- init 2 and app will NOT run");
            return;
        }
        if (!initRunMigration()) {
            System.out.println("[pod] init 2 failed -- app will NOT start");
            return;
        }
        mainAppStart();
    }
}
```

How to run: `java InitContainerRetry.java`

`isDbReachable` only returns `true` starting on the third call, simulating a dependency that takes a moment to become available. `initWaitForDbWithRetry` loops up to `maxAttempts` times, sleeping for a doubling `backoffMs` between failed checks — mirroring how Kubernetes, under the Pod's restart policy, re-runs a failed init container rather than failing the whole Pod on the very first unsuccessful attempt. Only once the retry loop succeeds does execution reach `initRunMigration` and, finally, `mainAppStart`.

## 6. Walkthrough

Trace `InitContainerRetry.main` in order. **First**, `initWaitForDbWithRetry()` is called, entering its retry loop with `attempt = 1`.

**Next**, `isDbReachable()` runs: `dbCheckAttempt` becomes `1`, which is less than `3`, so it prints "not ready yet" and returns `false`. The loop prints the backoff message, sleeps `10ms`, and doubles `backoffMs` to `20`.

**Then**, `attempt = 2` runs the same way: `dbCheckAttempt` becomes `2`, still less than `3`, another "not ready yet," another (longer) backoff sleep, `backoffMs` doubling again to `40`.

**After that**, `attempt = 3` runs: `dbCheckAttempt` becomes `3`, which meets the `>= 3` threshold, so `isDbReachable` returns `true`. `initWaitForDbWithRetry` prints the success line and returns `true` from the outer function, exactly like an init container finally exiting with status `0` after two failed, restarted attempts.

**Finally**, back in `main`, the first `if` check passes since `initWaitForDbWithRetry()` returned `true`, so execution proceeds to `initRunMigration()`, which succeeds immediately and prints its own success line, and then to `mainAppStart()`, which prints the final line confirming the application only started after both ordered init steps completed.

```
[init 1: wait-for-db] attempt 1: not ready yet
[init 1: wait-for-db] backing off 10ms before retry
[init 1: wait-for-db] attempt 2: not ready yet
[init 1: wait-for-db] backing off 20ms before retry
[init 1: wait-for-db] attempt 3: reachable
[init 1: wait-for-db] success on attempt 3 -- exiting 0
[init 2: run-migration] applying pending schema migrations...
[init 2: run-migration] schema is up to date -- exiting 0
[app] starting -- database reachable AND schema migrated
```

## 7. Gotchas & takeaways

> An init container that fails permanently blocks the Pod from starting at all — the application container never runs, and the Pod stays stuck in an `Init` state rather than crash-looping. This is usually the *desired* behavior (better a stuck Pod than a live one hammering a database that isn't there), but it means a broken init container can silently stall a rollout if nobody is watching Pod status.
- Init containers run once per Pod startup, strictly in the order they're listed — they are not a place to put ongoing background work; that belongs in a [sidecar](0456-sidecar-pattern.md), which runs for the Pod's entire lifetime.
- Because init containers can use a different image than the application, they're a good place for heavier setup tooling (migration CLIs, network utilities) that you don't want bloating the lean application image.
- A slow or endlessly retrying init container directly delays the Pod becoming ready — factor init container time into how quickly a [rolling deployment](0450-rolling-deployment.md) can actually complete.
- Init container failures should be visible in the same monitoring that watches deployment health; a Pod stuck in `Init` looks very different from a crash-looping application container, and needs different debugging.
- Use init containers for guaranteed *ordering* (dependency checks, migrations, config generation) — anything that must finish before the application code runs even once.

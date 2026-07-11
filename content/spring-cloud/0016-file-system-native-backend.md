---
card: spring-cloud
gi: 16
slug: file-system-native-backend
title: "File system / native backend"
---

## 1. What it is

The "native" backend serves Config Server configuration directly from the local filesystem or classpath, instead of cloning a remote Git repository — activated by setting `spring.profiles.active=native` and pointing `spring.cloud.config.server.native.search-locations` at a directory.

```yaml
spring:
  profiles:
    active: native
  cloud:
    config:
      server:
        native:
          search-locations: file:///opt/config-repo
```

## 2. Why & when

The Git backend (previous card) is the production default, but it introduces real dependencies: network access to a Git host, credentials, clone/pull latency. The native backend removes all of that, reading configuration files directly from disk — ideal for local development, testing the Config Server itself, or air-gapped environments where a full Git-based setup is unnecessary overhead.

Reach for the native backend when:

- Developing or testing locally, where standing up (or depending on network access to) a real Git repository is unnecessary friction.
- Running the Config Server in a constrained or air-gapped environment where configuration is deployed to disk by some other mechanism (a config-map mount, a deployment artifact) rather than fetched from Git directly.
- Writing integration tests for Config Server-dependent application startup, where a predictable, fast, local file source is preferable to network I/O.

## 3. Core concept

```
 spring.profiles.active=native
 spring.cloud.config.server.native.search-locations=file:///opt/config-repo

 /opt/config-repo/
   application.yml
   payment-service.yml
   payment-service-production.yml

 GET /payment-service/production
   -> Config Server reads DIRECTLY from /opt/config-repo (no Git clone/pull, no network call)
   -> same resolution logic (most-specific-first layering) as the Git backend
```

The native backend swaps *where* files come from; the resolution logic (layering by application/profile/label) covered in the Config Server card stays the same.

## 4. Diagram

<svg viewBox="0 0 640 150" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="A Config Server reads directly from a local filesystem directory instead of pulling from a remote Git host">
  <rect x="20" y="45" width="200" height="45" rx="8" fill="#1c2430" stroke="#8b949e" stroke-width="1.5"/>
  <text x="120" y="72" fill="#e6edf3" font-size="8.5" text-anchor="middle" font-family="sans-serif">local filesystem</text>

  <line x1="220" y1="67" x2="280" y2="67" stroke="#8b949e" stroke-width="1.3" marker-end="url(#a36)"/>
  <text x="250" y="57" fill="#8b949e" font-size="7" text-anchor="middle" font-family="sans-serif">read</text>

  <rect x="290" y="45" width="150" height="45" rx="8" fill="#6db33f30" stroke="#6db33f" stroke-width="1.5"/>
  <text x="365" y="72" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">Config Server</text>

  <line x1="440" y1="67" x2="500" y2="67" stroke="#8b949e" stroke-width="1.3" marker-end="url(#a36)"/>

  <rect x="510" y="45" width="110" height="45" rx="8" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="565" y="72" fill="#e6edf3" font-size="8.5" text-anchor="middle" font-family="sans-serif">client</text>

  <defs><marker id="a36" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#8b949e"/></marker></defs>
</svg>

The native backend removes the Git hop entirely — the Config Server reads local files directly.

## 5. Runnable example

The scenario: a local development setup using the native backend, evolving from a bare filesystem read with no resolution logic, to full application/profile layering matching the Git backend's behavior, to a demonstration that switching between native and Git backends is purely a configuration change — application code and resolution logic are identical either way.

### Level 1 — Basic

Model a bare filesystem read, files loaded directly with no layering yet.

```java
import java.util.*;

public class NativeBackendLevel1 {
    public static void main(String[] args) {
        FileSystemStore store = new FileSystemStore("/opt/config-repo");
        store.putFile("application.yml", Map.of("db.pool.size", "10"));
        store.putFile("payment-service-production.yml", Map.of("db.pool.size", "50"));

        System.out.println("application.yml: " + store.readFile("application.yml"));
        System.out.println("payment-service-production.yml: " + store.readFile("payment-service-production.yml"));
    }
}

class FileSystemStore {
    private final String rootPath;
    private final Map<String, Map<String, String>> files = new HashMap<>();
    FileSystemStore(String rootPath) { this.rootPath = rootPath; }
    void putFile(String filename, Map<String, String> content) { files.put(filename, content); }
    Map<String, String> readFile(String filename) { return files.get(filename); }
}
```

How to run: `java NativeBackendLevel1.java`

Files are read directly by exact name — no `{application}/{profile}` resolution logic connects a request to the right combination of files yet.

### Level 2 — Intermediate

Add the same layered resolution logic the Git-backed Config Server uses, now reading from the filesystem-backed store instead.

```java
import java.util.*;

public class NativeBackendLevel2 {
    public static void main(String[] args) {
        NativeConfigServer server = new NativeConfigServer("/opt/config-repo");
        server.putFile("application", Map.of("db.pool.size", "10"));
        server.putFile("payment-service-production", Map.of("db.pool.size", "50", "payment.gateway", "stripe-live"));

        System.out.println("GET /payment-service/production (native backend) ->");
        Map<String, String> resolved = server.resolve("payment-service", "production");
        System.out.println("  " + resolved);
    }
}

// Stands in for a Config Server running with spring.profiles.active=native.
class NativeConfigServer {
    private final String searchLocation;
    private final Map<String, Map<String, String>> files = new HashMap<>();
    NativeConfigServer(String searchLocation) { this.searchLocation = searchLocation; }
    void putFile(String name, Map<String, String> content) { files.put(name, content); }

    Map<String, String> resolve(String application, String profile) {
        Map<String, String> effective = new HashMap<>();
        if (files.containsKey("application")) effective.putAll(files.get("application"));
        String specific = application + "-" + profile;
        if (files.containsKey(specific)) effective.putAll(files.get(specific)); // most specific wins
        return effective;
    }
}
```

How to run: `java NativeBackendLevel2.java`

`resolve` applies exactly the same most-specific-wins layering the Git backend uses — the only difference from that earlier card is `NativeConfigServer` reads its files from `searchLocation` on disk (simulated here as an in-memory map populated once) instead of a Git clone.

### Level 3 — Advanced

Show the backend-swap payoff directly: identical application-facing resolution logic, running against two different backend implementations (native vs. Git-style), with the same result — demonstrating that switching backends is purely a Config Server-side configuration change.

```java
import java.util.*;

public class NativeBackendLevel3 {
    public static void main(String[] args) {
        ConfigBackend nativeBackend = new NativeBackend();
        nativeBackend.load("application", Map.of("db.pool.size", "10"));
        nativeBackend.load("payment-service-production", Map.of("db.pool.size", "50"));

        ConfigBackend gitBackend = new GitStyleBackend();
        gitBackend.load("application", Map.of("db.pool.size", "10"));
        gitBackend.load("payment-service-production", Map.of("db.pool.size", "50"));

        // The SAME resolution logic runs against EITHER backend -- interchangeably.
        System.out.println("Resolved via native backend: " + resolveConfig(nativeBackend, "payment-service", "production"));
        System.out.println("Resolved via Git-style backend: " + resolveConfig(gitBackend, "payment-service", "production"));
    }

    // Backend-agnostic resolution logic -- the Config Server's core behavior, independent of storage mechanism.
    static Map<String, String> resolveConfig(ConfigBackend backend, String application, String profile) {
        Map<String, String> effective = new HashMap<>();
        if (backend.has("application")) effective.putAll(backend.get("application"));
        String specific = application + "-" + profile;
        if (backend.has(specific)) effective.putAll(backend.get(specific));
        return effective;
    }
}

interface ConfigBackend {
    void load(String name, Map<String, String> content);
    boolean has(String name);
    Map<String, String> get(String name);
}

// Reads from local files -- no network involved.
class NativeBackend implements ConfigBackend {
    private final Map<String, Map<String, String>> files = new HashMap<>();
    public void load(String name, Map<String, String> content) { files.put(name, content); }
    public boolean has(String name) { return files.containsKey(name); }
    public Map<String, String> get(String name) { return files.get(name); }
}

// Simulates fetching from a cloned/pulled Git repository -- structurally different internally, same interface.
class GitStyleBackend implements ConfigBackend {
    private final Map<String, Map<String, String>> clonedRepoFiles = new HashMap<>();
    public void load(String name, Map<String, String> content) { clonedRepoFiles.put(name, content); }
    public boolean has(String name) { return clonedRepoFiles.containsKey(name); }
    public Map<String, String> get(String name) { return clonedRepoFiles.get(name); }
}
```

How to run: `java NativeBackendLevel3.java`

`resolveConfig` is written once, against the `ConfigBackend` interface, and produces identical results whether it's handed `NativeBackend` or `GitStyleBackend` — exactly mirroring how a real Config Server's core resolution logic is entirely independent of which backend (`spring.profiles.active=native` vs. the default Git configuration) actually supplies the underlying files.

## 6. Walkthrough

Execution starts in `main` for Level 3. Both `nativeBackend` and `gitBackend` are loaded with the identical two files and identical content. `resolveConfig` is called against each in turn.

For `nativeBackend`, `resolveConfig` checks `has("application")` (true), merges it in, then checks `has("payment-service-production")` (also true), merging that in as well, with its `db.pool.size=50` overwriting the shared default's `10`:

```
Resolved via native backend: {db.pool.size=50}
```

The exact same sequence of calls runs against `gitBackend` — a structurally different class internally (`clonedRepoFiles` instead of `files`, standing in for the fact that a real Git backend involves cloning and pulling, which `NativeBackend` never does) — but since both implement the same `ConfigBackend` interface with the same data loaded, the result is identical:

```
Resolved via Git-style backend: {db.pool.size=50}
```

In a real Spring Cloud Config Server, this is exactly the point of the native backend: a developer can run the *exact same* Config Server application, with the *exact same* client-facing behavior, by simply setting `spring.profiles.active=native` and pointing `search-locations` at a local directory — no code change, no different resolution behavior, just a different (and much faster, network-free) place for the underlying files to come from.

## 7. Gotchas & takeaways

> Gotcha: the native backend reads files directly from disk with no built-in versioning or audit trail — none of the Git backend's commit history, diff review, or `git revert` rollback capability (from the previous card) applies; using native for anything beyond local development or testing gives up that operational safety net entirely.

> Gotcha: `search-locations` supports multiple comma-separated paths, searched in order — a common mistake is assuming later paths override earlier ones the way Git backend files layer by specificity; the native backend's multi-location search is about *finding* files across several directories, not about overriding one location's file with another's.

- The native backend serves configuration directly from local files instead of a Git repository, using `spring.profiles.active=native` and `search-locations`.
- The same resolution logic (most-specific-wins layering by application and profile) applies regardless of backend — the Config Server's core behavior is backend-agnostic.
- Native is ideal for local development, testing, and air-gapped deployments, but gives up Git's commit history, review, and rollback capabilities.
- Switching between native and Git backends is a Config Server-side configuration change, requiring no changes to the resolution logic or to Config Client applications consuming the server.

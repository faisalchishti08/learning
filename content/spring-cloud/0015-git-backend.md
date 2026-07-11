---
card: spring-cloud
gi: 15
slug: git-backend
title: "Git backend"
---

## 1. What it is

The Git backend is Spring Cloud Config Server's default configuration source: a Git repository (local or remote — GitHub, GitLab, an internal Git server) that the server clones and periodically pulls, treating each file as a configuration source and each branch or tag as a `{label}` that clients can request.

```yaml
# Config Server's own application.yml
spring:
  cloud:
    config:
      server:
        git:
          uri: https://github.com/example-org/config-repo
          default-label: main
```

## 2. Why & when

The previous card described the Config Server's request/response shape without specifying where the actual data comes from. Git is the natural default backend: configuration changes get commit history, diffs, blame, pull-request review, and rollback — the exact same tooling and discipline already used for application code, applied to configuration instead.

Reach for the Git backend when:

- Configuration changes should be reviewable (via pull requests) and auditable (via commit history) before they take effect.
- Different environments' configuration should be able to diverge in a controlled, trackable way — via branches or tags, mapped to the `{label}` part of a Config Server request.
- Rolling back a bad configuration change should be as simple as reverting a commit, rather than manually reconstructing a previous state.

## 3. Core concept

```
 config-repo (Git):
   main branch:
     application.yml
     payment-service.yml
   release-2024-q3 tag:
     application.yml   (an OLDER version, as of that tag)
     payment-service.yml

 GET /payment-service/production            -- {label} defaults to "main"
 GET /payment-service/production/release-2024-q3  -- {label} = a specific tag, serving an OLDER config snapshot

 A commit to main -> Config Server's next pull picks it up -> served to clients on their next request/refresh
```

Git branches and tags map directly onto the Config Server's `{label}` parameter, letting different environments or historical snapshots be requested explicitly.

## 4. Diagram

<svg viewBox="0 0 640 150" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="The Config Server periodically pulls from a Git repository and serves whichever branch or tag a client requests as the label">
  <rect x="20" y="45" width="180" height="45" rx="8" fill="#1c2430" stroke="#8b949e" stroke-width="1.5"/>
  <text x="110" y="72" fill="#e6edf3" font-size="8.5" text-anchor="middle" font-family="sans-serif">Git repo (remote)</text>

  <line x1="200" y1="60" x2="260" y2="60" stroke="#8b949e" stroke-width="1.3" marker-end="url(#a35)"/>
  <text x="230" y="50" fill="#8b949e" font-size="7" text-anchor="middle" font-family="sans-serif">pull</text>

  <rect x="270" y="45" width="150" height="45" rx="8" fill="#6db33f30" stroke="#6db33f" stroke-width="1.5"/>
  <text x="345" y="72" fill="#e6edf3" font-size="9" text-anchor="middle" font-family="sans-serif">Config Server</text>

  <line x1="420" y1="60" x2="480" y2="60" stroke="#8b949e" stroke-width="1.3" marker-end="url(#a35)"/>

  <rect x="490" y="45" width="130" height="45" rx="8" fill="#1c2430" stroke="#79c0ff" stroke-width="1.5"/>
  <text x="555" y="72" fill="#e6edf3" font-size="8.5" text-anchor="middle" font-family="sans-serif">requesting client</text>

  <defs><marker id="a35" markerWidth="9" markerHeight="9" refX="7" refY="3" orient="auto"><path d="M0,0 L7,3 L0,6 Z" fill="#8b949e"/></marker></defs>
</svg>

The Config Server sits between the Git repository and requesting clients, pulling on one side and serving on the other.

## 5. Runnable example

The scenario: a Config Server backed by a simulated Git repository, evolving from reading whatever the latest commit happens to contain, to resolving a specific label (branch or tag) explicitly, to a rollback scenario demonstrating why commit history matters — reverting a bad config change by requesting a previous commit's label.

### Level 1 — Basic

Model reading configuration from the latest commit on the default branch, with no label awareness yet.

```java
import java.util.*;

public class GitBackendLevel1 {
    public static void main(String[] args) {
        GitRepo repo = new GitRepo();
        repo.commit("main", Map.of("db.pool.size", "10"));
        repo.commit("main", Map.of("db.pool.size", "50")); // a later commit, overwrites the file's content

        Map<String, String> latest = repo.latestOnBranch("main");
        System.out.println("Latest config on main: " + latest);
    }
}

class GitRepo {
    private final Map<String, List<Map<String, String>>> commitsByBranch = new HashMap<>();
    void commit(String branch, Map<String, String> content) {
        commitsByBranch.computeIfAbsent(branch, k -> new ArrayList<>()).add(content);
    }
    Map<String, String> latestOnBranch(String branch) {
        List<Map<String, String>> commits = commitsByBranch.get(branch);
        return commits.get(commits.size() - 1); // most recent commit's content
    }
}
```

How to run: `java GitBackendLevel1.java`

`latestOnBranch` only ever returns the most recent commit's content — there's no way yet to ask for an older snapshot, which is exactly what the `{label}` parameter and Git's tagging mechanism provide.

### Level 2 — Intermediate

Add label resolution: requesting a specific branch or tag, not just "whatever is latest."

```java
import java.util.*;

public class GitBackendLevel2 {
    public static void main(String[] args) {
        GitRepo repo = new GitRepo();
        repo.commit("main", Map.of("db.pool.size", "10"));
        repo.commit("main", Map.of("db.pool.size", "50"));
        repo.tag("release-2024-q3", repo.latestOnBranch("main")); // freeze a named snapshot

        repo.commit("main", Map.of("db.pool.size", "100")); // main keeps moving forward

        System.out.println("GET /payment-service/production (label=main) -> " + repo.resolve("main"));
        System.out.println("GET /payment-service/production/release-2024-q3 -> " + repo.resolve("release-2024-q3"));
    }
}

class GitRepo {
    private final Map<String, List<Map<String, String>>> commitsByBranch = new HashMap<>();
    private final Map<String, Map<String, String>> tags = new HashMap<>();

    void commit(String branch, Map<String, String> content) {
        commitsByBranch.computeIfAbsent(branch, k -> new ArrayList<>()).add(content);
    }
    Map<String, String> latestOnBranch(String branch) {
        List<Map<String, String>> commits = commitsByBranch.get(branch);
        return commits.get(commits.size() - 1);
    }
    void tag(String tagName, Map<String, String> snapshot) { tags.put(tagName, snapshot); }

    // Mirrors the Config Server resolving a {label} to either a branch's latest commit or a fixed tag.
    Map<String, String> resolve(String label) {
        if (tags.containsKey(label)) return tags.get(label);
        return latestOnBranch(label);
    }
}
```

How to run: `java GitBackendLevel2.java`

`resolve("main")` reflects `main`'s latest commit (`db.pool.size=100`), while `resolve("release-2024-q3")` returns the frozen snapshot taken *before* that last commit — the same repository, two different requested labels, two different results, exactly matching the `{label}` path segment in a real Config Server request URL.

### Level 3 — Advanced

Simulate a rollback: a bad configuration change goes out, and reverting to a previous commit (rather than manually reconstructing the prior state) fixes it — the actual operational payoff of Git-backed configuration history.

```java
import java.util.*;

public class GitBackendLevel3 {
    public static void main(String[] args) {
        GitRepo repo = new GitRepo();
        repo.commit("main", Map.of("db.pool.size", "10", "feature.newCheckout", "false"), "initial config");
        repo.commit("main", Map.of("db.pool.size", "50", "feature.newCheckout", "false"), "scale up pool size");
        repo.commit("main", Map.of("db.pool.size", "50", "feature.newCheckout", "true"), "enable new checkout -- BAD, causes errors");

        System.out.println("Current (broken) config: " + repo.resolve("main"));

        repo.revertToCommit("main", 1); // revert to the commit BEFORE the bad one, by index
        System.out.println("After revert, config: " + repo.resolve("main"));
        System.out.println("Commit history: " + repo.commitMessages("main"));
    }
}

class GitRepo {
    private final Map<String, List<Map<String, String>>> commitsByBranch = new HashMap<>();
    private final Map<String, List<String>> messagesByBranch = new HashMap<>();

    void commit(String branch, Map<String, String> content, String message) {
        commitsByBranch.computeIfAbsent(branch, k -> new ArrayList<>()).add(content);
        messagesByBranch.computeIfAbsent(branch, k -> new ArrayList<>()).add(message);
    }
    Map<String, String> resolve(String branch) {
        List<Map<String, String>> commits = commitsByBranch.get(branch);
        return commits.get(commits.size() - 1);
    }
    // A revert is itself a NEW commit whose content matches an earlier one -- history is preserved, not erased.
    void revertToCommit(String branch, int commitIndex) {
        Map<String, String> targetContent = commitsByBranch.get(branch).get(commitIndex);
        commit(branch, targetContent, "Revert to commit " + commitIndex);
    }
    List<String> commitMessages(String branch) { return messagesByBranch.get(branch); }
}
```

How to run: `java GitBackendLevel3.java`

`revertToCommit(repo, "main", 1)` doesn't delete the bad commit — it adds a *new* commit whose content matches commit index `1` (the pool-size-scaling commit, before the broken checkout flag was flipped), preserving the full history including the mistake, while making `resolve("main")` return to a known-good state.

## 6. Walkthrough

Execution starts in `main` for Level 3. Three commits build up: an initial config, a pool-size increase, and a bad commit enabling `feature.newCheckout` that causes errors. `repo.resolve("main")` at this point returns the broken state:

```
Current (broken) config: {db.pool.size=50, feature.newCheckout=true}
```

`repo.revertToCommit("main", 1)` looks up commit index `1` (the second commit, `{db.pool.size=50, feature.newCheckout=false}`) and adds it as a brand-new commit at the end of the branch's history — this is exactly what `git revert` does against a real repository: it doesn't rewrite history, it adds a new commit undoing the change. `resolve("main")` now reflects the reverted, known-good content:

```
After revert, config: {db.pool.size=50, feature.newCheckout=false}
Commit history: [initial config, scale up pool size, enable new checkout -- BAD, causes errors, Revert to commit 1]
```

Every step remains visible in `commitMessages` — the bad change, and the fact that it was reverted, are both permanent, reviewable parts of the history, unlike simply editing a mutable config file back to a previous value, which would leave no trace of what happened. In a real Spring Cloud Config setup, this same `git revert` workflow, applied to the actual config repository, is picked up by the Config Server on its next pull, then propagated to running services via the refresh mechanism from earlier cards.

## 7. Gotchas & takeaways

> Gotcha: the Config Server typically only picks up Git changes on its next scheduled pull (or on-demand via a webhook-triggered refresh), not instantly on every commit — a revert doesn't take effect for already-running services until that pull happens and each service's own refresh is triggered, meaning there's a real propagation delay to account for during an incident, not an instant fix.

> Gotcha: a Git backend pointed at a private repository needs credentials configured on the Config Server (SSH key, token, or username/password) — a misconfigured or expired credential causes the Config Server to silently fail to pull updates, serving stale configuration indefinitely until someone notices the pull failures in its logs.

- The Git backend is Spring Cloud Config Server's default and most common backend, treating branches and tags as the `{label}` clients can request.
- Configuration changes get full commit history, diff review, and rollback via standard Git operations — the same discipline already applied to application code.
- A revert adds a new commit rather than erasing history, preserving a full audit trail of both the mistake and its correction.
- Config Server pulls happen on a schedule or trigger, not instantly on every commit — there's a real propagation delay between a Git change and it taking effect on running services.

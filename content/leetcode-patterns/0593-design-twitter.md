---
card: leetcode-patterns
gi: 593
slug: design-twitter
title: Design Twitter
---

## 1. What it is

Design a `Twitter` class supporting `postTweet(userId, tweetId)` (post a tweet), `follow(followerId, followeeId)`, `unfollow(followerId, followeeId)`, and `getNewsFeed(userId)`, which returns the IDs of the **10 most recent tweets** from users that `userId` follows **and from `userId` themself**, ordered from most to least recent. Example: `postTweet(1, 5)`, `postTweet(1, 3)`, `follow(1, 2)`, `postTweet(2, 6)`, `getNewsFeed(1)` → `[6, 3, 5]` (tweet 6 from user 2 is newest, then user 1's own tweets, most recent first).

## 2. Why & when

The core challenge is merging multiple **already-sorted-by-time** tweet lists — one per followed user (plus the caller) — into a single feed, taking only the top 10 overall, without concatenating and fully sorting every tweet ever posted by every followed user. This "merge several sorted lists, take the top K" shape is exactly what a max-heap over "the current front of each list" solves.

## 3. Core concept

**Key idea:** store each user's tweets as a list of `(timestamp, tweetId)`, in the order posted (so the most recent is always at the end). Maintain a global increasing `timestamp` counter so tweets across different users can still be compared for recency. To build a feed, gather the relevant users (the caller plus everyone they follow), and run a **k-way merge**: push each relevant user's most recent tweet into a max-heap keyed by timestamp; repeatedly pop the overall newest, then push that same user's *next-most-recent* tweet (if any) to replace it, until 10 tweets are collected or the heap runs dry.

**Steps:**
1. `postTweet(userId, tweetId)`: append `(timestamp++, tweetId)` to `userTweets[userId]`.
2. `follow(followerId, followeeId)`: add `followeeId` to `followerId`'s follow set (a user implicitly always "follows" themself for feed purposes, so no explicit self-follow call is needed if you handle that case directly in `getNewsFeed`).
3. `unfollow(followerId, followeeId)`: remove `followeeId` from `followerId`'s follow set.
4. `getNewsFeed(userId)`: for `userId` and everyone they follow, if that user has any tweets, push a pointer to their most recent tweet (index = last) into a max-heap ordered by timestamp. Pop up to 10 times: each pop yields the next-newest tweet overall; after popping a user's tweet, if that user has an earlier tweet remaining, push it too. Collect the popped `tweetId`s in order.

**Why a heap, not sorting every candidate tweet:** if `userId` follows `f` users with `t` tweets each on average, sorting everything is O(f*t log(f*t)). The heap only ever holds at most `f` elements at once (one "current pointer" per relevant user) and does at most 10 pop-then-push cycles, costing O(f log f + 10 log f) — dramatically less work when each user has posted many tweets but the feed only needs the newest 10.

## 4. Diagram

<svg viewBox="0 0 700 190" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="A max-heap merging the current newest tweet from each followed user, popping the overall newest and replacing it with that user's next tweet">
  <g font-family="sans-serif" font-size="12">
    <text x="120" y="20" fill="#8b949e" text-anchor="middle">user 1's tweets (oldest -&gt; newest)</text>
    <rect x="20" y="30" width="80" height="30" fill="#161b22" stroke="#30363d"/><text x="60" y="50" fill="#e6edf3" text-anchor="middle" font-size="10">t=0: 5</text>
    <rect x="110" y="30" width="80" height="30" fill="#161b22" stroke="#3fb950"/><text x="150" y="50" fill="#e6edf3" text-anchor="middle" font-size="10">t=1: 3</text>
    <text x="480" y="20" fill="#8b949e" text-anchor="middle">user 2's tweets</text>
    <rect x="420" y="30" width="80" height="30" fill="#161b22" stroke="#3fb950"/><text x="460" y="50" fill="#e6edf3" text-anchor="middle" font-size="10">t=2: 6</text>
    <text x="350" y="110" fill="#79c0ff" text-anchor="middle">heap holds each user's newest pointer: (t=1,tweet3,user1), (t=2,tweet6,user2)</text>
    <text x="350" y="140" fill="#79c0ff" text-anchor="middle">pop (t=2,tweet6): result=[6]; push user2's next (none left)</text>
    <text x="350" y="165" fill="#79c0ff" text-anchor="middle">pop (t=1,tweet3): result=[6,3]; push user1's next -&gt; (t=0,tweet5)</text>
  </g>
</svg>

Only one "current" tweet per user sits in the heap at any time — popping the overall newest and refilling from that same user's next tweet performs the merge without ever sorting the full history.

## 5. Runnable example

**Level 1 — Brute force.** On every `getNewsFeed`, gather every tweet from every followed user into one list, sort it fully by timestamp descending, and take the first 10. O(total tweets from followed users x log(that count)) per call.

**KEY INSIGHT:** since each user's own tweet history is already sorted by time, merging several sorted lists to find just the top 10 needs only a max-heap over each list's current front — a full sort of everything is unnecessary extra work.

**Level 2 — Optimal.** Max-heap k-way merge over each relevant user's tweet list, capped at 10 pops.

**Level 3 — Hardened.** Treats a user as always following themself for feed purposes (without requiring an explicit `follow` call), and correctly stops early if fewer than 10 tweets exist in total among the relevant users.

```java
// Twitter.java
import java.util.*;

public class Twitter {

    private int timestamp = 0;
    private final Map<Integer, List<int[]>> userTweets = new HashMap<>(); // userId -> [(time, tweetId), ...]
    private final Map<Integer, Set<Integer>> follows = new HashMap<>();

    public void postTweet(int userId, int tweetId) {
        userTweets.computeIfAbsent(userId, k -> new ArrayList<>()).add(new int[]{timestamp++, tweetId});
    }

    public void follow(int followerId, int followeeId) {
        follows.computeIfAbsent(followerId, k -> new HashSet<>()).add(followeeId);
    }

    public void unfollow(int followerId, int followeeId) {
        Set<Integer> set = follows.get(followerId);
        if (set != null) set.remove(followeeId);
    }

    public List<Integer> getNewsFeed(int userId) {
        // heap entries: [timestamp, tweetId, ownerUserId, indexInOwnerList]
        PriorityQueue<int[]> heap = new PriorityQueue<>((a, b) -> b[0] - a[0]);

        Set<Integer> relevant = new HashSet<>(follows.getOrDefault(userId, Collections.emptySet()));
        relevant.add(userId);

        for (int uid : relevant) {
            List<int[]> tweets = userTweets.get(uid);
            if (tweets != null && !tweets.isEmpty()) {
                int lastIndex = tweets.size() - 1;
                int[] t = tweets.get(lastIndex);
                heap.offer(new int[]{t[0], t[1], uid, lastIndex});
            }
        }

        List<Integer> result = new ArrayList<>();
        while (!heap.isEmpty() && result.size() < 10) {
            int[] top = heap.poll();
            result.add(top[1]);
            int nextIndex = top[3] - 1;
            if (nextIndex >= 0) {
                List<int[]> tweets = userTweets.get(top[2]);
                int[] t = tweets.get(nextIndex);
                heap.offer(new int[]{t[0], t[1], top[2], nextIndex});
            }
        }
        return result;
    }

    public static void main(String[] args) {
        Twitter twitter = new Twitter();
        twitter.postTweet(1, 5);
        twitter.postTweet(1, 3);
        twitter.follow(1, 2);
        twitter.postTweet(2, 6);
        System.out.println(twitter.getNewsFeed(1)); // [6, 3, 5]
        twitter.unfollow(1, 2);
        System.out.println(twitter.getNewsFeed(1)); // [3, 5]
    }
}
```

**How to run:** save as `Twitter.java`, then run `java Twitter.java`.

## 6. Walkthrough

Trace `postTweet(1,5)`, `postTweet(1,3)`, `follow(1,2)`, `postTweet(2,6)`, `getNewsFeed(1)`:

1. After the posts: `userTweets = {1: [(0,5),(1,3)], 2: [(2,6)]}`. `follows = {1: {2}}`.
2. `getNewsFeed(1)`: `relevant = {1, 2}` (user `1` plus everyone they follow).
3. Seed the heap: user `1`'s newest is `(1,3)` (last element, index `1`); user `2`'s newest is `(2,6)` (index `0`). Heap: `[(1,3,user1,idx1), (2,6,user2,idx0)]`.
4. Pop the max by timestamp: `(2,6,user2,idx0)`. `result=[6]`. User `2` has no earlier tweet (`idx0-1=-1`), so nothing is pushed back.
5. Pop next: `(1,3,user1,idx1)`. `result=[6,3]`. User `1` has an earlier tweet at `idx0`: `(0,5)`. Push `(0,5,user1,idx0)`.
6. Pop next: `(0,5,user1,idx0)`. `result=[6,3,5]`. No earlier tweet for user `1`. Heap is now empty.
7. Return `[6,3,5]` — matches the expected feed order.

## 7. Gotchas & takeaways

> Gotcha: forgetting to always include `userId` themself in the `relevant` set (treating the feed as "only followed users") produces an incomplete feed — the problem requires a user's own tweets to always appear in their own feed, even without an explicit self-follow.

- Signal: "merge several already-sorted-by-time lists, keep only the top K overall" is a k-way-merge-with-a-heap signal, common whenever per-source data is naturally time-ordered.
- The heap only ever holds one "current pointer" per relevant source at a time — after popping, refill from that same source's next element, not from every source at once.
- Related problems: Merge k Sorted Lists (the same k-way-merge-via-heap idea, without the social-graph layer on top).

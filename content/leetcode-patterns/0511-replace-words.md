---
card: leetcode-patterns
gi: 511
slug: replace-words
title: Replace Words
---

## 1. What it is

Given a dictionary of root words and a sentence, replace every word in the sentence with its shortest root from the dictionary, if one exists as a prefix of that word (if multiple roots match, use the shortest). Example: roots `["cat", "bat", "rat"]`, sentence `"the cattle was rattled by the battery"` → `"the cat was rat by the bat"`.

## 2. Why & when

"Replace a word with its shortest matching root prefix" is a direct trie prefix-search problem, part of the [trie signal](0505-trie-signal-prefix-search-word-dictionaries-or-bit-tries.md) family — insert every root into a trie, then for each word in the sentence, walk the trie character by character and stop at the *first* end-of-word marker found (which is automatically the shortest matching root, since you stop as early as possible). Constraints: up to 1000 roots, up to 1000 words in the sentence.

## 3. Core concept

**Key idea:** insert every root word into a trie. For each word in the sentence, walk the trie one character at a time; the moment you reach a node marked `isEnd`, you have found the shortest root that is a prefix of this word — stop immediately and use that root. If you walk the entire word without ever hitting an `isEnd` node, the word has no matching root and stays unchanged.

**Steps:**
1. Build a trie from every root in the dictionary.
2. Split the sentence into words.
3. For each word, walk the trie character by character, building up the prefix matched so far.
4. If at any point the current node is `isEnd`, stop and replace the word with the prefix matched so far.
5. If the walk runs out of trie nodes (a character has no matching child) or reaches the end of the word without ever hitting `isEnd`, keep the original word unchanged.
6. Join all (possibly replaced) words back into a sentence.

**Why stopping at the *first* `isEnd` gives the shortest root:** walking the trie character by character visits nodes in order of increasing prefix length. The first `isEnd` encountered corresponds to the shortest root that matches — any root found later in the walk would necessarily be longer.

## 4. Diagram

<svg viewBox="0 0 700 150" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Walking a trie of roots and stopping at the first end-of-word marker">
  <g font-family="sans-serif" font-size="13">
    <text x="20" y="20" fill="#e6edf3" font-weight="bold">roots = [cat, bat, rat]. word = "cattle"</text>
    <text x="20" y="45" fill="#8b949e">walk: c -&gt; a -&gt; t (isEnd=true, this is root "cat")</text>
    <text x="20" y="70" fill="#3fb950">stop here -&gt; replace "cattle" with "cat"</text>
    <text x="20" y="100" fill="#8b949e">word = "the" (no matching root): walk t -&gt; h -&gt; e, no isEnd ever hit -&gt; unchanged</text>
  </g>
</svg>

The walk stops at the first `isEnd` marker, which is always the shortest matching root.

## 5. Runnable example

```java
// ReplaceWords.java
public class ReplaceWords {

    static class TrieNode {
        TrieNode[] children = new TrieNode[26];
        boolean isEnd = false;
    }

    static class Trie {
        TrieNode root = new TrieNode();

        void insert(String word) {
            TrieNode node = root;
            for (char c : word.toCharArray()) {
                int index = c - 'a';
                if (node.children[index] == null) node.children[index] = new TrieNode();
                node = node.children[index];
            }
            node.isEnd = true;
        }

        // returns the shortest root prefix of word, or word itself if none found
        String shortestRoot(String word) {
            TrieNode node = root;
            StringBuilder prefix = new StringBuilder();
            for (char c : word.toCharArray()) {
                int index = c - 'a';
                if (node.children[index] == null) return word;
                node = node.children[index];
                prefix.append(c);
                if (node.isEnd) return prefix.toString();
            }
            return word;
        }
    }

    static String replaceWords(java.util.List<String> dictionary, String sentence) {
        Trie trie = new Trie();
        for (String root : dictionary) trie.insert(root);

        String[] words = sentence.split(" ");
        StringBuilder result = new StringBuilder();
        for (int i = 0; i < words.length; i++) {
            if (i > 0) result.append(" ");
            result.append(trie.shortestRoot(words[i]));
        }
        return result.toString();
    }

    public static void main(String[] args) {
        java.util.List<String> roots = java.util.Arrays.asList("cat", "bat", "rat");
        String sentence = "the cattle was rattled by the battery";
        System.out.println(replaceWords(roots, sentence));
        // "the cat was rat by the bat"
    }
}
```

**How to run:** save as `ReplaceWords.java`, then run `java ReplaceWords.java`.

## 6. Walkthrough

Trace `shortestRoot("cattle")` against the trie built from `["cat", "bat", "rat"]`:

| char | node before | action | prefix so far | isEnd? |
|---|---|---|---|---|
| c | root | move to c | "c" | false |
| a | c | move to a | "ca" | false |
| t | a | move to t | "cat" | **true** |

The walk stops at `"cat"` since `isEnd` is true there — the rest of `"cattle"` (`t`, `l`, `e`) is never examined. `"cattle"` is replaced with `"cat"`. The same process applied to every word in the sentence produces `"the cat was rat by the bat"`.

## 7. Gotchas & takeaways

> Gotcha: continuing the walk past the first `isEnd` (looking for a "better" or longer match) violates the "shortest root" requirement — the problem explicitly wants the shortest matching root, so stopping immediately at the first `isEnd` is correct, not premature.

- Building on the [trie signal](0505-trie-signal-prefix-search-word-dictionaries-or-bit-tries.md), the "shortest prefix match" requirement is answered simply by stopping at the first `isEnd` during the walk.
- A word with no matching root in the dictionary is left completely unchanged.
- Time: O(total dictionary characters) to build the trie, O(sentence length) to process every word — each word's walk is bounded by its own length.

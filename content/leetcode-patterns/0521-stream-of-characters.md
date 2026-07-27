---
card: leetcode-patterns
gi: 521
slug: stream-of-characters
title: Stream of Characters
---

## 1. What it is

Design a class `StreamChecker` that receives characters one at a time (via repeated calls to `query(letter)`) and, after each new character, reports whether any word from a given list is now a **suffix** of the stream seen so far. Example: words `["cd","f","kl"]`; feeding the stream `"a","b","c","d",...` eventually returns `true` right after `'d'` is fed (since `"cd"` is now a suffix of the stream).

## 2. Why & when

Checking "is any dictionary word a suffix of everything seen so far" is a suffix question, which becomes a prefix question if you reverse both the dictionary words and the direction you read the stream — the same reversal trick as [Short Encoding of Words](0517-short-encoding-of-words.md), from the [trie signal](0505-trie-signal-prefix-search-word-dictionaries-or-bit-tries.md) family. Constraints: up to 150,000 total query calls, up to 2000 words.

## 3. Core concept

**Key idea:** insert every word into a trie, but insert each word **reversed**. Keep a running buffer of the letters seen so far (or just the most recent characters, up to the longest word's length). On each `query(letter)`, prepend `letter` to the front of your mental "read direction" — equivalently, walk the trie starting from the *most recently added* character and moving backward through the stream, checking if this backward walk hits an `isEnd` node at any point.

**Steps:**
1. Insert every word, reversed, into a trie.
2. Maintain a list (or deque) of all characters seen so far, most recent easily accessible.
3. On `query(letter)`: append `letter` to the stream history.
4. Walk the trie starting from the root, using the stream's characters in reverse order (most recent first): for each step, if the current character has no matching trie child, stop and return `false`. If a matching child's node has `isEnd = true` at any point during this walk, return `true` immediately.
5. If the walk runs out of trie nodes without ever hitting `isEnd` (or the stream is shorter than needed), return `false`.

**Why walking backward through the stream against a *reversed* trie matches "is a word a suffix":** a suffix of the stream, read in the normal left-to-right direction, is the same sequence of characters as reading backward from the most recent character. Since the trie stores each word reversed, walking backward through the stream in trie-forward order lines up exactly with checking whether that backward-read sequence matches a (reversed) dictionary word — i.e., whether the original word is a suffix of the stream.

## 4. Diagram

<svg viewBox="0 0 700 150" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Walking backward through the stream against a trie of reversed dictionary words">
  <g font-family="sans-serif" font-size="13">
    <text x="20" y="20" fill="#e6edf3" font-weight="bold">words = [cd, f, kl], reversed = [dc, f, lk]</text>
    <text x="20" y="45" fill="#8b949e">stream so far: a, b, c, d (most recent = 'd')</text>
    <text x="20" y="70" fill="#8b949e">walk trie starting from most recent char backward: 'd' -&gt; matches root's child 'd'</text>
    <text x="20" y="95" fill="#3fb950">next backward char 'c' -&gt; matches 'd' node's child 'c', and this node is isEnd (word "dc") -&gt; found "cd" as a suffix</text>
    <text x="20" y="125" fill="#79c0ff">query returns true right after 'd' is fed</text>
  </g>
</svg>

Reading the stream backward against a trie of reversed words checks for a suffix match in one walk.

## 5. Runnable example

```java
// StreamChecker.java
import java.util.*;

public class StreamChecker {

    static class TrieNode {
        TrieNode[] children = new TrieNode[26];
        boolean isEnd = false;
    }

    private final TrieNode root = new TrieNode();
    private final StringBuilder stream = new StringBuilder();
    private final int maxWordLength;

    public StreamChecker(String[] words) {
        int maxLen = 0;
        for (String word : words) {
            maxLen = Math.max(maxLen, word.length());
            String reversed = new StringBuilder(word).reverse().toString();
            TrieNode node = root;
            for (char c : reversed.toCharArray()) {
                int index = c - 'a';
                if (node.children[index] == null) node.children[index] = new TrieNode();
                node = node.children[index];
            }
            node.isEnd = true;
        }
        this.maxWordLength = maxLen;
    }

    public boolean query(char letter) {
        stream.append(letter);
        // only the last maxWordLength characters can ever matter
        if (stream.length() > maxWordLength) {
            stream.delete(0, stream.length() - maxWordLength);
        }

        TrieNode node = root;
        for (int i = stream.length() - 1; i >= 0; i--) {
            int index = stream.charAt(i) - 'a';
            node = node.children[index];
            if (node == null) return false;
            if (node.isEnd) return true;
        }
        return false;
    }

    public static void main(String[] args) {
        StreamChecker checker = new StreamChecker(new String[]{"cd", "f", "kl"});
        char[] stream = {'a', 'b', 'c', 'd', 'e', 'f', 'g', 'h', 'i', 'j', 'k', 'l'};
        for (char c : stream) {
            System.out.println(c + " -> " + checker.query(c));
        }
    }
}
```

**How to run:** save as `StreamChecker.java`, then run `java StreamChecker.java`.

## 6. Walkthrough

Trace `query('d')` after the stream has received `a, b, c, d`, with `maxWordLength = 2` (the longest word, `"cd"`, has length 2):

| step | buffer kept (last 2 chars) | trie walk (backward through buffer) | result |
|---|---|---|---|
| after query('d') | "cd" | i=1 ('d'): root->d (not isEnd). i=0 ('c'): d->c (isEnd=true, word "dc" = reverse of "cd") | **true** |

The method returns `true` right after `'d'` is fed, since `"cd"` is now a suffix of the stream `"abcd"`.

## 7. Gotchas & takeaways

> Gotcha: keeping the *entire* stream history without trimming it to the longest word's length wastes memory and time as the stream grows arbitrarily long — since no word can be longer than `maxWordLength`, only that many trailing characters can ever matter for any future suffix check.

- Reversing both the stored words and the stream-reading direction turns a suffix check into a standard forward trie walk, the same trick used in [Short Encoding of Words](0517-short-encoding-of-words.md).
- Trimming the buffer to the longest word's length keeps each `query` call's cost bounded, regardless of how many characters have streamed in total.
- Time: O(longest word length) per `query` call, after O(total characters across all words) to build the trie.

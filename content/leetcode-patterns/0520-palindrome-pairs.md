---
card: leetcode-patterns
gi: 520
slug: palindrome-pairs
title: Palindrome Pairs
---

## 1. What it is

Given a list of distinct `words`, find every pair of indices `(i, j)` (with `i != j`) such that concatenating `words[i] + words[j]` forms a palindrome. Example: `words = ["abcd","dcba","lls","s","sssll"]` → the four pairs `[0,1]`, `[1,0]`, `[3,2]`, `[2,4]` (order of the pairs in the output does not matter).

## 2. Why & when

Checking every pair directly is O(n² · L) (n words, average length L). Instead, for each word, only a handful of specific splits need checking, and finding "does the reverse of this specific piece exist in the dictionary" is a trie lookup — part of the [trie signal](0505-trie-signal-prefix-search-word-dictionaries-or-bit-tries.md) family. Constraints: up to 5000 words, each up to 300 characters.

## 3. Core concept

**Key idea:** for `words[i] + words[j]` to be a palindrome, split `words[i]` at every possible position into a `left` part and a `right` part. Two cases produce a valid pair:

1. **`left` is a palindrome and `right`, reversed, exists in the dictionary as `words[j]`.** Then `words[j] + words[i] = reverse(right) + left + right`. Since `left` is a palindrome, this reads the same forwards and backwards (the reversed `right` cancels with the `right` at the very end, and the palindromic `left` handles the middle).
2. **`right` is a palindrome and `left`, reversed, exists in the dictionary as `words[j]`.** Then `words[i] + words[j] = left + right + reverse(left)`, which is a palindrome by the same logic, mirrored.

A trie storing the **reversed** form of every word lets you look up "does the reverse of this piece exist" in O(piece length), instead of scanning the whole dictionary.

**Steps:**
1. Insert the reversed form of every word into a trie, storing the original word's index at each `isEnd` node.
2. For each word `words[i]`, split it at every position `k` from `0` to `words[i].length()` into `left = words[i][0..k)` and `right = words[i][k..)`.
3. If `left` is a palindrome, look up `reverse(right)` in the trie (via the reversed-word trie, this is a lookup of `right` walked in forward order); if found (and the found word's index is not `i`), record the pair `(foundIndex, i)`.
4. If `right` is a palindrome and non-empty (avoiding double-counting the empty-suffix case already covered by step 3 when `k = length`), look up `reverse(left)`; if found (and not `i`), record `(i, foundIndex)`.
5. Collect all pairs found across every word and every split position.

**Why storing the *reversed* word in the trie turns the lookup into a forward walk:** you need "does `reverse(piece)` exist in the dictionary." If the trie holds every word already reversed, walking the trie with `piece`'s own (non-reversed) characters, in order, is exactly equivalent to checking whether `reverse(piece)` matches some original word — no reversal needed at lookup time, only once, when building the trie.

## 4. Diagram

<svg viewBox="0 0 700 170" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Splitting a word into a palindromic part and a part whose reverse must exist in the dictionary">
  <g font-family="sans-serif" font-size="13">
    <text x="20" y="20" fill="#e6edf3" font-weight="bold">words[i] = "lls", split at k=2: left="ll", right="s"</text>
    <text x="20" y="45" fill="#8b949e">"ll" is a palindrome. look up reverse("s") = "s" in the dictionary.</text>
    <text x="20" y="70" fill="#3fb950">"s" exists at index 3 -&gt; pair (3, i): "s" + "lls" = "slls" (palindrome)</text>
    <text x="20" y="100" fill="#8b949e">words[i] = "sssll", split at k=2: left="ss", right="sll"</text>
    <text x="20" y="125" fill="#3fb950">"ss" is a palindrome. reverse("sll")="lls" exists at index 2 -&gt; pair (2, i)</text>
  </g>
</svg>

Splitting at every position and checking the palindrome half against a reversed-word trie finds every valid pair.

## 5. Runnable example

```java
// PalindromePairs.java
import java.util.*;

public class PalindromePairs {

    static class TrieNode {
        TrieNode[] children = new TrieNode[26];
        int wordIndex = -1;
    }

    static boolean isPalindrome(String s, int start, int end) {
        int left = start, right = end - 1;
        while (left < right) {
            if (s.charAt(left) != s.charAt(right)) return false;
            left++; right--;
        }
        return true;
    }

    static List<List<Integer>> palindromePairs(String[] words) {
        TrieNode root = new TrieNode();
        for (int i = 0; i < words.length; i++) {
            String reversed = new StringBuilder(words[i]).reverse().toString();
            TrieNode node = root;
            for (char c : reversed.toCharArray()) {
                int index = c - 'a';
                if (node.children[index] == null) node.children[index] = new TrieNode();
                node = node.children[index];
            }
            node.wordIndex = i;
        }

        List<List<Integer>> result = new ArrayList<>();
        for (int i = 0; i < words.length; i++) {
            String word = words[i];
            int n = word.length();
            for (int k = 0; k <= n; k++) {
                if (isPalindrome(word, 0, k)) {
                    int foundIndex = search(root, word, k, n);
                    if (foundIndex != -1 && foundIndex != i) {
                        result.add(Arrays.asList(foundIndex, i));
                    }
                }
                if (k < n && isPalindrome(word, k, n)) {
                    int foundIndex = search(root, word, 0, k);
                    if (foundIndex != -1 && foundIndex != i) {
                        result.add(Arrays.asList(i, foundIndex));
                    }
                }
            }
        }
        return result;
    }

    // walks the reversed-word trie using word[start..end) in forward order
    static int search(TrieNode root, String word, int start, int end) {
        TrieNode node = root;
        for (int idx = start; idx < end; idx++) {
            int index = word.charAt(idx) - 'a';
            if (node.children[index] == null) return -1;
            node = node.children[index];
        }
        return node.wordIndex;
    }

    public static void main(String[] args) {
        String[] words = {"abcd", "dcba", "lls", "s", "sssll"};
        System.out.println(palindromePairs(words));
    }
}
```

**How to run:** save as `PalindromePairs.java`, then run `java PalindromePairs.java`.

## 6. Walkthrough

Trace the splits for `words[2] = "lls"` (index 2), `n = 3`:

| k | left="lls"[0..k) | right="lls"[k..) | left is palindrome? | right is palindrome? | lookup | pair found |
|---|---|---|---|---|---|---|
| 0 | "" | "lls" | yes (empty) | no | search "lls" (reverse("")="") — no match for whole word here | — |
| 1 | "l" | "ls" | yes | no | — | — |
| 2 | "ll" | "s" | yes | (k<n, check right="s") yes | search "s" (right, k=2..3) → index 3 (word "s") | pair (3, 2) |
| 3 | "lls" | "" | no | (k==n, skip right check) | — | — |

At `k=2`: `left="ll"` is a palindrome, so the code looks up `reverse(right)` — walking the reversed-word trie forward with `right="s"` finds word index `3` (`"s"`), giving pair `(3, 2)`: `words[3] + words[2] = "s" + "lls" = "slls"`, a palindrome.

## 7. Gotchas & takeaways

> Gotcha: forgetting to skip the `right`-is-palindrome check when `k == n` (i.e., `right` is empty) can cause the empty-suffix case to be checked twice, potentially adding a duplicate pair — the code guards this with `k < n` before checking `right`.

- Reversing every word once, at trie-build time, turns every "does `reverse(piece)` exist" query into a plain forward trie walk.
- Checking both "left is a palindrome" and "right is a palindrome" at every split position covers both orders the pair could form (`found+i` and `i+found`).
- Time: O(total characters across all words × average word length) — building the trie is O(total characters); each word's L+1 split checks each cost O(L) for the palindrome check and trie walk.

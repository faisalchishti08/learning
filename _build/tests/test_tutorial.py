import os, sys, unittest
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
import tutorial

GOOD_BODY = """## 1. What it is
It is a thing explained simply.

## 2. Why & when
Because reasons.

## 3. Core concept
The mechanism in depth.

## 4. Diagram
<svg viewBox="0 0 10 10"><rect/></svg>

## 5. Runnable example
```js
console.log("hi");
```

## 6. Walkthrough
Line 1 logs hi to the console, which proves it runs.

## 7. Gotchas & takeaways
- Watch out for this.
"""

FULL = "---\ncard: webdev\ngi: 1\nslug: x\ntitle: X\n---\n\n" + GOOD_BODY

class TestTutorial(unittest.TestCase):
    def test_parse_front_matter(self):
        fm, body = tutorial.parse(FULL)
        self.assertEqual(fm["card"], "webdev")
        self.assertEqual(fm["title"], "X")
        self.assertTrue(body.lstrip().startswith("## 1. What it is"))

    def test_lint_passes_good(self):
        fm, body = tutorial.parse(FULL)
        self.assertEqual(tutorial.lint(fm, body), [])

    def test_lint_missing_heading(self):
        fm, body = tutorial.parse(FULL.replace("## 7. Gotchas & takeaways", "## 7. Wrong"))
        self.assertTrue(any("7. Gotchas" in e for e in tutorial.lint(fm, body)))

    def test_lint_no_code_in_example(self):
        broken = FULL.replace('```js\nconsole.log("hi");\n```', "no code here")
        fm, body = tutorial.parse(broken)
        self.assertTrue(any("code block" in e for e in tutorial.lint(fm, body)))

    def test_lint_placeholder(self):
        fm, body = tutorial.parse(FULL.replace("Because reasons.", "TODO fill in"))
        self.assertTrue(any("placeholder" in e for e in tutorial.lint(fm, body)))

    def test_lint_missing_front_matter_key(self):
        fm, body = tutorial.parse(FULL.replace("title: X\n", ""))
        self.assertTrue(any("title" in e for e in tutorial.lint(fm, body)))

if __name__ == "__main__":
    unittest.main()

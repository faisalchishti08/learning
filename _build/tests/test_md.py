import os, sys, unittest
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
import md

class TestMd(unittest.TestCase):
    def test_heading(self):
        self.assertIn("<h2>Hello</h2>", md.convert("## Hello"))

    def test_paragraph_inline(self):
        out = md.convert("This is **bold** and `code` and _em_.")
        self.assertIn("<strong>bold</strong>", out)
        self.assertIn("<code>code</code>", out)
        self.assertIn("<em>em</em>", out)

    def test_fenced_code_is_escaped_and_tagged(self):
        out = md.convert("```js\nconst x = a < b && c > d;\n```")
        self.assertIn('<pre><code class="lang-js">', out)
        self.assertIn("a &lt; b &amp;&amp; c &gt; d", out)

    def test_inline_code_not_formatted_inside(self):
        out = md.convert("use `a**b**c` here")
        self.assertIn("<code>a**b**c</code>", out)

    def test_unordered_list(self):
        out = md.convert("- one\n- two")
        self.assertIn("<ul><li>one</li><li>two</li></ul>", out)

    def test_ordered_list(self):
        out = md.convert("1. first\n2. second")
        self.assertIn("<ol><li>first</li><li>second</li></ol>", out)

    def test_table(self):
        out = md.convert("| A | B |\n|---|---|\n| 1 | 2 |")
        self.assertIn("<table>", out)
        self.assertIn("<th>A</th>", out)
        self.assertIn("<td>1</td>", out)

    def test_blockquote(self):
        self.assertIn("<blockquote>note here</blockquote>", md.convert("> note here"))

    def test_link(self):
        self.assertIn('<a href="http://x.com">x</a>', md.convert("see [x](http://x.com)"))

    def test_raw_svg_passthrough(self):
        src = '<svg viewBox="0 0 10 10"><rect x="1" y="1"/></svg>'
        self.assertIn(src, md.convert(src))

    def test_multiline_svg_passthrough(self):
        src = '<svg>\n<rect/>\n</svg>'
        self.assertIn("<rect/>", md.convert(src))

if __name__ == "__main__":
    unittest.main()

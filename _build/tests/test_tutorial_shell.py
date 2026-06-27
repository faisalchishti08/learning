import os, sys, unittest
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
import tutorial_shell

META = {
    "title": "Semantic elements",
    "area": "Web Development",
    "section": "HTML",
    "gi": 7,
    "storage_key": "spring-checklist:webdev.html",
    "back_href": "../../webdev.html#sec-2",
}

class TestShell(unittest.TestCase):
    def setUp(self):
        self.html = tutorial_shell.render(
            META, "<h2>1. What it is</h2><pre><code>x</code></pre>",
            {"href": "0006-prev.html", "title": "Prev topic"},
            {"href": "0008-next.html", "title": "Next topic"})

    def test_is_full_document(self):
        self.assertTrue(self.html.lstrip().startswith("<!DOCTYPE html>"))

    def test_has_title_and_breadcrumb(self):
        self.assertIn("Semantic elements", self.html)
        self.assertIn("Web Development", self.html)
        self.assertIn("HTML", self.html)

    def test_uses_storage_key_and_id(self):
        self.assertIn("spring-checklist:webdev.html", self.html)
        self.assertIn('"t7"', self.html)

    def test_back_and_nav_links(self):
        self.assertIn("../../webdev.html#sec-2", self.html)
        self.assertIn("0006-prev.html", self.html)
        self.assertIn("0008-next.html", self.html)

    def test_copy_button_script_present(self):
        self.assertIn("clipboard", self.html)

    def test_self_contained_no_external(self):
        self.assertNotIn("http://", self.html)
        self.assertNotIn("https://", self.html)

    def test_body_injected(self):
        self.assertIn("1. What it is", self.html)

if __name__ == "__main__":
    unittest.main()

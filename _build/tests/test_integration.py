import os, sys, unittest
HERE = os.path.dirname(__file__)
BUILD = os.path.join(HERE, "..")
sys.path.insert(0, BUILD)
import shell

class TestShellLinks(unittest.TestCase):
    def test_links_render_anchor_when_present(self):
        data = [{"name": "S", "tag": "t", "groups": [{"g": "G", "items": ["Alpha", "Beta"]}]}]
        out = shell.render("T", "L", "sub", "k", data, links={1: "tutorials/x/0001-alpha.html"})
        self.assertIn('tutorials/x/0001-alpha.html', out)
        self.assertIn('const LINKS =', out)

    def test_no_links_param_still_works(self):
        data = [{"name": "S", "tag": "t", "groups": [{"g": "G", "items": ["Alpha"]}]}]
        out = shell.render("T", "L", "sub", "k", data)
        self.assertIn("const LINKS = {}", out)

if __name__ == "__main__":
    unittest.main()

"""Run: python3 tests/test_mdlite.py  (exits non-zero on failure)"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from mpsc_build.mdlite import render


def check(name, got, must_contain):
    for m in must_contain:
        if m not in got:
            print(f"FAIL {name}: missing {m!r} in {got!r}"); sys.exit(1)
    print("ok", name)


check("h2", render("## Overview"), ["<h2>Overview</h2>"])
check("h3", render("### Sub"), ["<h3>Sub</h3>"])
check("para", render("Hello world."), ["<p>Hello world.</p>"])
check("bold", render("a **b** c"), ["<strong>b</strong>"])
check("italic", render("a *b* c"), ["<em>b</em>"])
check("code", render("use `x` here"), ["<code>x</code>"])
check("ul", render("- one\n- two"), ["<ul>", "<li>one</li>", "<li>two</li>", "</ul>"])
check("ol", render("1. one\n2. two"), ["<ol>", "<li>one</li>", "</ol>"])
check("link", render("[g](http://x)"), ['<a href="http://x">g</a>'])
check("hr", render("---"), ["<hr>"])
check("blockquote", render("> note"), ["<blockquote>note</blockquote>"])
check("rawhtml", render("<table><tr><td>x</td></tr></table>"), ["<table><tr><td>x</td></tr></table>"])
check("escape", render("a < b & c"), ["a &lt; b &amp; c"])
print("ALL MDLITE TESTS PASSED")

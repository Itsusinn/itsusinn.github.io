"""Validate the built blog with the Python standard library only."""

import json
from datetime import datetime
from email.utils import parsedate_to_datetime
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import unquote, urljoin, urlsplit
from xml.etree import ElementTree


ROOT = Path(__file__).resolve().parents[1] / "site"
ORIGIN = "https://itsusinn.github.io/"
POSTS = {
    "p/linux-tips/": "Linux Tips",
    "p/java-secure-random/": "Java Secure Random",
}
PUBLISHED = {
    "Linux Tips": "2023-08-27T21:55:07+08:00",
    "Java Secure Random": "2023-08-23T00:12:51+08:00",
}


class Page(HTMLParser):
    def __init__(self, path):
        super().__init__(convert_charrefs=True)
        self.ids = set()
        self.links = []
        self.canonical = None
        self.html = path.read_text(encoding="utf-8")
        self.feed(self.html)

    def handle_starttag(self, tag, attributes):
        attributes = dict(attributes)
        if "id" in attributes:
            self.ids.add(attributes["id"])
        for key in ("href", "src"):
            if attributes.get(key):
                self.links.append(attributes[key])
        if tag == "link" and attributes.get("rel") == "canonical":
            self.canonical = attributes.get("href")


def check():
    assert ROOT.is_dir(), "Run just build first"
    pages = {path: Page(path) for path in ROOT.rglob("*.html")}
    errors = []
    for path, page in pages.items():
        relative = path.relative_to(ROOT).as_posix()
        url = urljoin(ORIGIN, relative.removesuffix("index.html"))
        for link in page.links:
            target = urlsplit(urljoin(url, link))
            if target.scheme not in ("http", "https") or target.netloc != urlsplit(ORIGIN).netloc:
                continue
            destination = ROOT / unquote(target.path).lstrip("/")
            if destination.is_dir():
                destination /= "index.html"
            if not destination.is_file():
                errors.append(f"{relative}: missing target {link}")
            elif target.fragment and destination in pages:
                if unquote(target.fragment) not in pages[destination].ids:
                    errors.append(f"{relative}: missing anchor {link}")
    assert not errors, "\n".join(errors)

    home = pages[ROOT / "index.html"]
    assert home.html.index('href="p/linux-tips/"') < home.html.index('href="p/java-secure-random/"'), "Posts must be newest first"
    assert "FileInputStream.readBytes" not in home.html, "Homepage should contain excerpts, not full posts"
    for route, title in POSTS.items():
        page = pages[ROOT / route / "index.html"]
        assert page.canonical == urljoin(ORIGIN, route), f"Changed post URL: {route}"
        assert title in page.html

    for route, titles in {
        "archives/2023/": POSTS.values(),
        "categories/linux/": ["Linux Tips"],
        "categories/java/": ["Java Secure Random"],
        "author/ihsin/": POSTS.values(),
    }.items():
        page = pages[ROOT / route / "index.html"]
        for title in titles:
            assert title in page.html, f"Missing {title} in {route}"

    for route, target in {"archives/": "", "search/": "", "post/": "", "support/": "links/"}.items():
        page = pages[ROOT / route / "index.html"]
        assert urljoin(urljoin(ORIGIN, route), page.canonical) == urljoin(ORIGIN, target), f"Broken redirect: {route}"
        assert 'http-equiv="refresh"' in page.html

    for filename in ("index.xml", "feed_rss_updated.xml"):
        items = ElementTree.parse(ROOT / filename).findall("./channel/item")
        links = [item.findtext("link") for item in items]
        for route in POSTS:
            assert urljoin(ORIGIN, route) in links, f"Missing post in {filename}: {route}"
        assert all(link.startswith(urljoin(ORIGIN, "p/")) for link in links), "RSS must contain only posts"
        assert len(links) == len(set(links)), "Duplicate RSS posts"
        for item in items:
            assert item.findtext("pubDate"), "RSS date missing"
            if filename == "index.xml" and item.findtext("title") in PUBLISHED:
                assert parsedate_to_datetime(item.findtext("pubDate")) == datetime.fromisoformat(PUBLISHED[item.findtext("title")]), "Original publication date changed"
            if item.findtext("title") == "Java Secure Random":
                assert "FileInputStream.readBytes" in item.findtext("description", ""), "RSS must contain full posts"

    search = json.loads((ROOT / "search.json").read_text(encoding="utf-8"))
    locations = {item["location"].split("#")[0] for item in search["items"]}
    assert set(POSTS) <= locations, "Posts missing from native search index"
    print(f"Validated {len(pages)} HTML pages: local links and anchors, legacy URLs, blog views, RSS and search.")


if __name__ == "__main__":
    check()

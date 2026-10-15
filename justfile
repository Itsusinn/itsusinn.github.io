# Run the same pinned Zensical release locally and in CI.
set windows-shell := ["powershell.exe", "-NoLogo", "-NoProfile", "-Command"]

zensical := "zensical==0.0.65"
python := "3.13"
# Windows has no system IANA timezone database.
tzdata := "tzdata==2025.2"

default:
    @just --list

# Preview the blog, including drafts, at http://127.0.0.1:8000/.
serve:
    uvx --python {{python}} --with {{tzdata}} {{zensical}} serve

# Build the complete static site in site/.
build:
    uvx --python {{python}} --with {{tzdata}} {{zensical}} build --clean

# Check generated links, blog views, and RSS after building.
check: build
    uv run --no-project --python {{python}} scripts/check_site.py

"""Tests for LeetCode URL parsing/normalization."""

import pytest

from app.urls import UrlError, parse_leetcode_url


def test_basic():
    slug, norm = parse_leetcode_url("https://leetcode.com/problems/two-sum")
    assert slug == "two-sum"
    assert norm == "https://leetcode.com/problems/two-sum/"


def test_trailing_slash_and_extra_path():
    slug, norm = parse_leetcode_url("https://leetcode.com/problems/two-sum/description/")
    assert slug == "two-sum"
    assert norm == "https://leetcode.com/problems/two-sum/"


def test_query_string_ignored():
    slug, _ = parse_leetcode_url("https://leetcode.com/problems/two-sum/?envType=study")
    assert slug == "two-sum"


def test_whitespace_trimmed():
    slug, _ = parse_leetcode_url("   https://leetcode.com/problems/two-sum/   ")
    assert slug == "two-sum"


def test_matches_real_data_urls():
    for url in [
        "https://leetcode.com/problems/remove-duplicates-from-sorted-array-ii/",
        "https://leetcode.com/problems/valid-palindrome/",
        "https://leetcode.com/problems/sort-colors/",
        "https://leetcode.com/problems/merge-sorted-array/",
    ]:
        slug, norm = parse_leetcode_url(url)
        assert norm == url  # already canonical


def test_rejects_www():
    with pytest.raises(UrlError):
        parse_leetcode_url("https://www.leetcode.com/problems/two-sum/")


def test_rejects_other_host():
    with pytest.raises(UrlError):
        parse_leetcode_url("https://example.com/problems/two-sum/")


def test_rejects_non_problem_path():
    with pytest.raises(UrlError):
        parse_leetcode_url("https://leetcode.com/contest/weekly-contest-1/")


def test_rejects_empty():
    with pytest.raises(UrlError):
        parse_leetcode_url("")

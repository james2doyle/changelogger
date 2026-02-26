"""Tests for the changelogger module."""

import json
import subprocess
from unittest.mock import MagicMock, patch

import pytest
import requests

from changelogger import (
    build_raw_changelog_url,
    check_url_exists,
    find_changelog,
    get_github_url_from_bugs,
    get_github_url_from_repo,
    parse_github_url,
    setup_logging,
    try_unpkg,
)


class TestSetupLogging:
    """Tests for setup_logging function."""

    def test_setup_logging_verbose(self) -> None:
        """Test that verbose mode sets DEBUG level."""
        import logging

        setup_logging(verbose=True)
        assert logging.getLogger().level == logging.DEBUG

    def test_setup_logging_quiet(self) -> None:
        """Test that non-verbose mode sets WARNING level."""
        import logging

        setup_logging(verbose=False)
        assert logging.getLogger().level == logging.WARNING


class TestCheckUrlExists:
    """Tests for check_url_exists function."""

    def test_url_exists_returns_true(self) -> None:
        """Test that a 200 response returns True."""
        with patch("changelogger.requests.head") as mock_head:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_head.return_value = mock_response

            result = check_url_exists("https://example.com/file.md")

            assert result is True
            mock_head.assert_called_once_with(
                "https://example.com/file.md",
                timeout=10,
                allow_redirects=True,
            )

    def test_url_not_found_returns_false(self) -> None:
        """Test that a 404 response returns False."""
        with patch("changelogger.requests.head") as mock_head:
            mock_response = MagicMock()
            mock_response.status_code = 404
            mock_head.return_value = mock_response

            result = check_url_exists("https://example.com/notfound.md")

            assert result is False

    def test_request_exception_returns_false(self) -> None:
        """Test that a request exception returns False."""
        with patch("changelogger.requests.head") as mock_head:
            mock_head.side_effect = requests.RequestException("Connection error")

            result = check_url_exists("https://example.com/file.md")

            assert result is False


class TestTryUnpkg:
    """Tests for try_unpkg function."""

    def test_unpkg_found(self) -> None:
        """Test that a valid unpkg URL is returned when changelog exists."""
        with patch("changelogger.check_url_exists") as mock_check:
            mock_check.return_value = True

            result = try_unpkg("lodash")

            assert result == "https://unpkg.com/lodash/CHANGELOG.md"
            mock_check.assert_called_once_with("https://unpkg.com/lodash/CHANGELOG.md")

    def test_unpkg_not_found(self) -> None:
        """Test that None is returned when changelog doesn't exist."""
        with patch("changelogger.check_url_exists") as mock_check:
            mock_check.return_value = False

            result = try_unpkg("some-package")

            assert result is None


class TestParseGithubUrl:
    """Tests for parse_github_url function."""

    def test_parse_simple_repo_url(self) -> None:
        """Test parsing a simple GitHub repo URL."""
        owner, repo, subpath = parse_github_url("https://github.com/owner/repo")

        assert owner == "owner"
        assert repo == "repo"
        assert subpath is None

    def test_parse_issues_url(self) -> None:
        """Test parsing a GitHub issues URL."""
        owner, repo, subpath = parse_github_url(
            "https://github.com/lorenzodejong/next-sanity-image/issues"
        )

        assert owner == "lorenzodejong"
        assert repo == "next-sanity-image"
        assert subpath is None

    def test_parse_tree_url_with_subpath(self) -> None:
        """Test parsing a GitHub tree URL with subdirectory."""
        owner, repo, subpath = parse_github_url(
            "https://github.com/sanity-io/plugins/tree/HEAD/plugins/sanity-plugin-iframe-pane"
        )

        assert owner == "sanity-io"
        assert repo == "plugins"
        assert subpath == "plugins/sanity-plugin-iframe-pane"

    def test_parse_tree_url_with_main_branch(self) -> None:
        """Test parsing a GitHub tree URL with main branch."""
        owner, repo, subpath = parse_github_url(
            "https://github.com/org/repo/tree/main/packages/subpackage"
        )

        assert owner == "org"
        assert repo == "repo"
        assert subpath == "packages/subpackage"

    def test_non_github_url_raises_error(self) -> None:
        """Test that non-GitHub URLs raise ValueError."""
        with pytest.raises(ValueError, match="Unsupported host"):
            parse_github_url("https://gitlab.com/owner/repo")

    def test_invalid_github_url_raises_error(self) -> None:
        """Test that invalid GitHub URLs raise ValueError."""
        with pytest.raises(ValueError, match="Invalid GitHub URL format"):
            parse_github_url("https://github.com/owner")


class TestBuildRawChangelogUrl:
    """Tests for build_raw_changelog_url function."""

    def test_build_url_without_subpath(self) -> None:
        """Test building URL without subpath."""
        url = build_raw_changelog_url("owner", "repo", "main")

        assert (
            url
            == "https://raw.githubusercontent.com/owner/repo/refs/heads/main/CHANGELOG.md"
        )

    def test_build_url_with_subpath(self) -> None:
        """Test building URL with subpath."""
        url = build_raw_changelog_url(
            "sanity-io", "plugins", "main", "plugins/sanity-plugin-iframe-pane"
        )

        assert url == (
            "https://raw.githubusercontent.com/sanity-io/plugins/refs/heads/main/"
            "plugins/sanity-plugin-iframe-pane/CHANGELOG.md"
        )

    def test_build_url_with_master_branch(self) -> None:
        """Test building URL with master branch."""
        url = build_raw_changelog_url("owner", "repo", "master")

        assert (
            url
            == "https://raw.githubusercontent.com/owner/repo/refs/heads/master/CHANGELOG.md"
        )


class TestGetGithubUrlFromBugs:
    """Tests for get_github_url_from_bugs function."""

    def test_bugs_url_found(self) -> None:
        """Test that bugs URL is returned when available."""
        npm_output = json.dumps(
            {
                "name": "test-package",
                "bugs": {"url": "https://github.com/owner/repo/issues"},
            }
        )

        with patch("changelogger.subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(
                returncode=0,
                stdout=npm_output,
                stderr="",
            )

            result = get_github_url_from_bugs("test-package")

            assert result == "https://github.com/owner/repo/issues"

    def test_bugs_url_not_found(self) -> None:
        """Test that None is returned when bugs URL is not available."""
        npm_output = json.dumps({"name": "test-package"})

        with patch("changelogger.subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(
                returncode=0,
                stdout=npm_output,
                stderr="",
            )

            result = get_github_url_from_bugs("test-package")

            assert result is None

    def test_npm_command_fails(self) -> None:
        """Test that None is returned when npm command fails."""
        with patch("changelogger.subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(
                returncode=1,
                stdout="",
                stderr="npm ERR! 404",
            )

            result = get_github_url_from_bugs("nonexistent-package")

            assert result is None

    def test_npm_not_found(self) -> None:
        """Test that None is returned when npm is not installed."""
        with patch("changelogger.subprocess.run") as mock_run:
            mock_run.side_effect = FileNotFoundError("npm not found")

            result = get_github_url_from_bugs("test-package")

            assert result is None

    def test_npm_timeout(self) -> None:
        """Test that None is returned when npm times out."""
        with patch("changelogger.subprocess.run") as mock_run:
            mock_run.side_effect = subprocess.TimeoutExpired("npm", 30)

            result = get_github_url_from_bugs("test-package")

            assert result is None


class TestGetGithubUrlFromRepo:
    """Tests for get_github_url_from_repo function."""

    def test_repo_url_found(self) -> None:
        """Test that repo URL is returned when available."""
        with patch("changelogger.subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(
                returncode=0,
                stdout="https://github.com/sanity-io/plugins/tree/HEAD/plugins/sanity-plugin-iframe-pane\n",
                stderr="",
            )

            result = get_github_url_from_repo("sanity-plugin-iframe-pane")

            assert (
                result
                == "https://github.com/sanity-io/plugins/tree/HEAD/plugins/sanity-plugin-iframe-pane"
            )

    def test_repo_url_with_extra_output(self) -> None:
        """Test that repo URL is extracted even with extra output lines."""
        with patch("changelogger.subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(
                returncode=0,
                stdout="Some extra line\nhttps://github.com/owner/repo\n",
                stderr="",
            )

            result = get_github_url_from_repo("test-package")

            assert result == "https://github.com/owner/repo"

    def test_npm_repo_fails(self) -> None:
        """Test that None is returned when npm repo fails."""
        with patch("changelogger.subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(
                returncode=1,
                stdout="",
                stderr="npm ERR!",
            )

            result = get_github_url_from_repo("nonexistent-package")

            assert result is None


class TestFindChangelog:
    """Tests for find_changelog function."""

    def test_finds_changelog_via_unpkg(self) -> None:
        """Test that changelog is found via unpkg (Option 1)."""
        with patch("changelogger.try_unpkg") as mock_unpkg:
            mock_unpkg.return_value = "https://unpkg.com/lodash/CHANGELOG.md"

            result = find_changelog("lodash")

            assert result == "https://unpkg.com/lodash/CHANGELOG.md"
            mock_unpkg.assert_called_once_with("lodash")

    def test_finds_changelog_via_bugs_url(self) -> None:
        """Test that changelog is found via bugs URL (Option 2)."""
        with (
            patch("changelogger.try_unpkg") as mock_unpkg,
            patch("changelogger.get_github_url_from_bugs") as mock_bugs,
            patch("changelogger.check_url_exists") as mock_check,
        ):
            mock_unpkg.return_value = None
            mock_bugs.return_value = "https://github.com/owner/repo/issues"
            mock_check.return_value = True

            result = find_changelog("test-package")

            assert (
                result
                == "https://raw.githubusercontent.com/owner/repo/refs/heads/main/CHANGELOG.md"
            )

    def test_finds_changelog_via_repo_with_subpath(self) -> None:
        """Test that changelog is found via repo URL with subpath (Option 3)."""
        with (
            patch("changelogger.try_unpkg") as mock_unpkg,
            patch("changelogger.get_github_url_from_bugs") as mock_bugs,
            patch("changelogger.get_github_url_from_repo") as mock_repo,
            patch("changelogger.check_url_exists") as mock_check,
        ):
            mock_unpkg.return_value = None
            mock_bugs.return_value = None
            mock_repo.return_value = "https://github.com/sanity-io/plugins/tree/HEAD/plugins/sanity-plugin-iframe-pane"
            mock_check.return_value = True

            result = find_changelog("sanity-plugin-iframe-pane")

            expected = (
                "https://raw.githubusercontent.com/sanity-io/plugins/refs/heads/main/"
                "plugins/sanity-plugin-iframe-pane/CHANGELOG.md"
            )
            assert result == expected

    def test_falls_back_to_master_branch(self) -> None:
        """Test that master branch is tried when main branch fails."""
        with (
            patch("changelogger.try_unpkg") as mock_unpkg,
            patch("changelogger.get_github_url_from_bugs") as mock_bugs,
            patch("changelogger.check_url_exists") as mock_check,
        ):
            mock_unpkg.return_value = None
            mock_bugs.return_value = "https://github.com/owner/repo/issues"
            # First call (main) fails, second call (master) succeeds
            mock_check.side_effect = [False, True]

            result = find_changelog("test-package")

            assert (
                result
                == "https://raw.githubusercontent.com/owner/repo/refs/heads/master/CHANGELOG.md"
            )

    def test_returns_none_when_not_found(self) -> None:
        """Test that None is returned when no changelog is found."""
        with (
            patch("changelogger.try_unpkg") as mock_unpkg,
            patch("changelogger.get_github_url_from_bugs") as mock_bugs,
            patch("changelogger.get_github_url_from_repo") as mock_repo,
        ):
            mock_unpkg.return_value = None
            mock_bugs.return_value = None
            mock_repo.return_value = None

            result = find_changelog("nonexistent-package")

            assert result is None

    def test_handles_non_github_bugs_url(self) -> None:
        """Test that non-GitHub bugs URLs are handled gracefully."""
        with (
            patch("changelogger.try_unpkg") as mock_unpkg,
            patch("changelogger.get_github_url_from_bugs") as mock_bugs,
            patch("changelogger.get_github_url_from_repo") as mock_repo,
        ):
            mock_unpkg.return_value = None
            mock_bugs.return_value = "https://gitlab.com/owner/repo/issues"
            mock_repo.return_value = None

            # Should not raise, should return None
            result = find_changelog("gitlab-package")

            assert result is None


class TestMain:
    """Tests for main function."""

    def test_main_with_single_package(self, capsys: pytest.CaptureFixture[str]) -> None:
        """Test main function with a single package."""
        with (
            patch("changelogger.find_changelog") as mock_find,
            patch("sys.argv", ["changelogger", "lodash"]),
        ):
            mock_find.return_value = "https://unpkg.com/lodash/CHANGELOG.md"

            from changelogger import main

            main()

            captured = capsys.readouterr()
            assert "https://unpkg.com/lodash/CHANGELOG.md" in captured.out

    def test_main_with_not_found(self, capsys: pytest.CaptureFixture[str]) -> None:
        """Test main function when changelog is not found."""
        with (
            patch("changelogger.find_changelog") as mock_find,
            patch("sys.argv", ["changelogger", "nonexistent"]),
        ):
            mock_find.return_value = None

            from changelogger import main

            main()

            captured = capsys.readouterr()
            assert "nonexistent: CHANGELOG.md not found" in captured.err

    def test_main_with_multiple_packages(
        self, capsys: pytest.CaptureFixture[str]
    ) -> None:
        """Test main function with multiple packages."""
        with (
            patch("changelogger.find_changelog") as mock_find,
            patch("sys.argv", ["changelogger", "pkg1", "pkg2"]),
        ):
            mock_find.side_effect = [
                "https://unpkg.com/pkg1/CHANGELOG.md",
                "https://unpkg.com/pkg2/CHANGELOG.md",
            ]

            from changelogger import main

            main()

            captured = capsys.readouterr()
            assert "https://unpkg.com/pkg1/CHANGELOG.md" in captured.out
            assert "https://unpkg.com/pkg2/CHANGELOG.md" in captured.out

    def test_main_with_verbose_flag(self) -> None:
        """Test main function with verbose flag."""
        with (
            patch("changelogger.find_changelog") as mock_find,
            patch("changelogger.setup_logging") as mock_setup,
            patch("sys.argv", ["changelogger", "--verbose", "lodash"]),
        ):
            mock_find.return_value = "https://unpkg.com/lodash/CHANGELOG.md"

            from changelogger import main

            main()

            mock_setup.assert_called_once_with(True)

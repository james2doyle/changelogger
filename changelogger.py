#!/usr/bin/env python3
"""
Changelogger - Find CHANGELOG.md URLs for npm packages.

This script uses multiple methods to locate CHANGELOG.md files for npm packages:
1. Check unpkg.com directly for the CHANGELOG.md
2. Use npm view to get the bugs URL and construct a GitHub raw URL
3. Use npm repo to get the full repository path (handles nested packages)
4. Use npm outdated to get version info and return a GitHub compare URL
"""

import argparse
import json
import logging
import subprocess
import sys
from urllib.parse import urlparse

import requests
from packageurl import PackageURL

# Constants
UNPKG_BASE_URL = "https://unpkg.com"
RAW_GITHUB_BASE_URL = "https://raw.githubusercontent.com"
GITHUB_BASE_URL = "https://github.com"
CHANGELOG_FILENAME = "CHANGELOG.md"
DEFAULT_BRANCHES = ["main", "master"]
TAG_PREFIXES = ["", "v"]  # Try without prefix first, then with 'v'
REQUEST_TIMEOUT = 10

# Configure module-level logger
logger = logging.getLogger(__name__)


def setup_logging(verbose: bool) -> None:
    """
    Configure logging based on verbosity setting.

    Args:
        verbose: If True, set logging level to DEBUG; otherwise WARNING.
    """
    level = logging.DEBUG if verbose else logging.WARNING

    # Get root logger and configure it
    root_logger = logging.getLogger()
    root_logger.setLevel(level)

    # Only add handler if none exist
    if not root_logger.handlers:
        handler = logging.StreamHandler(sys.stderr)
        handler.setFormatter(logging.Formatter("%(levelname)s: %(message)s"))
        root_logger.addHandler(handler)


def check_url_exists(url: str) -> bool:
    """
    Check if a URL exists by sending a HEAD request.

    Args:
        url: The URL to check.

    Returns:
        True if the URL returns a 200 status code, False otherwise.
    """
    logger.debug(f"Checking URL exists: {url}")
    try:
        response = requests.head(url, timeout=REQUEST_TIMEOUT, allow_redirects=True)
        exists = response.status_code == 200
        logger.debug(
            f"URL {'exists' if exists else 'does not exist'} (status: {response.status_code})"
        )
        return exists
    except requests.RequestException as e:
        logger.debug(f"Request failed: {e}")
        return False


def try_unpkg(package_name: str) -> str | None:
    """
    Try to find CHANGELOG.md via unpkg.com (Option 1).

    Some packages publish their changelogs directly to npm, making them
    accessible via unpkg.com.

    Args:
        package_name: The npm package name.

    Returns:
        The unpkg URL if the CHANGELOG.md exists, None otherwise.
    """
    url = f"{UNPKG_BASE_URL}/{package_name}/{CHANGELOG_FILENAME}"
    logger.debug(f"Trying unpkg URL: {url}")

    if check_url_exists(url):
        logger.debug(f"Found CHANGELOG at unpkg: {url}")
        return url

    return None


def parse_github_url(url: str) -> tuple[str, str, str | None]:
    """
    Parse a GitHub URL to extract owner, repo, and optional subpath.

    Handles various GitHub URL formats:
    - https://github.com/owner/repo
    - https://github.com/owner/repo/issues
    - https://github.com/owner/repo/tree/HEAD/path/to/subdir

    Args:
        url: The GitHub URL to parse.

    Returns:
        A tuple of (owner, repo, subpath) where subpath may be None.

    Raises:
        ValueError: If the URL is not a valid GitHub URL.
    """
    parsed = urlparse(url)

    # Validate this is a GitHub URL
    if parsed.netloc != "github.com":
        raise ValueError(
            f"Unsupported host: {parsed.netloc}. Only GitHub URLs are supported."
        )

    # Remove leading slash and split path
    path_parts = parsed.path.strip("/").split("/")

    if len(path_parts) < 2:
        raise ValueError(f"Invalid GitHub URL format: {url}")

    owner = path_parts[0]
    repo = path_parts[1]

    # Check for subpath (e.g., /tree/HEAD/path/to/subdir)
    subpath: str | None = None
    if len(path_parts) > 2:
        # Handle /tree/BRANCH/subpath or /blob/BRANCH/subpath formats
        if path_parts[2] in ("tree", "blob") and len(path_parts) > 4:
            # Skip "tree" and branch name (e.g., "HEAD", "main")
            subpath = "/".join(path_parts[4:])
        # Handle /issues, /pulls, etc. - no subpath needed
        elif path_parts[2] in ("issues", "pulls", "actions", "wiki"):
            subpath = None

    logger.debug(f"Parsed GitHub URL: owner={owner}, repo={repo}, subpath={subpath}")
    return owner, repo, subpath


def build_raw_changelog_url(
    owner: str, repo: str, branch: str, subpath: str | None = None
) -> str:
    """
    Build a raw.githubusercontent.com URL for a CHANGELOG.md file.

    Args:
        owner: The GitHub repository owner.
        repo: The GitHub repository name.
        branch: The branch name (e.g., "main" or "master").
        subpath: Optional subdirectory path within the repository.

    Returns:
        The full URL to the raw CHANGELOG.md file.
    """
    if subpath:
        url = f"{RAW_GITHUB_BASE_URL}/{owner}/{repo}/refs/heads/{branch}/{subpath}/{CHANGELOG_FILENAME}"
    else:
        url = f"{RAW_GITHUB_BASE_URL}/{owner}/{repo}/refs/heads/{branch}/{CHANGELOG_FILENAME}"

    logger.debug(f"Built raw changelog URL: {url}")
    return url


def get_github_url_from_bugs(package_name: str) -> str | None:
    """
    Get GitHub URL from npm package bugs field (Option 2).

    Uses `npm view <package> --json` to get the bugs.url field,
    which typically points to the GitHub issues page.

    Args:
        package_name: The npm package name.

    Returns:
        The GitHub bugs URL if found, None otherwise.
    """
    logger.debug(f"Getting bugs URL for package: {package_name}")

    try:
        result = subprocess.run(
            ["npm", "view", package_name, "--json"],
            capture_output=True,
            text=True,
            timeout=30,
            check=False,
        )

        if result.returncode != 0:
            logger.debug(f"npm view failed: {result.stderr}")
            return None

        data = json.loads(result.stdout)
        bugs_url = data.get("bugs", {}).get("url")

        if bugs_url:
            logger.debug(f"Found bugs URL: {bugs_url}")
            return bugs_url

        logger.debug("No bugs URL found in package data")
        return None

    except subprocess.TimeoutExpired:
        logger.debug("npm view command timed out")
        return None
    except json.JSONDecodeError as e:
        logger.debug(f"Failed to parse npm view output: {e}")
        return None
    except FileNotFoundError:
        logger.debug("npm command not found")
        return None


def get_github_url_from_repo(package_name: str) -> str | None:
    """
    Get GitHub URL from npm repo command (Option 3).

    Uses `npm repo <package> --no-browser` to get the full repository URL,
    which handles nested packages within monorepos.

    Args:
        package_name: The npm package name.

    Returns:
        The GitHub repository URL if found, None otherwise.
    """
    logger.debug(f"Getting repo URL for package: {package_name}")

    try:
        result = subprocess.run(
            ["npm", "repo", package_name, "--no-browser"],
            capture_output=True,
            text=True,
            timeout=30,
            check=False,
        )

        if result.returncode != 0:
            logger.debug(f"npm repo failed: {result.stderr}")
            return None

        # The output may have a leading line we need to skip
        # Use sed '1d' equivalent - skip first line if there are multiple
        lines = result.stdout.strip().split("\n")

        # Find the line that looks like a URL
        for line in lines:
            line = line.strip()
            if line.startswith("http"):
                logger.debug(f"Found repo URL: {line}")
                return line

        logger.debug("No valid URL found in npm repo output")
        return None

    except subprocess.TimeoutExpired:
        logger.debug("npm repo command timed out")
        return None
    except FileNotFoundError:
        logger.debug("npm command not found")
        return None


def get_outdated_versions(package_name: str) -> tuple[str, str] | None:
    """
    Get current and latest versions for an outdated local package.

    Uses `npm outdated <package_name> --json` to determine if a locally
    installed package is outdated and returns the version information.

    Args:
        package_name: The npm package name.

    Returns:
        A tuple of (current_version, latest_version) if the package is
        outdated, None if the package is not installed, up to date, or
        if the npm command fails.
    """
    logger.debug(f"Getting outdated versions for package: {package_name}")

    try:
        result = subprocess.run(
            ["npm", "outdated", package_name, "--json"],
            capture_output=True,
            text=True,
            timeout=30,
            check=False,
        )

        # npm outdated returns exit code 1 when packages are outdated
        # and exit code 0 when all packages are up to date (empty output)
        if result.stdout.strip() == "" or result.stdout.strip() == "{}":
            logger.debug("Package is not installed or is up to date")
            return None

        data = json.loads(result.stdout)

        # Handle both regular and scoped package names in the output
        # The key in the JSON output is the package name without scope prefix issues
        package_data = data.get(package_name)
        if not package_data:
            # Try to find the package in the output (handles edge cases)
            for key, value in data.items():
                if key == package_name or key.endswith(f"/{package_name}"):
                    package_data = value
                    break

        if not package_data:
            logger.debug(f"Package {package_name} not found in outdated output")
            return None

        current = package_data.get("current")
        latest = package_data.get("latest")

        if not current or not latest:
            logger.debug("Missing current or latest version in output")
            return None

        if current == latest:
            logger.debug("Package is already up to date")
            return None

        logger.debug(f"Found outdated package: {current} -> {latest}")
        return (current, latest)

    except subprocess.TimeoutExpired:
        logger.debug("npm outdated command timed out")
        return None
    except json.JSONDecodeError as e:
        logger.debug(f"Failed to parse npm outdated output: {e}")
        return None
    except FileNotFoundError:
        logger.debug("npm command not found")
        return None


def build_compare_url(
    owner: str,
    repo: str,
    current_version: str,
    latest_version: str,
) -> str | None:
    """
    Build a GitHub compare URL for two versions.

    Tries both tag formats (with and without 'v' prefix) to find valid tags.

    Args:
        owner: The GitHub repository owner.
        repo: The GitHub repository name.
        current_version: The current installed version.
        latest_version: The latest available version.

    Returns:
        The compare URL if valid tags are found, None otherwise.
    """
    logger.debug(
        f"Building compare URL for {owner}/{repo}: {current_version}...{latest_version}"
    )

    for prefix in TAG_PREFIXES:
        current_tag = f"{prefix}{current_version}"
        latest_tag = f"{prefix}{latest_version}"
        compare_url = (
            f"{GITHUB_BASE_URL}/{owner}/{repo}/compare/{current_tag}...{latest_tag}"
        )

        logger.debug(f"Trying compare URL: {compare_url}")
        if check_url_exists(compare_url):
            logger.debug(f"Found valid compare URL: {compare_url}")
            return compare_url

    logger.debug("No valid compare URL found for any tag format")
    return None


def find_changelog(package_name: str) -> str | None:
    """
    Find the CHANGELOG.md URL for an npm package.

    Tries multiple methods in order:
    1. Check unpkg.com directly
    2. Use npm view bugs URL to construct GitHub raw URL
    3. Use npm repo to get full path (handles nested packages)
    4. Use npm outdated to get version info and return a GitHub compare URL

    For GitHub URLs, tries both 'main' and 'master' branches.
    For compare URLs, tries both tag formats ('1.0.0' and 'v1.0.0').

    Args:
        package_name: The npm package name.

    Returns:
        The URL to the CHANGELOG.md or compare URL if found, None otherwise.
    """
    logger.debug(f"Finding changelog for package: {package_name}")

    # Create a PackageURL for proper npm package handling
    try:
        purl = PackageURL(type="npm", name=package_name)
        logger.debug(f"Package URL: {purl.to_string()}")
    except ValueError as e:
        logger.debug(f"Invalid package name: {e}")

    # Cache owner/repo for Option 4 fallback
    cached_owner: str | None = None
    cached_repo: str | None = None

    # Option 1: Try unpkg.com
    logger.debug("Trying Option 1: unpkg.com")
    unpkg_url = try_unpkg(package_name)
    if unpkg_url:
        return unpkg_url

    # Option 2: Try npm view bugs URL
    logger.debug("Trying Option 2: npm view bugs URL")
    bugs_url = get_github_url_from_bugs(package_name)
    if bugs_url:
        try:
            owner, repo, _ = parse_github_url(bugs_url)
            cached_owner, cached_repo = owner, repo
            # bugs URL doesn't have subpath info, so we try root
            for branch in DEFAULT_BRANCHES:
                changelog_url = build_raw_changelog_url(owner, repo, branch)
                if check_url_exists(changelog_url):
                    return changelog_url
        except ValueError as e:
            logger.debug(f"Failed to parse bugs URL: {e}")

    # Option 3: Try npm repo (handles nested packages)
    logger.debug("Trying Option 3: npm repo")
    repo_url = get_github_url_from_repo(package_name)
    if repo_url:
        try:
            owner, repo, subpath = parse_github_url(repo_url)
            cached_owner, cached_repo = owner, repo
            for branch in DEFAULT_BRANCHES:
                changelog_url = build_raw_changelog_url(owner, repo, branch, subpath)
                if check_url_exists(changelog_url):
                    return changelog_url
        except ValueError as e:
            logger.debug(f"Failed to parse repo URL: {e}")

    # Option 4: Try GitHub compare URL for outdated packages
    logger.debug("Trying Option 4: GitHub compare URL")
    if cached_owner and cached_repo:
        versions = get_outdated_versions(package_name)
        if versions:
            current_version, latest_version = versions
            compare_url = build_compare_url(
                cached_owner, cached_repo, current_version, latest_version
            )
            if compare_url:
                return compare_url

    logger.debug(f"No CHANGELOG.md found for package: {package_name}")
    return None


def main() -> None:
    """
    CLI entry point for changelogger.

    Parses command line arguments and finds CHANGELOG.md URLs for
    the specified npm packages.
    """
    parser = argparse.ArgumentParser(
        prog="changelogger",
        description="Find CHANGELOG.md URLs for npm packages.",
    )
    parser.add_argument(
        "packages",
        nargs="+",
        metavar="package",
        help="One or more npm package names",
    )
    parser.add_argument(
        "-v",
        "--verbose",
        action="store_true",
        help="Enable verbose logging output",
    )

    args = parser.parse_args()

    setup_logging(args.verbose)

    for package_name in args.packages:
        logger.debug(f"Processing package: {package_name}")
        changelog_url = find_changelog(package_name)

        if changelog_url:
            print(changelog_url)
        else:
            print(f"{package_name}: CHANGELOG.md not found", file=sys.stderr)


if __name__ == "__main__":
    main()

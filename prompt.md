# Changelogger

Changelogger is a python script that, given a list of npm package names, can turn them into the links to the raw CHANGELOG.md for that package.

## build details

- uses the latest python
- uses python typing
- uses uv for tooling
- uses basedpyright and ruff
- uses a pyproject
- uses tests for any functions
- comments code and uses docblock
- logging can be enabled with a `--verbose` flag

## how it works

Here are some options for finding the github repo page:

**Option 1**

Some packages publish their changelogs directly to `npm`, making them accessible via unpkg.com.

You can do a check to see if a package includes a CHANGELOG.md file:

`curl https://unpkg.com/<package-name>/CHANGELOG.md`

**Option 2**

This works by using the `npm` command to find the package github page and use that to build a URL to the raw CHANGELOG.md file.

`npm view next-sanity-image --json | jq '.bugs.url'`

This command returns the url to the `/issues` page for the github project.

This specific example returns this url: https://github.com/lorenzodejong/next-sanity-image/issues

The url to the changelog is: https://raw.githubusercontent.com/lorenzodejong/next-sanity-image/refs/heads/main/CHANGELOG.md

**Option 3**

This works by using the `npm` command to find the package github page and use that to build a URL to the raw CHANGELOG.md file.

This command is similar in that it should link to the full path to the source code. The benefit of this one is that it can link to nested packages within projects.

`npm repo sanity-plugin-iframe-pane --no-browser | sed '1d'`

This command returns: https://github.com/sanity-io/plugins/tree/HEAD/plugins/sanity-plugin-iframe-pane

The url that to the changelog is: https://raw.githubusercontent.com/sanity-io/plugins/refs/heads/main/plugins/sanity-plugin-iframe-pane/CHANGELOG.md

You can see how this url is much more complex when the package is nested. This is becoming more and more common.

If you had run this command:

`npm view sanity-plugin-iframe-pane --json | jq '.bugs.url'`

You would get this url: https://github.com/sanity-io/plugins/issues

As you can see, it would not give you the actual details you would need to get the changelog url given this is a nested package.

**Option 4**

Do a search using the Github REST API to find CHANGELOG.md file in the repo

First you need the name of the repo:

`npm view next-sanity --json | jq '.repository.url'`

This returns: "git+ssh://git@github.com/sanity-io/next-sanity.git"

To search for a CHANGELOG.md for this project would look like this:

https://github.com/search.json?q=repo%3Asanity-io%2Fnext-sanity%20changelog.md&type=code

The response looks like this:

```json
{
  "payload": {
    "header_redesign_enabled": true,
    "results": [
      {
        "path": "packages/next-sanity/CHANGELOG.md",
        "repo_id": 306368933,
        "repo_nwo": "sanity-io/next-sanity",
        "owner_id": 17177659,
        "commit_sha": "3c644fb1f309b73ac614762f37bfc2a0bc08f2dd",
        "ref_name": "refs/heads/main",
        "blob_sha": "afa62bb9e6caef9e08a15f59796bb395ed9d284f",
        "language_name": "Markdown",
        "language_id": 222,
        "has_language_id": true,
        "language_color": "#083fa1",
        "match_count": 1,
        "matched_symbols": [],
        "snippets": [
          {
            "lines": [
              "…anity/client` to `v3`, see its [CHANGELOG](https://github.com/sanity-io/client/blob/main/<mark>CHANGELOG.md</mark>#300) for details."
            ],
            "starting_line_number": 2815,
            "ending_line_number": 2816,
            "jump_to_line_number": 2815,
            "format": "SNIPPET_FORMAT_HTML",
            "match_count": 1,
            "score": -1.0,
            "start": 208166,
            "end": 208285
          }
        ],
        "debug_info": {
          "retrieval_position": 0,
          "score": -5.260861396789551,
          "factors": []
        },
        "line_number": 2815,
        "term_matches": [
          {
            "start": 208255,
            "end": 208267
          }
        ],
        "duplicate_locations": [],
        "file_size": 209042,
        "enclosing_symbols": [],
        "path_term_matches": [
          {
            "start": 21,
            "end": 33
          }
        ],
        "repo_is_public": true,
        "repo_is_archived": false
      }
  ]
}
```

You can see that the path to a CHANGELOG.md file is in 'payload.results.0.path'

So the url to this file would be: https://raw.githubusercontent.com/sanity-io/next-sanity/refs/heads/main/<payload.results.0.path>

# The Script

Your job is to create a python script that can use these two methods to find a valid CHANGELOG.md.

The steps for this program are as follows:

1. someone runs `changelogger.py sanity-plugin-iframe-pane`
2. the program uses option 1 and some string manipulation to build a CHANGELOG.md url
3. a head request is sent to that generated url to the CHANGELOG.md to see if it exists
4. if it does exist, the url is returned
5. if it does not, option 2 is used to build the url
6. a head request is sent to that generated url to the CHANGELOG.md to see if it exists
7. if it does exist, repeat with option 3
7. if it does exist, repeat with option 4
8. if nothing is returned

See @README.md for the expected API

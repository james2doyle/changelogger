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

Use the following packages:
- https://github.com/package-url/packageurl-python
- https://requests.readthedocs.io/en/latest/api/


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
8. if nothing is returned

See @README.md for the expected API

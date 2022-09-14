# doi-jekyll: Create DOIs for Jekyll Blog Posts

`doi-jekyll` is a small Python tool to collect metadata of a Jekyll blog post and submit it to [DataCite Fabrica](https://doi.datacite.org/), minting a DOI for it. It is made for the [X-Dev Lab blog](https://x-dev.pages.jsc.fz-juelich.de/), but should work for any Jekyll-based blog (see `examples/` directory).

For a given blog post, the tool collects the metadata of the post, some metadata from the blog itself, and data from the author. It packages everything together in a dictionary following DataCite's Metadata Schema, converts it to XML (dicts are just much easier in Python), registers it with DataCite through the MDS API, and finally mints a DOI for it.

`doi-jekyll` is written with other installations in mind, but is only tested with the X-Dev Blog setup. There are some edge cases which are obvious, but currently not implemented, because there's yet no use case. Plenty of command line arguments are available to modify execution.

## Installation

Currently, no package on PyPI exists. Rather, directly install from GitHub

```bash
python3 -m pip install https://github.com/FZJ-JSC/doi-jekyll/archive/main.zip
```
(or better specify the most recent release.)

There are some dependencies, but nothing outworldly

## Usage

Relying on defaults, the usage boils down to

```bash
doi-jekyll _posts/2022-09-12-my-blogpost.md
```

Quite certainly, your Jekyll installation needs to be adapted.

* The blog post needs to contain some metadata in the YAML frontmatter for the DOI metadata, like `title`, `date`, `author`, `author`. And optionally `tags`, `license`, `abstract`, or `doi-additional-metadata`.
* The blog-wide Jekyll config, `_config.yml`, is located in the root of the blog. It also needs to contain blog-wide metadata, like `publisher`, `affiliation`, `provider_url`, `suffix_base`, `prefix` and optionally `doi` (for the DOI of the blog itself, will be a relational _parent_ (`isPartOf`) to the posts). All these keys need to be part of the `doi_jekyll` first-level key.
* A file for the author needs to exist with metadata like `name`, `firstname`, `lastname`, and `orcid_id`. The author file is automatically searched for in the `_authors/` directory (using the blog post's `author`), but can also be given via command line.

In addition, credentials to login to DataCite need to be given either via command line (`--user`, `--password`) or via environment variables (see `.env.sample.sh`). I recommend using the DataCite Test instance for testing by setting the according url as `provider_url` in `_config.yml`

## Command Line Arguments

While `doi-jekyll` is made to run with the default values, there are plenty of command line arguments to change execution, like `-vv` to get plenty of verbose information.

See all available command line arguments with

```bash
doi-jekyll -h
```

The command line switch `--additional-metadata` and the optional blog post frontmatter key `doi-additional-metadata` are _merged_ into the metadata dictionary recursively and can be used to extend the metadata post-specific. See `examples/`.
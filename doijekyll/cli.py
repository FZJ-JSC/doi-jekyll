#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
# Author: Andreas Herten, 2022
import os
import argparse

class CustomRawDescriptionArgumentDefaultsHelpFormatter(argparse.ArgumentDefaultsHelpFormatter, argparse.RawDescriptionHelpFormatter):
    pass
def parseArguments():
    """
    Parse CLI arguments.
    """
    parser = argparse.ArgumentParser(description='doi-jekyll: Parse Jekyll blog data to create DOIs via DataCite MDS. YAML Frontmatter of a post is the basis, augmented with blog-wide YAML configuration (in a "doi-jekyll" key) and author-specific data in an author-file.', epilog="""
Examples:
  $ doi-jekyll --dry-run -v _posts/2022-08-01-abcdef.md
  Dry-runs registration of a DOI with automatically extracted metadata with DataCite; will output some status information. Will not actually register a DOI. DataCite username and password are taken from environment variables.

  $ doi-jekyll -vvv -af _authors/stephen.md -c _configs/config.yml --skip-url _posts/2022-08-01-abcdef.md
  Registers DOI metadata with DataCite (not the actual DOI URL), extracting blog-wide infos from non-standard "_configs/config.yml" and author-related infos from "_authors/stephen.md" file, skipping automatic discovery of author file. Will print lots of debug output, including the full submitted XML.

      """, formatter_class=CustomRawDescriptionArgumentDefaultsHelpFormatter)
    parser.add_argument('blogpost', type=argparse.FileType('r'), nargs=1, help='Markdown file (with YAML Frontmatter) to create DOI for')
    parser.add_argument('-c', '--config', metavar='JEKYLL_CONFIG', help='Jekyll _config.yml', default='_config.yml', type=argparse.FileType('r'))
    parser.add_argument('-ad', '--authors-dir', help='Directory with Author Markdown file with YAML Frontmatter', default='_authors')
    parser.add_argument('-af', '--author-file', help='Markdown file with YAML Frontmatter')
    parser.add_argument('-f', '--force', help='Overwrite existing DOI in blogpost', action='store_true')
    parser.add_argument('-u', '--user', help='Username for DataCite. Can also be given by $DJ_DATACITE_USER, CLI takes precedence.', default=os.environ.get('DJ_DATACITE_USER', default=os.environ.get('DATACITE_USER', None)))
    parser.add_argument('-p', '--password', help='Password for DataCite. Can also be given by $DJ_DATACITE_PASSWORD, CLI takes precedence.', default=os.environ.get('DJ_DATACITE_PASSWORD', default=os.environ.get('DATACITE_PASSWORD', None)))
    parser.add_argument('--skip-url', help="Don't register URL for entry", action='store_true')
    parser.add_argument('-d', '--dry-run', help="Dry Run: Don't communicate anything with DataCite", action='store_true')
    parser.add_argument('-v', '--verbose', action='count', default=0, help="Increase verbosity via increasing logging levels. -v: WARNING, -vv: INFO, -vvv: DEBUG. May also be used by included Python packages (for example DEBUG is used by urllib3).")
    return parser.parse_args()
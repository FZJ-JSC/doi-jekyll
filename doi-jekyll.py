#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
# Author: Andreas Herten, 2022
import os
import sys
import json
import yaml
import base64
import datetime
import argparse
import logging
from pathlib import PurePath

import requests
import xmltodict
import frontmatter
import dateparser

class CustomRawDescriptionArgumentDefaultsHelpFormatter(argparse.ArgumentDefaultsHelpFormatter, argparse.RawDescriptionHelpFormatter):
    pass
def parseCredentials(username: str, password: str) -> str:
    if username is None:
        print("Please provide DataCite username (--user or  $DJ_DATACITE_USER)")
        exit()
    if password is None:
        print("Please provide DataCite password (--password or $DJ_DATACITE_PASSWORD)")
        exit()
    return username, password
def collectBlogData(file):
    """
    Collect global blog data, usually from Jekyll's _config.yaml.
    Data in a dedicated key, 'doi_jekyll' is only used.
    In addition, the base url of the entire blog is needed, as specified in the top-level 'url' key of Jekyll's configuration.
    """
    all_yaml = yaml.safe_load(file)
    doi_yaml = all_yaml['doi_jekyll']
    return {
        **doi_yaml,
        'url': all_yaml['url']
    }
def collectPostData(file):
    """Collect data from blog post file."""
    return frontmatter.loads(file.read())
def collectAuthorData(authorname: str, args):
    """
    Collect data from author file.
    Either directly take an author file as supplied by command line arguments, or search for `authorname` in the default/a specified directory.
    """
    if args.author_file:
        filename = args.author_file
    else:
        filename = PurePath(args.authors_dir, authorname.lower()).with_suffix('.md')
    return frontmatter.load(filename)
def genDoi(title: str, base: str, prefix: str) -> str:
    """
    Generate a DOI name.
    Use the first 6 characters of the base64-encoded title of a post as the last part of the suffix.
    Use the global blog identifier as the first part of the suffix (the `base`).
    Use the global prefix as the identifier before the slash.
    """
    import base64
    b64 = base64.b64encode(title.encode())
    b64_short = b64[0:6]
    return f'{prefix}/{base}-{b64_short.decode()}'
def parseLicense(data_post) -> dict:
    """
    Take a license short-name ('mit') and make the SPDX proper identifier form it, including an URL.
    Is not smart but will just look up the short-name. Needs to be extended for new licenses.
    """
    # could be extended via https://github.com/nexB/license-expression maybe
    if 'license' not in data_post:
        logging.warning(f'Note: No license specified!')
        return None
    else:
        match data_post['license'].lower():
            case 'mit':
                license='MIT'
                url='https://spdx.org/licenses/MIT.html'
            case 'cc0':
                license='CC0-1.0'
                url='https://creativecommons.org/publicdomain/zero/1.0/'
            case 'cc-by4':
                license='CC-BY-4.0'
                url='https://creativecommons.org/licenses/by/4.0/'
            case 'gpl3':
                license='GPL-3.0-only'
                url='https://opensource.org/licenses/GPL-3.0'
            case _:
                logging.error(f"License {data_post['license']} unknown. Please extend license-parsing in tool!")
                sys.exit()
        logging.debug(f'License {license} at {url}')
        return {
            '@schemeURI': 'https://spdx.org/licenses/',
            '@rightsIdentifierScheme': 'SPDX',
            '@rightsIdentifier': license,
            '@rightsURI': url
        }
def getMdSchema():
    return {
        '@xmlns:xsi': 'http://www.w3.org/2001/XMLSchema-instance',
        '@xmlns': 'http://datacite.org/schema/kernel-4',
        '@xsi:schemaLocation': 'http://datacite.org/schema/kernel-4 http://schema.datacite.org/meta/kernel-4/metadata.xsd'
    }
def getMdIdentifier(data_post):
    return {
        'identifier': {
            '@identifierType': 'DOI',
            '#text': data_post['doi'],
        }
    }
def getMdCreators(data_blog, data_author):
    return {
        'creators': {
            'creator': {
                'creatorName': {
                    '@nameType': 'Personal',
                    '#text': data_author['name']
                },
                'givenName': data_author['first_name'],
                'familyName': data_author['last_name'],
                'nameIdentifier': {
                    '@nameIdentifierScheme': 'ORCID',
                    '@schemeURI': 'https://orcid.org',
                    '#text': f'https://orcid.org/{data_author["orcid_id"]}'
                },
                'affiliation': data_blog['affiliation']
            }
        }
    }
def getMdTitles(data_post):
    return {
        'titles': {
            'title': {
                '@xml:lang': 'en',
                '#text': data_post['title']
            }
        }
    }
def getMdPublicationYear(data_post):
    return {
        'publicationYear': dateparser.parse(data_post['date']).strftime('%Y')
    }
def getMdPublisher(data_blog):
    return {
        'publisher': data_blog['publisher']
    }
def getMdResourceType():
    return {
        'resourceType': {
            "@resourceTypeGeneral": "Text",
            "#text": "BlogPosting"
        }
    }
def getMdLanguage():
    return {
        'language': 'en'
    }
def getMdFormats():
    return {
        'formats': {
            'format': 'HTML'
        }
    }
def getMdVersion(data_post):
    return {
        'version': data_post['version'] if 'version' in data_post else '1.0',
    }
def getMdRightsList(data_post):
    return {
        'rightsList': {
            'rights': parseLicense(data_post)
        }
    }
def getMdSubjects(data_post):
    return {
        'subjects': {
            'subject': data_post['tags'].split()
        }
    }
def getMdDescriptions(data_post):
    if 'abstract' not in data_post:
        print(f'Note: No abstract given!')
        return {}
    else:
        return {
            'descriptions': {
                'description': {
                    "@descriptionType": "Abstract",
                    "#text": data_post['abstract']
                }
            }
        }
def assembleMetadata(data_blog, data_post, data_author) -> dict:
    """
    Generate dictionary to be uploaded as metadata to DataCite.
    All level 1 keys (with 'resource' being considered as level 0) are generated in dedicated functions and merged into the internal `data` dictionary.
    Some dedicated functions only contain static values and hence no arguments, others need global data from the blog (`data_blog`), data from the specific post (`data_post`), or data from the respective author (`data_author`)
    """
    data = dict()
    data |= getMdSchema()  # this is new Python 3.9 syntax to merge two dictionaries
    data |= getMdIdentifier(data_post=data_post)
    data |= getMdCreators(data_blog=data_blog, data_author=data_author)
    data |= getMdTitles(data_post=data_post)
    data |= getMdPublicationYear(data_post=data_post)
    data |= getMdPublisher(data_blog=data_blog)
    data |= getMdResourceType()
    data |= getMdLanguage()
    data |= getMdFormats()
    data |= getMdVersion(data_post=data_post)
    data |= getMdRightsList(data_post=data_post)
    data |= getMdSubjects(data_post=data_post)
    data |= getMdDescriptions(data_post=data_post)
    return {
        'resource': data
    }
def registerMetadata(data_blog, dj_data_xml, doi, user, password):
    """
    Register metadata for a DOI at DataCite.
    PUT data, as assembled previously and converted to XML, with proper header and auth to the API endpoint, as specified in the global blog config.
    """
    dj_header = {
        'Content-Type': 'application/xml;charset=UTF-8',
    }
    return requests.put(
        f'{data_blog["provider_url"]}/metadata/{doi}', 
        headers=dj_header, 
        data=dj_data_xml, 
        auth=(user, password)
    )
def genPermalink(data_blog, post_filename, data_post):
    """
    Generate a permalink for a post of a blog.
    Tries to emulate some Jekyll defaults. Will probably not work for every case, especially not for cases with different-than-default permalink configuration. This one assumes https://BASEURL/YEAR/MONTH/DATE/FILENAME.html.
    """
    import re
    regex_filename = r"(\d{4}-\d{1,2}-\d{1,2}-)(.*)"

    url_base = data_blog['url'].rstrip('/')
    post_date_raw = dateparser.parse(data_post['date'])
    post_date_formatted = post_date_raw.strftime('%Y/%m/%d')
    post_filename_base = PurePath(post_filename).stem
    post_filename_clean = re.search(regex_filename, post_filename_base).group(2)
    return f'{url_base}/{post_date_formatted}/{post_filename_clean}.html'
def registerUrl(data_blog, post_filename, data_post, doi, user, password):
    """
    Register URL for a DOI at DataCite, which had previously its metadata registered.
    PUT ad-hoc created data payload with DOI and URL (with proper header and auth) to the API endpoint.
    """
    import textwrap
    url = genPermalink(data_blog=data_blog, post_filename=post_filename, data_post=data_post)
    logging.debug(f'Assembled permalink {url} from filename {post_filename}')
    data = textwrap.dedent(
        f'''\
            #Content-Type:text/plain;charset=UTF-8
            doi= {doi}
            url= {url}\
        ''')
    logging.debug(f'DataCite URL registration payload:\n{data}')
    dj_header = {
        'Content-Type': 'text/plain;charset=UTF-8',
    }
    return requests.put(
        f'{data_blog["provider_url"]}/doi/{doi}',
        headers=dj_header, 
        data=data, 
        auth=(user, password)
    )
def updateBlogpostMarkdown(data_post, post_filename, doi):
    """
    Add DOI key to YAML frontmatter of blogpost.
    Updates the blogpost for which a DOI was just registered.
    """
    data_post['doi'] = f'https://doi.org/{doi}'
    return frontmatter.dump(
        data_post, 
        post_filename, 
        sort_keys=False,  # original YAML frontmatter keys are probably also not sored
        width=float("inf")  # especially the abstract might be unformatted text; we should change this
    )

def main(args):
    """
    Run through the workflow of registering a DOI for a blogpost, assembling data from different sources.
    Logging is available on different levels.
    """
    logging.debug(f'argparse arguments: {args}')
    dc_user, dc_password = parseCredentials(args.user, args.password)
    logging.debug(f'Using DataCite user ..{dc_user[2:-4]}.. and password ..{dc_password[3:-6]}...')

    raw_data_blog = collectBlogData(args.config)
    logging.debug(f'Parsed raw data from blog: {raw_data_blog}')
    raw_data_post = collectPostData(args.blogpost[0])
    logging.debug(f'Parsed raw data from post: {raw_data_post.metadata}')
    raw_data_author = collectAuthorData(raw_data_post['author'], args)
    logging.debug(f'Parsed raw data from author: {raw_data_author.metadata}')

    if 'doi' in raw_data_post and not args.force:
        sys.exit(f'DOI already exists for blog post ({raw_data_post["doi"]}). Launch with "-f" to force overwrite.')
    raw_data_post['doi'] = genDoi(title=raw_data_post['title'], base=raw_data_blog['suffix_base'], prefix=raw_data_blog['prefix'])
    logging.debug(f"Auto-generated DOI {raw_data_post['doi']}")

    dj_data_json = assembleMetadata(data_blog=raw_data_blog, data_post=raw_data_post, data_author=raw_data_author)
    logging.debug(f"Metadata JSON:\n{json.dumps(dj_data_json, indent=4)}")

    dj_data_xml = xmltodict.unparse(dj_data_json)
    logging.info(f"Metadata XML:\n{xmltodict.unparse(dj_data_json, pretty=True)}")

    if args.dry_run:
        logging.warning("DRY-RUN: Not registering metadata with DataCite")
    else:
        dj_regMd_result = registerMetadata(data_blog=raw_data_blog, dj_data_xml=dj_data_xml, doi=raw_data_post['doi'], user=dc_user, password=dc_password)
        logging.debug(dj_regMd_result.text)
        logging.debug(dj_regMd_result.headers)
        if not debug.ok:
            logging.error('Something went wrong registering Metadata')
            logging.warning(dj_regMd_result.text)
            logging.warning(dj_regMd_result.headers)
            sys.exit()

    if args.skip_url or args.dry_run:
        if args.skip_url:
            logging.warning("SKIP-URL: Skipping URL creation at DataCite")
        if args.dry_run:
            logging.warning("DRY-RUN: Not registering URL with DataCite")
    else:
        dj_regUrl_result = registerUrl(data_blog=raw_data_blog, data_post=raw_data_post, post_filename=args.blogpost[0].name, doi=raw_data_post['doi'], user=dc_user, password=dc_password)
        logging.debug(dj_regUrl_result.text)
        logging.debug(dj_regUrl_result.headers)
        if not dj_regUrl_result.ok:
            logging.error('Something went wrong registering URL')
            logging.warning(dj_regUrl_result.text)
            logging.warning(dj_regUrl_result.headers)
            sys.exit()

    if args.dry_run:
        logging.warning("DRY-RUN: Not changing blog post's YAML Frontmatter to include DOI")
    else:
        _ = updateBlogpostMarkdown(data_post=raw_data_post, post_filename=args.blogpost[0].name, doi=raw_data_post['doi'])
    print(f"Successfully created {raw_data_post['doi']} at DataCite!")
    return 0

if __name__ == '__main__':
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

    args = parser.parse_args()
    logging_levels = [logging.ERROR, logging.WARNING, logging.INFO, logging.DEBUG]
    logging_level_cleaned = logging_levels[min(args.verbose, len(logging_levels) - 1)]
    logging.basicConfig(level=logging_level_cleaned)

    sys.exit(main(args))
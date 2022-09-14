#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
# Author: Andreas Herten, 2022
import logging

import dateparser
from mergedeep import merge

class extDict(dict):
    """This class extends the dict() method for the
    &
    &=
    operators (like | and |=), to add deepmerge functionality of `mergedeep`.
    It is currently not used as I fear reduced clarity.
    """
    def __init__(self, *args, **kwargs):
        super(extDict, self).__init__(*args, **kwargs)
    def __and__(self, other):
        return merge({}, self, other)
    def __rand__(self, other):
        return merge({}, other, self)
    def __iand__(self, other):
        return merge(self, other)
def parseLicense(data_post) -> dict:
    """
    Take a license short-name ('mit') and make the SPDX proper identifier form it, including an URL.
    Is not smart but will just look up the short-name. Needs to be extended for new licenses.
    """
    # could be extended via https://github.com/nexB/license-expression maybe
    if 'license' not in data_post:
        logging.warning(f'METADATA: No license specified!')
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
        print(f'METADATA: Note, no abstract given!')
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
def getMdRelToBlog(data_blog):
    if 'doi' in data_blog:
        logging.info(f'METADATA: Add relation to entire blog with DOI {data_blog["doi"]}.')
        return {
            'relatedIdentifiers': {
                'relatedIdentifier': {
                    '@relatedIdentifierType': 'DOI',
                    '@relationType': 'IsPartOf',
                    '#text': data_blog['doi']
                }
            }
        }
    else:
        return {}
def addAdditionalMetadata(additional_metadata):
    if additional_metadata:
        logging.info(f'METADATA: Add additional metadata {additional_metadata}')
        return additional_metadata
    else:
        return {}
def assembleMetadata(data_blog, data_post, data_author, additional_metadata) -> dict:
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
    data |= getMdRelToBlog(data_blog=data_blog)
    merge(data, addAdditionalMetadata(additional_metadata=additional_metadata))
    if 'doi-additional-metadata' in data_post:
        merge(data, addAdditionalMetadata(additional_metadata=data_post['doi-additional-metadata']))
    return {
        'resource': data
    }
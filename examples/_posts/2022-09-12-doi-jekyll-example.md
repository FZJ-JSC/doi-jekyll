---
layout: post
title: Example DOI Jekyll Post
date: 2022-08-12 15:05:02 +0200
tags: DOI Jekyll Examples
author: Anon
license: mit
abstract: The abstract doesn't say too much here
doi-additional-metadata:
  relatedIdentifiers:
    relatedIdentifier:
    	'@relatedIdentifierType': 'DOI'
    	'@relationType': 'Documents'
    	'#text': '10.5281/zenodo.754312'
---

This is an example blog post to showcase the `doi-jekyll` tool. Nothing to see here. Please continue.`

Note that `doi-additional-metadata` needs to be given in YAML form which is then read-in as a Python dict and eventually converted to XML using `xmltodict`. To allow for XML attributes, `xmltodict` specifies attributes with `@`, like above.
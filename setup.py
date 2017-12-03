# -*- coding:utf-8 -*-
# created by Toons on 01/05/2017
import sys
try:
	from setuptools import setup
	import wheel
except ImportError:
	from distutils.core import setup

kw = {}
f = open("VERSION", "r")
long_description = open("readme.rst", "r")
kw.update(**{
	"version": f.read().strip(),
	"name": "dpos-pool",
	"keywords": ["cli", "dpos", "blockchain"],
	"author": "Toons",
	"author_email": "moustikitos@gmail.com",
	"maintainer": "Toons",
	"maintainer_email": "moustikitos@gmail.com",
	"url": "https://github.com/Moustikitos/dpos-pool",
	"download_url": "https://github.com/Moustikitos/dpos-pool.git",
	"include_package_data": True,
	"data_files": [
		("", ["lib/pshare%d%d.pyc"%sys.version_info[:2]]),
		("", ["dpos-pool.html"])
	],
	"description": "One CLI to rule all DPOS blockchains",
	"long_description": long_description.read(),
	"packages": [],
	"scripts": ["lib/pool.py"],
	"install_requires": ["arky>=1.0"],
	"license": "Copyright 2017 Toons, MIT licence",
	"classifiers": [
		'Development Status :: 6 - Mature',
		'Environment :: Console',
		'Environment :: Web Environment',
		'Intended Audience :: Developers',
		'Intended Audience :: End Users/Desktop',
		'License :: OSI Approved :: MIT License',
		'Operating System :: OS Independent',
		'Programming Language :: Python',
		'Programming Language :: Python :: 2',
		'Programming Language :: Python :: 3',
	],
})
long_description.close()
f.close()

setup(**kw)

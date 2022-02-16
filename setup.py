import setuptools

with open('README.md', 'r') as fh:
	long_description = fh.read()

setuptools.setup(
	name="knitout_kniterate_3D",
	version="1.0.2",
	author="Gabrielle Ohlson",
	author_email="gmoa2017@mymail.pomona.edu",
	description="Code for producing knitout files to do 3D knitting on the kniterate knitting machine (and also optionally adding stitch patterns along the 3D surface).",
	long_description=long_description,
	long_description_content_type="text/markdown",
	url="https://github.com/gabrielle-ohlson/knit3D",
	# packages=setuptools.find_packages('knitout_kniterate_3D'),
	packages=['knitout_kniterate_3D'],
	install_requires=['numpy', 'Pillow'],
	classifiers=(
		"Programming Language :: Python :: 3",
		"License :: OSI Approved :: MIT License",
		"Operating System :: OS Independent",
	),
)

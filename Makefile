VERSION := $(shell python setup.py --version)

all: build

sources: clean
	$(eval TMPDIR := $(shell mktemp -d))
	# Populate the spec file with correct version from setup.py
	tar czf "$(TMPDIR)/smoker.tar.gz" ../smoker
	mv "$(TMPDIR)/smoker.tar.gz" smoker.tar.gz
	rmdir "$(TMPDIR)"

build install test:
	python setup.py $@

rpm: sources
	# Prepare directories and source for rpmbuild
	mkdir -p build/rpm/SOURCES
	cp smoker*.tar.gz build/rpm/SOURCES/
	mkdir -p build/rpm/SPECS
	cp smoker.spec build/rpm/SPECS/
	# Build RPM
	rpmbuild --define "_topdir $(CURDIR)/build/rpm" -ba build/rpm/SPECS/smoker.spec

clean:
	rm -f smoker.tar.gz
	rm -rf smoker.egg-info
	rm -rf build
	rm -rf dist

version:
	# Use for easier version bumping.
	# Helps keeping version consistent both in setup.py and smoker.spec
	@echo "Current version: $(VERSION)"
	@read -p "Type new version: " newversion; \
	sed -i -e "s/    'version': .*/    'version': '$$newversion',/" setup.py; \
	sed -i -e "s,Version:	.*,Version:	$$newversion," smoker.spec

upload:
	# You need following in ~/.pypirc to be able to upload new build
	# Also you need to be a maintainer or owner of gdc-smoker package
	#
	#	[pypi]
	#	username: xyz
	#	password: foo
	#
	#	[server-login]
	#	username: xyz
	#	password: foo
	#
	@while [ -z "$$CONTINUE" ]; do \
		read -r -p "Are you sure you want to upload version $(VERSION) to Pypi? [y/N] " CONTINUE; \
	done ; \
	if [ "$$CONTINUE" != "y" ]; then \
		echo "Exiting." ; exit 1 ; \
	fi

	python setup.py sdist upload

tag:
	git tag "v$(VERSION)"

release: tag upload
	$(info == Tagged and uploaded new version, do not forget to push new release tag and draft release on Github)

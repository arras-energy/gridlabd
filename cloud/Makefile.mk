# cloud/websites/Makefile.mk
#
# Cloud deployment makefile
#
#   $ make cloud-deploy
#
# AWS - Update AWS S3 buckets *.arras.energy
#
#   $ make aws-deploy
#
#   The *-dev.arras.energy websites are updated for all
#   branches except "master", which updates *.arras.energy
#
#   Options:
#
#     AWS_OPTIONS=--dryrun    do not update websites
#
# GCP - No GCP resources are updated at this time
#
#   $ make gcp-deploy
#
# AZ - No AZ resources are updated at this time
#
#   $ make az-deploy
#

cloud-help:
	@echo "Valid targets:"
	@echo "  release      release the current version to install.arras.energy"
	@echo "  aws-deploy   deploy code, docs, and www to AWS"
	@echo ""
	@echo "Options:"
	@echo "   SUFFIX=-dev deploy to *-dev.arras.energy instead of *.arras.energy"


cloud-deploy: aws-deploy gcp-deploy azure-deploy

cloud-deploy: aws-deploy gcp-deploy az-deploy

#
# Get a list of files that have to be updated
#

WEBSITES=$(shell find $(top_srcdir)/cloud/websites/*.arras.energy -type d -prune)

#
# Target that forces updates
#

FORCE:

#
# AWS hosts the main websites to sync
#
aws-deploy: $(WEBSITES)

#
# Target *-dev.arras.energy for all branches except "master"
#

AWS_TARGET=$(if $(subst master,,$(shell git rev-parse --abbrev-ref HEAD)),-dev,)

#
# Websites that should be sync'd
#

%.arras.energy: FORCE
	@echo "syncing $(subst .arras.energy,$(AWS_TARGET).arras.energy,$(notdir $@)) with AWS_OPTIONS='$(AWS_OPTIONS)' ..."
	@aws s3 sync $@ s3://$(subst .arras.energy,$(AWS_TARGET).arras.energy,$(notdir $@)) $(AWS_OPTIONS) --acl public-read

#
# GCP updates
#
gcp-deploy:

azure-deploy:
if HAVE_AZCLI
	@echo "WARNING: azure-deploy is not implemented yet"
endif

install.arras.energy: update-requirements
	@echo "Uploading files to $@..."
	@aws s3 ls s3://$@
	@echo "WARNING: make release not implemented yet"

install-dev.arras.energy: $(top_srcdir)/cloud/websites/install.arras.energy/requirements.txt $(top_srcdir)/cloud/websites/install.arras.energy/validate.tarz
	@echo "Copying files to s3://$@..."
	@for file in cloud/websites/install.arras.energy/*{html,sh,txt}; do ( aws s3 cp "$$file" "s3://$@" && aws s3api put-object-acl --bucket "$@" --key $$(basename $$file) --acl public-read); done
	@aws s3 cp $(top_srcdir)/cloud/websites/install.arras.energy/validate.tarz "s3://$@/validate-$$($(top_srcdir)/build-aux/version.sh --version).tarz"
	@aws s3api put-object-acl --bucket "$@" --key validate-$$($(top_srcdir)/build-aux/version.sh --version).tarz --acl public-read

$(top_srcdir)/cloud/websites/install.arras.energy/requirements.txt:
	@cat $$(find $(top_srcdir) -name requirements.txt -print) | sort -u > $@

$(top_srcdir)/cloud/websites/install.arras.energy/validate.tarz:
	@tar cfz $@ $$(find $(top_srcdir) -type d -name autotest -print -prune )

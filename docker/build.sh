#!/bin/sh
## Syntax: docker/build.sh [--push] [--release]
##
## Build a docker image of the current repository. The default image name is
## the output of `build-aux/version.sh --docker`. The source image repo is
## the output of `build-aux/version.sh --origin`. If the branch is `master`
## then the release is tags `latest` otherwise, the tag is the branch name.
##
## Options:
##
##   --push     Pushes the resulting image to user's Dockerhub. If the user
##     			does not have a Dockerhub account, then the push will fail.
##     			If `--release` is also specified then the push will be
##     			performed first
##
##   --release  Release the resulting image as the latest version of
##    			arras-energy/gridlabd. The master branch is released
##    			as 'latest'. Otherwise the branch name is used as the tag name.
## 
error () { echo "ERROR [docker/build.sh]: $*" ; exit 1; }

DOPUSH=no
DOLATEST=no
while [ $# -gt 0 ]; do
	case $1 in 
		-h|--help|help )
			grep '^##' $0 | cut -c4-
			exit 0
			;;
		--push )
			DOPUSH=yes
			;;
		--release )
			DOLATEST=yes
			;;
		* )
			error "option '$1' is invalid"
			;;
	esac
	shift 1
done

docker -v || error "you do not have docker installed and running"

ORIGIN=$(build-aux/version.sh --origin)
NAME=$(build-aux/version.sh --docker | cut -f1 -d:)
TAG=$(build-aux/version.sh --docker | cut -f2 -d:)
docker build docker --build-arg GRIDLABD_ORIGIN="$ORIGIN" -t "$NAME:$TAG" || error "build failed"
if [ "$DOPUSH" = "yes" ]; then
	docker push "$NAME:$TAG" || error "push image failed"
fi
if [ "$DOLATEST" = "yes" ]; then
	BRANCH=$(build-aux/version.sh --branch)
	if [ "$BRANCH" = "master" ]; then
		BRANCH="latest"
	fi
	IMAGE="arras-energy/gridlabd-$(build-aux/version.sh --machine)"
	docker tag "$NAME:$TAG" "$IMAGE:$BRANCH" || error "tag latest failed"
	if [ "$DOPUSH" = "yes" ]; then
		docker push "$IMAGE:$BRANCH" || error "push latest failed"
	fi
fi

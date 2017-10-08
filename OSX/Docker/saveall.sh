#!/bin/sh

OUTDIR="$1"

die() {
    echo "" >&2
    echo "$*" >&2
    exit 1
}

[ -n "${OUTDIR}" ] || die "No destination specified"
[ -d "${OUTDIR}" ] || die "No such dir"

IFS=$'\n'
for di in $(docker images | tail -n +2); do
   tag=`echo "$di" | awk '{print $1}'`
   rev=`echo "$di" | awk '{print $2}'`
   # skip network (Docker Hub) images
   echo "$tag" | grep -q '/'
   if [ $? -eq 0 ]; then
       echo "Skipping ${tag}:${rev}"
       continue
   fi
   echo "Saving ${tag}:${rev}"
   docker save "$tag:$rev" | pv -trb | xz -T0 -c > "$OUTDIR/docker-${tag}-${rev}.tar.xz"
done

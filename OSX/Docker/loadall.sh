#!/bin/sh

INDIR="$1"

die() {
    echo "" >&2
    echo "$*" >&2
    exit 1
}

[ -n "${INDIR}" ] || die "No destination specified"
[ -d "${INDIR}" ] || die "No such dir"

for di in `ls -1 ${INDIR}/docker-*.tar.xz`; do
   name=`basename "${di}" | sed 's/docker-\(.*\)\.tar\.xz$/\1/'`
   tag=`echo "${name}" | cut -d'@' -f1`
   rev=`echo "${name}" | cut -d'@' -f2`
   echo "Loading $name ${tag}:${rev}"
   xz -d -c "${di}" | pv -trb | docker load
done

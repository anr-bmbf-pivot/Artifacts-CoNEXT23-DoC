#! /bin/sh

# Copyright (C) 2021 Freie Universität Berlin
#
# This file is subject to the terms and conditions of the GNU Lesser
# General Public License v2.1. See the file LICENSE in the top level
# directory for more details.

SCRIPT_DIR="$(dirname "$(readlink -f $0)")"
RIOT="${SCRIPT_DIR}/RIOT/"
CURRENT_BRANCH=$(git branch --show-current)
TARGET_BRANCH='dns-comparison'
BASE_RELEASE='2021.10-branch'
DONE_PRS_FILE=${SCRIPT_DIR}/done_prs.txt

if [ "${CURRENT_BRANCH}" = "${TARGET_BRANCH}" ]; then
    git -C "${RIOT}" checkout "${TARGET_BRANCH}" || exit 1
fi

if ! git -C "${RIOT}" remote -v | grep -q "upstream.*RIOT-OS/RIOT.git (fetch)"
then
    git -C "${RIOT}" remote add upstream https://github.com/RIOT-OS/RIOT.git || exit 1
fi
git -C "${RIOT}" fetch upstream || exit 1

if ! [ -e "${DONE_PRS_FILE}" ]; then
    git -C "${RIOT}" reset --hard "upstream/${BASE_RELEASE}"
fi

for pr in 16705 16861 16963; do
    if grep -q "\<${pr}\>" "${DONE_PRS_FILE}" 2>/dev/null ; then
        continue
    fi
    git -C "${RIOT}" fetch upstream refs/pull/${pr}/head || exit 1
    MERGE_BASE=$(git -C "${RIOT}" log --oneline --graph FETCH_HEAD | \
        awk '1;/^[^*]/ {exit}' | head -n-1 | tail -n-1 | awk '{print $2}')
    for commit in $(git -C "${RIOT}" log --reverse --oneline --pretty=format:%H \
        "${MERGE_BASE}"..FETCH_HEAD); do
        if grep -q "\<${commit}\>" "${DONE_PRS_FILE}" 2>/dev/null ; then
            if tail -n-1 "${DONE_PRS_FILE}" | grep -q "\<${commit}\>" && \
               git -C "${RIOT}" show | \
                    grep  "(cherry picked from commit ${commit})" 2>/dev/null && \
               ! git -C "${RIOT}" show | grep "From PR${pr}" 2>/dev/null; then
                git -C "${RIOT}" log --format=%B -n 1 HEAD | \
                    sed "$ a See PR${pr}" | \
                    git -C "${RIOT}" commit --amend -F -
            fi
            continue
        fi
        echo "${commit}" >> "${DONE_PRS_FILE}"
        git -C "${RIOT}" cherry-pick -xs --rerere-autoupdate "${commit}" || exit 1
        git -C "${RIOT}" log --format=%B -n 1 HEAD | \
            sed "$ a From PR${pr}" | \
            git -C "${RIOT}" commit --amend -F -
    done
    echo "${pr}" >> "${DONE_PRS_FILE}"
done
rm "${DONE_PRS_FILE}"

#!/usr/bin/env bash

contains() {
    [[ $1 =~ (^| )$2($| ) ]] && echo '1' || echo '0'
}

# safer to explicitly whitelist
whitelist="py ipynb txt json java go"

# see https://askubuntu.com/questions/819265/bash-script-to-monitor-file-change-and-execute-command
inotifywait -r -m --event modify --event move --event delete --format "%e %w%f" "${REPO_DIR}" |
while read event fullpath; do
    echo "Event: $event on $fullpath"
    filename=$(basename -- "$fullpath")
    ext="${filename##*.}"
    test=$(contains "$whitelist" "$ext")
    if [ "$test" == '1' ]; then
        cd "${REPO_DIR}"
        git add "$fullpath"
        git commit -m "auto commit"
        git push origin "$(git rev-parse --abbrev-ref HEAD)"
        cd -
    fi
done

#!/usr/bin/env bash

repo_dir=${1:-$REPO_DIR}

contains() {
    [[ $1 =~ (^| )$2($| ) ]] && echo '1' || echo '0'
}

# safer to explicitly whitelist
whitelist="py ipynb txt json java go js ts md rst yml yaml jsx tsx"

# see https://askubuntu.com/questions/819265/bash-script-to-monitor-file-change-and-execute-command
inotifywait -r -m --event modify --event move --event delete --exclude \.garden --format "%e %w%f" "${repo_dir}" |
while read event fullpath; do
    echo "Event: $event on $fullpath"
    filename=$(basename -- "$fullpath")
    ext="${filename##*.}"
    test=$(contains "$whitelist" "$ext")
    if [ "$test" == '1' ]; then
        cd "${repo_dir}"
        git add "$fullpath"
        git commit -m "auto commit"
        git push origin "$(git rev-parse --abbrev-ref HEAD)"
        cd -
    fi
done

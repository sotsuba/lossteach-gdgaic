loading() {
    local duration=$1  # duration in seconds
    echo -n "Loading "
    local spin='-\|/'
    local i=0
    local end=$((SECONDS + duration))
    while [ $SECONDS -lt $end ]; do
        i=$(( (i + 1) % 4 ))
        printf "\b${spin:$i:1}"
        sleep 0.1
    done
    echo " Done!"
}
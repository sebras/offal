#!/bin/bash

while [ $# -gt 0 ]; do
    FILE="$1"
    echo "$FILE"

    OBJS=$(mutool show "$FILE" grep 2> /dev/null | grep JPXDecode | cut -d: -f2)

    HEREFILE="$(basename "$FILE")"

    for OBJ in $OBJS; do
        mutool show -be "$FILE" $OBJ > "$HEREFILE-$OBJ.jp2" 2> /dev/null
    done

    shift
done

#!/bin/bash

while [ $# -gt 0 ]; do
    FILE="$1"
    echo "$FILE"

    OBJS=$(mutool show "$FILE" g 2> /dev/null | grep JBIG2Decode | cut -d: -f2)

    HEREFILE="$(basename "$FILE")"

    for OBJ in $OBJS; do
        GLOBALS="$(mutool show "$FILE" g 2> /dev/null | grep '^[^:]*:'$OBJ':' | grep JBIG2Globals | sed -e 's/^.*JBIG2Globals \([0-9]\+\) 0 R.*$/\1/')"
        if [ -n "$GLOBALS" ]; then
            mutool show -be "$FILE" "$GLOBALS" > "$HEREFILE-$OBJ.globals" 2> /dev/null
        fi
        mutool show -be "$FILE" $OBJ > "$HEREFILE-$OBJ.jb2" 2> /dev/null
    done

    shift
done

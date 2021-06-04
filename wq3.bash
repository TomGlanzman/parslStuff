#!/bin/bash
## wq3.bash - trivial bash script called from a Parsl "bash_app"

echo "Entering wq3.bash"

## generate a sufficiently random number between 1 and 100
foo=$(((RANDOM % 100) +1 ))
echo "foo = $foo"

if [ $foo -ge 50 ]; then
    exit 76
else
    exit 0
fi


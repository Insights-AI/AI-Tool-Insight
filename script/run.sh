#!/bin/bash

git branch -D master
git fetch
git checkout -b master origin/master
python3 ./script/run.py > tools.md

sed -n '1,642p' tools.md > README.md
echo '\n\n<a href="/READMORE.md">READMORE</a>' >> README.md

echo '| Name | Description | Website | Screenshot | Pricing | Category |\n|---|---|---|---|---|---|' > READMORE.md
sed -n '642,5000p' tools.md >> READMORE.md

git add README.md READMORE.md

git commit -am 'auto sync readme'

git push origin master



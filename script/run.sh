#!/bin/bash

git branch -D master
git fetch
git checkout -b master origin/master
python3 ./script/run.py > README.md

git commit -am 'auto sync readme'

git push origin master



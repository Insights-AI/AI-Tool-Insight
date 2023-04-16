#!/bin/bash

git branch -D feature-script
git fetch
git checkout -b feature-script
python3 ./script/run.py > README.md

git commit -am 'auto sync readme'

git push origin feature-script



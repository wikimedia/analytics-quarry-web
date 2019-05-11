#!/usr/bin/env bash
#Generate HTTP error pages from template

FOLDER="$(git rev-parse --show-toplevel)/quarry/web/static/error/"
>&2 echo "Will generate error files in $FOLDER"

sed "s/{{error}}/500 Internal Error/g" "$FOLDER/error.html" > "$FOLDER/500.html"
sed "s/{{error}}/502 Bad Gateway/g" "$FOLDER/error.html" > "$FOLDER/502.html"

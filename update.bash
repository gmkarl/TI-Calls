#!/usr/bin/env bash
git annex importfeed --force --fast --template '${feedtitle}/${itempubdate}-${itempubhour}:${itempubminute}:${itempubsecond}-${itemtitle}${extension}' https://www.freeconferencecall.com/rss/podcast?id=a3c83a2ec931a8f5c69c930bfd942aa06f1c02393a36020d9a3fde7a5d9796a4_462001320
for file in */*_???
do
	name=${file%_???}
	ext=${file##*_}
	git mv "$file" "$name"."$ext"
	mv -v "$file" "$name"."$ext" 2>/dev/null
done
rm -rf .git/annex/tmp
git annex get --jobs=2 .
git annex migrate
git annex sync

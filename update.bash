#!/usr/bin/env bash
for feed in \
	https://www.freeconferencecall.com/rss/podcast?id=a3c83a2ec931a8f5c69c930bfd942aa06f1c02393a36020d9a3fde7a5d9796a4_462001320 \
	https://www.talkshoe.com/rss-pacts-international.xml \
	https://www.talkshoe.com/rss-pacts-international-conference-calls.xml \
	https://www.talkshoe.com/rss-targeted-individuals-ffchs.xml \
	https://www.talkshoe.com/rss-osi-late-night-lounge.xml \
	https://www.talkshoe.com/rss-electronic-harassmentorganized-stalking.xml \
	# googling talkshoe and freeconferencecall with reasonable keywords helps find more of these
; do
	git annex importfeed --force --fast --template '${feedtitle}/${itempubdate}-${itempubhour}:${itempubminute}:${itempubsecond}-${itemtitle}${extension}' "$feed"
done
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

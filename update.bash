#!/usr/bin/env bash

	# googling talkshoe and freeconferencecall with reasonable keywords helps find more of these
for feed in \
	https://www.freeconferencecall.com/rss/podcast?id=a3c83a2ec931a8f5c69c930bfd942aa06f1c02393a36020d9a3fde7a5d9796a4_462001320 \
	https://www.talkshoe.com/rss-pacts-international.xml \
	https://www.talkshoe.com/rss-pacts-international-conference-calls.xml \
	https://www.talkshoe.com/rss-targeted-individuals-ffchs.xml \
	https://www.talkshoe.com/rss-osi-late-night-lounge.xml \
	https://www.talkshoe.com/rss-electronic-harassmentorganized-stalking.xml \
; do
	git annex importfeed --force --fast --template '${feedtitle}/${itempubdate}-${itempubhour}:${itempubminute}:${itempubsecond}-${itemtitle}${extension}' "$feed"
done
for file in */*_???
do
	name=${file%_???}
	ext=${file##*_}
	if [ -h "$file" ]
	then
		finalname="$name"."$ext"
		git mv -f "$file" "$finalname" 2>/dev/null
		mv -fv "$file" "$finalname" 2>/dev/null
		git add "$finalname"
	fi
done
rm -rf .git/annex/tmp
git annex get --jobs=2 .
git annex migrate

bundlename='9999-TI_Calls.bundle'
rm "$bundlename"
git bundle create "$bundlename" git-annex master && git annex add "$bundlename" && git annex copy "$bundlename" --to=skynet

indexfile='9999-index.html'
rm "$indexfile"
./makeindex.py > "$indexfile" && git annex add "$indexfile" && git annex copy "$indexfile" --to=skynet

git annex sync

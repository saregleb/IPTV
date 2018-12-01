#!/bin/bash
gistdir='/opt/iptv-epg/playlist-private'
privplaylist_name='skynet-pl-private.m3u'
targetfile='/opt/iptv-epg/epg-repo/skynet-pl-local.m3u'
file='/opt/iptv-epg/epg-repo/tools/secret-path'  # The secret url a gateway to the power of allmighty KEK
outfile="$gistdir/$privplaylist_name"

secretprefix=$(cat "$file")  # Reading textfile to var
oldprefix='udp://@'
oldprefix=$(echo "$oldprefix" | sed 's/\//\\\//g')
secretprefix=$(echo "$secretprefix" | sed 's/\//\\\//g')

sed "s/$oldprefix/$secretprefix/g" $targetfile | tee $outfile

# git magic
cd $gistdir
git add $privplaylist_name
DATE=`date`
git commit -m "Playlist update for $DATE"
git push origin master

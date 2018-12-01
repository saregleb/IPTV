#!/bin/bash

BASE_DIR='/opt/iptv-epg'
WG_DIR='/opt/iptv-epg/wgpp'
REPO_DIR='/opt/iptv-epg/epg-repo'
REPLACER_DIR='/opt/iptv-epg/epg-repo/tools/replace.sh'

cd $REPO_DIR
git pull origin master
# cp "$REPO_DIR/tools/WebGrab++.config.xml" $WG_DIR

cd $WG_DIR
"$WG_DIR/run.sh"
cp "$WG_DIR/guide.xml" $REPO_DIR
cd $REPO_DIR
git add guide.xml
DATE=`date`
git commit -m "epg update for $DATE"
git push origin master

# runs private playlist generation
sh $REPLACER_DIR

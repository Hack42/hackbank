#!/bin/bash
cd /home/barapp/kassa/rrd && cat ../data/revbank.stock | while read -r prod aantal crap;do
  if [ ! -f "$prod".rrd ] ; then
    rrdtool create "$prod".rrd --start N --step 43200 DS:wut:GAUGE:86400:-1024:4096 RRA:AVERAGE:0:1:1800
  fi
  rrdtool update "$prod.rrd" N:"$aantal"
done

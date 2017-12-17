from database import *
import urllib2
import json
import time
from retry import retry
from models import Ship
import sys
cargo_capacity = 18913 #tayra with 3 expandeds = 18913
isk = 386000000
location = 'J143234'
jumps = 5

#connected_systems = []
connected_systems = ['Fluekele']

regions = all_region_ids()

paths = map_solarsystem_jumps(location, connected_systems, jumps)
#for path in paths:
#    for system in path:
#        print solar_system_by_id(system)['solarSystemName']
regions = get_involved_regions_from_paths(paths)

#url = 'https://esi.tech.ccp.is/latest/markets/' + str(solar_system['regionID']) + '/orders/?datasource=tranquility&order_type=sell&page=1'
#md = urllib2.urlopen(url).read()
#ms = json.loads(md)
ms = {}
@retry(urllib2.HTTPError, tries=4, delay=3, backoff=2)
def fetch_by_region_s(region):
    url = 'https://esi.tech.ccp.is/latest/markets/' + str(region) + '/orders/?datasource=tranquility&order_type=sell&page=1'
    md = urllib2.urlopen(url).read()
    items = json.loads(md)
    for item in items:
        if station_by_id(item['location_id']):
            ss_id = str(station_by_id(item['location_id'])['solarSystemID'])
            if ss_id not in ms:
                ms[ss_id] = {}
            if item['type_id'] not in ms[ss_id]:
                ms[ss_id][item['type_id']] = {}
            try:
                ms[ss_id][item['type_id']].append(item)
            except:
                ms[ss_id][item['type_id']] = [item]

mb = {}
@retry(urllib2.HTTPError, tries=4, delay=3, backoff=2)
def fetch_by_region_b(region):
    url = 'https://esi.tech.ccp.is/latest/markets/' + str(region) + '/orders/?datasource=tranquility&order_type=buy&page=1'
    md = urllib2.urlopen(url).read()
    items = json.loads(md)
    for item in items:
        if station_by_id(item['location_id']):
            ss_id = str(station_by_id(item['location_id'])['solarSystemID'])
            if ss_id not in mb:
                mb[ss_id] = {}
            if item['type_id'] not in mb[ss_id]:
                mb[ss_id][item['type_id']] = {}
            try:
                mb[ss_id][item['type_id']].append(item)
            except:
                mb[ss_id][item['type_id']] = [item]
    #Retry with a few seconds pause until you get a proper answer. This is literally the approach I take on zKillboard. In a 5 minute time span I can have anywhere from 200-1000 CREST requests with about a 0.1% error rate.

for region in regions:
    print "fetching region: " + str(region)
    fetch_by_region_s(region)
    fetch_by_region_b(region)
    
search_paths = False
if search_paths:
    for path in paths:
        print "New ship for path: " + str(path)
        s = Ship()
        s.capacity=cargo_capacity
        s.isk=isk
        s.starting_isk=isk
        count = 0
        pbs = {}
        for ss in path[1:]:
            if ss in mb.keys(): #maybe nothing in ss
                for typeid in mb[ss].keys():
                    for item in mb[ss][typeid]:
                        #print item
                        try:
                            pbs[typeid].append(item)
                        except:
                            pbs[typeid] = [item]
        for ss in path:
            count += 1
            #get ms for ss
            if ss in ms.keys():
                for typeid in ms[ss].keys():
                    #if b exists further down the path
                    for item in ms[ss][typeid]:
                        if typeid in pbs.keys():
                            for item2 in pbs[typeid]:
                                if item2['price'] > item['price']:
                                    #try:
                                    #    s.inv[item['type_id']] += min(item['volume_remain'], item2['volume_remain'])
                                    #except:
                                    q = min(item['volume_remain'], item2['volume_remain'])
                                    p = (q * item2['price']) - (q * item['price'])
                                    if p > 10000000.0:

                                        ##got stuck in rens because min_volume was 8000


                                        #q = min(q, s.capacity)
                                        s.inv[item['type_id']] = q
                                        #s.capacity -= item_by_id(item['type_id'])['volume'] * q
                                        s.digest.append('B: @' + station_by_id(item['location_id'])['stationName'] + ' ' + str(q) + ' of ' + item_by_id(item['type_id'])['typeName'])
                                        s.digest.append('S: @' + station_by_id(item2['location_id'])['stationName'] + ' ' + str(q) + ' of ' + item_by_id(item['type_id'])['typeName'])
                                        s.digest.append('P:' + str(q * item['price']) + ' | ' + str(q * item2['price']) + ' = ' + str(p))
        for digest in s.digest:
            print digest
    
pbs = []
for ss in ms.keys():
    for typeid in ms[ss].keys():
        pbs.append(typeid) #save this typeid as exists for s

found = []
for ss in mb.keys():
    for typeid in mb[ss].keys():
        if typeid in pbs:
            for item in mb[ss][typeid]:
                for ss2 in ms.keys():
                    try:
                        for item2 in ms[ss2][typeid]:
                            if item['price'] > item2['price']:
                                volume = min(item['volume_remain'], item2['volume_remain'])
                                if volume > max(item['min_volume'], item2['min_volume']):
                                    b = (item2['price'] * volume)
                                    s = (item['price'] * volume)
                                    p = s - b
                                    if p >= 10000000:
                                        capacity = volume * item_by_id(typeid)['volume']
                                        if capacity <= cargo_capacity:
                                            #desc = str(volume) + " " + item_by_id(typeid)['typeName'] + ". From: " + station_by_id(item2['location'])['stationName'] + " To: " + station_by_id(item['location'])['stationName'] + ". Capacity: " + str(volume * item_by_id(typeid)['volume'])
                                            desc = str(volume) + ' of ' + item_by_id(typeid)['typeName'] + '. ' + 'Capacity: ' + str(capacity) + ' From: ' + station_by_id(item2['location_id'])['stationName'] + ' To: ' + station_by_id(item['location_id'])['stationName']
                                            found.append([b, s, p, desc])
                    except: 
                        pass
from operator import itemgetter
sort = sorted(found, key=itemgetter(2))
sort.reverse()
for line in sort[:100]:
    print line
#print "Analyzing..."
#items = []
#for item_s in ms:
#    for mbr in mb:
#        for item_b in mbr:
#            if item_b['type_id'] == item_s['type_id']:
#                if item_b['price'] > item_s['price']:
#                    items.append([item_s, item_b])

#for item in items:
#    station_from = station_by_id(item[0]['location_id'])
#    station_to = station_by_id(item[1]['location_id'])
#    if station_from and station_to:
#        starting_isk = int(item[0]['volume_remain']) * int(item[0]['price'])
#        ending_isk = int(item[0]['volume_remain']) * int(item[1]['price']) #USING ITEM[0]'s volume remain. use a simulated cargo
#        difference = ending_isk - starting_isk
#        if difference >= 1000000:
#            print "Item: " + item_by_id(item[0]['type_id'])['typeName']
#            print "From: " + station_from['stationName']
#            print "To: " + station_to['stationName']
#            print "Starting ISK: " + str(starting_isk) + " @ " + str(item[0]['price']) + "/unit"
#            print "Ending ISK: " + str(ending_isk) + " @ " + str(item[1]['price']) + "/unit"
#            print "Difference: " + str(difference)
#            print "Required capacity: " + str(float(item[0]['volume_remain']) * float(item_by_id(item[0]['type_id'])['volume']))
#            print "----------------------------------------------------"
#            #use min(capacity,required_capacity) and calculate difference based off the min
            #put this into a dict, sort top down by difference, remove ones with higher than required min capacity

#!!!!!!!if mb range is region, say ANYWHERE IN REGION (X). range "region" or number. what is number?
#jumps appear off, length is longer than expected in-game
#allow wh to be used
#multiple b or s put together
#if multiple pages per region
#eventually include region wide
#include if reprocess

import sqlite3
#https://www.fuzzwork.co.uk/dump/sqlite-latest.sqlite.bz2
conn = sqlite3.connect('sqlite-latest.sqlite')
c = conn.cursor()

def dfs_paths(graph, start, jumps):
    stack = [(start, [start])]
    while stack:
        (vertex, path) = stack.pop()
        for next in graph[vertex] - set(path):
            #if (goal and next == goal) or len(path + [next]) > (jumps - 1):
            if len(path + [next]) == jumps:
            #if next == goal or len(path+[next]) == 20:
                yield path + [next]
            else:
                stack.append((next, path + [next]))
    
def map_solarsystem_jumps(solar_system, jumps):
    c.execute('SELECT fromSolarSystemID, toSolarSystemID FROM mapSolarSystemJumps')
    jump_map = c.fetchall()
    graph = {}
    for jump in jump_map:
        try:
            graph[str(jump[0])].add(str(jump[1]))
        except:
            graph[str(jump[0])] = set([str(jump[1])])
    paths = list(dfs_paths(graph, solar_system, jumps))
    #print paths
    #get all involved solar systems from paths
    return paths

def get_involved_regions_from_paths(paths):
    involved_solar_systems = []
    for path in paths:
        for ss in path:
            if ss not in involved_solar_systems:
                involved_solar_systems.append(ss)
    #get all involved regions from solar systems
    regions = []
    for ss in involved_solar_systems:
        regionID = solar_system_by_id(ss)['regionID']
        if regionID not in regions:
            regions.append(regionID)
    return regions

def all_region_ids():
    c.execute('SELECT * FROM mapRegions')
    regions = c.fetchall()
    return regions

def item_properties(item):
    it = {}
    it['typeID'] = item[0]
    it['typeName'] = item[2]
    it['volume'] = item[5]
    return it

def item_by_id(itemid):
    id = (itemid,)
    c.execute('SELECT * FROM invTypes WHERE typeID=?', id)
    item = c.fetchone()
    return item_properties(item)

def solar_system_properties(solar_system):
    ss = {}
    ss['regionID'] = solar_system[0]
    ss['solarSystemID'] = solar_system[2]
    ss['solarSystemName'] = solar_system[3]
    ss['security'] = solar_system[21]
    return ss

def solar_system_by_name(name):
    name = (name,)
    c.execute('SELECT * FROM mapSolarSystems WHERE solarSystemName=?', name)
    solar_system = c.fetchone()
    return solar_system_properties(solar_system)

def solar_system_by_id(id):
    id = (id,)
    c.execute('SELECT * FROM mapSolarSystems WHERE solarSystemID=?', id)
    solar_system = c.fetchone()
    return solar_system_properties(solar_system)

def station_properties(station):
    if station == None:
        return None
    s = {}
    s['stationID'] = station[0]
    s['solarSystemID'] = station[8]
    s['regionID'] = station[10]
    s['stationName'] = station[11]
    return s

def station_by_id(id):
    if id > 70000000: #unknown location id with high number ie, 1023968078820
        return None
    id = (id,)
    c.execute('SELECT * FROM staStations WHERE stationID=?', id)
    station = c.fetchone()
    return station_properties(station)

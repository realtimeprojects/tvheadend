#!/usr/bin/python

from glob import glob
from os.path import expanduser, basename
from re import match
import json
from os import mkdir

base = "~/.hts/tvheadend"

config = {}
channels = {}

for transport in glob( expanduser( base + "/dvbtransports/*" )):
  for sfile in glob( "%s/*"%transport ):
    frontend = 0
    m = match( "^_dev_dvb_adapter(\d+)_.*(\d{8})_([HV+])_satconf_(\d+)_[a-z\d]+$", basename( sfile ))
    if m:
      adapter, freq, pol, satconf = m.groups( )
      adapter = int(adapter)
      freq    = int(freq)
      satconf = int(satconf)
    else:
      print "Error parsing '%s'"%sfile
      exit( -1 )

    if not config.has_key( adapter ):
      config[adapter] = {}
      config[adapter][frontend] = { "portcount": 0 }
      adapterconf = expanduser( base + "/dvbadapters/_dev_dvb_adapter%d_*"%( adapter ))
      g = glob( adapterconf )
      if len( g ) != 1:
        print "Error finding adatper config: '%s'"%adapterconf
        exit( -1 )
      fp = open( g[0] )
      adapterconf = json.load( fp )
      fp.close( )
      config[adapter]["config"]  = { }
      config[adapter]["config"]["displayname"] = adapterconf["displayname"]
      config[adapter][frontend]["config"] = { }
      config[adapter][frontend]["config"]["autodiscovery"]  = adapterconf["autodiscovery"]
      config[adapter][frontend]["config"]["nitoid"]         = adapterconf["nitoid"]
      config[adapter][frontend]["config"]["diseqc_version"] = adapterconf["diseqc_version"]
      config[adapter][frontend]["config"]["qmon"]           = adapterconf["qmon"]
      config[adapter][frontend]["config"]["idlescan"]       = adapterconf["idlescan"]
      config[adapter][frontend]["config"]["type"]           = adapterconf["type"]
      config[adapter][frontend]["config"]["dump_muxes"]     = adapterconf["dump_muxes"]

    foundport = False
    port = None
    portcount = config[adapter][frontend]["portcount"]
    for port in range( portcount + 1 ):
      if config[adapter][frontend].has_key( port ) and config[adapter][frontend][port]["satconf"] == satconf:
        foundport = True
        break
    if not foundport:
      port = portcount
      config[adapter][frontend][port] = { "satconf": satconf, "muxcount": 0 }
      config[adapter][frontend]["portcount"] += 1
      pfile = expanduser( base + "/dvbsatconf/_dev_dvb_adapter%d_*/%d"%( adapter, satconf ))
      g = glob( pfile )
      if len( g ) != 1:
        print "Error finding satconf: '%s'"%pfile
        exit( -1 )
      fp = open( g[0] )
      conf = json.load( fp )
      fp.close( )
      config[adapter][frontend][port]["config"] = {}
      config[adapter][frontend][port]["config"]["name"]    = conf["name"]
      config[adapter][frontend][port]["config"]["port"]    = conf["port"]
      config[adapter][frontend][port]["config"]["comment"] = conf["comment"]
      config[adapter][frontend][port]["config"]["lnb"]     = conf["lnb"]

    foundmux = False
    mux = None
    muxcount = config[adapter][frontend][port]["muxcount"]
    for mux in range( muxcount + 1 ):
      if config[adapter][frontend][port].has_key( mux ) and config[adapter][frontend][port][mux]["freq"] == freq and config[adapter][frontend][port][mux]["pol"] == pol:
        foundmux = True
        break
    if not foundmux:
      mux = muxcount
      config[adapter][frontend][port][mux] = { "freq": freq, "pol": pol, "servicecount": 0 }
      config[adapter][frontend][port]["muxcount"] += 1
      mfile = expanduser( base + "/dvbmuxes/_dev_dvb_adapter%d_*/_dev_dvb_adapter%d_*%d_%s_satconf_%d"%( adapter, adapter, freq, pol, satconf ))
      g = glob( mfile )
      if len( g ) != 1:
        print "Error finding mux: '%s'"%mfile
        exit( -1 )
      fp = open( g[0] )
      conf = json.load( fp )
      fp.close( )
      config[adapter][frontend][port][mux]["config"] = {}
      config[adapter][frontend][port][mux]["config"]["quality"]           = conf["quality"]
      config[adapter][frontend][port][mux]["config"]["enabled"]           = conf["enabled"]
      config[adapter][frontend][port][mux]["config"]["status"]            = conf["status"]
      config[adapter][frontend][port][mux]["config"]["transportstreamid"] = conf["transportstreamid"]
      config[adapter][frontend][port][mux]["config"]["frequency"]         = conf["frequency"]
      config[adapter][frontend][port][mux]["config"]["symbol_rate"]       = conf["symbol_rate"]
      config[adapter][frontend][port][mux]["config"]["fec"]               = conf["fec"]
      config[adapter][frontend][port][mux]["config"]["polarisation"]      = conf["polarisation"]
      config[adapter][frontend][port][mux]["config"]["modulation"]        = conf["modulation"]
      config[adapter][frontend][port][mux]["config"]["delivery_system"]   = conf["delivery_system"]
      config[adapter][frontend][port][mux]["config"]["rolloff"]           = conf["rolloff"]

    service = config[adapter][frontend][port][mux]["servicecount"]

    print sfile
    fp = open( sfile )
    conf = json.load( fp )
    fp.close( )
    if conf.has_key( "channelname" ):
      channel = conf.pop( "channelname" )
      if not channels.has_key( channel ):
        channels[channel] = { "services": [] }
        channels[channel]["dvr_extra_time_pre"] = 0
        channels[channel]["dvr_extra_time_post"] = 0
        channels[channel]["channel_number"] = len( channels ) + 1
        channels[channel]["tags"] = []
        channels[channel]["name"] = channel
      channels[channel]["services"].append( (adapter, frontend, port, mux, service) )

    service = config[adapter][frontend][port][mux]["servicecount"]
    config[adapter][frontend][port][mux][service] = conf
    config[adapter][frontend][port][mux]["servicecount"] += 1

path = expanduser( base ) + "/newconf"
mkdir( path )
path += "/adapters"
mkdir( path )
for a in config:
  t = path + "/adapter%d"%a
  mkdir( t )
  fp = open( t + "/config", "w" )
  fp.write( json.dumps( config[a]["config"], sort_keys=True, indent=4 ))
  fp.close( )
  for f in config[a]:
    if str(f).isdigit( ):
      t2 = t + "/frontend%d"%f
      mkdir( t2 )
      fp = open( t2 + "/config", "w" )
      fp.write( json.dumps( config[a][f]["config"], sort_keys=True, indent=4 ))
      fp.close( )
      for p in config[a][f]:
        if str(p).isdigit( ):
          t3 = t2 + "/port%d"%p
          mkdir( t3 )
          fp = open( t3 + "/config", "w" )
          fp.write( json.dumps( config[a][f][p]["config"], sort_keys=True, indent=4 ))
          fp.close( )
          for m in config[a][f][p]:
            if str(m).isdigit( ):
              t4 = t3 + "/mux%d"%m
              mkdir( t4 )
              fp = open( t4 + "/config", "w" )
              fp.write( json.dumps( config[a][f][p][m]["config"], sort_keys=True, indent=4 ))
              fp.close( )
              for s in config[a][f][p][m]:
                if str(s).isdigit( ):
                  t5 = t4 + "/service%d"%s
                  mkdir( t5 )
                  fp = open( t5 + "/config", "w" )
                  fp.write( json.dumps( config[a][f][p][m][s], sort_keys=True, indent=4 ))
                  fp.close( )

for channel in glob( expanduser( base + "/channels/*" )):
  fp = open( channel )
  conf = json.load( fp )
  fp.close( )
  if conf["name"] in channels:
    channels[conf["name"]]["dvr_extra_time_pre"] = conf["dvr_extra_time_pre"]
    channels[conf["name"]]["dvr_extra_time_post"] = conf["dvr_extra_time_post"]
    channels[conf["name"]]["channel_number"] = conf["channel_number"]
    channels[conf["name"]]["tags"] = conf["tags"]
    channels[conf["name"]]["name"] = conf["name"]

path = expanduser( base ) + "/newconf/channels"
mkdir( path )
channelcount = 0
for c in channels:
  t = path + "/channel%d"%channelcount
  mkdir( t )
  channelcount += 1
  fp = open( t + "/config", "w" )
  fp.write( json.dumps( channels[c], sort_keys=True, indent=4 ))
  fp.close( )


# -*- coding: utf-8 -*-
def name():
  return "OSMPOLY_export"
def description():
  return "Generate Poly files used by Osmosis from layers"
def qgisMinimumVersion(): 
  return "1.0" 
def version():
  return "Version " + "0.0.3"
def authorName():
  return "Maxim Dubinin, sim@gis-lab.info"
def classFactory(iface):
  from polygenerator import osmpoly_export
  return osmpoly_export(iface)
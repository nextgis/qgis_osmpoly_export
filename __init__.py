# -*- coding: utf-8 -*-
mVersion = "0.1.4"
def name():
  return "OSMPOLY_export"
def description():
  return "Generate Poly files used by Osmosis from layers"
def category():
  return "Vector"
def icon():
  return "icon.png"
def qgisMinimumVersion():
  return "1.0.0"
def version():
  return "0.1.4"
def authorName():
  return "Maxim Dubinin (NextGIS)"
def classFactory(iface):
  from polygenerator import osmpoly_export
  return osmpoly_export(iface)

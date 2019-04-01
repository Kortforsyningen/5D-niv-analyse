import os, sys
import pprint

def Reorganiser_brugbar_info(file):
	"""
	Omformatter logfilen med brugbar info fra 5d-analyse-kørsel. Det er en tekstfil med oplysning om jessenpunkt, 5d-punkt, stabilitet deraf og antal målinger af hvert punkt i gruppen. 
	"""
	
	d = {}
	
	with open(file) as f:
		for line in f:
			if "Jessen" in line:
				words = line.strip().split()
				d[words[-1]] = {"Jessen" : words[3]}
				femd = words[-1]
			elif str(femd) in line:
				d[femd]["Motion"] = line.strip().split()[3]
				d[femd]["Measured"] = line.strip().split()[-11]
				d[femd]["Stable"] = line.strip().split()[-8]

			
	return d
	
#print(Reorganiser_brugbar_info("brugbarinfo"))
out = Reorganiser_brugbar_info("brugbarinfo")
pp = pprint.PrettyPrinter(indent=4)
pp.pprint(out)

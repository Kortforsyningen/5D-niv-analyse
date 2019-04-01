#!/usr/bin/python 
#########################
##  KMS-format reader(s) 
##
##  simlk, sep. 2011
##
#########################
import string
import datetime
import sys, os
VERBOSE=True
UNITS=["m","dg","sx","nt","rad"]
H_UNIT="m"
VALID_CODES=["r","e","f","g","n","p","t","v",u"u\00E5",u"u\00F8"]
#Max and min length of pointnames
MAX_POINT=25
MIN_POINT=2
def GetLabelDimension(mlb):
	#Has region?#
	if len(mlb)<3 or "_idt" in mlb:
		return 0
	mlb=mlb.strip()
	if mlb[0]=="#":
		mlb=mlb[1:] #delete hash
	if len(mlb)>3 and mlb[0:2].isupper() and mlb[2]=="_":
		mlb=mlb[3:]
	if mlb[0:2]=="h_":
		return 1
	if ("E" in mlb) or ("_h_" in mlb) or ("N" in mlb) or ("crt") in mlb:
		return 3
	return 2 #default

class Test(object):
	def readline(self):
		return raw_input(":> ")+"\n"



def fgetln(fp):
	line=fp.readline()
	out=""
	in_comment=False
	while len(line)>0:
		out+=line
		if "*" in line:
			in_comment=True
		if line.rfind("*")<line.rfind(";") or not in_comment:
			break
		line=fp.readline()
	return TransformSpaces(RemoveComments(out))
	
#Can be used to remove comments in a given chunk of text.....
def RemoveComments_fancy(text):
	out=""
	before,sep,after=text.partition("*")
	while len(after)>0:
		out+=before
		cmt,sep,after=after.partition(";")
		before,sep,after=after.partition("*")
	out+=before
	return out

def MyPartition(text,sep):
	i=text.find(sep)
	if i==-1:
		return text,"",""
	else:
		return text[:i],sep,text[i+len(sep):]

def RemoveComments(text):
	out=""
	before,sep,after=MyPartition(text,"*")
	while len(after)>0:
		out+=before
		cmt,sep,after=MyPartition(after,";")
		before,sep,after=MyPartition(after,"*")
	out+=before
	return out
	
		
def TransformSpaces(text): #Remove single spaces!
	#Well we hope that "_^_^_" is not present in text!
	#out=text.replace("\t"," ")
	out=text.replace("  ","_^_^_")
	out=out.replace(" ","") #Well then remove the SINGLE space....
	out=out.replace("_^_^_"," ")
	return out


def EmptyString2Space(s):
	if s=="":
		return " "
	return s

def TransformSpaces2(text): #simpler but slower
	s=string.join(map(EmptyString2Space,text.split(" ")),"")
	return s


def CleanPointName(text):
	text=unicode(text.decode("latin1"))
	while text[-1] in VALID_CODES:
		text=text[:-1]
	return text

def IsKMSPointName(text): #Very primitive test
	if MIN_POINT<=len(text)<=MAX_POINT:
		return True
	return False
	
		
def IsGPSName(text):
	if len(text)>=4 and text[:4].isupper():
		return True
	return False

def GetKMSFormat(fp):
	bytes=RemoveComments(fp.read())
	bytes=TransformSpaces(bytes)
	return bytes.splitlines()


def GetIDT(fp):
	ids=[]
	mlb=None
	line=fgetln(fp)
	while len(line)>0:
		items=line.split()
		if len(items)==0:
			line=fgetln(fp)
			continue
		if items[0][0]=="#" and mlb is None:
			mlb=items[0][1:]
			if not "idt" in mlb:
				return ids,mlb
		if len(items)>1 and IsKMSPointName(items[0]):
			ids.append(map(CleanPointName,items))
		line=fgetln(fp)
	return ids, mlb

#Assumes a format (KMS) like: point X (unit)  Y (unit) (  Z (unit)) * comment ; etc
def GetCRD(fp,label_in_file=True,read_items=None):
	stations=dict()
	if label_in_file:
		mlb=None #minilabel
		read_items=0
	else:
		mlb="dummy"
		if read_items is None:
			raise ValueError("When label not in file, dimension/number of coords must be specified!") 
	Nerr=0
	line=fgetln(fp)
	while len(line)>0:
		items=line.split()
		if len(items)>0:
			item=items[0]
			if item[0]=="#":
				if label_in_file:
					mlb=item
					read_items=GetLabelDimension(mlb)
				elif VERBOSE:
					print line
			elif read_items>0 and len(items)>read_items:
				point=CleanPointName(item)
				if IsKMSPointName(point):
					items_here=items[1:read_items+1]
					found_units=[]
					if read_items>1:
						planar_unit=""
						for unit in UNITS:
							if (unit in items_here[0]) and (unit in items_here[1]):
								planar_unit=unit
						found_units=[planar_unit]*2
					if (read_items in [1,3]):
						h_item=read_items-1
						if (H_UNIT in items_here[h_item]):
							found_units.append(H_UNIT)
						else:
							found_units.append("")
					OK=True
					for k in range(len(items_here)): 
						try:
							stop_here=len(items_here[k])-len(found_units[k])
							items_here[k]=float(items_here[k][0:stop_here])
						except Exception,msg:
							if VERBOSE:
								print repr(msg)
								print ("Error reading line:\n%s" %line.strip())
								print("items: %s" %repr(items_here))
								print read_items
							OK=False
							Nerr+=1
					if OK:	
						stations[point]=items_here
				elif VERBOSE:
					print("Point: %s does not seem to be a valid point name!, line:\n%s" %(point,line.strip()))
		line=fgetln(fp)
	if Nerr>0 and VERBOSE:
		print("%i formatting errors during file reading...." %Nerr)
	if mlb is not None and mlb[0]=="#":
		mlb=mlb[1:]
	return stations,mlb
	
#Reads a z-time series in KMS-format
def GetSeries(f):
	max_stations=4
	stations=dict()
	has_wor=False
	line_in=fgetln(f)
	Jessen=None
	while len(line_in)>0:
		line=line_in.split()
		if len(line)>0 and line[0]=="beregningsdato":
			year=int(line[1][0:4])
			month=int(line[1][4:6])
			day=int(line[1][6:8])
			has_wor=True
		if len(line)>2 and line[1][-1]=="m":
			station=CleanPointName(line[0])
			if IsKMSPointName(station):
				h=float(line[1][:-1])
				if not has_wor:
					year=int(line[2])
					month=1
					day=1
				m=float(line[-1][-3:])*0.001+0.0005
				type=int(line[-1][0])
				has_wor=False
				if type==9:
					Jessen=station
				else:
					t=datetime.datetime(year,month,day)
					if stations.has_key(station):
						stations[station].append([t,h,m])
					elif len(stations)<max_stations:
						stations[station]=[[t,h,m]]
		line_in=fgetln(f)
	return stations,Jessen

#This func will try to read stations, z and stations, std_dev (mm) as well as meas. dates from a ADJ (niv) file
def ReadADJ_z(f,verbose=False):
	stations=dict()
	dates=[]
	mlb=None
	line_in=fgetln(f)
	Jessen=None
	nerr=0
	state=0 #0 means no coords yet, 1 means we read coords, 2 means we read std_devs, 3 means we read observations....
	read_dates=False
	header_date=None
	while len(line_in)>0:
		line=line_in.split()
		if len(line)>0:
			if line[0][0]=="#":
				if mlb is None:
					mlb=line[0][1:]
				elif "niv" in line[0] or "niDzds" in line[0] or "mtz" in line[0]:
					read_dates=True
			elif state==0 and "jessenpunkt" in line_in.lower():
				di=line_in.rfind(":")
				ds=line_in[di+1:].strip().split("-")
				try:
					year=int(ds[0])
					month=int(ds[1])
					day=int(ds[2])
				except:
					print("Wrong format of header date!")
				else:
					if month>12:
						month=day
						day=int(ds[1])
					print("Interpreting header date as: year %d, month %d, day %d" %(year,month,day))
					try:
						header_date=datetime.datetime(year,month,day)
					except:
						print("Invalid date!")
			elif line[0]=="-1x" or line[0]=="-1z":
				state+=1
			elif state>0:
				station=CleanPointName(line[0])
				if IsKMSPointName(station):
					if state==1 and len(line)>1 and len(line[1])>1 and line[1][-1]=="m" and (line[1][-2]).isdigit():
						try:
							z=float(line[1][:-1])
						except:
							nerr+=1
							if verbose:
								print("Error in %s" %line_in)
						else:
							stations[station]=[z]
					elif state>1 and len(line)==2 and line[1][-2:]=="mm": #then we read sd's
						try:
							mf=float(line[1][:-2])
						except:
							nerr+=1
							if verbose:
								print("Error in %s" %line_in)
						else:
							if stations.has_key(station):
								stations[station].append(mf)
			if read_dates and len(line)>5:
				station=CleanPointName(line[0]) #find the right line to look for a date....
				if stations.has_key(station) and line[1][-1]=="m":
					try:
						date=line[3]
						year=int(date[0:4])
						month=int(date[4:6])
						day=int(date[6:8])
					except:
						nerr+=1
						if verbose:
							print("Error in %s" %line_in)
					else:
						dates.append(datetime.datetime(year,month,day))
		line_in=fgetln(f)
	#Calculate mean observation date#
	if len(dates)==0 and header_date is not None:
		print("No observation dates found - using header date. Check that this is OK!!!!")
		dates=[header_date]
	if len(dates)>0:
		time_span=(max(dates)-min(dates)).days
		if time_span>180:
			print("Warning! Large time span in measurements: %i days" %time_span)
		dt=datetime.timedelta(0)
		if len(dates)>1:
			for date in dates[1:]:
				dt+=dates[0]-date
		dt/=(len(dates))
		mean_date=dates[0]+dt
	else:
		print("No observation dates found in file!")
		mean_date=None
		time_span=None
	return stations,mean_date,time_span,mlb,nerr



def ReadVectors(f,verbose=False):
	stations=dict()
	vectors=dict()
	mlbs=[]
	line_in=fgetln(f)
	Jessen=None
	nerr=0
	state=0 #0 means no coords yet, 1 means we read coords of fixed stations, 2 means we read coords of comp. stations, 3 means we read observations....
	mode=0 #0 means start new vector, 1 means finish current vector
	while len(line_in)>0:
		line=line_in.split()
		if len(line)>0:
			if line[0][0]=="#":
				mlb=line[0][1:]
				if mlb not in mlbs:
					mlbs.append(mlb)
			elif line[0]=="-1x" or line[0]=="-1z":
				state+=1
			elif state==0 or state==1:
				station=CleanPointName(line[0])
				if IsKMSPointName(station):
					try:
						y=float(line[1].replace("m",""))
						x=float(line[2].replace("m",""))
						z=float(line[3].replace("m",""))
					except:
						if verbose:
							print("Bad line: %s" %line_in)
					else:
						if stations.has_key(station):
							print("Double defined station %s" %station)
						stations[station]=[x,y,z,1-state]
			elif state>1:
				station=CleanPointName(line[0])
				if IsKMSPointName(station):
					if mode==0 and station[-1]=="a":
						try:
							int(line[2])
						except:
							pass
						else:
							station=station[:-1]
							vstart=station
							mode=1
					elif mode==1 and line[1][-1]=="m":
						try:
							x=float(line[1].replace("m",""))
							y=float(line[1].replace("m",""))
							z=float(line[3].replace("m",""))
						except:
							pass
						else:
							mode=0
							vectors[(vstart,station)]=[x,y,z]
		line_in=fgetln(f)
	return stations,vectors,mlbs
			
				
						
			
	


if __name__=="__main__":
	print("This is a library script containing functions designed to read KMS-format output.")
	print("Include this in your main python script!")
	sys.exit()

					
					
				
								
	
					
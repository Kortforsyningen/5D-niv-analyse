#!/usr/bin/python 
######################################
## Script to extract z-timeseries from ADJ-output files
## Uses Eksm.py library functions!
## simlk, oct. 2011
## Last update: 2012-04-13
######################################
STD_ADJ_DIR="/export/home/ADJ_RES/ADJ_TSRES"
GET_LOC_CMD="fromcrd "
GET_IDT_CMD="fromidt "
SL="*"*50
try:
	import Ekms
except ImportError:
	print("Could not import Ekms.py... Is this script removed??")
	sys.exit()
import sys,os,glob,datetime

def GetData(input_files):
	all_data=dict()
	nok=0
	for fname in input_files: #we HOPE that station naming is consistent across ADJ-files!!!!! otherwise we can use fromidt....
		try:
			f=open(fname)
		except:
			print("Could not open %s!" %fname)
			continue
		print("%s" %SL)
		print("Reading %s" %fname)
		stations,mean_date,time_span,mlb,nerr=Ekms.ReadADJ_z(f,True)
		f.close()
		if len(stations)==0:
			print("No stations found in %s" %fname)
			continue
		if mean_date is None:
			print("Mean observation date could not be calculated!")
			print("Perhaps there are no niv observations included in %s?" %fname)
			print("Trying to get date from filename.")
			tokens=os.path.splitext(os.path.basename(fname))[0].split("_")
			if len(tokens)>1 and len(tokens[1])>=8:
				date=tokens[1]
				try:
					year=int(date[0:4])
					month=int(date[4:6])
					day=int(date[6:8])
				except:
					print("Date could not be extracted from filename!")
					continue
				if month>12 and day<=12:
					print("Switching day and month!")
					sday=day
					day=month
					month=sday
				try:
					mean_date=datetime.datetime(year,month,day)
				except:
					print("Date could not be extracted from filename!")
					continue
				print("Using date: year: %d, month: %d, day: %d" %(year,month,day))
			else:
				print("Date could not be extracted from filename!")
				continue
		if "hts" not in mlb:
			print("Is this really a z-timeseries ADJ output file? Minilabel seems to be %s." %mlb)
			print("Skipping data!")
			continue
		if nerr>0:
			print("Got %i formatting errors reading %s" %(nerr,fname))
		print("Got %i stations, mean date is %s, time span is %i day(s)" %(len(stations),mean_date.isoformat()[:10],time_span+1))
		nok+=len(stations)
		for station in stations.keys():
			if all_data.has_key(station):
				all_data[station].append(stations[station]+[mean_date])
			else:
				all_data[station]=[stations[station]+[mean_date]]
	return all_data,nok


	
def Usage():
	print("To run:\n%s <jessen_nr> [<adj_dir>]" %os.path.basename(sys.argv[0]))
	print("<adj_dir> is optional, if not given will default to: "+STD_ADJ_DIR)
	print("Will output time series and locations of data extracted from files in adj_dir")
	sys.exit()
	

def main(args):
	if len(args)<2:
		Usage()
	jessen_nr=args[1]
	if len(jessen_nr)<5 and jessen_nr[0:2]!="81":
		jessen_nr="81"+jessen_nr
	try:
		int(jessen_nr)
	except:
		print("Input: %s can't be converted to a number!" %jessen_nr)
		Usage()
	if len(args)>2:
		ADJ_DIR=args[2]
	else:
		ADJ_DIR=STD_ADJ_DIR
	print("Looking for files in "+ADJ_DIR)
	pat=os.path.join(ADJ_DIR,"*_%s_1d*" %jessen_nr)
	print("Looking for files like: %s" %pat) 
	files=glob.glob(pat)
	real_files=[]
	for fname in files:
		if "geo" in os.path.basename(fname):
			continue
		real_files.append(fname)
	print("Found %i matching files in %s" %(len(real_files),ADJ_DIR))
	if len(real_files)==0:
		Usage()
	outname_ts="ts_%s.txt" %jessen_nr
	outname_xy="ts_%s_loc.txt" %jessen_nr
	try:
		out_fp=open(outname_ts,"w")
	except:
		print("Could not create %s" %outname_ts)
		sys.exit(1)
	data,nfound=GetData(real_files)
	if nfound==0:
		print("No data found in files!")
		sys.exit(1)
	print("\nFound %i z-measurements in files and %i stations" %(nfound,len(data)))
	print("Testing for uniquness of stations via %s." %GET_IDT_CMD)
	#Get ids of stations#
	tmp_id_name="tmp_id_%s.txt" %jessen_nr
	outname_id="id_%s.txt" %jessen_nr
	try:
		tmp_fp=open(tmp_id_name,"w")
	except:
		print("Could not open %s!" %tmp_id_name)
		sys.exit(1)
	tmp_fp.write("#DK_idt    *help file to get ids for ts: %s;\n" %jessen_nr)
	for station in data.keys():
		tmp_fp.write("%s\n" %station)
	tmp_fp.write("-1z\n")
	tmp_fp.close()
	rc=os.system("%s -f %s -o %s" %(GET_IDT_CMD,tmp_id_name,outname_id)) #test return code?
	print("Return code: %i" %rc)
	try:
		f=open(outname_id,"r")
	except:
		print("Could not open output id file from %s!" %GET_IDT_CMD)
		sys.exit(1)
	ids,mlb=Ekms.GetIDT(f)
	f.close()
	if not "idt" in mlb:
		print("Is %s really an id file? Minilabel is: %s" %(outname_id,mlb))
	else:
		stations_set=set(data.keys())
		for translation in ids:
			trans_set=set(translation)
			intersect=trans_set.intersection(stations_set)
			#test merge#
			if len(intersect)>1:
				print("Found identical points %s, merging data." %repr(translation))
				merge_data=[]
				for station in intersect:
					merge_data.extend(data[station])
				stations=list(intersect) 
				keep=stations[0] #or translation[0]
				print("Keeping %s" %keep)
				data[keep]=merge_data
				for station in stations[1:]:
					del data[station]
					stations_set.remove(station)
	
	#Get locations of points#
	tmp_loc_name="tmp_loc_%s.txt" %jessen_nr
	try:
		tmp_fp=open(tmp_loc_name,"w")
	except:
		print("Could not generate %s!" %tmp_loc_name)
		sys.exit(1)
	tmp_fp.write("#DK_utm32Leuref89     *help file to get locations for ts: %s;\n" %jessen_nr)
	tmp_fp.write("%s\n" %jessen_nr)
	for station in data.keys():
		tmp_fp.write("%s\n" %station)
	tmp_fp.write("-1z\n")
	tmp_fp.close()
	#Now use fromcrd to get locations#
	print("Getting locations of points via %s." %GET_LOC_CMD)
	rc=os.system("%s -f %s -o %s" %(GET_LOC_CMD,tmp_loc_name,outname_xy)) #test return code?
	print("Return code: %i" %rc)
	#Write output file#
	out_fp.write("Jessen_pkt:  %s\n" %jessen_nr)
	for station in data.keys():
		ts=data[station]
		for meas in ts:
			z=meas[0]
			date=meas[-1].isoformat()[:10]
			if len(meas)==2:
				mf="NAN"
			else:
				mf="%.3f" %(meas[1])
			out_fp.write("%-13s  %.7f  %-7s  %s\n" %(station,z,mf,date))
	out_fp.close()
	loc_fp=open(outname_xy)
	xy,mlb=Ekms.GetCRD(loc_fp)
	loc_fp.close()
	del data
	print("Found %i point locations in %s" %(len(xy),outname_xy))
	outname_xy2="ts_%s_xy.txt" %jessen_nr
	print("Tranlating coord list to a more readable format in %s" %outname_xy2)
	loc_fp=open(outname_xy2,"w")
	loc_fp.write("Name,x,y\n")
	for station in xy.keys():
		y,x=xy[station]
		loc_fp.write("%s,%.2f,%.2f\n" %(station,x,y))
	loc_fp.close()
	sys.exit()

if __name__=="__main__":
	main(sys.argv)

	
	
			
		
		
	
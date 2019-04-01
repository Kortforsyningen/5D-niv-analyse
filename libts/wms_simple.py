basestring="""
http://kortforsyningen.kms.dk/service?
servicename=servicename
&REQUEST=GetMap
&VERSION=1.1.1
&SRS=EPSG:25832
&BBOX=xmin,ymin,xmax,ymax
&WIDTH=WIDTH
&HEIGHT=HEIGHT
&STYLES=
&LAYERS=
&ignoreillegallayers=TRUE
&FORMAT=image/png
&BGCOLOR=0xffffff
&TRANSPARENT=FALSE
&EXCEPTIONS=application/vnd.ogc.se_inimage
&login=kms1
&password=adgang
"""
import urllib
def WMSmap(x1,x2,y1,y2,width,height,servicename="topo_skaermkort",layers=["dtk_skaermkort"],outname="map.png"):
	global basestring
	url=basestring.replace("xmin",str(x1)).replace("ymin",str(y1)).replace("xmax",str(x2)).replace("ymax",str(y2))
	url=url.replace("WIDTH=WIDTH","WIDTH=%i" %width).replace("HEIGHT=HEIGHT","HEIGHT=%i" %height)
	url=url.replace("=servicename","=%s" %servicename)
	if servicename=="ortofoto":
		url=url+"&LAYERS=Orto_dk"
		mr=max(x2-x1,y2-y1)
		if mr>4000:
			url=url+"&Jpegquality=30"
		elif mr>2000:
			url=url+"&Jpegquality=40"
		else:
			url=url+"&Jpegquality=80"
	if len(layers)>0:
		lstring=""
		for layer in layers:
			lstring+=layer+","
		lstring=lstring[0:-1] #delete last ','
		url=url.replace("&LAYERS=","&LAYERS=%s" %lstring)
	url=url.replace("\n","") #slet newlines
	try:
		f=urllib.urlopen(url)
		inf=str(f.info())
		#print inf
		g=f.read()
		f.close()
	except:
		return False
	if True:
		f=open(outname,"wb")
		f.write(g)
		f.close()
		return True
	else:
		print str(g),inf
		return False
		
		
	
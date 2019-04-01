#!/usr/bin/python
##############################
## Nice 5D-timeseries report generator   ##
## simlk, sep. 2011  
##############################
TABLE_ROW="""<tr>
<td style="vertical-align: top;">N__P__<br>
</td>
<td style="vertical-align: top;">ST__P__<br>
</td>
<td style="vertical-align: top;">SL__P__<br>
</td>
<td style="vertical-align: top;">NM__P__<br>
</td>
<td style="vertical-align: top;">MO__P__<br>
</td>
<td style="vertical-align: top;">SD__P__<br>
</td>
<td style="vertical-align: top;">SIG__P__<br>
</td>
<td style="vertical-align: top;">STA__P__<br>
</td>
</tr>
"""
SIM_MATRIX_HEADER="""<table style=" text-align: left; width: 75%;" border="1"
cellpadding="2" cellspacing="2">
<tbody>
<tr>
"""
MATRIX_ENTRY="""<td style="vertical-align: top; text-align: center;">Punkt<br>
</td>
"""
#'codes' to locate insertion points in template....
T1_MARK="__T1__"
T2_MARK="__T2__"
LINK_CODE="__INSERT_LINKS_HERE__"
SIM_TABLE_BEGIN="__SIM_TABLE_BEGIN__"
SIM_TABLE_END="__SIM_TABLE_END__"
#W,H for mapwindow
MAPW=500
MAPH=400
PIXMIN=0.25 

import os,sys
import time
import matplotlib
#important to set up mpl here before importing ts 
if not sys.platform.startswith("win"):
    matplotlib.use("cairo")
import matplotlib.pyplot as plt
from matplotlib.dates import date2num
import numpy as np
from libts import ts, wms_simple
PROGNAME="5d.py v. 0.2"
PROGDATE="2015-08-19"
TEMPLATE=os.path.join(os.path.dirname(__file__),"libts","Template.html")
MAX_PTS=7 #maximal number of points for html....
DEBUG=False

def PlotMany(stations,title="Time Series",save_name=None,legend=True):
    #Make a graph with all timeseries
    plt.ioff()
    plt.figure()
    nl=0
    plt.xticks(rotation=35)
    COLORS=["red","blue","green","black","yellow","brown","pink"]
    for station in stations.keys():
        ts=stations[station]
        ts_dates=date2num(ts[:,0])
        z=ts[:,1].astype(np.float64)
        if ts.shape[0]>1:
            color=COLORS[nl%len(COLORS)]
            dz=z-z.mean()
            plt.plot_date(ts_dates,dz,marker="+",label="_nolegend_",color=color)
            plt.plot(ts_dates,dz,"-",label=station,color=color)
            nl+=1
    if title is not None:
        plt.title(title)
    plt.xlabel("Time")
    plt.ylabel("dz [m]")
    if legend:
        plt.legend()
    if save_name is None:
        plt.show()
    else:
        plt.savefig(save_name)

def PlotDetailed(ts,a,b,title=None,save_name=None,ignore_limit=0,sd_interval=2.0):
    #Make a detailed plot of a single timeseries
    plt.ioff()
    plt.figure()
    if title is not None:
        plt.title(title)
    #ts=np.array(ts) it os an array now! 
    ts_dates=date2num(ts[:,0])
    z=ts[:,1].astype(np.float64)
    e=sd_interval*ts[:,2].astype(np.float64)
    m=z.mean()
    dz=z-m
    tmin=min(ts_dates)
    tmax=max(ts_dates)
    tbuf=(tmax-tmin)*0.1
    plt.xticks(rotation=35)
    plt.plot_date(ts_dates,dz,marker="o",label="_nolegend_",color="cyan")
    plt.errorbar(ts_dates,dz,e,fmt="-",marker="s",label="%.1f*middelfejl"%sd_interval,color="blue")
    #plt.plot(ts_dates,dz,".",label=u"m\u00E5linger")
    line_x=np.array([tmin-tbuf,tmax+tbuf])
    if z.shape[0]>=2:
        if z.shape[0]==2:
            a=(dz[1]-dz[0])/(ts_dates[1]-ts_dates[0])
            b=dz[0]-a*ts_dates[0]
            line_y=a*line_x+b
        elif (a is not None) and (b is not None):
            line_y=a*line_x+b-m
        plt.plot(line_x,line_y,"--",label="Bedste rette linie",color="red")
    zl=[0,0]
    plt.plot(line_x,zl,"--",label="_nolegend_",color="green")
    if ignore_limit>0 and np.fabs(dz).max()*3>ignore_limit: #should be some variation in dz relative to ilim before we want to plot that
        irad=ignore_limit*0.5
        plt.plot(line_x,[irad,irad],"--",label="_nolegend_",color="green")
        plt.plot(line_x,[-irad,-irad],"--",label="_nolegend_",color="green")
    plt.xlabel("Time [y]")
    plt.ylabel("dz [m]")
    plt.legend()
    #plt.xlim(tmin-tbuf,tmax+tbuf)
    if save_name is None:
        plt.show()
    else:
        print("Saving %s" %save_name)
        plt.savefig(save_name)

def Usage():
    #OMG: why do we still use python26 on linux and do not have argparse...
    sys.stdout=sys.__stdout__
    msg="To run:\n%s <z_time_series> <point_locations> -inc <file_name_poi> -o <outdir>" %os.path.basename(sys.argv[0])
    msg+=" -html -log <file_name> -map -kurt"
    msg+=" -min <year1> -max <year2>"
    print(msg)
    print("-o <outdir> is optional. If not present program will save output to current (working) dir.")
    print("-html (optional) will turn ON generation of plots and html result page.")
    print("-log <file_name> (optional) will save text output to file with name file_name.")
    print("-map (optional) adds map fetched via wms from 'kortforsyningen'.")
    print("-inc <file_name_poi> specifies a file containing the names of the points to be included in analysis.")
    print("-nosim (optional) Do NOT generate similarity matrix table.")
    print("-kurt (optional) reads first input file in Kurt's format - no location file needed then!")
    print("-min <year1> used to set a minimum year of interest.")
    print("-max <year2> used to set a maximum year of interest.")
    print("-gis <outname>(optional) Export data as a csv-file given in outname.")
    print("-ilim <ignore_limit> Specify the 'ignore limit' for stability tests in [mm].")
    print("-sdi <ignore_limit> Specify the 'error interval' for stability tests, e.g. 2.0") 
    print("REMEMBER to include a space between option switch and option value!")
    
    sys.exit()

class RedirectStdout(object):
    """
    Class to redirect stdout to a file.
    """
    def __init__(self,fp=None):
        self.fp=fp
    def write(self,text):
        sys.__stdout__.write(text)
        if self.fp is not None:
            try:
                self.fp.write(text)
            except:
                pass

def main(args):
    #OMG: argparing. Should really use argparse (python27)
    if len(args)<3:
        Usage()
    log_file=None
    inc_file=None
    min_year=None
    max_year=None
    if "-log" in args:
        try:
            fname=args[args.index("-log")+1]
            log_file=open(fname,"w")
        except:
            
            print("Could not open logfile!")
            Usage()
        else:
            print("Using logfile: %s" %fname)
            sys.stdout=RedirectStdout(log_file)
    if "-inc" in args:
        try:
            fname=args[args.index("-inc")+1]
            inc_file=open(fname,"r")
        except:
            print("Could not open file with list of included points!")
            Usage()
    #now start program#
    print("Running %s at %s on input file: %s" %(PROGNAME,time.asctime(),args[1]))
    if "-min" in args:
        try:
            min_year=int(args[args.index("-min")+1])
        except:
            Usage()
    if "-max" in args:
        try:
            max_year=int(args[args.index("-max")+1])
        except:
            Usage()
    if "-ilim" in args:
        try:
            ilim=float(args[args.index("-ilim")+1])
        except:
            print("-ilim must be a float!")
            Usage()
        ts.SetIgnoreLimit(ilim)
    if "-sdi" in args:
        try:
            sdi=float(args[args.index("-sdi")+1])
        except:
            print("-sdi must be a float!")
            Usage()
        ts.SetStabilityInterval(sdi)
    if "-kurt" in args:
        ts_file=args[1]
        try:
            f=open(ts_file)
        except:
            print("Could not open input file...")
            if log_file is not None:
                log_file.close()
            Usage()
        stations,attrs,coords,Jessen=ts.GetMotions(f,inclusion_file=inc_file,format="KURT",min_y=min_year,max_y=max_year)
        f.close()
        Jessen=None
    else:
        ts_file=args[1]
        xy_file=args[2]
        try:
            f=open(ts_file)
            g=open(xy_file)
        except:
            print("Could not open input files...")
            if log_file is not None:
                log_file.close()
            Usage()
        stations,attrs,coords,Jessen=ts.GetMotions(f,g,inclusion_file=inc_file,min_y=min_year,max_y=max_year)
        f.close()
        g.close()
    if "-gis" in args:
        out=args[args.index("-gis")+1]
        print("Exporting data in gis-format as %s" %out)
        ts.ExportData(stations,attrs,coords,out,",","-swap_xy" in args)
    if Jessen is not None:
        plot_title="Jessen pkt. %s" %Jessen
    else:
        plot_title=None
    template=TEMPLATE
    if len(stations)==0:
        Usage()
    if "-html" not in args: #dont do anything further!!
        if log_file is not None:
            log_file.close()
        if inc_file is not None:
            inc_file.close()
        return
    if len(stations)>MAX_PTS and "-inc" not in args:
        print("%i points found, restricting to the 'first' %i points for html page." %(len(stations),MAX_PTS))
        stations=dict(stations.items()[:MAX_PTS])  #restrict to maximal number of pts.
    if "-o" in args:
        outdir=args[args.index("-o")+1]
        if not os.path.exists(outdir):
            os.mkdir(outdir)
    else:
        outdir=os.getcwd()
    keys=stations.keys()
    main_title=os.path.splitext(os.path.basename(ts_file))[0]
    graph_name=os.path.join(outdir,main_title+"_graph.png")
    PlotMany(stations,plot_title,graph_name)
    graph_name_no_legend=os.path.join(outdir,main_title+"_graph_no_legend.png")
    PlotMany(stations,plot_title,graph_name_no_legend,False)
    map_name=os.path.join(outdir,main_title+"_map.png")
    map_name_no_names=os.path.join(outdir,main_title+"_map_no_names.png")
    #Get coords#
    XY=np.empty((0,2))
    PLT_NAMES=[]
    for station in keys+[Jessen]:
        if coords.has_key(station):
            x,y=coords[station]
            if x is not None:
                XY=np.vstack((XY,[x,y]))
                PLT_NAMES.append(station)
    #Determine bounds of map#
    map_size=np.array([MAPW,MAPH],dtype=np.float64)
    min_xy=XY.min(axis=0)
    max_xy=XY.max(axis=0)
    c_xy=(max_xy+min_xy)*0.5
    buf=(max_xy-min_xy)*0.1
    p_xy=(max_xy-min_xy+buf)/map_size
    pix=max(PIXMIN,p_xy.max()) #gst pixelsize
    xmax,ymax=c_xy+0.5*pix*map_size
    xmin,ymin=c_xy-0.5*pix*map_size
    #Construct map#
    plt.ioff()
    plt.figure()
    plt.title("Kort")
    if "-map" in args:
        #Fetch map via wms#
        print("Fetching map via wms......")
        wms_out=os.path.join(outdir,main_title+"_wms.png")
        OK=wms_simple.WMSmap(xmin,xmax,ymin,ymax,MAPW,MAPH,outname=wms_out)
        if OK:
            im=plt.imread(wms_out)
            plt.imshow(im,extent=(xmin,xmax,ymin,ymax))
    plt.scatter(XY[:,0],XY[:,1],s=12)
    plt.xlabel("[m]")
    plt.ylabel("[m]")
    plt.savefig(map_name_no_names)
    for i in range(XY.shape[0]):
        plt.text(XY[i,0]+2*pix,XY[i,1]+2*pix,PLT_NAMES[i])
    plt.savefig(map_name)
    if DEBUG:
        plt.show()
    #Write HTML#
    f=open(template)
    html=f.read()
    f.close()
    #Do replacements#
    html=html.replace("THE_GRAPH_NO_LEGEND",os.path.basename(graph_name_no_legend)) # important that this is before the other below
    html=html.replace("THE_GRAPH",os.path.basename(graph_name))
    html=html.replace("THE_MAP_NO_NAMES",os.path.basename(map_name_no_names)) #as above...
    html=html.replace("THE_MAP",os.path.basename(map_name))
    html=html.replace("__STABILITY_SD_MULTIPLIER__","%.1f" % ts.STABILITY_SD_MULTIPLIER)
    if Jessen is not None:
        Jessen_text=u"Analyse af bev\u00E6gelser relativt til Jessen punkt: %s" %Jessen
    else:
        Jessen_text=""
    html=html.replace("__JESSEN__",Jessen_text.encode("latin1"))
    html=html.replace("__title__",main_title)
    html=html.replace("__VERSION__",PROGNAME)
    html=html.replace("__DATE__",time.asctime())
    html=html.replace("__IGNORE_LIMIT__","%.2f" %ts.IGNORE_LIMIT)
    restrict_text=""
    if min_year is not None:
        restrict_text+="Min_year sat til: %d." %min_year
    if max_year is not None:
        restrict_text+=" Max_year sat til: %d" %max_year
    html=html.replace("__RESTRICT__",restrict_text)
    subhtml1=""
    subhtml2=""
    for station in keys:
        tmin,tmax,n,a,sa,signif,stable,a_plot,b_plot,corr_coeff=attrs[station]
        #transform to app. strings#
        n=str(n)
        if n>1:
            a="%.4f" %a
            sa="%.4f" %sa
            if (signif):
                signif="JA"
            else:
                signif="NEJ"
            if (stable):
                stable="JA"
            else:
                stable="NEJ"
        else:
            stable="NA"
            signif="NA"
            a="NAN"
            b="NAN"
        html_row=TABLE_ROW.replace("N__P__",station)
        html_row=html_row.replace("ST__P__",tmin)
        html_row=html_row.replace("SL__P__",tmax)
        html_row=html_row.replace("NM__P__",n)
        html_row=html_row.replace("MO__P__",a)
        html_row=html_row.replace("SD__P__",sa)
        html_row=html_row.replace("SIG__P__",signif)
        html_row=html_row.replace("STA__P__",stable)
        subhtml1+=html_row
        series=stations[station]
        if series.shape[0]>1:
            graph_name=os.path.join(outdir,main_title+"_%s.png" %station)
            PlotDetailed(series,a_plot,b_plot,station,graph_name,ignore_limit=ts.IGNORE_LIMIT*0.001,sd_interval=ts.STABILITY_SD_MULTIPLIER)
            subhtml2+='<a href="./%s">%s</a><br>\n' %(os.path.basename(graph_name),station)
    #Find the end of first row in second table#
    insert_here=html.find(T1_MARK)
    insert_here+=html[insert_here:].find("</tr>")
    insert_here+=html[insert_here:].find("\n")+1 #position after newline after table header row
    html=html[:insert_here]+subhtml1+html[insert_here:] #insert table rows
    html=html.replace(T1_MARK,"") #remove loaction code
    #Locate insertion point for links to images at bottom of page#
    insert_here=html.find(LINK_CODE)
    html=html[:insert_here]+subhtml2+html[insert_here+len(LINK_CODE):]
    #construct sim-matrix table #
    if not ("-nosim" in args):
        for station in keys:
            if len(stations[station])<2:
                del stations[station]
        keys=stations.keys()
        subhtml=SIM_MATRIX_HEADER+MATRIX_ENTRY
        for i in range(len(keys)): #construct header row "Punkt" P1 P2 P3 ....
            subhtml+=MATRIX_ENTRY.replace("Punkt",keys[i])
        subhtml+="</tr>\n"
        for i in range(len(keys)): #every row starts with Point name, thus first/header column = header row
            row="<tr>\n"+MATRIX_ENTRY.replace("Punkt",keys[i])
            for j in range(len(keys)):
                if j>i:
                    m1,m2,c=ts.Overlap(ts.GetTS(stations[keys[i]]),ts.GetTS(stations[keys[j]]),ts.IGNORE_LIMIT*0.001)
                    row+=MATRIX_ENTRY.replace("Punkt","%.2f" %c)
                else:
                    row+=MATRIX_ENTRY.replace("Punkt","***")
            row+="</tr>\n"
            subhtml+=row
        subhtml+="</tbody>\n</table>\n<br>\n"
        #end construct sim-matrix#
        #insert table at mark#
        insert_here=html.find(T2_MARK)
        insert_here+=html[insert_here:].find("\n")+1 #position after newline after mark
        html=html[:insert_here]+subhtml+html[insert_here:]
        html=html.replace(T2_MARK,"") #remove mark
        html=html.replace(SIM_TABLE_BEGIN,"")
        
    else:
        i=html.find(SIM_TABLE_BEGIN)
        j=html.find(SIM_TABLE_END)
        if (i>0 and j>0):
            html=html[:i]+html[j:]
    html=html.replace(SIM_TABLE_END,"")
    #end insert table#
    outname=os.path.join(outdir,main_title+".html")
    print("Generating html page %s" %outname)
    f=open(outname,"w")
    f.write(html)
    f.close()
    if log_file is not None:
        log_file.close()
    if inc_file is not None:
        inc_file.close()
    return 0

if __name__=="__main__":
    sys.exit(main(sys.argv))
        

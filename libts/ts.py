#################################
## NIV. Z-Time Series Analysis Module
## simlk, sep. 2011
## modified feb. 2019 MAJWS (init, MyReader, POIReader, GetMotion)
##################################
import numpy as np
try:
    import matplotlib.pyplot as plt
except:
    HAS_MPL=False
else:
    HAS_MPL=True
import os
import sys
import datetime
from math import sqrt
DEBUG=False
IGNORE_LIMIT= 0.1   #[mm] limit for ignoring small motions when determining unstability.
STABILITY_SD_MULTIPLIER=2.0  #what factor to multiply standard deviation by for stability test.
TREND_SD_MULTIPLIER=2.5  #what factor to multiply standard deviation by for test for significant trend.
#I think that this really shouldn't be included cause uncertainties are relative to Jessen point, i.e. depend on distance to this point.
#otherwise it should be some geo-physical consideration, that we accept certain distance dependent relative motions. 
DIST_DEP=0 #so really small for now!
MAX_PTS=1000
APRIORI_SD=1.5  #apriori std_dev - used if sd not given

# List of 5d points in db pr February 2019. Update the list for next run.
fivedpoints = ["G.I.2065","G.I.2109","G.I.2113","G.I.2114","G.I.2120","G.I.2123","G.I.2125","G.I.2127","G.I.2134","G.I.2135","G.I.2139","G.I.2141","G.I.2143","G.I.2144","G.I.2146","G.I.2148","G.I.2149","G.I.2150","G.I.2152","G.I.2154","G.I.2155","G.I.2156","G.I.2157","G.I.2158","G.I.2159","G.I.2160","G.I.2162","G.I.2164","G.I.2165","G.I.2190","G.I.2193","G.I.2194","G.I.2195","G.I.2196","G.I.2197","G.I.2198","G.I.2199","G.I.2200","G.I.2201","G.I.2202","G.I.2207","G.I.2210","G.I.2212","G.I.2213","G.I.2214","G.I.2215","G.I.2217","G.I.2218","G.I.2219","G.I.2220","G.I.2221","G.I.2222","G.I.2223","G.I.2224","G.I.2230","G.I.2232","G.I.2233","G.I.2234","G.I.2236","G.I.2237","G.I.2241","G.I.2242","G.I.2243","G.I.2244","G.I.2245","G.I.2246","G.I.2247","G.I.2248","G.I.2249","G.I.2250","G.I.2251","G.I.2252","G.I.2256","G.I.2257","G.I.2258","G.I.2259","G.I.2261","G.I.2264","G.I.2271","G.I.2274","G.I.2278","G.I.2281","G.I.2286","G.I.2288","G.I.2290","G.I.2294","G.I.2297","G.I.2300","G.I.2305","G.I.2308","G.I.2311","G.I.2312","G.I.2315","G.I.2318","G.I.2319","G.I.2320","G.I.2326","G.I.2330","G.I.2332","G.I.2336","G.I.2338","G.I.2349","G.I.2354","G.I.2355","G.I.2358","G.I.2361","G.I.2365","G.I.2367","G.I.2371","G.I.2372","G.I.2375","G.I.2377","G.I.2379","G.I.2381","G.I.2382","G.I.2385","G.I.2387","G.I.2390","G.I.2391"]

# Function definition starts. These are called through 5d.py
def NoLog(text):
    print text
LOG_METHOD=NoLog

def SetLogMethod(f):
    global LOG_METHOD
    LOG_METHOD=f

def SetIgnoreLimit(ilim):
    global IGNORE_LIMIT
    IGNORE_LIMIT=ilim

def SetStabilityInterval(sdi):
    global STABILITY_SD_MULTIPLIER
    STABILITY_SD_MULTIPLIER=sdi

def StabilityTest(diff,dist=0):
    #Not used anymore....
    return diff<(IGNORE_LIMIT+dist*DIST_DEP)


def GetTS(data):
    data=np.array(data) 
    data=np.column_stack((map(lambda x:x.toordinal(),data[:,0]),data[:,1:])).astype(np.float64)
    return data

def GetTimeSpan(ts):
     #ts=np.array(ts)
     tmin=ts.min(axis=0)[0].isoformat()[:10]
     tmax=ts.max(axis=0)[0].isoformat()[:10]
     return tmin,tmax
     
def KurtReader(f,poi=None,min_y=None,max_y=None): #returns SORTED ts
    badlines=0
    stations=dict()
    xy=dict()
    if min_y is not None:
        min_y=datetime.datetime(min_y,1,1)
    if max_y is not None:
        max_y=datetime.datetime(max_y+1,1,1)
    line=f.readline()
    while len(line)>0:
        sline=line.split()
        if 0<len(sline)<10 and line[0]!="#":
            LOG_METHOD("Wrong line: %s" %line.strip())
            badlines+=1
        else:
            try:
                station=sline[0].replace("/", "-")
                y=float(sline[1])
                x=float(sline[2])
                z=float(sline[3])
                year=int(sline[4])
                month=int(sline[5])
                day=int(sline[6])
                sx=float(sline[7])
                sy=float(sline[8])
                sz=float(sline[9])
            except:
                LOG_METHOD("Wrong line: %s" %line.strip())
                badlines+=1
            else:
                if poi is not None and (not station in poi):
                    #LOG_METHOD("Skipping point %s" %station)
                    line=f.readline()
                    continue
                t=datetime.datetime(year,month,day)
                if min_y is not None and t<min_y:
                    line=f.readline()
                    continue
                if max_y is not None and t>max_y:
                    line=f.readline()
                    continue
                if stations.has_key(station):
                    stations[station].append([t,z,sz*0.001])
                else:
                    stations[station]=[[t,z,sz*0.001]]
                xy[station]=[x,y]  #make same order as KMS-format
        line=f.readline()
    #If we are unlucky, things might get read in an unsorted state wrt time, so sort it now!#
    for station in stations.keys():
        ts=np.array(stations[station])
        I=np.argsort(ts[:,0])
        stations[station]=ts[I]
    return stations,xy #No Jessen point
                

def MyReader(f,poi=None,max_pts=10000,min_y=None,max_y=None): #returns SORTED ts
    badlines=0
    found_items=0
    stations=dict()
    line=f.readline()
    Jessen=None
    if min_y is not None:
        min_y=datetime.datetime(min_y,1,1)
    if max_y is not None:
        max_y=datetime.datetime(max_y+1,1,1)
    while len(line)>0:
        sline=line.split()
        if Jessen is None and "jessen" in line.lower():
            Jessen=sline[1]
        elif len(sline)>2 and sline[0][0]!="#":
            station=sline[0].replace("/", "-")  #MWS Replace slash like in POIReader
            try:
                z=float(sline[1])
            except:
                LOG_METHOD("Wrong line: %s" %line.strip())
                badlines+=1
            else:
                next_item=2
                try:
                    if len(sline)>3:
                        sz=float(sline[2])
                        next_item+=1
                        found_items=4
                    else:
                        sz=APRIORI_SD
                        if (found_items==4):
                            LOG_METHOD("Weird format - found sd in previous line, but not in this...")
                    y,m,d=sline[next_item].split("-")
                    #test if reverse format
                    if len(d)==4:
                        tmp=d
                        d=y
                        y=tmp
                        
                    y=int(y)
                    m=int(m)
                    d=int(d)
                except:
                    LOG_METHOD("Wrong line: %s" %line.strip())
                    badlines+=1
                else:
                    if poi is not None and (not station in poi):
                        #LOG_METHOD("Skipping point %s" %station)
                        line=f.readline()
                        continue
                    
                    t=datetime.datetime(y,m,d)
                    if min_y is not None and t<min_y:
                        line=f.readline()
                        continue
                    if max_y is not None and t>max_y:
                        line=f.readline()
                        continue
                    if stations.has_key(station):
                        stations[station].append([t,z,sz*0.001])
                    elif len(stations)<max_pts:
                        stations[station]=[[t,z,sz*0.001]]
        line=f.readline()
    #If we are unlucky, things might get read in an unsorted state wrt time, so sort it now!#
    for station in stations.keys():
        ts=np.array(stations[station])
        I=np.argsort(ts[:,0])
        stations[station]=ts[I]
    return stations,Jessen

def MyXYReader(f):
    #Read station coordinates from a csv file: station, x, y
    #Return a dict with station names as keys
    badlines=0
    xy=dict()
    line=f.readline()
    while len(line)>0:
        sline=line.split(",")
        if len(sline)>0:
            station=sline[0].strip()
            try:
                x=float(sline[1].strip())
                y=float(sline[2].strip())
            except:
                LOG_METHOD("Header line (or wrong line) in location file: %s" %line.strip())
                badlines+=1
            else:
                xy[station]=[x,y]
        line=f.readline()
    return xy

def POIReader(f):
    badlines=0
    poi=[]
    d5=None
    line=f.readline()
    while len(line)>0:
        sline=line.split()
        if len(sline)>0 and sline[0][0]!="#":
            station=sline[0].strip()
	    station = station.replace("/", "-")   #MWS: try to filter the stations out where slash is used
	    if len(sline)>1 and "5d" in sline[1]:
                d5=station
            poi.append(station)
        line=f.readline()
    return poi,d5

def WanderAlongGraph(graph,vertex,edges):
    if graph.has_key(vertex):
        for e in graph[vertex]:
            if e not in edges:
                edges.append(e)
                WanderAlongGraph(graph,e,edges)

def GetComponents(graph):
    DONE=[]
    keys=graph.keys()
    keys.sort()
    components=[]
    for vertex1 in keys:
        if vertex1 not in DONE:
            done=[vertex1] #start new branch
            WanderAlongGraph(graph,vertex1,done)
            DONE.extend(done)
            components.append(done)
    return components

def OldSchool(ts):
    if ts.shape[0]>1:
        a,b=np.polyfit(ts[:,0],ts[:,1],1)
        sigma2=((a*ts[:,0]+b-ts[:,1])**2).sum()
        t2=(ts[:,0]**2).sum()
        tt=(ts[:,0]).sum()
        s=np.sqrt(sigma2/(ts.shape[0]-2.0))  #sigma estimat
        sb=np.sqrt(t2/(ts.shape[0]*t2-tt**2))*s
        sig=np.sqrt(ts.shape[0]/(ts.shape[0]*t2-tt**2))
        sa=sig*s
    return a,b,sa

def GetMotions(z_file,xy_file=None,inclusion_file=None,format="KMS",min_y=None,max_y=None):
    if inclusion_file is not None:
        poi,d5point=POIReader(inclusion_file)
        LOG_METHOD("Restricting analysis to %d points of interest." %len(poi))
        if d5point is not None:
            LOG_METHOD("%s marked as 5d-point." %d5point)
    else:
        poi=None
    
    if format=="KMS":
        stations,Jessen=MyReader(z_file,poi=poi,max_pts=MAX_PTS,min_y=min_y,max_y=max_y)
        xy=MyXYReader(xy_file)
    else:
        stations,xy=KurtReader(z_file,poi,min_y=min_y,max_y=max_y)
        Jessen=None
    
    LOG_METHOD("Found %i stations in time series, and %i stations with (x,y) coords." %(len(stations),len(xy)))
    LOG_METHOD("Jessen point is %s" %Jessen)
    
    for station in stations:
        if station in fivedpoints:
	    LOG_METHOD("#Jessen point is %s and 5d point is %s" %(Jessen,station))
	    break

    LOG_METHOD("Using ignore limit %.3f mm and error multiplier/interval %.2f in stability test." %(IGNORE_LIMIT,STABILITY_SD_MULTIPLIER))
    
    if min_y is not None:
        LOG_METHOD("Restricting to dates after %d-01-01" %min_y)
    if max_y is not None:
        LOG_METHOD("Restricting to dates before %d-12-31" %max_y)
    attrs=dict()
    nunstable=0
    ntrend=0
    ntrend_p=0 #holds number of points with sign. positive trend.
    for station in stations.keys():
        ts=stations[station]
        tmin,tmax=GetTimeSpan(ts)
        ts=GetTS(stations[station]) #now we are in days from UTC time 0, could easily be extended to finer grained things with timedelta objects...
        ts[:,0:2]-=np.copy(ts[0,0:2]) #subtract 'start' to get more numeric stability. Copy necc. to avoid strange effects....
        ts[:,1:]*=1000.0 #then we are in mm and things should be even more stable...
        ts[:,0]/=365.25# and then we are in years!
        signif=False
        stable=True #stable by default. So only update to False if failing test below.
        corr_coeff=0
        scale_sigma=1
        has_motion=False
        a=0
        a_plot=0
        b_plot=0
        sa=10000
        b=-999
        if ts[:,0].min()==ts[:,0].max() and ts.shape[0]>1:
            LOG_METHOD("Station: %-16s, something wrong, min date %s equals max date %s" %(station,tmin,tmax))
        elif ts.shape[0]>1:
            #do a weighted linear regression! Works fine also for just two points!!!
            W=np.diag(1/(ts[:,2]**2))  #weights for weighted lin. regr. - really the square root of the weight matrix!
            X=np.column_stack((np.ones(ts.shape[0],),ts[:,0]))
            #What we want to solve is (X^tWX)(coff_est)=X^tWy, where y=z-observations
            Z=np.dot(X.transpose(),W)
            try:
                Q=np.linalg.inv(np.dot(Z,X)) #by linear error propagation cov(coeff_est)=Bcov(y)B^t, when coeff_est=By, the diagonal elements of Q give us our uncertainties.
            except:
                print("Exception in matrix inversion, station: %s, time series:\n%s" %(station,repr(ts)))
            else:
                H=np.dot(Q,Z)
                C=np.dot(H,ts[:,1].reshape((ts.shape[0],1))) #coeff estimate....
                b=C[0,0]
                a=C[1,0]
                #trivial matrix caluculations reduces the simple (NO a posteriori) error propagation result to this
                # Notice: NO depency on goodness of fit - only depends on input variances and distribution of times.
                __sa=np.sqrt(Q[1,1])
                #Now caluculate the a-posteriori variance estimate, which takes "goodness of fit" into account
                #Should be the same as in an unweighted regression if all input weights are the same....
                #Hmmm - what is minimized is the weighted distance - TODO: take this into account
                res=ts[:,1]-(ts[:,0]*a+b)
                if ts.shape[0]>2:
                    res_sum=np.sum(((1/ts[:,2])*res)**2)
                    ap_var=res_sum/(ts.shape[0]-2)
                    scale_sigma=np.sqrt(ap_var)
                    corr_coeff=np.corrcoef(ts[:,0],ts[:,1])[0,1]
                else:
                    scale_sigma=1
                #Q=np.dot(H,H.transpose())*ap_var
                #sb=np.sqrt(Q[0,0])
                #sa=np.sqrt(Q[1,1])
                sa=__sa*scale_sigma
                if DEBUG and ts.shape[0]>2:
                    _a,_b,_sa=OldSchool(ts)
                    print "Unweighted: ", _a,_sa," Weighted: ",a,sa," No-aposteriori: ",__sa
                if abs(a)>TREND_SD_MULTIPLIER*sa:
		    print("The sa is: " + str(sa))
                    signif=True
                    ntrend+=1
                    ntrend_p+=(a>0)
                    has_motion=True
                else:
                    signif=False
                
        #STABILITY?#
        if ts.shape[0]>1:
            #@Aslak: first test for max diff < ignore limit
            #if ok: stable
            #else: continue testing for overlap of uncertainty intervals
            #Note: at this point all heights and sd's should be in mm
            zmax=ts[:,1].max()
            zmin=ts[:,1].min()
            #stable is set to True by default - so only continue testing if we might be unstable
            if (zmax-zmin)>IGNORE_LIMIT: #in mm so ok.
                #ok - so look further. The diff should be less than the properly combined uncertainty for each pair.
                #can we avoid a loop over all pairs??
                for i in range(ts.shape[0]):
                    if not stable:
                        break
                    for j in range(i+1,ts.shape[0]):
                        #check diff
                        combined_error=sqrt(ts[i,2]**2+ts[j,2]**2) 
                        gap=abs(ts[i,1]-ts[j,1])-STABILITY_SD_MULTIPLIER*combined_error
                        if gap>0:
                            stable=False
                            break
                
            if not stable:
                nunstable+=1
            #Now transform best line parameters to something useful for plotting#
            b_plot=b*0.001+ stations[station][0,1]-a*stations[station][0,0].toordinal()/365.25*0.001
            a_plot=a/365.25*0.001 #transform back to days...
        if ts.shape[0]>2:
            extra_info=", corr_coeff: %.4f , a posteriori scale: %.4f." %(corr_coeff,scale_sigma)
        else:
            extra_info="."
        if has_motion: #we include motions with only two measurements -. just because we typically don't have a lot of data....
            LOG_METHOD("#Station: %-16s, motion: %.4f mm/year, measured %i times, stable: %5s" %(station,a,ts.shape[0],stable)+extra_info)
        elif ts.shape[0]<2:
            LOG_METHOD("#Station: %-16s, insufficent number of measurements." %station)
        else:
            LOG_METHOD("#Station: %-16s, no significant motion, measured %i times, stable: %5s" %(station,ts.shape[0],stable)+extra_info)
        attrs[station]=[tmin,tmax,ts.shape[0],a,sa,signif,stable,a_plot,b_plot,corr_coeff]
    ls="*"*60
    LOG_METHOD("%s\n#Unstable points:         %i" %(ls,nunstable))
    LOG_METHOD("#Points with sign. trend: %i" %(ntrend))
    LOG_METHOD("#")
    if (ntrend_p!=ntrend) and (ntrend_p>0):
        LOG_METHOD("WARNING: %i points with positive trend and %i with negative trend." %(ntrend_p,ntrend-ntrend_p))
    LOG_METHOD("%s" %ls)
    return stations,attrs,xy,Jessen
    
    

def Compare(stations):
    equals=dict()
    for station in stations.keys():
        if stations[station].shape[0]>1:
            equals[station]=[np.empty((0,),dtype='<S18'),np.empty((0,))]
            #print station
            for station2 in stations.keys():
                if station2!=station and stations[station2].shape[0]>1:
                    m1,m2,c=Overlap(stations[station],stations[station2])
                    #LOG_METHOD("%s to %s: %.5f %.5f" %(station,station2,m1,m2))
                    if m1<m2 and m1>-10000:
                        equals[station][0]=np.append(equals[station][0],station2)
                        equals[station][1]=np.append(equals[station][1],c)
    for station in equals.keys():
        I=np.argsort(equals[station][1])
        equals[station][0]=(equals[station][0])[I[::-1]]
        equals[station][1]=(equals[station][1])[I[::-1]]
    return equals


    


def PlotComparison(ts1,ts2,title="Comparison"):
    if not HAS_MPL:
        LOG_METHOD("No matplotlib...")
        return
    I=np.argsort(ts1[:,0])
    ts1=ts1[I]
    I=np.argsort(ts2[:,0])
    ts2=ts2[I]
    plt.ioff()
    plt.figure()
    plt.plot(ts2[:,0],ts2[:,1]-ts2[:,2],"--",color="red")
    plt.plot(ts2[:,0],ts2[:,1]+ts2[:,2],"--",color="red")
    plt.plot(ts2[:,0],ts2[:,1],color="red")
    plt.scatter(ts2[:,0],ts2[:,1],c="red",marker="s")
    m1,m2,c=Overlap(ts1,ts2)
    if m1<m2:
        m=(m1+m2)*0.5
        plt.plot(ts1[:,0],ts1[:,1]-ts1[:,2]-m,"--",color="blue")
        plt.plot(ts1[:,0],ts1[:,1]+ts1[:,2]-m,"--",color="blue")
        plt.scatter(ts1[:,0],ts1[:,1]-m,c="blue",marker="d")
        plt.plot(ts1[:,0],ts1[:,1]-m,color="blue")
        plt.xlabel("Match: %.2f" %c)
    else:
        m=(m1+m2)*0.5
        plt.scatter(ts1[:,0]-m,ts1[:,1]-m)
        plt.xlabel("No match")
    plt.title(title)
    plt.show()


def PlotSingle(ts,title="Time Series Plot",filename=None):
    if not HAS_MPL:
        LOG_METHOD("No matplotlib...")
        return
    plt.ioff()
    I=np.argsort(ts[:,0])
    ts=ts[I]
    plt.figure()
    plt.errorbar(ts[:,0],ts[:,1],ts[:,2])
    plt.plot(ts[:,0],ts[:,1],"-",color="red")
    plt.xlabel("Time")
    plt.ylabel("height [m]")
    plt.title(title)
    if filename is None:
        plt.show()
    else:
        plt.savefig(filename)

def PlotMany(ts_list,labels,title="Time Series",save_name=None):
    if not HAS_MPL:
        LOG_METHOD("No matplotlib...")
        return
    plt.ioff()
    plt.figure()
    nl=0
    for ts in ts_list:
        dz=ts[:,1]-ts[:,1].mean()
        plt.plot(ts[:,0],dz,label=labels[nl])
        nl+=1
    plt.title(title)
    plt.xlabel("Time [y]")
    plt.ylabel("dz [m]")
    plt.legend()
    if save_name is None:
        plt.show()
    else:
        plt.savefig(save_name)
        
def GetTimeOverlap(ts1,ts2):
    tmin1=ts1[:,0].min()
    tmax1=ts1[:,0].max()
    tmin2=ts2[:,0].min()
    tmax2=ts2[:,0].max()
    I1=np.where(np.logical_and(ts1[:,0]<=tmax2,ts1[:,0]>=tmin2))[0]
    I2=np.where(np.logical_and(ts2[:,0]<=tmax1,ts2[:,0]>=tmin1))[0]
    return I1,I2
    
    
def Overlap(ts1,ts2,ignore_limit=0): #must be sorted!
    #Sort the time series#
    #I=np.argsort(ts1[:,0])
    #ts1=ts1[I]
    #I=np.argsort(ts2[:,0])
    #ts2=ts2[I]
    #end sort#
    #print "Getting 1-2"
    Intervals1=GetIntervals(ts1,ts2)
    #print "Getting 2-1"
    Intervals2=np.fliplr(GetIntervals(ts2,ts1)*-1)
    m1=10000
    m2=-10000
    if Intervals1.size>0:
        #LOG_METHOD("%s" %repr(Intervals1.shape))
        #LOG_METHOD("%s" %repr(Intervals1))
        m2=Intervals1[:,1].min()
        m1=Intervals1[:,0].max()
        #LOG_METHOD("%.1f %.1f" %(m1,m2))
    if Intervals2.size>0:
        #LOG_METHOD("%s" %repr(Intervals2.shape))
        #LOG_METHOD("%s" %repr(Intervals2))
        m2=min(m2,Intervals2[:,1].min())
        m1=max(m1,Intervals2[:,0].max())
        #LOG_METHOD("%.1f %.1f" %(m1,m2))
    I1,I2=GetTimeOverlap(ts1,ts2)
    n=max(I1.size,I2.size)
    if I1.size>0:
        s1=np.mean(ts1[I1,2])
    else:
        s1=0
    if I2.size>0:
        s2=np.mean(ts2[I2,2])
    else:
        s2=0
    if (I1.size+I2.size)>0:
        s=(I1.size*s1+I2.size*s2)/(I1.size+I2.size)
    else:
        s=999
    c=(m2+ignore_limit-m1)*n/s
    return m1,m2,c
    
def GetPointsInInterval(start,stop,points):
    return np.where(np.logical_and(points>=start,points<=stop))[0]

def GetIntervals(ts1,ts2):
    Intervals=np.empty((0,2))
    currentindex=0
    for i in range(1,ts1.shape[0]):
        start=ts1[i-1,0]
        stop=ts1[i,0]
        In=GetPointsInInterval(start,stop,ts2[currentindex:,0])
        #print start,stop,ts2[currentindex:][In,0]
        if In.size>0:
            if In.size>1:
                intv1=GetInterval(ts1[i-1],ts1[i],ts2[In[0]+currentindex])
                intv2=GetInterval(ts1[i-1],ts1[i],ts2[In[-1]+currentindex])
                currentindex+=In[-1]
                Intervals=np.vstack((Intervals,np.array([intv1,intv2])))
            else:
                intv=GetInterval(ts1[i-1],ts1[i],ts2[In[0]+currentindex])
                currentindex+=In[0]
                Intervals=np.vstack((Intervals,intv))
    return Intervals

def GetInterval(row1,row2,row_in):
    t1,x1,s1=row_in
    t0,x0,s0=row1
    t2,x2,s2=row2
    #s1*=0.5
    #s0*=0.5
    #s2*=0.5
    if t2==t0:
        LOG_METHOD("times: %.2f %.2f %.2f" %(t2,t0,t1))
        LOG_METHOD("%s %s" %(repr(row1),repr(row2)))
    val=x0+(x2-x0)/(t2-t0)*(t1-t0)
    s=(t1-t0)/(t2-t0)*s0+(t2-t1)/(t2-t0)*s2
    #print trans_type,val,s,no,t1,x1,s1
    high=(val-x1)+s+s1
    low=(val-x1)-s-s1
    #LOG_METHOD("LH: %.2f %.2f" %(low,high))
    return [low,high]
    
####################
## A function which can export data in a format that can be imported into other apps...
####################
def ExportData(stations,attrs,xy,output_file,sep_char=",",swap_xy=False):
    h=open(output_file,"w")
    h.write("NAME,X,Y,TMIN,TMAX,NMEAS,MOTION,SD,CORR_COEF,SIGNIF\n".replace(",",sep_char))
    for station in stations:
        tmin,tmax,n,a,sa,signif,stable,a_plot,b_plot,corr_coeff=attrs[station]
        signif=int(signif)
        if station in xy:
            if swap_xy:
                y,x=xy[station]
            else:
                x,y=xy[station]
            h.write(("%s*,*%.3f*,*%.3f*,*%s*,*%s*,*%d*,*%.5f*,*%.5f*,*%.5f*,*%d\n" %(station,x,y,tmin,tmax,n,a,sa,corr_coeff,signif)).replace("*,*",sep_char))
        else:
            print("No coords for %s" %station)
            
    h.close()
    

if __name__=="__main__":
    ExportData(*sys.argv[1:])

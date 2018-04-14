''' Scheduling Aircraft Landing (Dynamic Case) with 1 runway
    Landing times of aircrafts are determined satisfying certain constraints
    Constraints- The aircraft should land within a predetermined time interval
                 Clearance time between two landing should be satisfied
'''
import numpy as np
from gurobipy import *
import os

def fetch_data(file_name):
    data=open(os.getcwd()+'\\data_files\\'+file_name,'r')
    lines=data.readlines()
    num_planes=int(lines[0].split()[0])
    freeze_time=int(lines[0].split()[1])

    flight_details=np.empty([num_planes,6],dtype=float)
    sep_time=np.empty([num_planes,num_planes],dtype=int)
    s=''
    for line in lines[1:]:
        s=s+line
    s=s.split()
    flag=0
    count=0
    for items in [s[x:x+6+num_planes] for x in range(0,len(s),num_planes+6)]:
        flight_details[count]=[float(x) for x in items[:6]]
        sep_time[count]=[int(x) for x in items[6:]]
        count=count+1
    print(flight_details)
    print(sep_time)
    data.close()
    return num_planes,flight_details,sep_time


def schedule(flight_ids,flights,clearance,frozen=None,scheduling_type='static',prev_scheduled_times={}):
    num_flights=len(flight_ids)
    try:
        #Creating a Gurobi model
        model=Model("Aircraft Landing Schedule")
        M=max(flights[i,3] for i in flight_ids)-min(flights[i,1] for i in flight_ids)

        
        z_pos={}
        for i in flight_ids:
            z_pos[i]=flights[i,5]
        z_neg={}
        for i in flight_ids:
            z_neg[i]=flights[i,4]
        x_={}
        for i in flight_ids:
            x_[i]=0
        del_={}
        for i in flight_ids:
            for j in flight_ids:
                del_[i,j]=0
        D={}
        if scheduling_type!='static':
            for i in list(prev_scheduled_times.keys()):
                D[i]=1
                
        #Adding decision variables
        z_p=model.addVars(z_pos.keys(),lb=0,ub=GRB.INFINITY,obj=z_pos,vtype=GRB.CONTINUOUS,name="z_p")
        z_n=model.addVars(z_neg.keys(),lb=0,ub=GRB.INFINITY,obj=z_neg,vtype=GRB.CONTINUOUS,name="z_n")
        x=model.addVars(x_.keys(),lb=0,ub=GRB.INFINITY,obj=x_,vtype=GRB.CONTINUOUS,name="x")
        d=model.addVars(del_.keys(),lb=0,ub=1,obj=del_,vtype=GRB.BINARY,name="d")
        D=model.addVars(D.keys(),lb=0,ub=GRB.INFINITY,obj=D,vtype=GRB.CONTINUOUS,name="D")

        
        if scheduling_type!='static':
            # Change objective
            model.setObjective((quicksum(flights[i,5]*z_p[i]+flights[i,4]*z_n[i] for i in flight_ids)+
                               quicksum(D[i] for i in list(prev_scheduled_times.keys()))), GRB.MINIMIZE)
                               

        #Adding constraints
        model.addConstrs((x[j]-x[i]>=clearance[i,j] - d[j,i]*M for i in flight_ids for j in flight_ids if j!=i),name="Clearance")
        model.addConstrs((z_p[i]>=x[i]-flights[i,2] for i in flight_ids),name="+")
        model.addConstrs((z_n[i]>=flights[i,2]-x[i] for i in flight_ids),name="-")
        model.addConstrs((x[i]>=flights[i,1] for i in flight_ids),name="Land after earliest landing time")
        model.addConstrs((x[i]<=flights[i,3] for i in flight_ids),name="Land before latest landing time")
        model.addConstrs((d[i,j]+d[j,i]==1 for i in flight_ids for j in flight_ids if j!=i),name="~")

        # if some landing times are frozen, they can't be changed
        if frozen!=None:
            model.addConstrs((x[i]==j for i,j in frozen.items()),name="landing times frozen")

        # if it's dynamic scheduling, add max displacement constraints
        if scheduling_type!='static':
            model.addConstrs((D[i]>=(prev_scheduled_times[i]-x[i])*flights[i,4] for i in list(prev_scheduled_times.keys()) if prev_scheduled_times[i]<flights[i,2]),name="displacement if originally scheduled to land before target time")
            model.addConstrs((D[i]>=(x[i]-prev_scheduled_times[i])*flights[i,5] for i in list(prev_scheduled_times.keys()) if prev_scheduled_times[i]>flights[i,2]),name="displacemnt if orignally scheduled to land after target time")
            model.addConstrs((D[i]>=flights[i,4]*(prev_scheduled_times[i]-x[i]) for i in list(prev_scheduled_times.keys()) if prev_scheduled_times[i]==flights[i,2]),name="displacement if originally scheduled to land at taget time1")
            model.addConstrs((D[i]>=flights[i,5]*(x[i]-prev_scheduled_times[i]) for i in list(prev_scheduled_times.keys()) if prev_scheduled_times[i]==flights[i,2]),name="displacement if originally scheduled to land at target time2")
            model.addConstrs((D[i]<=50 for i in list(prev_scheduled_times.keys())),name="Limiting displacement") 
            
            
        model.optimize()

        # Displaying scheduled landing times

        sch_times={}
        for i in flight_ids:
            sch_times[i]=model.getVarByName("x["+str(i)+"]").X
            if scheduling_type=='static':
                print('%s %g' % ('SCHEDULED LANDING TIME FOR AIRCRAFT '+str(i)+" = ", model.getVarByName("x["+str(i)+"]").X))
            #print("Z_pos[%s]=  %s and Z_neg[%s]= %s"%(i,model.getVarByName("z_p["+str(i)+"]").X,i,model.getVarByName("z_n["+str(i)+"]").X))

        if scheduling_type!='static':
            '''
            for i in list(prev_scheduled_times.keys()):
                print("D[%s]= %s" % (i,model.getVarByName("D["+str(i)+"]").X))
            '''
            ori_cost=sum((flights[i,5]*model.getVarByName("z_p["+str(i)+"]").X)+(flights[i,4]*model.getVarByName("z_n["+str(i)+"]").X) for i in flight_ids)
            #print(ori_cost)
            disp_cost=model.objVal-ori_cost
            
   
    except GurobiError as e:
        print('Error code ' + str(e.errno) + ": " + str(e))

    except AttributeError as a:
        print('Encountered an attribute error '+str(a))

    if scheduling_type=='static':
        return sch_times,model.objVal
    else:
        return sch_times,disp_cost,ori_cost


def dynamic_schedule():
    
    t=0
    F0=[i for i in range(num_flights)]      #Set of aircraft that have not yet appeared by time t
    F1=[]       #Set of aircraft that have appeared by time t, but have not yet landed or had their landing times frozen
    F2=[]       #Set of aircraft that have appeared by time t and have either landed or have had their landing time frozen
    x={i:9999 for i in range(num_flights)}       #Dictionary of landing time scheduled/updated as time passes with flight ids as keys
    Z_disp=0        #accumulated displacement cost
    t_star=20   #Freeze time (any aircraft scheduled to land with within t_star of current time has it's landing time frozen
    

    t,ind=min((flights[i,0],i) for i in F0)     #Starting with the first flight to appear
    F1.append(ind)
    F0.remove(ind)
    x[ind]=flights[ind,2]

    #while there are flights yet to be appeared
    while(len(F0)>0):

        # Get next flight's apperance time (set as current time) and it's flight id
        t,ind=min((flights[i,0],i) for i in F0)
        F1.append(ind)
        F0.remove(ind)

        # Check if any flights in F1 have their landing times frozen by current time t, if yes, then move them to F2
        frozen_=[]
        for items in F1:
            if x[items]<=t+t_star:
                frozen_.append(items)
        F1=list(set(F1)-set(frozen_))
        F2=F2+frozen_
        
        flights_with_time_frozen={i:j for i,j in x.items() if i in F2}

        # Schedule flights that have appeared and reschedule, if required, previously scheduled flights except for those which have landed or have had their landing time frozen
        x_new,disp_cost,landing_cost=schedule(F1+F2,flights,clearance,frozen=flights_with_time_frozen,scheduling_type='dynamic',prev_scheduled_times={i:j for i,j in x.items() if i in [item for item in F1 if item!=ind]})
        Z_disp+=disp_cost
        for ind,time in x_new.items():
            x[ind]=time
    print("\n\n\nDYNAMIC SCHEDULE OF FLIGHTS")
    for ind,time in x.items():
        print("SCHEDULED TIME OF LANDING OF FLIGHT %s is : %s" % (ind,time))
    print("Total Displacement Cost: %s" % Z_disp)
    print("Total Landing Cost: %s" % landing_cost)
        

if __name__=="__main__":
    
    a='''The available cases are:
        [1] airland1.txt with 10 flights
        [2] airland8.txt with 50 flights
        '''

    print(a)
    fil={1:1,2:8}
    num=input('Enter your choice (1/2):')
    num_flights,flights,clearance=fetch_data('airland'+str(fil[num])+'.txt')
    dynamic_schedule()
    resp=input("\n\n\nDo you wanna check the scheduling for same flights in static case???? If yes, enter 1: ")
    if resp==1:
        scheduled_time,cost=schedule([i for i in range(num_flights)],flights,clearance)
        print("Landing cost = %s" % cost)
    
    



'''Testing'''
#print(schedule([2,3,4,5],flights,clearance,frozen={},scheduling_type='dynamic',prev_scheduled_times={2:98,3:106,4:123}))
#print(schedule([i for i in range(num_flights)],flights,clearance))


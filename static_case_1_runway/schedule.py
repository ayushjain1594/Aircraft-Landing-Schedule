''' Scheduling Aircraft Landing (Static Case) with 1 runway
    Landing times of aircrafts are determined satisfying certain constraints
    Constraints- The aircraft should land within a predetermined time interval
                 Clearance time between two landing should be satisfied
'''
import numpy as np
from gurobipy import *
import os

#=====================================================================
# Function to fetch data from provided txt file
# @parameters- file_name : Data file(must be present in same directory)
#=====================================================================
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

#=====================================================================
# Function to find landing time of the aircrafts
# @parameters- file_name Data file(must be present in same directory)
#=====================================================================
def schedule(file_):
    num_flights,flights,clearance=fetch_data(file_)
    try:
        #Creating a Gurobi model
        model=Model("Aircraft Landing Schedule")
        M=max(flights[:,3])-min(flights[:,1])
        z_pos={}
        for i in np.arange(1,num_flights+1):
            z_pos[i]=flights[i-1,5]
        z_neg={}
        for i in np.arange(1,num_flights+1):
            z_neg[i]=flights[i-1,4]
        x_={}
        for i in np.arange(1,num_flights+1):
            x_[i]=0
        del_={}
        for i in np.arange(1,num_flights+1):
            for j in np.arange(1,num_flights+1):
                del_[i,j]=0
            
        #Adding decision variables
        z_p=model.addVars(z_pos.keys(),lb=0,ub=GRB.INFINITY,obj=z_pos,vtype=GRB.CONTINUOUS,name="z_p")
        z_n=model.addVars(z_neg.keys(),lb=0,ub=GRB.INFINITY,obj=z_neg,vtype=GRB.CONTINUOUS,name="z_n")
        x=model.addVars(x_.keys(),lb=0,ub=GRB.INFINITY,obj=x_,vtype=GRB.CONTINUOUS,name="x")
        d=model.addVars(del_.keys(),lb=0,ub=1,obj=del_,vtype=GRB.BINARY,name="d")

        #Adding constraints
        model.addConstrs((x[j]-x[i]>=clearance[i-1,j-1] - d[j,i]*M for i in np.arange(1,num_flights+1) for j in np.arange(1,num_flights+1) if j!=i),name="Clearance")
        model.addConstrs((z_p[i]>=x[i]-flights[i-1,2] for i in np.arange(1,num_flights+1)),name="+")
        model.addConstrs((z_n[i]>=flights[i-1,2]-x[i] for i in np.arange(1,num_flights+1)),name="-")
        model.addConstrs((x[i]>=flights[i-1,1] for i in np.arange(1,num_flights+1)),name="Land after earliest landing time")
        model.addConstrs((x[i]<=flights[i-1,3] for i in np.arange(1,num_flights+1)),name="Land before latest landing time")
        model.addConstrs((d[i,j]+d[j,i]==1 for i in np.arange(1,num_flights +1) for j in np.arange(1,num_flights+1) if j!=i),name="~")

        
        model.optimize()

        # Displaying scheduled landing times
        
        for i in np.arange(1,num_flights+1):
            print('%s %g' % ('SCHEDULED LANDING TIME FOR AIRCRAFT '+str(i)+" = ", model.getVarByName("x["+str(i)+"]").X))
        
        
                
    except GurobiError as e:
        print('Error code ' + str(e.errno) + ": " + str(e))

    except AttributeError as a:
        print('Encountered an attribute error '+str(a))

    return model

a='''The available cases are:
    [1] airland1.txt with 10 flights
    [2] airland8.txt with 50 flights
    [3] airland13.txt with 500 flights
    '''

print(a)
num=input('Enter your choice (1/2/3):')
if num==1:
    schedule('airland1.txt')
elif num==2:
    schedule('airland8.txt')
elif num==3:
    schedule('airland13.txt')

'''Print extracted data'''
#fetch_data('airland13.txt')

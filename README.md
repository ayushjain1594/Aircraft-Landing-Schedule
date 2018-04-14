# Aircraft-Landing-Schedule
MILP Models for scheduling aircraft landings for static/dynamic and single/multiple runway cases (Under development)

## Problem Statement
The problem is scheduling of aircraft landings within a predetermined time frame. 
The problem often occurs at major airports handling hundreds of flights in a day. 
The flight landinds not only need to be scheduled within a predetermined (slightly relaxed) time frame but also satisfy clearance time between consecutive flights depending upon various factors such as aircraft size, taxing traffic, airport arrival capacity, etc.

## Model
Currently, mixed integer programming models have been developed for static case with single and multiple runways. 
In the static case, all the data is predetermined and does not change over time.

Models for dynamic case are currently under development.

## Data Format

The format of the data files is:

```javascript
number of planes (p), freeze time

for each plane i (i=1,...,p): 
          appearance time, earliest landing time, target landing time, 
          latest landing time, penalty cost per unit of time for landing before target, 
          penalty cost per unit of time for landing after target
   
          for each plane j (j=1,...p): separation time required after 
                                i lands before j can land
```

Data reference- [OR-Library by J.E. Beasley](http://people.brunel.ac.uk/~mastjjb/jeb/info.html)

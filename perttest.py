#!/usr/bin/env python
import random

#Constraints:
#
# [a,b,c],..., [d,e,f]
#
# b > a and e > d implies b <= d
# a > b and e > d implies a < d
#
# If statistical reports come in,
# and before starting a count, [a,0,0] is reported,
# and [d,e,f] is reported when it finishes,
# 
# the individual rate (where a,d are start..b,e are stop, c,f are count)
#   (b-a)/c
#
#
# As long as time is non-decreasing in these reports, and all [a,0,0] are
# terminated with a [a,b,c] eventually, the constraints are met.
# So in a concurrent setting, let the counting process actually set these time
# stamps.  As long as individual clients report in order, this works
# even with a lot of concurrency
perfQueue = [
    [3, 0,   0],
    [4, 0,   0],
    [3, 5, 131],
    [6, 0,   0],
    [7, 0,   0],
    [4, 8,  71],
    [9, 0,   0],
    [9, 10, 22],
    [7, 11, 31],
    [6, 20, 30],
]

def qcount(pq,start,stop):
    #population up to 8
    popTime = [0,0,0,0,0,0,0,0]
    popCount = [0,0,0,0,0,0,0,0]
    #total potential idle time
    popTime[0] = stop-start
    for i in range(1,len(pq)):
       popTime[pq[i][3]] += pq[i][1]-pq[i][0]
       popCount[pq[i][3]] += pq[i][2]
    #remove non-idle time
    for i in range(1,len(popTime)):
       popTime[0] -= popTime[i]
    return popCount,popTime

def qadd(item,pq):
    #Set the population on items as added
    if item[1] == 0:
        if len(pq) == 0:
            pop = 1
        else:
            pop = pq[-1][3] + 1
    else:
        pop = pq[-1][3] - 1
    newitem = [
            item[0],
            item[1],
            item[2],
            pop,
    ]
    pq.append(newitem)
    #Now do a reduction.
    #This combines the records noting that a count started, with the stop record,
    #and the records in between.
    i = len(pq)-1
    j = i-1
    while j >= 0:
        if pq[i][0] == pq[i][1]:
            break
        if pq[i][0] > pq[j][0] and pq[i][0] == pq[j][1]:
            break
        if pq[i][0] < pq[j][1]:
            z = pq[i][2] * (pq[i][1]-pq[j][1]) / (pq[i][1]-pq[i][0])
            pq[i][0], pq[j][1] = pq[j][1], pq[i][0]
            pq[j][2] += pq[i][2]-z
            pq[i][2] = z
            pq[j][1] = pq[i][0]
        if pq[i][0] < pq[j][0]:
            z = pq[i][2] * (pq[i][1]-pq[j][0]) / (pq[i][1]-pq[i][0])
            pq[i][0], pq[j][0] = pq[j][0], pq[i][0]
            pq[j][2] += pq[i][2]-z
            pq[i][2] = z
            pq[j][1] = pq[i][0]
        if pq[j][1] < pq[j][0]:
            pq[j][0],pq[j][1] = pq[j][1], pq[j][0]
        i -= 1
        j -= 1


pq = []

for item in perfQueue:
    qadd(item,pq)

popTime,popCount = qcount(pq,0,22)
print(pq)
for i in range(0, len(popTime)):
    if popTime[i] > 0:
        print("t:%d = %f" % (i, (1.0*popCount[i])/popTime[i]))


import pandas as pd
import os
from datetime import datetime,timedelta
import random

def getHR():
    
    resting_average = 70
    resting_sd = 5 #resting standard deviation
    max_variation = 20

    resting_hr = random.normalvariate(resting_average,resting_sd)
    max_hr = resting_hr + max_variation
    heart_rate = random.randint(int(resting_hr),int(max_hr))

    return heart_rate


def getO2():
    O2_average = 97
    resting_sd = 1 #standard deviation
    max_variation = 2

    O2_rand = random.normalvariate(O2_average,resting_sd)
    max_O2 = O2_rand + max_variation
    O2Sat = random.randint(int(O2_rand),int(max_O2))

    return round(O2Sat,2)


def getBP():
    sys_bp_average = 130
    sys_bp_sd = 10
    dia_bp_average = 80
    dia_bp_sd = 5

    sys_bp = random.normalvariate(sys_bp_average,sys_bp_sd)
    dia_bp = random.normalvariate(dia_bp_average,dia_bp_sd)

    return round(sys_bp,2),round(dia_bp,2)



def getBG():
    bg_average = 100
    bg_sd = 10

    blood_glucose = random.normalvariate(bg_average,bg_sd)

    return round(blood_glucose,2)


def getDate(i):
    started  = datetime(2022, 6, 6)
 
    return (started + timedelta(days=i)).strftime("%Y-%m-%d")

def getPain():
    pain_sd = 1
    pain_start = random.randint(0,4)
    pain = random.normalvariate(pain_start,pain_sd)

    big_event = random.randint(0,1000)
    if big_event == 1000:
        pain = random.randint(7,10)

    if pain < 0:
        pain = 0

    return round(pain)

def getWT(prev):
    weight_change = random.normalvariate(0,1)

    big_event = random.randint(0,1000)
    if big_event == 1000:
        weight_change = 10
    elif big_event == 999:
        weight_change = -10
    
    return round(prev + weight_change)



def main():
    myDict = []
    fields = ['Date','HR','O2Sat','Systolic','Diastolic','BG','Pain','Weight']
    prev_weight = random.randint(120,200)

    if not os.path.isfile('./vitals.csv'):
        print("no csv file, creating new one")
        for i in range(1000):
            tempDict = {}

            tempDict['HR'] = getHR()
            tempDict['O2Sat'] = getO2()
            tempDict['Systolic'],tempDict['Diastolic'] = getBP()
            tempDict['BG'] = getBG()
            tempDict['Date'] = getDate(i)
            tempDict['Pain'] = getPain()
            prev_weight = getWT(prev_weight)
            tempDict['Weight'] = prev_weight

            
            myDict.append(tempDict)


        df = pd.DataFrame(data=myDict,columns=fields)
        df.to_csv('vitals.csv', index=False)

    else:
        print("found csv file")
        df = pd.read_csv('./vitals.csv')
        





if __name__ == "__main__":
    main()
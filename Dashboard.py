import pandas as pd
import panel as pn
import hvplot.pandas
from panel.interact import interact
import datetime as dt
from dtrelay import DTRelay
import os

from bokeh.plotting import figure
from bokeh.transform import cumsum
from bokeh.palettes import Category20c
from math import pi
pn.extension()

house_id = 112
start_at = None
end_at = None

r = DTRelay("Relay", {
    'url': "https://relay.assets.mu.hekademeia.org/",
    'manifest': {
        'assets-api-oauth': {
            'House': 'house',
            'Item': "item",
            'Group': "group",
            'Sensation': "sensation",
            'Reading': "reading",
            'Event': 'event',
            'EventSummary':'eventsummary'
        }
    }
})

# fixed creds
r.tok = 'REDACTED'
r.sec = 'REDACTED'

# SHS codes to house ids
houses = {"SHS001": 27,"SHS002": 28,"SHS006": 32,"SHS005": 34,"SHS007": 35,"SHS008": 36,"SHS003": 37,"SHS004": 39,"SHS009": 51,"SHS011": 61,"SHS016": 62,"SHS012": 65,"SHS019 ": 66,"SHS014": 67,"SHS018": 68,"SHS017": 69,"SHS013": 70,"SHS020": 71,"SHS021": 72,"SHS024": 76,"SHS025": 78,"SHS015": 81,"SHS023": 82,"SHS026": 87,"SHS022": 88,"SHS032": 101,"SHS041": 112,"SHS060": 114,"SHS031": 115,"SHS051": 117,"SHS052": 119,"SHS046": 120,"SHS048": 121,"SHS036": 122,"SHS062": 124,"SHS061": 125,"SHS030": 126,"SHS047": 127,"SHS049": 128,"SHS027": 130,"SHS050": 131,"SHS057": 133,"SHS037": 134,"SHS056": 137,"SHS058": 139,"SHS063": 156}

def bathroom(rsp):
    global bathroom_data
    # get durations and entry data without making another query to DB for at location data
    durations(rsp)
    entry(rsp)
    df = pd.DataFrame(columns=['Date', 'Trips', 'duration (mins)', 'Avg Time per Trip (mins)'])
    in_bathroom = 0
    duration_spent = 0
    current_date = None
    for evt in rsp['obj']:
        if evt['item']['name'].split('_')[0] == "BathroomSensor":
            timeStamp = dt.datetime.fromtimestamp(evt['start_at_ms'] / 1000.0, tz=dt.timezone.utc).date()
            if current_date is None:
                current_date = timeStamp
            if current_date != timeStamp:
                if in_bathroom != 0:
                    df.loc[len(df.index)] = [current_date, in_bathroom, duration_spent / 60, (duration_spent / 60) / in_bathroom]
                else:
                    df.loc[len(df.index)] = [current_date, 0, 0, 0]
                in_bathroom = 1
                duration_spent = 0
                current_date = timeStamp
            else:
                in_bathroom += 1
                duration_spent += (int(evt['end_at_ms']) - int(evt['start_at_ms']))/1000
    if in_bathroom != 0:
        df.loc[len(df.index)] = [current_date, in_bathroom, duration_spent / 60, (duration_spent / 60) / in_bathroom]
    else:
        df.loc[len(df.index)] = [current_date, 0, 0, 0]
    bathroom_data = df

def durations(rsp):
  global timespent_data
  df = pd.DataFrame(columns=['Location','Duration'])
  bath_dur = 0
  bed_dur = 0
  kitchen_dur = 0
  living_dur = 0
  for evt in rsp['obj']:
    duration = (int(evt['end_at_ms']) - int(evt['start_at_ms']))/1000
    match evt['item']['name'].split('_')[0]:
      case "BathroomSensor":
        bath_dur += duration
      case "BedroomSensor":
        bed_dur += duration
      case "KitchenSensor":
        kitchen_dur += duration
      case "LivingroomSensor":
        living_dur += duration
      case _:
        continue

  df.loc[len(df.index)] = ['bathroom',(bath_dur/60)/60]
  df.loc[len(df.index)] = ['bedroom',(bed_dur/60)/60]
  df.loc[len(df.index)] = ['kitchen',(kitchen_dur/60)/60]
  df.loc[len(df.index)] = ['livingroom',(living_dur/60)/60]
  timespent_data = df

def pieRestTimeBedLiv(rsp,durationTag,areaTag):
  global rest_data
  whereRest = {}
  whereRestLocations = []
  expectedArea = areaTag
  for event in rsp:

    duration = (event[durationTag]/60)/60
    match event[areaTag]:
        case "bed1":
            expectedArea = "bedroom"
        case "living":
            expectedArea = "livingroom"
        case _:
            expectedArea = event[areaTag]
    
    if duration == 0:
      continue
    
    if expectedArea in whereRest.keys():
      whereRest[expectedArea] += duration
    else:
      whereRestLocations.append(expectedArea)
      whereRest[expectedArea] = duration

  rest_data = pd.DataFrame(data=whereRest.items(),columns=["Location","Duration"])


def barTimeAndLocation(rsp,durationTag):
  global sleep_data
  global avg_sleep_time
  times = []
  xVals = []
  total = 0

  for i,event in enumerate(rsp):
    duration = event[durationTag]

    if duration == 0:
      #print(f"{i}: No Rest Time")
      continue
        
    try:
      times.append(duration/3600)
      total += duration/3600
      xVals.append(dt.datetime.fromtimestamp(event['start_at_ms'] / 1000.0, tz=dt.timezone.utc).date())
    except:
      continue

  avg_sleep_time = round(total/len(times),2)
  sleep_data = pd.DataFrame(data=[times,xVals])
  sleep_data = sleep_data.T
  sleep_data.columns = ["Hours Slept","Date"]
  print(sleep_data)

def vitalSignData():
    global vital_data
    global high_resting_heartrate
    global low_resting_heartrate
    global high_sys
    global low_sys
    global high_dia
    global low_dia
    global high_o2_sat
    global low_o2_sat
    global high_blood_glucose
    global low_blood_glucose
    global high_pain_scale
    global low_pain_scale
    global high_daily_weight
    global low_daily_weight

    if os.path.isfile('./vitals.csv'):
        # read in fake vitals data and only select from desired timeframe
        vitals = pd.read_csv('./vitals.csv')
        vital_data = vitals[(vitals['Date'] >= start_at) & (vitals['Date'] <= end_at)]
        # get the highest and lowest vitals during timeframe
        high_resting_heartrate = int(vital_data['HR'].max())
        low_resting_heartrate = int(vital_data['HR'].min())
        high_o2_sat = int(vital_data['O2Sat'].max())
        low_o2_sat = int(vital_data['O2Sat'].min())
        high_blood_glucose = int(vital_data['BG'].max())
        low_blood_glucose = int(vital_data['BG'].min())
        high_sys = int(vital_data['Systolic'].max())
        low_sys = int(vital_data['Systolic'].min())
        high_dia = int(vital_data['Diastolic'].max())
        low_dia = int(vital_data['Diastolic'].min())
        high_pain_scale = int(vital_data['Pain'].max())
        low_pain_scale = int(vital_data['Pain'].min())
        high_daily_weight = int(vital_data['Weight'].max())
        low_daily_weight = int(vital_data['Weight'].min())

def entry(rsp):
    global entry_data
    df = pd.DataFrame(columns=['Date', 'Trips', 'Duration Gone (mins)'])
    entries = set()
    others = set()
    # get "at location" events seperate entries from other
    for evt in rsp['obj']:
        timeStamp = dt.datetime.fromtimestamp(evt['start_at_ms'] / 1000.0, tz=dt.timezone.utc)
        if (evt['item']['name'].split('_')[0] == "EntrySensor"):
            entries.add(timeStamp)
        else:
            others.add(timeStamp)
    # sort the dates 
    sorted_other = sorted(others)
    list_entries = list(sorted(entries))
    # check if the possible "departure" and "arrival" dates are valid
    index = 0
    leave_counter = 0
    duration_gone = 0
    current_date = list_entries[0].date()
    while index < len(list_entries) - 1:
        flag = False
        for date in others:
            if (date > list_entries[index] and date < list_entries[index+1]):
                flag = True
                break
        if not flag: # no sensors triggered during those two timestamps so likely a valid "leave home" event
            duration_gone += ((list_entries[index+1] - list_entries[index]).total_seconds()) / 60
            leave_counter += 1
            index += 2
        else:
            index += 1
        if list_entries[index].date() != current_date or index == len(list_entries) - 2: 
            # new day, track stats for current day then reset and continue
            if leave_counter != 0: 
                df.loc[len(df.index)] = [current_date, leave_counter, duration_gone]
            else:
                df.loc[len(df.index)] = [current_date, leave_counter, 0]
            current_date = list_entries[index].date()
            leave_counter = 0
            duration_gone = 0
    entry_data = df
    print(entry_data)

def getALData():
    if start_at == None:
        return
    r.get("EventSummary", {
        'dtf': {
            'house_id': house_id,
            'start_at': [">=<", start_at, end_at],
            'type_id': 5
        }
    }, bathroom)

def getRestData():
    if start_at == None:
        return
    r.get("Event",{
        'dtf':{
            'house_id':house_id,
            'start_at': [">=<", start_at, end_at],
            "type_id":4,
            'expected':["IN",["bed1","living"]]
        }
    },lambda rsp: pieRestTimeBedLiv(rsp['obj'],'duration_sec','expected'))
  
def getSleepData():
   if start_at == None:
      return
   r.get("Event",{
        'dtf':{
            'house_id':house_id,
            "type_id":6,
            'start_at':[">=<",start_at,end_at]
        }
    },lambda rsp: barTimeAndLocation(rsp['obj'],'duration_sec'))

def getVitalsData():
    if start_at == None:
      return
    vitalSignData()

def update_houseID(id):
    global house_id
    if id != '':
        house_id = houses[id]
    getALData()
    getRestData()
    getSleepData()
    getVitalsData()

def update_timeFrame(tf):
    global start_at, end_at
    start_at = tf[0].strftime("%Y-%m-%d")
    end_at = tf[1].strftime("%Y-%m-%d")
    getALData()
    getRestData()
    getSleepData()
    getVitalsData()

def update_bathroom(clicked):
    return bathroom_data

def update_timespent(clicked):
    timespent_data['angle'] = timespent_data['Duration']/timespent_data['Duration'].sum() * 2*pi
    timespent_data['color'] = ["#c6dbef","#6baed6","#9ecae1",'#08519c']
    timespent.data_source.data = timespent_data

def update_rest(clicked):
    rest_data['angle'] = rest_data['Duration']/rest_data['Duration'].sum() * 2*pi
    rest_data['color'] = ["#9ecae1","#08519c"]
    rest.data_source.data = rest_data

def update_sleep(clicked):
   return sleep_data

def update_vitals(clicked):
   return vital_data

def update_entry(clicked):
   return entry_data

def update_stats(clicked):
    sleepAlert.object = f'#### Sleep Time: Avg {avg_sleep_time}hrs'
    sysAlert.object = f'#### Systolic: High {high_sys} Low {low_sys}'
    diaAlert.object = f'#### Diastolic: High {high_dia} Low {low_dia}'
    bgAlert.object = f'#### Blood Glucose: High {high_blood_glucose} Low {low_blood_glucose}'
    o2Alert.object = f'#### O2 Saturation: High {high_o2_sat} Low {low_o2_sat}'
    hrAlert.object = f'#### Heart Rate: High {high_resting_heartrate} Low {low_resting_heartrate}'
    painAlert.object = f'#### Pain Scale: High {high_pain_scale} Low {low_pain_scale}'
    wtAlert.object = f'#### Daily Weight: High {high_daily_weight} Low {low_daily_weight}'

    if avg_sleep_time < 6:
       sleepAlert.alert_type = "danger"

    if high_sys > 130 or low_sys < 90:
       sysAlert.alert_type = "danger"

    if high_dia > 110 or low_dia < 60:
        diaAlert.alert_type = "danger"

    if high_blood_glucose > 215 or low_blood_glucose < 50:
       bgAlert.alert_type = "danger"

    if low_o2_sat < 90:
       o2Alert.alert_type = "danger"

    if high_resting_heartrate > 100 or low_resting_heartrate < 60:
        hrAlert.alert_type = "danger"

    if high_pain_scale > 8:
       painAlert.alert_type = "danger"

    if high_daily_weight > 200 or low_daily_weight < 120:
       wtAlert.alert_type = "danger"

    
    
# Create widgets for dashboard
house = pn.widgets.TextInput(name="House ID", placeholder='SHS041')
timeframe = pn.widgets.DatetimeRangeInput(name="Date Range", start=dt.datetime(2022, 6, 1), end=dt.datetime(2024, 4, 1),value=(dt.datetime(2024, 1, 1), dt.datetime(2024, 1, 3)))
interact(update_houseID,id=house) # when house id widget is changed update_houseID will be called
interact(update_timeFrame, tf=timeframe) # when timeframe widget is changed update_timeframe will be called
update_visuals = pn.widgets.Button(name="Update Visuals")

# Plot Bathroom Data
idf = hvplot.bind(update_bathroom,update_visuals).interactive()
yaxis_bathroom = pn.widgets.RadioButtonGroup(
    name='Y axis',
    options=['Trips', 'Avg Time per Trip (mins)'],
    button_type='primary'
)
bathroom_plot = idf.hvplot.bar(x='Date', bar_width=0.2, y=yaxis_bathroom, title='Bathroom Use per Day',rot=45, color="#9ecae1")

# Plot Entry data
idf2 = hvplot.bind(update_entry,update_visuals).interactive()
yaxis_entry = pn.widgets.RadioButtonGroup(
    name='Y axis',
    options=['Trips','Duration Gone (mins)'],
    button_type='primary'
)
entry_plot = idf2.hvplot.bar(x='Date', bar_width=0.2, y=yaxis_entry, title='Exiting Home per Day', rot=45, color='#6baed6')

# Plot sleep data
idf3 = hvplot.bind(update_sleep,update_visuals).interactive()
sleep_plot = idf3.hvplot.bar(x='Date', bar_width=0.2, y='Hours Slept', title='Sleep per Night',rot=45, color="#c6dbef")

# Display vitals data in table
idf4 = hvplot.bind(update_vitals,update_visuals).interactive()
vitals_table = idf4.hvplot.table(columns=['Date','HR','Systolic','Diastolic','O2Sat','BG','Pain','Weight'],width=435)

# Plot Timespent Data
update_visuals.on_click(update_timespent)
timespent_data['angle'] = timespent_data['Duration']/timespent_data['Duration'].sum() * 2*pi
timespent_data['color'] = ["#c6dbef","#6baed6","#9ecae1",'#08519c']
timespent_plot = figure(width=435,height=310, title="Time Spent per Location", toolbar_location=None,
        tools="hover", tooltips="@Location: @Duration Hours", x_range=(-0.5, 1.0))
timespent = timespent_plot.wedge(x=0, y=1, radius=0.4,
    start_angle=cumsum('angle', include_zero=True), end_angle=cumsum('angle'),
    line_color="white", fill_color='color', legend_field='Location', source=timespent_data)
timespent_plot.axis.axis_label=None
timespent_plot.axis.visible=False
timespent_plot.grid.grid_line_color = None

# Plot Rest Data
update_visuals.on_click(update_rest)
rest_data['angle'] = rest_data['Duration']/rest_data['Duration'].sum() * 2*pi
rest_data['color'] = ["#9ecae1","#08519c"]
rest_plot = figure(width=435,height=310, title="Rest Spent per Location", toolbar_location=None,
        tools="hover", tooltips="@Location: @Duration hours", x_range=(-0.5, 1.0))
rest = rest_plot.wedge(x=0, y=1, radius=0.4,
    start_angle=cumsum('angle', include_zero=True), end_angle=cumsum('angle'),
    line_color="white", fill_color='color', legend_field='Location', source=rest_data)
rest_plot.axis.axis_label=None
rest_plot.axis.visible=False
rest_plot.grid.grid_line_color = None


# sidebar color
ast_type = "light"
asys_type = "light"
adia_type = "light"
ao2_type = "light"
ahr_type = "light"
abg_type = "light"
p_type = "light"
wt_type = "light"

# vitals warning
if avg_sleep_time < 6:
   ast_type = "danger"

if high_sys > 130 or low_sys < 90:
   asys_type = "danger"

if high_dia > 110 or low_dia < 60:
    adia_type = "danger"

if high_blood_glucose > 215 or low_blood_glucose < 50:
    abg_type = "danger"

if low_o2_sat < 90:
    ao2_type = "danger"

if high_resting_heartrate > 100 or low_resting_heartrate < 60:
    ahr_type = "danger"

if high_pain_scale > 8:
    p_type = "danger"

if high_daily_weight > 200 or low_daily_weight < 120:
    wt_type = "danger"
    
# Alerts for the sidebar
update_visuals.on_click(update_stats)
sleepAlert = pn.pane.Alert(f'#### Sleep Time: Avg {avg_sleep_time}hrs', alert_type=ast_type, height=38)
sysAlert = pn.pane.Alert(f'#### Systolic: High {high_sys} Low {low_sys}', alert_type=asys_type, height=38)
diaAlert = pn.pane.Alert(f'#### Diastolic: High {high_dia} Low {low_dia}', alert_type=adia_type, height=38)
bgAlert = pn.pane.Alert(f'#### Blood Glucose: High {high_blood_glucose} Low {low_blood_glucose}', alert_type=abg_type, height=38)
o2Alert = pn.pane.Alert(f'#### O2 Saturation: High {high_o2_sat} Low {low_o2_sat}', alert_type=ao2_type, height=38)
hrAlert = pn.pane.Alert(f'#### Heart Rate: High {high_resting_heartrate} Low {low_resting_heartrate}', alert_type=ahr_type, height=38)
painAlert = pn.pane.Alert(f'#### Pain Scale: High {high_pain_scale} Low {low_pain_scale}', alert_type=ahr_type, height=38)
wtAlert = pn.pane.Alert(f'#### Daily Weight: High {high_daily_weight} Low {low_daily_weight}', alert_type=ahr_type, height=38)


# Create and organize dashboard
template = pn.template.FastListTemplate(
    title="SHS study dashboard",
    sidebar=[pn.pane.Markdown("# Data Narratives"),
            pn.pane.Markdown("""#### \n Sleeptime - the amount of time spent sleeping for each day during the given timeframe.
                             \n\n Bathroom – trips to bathroom and avg time spent in bathroom per day for given timeframe. 
                             \n\n Entry – trips leaving the home, total duration gone per day, and avg time gone per day for given timeframe.
                             \n\n Timespent – where most of their time is spent during the given timeframe.
                             \n\n Restspent - where most of their time is spent while resting during the given timeframe."""),
            pn.pane.Markdown("## Controls"),
            house,
            timeframe,
            pn.pane.Markdown("## Relevant stats"),
            sleepAlert,
            sysAlert,
            diaAlert,
            bgAlert,
            o2Alert,
            hrAlert,
            painAlert,
            wtAlert],
    main=[
          pn.Row(pn.Column(update_visuals,sleep_plot.panel(width=460,height=315)),pn.Column(yaxis_bathroom,bathroom_plot.panel(width=460,height=315)),pn.Column(yaxis_entry,entry_plot.panel(width=460,height=315)),width=460,height=390),
          pn.Row(pn.Column(vitals_table),"",pn.Column(timespent_plot,"Hover cursor over slices to observe hours spent in each location"),pn.Column(rest_plot,"Hover cursor over slices to observe hours spent in each location"),width=460,height=390)
    ],
    accent_base_color="#88d8b0",
    header_background="#88d8b0",
)
# show the dashboard
template.show()
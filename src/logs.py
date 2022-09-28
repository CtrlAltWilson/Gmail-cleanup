import pytz
from datetime import datetime
import json

def log(text, text2 = None, json_data = 0,silent = 0):
    if text2 is not None:
        text += text2

    to_zone = pytz.timezone('America/Chicago')
    
    now = datetime.now(to_zone)
    new_time = now.strftime("%Y-%d-%m %I:%M %p")
    if silent == 0:
        print("{}: {}".format(new_time,text))
    if json_data == 1:
        with open('logs.json','w') as f:
            json.dump(text,f)
    else:
        with open("logs.txt","a") as f:
            f.write("{}: {}\n".format(new_time,text))
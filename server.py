from fastapi import FastAPI, UploadFile 
from fastapi.responses import FileResponse 
from fastapi.responses import JSONResponse
from fastapi.responses import Response
from io import StringIO
import logging
import pandas as pd
from utils import BauBuddy

logging.basicConfig(level=logging.DEBUG, filename='server_log.log', filemode='a')

baubuddy = BauBuddy(cache_labels=True)
#Create api
app = FastAPI()

#Send json response
@app.post("/send/")
async def upload_file(file: UploadFile)-> FileResponse:
    #CSV file
    content = await file.read()
    df = prepare(content)
    logging.debug(f'99- {df.columns} ')
    return JSONResponse(content=df.to_json())

def prepare(content):
    #Read CSV file
    s=str(content,'utf-8')
    data = StringIO(s) 
    vehicles = pd.read_csv(data, delimiter=';')
   
    #prepare csv file to dataframe
    active_data = baubuddy.download_active() 
    active_vehicles = pd.DataFrame(data=active_data)
    #Combine dataframes
    result = pd.concat([vehicles, active_vehicles], ignore_index=True)
    #reset index
    result.reset_index(drop=True, inplace=True)
    logging.debug(f"labelIds xxx= {result['labelIds'].dropna(inplace=False)}")
    #Drop drop_duplicates
    result = result.drop_duplicates()
    #Select rows with no missing values
    result = result[~result['hu'].isna()]
    #Create a color code for each value in the labelid column and add a column called color codes
    result['colorCodes'] = result['labelIds'].apply(lambda x: tuple([baubuddy.get_color(l) for l in str(x).split(',') if l not in ('None', 'nan', 'null')]))
    return result


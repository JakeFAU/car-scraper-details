import logging
import requests
import json
import os

import azure.functions as func
import uuid
from azure.storage.blob import BlobServiceClient, BlobClient, ContainerClient, __version__


from typing import Dict, Any
from bs4 import BeautifulSoup


def main(req: func.HttpRequest) -> func.HttpResponse:
    logging.info('Python HTTP trigger function processed a request.')

    make = req.params.get('make')
    model = req.params.get('model')
    year = req.params.get('year')
    logging.info(f'{make}-{model}-{year}')
    if not make:
        try:
            req_body = req.get_json()
        except ValueError:
            pass
        else:
            make = req_body.get('make')
            model = req_body.get('model')
            year = req_body.get('year')

            logging.info(f'{make}-{model}-{year}')

    if make:
        results = check_blob(make, model, year)
        return func.HttpResponse(results) 
    else:
        return func.HttpResponse(
             "This HTTP triggered function executed successfully. Pass a name in the query string or in the request body for a personalized response.",
             status_code=200
        )

def check_blob(make: str, model: str, year:str) -> Dict[str,Any]:
    connect_str = os.getenv('AZURE_STORAGE_CONNECTION_STRING')
    blob_service_client = BlobServiceClient.from_connection_string(connect_str)
    filename = f'{make}/{model}/{year}/data.json'
    try:
        blob_client = blob_service_client.get_blob_client(container="cardata", blob=filename)
        if blob_client.exists():
            return blob_client.download_blob().readall()
        else:
            resp = recalls(make, model, year)
            dets = cardata(make,model,year)
            rev = review(make,model,year)
            results = {"details" : dets,
                        "review" : rev,
                        "recalls" : resp}  
            blob_client.upload_blob(json.dumps(results))
            return json.dumps(results)
    except Exception as ex:
        return json.dumps({"error": str(ex)})



def recalls(make: str, model: str, year:str) -> Dict[str,Any]:
    url = f'http://api.nhtsa.gov/recalls/recallsByVehicle?make={make}&model={model}&modelYear={year}'
    resp = requests.get(url)
    j = resp.json()
    results = j['results']
    recallDict = {} 
    for i, r in enumerate(results):
        recallDict["recall_" + str(i)] = r
    return recallDict

def cardata(make: str, model: str, year:str) -> Dict[str,Any]:
    url = f'https://www.cars.com/research/{make}-{model}-{year}/'
    page = requests.get(url)
    soup = BeautifulSoup(page.text, 'html.parser')
    p_tag = soup.find(class_='specs-list key-specs-list')
    details = ['body','mpg','seats','dims','drivetrain']
    resultDict = {}
    for i, li in enumerate(p_tag.find_all('li')):
        resultDict[details[i]] = "".join(li.text.splitlines()).strip(" ")
        resultDict[details[i]] = resultDict[details[i]].replace('View similar vehicles','')
        resultDict[details[i]] = resultDict[details[i]].replace('See how it ranks','') 
    m_tag = soup.find(class_='msrp-container')
    resultDict['MSRP'] = m_tag.findChild('div').text
    print(resultDict)
    return resultDict

def review(make: str, model: str, year:str) -> Dict[str,Any]:
    url = f'https://www.cars.com/research/{make}-{model}-{year}/'
    page = requests.get(url)
    soup = BeautifulSoup(page.text, 'html.parser')
    e_tag = soup.find(class_='expert-review')
    if e_tag is None:
        return {}
    p_tag = e_tag.findChild('p')
    result_dict = {}
    result_dict['summary'] = p_tag.text
    return result_dict

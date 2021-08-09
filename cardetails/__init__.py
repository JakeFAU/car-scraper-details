import logging
import requests
import json

import azure.functions as func

from typing import Dict, Any


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
        resp = recalls(make, model, year)
        return func.HttpResponse(json.dumps(resp))
    else:
        return func.HttpResponse(
             "This HTTP triggered function executed successfully. Pass a name in the query string or in the request body for a personalized response.",
             status_code=200
        )



def recalls(make: str, model: str, year:str) -> Dict[str,Any]:
    url = f'http://api.nhtsa.gov/recalls/recallsByVehicle?make={make}&model={model}&modelYear={year}'
    resp = requests.get(url)
    j = resp.json()
    results = j['results']
    return results

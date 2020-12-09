## Import Modules - Both are required inthe requirements.txt
from fastapi import FastAPI, Response
import checkdmarc

## Initialise the application
app = FastAPI()

## Endpoint in which the API is hosted
@app.get("/api/dnslookup/{domain}")
async def check_domain(domain: str, response: Response):
    response.headers["Access-Control-Allow-Origin"] = "*" ## Headers to check when a request is made
    search = checkdmarc.check_domains([domain], include_dmarc_tag_descriptions=True) ## What happens when the request is made

    return search ## Return the results of the search on the given domain.

## Feel free to test at https://development.joshh.me/api/dnslookup/ignition-technology.com

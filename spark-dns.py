from fastapi import FastAPI, Response
import checkdmarc

app = FastAPI()

@app.get("/api/dnslookup/{domain}")
async def check_domain(domain: str, response: Response):
    response.headers["Access-Control-Allow-Origin"] = "*"
    search = checkdmarc.check_domains([domain], include_dmarc_tag_descriptions=True)

    return search

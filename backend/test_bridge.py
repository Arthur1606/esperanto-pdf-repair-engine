from werkzeug.wrappers import Request, Response
from a2wsgi import ASGIMiddleware
from fastapi import FastAPI, Request as FastAPIRequest

fastapp = FastAPI()

@fastapp.post("/")
async def root(req: FastAPIRequest):
    body = await req.body()
    return {"got_body": body.decode('utf-8')}

wsgi_app = ASGIMiddleware(fastapp)

def test():
    req = Request.from_values(method="POST", data=b'{"hello":"world"}', content_type="application/json")
    _ = req.data
    
    import io
    environ = req.environ.copy()
    environ['wsgi.input'] = io.BytesIO(req.get_data())
    environ['CONTENT_LENGTH'] = str(len(req.get_data()))
    
    resp = Response.from_app(wsgi_app, environ)
    print(resp.status)
    print(resp.get_data())

test()

from __future__ import annotations
from itertools import count
from urllib.parse import parse_qs
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, JSONResponse
from . import __version__
from .mount import EquatorialMount

_tx = count(1)

def create_app(mount: EquatorialMount) -> FastAPI:
    app = FastAPI(title="Servo42D ASCOM Alpaca", version=__version__)
    connection_clients: set[tuple[str, str]] = set()

    def ok(value=None, client_tx=0):
        result={"ClientTransactionID":int(client_tx or 0),"ServerTransactionID":next(_tx),"ErrorNumber":0,"ErrorMessage":""}
        if value is not None: result["Value"]=value
        return result

    def fail(exc, client_tx=0):
        number = 0x400 if isinstance(exc,(ValueError,RuntimeError)) else 0x401
        if isinstance(exc,NotImplementedError): number=0x400
        return JSONResponse({"ClientTransactionID":int(client_tx or 0),"ServerTransactionID":next(_tx),"ErrorNumber":number,"ErrorMessage":str(exc)})

    async def params(request: Request):
        data={k.lower():v for k,v in request.query_params.items()}
        if request.method=="PUT":
            body=(await request.body()).decode(errors="replace")
            for k,v in parse_qs(body).items(): data[k.lower()]=v[-1]
        return data

    @app.get("/management/apiversions")
    def versions(): return ok([1])
    @app.get("/management/v1/description")
    def description(): return ok({"ServerName":"Servo42D Alpaca","Manufacturer":"Open source","ManufacturerVersion":__version__,"Location":"Local"})
    @app.get("/management/v1/configureddevices")
    def devices(): return ok([{"DeviceName":"Servo42D Equatorial Mount","DeviceType":"Telescope","DeviceNumber":0,"UniqueID":"0c11c515-ea12-49f5-a89d-42d57d000001"}])

    base="/api/v1/telescope/0"
    getters={
      "connected":lambda:mount.connected,"name":lambda:"Servo42D Equatorial Mount","description":lambda:"Dual-axis MKS Servo42D/57D CAN equatorial mount",
      "driverinfo":lambda:f"Servo42D ASCOM Alpaca {__version__}","driverversion":lambda:__version__,"interfaceversion":lambda:3,
      "supportedactions":lambda:[],"rightascension":lambda:mount.right_ascension,"declination":lambda:mount.declination,
      "altitude":lambda:mount.altitude,"azimuth":lambda:mount.azimuth,
      "tracking":lambda:mount.tracking,"slewing":lambda:mount.slewing,"ispulseguiding":lambda:mount.is_pulse_guiding,
      "canslew":lambda:True,"canslewasync":lambda:False,"cansync":lambda:True,"canpulseguide":lambda:True,
      "cansettracking":lambda:True,"cansetguiderates":lambda:False,"canpark":lambda:False,"canunpark":lambda:False,
      "canfindhome":lambda:False,"cansetpark":lambda:False,"cansetpierside":lambda:False,"canslewaltaz":lambda:False,
      "cansetdeclinationrate":lambda:False,"cansetrightascensionrate":lambda:False,
      "declinationrate":lambda:0.0,"rightascensionrate":lambda:0.0,
      "athome":lambda:False,"atpark":lambda:False,
      "alignmentmode":lambda:2,"equatorialsystem":lambda:1,"trackingrate":lambda:0,"trackingrates":lambda:[0],
      "guideratedeclination":lambda:0.5,"guideraterightascension":lambda:0.5,"aperturearea":lambda:0.0,"aperturediameter":lambda:0.0,
      "doesrefraction":lambda:False,"focallength":lambda:0.0,"sideofpier":lambda:0,"siderealtime":lambda:mount.sidereal_time,
      "siteelevation":lambda:mount.site_elevation,"sitelatitude":lambda:mount.site_latitude,"sitelongitude":lambda:mount.site_longitude,
      "slewsettletime":lambda:0,"targetdeclination":lambda:mount.declination,"targetrightascension":lambda:mount.right_ascension,
      "utcdate":lambda:mount.utc_date.isoformat().replace('+00:00','Z')
    }
    for name,fn in getters.items():
        def handler(ClientTransactionID:int=0,_fn=fn):
            try:return ok(_fn(),ClientTransactionID)
            except Exception as e:return fail(e,ClientTransactionID)
        app.add_api_route(f"{base}/{name}",handler,methods=["GET"],name=f"get_{name}")

    @app.put(f"{base}/connected")
    async def connected(request:Request):
        p=await params(request)
        host=request.client.host if request.client else "unknown"
        client=(host,p.get("clientid","0"))
        try:
            desired=p.get("connected","").lower()=="true"
            if desired:
                connection_clients.add(client)
                try:
                    if not mount.connected: mount.connect()
                except Exception:
                    connection_clients.discard(client)
                    raise
            else:
                connection_clients.discard(client)
                if not connection_clients and mount.connected: mount.disconnect()
            return ok(client_tx=p.get("clienttransactionid",0))
        except Exception as e:return fail(e,p.get("clienttransactionid",0))

    @app.put(f"{base}/tracking")
    async def tracking(request:Request):
        p=await params(request)
        try: mount.set_tracking(p.get("tracking","").lower()=="true"); return ok(client_tx=p.get("clienttransactionid",0))
        except Exception as e:return fail(e,p.get("clienttransactionid",0))

    @app.put(f"{base}/trackingrate")
    async def trackingrate(request:Request):
        p=await params(request)
        try:
            if int(p["trackingrate"]) != 0: raise ValueError("Only sidereal tracking is supported")
            return ok(client_tx=p.get("clienttransactionid",0))
        except Exception as e:return fail(e,p.get("clienttransactionid",0))

    @app.get(f"{base}/canmoveaxis")
    async def canmoveaxis(request:Request):
        p=await params(request)
        try:return ok(int(p["axis"]) in (0,1),p.get("clienttransactionid",0))
        except Exception as e:return fail(e,p.get("clienttransactionid",0))

    @app.get(f"{base}/axisrates")
    async def axisrates(request:Request):
        p=await params(request)
        try:
            axis=int(p["axis"])
            if axis not in (0,1,2): raise ValueError("Axis must be 0, 1, or 2")
            value=[] if axis==2 else [{"Minimum":0.0,"Maximum":mount.config.max_axis_rate_deg_per_sec}]
            return ok(value,p.get("clienttransactionid",0))
        except Exception as e:return fail(e,p.get("clienttransactionid",0))

    async def set_float(request:Request, key:str, setter):
        p=await params(request)
        try:setter(float(p[key])); return ok(client_tx=p.get("clienttransactionid",0))
        except Exception as e:return fail(e,p.get("clienttransactionid",0))

    @app.put(f"{base}/sitelatitude")
    async def sitelatitude(request:Request): return await set_float(request,"sitelatitude",mount.set_site_latitude)

    @app.put(f"{base}/sitelongitude")
    async def sitelongitude(request:Request): return await set_float(request,"sitelongitude",mount.set_site_longitude)

    @app.put(f"{base}/siteelevation")
    async def siteelevation(request:Request): return await set_float(request,"siteelevation",mount.set_site_elevation)

    @app.put(f"{base}/utcdate")
    async def utcdate(request:Request):
        p=await params(request)
        try:mount.set_utc_date(p["utcdate"]); return ok(client_tx=p.get("clienttransactionid",0))
        except Exception as e:return fail(e,p.get("clienttransactionid",0))

    @app.put(f"{base}/moveaxis")
    async def moveaxis(request:Request):
        p=await params(request)
        try: mount.move_axis(int(p["axis"]),float(p["rate"])); return ok(client_tx=p.get("clienttransactionid",0))
        except Exception as e:return fail(e,p.get("clienttransactionid",0))

    @app.put(f"{base}/slewtocoordinates")
    async def slew(request:Request):
        p=await params(request)
        try: mount.slew_to(float(p["rightascension"]),float(p["declination"])); return ok(client_tx=p.get("clienttransactionid",0))
        except Exception as e:return fail(e,p.get("clienttransactionid",0))

    @app.put(f"{base}/synctocoordinates")
    async def sync(request:Request):
        p=await params(request)
        try: mount.sync(float(p["rightascension"]),float(p["declination"])); return ok(client_tx=p.get("clienttransactionid",0))
        except Exception as e:return fail(e,p.get("clienttransactionid",0))

    @app.put(f"{base}/pulseguide")
    async def guide(request:Request):
        p=await params(request)
        try: mount.pulse_guide(int(p["direction"]),int(p["duration"])); return ok(client_tx=p.get("clienttransactionid",0))
        except Exception as e:return fail(e,p.get("clienttransactionid",0))

    @app.put(f"{base}/abortslew")
    async def abort(request:Request):
        p=await params(request)
        try: mount.abort(); return ok(client_tx=p.get("clienttransactionid",0))
        except Exception as e:return fail(e,p.get("clienttransactionid",0))

    @app.get("/setup/v1/telescope/0/setup",response_class=HTMLResponse)
    def setup(): return "<h1>Servo42D Equatorial Mount</h1><p>Edit config.json, then restart the service.</p>"
    return app

from __future__ import annotations
import argparse, socket, threading
import can, uvicorn
from .api import create_app
from .config import AppConfig
from .mks_protocol import Servo42dCan, SimulatedMotor
from .mount import EquatorialMount

def discovery(port:int,stop:threading.Event):
    sock=socket.socket(socket.AF_INET,socket.SOCK_DGRAM); sock.setsockopt(socket.SOL_SOCKET,socket.SO_REUSEADDR,1); sock.bind(("",32227)); sock.settimeout(0.5)
    while not stop.is_set():
        try:
            data,addr=sock.recvfrom(64)
            if data==b"alpacadiscovery1": sock.sendto((f'{{"AlpacaPort":{port}}}').encode(),addr)
        except socket.timeout: pass
    sock.close()

def build(config:AppConfig):
    if config.can.interface=="virtual":
        ra=SimulatedMotor(config.mount.ra_gear_ratio); dec=SimulatedMotor(config.mount.dec_gear_ratio)
    else:
        bus=can.Bus(interface=config.can.interface,channel=config.can.channel,bitrate=config.can.bitrate)
        bus_lock=threading.Lock()
        ra=Servo42dCan(bus,config.can.ra_motor_id,bus_lock=bus_lock); dec=Servo42dCan(bus,config.can.dec_motor_id,bus_lock=bus_lock)
    return EquatorialMount(ra,dec,config.mount)

def main():
    parser=argparse.ArgumentParser(); parser.add_argument("--config"); args=parser.parse_args()
    cfg=AppConfig.load(args.config); cfg.validate(); mount=build(cfg); stop=threading.Event()
    if cfg.server.discovery: threading.Thread(target=discovery,args=(cfg.server.port,stop),daemon=True).start()
    try: uvicorn.run(create_app(mount),host=cfg.server.host,port=cfg.server.port)
    finally: stop.set(); mount.ra_motor.close(); mount.dec_motor.close()

if __name__=="__main__": main()

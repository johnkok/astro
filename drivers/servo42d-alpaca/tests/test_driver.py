import can
from fastapi.testclient import TestClient
from servo42d_ascom.api import create_app
from servo42d_ascom.config import MountConfig
from servo42d_ascom.mks_protocol import SimulatedMotor, checksum, command_frame
from servo42d_ascom.mount import EquatorialMount
from servo42d_ascom.mount import SIDEREAL_DEG_PER_SEC

def test_speed_frame():
    frame=command_frame(1,0xF6,bytes([0x80,0x64,0xEC]))
    assert list(frame.data)==[0xF6,0x80,0x64,0xEC,checksum(1,bytes([0xF6,0x80,0x64,0xEC]))]

def make_mount():
    cfg=MountConfig(ra_gear_ratio=1440,dec_gear_ratio=1440,initial_ra_hours=5,initial_dec_degrees=20)
    return EquatorialMount(SimulatedMotor(1440),SimulatedMotor(1440),cfg)

def test_sync_and_goto_simulator():
    m=make_mount(); m.connect(); m.sync(5,20); m.slew_to(6,30)
    assert abs(m.right_ascension-6)<0.001
    assert abs(m.declination-30)<0.001

def test_alpaca_connect_and_coordinates():
    client=TestClient(create_app(make_mount()))
    assert client.put('/api/v1/telescope/0/connected',data={'Connected':'true'}).json()['ErrorNumber']==0
    assert client.get('/api/v1/telescope/0/rightascension').json()['Value']==5
    assert client.get('/management/v1/configureddevices').json()['Value'][0]['DeviceType']=='Telescope'

def test_alpaca_connection_is_leased_per_client():
    client=TestClient(create_app(make_mount()))
    endpoint='/api/v1/telescope/0/connected'
    assert client.put(endpoint,data={'Connected':'true','ClientID':'1'}).json()['ErrorNumber']==0
    assert client.put(endpoint,data={'Connected':'true','ClientID':'2'}).json()['ErrorNumber']==0
    assert client.put(endpoint,data={'Connected':'false','ClientID':'1'}).json()['ErrorNumber']==0
    assert client.get(endpoint).json()['Value'] is True
    assert client.put(endpoint,data={'Connected':'false','ClientID':'999'}).json()['ErrorNumber']==0
    assert client.get(endpoint).json()['Value'] is True
    assert client.put(endpoint,data={'Connected':'false','ClientID':'2'}).json()['ErrorNumber']==0
    assert client.get(endpoint).json()['Value'] is False

def test_nina_required_telescope_properties_and_setters():
    client=TestClient(create_app(make_mount()))
    assert client.put('/api/v1/telescope/0/connected',data={'Connected':'true'}).json()['ErrorNumber']==0
    for name in ('altitude','azimuth','cansetdeclinationrate','cansetrightascensionrate',
                 'declinationrate','rightascensionrate','cansetpark','canslewaltaz'):
        response=client.get(f'/api/v1/telescope/0/{name}')
        assert response.status_code==200
        assert response.json()['ErrorNumber']==0
    assert client.put('/api/v1/telescope/0/sitelatitude',data={'SiteLatitude':'45.0'}).json()['ErrorNumber']==0
    assert client.put('/api/v1/telescope/0/sitelongitude',data={'SiteLongitude':'10.0'}).json()['ErrorNumber']==0
    assert client.put('/api/v1/telescope/0/siteelevation',data={'SiteElevation':'100.0'}).json()['ErrorNumber']==0
    assert client.get('/api/v1/telescope/0/sitelatitude').json()['Value']==45.0
    assert client.get('/api/v1/telescope/0/sitelongitude').json()['Value']==10.0
    assert client.get('/api/v1/telescope/0/siteelevation').json()['Value']==100.0
    assert client.put('/api/v1/telescope/0/utcdate',data={'UTCDate':'2026-10-24T13:00:00Z'}).json()['ErrorNumber']==0
    assert client.put('/api/v1/telescope/0/trackingrate',data={'TrackingRate':'0'}).json()['ErrorNumber']==0

def test_axis_capabilities_and_rates():
    client=TestClient(create_app(make_mount()))
    for axis in (0,1):
        assert client.get('/api/v1/telescope/0/canmoveaxis',params={'Axis':axis}).json()['Value'] is True
        rates=client.get('/api/v1/telescope/0/axisrates',params={'Axis':axis}).json()['Value']
        assert rates==[{'Minimum':0.0,'Maximum':2.0}]
    assert client.get('/api/v1/telescope/0/canmoveaxis',params={'Axis':2}).json()['Value'] is False
    assert client.get('/api/v1/telescope/0/axisrates',params={'Axis':2}).json()['Value']==[]

def test_pulse_guide_uses_exact_relative_encoder_moves_at_sub_rpm_rates():
    cfg=MountConfig(ra_gear_ratio=864,dec_gear_ratio=864,initial_ra_hours=5,initial_dec_degrees=20)
    ra=SimulatedMotor(864); dec=SimulatedMotor(864)
    m=EquatorialMount(ra,dec,cfg); m.connect()

    duration_ms=750
    ra_expected=round(SIDEREAL_DEG_PER_SEC*0.5*(duration_ms/1000)/360*16384*864)
    dec_expected=round(SIDEREAL_DEG_PER_SEC*(duration_ms/1000)/360*16384*864)

    m.pulse_guide(2,duration_ms)  # East / RA-
    assert ra.read_encoder()==-ra_expected
    m.pulse_guide(3,duration_ms)  # West / RA+
    assert ra.read_encoder()==0
    m.pulse_guide(0,duration_ms)  # North / DEC+
    assert dec.read_encoder()==dec_expected
    m.pulse_guide(1,duration_ms)  # South / DEC-
    assert dec.read_encoder()==0
    assert m.is_pulse_guiding is True

def test_ra_pulse_includes_tracking_displacement():
    cfg=MountConfig(ra_gear_ratio=864,dec_gear_ratio=864,initial_ra_hours=5,initial_dec_degrees=20)
    ra=SimulatedMotor(864); m=EquatorialMount(ra,SimulatedMotor(864),cfg); m.connect()
    m.tracking=True
    duration_ms=1000
    m.pulse_guide(2,duration_ms)
    expected=round(SIDEREAL_DEG_PER_SEC*0.5/360*16384*864)
    assert ra.read_encoder()==expected

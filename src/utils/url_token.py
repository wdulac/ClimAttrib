from base64 import urlsafe_b64encode, urlsafe_b64decode
import datetime as dt
import hashlib
import hmac
import struct
import os


SECRET_KEY = os.getenv('URL_SIG_SECRET_KEY').encode('utf-8')
STRUCT_FMT = '>BBIIfff' # 1 + 1 + 4 + 4 + 4 + 4 + 4 = 22 bytes
HASH = hashlib.sha256
HMAC_SIZE = 16 # 16 bytes HMAC Truncature

# Mapping strings to enums for size reduction 
EXTREME_MAP = {'hot': 0, 'cold': 1}
METHOD_MAP = {'yearmax': 0, 'calendar': 1}
EXTREME_INV = {v: k for k, v in EXTREME_MAP.items()}
METHOD_INV = {v: k for k, v in METHOD_MAP.items()}


def encode_token(
    extreme_type: str,
    computation_method: str,
    date: list,
    lat: float,
    lon: float,
    intensity: float
) -> str:

    # Convert dates to int
    start_date = int(date[0].replace('-', ''))
    stop_date  = int(date[1].replace('-', ''))

    # Pack valeus straight into binary for minimal footprint
    payload = struct.pack(
        STRUCT_FMT, 
        EXTREME_MAP[extreme_type],
        METHOD_MAP[computation_method],
        start_date,
        stop_date,
        lat,
        lon,
        intensity
    )

    # Compute SHA256 HMAC to prevent tampering
    sig = hmac.new(SECRET_KEY, payload, HASH).digest()[:HMAC_SIZE]
    # Create token
    token = urlsafe_b64encode(payload + sig).decode('utf-8').rstrip('=')
    
    return token


def decode_token(token: str) -> dict:

    # Add back padding characters and decode token
    raw = urlsafe_b64decode(token + '=' * (-len(token) % 4))
    
    # Separate payload from signature
    payload, sig = raw[:-HMAC_SIZE], raw[-HMAC_SIZE:]

    # Validate signature
    expected_sig = hmac.new(SECRET_KEY, payload, HASH).digest()[:HMAC_SIZE]
    if not hmac.compare_digest(sig, expected_sig):
        raise ValueError("Invalid signature")
    
    # Unpack payload
    extreme_code, method_code, start_date, stop_date, lat, lon, intensity = struct.unpack(STRUCT_FMT, payload)

    # Convert dates to datetime objects
    start_date_dt = dt.datetime.strptime(str(start_date), '%Y%m%d')
    stop_date_dt  = dt.datetime.strptime(str(stop_date), '%Y%m%d')

    # Compute duration and middle date
    middle_date = start_date_dt + (stop_date_dt - start_date_dt)/2
    duration = (stop_date_dt - start_date_dt).days + 1
    
    # Map int flags to human readable values
    extreme_type = EXTREME_INV[extreme_code]
    computation_method = METHOD_INV[method_code]

    return {
        'extreme_type': extreme_type,
        'method': computation_method,
        'start_date': start_date_dt,
        'stop_date': stop_date_dt,
        'date': middle_date,
        'duration': duration,
        'lat': lat,
        'lon': lon,
        'intensity': intensity
    }
import requests
import json

BASE_URL = "http://127.0.0.1:8000"

endpoints = [
    "/api/amapr/portfolio",
    "/api/ssap/verdict/RELIANCE",
    "/api/darkpool/stats",
    "/api/gmss/report/test",
    "/api/biofeedback/status"
]

def check_endpoints():
    print(f"Checking endpoints on {BASE_URL}...")
    for endpoint in endpoints:
        url = f"{BASE_URL}{endpoint}"
        try:
            response = requests.get(url)
            print(f"GET {endpoint}: {response.status_code}")
            if response.status_code == 200:
                print(f"  Success! Response: {json.dumps(response.json())[:100]}...")
            else:
                print(f"  Failed with status {response.status_code}")
        except Exception as e:
            print(f"  Error connecting to {endpoint}: {e}")

if __name__ == "__main__":
    check_endpoints()

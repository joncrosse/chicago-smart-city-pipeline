import os
import requests
import json
from datetime import datetime
from google.cloud import storage
import yaml

def load_config():
    if os.path.exists("config.yaml"):
        with open("config.yaml", "r") as f:
         return yaml.safe_load(f)

    else:
        return{
            'gcp': {
                'project_id': os.environ.get('GCP_PROJECT_ID'),
                'bucket_name': os.environ.get('GCP_BUCKET_NAME')
            },
            'cta':{
                'api_key': os.environ.get('API_KEY')
            }
        }

my_config = load_config()

API_URL = "https://data.cityofchicago.org/resource/pubx-yq2d.json"
PROJECT_ID = my_config['gcp']['project_id']
BUCKET_NAME = my_config['gcp']['bucket_name']

def fetch_chicago_permits():
    

    params = {
        "$limit": 7500,
        "$order": "APPLICATIONSTARTDATE DESC"
    }

    try:
        print(f"[{datetime.now()}] Fetching active permit data from CDOT...")
        response = requests.get(API_URL, params=params)
        response.raise_for_status()

        raw_data = response.json()
        print(f"Successfully retrieved {len(raw_data)} records.")

        #os.makedirs("data/raw/chicago_permits", exist_ok=True)
        #timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        #filename = f"data/raw/chicago_permits/permits_{timestamp}.json"

        #with open(filename, "w") as f:
        #    json.dump(raw_data, f, indent=4)

        #print(f"Data landed locally at: {filename}")

        return raw_data

    except requests.exceptions.RequestException as e:
        print(f"Pipeline Execution Failed: {e}")
        return None

def upload_permits_to_gcs(raw_data):
    storage_client = storage.Client(project=PROJECT_ID)
    bucket = storage_client.bucket(BUCKET_NAME)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    time_path = datetime.now().strftime("%Y/%m/%d")
    blob_name = f"raw/chicago_permits/{time_path}/permits_{timestamp}.json"

    blob = bucket.blob(blob_name)
    
    blob.upload_from_string(
        data=json.dumps(raw_data, indent=4),
        content_type='application/json'
    )

if __name__ == "__main__":
    chicago_permits = fetch_chicago_permits()
    if chicago_permits:
        upload_permits_to_gcs(chicago_permits)
    else:
        print("No Chicago permit data was retrieved, upload skipped.")

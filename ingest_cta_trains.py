
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

API_KEY = my_config['cta']['api_key']
PROJECT_ID = my_config['gcp']['project_id']
BUCKET_NAME = my_config['gcp']['bucket_name']


def fetch_cta_trains():

    api_url = "http://lapi.transitchicago.com/api/1.0/ttpositions.aspx?"

    params = {
        "key": API_KEY,
        "rt": "red,blue,brn,g,org,p,pink,y",
        "outputType": 'JSON'
    }

    try:
        print("Getting data from CTA...")

        response = requests.get(api_url, params=params)
        response.raise_for_status()

        raw_data = response.json()

        print(f"Successfully retrieved {len(raw_data['ctatt']['route'])} train routes.")

        os.makedirs("data/raw/cta_trains/test_trains", exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"data/raw/cta_trains/test_trains/trains_{timestamp}.json"

        with open(filename,"w") as f:
            json.dump(raw_data, f, indent=4)

        return raw_data

    except requests.exceptions.RequestException as e:
        print(f"Pipeline Execution Failed: {e}")
        return None

def upload_cta_to_gcs(raw_data):
    storage_client = storage.Client(project=PROJECT_ID)
    bucket = storage_client.bucket(BUCKET_NAME)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    time_path = datetime.now().strftime("%Y/%m/%d")
    blob_name = f"raw/cta_trains/{time_path}/trains_{timestamp}.json"
    blob = bucket.blob(blob_name)

    blob.upload_from_string(
        data=json.dumps(raw_data, indent=4),
        content_type='application/json'
    )


if __name__ == "__main__":
    cta_data = fetch_cta_trains()
    if cta_data:
        upload_cta_to_gcs(cta_data)
    else:
        print("No CTA data was retrieved, upload skipped.")

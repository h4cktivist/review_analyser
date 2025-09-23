from typing import List, Dict

import json
import requests


def fetch_reviews_with_pagination(initial_url: str, auth_header: str) -> List[Dict]:
    extracted_data = []
    current_url = initial_url
    iteration_count = 0

    headers = {
        'Authorization': auth_header,
        'Content-Type': 'application/json'
    }

    while current_url:
        try:
            response = requests.get(current_url, headers=headers)
            response.raise_for_status()

            data = response.json()

            for review in data.get('reviews', []):
                extracted_review = {
                    'date_created': review.get('date_created'),
                    'text': review.get('text').replace("\n", " ")
                }
                extracted_data.append(extracted_review)

            next_link = data.get('meta', {}).get('next_link')
            current_url = next_link

            iteration_count += 1

            import time
            time.sleep(1)

        except requests.exceptions.RequestException as e:
            print(f"Request error: {e}")
            break
        except json.JSONDecodeError as e:
            print(f"JSON error: {e}")
            break
        except Exception as e:
            print(f"Unexpected error: {e}")
            break

    return extracted_data

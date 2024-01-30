'''
    Meetup API scraping here. 
    
    created 29.01.2024 by bogdansharpy@gmail.com

    Uses publicly accessible Meetup GraphQL API to get information about Events: https://www.meetup.com/api/schema/#Event
    API Endpoint: "https://api.meetup.com/gql"

    Example of how to use script:
        python meetup.py --group pythonireland

    With no arguments by default will get events for group: "pythonireland"
'''

import argparse
import requests
import csv

def get_meetup_data(group):
    graphql_url = "https://api.meetup.com/gql"
    headers = {"Content-Type": "application/json"}
    csv_file_name = f"{group}_meetups.csv"
    payload = {
        "query": """
            query ($urlname: String!) {
                groupByUrlname(urlname: $urlname) {
                    id
                    name
                    pastEvents(input: { first: 100500 }) {
                        count
                        pageInfo {
                            hasNextPage
                            hasPreviousPage
                            startCursor
                            endCursor
                        }
                        edges {
                            node {
                                id
                                status
                                token
                                eventUrl
                                title
                                dateTime
                                endTime
                                description
                                going
                                eventType
                                imageUrl
                                venue {
                                    name
                                    city
                                    address
                                    postalCode
                                    lat
                                    lng
                                }
                                hosts {
                                    id
                                    name
                                }
                                topics {
                                    count
                                    edges {
                                        node {
                                            urlkey
                                            name
                                            id
                                        }
                                    }
                                }
                            }
                        }
                    }
                }
            }
        """,
        "variables": { "urlname": args.group }
    }
    events = []
    try:
        response = requests.post(graphql_url, json=payload, headers=headers)
        if response.status_code == 200:
            result = response.json()
            if (not result) or ('data' not in result) or \
                ('groupByUrlname' not in result['data']) or \
                (not result['data']['groupByUrlname']):
                raise Exception(f"GraphQL empty result")
            events = [event['node'] for event in result['data']['groupByUrlname']['pastEvents']['edges']]
        else:
            raise Exception(f"GraphQL request failed with status code {response.status_code}: {response.text}")
        headers = ['id', 'status', 'title', 'url', 'start_at', 'end_at', 'going', 'eventType', 'venue', 'city', 'address', 'postalCode', 'lat', 'lng', 'hosts', 'topics', 'description']
        with open(csv_file_name, 'w', newline='', encoding='utf-8') as outf:
            csvwriter = csv.DictWriter(outf, delimiter =',', fieldnames=headers)
            csvwriter.writeheader()
            for e in events:
                row = {field: "" for field in headers}
                if 'id' in e: row['id'] = e['id']
                if 'status' in e: row['status'] = e['status']
                if 'title' in e: row['title'] = e['title']
                if 'eventUrl' in e: row['url'] = e['eventUrl']
                if 'dateTime' in e: row['start_at'] = e['dateTime']
                if 'endTime' in e: row['end_at'] = e['endTime']
                if 'going' in e: row['going'] = e['going']
                if 'eventType' in e: row['eventType'] = e['eventType']
                if 'venue' in e and e['venue']:
                    venue = e['venue']
                    if 'name' in venue: row['venue'] = venue['name']
                    if 'city' in venue: row['city'] = venue['city']
                    if 'address' in venue: row['address'] = venue['address']
                    if 'postalCode' in venue: row['postalCode'] = venue['postalCode']
                    if 'lat' in venue: row['lat'] = venue['lat']
                    if 'lng' in venue: row['lng'] = venue['lng']
                if e['hosts']: row['hosts'] = ', '.join([host['name'] for host in e['hosts']])
                if 'topics' in e and 'edges' in e['topics'] and e['topics']['edges']:
                    topics = [topic['node'] for topic in e['topics']['edges']]
                    row['topics'] = ', '.join([topic['name'] for topic in topics])
                if 'description' in e: row['description'] = e['description']
                csvwriter.writerow(row)
        
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Process meetup group url.')
    parser.add_argument('--group', type=str, help='The group url in meetup', default='pythonireland')
    args = parser.parse_args()
    get_meetup_data(args.group)
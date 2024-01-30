'''
    Sessionize API acraping here. 

    created 28.01.2024 by bogdansharpy@gmail.com

    Needs bs4 to be installed: pip install bs4

    Uses publicly accessible Sessionize Embedding API : https://sessionize.com/playbook/embedding
    API Endpoint:
        f"https://sessionize.com/api/v2/{event_id}/view/{type}?under=True"
        type in {"GridSmart", "SpeakerWall", "Speakers", "Sessions"}

    Example of how to use script:
        python sessionize.py --id amtv2kwb --name "PyCon 2022"

    With no arguments by default will get this events: PyCon 2022, PyCon Limerick 2023, PyCon 2023

'''

import argparse
import requests
import csv
from bs4 import BeautifulSoup

events = { \
    'amtv2kwb': 'PyCon 2022', \
    'jb4vxosa': 'PyCon Limerick 2023', \
    'jbshwhme': 'PyCon 2023', \
    }

def get_sessionize_data(event_id, event_name, type):
    url = f"https://sessionize.com/api/v2/{event_id}/view/{type}?under=True"
    csv_file_name = f"{event_name}_{type}.csv"
    text_or_default = lambda el, default: el.text if el else default
    rows = []

    try:
        response = requests.get(url)
        response.raise_for_status()
        soup = BeautifulSoup(response.content, 'html.parser')

        if type == "Speakers":
            rows.append(['id', 'name', 'tagline', 'bio', 'photo']) 
            top_element = soup.find('ul', class_="sz-speakers--list")
            if not top_element:
                raise RuntimeError('Unexpected server response!')
            for row in top_element.find_all('li', class_='sz-speaker'):
                id = row.get('data-speakerid', '')
                name = text_or_default(row.find('h3', class_='sz-speaker__name'), "")
                tagline = text_or_default(row.find('h4', class_='sz-speaker__tagline'), "")
                bio = text_or_default(row.find('p', class_='sz-speaker__bio'), "")
                bio = bio.replace('<br>', '\n')
                photo = ''
                photo_el = row.find('div', class_='sz-speaker__photo')
                if photo_el:
                    photo_img_el = photo_el.find('img')
                    if photo_img_el:
                        photo = photo_img_el.get('src', '')
                rows.append([id, name, tagline, bio, photo]) 
        
        elif type == "Sessions":
            rows.append(['id', 'speaker_id', 'speaker', 'title', 'room_id', 'room', 'start_at', 'end_at', 'description']) 
            top_element = soup.find('ul', class_="sz-sessions--list")
            if not top_element:
                raise RuntimeError('Unexpected server response!')
            for row in top_element.find_all('li', class_='sz-session'):
                id = row.get('data-sessionid', '')
                title = text_or_default(row.find('h3', class_='sz-session__title'), "")
                description = text_or_default(row.find('p', class_='sz-session__description'), "")
                description = description.replace('<br>', '\n')
                room, room_id = '', ''
                room_el = row.find('div', class_='sz-session__room')
                if room_el:
                    room = room_el.text
                    room_id = room_el.get('data-roomid', '')
                time_el = row.find('div', class_='sz-session__time')
                start_at, end_at = '', ''
                if time_el:
                    time_str = time_el.get('data-sztz', '')
                    if time_str:
                        time_arr = time_str.split('|')
                        if len(time_arr) >= 3:
                            start_at = time_arr[2]
                        if len(time_arr) >= 4:
                            end_at = time_arr[3]
                speaker_id, speaker = '', ''
                speakers_el = row.find('ul', class_='sz-session__speakers')
                if speakers_el:
                    for speaker_el in speakers_el.find_all('li'):
                        speaker_id += ', ' if len(speaker_id) else ''
                        speaker_id += speaker_el.get('data-speakerid', '')
                        speaker += ', ' if len(speaker) else ''
                        speaker += text_or_default(speaker_el.find('a'), "")
                rows.append([id, speaker_id, speaker, title, room_id, room, start_at, end_at, description]) 

        with open(csv_file_name, 'w', newline='', encoding='utf-8') as outf:
            csvwriter = csv.writer(outf, delimiter =',')
            for row in rows:
                csvwriter.writerow(row)

    except requests.exceptions.RequestException as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Process event id and name.')
    parser.add_argument('--id', type=str, help='The event id', nargs='?')
    parser.add_argument('--name', type=str, help='The group name', nargs='?')
    args = parser.parse_args()
    if args.id:
        events = { args.id: args.name if args.name else args.id }
    for event_id, event_name in events.items():
        for type in ("Sessions", "Speakers"):
            get_sessionize_data(event_id, event_name, type)

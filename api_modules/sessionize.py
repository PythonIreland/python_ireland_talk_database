'''
    Sessionize API acraping here. 

    created 28.01.2024 by bogdansharpy@gmail.com, updated 09.02.2024

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

class Sessionize:
    def __init__(self, events=None) -> None:
        default_events = { \
            'amtv2kwb': 'PyCon 2022', \
            'jb4vxosa': 'PyCon Limerick 2023', \
            'jbshwhme': 'PyCon 2023', \
        }
        self.events = events if events else default_events

    def get_sessionize_data(self):
        for event_id, event_name in self.events.items():
            for type in ("Sessions", "Speakers"):
                self.__get_sessionize_event(event_id, event_name, type)

    def __get_sessionize_event(self, event_id, event_name, type):
        url = f"https://sessionize.com/api/v2/{event_id}/view/{type}?under=True"
        csv_file_name = f"{event_name}_{type}.csv"
        rows = []
        headers = []

        try:
            response = requests.get(url)
            response.raise_for_status()
            soup = BeautifulSoup(response.content, 'html.parser')

            if type == "Speakers":
                top_element = soup.find('ul', class_="sz-speakers--list")
                if not top_element:
                    raise RuntimeError('Unexpected server response!')

                for row in top_element.find_all('li', class_='sz-speaker'):
                    csv_row = {}
                    # id
                    if row.has_attr('data-speakerid'):
                        csv_row['id'] = row.get('data-speakerid', '').strip()
                    # name
                    name_el = row.find('h3', class_='sz-speaker__name')
                    if name_el:
                        csv_row['name'] = name_el.text.strip()
                    # tagline    
                    tagline_el = row.find('h4', class_='sz-speaker__tagline')
                    if tagline_el:
                        csv_row['tagline'] = tagline_el.text.strip()
                    # bio
                    bio_el = row.find('p', class_='sz-speaker__bio')
                    if bio_el:
                        csv_row['bio'] = bio_el.text.strip().replace('<br>', '\n')
                    #photo
                    photo_el = row.find('div', class_='sz-speaker__photo')
                    if photo_el:
                        photo_img_el = photo_el.find('img')
                        if photo_img_el and photo_img_el.has_attr('src'):
                            csv_row['photo'] = photo_img_el.get('src', '').strip()
                    #
                    rows.append(csv_row)

                headers = ['id', 'name', 'tagline', 'bio', 'photo']
            
            elif type == "Sessions":
                max_speakers = 0
                top_element = soup.find('ul', class_="sz-sessions--list")
                if not top_element:
                    raise RuntimeError('Unexpected server response!')
                    
                for row in top_element.find_all('li', class_='sz-session'):
                    csv_row = {}
                    # id
                    if row.has_attr('data-sessionid'):
                        csv_row['id'] = row.get('data-sessionid', '').strip()
                    # title
                    title_el = row.find('h3', class_='sz-session__title')
                    if title_el:
                        csv_row['title'] = title_el.text.strip()
                    # description
                    description_el = row.find('p', class_='sz-session__description')
                    if description_el:
                        csv_row['description'] = description_el.text.strip().replace('<br>', '\n')
                    # room, room_id
                    room_el = row.find('div', class_='sz-session__room')
                    if room_el:
                        csv_row['room'] = room_el.text.strip()
                        if room_el.has_attr('data-roomid'):
                            csv_row['room_id'] = room_el.get('data-roomid', '').strip()
                    # start_at, end_at
                    time_el = row.find('div', class_='sz-session__time')
                    if time_el:
                        time_str = time_el.get('data-sztz', '')
                        if time_str:
                            time_arr = time_str.split('|')
                            if len(time_arr) >= 3:
                                csv_row['start_at'] = time_arr[2].strip()
                            if len(time_arr) >= 4:
                                csv_row['end_at'] = time_arr[3].strip()
                    # speakerN, speaker_idN
                    speakers_el = row.find('ul', class_='sz-session__speakers')
                    if speakers_el:
                        for i, speaker_el in enumerate(speakers_el.find_all('li')):
                            max_speakers = max(max_speakers, i + 1)
                            speaker_el_a = speaker_el.find('a')
                            if speaker_el_a: 
                                csv_row[f"speaker{i + 1}"] = speaker_el_a.text.strip()
                            if speaker_el.has_attr('data-speakerid'):
                                csv_row[f"speaker_id{i + 1}"] = speaker_el.get('data-speakerid', '').strip()
                    # 
                    rows.append(csv_row) 

                headers = ['id']
                for i in range(max_speakers):
                    headers.append(f"speaker{i + 1}")
                for i in range(max_speakers):
                    headers.append(f"speaker_id{i + 1}")
                headers += ['title', 'room_id', 'room', 'start_at', 'end_at', 'description']

            with open(csv_file_name, 'w', newline='', encoding='utf-8') as outf:
                csvwriter = csv.DictWriter(outf, delimiter =',', fieldnames=headers)
                csvwriter.writeheader()
                for row in rows:
                    csvwriter.writerow(row)

        except requests.exceptions.RequestException as e:
            print(f"Error: {e}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Process event id and name.')
    parser.add_argument('--id', type=str, help='The event id', nargs='?')
    parser.add_argument('--name', type=str, help='The group name', nargs='?')
    args = parser.parse_args()
    events = None
    if args.id:
        events = { args.id: args.name if args.name else args.id }
    sessionizeScraper = Sessionize(events=events)
    sessionizeScraper.get_sessionize_data()
    

import re
import os
import csv
import io
import requests
from db_manager import Base
from sqlalchemy import Column, Integer, String, Boolean
import json
from geopy.geocoders import Nominatim
from db_manager import db_session




class Location(Base):
    __tablename__ = 'Location'
    id = Column(Integer, primary_key=True)
    location = Column(String)

    def __init__(self, location: str):
        self.location = location

    def get_coordinates(self) -> None:
        geolocator = Nominatim(user_agent="MyApp")
        loc = geolocator.geocode(self.location)
        self.lat = str(loc.latitude)
        self.lng = str(loc.longitude)
    
    
    def scrape(self) -> None:  
        self.get_coordinates()
        self.url = "https://api.ebird.org/v2/ref/hotspot/geo?lat=" + self.lat + "&lng=" + self.lng + "&fmt=json"
        payload={}
        headers = {}
        self.locations = []

        response = requests.request("GET", self.url, headers=headers, data=payload)
        response = response.json()

        for locs in response[:100]:
         
            location_data = {
                'locId': locs["locId"],
                'locName': locs["locName"],
                'countryCode': locs["countryCode"],
                'subnational1Code':  locs["subnational1Code"],
                'subnational2Code': locs["subnational2Code"],
                'lat': locs["lat"],
                'lng': locs["lng"],
                'latestObsDt': locs["latestObsDt"],
                'numSpeciesAllTime': locs["numSpeciesAllTime"]
            }
            h = Hotspot(location_data['locName'],location_data['lat'],location_data['lng'],location_data)
            db_session.add(h)
            db_session.commit()
            self.locations.append(h)

    def display(self, locName: bool = False) -> tuple: # 8 LOC
        # return a tuple with the subreddits URL and a list of Posts you want to
        # display (it's possible this may be an empty list)
        # if titles is True, then scrape the subreddit]
        if locName is True: 
            self.scrape()
            locations_list = []
            for i, location in enumerate(self.locations): 
                locations_list.append((location.locName,location.lat,location.lng, location.numSpeciesAllTime,location.id))
                 
        return locations_list

    def __repr__(self) -> str:
        return super().__repr__()
    


class Hotspot(Base):
    __tablename__ = 'Hotspot'
    id = Column(Integer, primary_key=True)
    locName = Column(String)
    lat = Column(String)
    lng = Column(String)

    def __init__(self,locName, lat, lng, data):
        self.locId = data['locId']
        self.locName = locName
        self.countryCode = data['countryCode']
        self.subnational1Code = data['subnational1Code']
        self.subnational2Code = data['subnational2Code']
        self.lat = lat
        self.lng = lng
        self.latestObsDt = data['latestObsDt']
        self.numSpeciesAllTime = data['numSpeciesAllTime']

    def get_regioncode(self) -> None:
    
        # this municipal api is a publicly available, no keys needed afaict
        census_url = str('https://geo.fcc.gov/api/census/area?lat=' +
                        str(self.lat) +
                        '&lon=' +
                        str(self.lng) +
                        '&format=json')

        # send out a GET request:
        payload = {}
        get = requests.request("GET", census_url, data=payload)

        # parse the response, all api values are contained in list 'results':
        response = json.loads(get.content)['results'][0]

        # use the last three digits from the in-state fips code as the "subnational 2" identifier:
        fips = response['county_fips']

        # assemble and return the "subnational type 2" code:
        regioncode = 'US-' + response['state_code'] + '-' + fips[2] + fips[3] + fips[4]
        print('formed region code: ' + regioncode)
        self.regioncode = regioncode
    
    def scrape(self) -> None:
        self.url = "https://api.ebird.org/v2/data/obs/" + self.regioncode + "/recent"
        payload={}
        headers = {'X-eBirdApiToken': '7q8375ctq99e'}
        self.sightings = []
        response = requests.request("GET", self.url, headers=headers, data=payload)
        response = response.json()
        for sighting in response:
            sighting_data = {
                'speciesCode': sighting.get("speciesCode",''),
                'comName': sighting.get("comName",''),
                'locId': sighting.get("locId",''),
                'locName':  sighting.get("locName",''),
                'obsDt': sighting.get("obsDt",''),
                'howMany': sighting.get("howMany", 0),
                'lat': sighting.get("lat",0),
                'lng': sighting.get("lng",0),
                'obsValid': sighting.get("obsValid",False),
                'obsReviewed': sighting.get("obsReviewed",False),
                'locationPrivate': sighting.get("locationPrivate",True),
                'subId': sighting.get("subId",'')
            }
            s = Sighting(sighting_data,sighting_data['speciesCode'])
            db_session.add(s)
            db_session.commit()
            self.sightings.append(s)

    def display(self, loc: int, birdName: bool = False) -> tuple: # 8 LOC
        # return a tuple with the subreddits URL and a list of Posts you want to
        # display (it's possible this may be an empty list)
        # if titles is True, then scrape the subreddit
        if birdName: 
            self.get_regioncode()
            self.scrape()
            sightings_list = []
            for i, sighting in enumerate(self.sightings): 
                sightings_list.append((sighting.comName, sighting.lat, sighting.lng, sighting.speciesCode,sighting.obsDt, sighting.locName,int(sighting.id)))
                 
        return (self.url,sightings_list)
    

    def __repr__(self) -> str:
        return super().__repr__()
    

class Sighting(Base):
    __tablename__ = 'Sighting'
    id = Column(Integer, primary_key=True)
    speciesCode = Column(String)
    

    def __init__(self,data,speciesCode):
        self.speciesCode = speciesCode
        self.comName = data["comName"],
        self.locId = data["locId"],
        self.locName = data["locName"],        
        self.obsDt = data["obsDt"],
        self.howMany = data["howMany"],
        self.lat = data["lat"],
        self.lng = data["lng"],
        self.obsValid = data["obsValid"],
        self.obsReviewed = data["obsReviewed"],
        self.locationPrivate = data["locationPrivate"],
        self.subId = data["subId"]

    def scrape(self) -> None:

        self.url = "https://api.ebird.org/v2/ref/taxonomy/ebird?species=" + self.speciesCode + "&version=2019"
        payload={}
        headers = {'X-eBirdApiToken': '7q8375ctq99e'}
        self.birds = []
        response = requests.request("GET", self.url, headers=headers, data=payload)
        response = response.text

        # Create a file-like object from the text
        f = io.StringIO(response)

        # Use csv.reader to parse the text into a list of lists
        rows = csv.reader(f)

        # Extract the header row and data row from the list of lists
        header = next(rows)
        data = next(rows)

        # Combine the header row and data row into a dictionary
        bird_data = dict(zip(header, data))

        b = Bird(bird_data, bird_data['SPECIES_CODE'])
        db_session.add(b)
        db_session.commit()
        self.birds.append(b)

    def display(self, loc: int, birdName: bool = False) -> tuple: # 8 LOC
        # return a tuple with the subreddits URL and a list of Posts you want to
        # display (it's possible this may be an empty list)
        # if titles is True, then scrape the subreddit
        if birdName: 
            self.scrape()
            birds_list = []
            for i, bird in enumerate(self.birds): 
                birds_list.append((bird.comName, bird.speciesCode,bird.category, bird.taxonOrder, bird.order, bird.familyComName, bird.familySciName,i))
                 
        return (self.url,birds_list)

    def __repr__(self) -> str:
        return super().__repr__()

class Bird(Base):
    __tablename__ = 'Bird'
    id = Column(Integer, primary_key=True)
    speciesCode = Column(Integer)


    def __init__(self,data,speciesCode):
        self.speciesCode = speciesCode
        self.sciName = data['SCIENTIFIC_NAME']
        self.comName = data['COMMON_NAME']
        self.category = data['CATEGORY']
        self.taxonOrder = data['TAXON_ORDER']
        self.order = data['ORDER']
        self.familyComName = data['FAMILY_COM_NAME']
        self.familySciName = data['FAMILY_SCI_NAME']

    def __repr__(self) -> str:
        return super().__repr__()


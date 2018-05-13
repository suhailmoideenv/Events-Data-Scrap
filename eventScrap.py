from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from time import sleep
from lxml import html
import pandas as pd
import collections
import sys
from collections import OrderedDict
import datetime
from dateutil import parser
from dateparser.search import search_dates
import requests
import numpy as np
from datetime import timedelta
import json

now = datetime.datetime.now()

driver = webdriver.Firefox()

def fetchScientificEvents():

    url = 'http://www.globaleventslist.elsevier.com/events/#/filterYears=2018&filterDates=2018-05&continentCodes=EU&countryCodes=GB&sortBy=recency'
    driver.get(url)
    sleep(5)
    parsers = html.fromstring(driver.page_source,driver.current_url)
    pages = parsers.xpath(".//*[@id='paging-top']/ul/li")
    length = len(pages)
    nth = length - 1
    totalPages = parsers.xpath(".//*[@id='paging-top']/ul/li[%s]/a/text()" % nth)
    pageNums = int(totalPages[0])
    place = []
    eventDet = pd.DataFrame([])
    
    for i in range(1,pageNums+1):
        pagUrl = 'http://www.globaleventslist.elsevier.com/events/#/filterYears=2018&filterDates=2018-05&continentCodes=EU&countryCodes=GB&sortBy=recency&page=%s'%i

        driver.get(pagUrl)
        sleep(8)
        parsers = html.fromstring(driver.page_source,driver.current_url)
        eventsContainer = parsers.xpath(".//*[@id='container-events']/div/div")
        for events in eventsContainer:
            venuePlace = events.xpath("div/div/ul/li[3]/strong/text()")
            eventDate = events.xpath("div/div/ul/li[1]/strong/text()")

            eventDate = search_dates(eventDate[0])

            dateLength = len(eventDate)
            if (dateLength > 1):
                eventDate = prevDate
            eventName = events.xpath("div/h3/a/text()")
            prevDate = eventDate
            eventDate = eventDate[0]
            eventOn = eventDate[1].date()
            eventOn = eventOn.strftime('%Y-%m-%d')
            

            eventDet = eventDet.append(pd.DataFrame({'Event':eventName[0],'Venue':venuePlace[0],'Date':eventOn,'Category':'Scientific'}, index=[0]), ignore_index=True)
    return (eventDet)


def fetchBussinessEvents():

    url = 'https://www.eventbrite.com/d/united-kingdom--london/business--events/?crt=regular&end_date=05/31/2018&sort=best&start_date=05/01/2018&subcat=1007'
    driver.get(url)
    sleep(5)
    parsers = html.fromstring(driver.page_source,driver.current_url)

    pages = parsers.xpath("/html/body/div[4]/section[2]/div[7]/nav/div/div/ul/li")

    length = len(pages)
    nth = length - 1
    totalPages = parsers.xpath("/html/body/div[4]/section[2]/div[7]/nav/div/div/ul/li[%s]/a/text()" % nth)
    pageNums = int(totalPages[0])

    place = []
    eventDet = pd.DataFrame([])

    for i in range(1,pageNums+1):
        pagUrl = 'https://www.eventbrite.com/d/united-kingdom--london/business--events/?crt=regular&end_date=05/31/2018&sort=best&start_date=05/01/2018&subcat=1007&page={}'.format(i)
        driver.get(pagUrl)
        sleep(8)
        parsers = html.fromstring(driver.page_source,driver.current_url)

        eventsContainer = parsers.xpath(".//*[@data-automation='event-list-container']/div")

        for events in eventsContainer:
            venuePlace = events.xpath("normalize-space(a/div[2]/div[2]/text())")
            eventDate = events.xpath("normalize-space(a/div[2]/time/text())")
            eventName = events.xpath("normalize-space(a/div[2]/div[1]/text())")

            eventDate = search_dates(eventDate)
            dateLength = len(eventDate)
            if (dateLength > 1):
                eventDate = prevDate

            prevDate = eventDate
            eventDate = eventDate[0]
            eventOn = eventDate[1].date()
            eventOn = eventOn.strftime('%Y-%m-%d')

            eventDet = eventDet.append(pd.DataFrame({'Event':eventName,'Venue':venuePlace,'Date':eventOn,'Category':'Bussiness'}, index=[0]), ignore_index=True)
            

    return (eventDet)

def fetchHotelPrices(dateHotel):
    
    avg = []
    final = pd.DataFrame([])
    
    for start_date in dateHotel:
        lists = []
        datetime_new = datetime.datetime.strptime(start_date,'%m/%d/%Y')
        end_date = datetime_new + timedelta(days=1)
        end_date = datetime.datetime.strftime(end_date, "%m/%d/%Y")

        url = "https://www.expedia.com/Hotel-Search?destination=london&startDate={}&endDate={}&adults=2&star=50,40&lodging=hotels".format(start_date,end_date)
        dates = datetime.datetime.strptime(start_date, '%m/%d/%Y')
        dates = dates.strftime('%Y-%m-%d')
        driver.get(url)
        sleep(20)
        parser = html.fromstring(driver.page_source,driver.current_url)

        hotels = parser.xpath(".//*[@id='resultsContainer']/section/article")

        for hotel in hotels:
            lowestPrice =  hotel.xpath("normalize-space(div[2]/div/div[1]/div[3]/div/div[1]/span/ul/li[@data-automation='actual-price']/span[2]/text())")
            if (lowestPrice is None or lowestPrice == ''):

                lowestPrice =  hotel.xpath("normalize-space(div[2]/div/div[1]/div[3]/div/div[1]/span/ul/li[@data-automation='actual-price']/a/text())")
            else:
                lowestPrice

            if (lowestPrice is None or lowestPrice == ''):
                continue

            lowestPrice = lowestPrice.replace("$","").replace(",","")
            lowestPrice = int(lowestPrice)
            lists.append(lowestPrice)
            
        if (len(lists) == 0):
            continue

        avgPrice = sum(lists) / len(lists)
        
        angDataFrame = pd.DataFrame({'Date':dates,'HotelRate':avgPrice}, index=[0])
        final = final.append(angDataFrame, ignore_index=True)
        
    return (final)


def fetchFlightFare(dateFlight):
    
    avg = []
    final = pd.DataFrame([])
    
    #carrierDetails = [{'origin':'doha','carrier':'QR'},{'origin':'istanbul','carrier':'TK'}]
    carrierDetails = [{'origin':'doha','carrier':'QR'}]
    
    for carriers in carrierDetails:
        source = carriers['origin']
        destination = 'london'
        carrierFlight = carriers['carrier']
        
        for start_date in dateFlight:
            lists = []
            
            dates = datetime.datetime.strptime(start_date, '%m/%d/%Y')
            dates = dates.strftime('%Y-%m-%d')
            
            url = "https://www.expedia.com/Flights-Search?trip=oneway&leg1=from:{0},to:{1},departure:{2}TANYT&passengers=adults:1,children:0,seniors:0,infantinlap:Y&options=carrier:{3},cabinclass:economy,maxhops:0&mode=search&origref=www.expedia.com".format(source,destination,start_date,carrierFlight)
            
            driver.get(url)
            
            parser = html.fromstring(driver.page_source,driver.current_url)
            
            json_data_xpath = parser.xpath("//script[@id='cachedResultsJson']//text()")
            
            raw_json =json.loads(json_data_xpath[0])
            flight_data = json.loads(raw_json["content"])
            
            for i in flight_data['legs'].keys():
                exact_price = flight_data['legs'][i]['price']['totalPriceAsDecimal']
                
                lists.append(exact_price)
                
            if(len(lists) == 0):
                continue
            
            avgPrice = sum(lists) / len(lists)

            angDataFrame = pd.DataFrame({'Date':dates,'FlightRate':avgPrice,'Carrier':carrierFlight}, index=[0])
            final = final.append(angDataFrame, ignore_index=True)
    return (final)


    
science = fetchScientificEvents()
bussiness = fetchBussinessEvents()

consolidated = science.append(bussiness, ignore_index=True)
consolidated = consolidated.sort_values(by='Date')


eventsCount = pd.DataFrame({'count' : consolidated.groupby( ['Date'] ).size()}).reset_index()



#eventsCount = eventsCount.head(5)

dateHotel = eventsCount['Date'].tolist()
dateHotel = [datetime.datetime.strptime(date,'%Y-%m-%d') for date in dateHotel]
dateHotel = np.array(dateHotel)

dateHotel = [d.strftime('%m/%d/%Y') for d in np.unique(dateHotel)]




hotelPrices = fetchHotelPrices(dateHotel)

flightPrices = fetchFlightFare(dateHotel)


prices = pd.merge(flightPrices, hotelPrices, on=['Date'])

events = pd.merge(eventsCount, prices, on=['Date'])

events.set_index('Date', inplace=True)

Json = events.to_json(orient='split')

print (Json)

with open('data.txt', 'w') as outfile:
    json.dump(Json, outfile)
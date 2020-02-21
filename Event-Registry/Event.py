from eventregistry import *
from SPARQLWrapper import SPARQLWrapper, JSON, XML
import json
import simplejson as json
import os
from IntegratedModel import Model as model
from rdflib import Graph, URIRef, RDFS, BNode, Literal, XSD
from rdflib.namespace import RDF, FOAF

# for extructing all the synonyms
import nltk
from nltk.corpus import wordnet  # Import wordnet from the NLTK

nltk.download('wordnet')


def GetSynonyms(name):
    syn = list()
    for synset in wordnet.synsets(name):
        for lemma in synset.lemmas():
            syn.append(lemma.name())  # add the synonyms
    return syn


# manual synonyms
loc_syn = ['loc', 'place', 'venue', 'site', 'spot']
loc_syn += GetSynonyms('location')
label_syn = ['tag', 'title', 'name', 'subtitle', 'subject', 'entitle']
label_syn += GetSynonyms('label')
startTime_syn = ['startTime', 'starts', 'start_time', 'time_starts', 'time_start']
startTime_syn += GetSynonyms('start')
endTime_syn = ['endTime', 'ended', 'end', 'end_Time', 'time_ends', 'time_end']
endTime_syn += GetSynonyms('end')
lon_syn = ['lon', 'Lon', 'longi','longitude']
lon_syn += GetSynonyms('longitude')
lat_syn = ['lat', 'Lat', 'lati','latitude']
lat_syn += GetSynonyms('latitude')
event_syn = ['event', 'event_resource', 'resource']
event_syn += GetSynonyms('event')


def event_kg(sparql_query):
    sparql.setQuery(sparql_query)
    sparql.setReturnFormat(JSON)
    results = sparql.query().convert()
    return results

def event_preprocess(sparql_query):
    sparql.setQuery(sparql_query)
    query_string = sparql.queryString
    event = re.findall(r"dbr:([^ <]+)", query_string)
    event += re.findall(r"label \"(.*)\"", query_string)
    event = "".join(event)
    event = event.replace("_", " ")
    # event = re.findall(r"rdfs:label \'(.*)\'@en", query_string)
    # event.append(re.findall(r"sameAs dbr:(.*)", query_string))
    return event


def GetArticle(event):
    q = QueryArticles(
        conceptUri=er.getConceptUri(event),
        keywords=event,
        keywordsLoc="title",
        lang=["eng"])
    q.setRequestedResult(RequestArticlesInfo(count=20, sortBy="rel"))
    res = er.execQuery(q)
    json_res = json.dumps(res, indent=4)
    return res


def article_mapping(eventName, result_eventRegistry):
    newDatalistwithKRdata = []
    for item in result_eventRegistry['articles']['results']:
        if item['title'].lower().count(eventName.lower()) > 0:
            dataItem = model('', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '')
            dataItem.ERTitle = item['title']
            dataItem.erUri = item['eventUri']
            dataItem.EventName = eventName
            dataItem.erUrl = item['url']
            dataItem.Desc = item['body']
            dataItem.erUriType = item['dataType']
            dataItem.Type = 'Er-Article'
            dataItem.structedFrom = 'https://eventregistry.org/'
            newDatalistwithKRdata.append(dataItem)
    return newDatalistwithKRdata


def GetEvent(event):
    q = QueryEvents(
        conceptUri=er.getConceptUri(event),
        keywords=event,
        keywordsLoc="title",
        lang=["eng"])
    q.setRequestedResult(RequestEventsInfo(sortBy="date", count=50))
    eventRes = er.execQuery(q)
    json_res = json.dumps(eventRes, indent=4)
    return eventRes


def event_mapping(eventName, dataset):
    newDatalistwithRdata = []
    for item in dataset['events']['results']:
        if item['title']['eng'].lower().count(eventName.lower()) > 0:
            dataItem = model('', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '')
            dataItem.Type = 'Er-Event'
            dataItem.EventName = eventName
            dataItem.structedFrom = 'https://eventregistry.org/'
            dataItem.erUri = item['uri']
            dataItem.erUriType = item['categories'][0]['label']
            dataItem.Desc = item['summary']['eng']
            if item['location'] is not None:
                # print("location: ",results[i]['location'])
                if item['location']['country'] is not None:
                    if item['location']['country']['label'] is not None:
                        if item['location']['country']['label']['eng'] is not None:
                            dataItem.Place = item['location']['country']['label']['eng']
                            if item['location']['type'] is not None:
                                dataItem.PlaceType = item['location']['type']
            newDatalistwithRdata.append(dataItem)
    return newDatalistwithRdata


def Create_Rdf_From_FinalModel(finalDataset):
    global event_uri
    g = Graph()
    for data in finalDataset:
        event_name = Literal(data.EventName, lang="en")
        if data.ekgUri != '':
            event_uri = URIRef(data.ekgUri)
        ekg_event = BNode("Event-kg")
        er_articleNode = BNode("Event_registry_article")
        er_eventNode = BNode("Event_registry_event")
        er_place = BNode('Er-Location')  # a GUID is generated
        eventRegistryEntity = BNode('Event-Registry-Relation')  # a GUID is generated
        nPlace = BNode('Location')  # a GUID is generated
        Type = Literal(data.Type)
        PlaceType = Literal(data.PlaceType)
        longitude = Literal(data.longitude, datatype=XSD.float)  # passing a string
        latitude = Literal(data.latitude, datatype=XSD.float)  # passing a python float
        eventDate = Literal(data.EventDate, datatype=XSD.date)  # passing a python date
        event_place = Literal(data.Place)
        Desc = Literal(data.Desc)
        erUrl = Literal(data.erUrl)
        erUriType = Literal(data.erUriType)
        ERTitle = Literal(data.ERTitle, lang="en")
        erUri = Literal(data.erUri)
        nStructedFromAr = BNode('re_Article')  # a GUID is generated
        nStructedFromEv = BNode('re_Event')  # a GUID is generated
        nekg_StructedFrom = BNode('Ekg-Resource')
        structedFrom = Literal(data.structedFrom)

        g.add((ekg_event, FOAF.label, event_name))
        if data.Type == 'Event':
            g.add((ekg_event, RDF.type, Type))
            g.add((ekg_event, FOAF.structedFrom, nekg_StructedFrom))
            g.add((nekg_StructedFrom, FOAF.hasUrl, structedFrom))
        if data.ekgUri != '':
            g.add((ekg_event, FOAF.hasUri, event_uri))
            g.add((event_uri, FOAF.hasType, FOAF.uri))
        if data.Type != 'Event':
            g.add((ekg_event, FOAF.hasRelationWith, eventRegistryEntity))
            g.add((er_eventNode, RDF.type, FOAF.API))
        if data.Type == 'Er-Event':
            g.add((eventRegistryEntity, FOAF.hasEvent, er_eventNode))
            g.add((er_eventNode, RDF.subject, Type))
            g.add((er_eventNode, FOAF.extructedFrom, nStructedFromEv))
            g.add((nStructedFromEv, FOAF.hasUrl, structedFrom))
            if data.ERTitle != '':
                g.add((er_eventNode, FOAF.hasTitel, ERTitle))
            if data.ERTitle != '':
                g.add((er_eventNode, FOAF.hasUrl, erUrl))
            if data.ERTitle != '':
                g.add((er_eventNode, RDF.type, erUriType))
            if data.erUri != '':
                g.add((er_eventNode, FOAF.hasUri, erUri))
            if data.Place != '':
                g.add((er_eventNode, FOAF.hasPlace, er_place))
                g.add((er_place, FOAF.label, event_place))
                g.add((er_place, RDF.type, PlaceType))
        elif data.Type == 'Er-Article':
            g.add((eventRegistryEntity, FOAF.hasArticle, er_articleNode))
            g.add((er_articleNode, RDF.subject, Type))
            g.add((er_articleNode, FOAF.extructedFrom, nStructedFromAr))
            if data.erUrl != '':
                g.add((er_articleNode, FOAF.hasUrl, erUrl))
            if data.ERTitle != '':
                g.add((er_articleNode, FOAF.hasTitel, ERTitle))
            if data.ERTitle != '':
                g.add((er_articleNode, FOAF.hasUrl, erUrl))
            if data.ERTitle != '':
                g.add((er_articleNode, RDF.type, erUriType))
            if data.erUri != '':
                g.add((er_articleNode, FOAF.hasUri, erUri))
            if data.Place != '':
                g.add((er_articleNode, FOAF.hasPlace, er_place))
                g.add((er_place, FOAF.label, event_place))
                g.add((er_place, RDF.type, PlaceType))

        if data.Place != '' and (data.Type != 'Er-Article' or data.Type != 'Er-Event'):
            g.add((ekg_event, FOAF.hasPlace, nPlace))
            g.add((nPlace, RDF.type, FOAF.place))
            g.add((nPlace, FOAF.label, event_place))
            if data.longitude != '':
                g.add((event_place, FOAF.hasLon, longitude))
            if data.latitude != '':
                g.add((event_place, FOAF.hasLat, latitude))
        if data.EventDate != '':
            g.add((ekg_event, FOAF.hasEventDate, eventDate))
            g.add((ekg_event, FOAF.hasStartDate, eventDate))
            g.add((ekg_event, FOAF.hasEndDate, eventDate))
        elif data.StartTime != '' or data.EndTime != '':
            g.add((ekg_event, FOAF.hasStartDate, Literal(data.StartTime, datatype=XSD.date)))
            g.add((ekg_event, FOAF.hasEndDate, Literal(data.EndTime, datatype=XSD.date)))

    output = g.serialize(format='turtle')
    cwd = os.getcwd()  # Get the current working directory (cwd)
    filePath = cwd + "\\" + event_name + ".rdf"
    if os.path.exists(filePath):
        os.remove(filePath)
        f = open(filePath, "x")
        g.serialize(destination=filePath, format='turtle')
        f.close()
    else:
        f = open(filePath, "x")
        g.serialize(destination=filePath, format='turtle')
        f.close()

    print (g.serialize(format='turtle'))



er = EventRegistry(apiKey='YOUR_API_KEY') #get your API key from the Event registry 
sparql = SPARQLWrapper("http://eventkginterface.l3s.uni-hannover.de/sparql")
sparql_query = input("Please enter the sparql query : ")

event_kg_result = event_kg(sparql_query)
entity_list = event_kg_result['head']['vars']

event = event_preprocess(sparql_query)
ekg_dataList = []

for item in event_kg_result['results']['bindings']:
    m1 = model('', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '')
    m1.Type = 'Event'
    m1.structedFrom = 'http://eventkginterface.l3s.uni-hannover.de/'

    # event uri confirmation
    for elem in entity_list:
        if elem in event_syn:
            if item.get(elem):
                m1.ekgUri = item[elem]['value']
    # event label confirmation
    for elem in entity_list:
        if elem in label_syn:
            if item.get(elem):
                m1.EventName = item[elem]['value']
                # m1.EventName = event
        # Location confirmation
        if elem in loc_syn:
            if item.get(elem):
                m1.Place = item[elem]['value']
            # event name confirmation
        if elem in lon_syn:
            if item.get(elem):
                m1.longitude = item[elem]['value']
            # if item.get('longitude'):
            #     m1.longitude = item['longitude']['value']
        if elem in lat_syn:
            if item.get(elem):
                m1.latitude = item[elem]['value']
            # if item.get('latitude'):
            #     m1.latitude = item['latitude']['value']
        # start time confirmation
        if elem in startTime_syn:
            if item.get(elem):
                m1.StartTime = item[elem]['value']
                # if item.get('startTime'):
                #     m1.StartTime = item['startTime']['value']
        # end time confirmation
        if elem in endTime_syn:
            if item.get(elem):
                m1.EndTime = item[elem]['value']
                # if item.get('endTime'):
                #     m1.EndTime = item['endTime']['value']
    if m1.EndTime == m1.StartTime:
        m1.EventDate = m1.StartTime
    if item.get('description'):
        m1.Desc = item['description']['value']
    if item.get('event'):
        m1.ekgUri = item['event']['value']
    ekg_dataList.append(m1)

event_registry_result = GetEvent(event)
event_data_list = event_mapping(event, event_registry_result)

article_registry_result = GetArticle(event)
article_data_list = article_mapping(event, article_registry_result)

# Taking all the list in to one single list
finalDataList = []

finalDataList = ekg_dataList
finalDataList += event_data_list
finalDataList += article_data_list

Create_Rdf_From_FinalModel(finalDataList)

print("Finished")

class Model:
    def __init__(self, EventName, Place, PlaceType, longitude, latitude, ekgUri, Desc, EventDate, StartTime,
                 EndTime, Type, erUri, ERTitle, ERSource, erUrl, erUriType, structedFrom):
        self.EventName = EventName
        self.Place = Place
        self.PlaceType = PlaceType
        self.longitude = longitude
        self.latitude = latitude
        self.ekgUri = ekgUri
        self.Desc = Desc
        self.EventDate = EventDate
        self.StartTime = StartTime
        self.EndTime = EndTime
        self.Type = Type
        self.erUri = erUri
        self.ERTitle = ERTitle
        self.ERSource = ERSource
        self.erUrl = erUrl
        self.erUriType = erUriType
        self.structedFrom = structedFrom

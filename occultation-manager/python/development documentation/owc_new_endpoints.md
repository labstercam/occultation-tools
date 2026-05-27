Emails from Hristo on the new endpoints


Hi Michael,

Apologies for the delay. 

Firstly a few updates. You will be able to hit all all of the API endpoints you use, including the ones you listed:

/api2/v1/events/details-list
/api2/v1/owc/event/my/%s/occelmnts

by simply specifying an HTTP header called OW-ApiKey and not having to provide the API key as a request parameters and not having to provide Basic Auth user name and password (if you are doing this).

The purpose of this change was to simplify how the API can be called. The old way will continue to work but if you are releasing a new version of your software you may want to switch to this new method of authentication with an API Key passed as an HTTP header.

In order to submit a report you will need to send a POST request to: /api2/v1/owc/report-observation and with a application/json content type in the body

The object format is: 

{
    eventId: "", 
    stationId: 0,
    report: 0,
    comment: ""
}

Where the report values are:

int REPORT_NOT_REPORTED = 0;
int REPORT_MISS = 1;
int REPORT_CLOUDED = 2;
int REPORT_FAILED = 3;
int REPORT_POSITIVE = 4;
int REPORT_NOT_OBSERVED = 5;
int REPORT_NOT_REDUCED = 6;

if this is a positive event you can also include a duration property with a value in seconds:

{
    duration: 0.0
}

if you want to update the location of the station the following properties can be included at the same time:

{
    updateLocation: true,
    latDeg: 0.0,
    lngDeg: 0.0,
    altMslMeters: 0.0
}
    

where the altMslMeters property is optional.

I have not built the end-point yet. The end-point is avaiable but is not working. 

I will let you know once it is ready. I may need to do some extra work to bridge the two underlying systems to get this working so it may take me some time. Thanks for your patience.

If you don't hear from me in a week, please ping me.

Hristo.


Hey Michael,

I implemented the report observation so you can give it a go.

Also added one extra method to receive event info by EventId (e.g. for past events where the event ids are known) in order to retrieve the station ids. It is:

https://www.occultwatcher.net/api2/v1/events/%EventID%

Hristo.
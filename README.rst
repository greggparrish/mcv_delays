MANCHESTER VICTORIA STATION DELAYS
==================================
The script streams a live count of the number of delayed departures at Victoria Station in Manchester to a Grok instance every five minutes.


THE DATA
--------
- TRANSPORTAPI <https://www.transportapi.com/>: UK transport data API.  Free accounts offer 1000 hits per day (we only need 288).


WHY
---
When I was living in NYC, subway service was fairly reliable with only occasional problems, and those mostly due to obvious causes: sick passengers, broken trains, police action, or extreme weather.  Heavy rain or snow could create problems on the lines themselves (icing, flooding) as well as an increase in the number of riders.

In Manchester, although the weather was predictably quite grim, the train service was *unpredictably* so.  Train lines or entire stations would frequently be out of service even on Manchester's few sunny days, or running perfectly after a week of heavy rain.

For the challenge, I was curious to see if the weather in Manchester was still a primary cause of poor train service.  The sheer accumulation of rain over weeks, sudden temperature changes, or wind conditions might be playing as vital a role in Manchester as they are in NYC and in just as predictable patterns, even if less obvious.

The first step is getting and storing the number of delays experienced by each station, or in this case, one of them.  This data could then be compared with regional weather data encoded to represent time, wind, temp, precipitation, etc.  In NYC, flooding was greater at some stations than others, but the delay effect would cascade down all connected lines.  Since the transport API provides results for each station, these choke points could be identified along with their susceptibility to particular weather patterns.


WELL, THAT'S NOT TERRIBLY INTERESTING
-------------------------------------
No, but it does provide a potentially interesting analogy for server outages and the mesh of internal and external, social, technological and infrastructural systems within massive networks that succeed or fail quite differently despite surface similarities. Also, I'm honestly interested to see how much of the blame for unpredictable train service is due to the weather.  I suspect it's very little.

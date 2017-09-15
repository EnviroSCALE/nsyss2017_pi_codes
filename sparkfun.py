import time              # time used for delays
import httplib, urllib   # http and url libs used for HTTP POSTs
import socket            # socket used to get host name/IP

#################
## Phant Stuff ##
#################
server = "data.sparkfun.com"  # base URL of your feed
publicKey = "5JpDrdJ29qHKqo0EXN1O"  # public key, everyone can see this
privateKey = "7BjE1eBwz0UKEM0o8mPr"  # private key, only you should know
fields = ["text", "temp", "humidity", "lat", "long", "sound", "co2", "lpg", "ch4", "dust"]  # Your feed's data fields

def getDataList():
    data = {}  # Create empty set, then fill in with our fields:
    for i in range(0, 10):
        data[fields[i]] = "0"
    return data

def writeList(data):
    try:
        ######################
        ## I/O Stuff & Misc ##
        ######################
        myname = socket.gethostname()  # Send local host name as one data field
        ##############
        #print("Sending an update!")
        params = urllib.urlencode(data) # Next, we need to encode that data into a url format:
        headers = {}  # Now we need to set up our headers: start with an empty set
        headers["Content-Type"] = "application/x-www-form-urlencoded"         # These are static, should be there every time:
        headers["Connection"] = "close"         # These are static, should be there every time:
        headers["Content-Length"] = len(params)  # length of data
        headers["Phant-Private-Key"] = privateKey  # private key header

        c = httplib.HTTPConnection(server)         # Now we initiate a connection, and post the data
        # Here's the magic, our reqeust format is POST, we want
        # to send the data to data.sparkfun.com/input/PUBLIC_KEY.txt
        # and include both our data (params) and headers
        c.request("POST", "/input/" + publicKey + ".txt", params, headers)
        r = c.getresponse()  # Get the server's response and print it
        print "        ",  r.status, r.reason
        time.sleep(2)
    except httplib.BadStatusLine:
        print "ERROR: BAD STATUS LINE"
        pass


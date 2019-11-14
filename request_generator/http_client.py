import requests as req
def send_http_load_request(ip_addr, port=5000,load_level=1, timeout=100):
    print ("generating request....")
    get_path = "/load/create_load/" + str(load_level)
    #connection.request("GET", get_path)
    #response = connection.getresponse()
    url = "http://" + ip_addr + ":" + str(port) + get_path
    resp = req.get(url)
    print (resp.text)
    #print("Status: {} and reason: {}".format(response.status, response.reason))

# Unit test
#if __name__ == '__main__':
print("Testinggggg!!!!!!!!!!!!")
send_http_load_request("35.170.37.1", port =5000, load_level=1)

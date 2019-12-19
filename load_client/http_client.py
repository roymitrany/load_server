import requests
import requests as req
import argparse

num_of_servers = 3

def send_http_load_request(ip_addr, port=4999,load_level=1, timeout=100):
    #print ("generating request....")
    #get_path = "/load/create_load/" + str(load_level)
    get_path = "/load/queue_load/" + str(load_level)
    #connection.request("GET", get_path)
    #response = connection.getresponse()
    url = "http://" + ip_addr + ":" + str(port) + get_path
    try:
        resp = req.get(url, timeout=10)
        print (resp.text)
    except requests.ReadTimeout:
        print ('Timeoutttt')
    except:
        print ('Errorrrr on server:', str(ip_addr),':', str(port))

    #print("Status: {} and reason: {}".format(response.status, response.reason))

# Unit test
#if __name__ == '__main__':
print("Testinggggg!!!!!!!!!!!!")
parser = argparse.ArgumentParser(
    description='RRRRRR',
)
parser.add_argument ('server_addr', type=str)
parser.add_argument ('server_port', type=int)
parser.add_argument ('load_level', type=int)
args = parser.parse_args ()

ip_addr = args.server_addr
port = args.server_port
send_http_load_request(ip_addr, port=port, load_level=args.load_level)
#send_http_load_request("35.170.37.1", port =5000, load_level=1)

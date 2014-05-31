import sys
import os.path
import json
import time
import requests


services = ["dropbox", "box"]
service_statuses = {
    "INVALID_ACCESS_TOKEN": 1
    "OK": 2
}

def download_cloud_to_local():
    print "download_cloud_to_local"

def update_cloud_to_local():
    print "update_cloud_to_local"

service_ops = {
    "dropbox": {
        "LOCAL_CREATE": download_cloud_to_local,
        "LOCAL_UPDATE": update_cloud_to_local
    },
    "box": {

    }
}

API_URL_PREFIX = "http://" + "HOSTNAME" + "/api"
GET_ALL_TOKENS_PATH = "/tokens"
GET_TOKEN_PATH = "/token"
GET_FS_TREE_PATH = "/directory"
POST_CREATE_FILE_PATH = "/create"
POST_MODIFY_FILE_PATH = "/modify"
POST_DELETE_FILE_PATH = "/delete"
JSON_HEADER = {'content-type': 'application/json'}

# Create a file and send updates to file mapping server
# Modify a file and send updates to file mapping server
# Delete a file and send updates to file mapping server
# Get access tokens from the file mapping server

# Figure out how updates from file mapping server will be done on the client

# Two roles
# Get file system tree updates from the file mapping server
# Send file system tree updates from the file mapping server
# What happens when a new service is integrated

class FileMappingService:
    def __init__(self, dal, userid, logfile=sys.stdout):
        self.dal = dal
        self.userid = userid
        self.logfile = logfile
        self.access_tokens = {}
        self.get_all_access_tokens()

    def execute_service_op(self, optype, remote_filepath, local_filepath, service, access_token):
        service_op = service_ops[service][optype]
        service_status = service_op((remote_filepath, local_filepath, access_token))
        if service_status == service_statuses["INVALID_ACCESS_TOKEN"]:
            access_token = self.get_access_token(service)
            service_status = service_op((remote_filepath, local_filepath, access_token))
            if service_status != service_statuses["OK"]:
                self.logfile.write("%s encountered %s in %s operation on file %s from cloud to local" % (service, service_status, optype, local_filepath))

    def get_file_system_updates(self):
        url = API_URL_PREFIX + GET_FS_TREE_PATH + "/" + self.userid
        r = requests.get(url)
        jsonr = r.json()
        for service in jsonr:
            if service in services:
                access_token = self.access_tokens[service]
                files = jsonr[service]
                for file in files:
                    local_filepath = file["lid"]
                    remote_filepath = file["rid"]
                    share_link = file["sl"]
                    remote_modified_time = file["mt"]
                    local_modified_time = self.dal.get_last_modified_time(local_filepath)
                    if local_modified_time is None:
                        self.logfile.write("Creating file %s from cloud to local" % local_filepath)
                        self.execute_service_op("LOCAL_CREATE", remote_filepath, local_filepath, service, access_token)
                    elif local_modified_time < remote_modified_time:
                        self.logfile.write("Updating file %s from cloud to local" % local_filepath)
                        self.execute_service_op("LOCAL_UPDATE", remote_filepath, local_filepath, service, access_token)
                    share_status = self.dal.get_share_status(local_filepath)
                    if share_status is None and share_link is not None:
                        self.dal.set_share_status(local_filepath)
            else:
                self.logfile.write("Unrecognized service %s" % service)

    def get_all_access_tokens(self):
        url = API_URL_PREFIX + GET_ALL_TOKENS_PATH + "/" + self.userid
        r = requests.get(url)
        jsonr = r.json()
        for service in jsonr:
            if service in services:
                self.access_tokens[service] = jsonr[service]
            else:
                self.logfile.write("Invalid service provider %s" % service)


    def get_access_token(self, service):
        if service in services:
            url = API_URL_PREFIX + GET_TOKEN_PATH + "/" + service + "/" + self.userid
            r = requests.get(url)
            return json.loads(r.text)

    def post_create_file(self, local_filepath, remote_filepath, service):
        url = API_URL_PREFIX + POST_CREATE_FILE_PATH + "/" + service
        creation_time = os.path.getmtime(local_filepath)
        post_data = {
            "uid": self.userid,
            "lid": local_filepath,
            "rid": remote_filepath,
            "ct": creation_time
        }
        r = requests.post(url, data=json.dumps(post_data), headers=JSON_HEADER)
        return r.status_code == requests.codes.ok

    def post_modify_file(self, local_filepath, service):
        url = API_URL_PREFIX + POST_MODIFY_FILE_PATH + "/" + service
        modification_time =  os.path.getmtime(local_filepath)
        post_data = {
            "uid": self.userid,
            "lid": local_filepath,
            "mt": modification_time
        }
        r = requests.post(url, data=json.dumps(post_data), headers=JSON_HEADER)
        return r.status_code == requests.codes.ok

    def post_delete_file(self, local_filepath):
        url = API_URL_PREFIX + POST_MODIFY_FILE_PATH + "/" + service
        post_data = {
            "uid": self.userid,
            "lid": local_filepath,
        }
        r = requests.post(url, data=json.dumps(post_data), headers=JSON_HEADER)
        return r.status_code == requests.codes.ok
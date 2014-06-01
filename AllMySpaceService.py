import sys
import os.path
import json
import requests
from space_providers.Dropbox import DropboxSyncClient

API_URL_PREFIX = "http://" + "172.16.136.72:8080" + "/api"
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


class AllMySpaceService:
    providers = ["dropbox", "box"]
    service_status = {
        "OK": 1,
        "INVALID_ACCESS_TOKEN": 2
    }
    services = {
        "dropbox": None,
        "box": None
    }

    def __init__(self, dal, userid, logfile=sys.stdout):
        self.dal = dal
        self.userid = userid
        self.logfile = logfile
        self.access_tokens = {}
        self.get_all_access_tokens()

        AllMySpaceService.services["dropbox"] = DropboxSyncClient(self.access_tokens["dropbox"])
        #services["box"] = BoxSyncClient(self.access_tokens["box"])

    def execute_service(self, service, remote_filepath, local_filepath, provider):
        service_rpc = {
            'REMOTE_DELETE': AllMySpaceService.services[provider].delete_file,
            'REMOTE_CREATE': AllMySpaceService.services[provider].upload_file,
            'LOCAL_CREATE' : AllMySpaceService.services[provider].update_cloud_to_local,
            'LOCAL_UPDATE' : AllMySpaceService.services[provider].update_cloud_to_local,
            'REMOTE_UPDATE': AllMySpaceService.services[provider].update_local_to_cloud,
            'SET_ACCESS_TOKEN' : AllMySpaceService.services[provider].set_access_token
        }

        if service == 'REMOTE_DELETE':
            (status, msg) = service_rpc[service](remote_filepath)
        else:
            (status, msg) = service_rpc[service](remote_filepath, local_filepath)

        if status == AllMySpaceService.service_status["INVALID_ACCESS_TOKEN"]:
            access_token = self.get_access_token(provider)
            service_rpc["SET_ACCESS_TOKEN"](access_token)
            if service == 'REMOTE_DELETE':
                (status, msg) = service_rpc[service](remote_filepath)
            else:
                (status, msg) = service_rpc[service](remote_filepath, local_filepath)
            if status != AllMySpaceService.service_status["OK"]:
                self.logfile.write("%s encountered %s in %s operation on file %s from cloud to local" % (provider, status, service, local_filepath))

    def get_file_system_updates(self):
        url = API_URL_PREFIX + GET_FS_TREE_PATH + "/" + self.userid
        r = requests.get(url)
        jsonr = r.json()
        for provider in jsonr:
            if provider in AllMySpaceService.providers:
                #access_token = self.access_tokens[provider]
                files = jsonr[provider]
                for _file in files:
                    local_filepath = _file["lid"]
                    remote_filepath = _file["rid"]
                    share_link = _file["sl"]
                    remote_modified_time = _file["mt"]
                    local_modified_time = self.dal.get_last_modified_time(local_filepath)
                    if local_modified_time is None:
                        self.logfile.write("[" + self.__class__.__name__ + "] creating file %s from cloud to local" % local_filepath)
                        self.execute_service(self, "LOCAL_CREATE", remote_filepath, local_filepath, provider)
                    elif local_modified_time < remote_modified_time:
                        self.logfile.write("Updating file %s from cloud to local" % local_filepath)
                        self.execute_service(self, "LOCAL_UPDATE", remote_filepath, local_filepath, provider)
                        share_status = self.dal.get_share_status(local_filepath)
                    if share_status is None and share_link is not None:
                        self.dal.set_share_status(local_filepath)
            else:
                self.logfile.write("Unrecognized provider %s" % provider)

    def get_all_access_tokens(self):
        url = API_URL_PREFIX + GET_ALL_TOKENS_PATH + "/" + self.userid
        r = requests.get(url)
        jsonr = r.json()
        for provider in jsonr:
            if provider in AllMySpaceService.providers:
                self.access_tokens[provider] = jsonr[provider]
            else:
                self.logfile.write("Unrecognized provider %s" % provider)


    def get_access_token(self, provider):
        if provider in AllMySpaceService.providers:
            url = API_URL_PREFIX + GET_TOKEN_PATH + "/" + provider + "/" + self.userid
            r = requests.get(url)
            return json.loads(r.text)

    def post_create_file(self, local_filepath, remote_filepath, provider):
        url = API_URL_PREFIX + POST_CREATE_FILE_PATH + "/" + provider
        creation_time = os.path.getmtime(local_filepath)
        post_data = {
            "uid": self.userid,
            "lid": local_filepath,
            "rid": remote_filepath,
            "ct": creation_time
        }
        r = requests.post(url, data=json.dumps(post_data), headers=JSON_HEADER)
        return r.status_code == requests.codes.ok

    def post_modify_file(self, local_filepath, provider):
        url = API_URL_PREFIX + POST_MODIFY_FILE_PATH + "/" + provider
        modification_time =  os.path.getmtime(local_filepath)
        post_data = {
            "uid": self.userid,
            "lid": local_filepath,
            "mt": modification_time
        }
        r = requests.post(url, data=json.dumps(post_data), headers=JSON_HEADER)
        return r.status_code == requests.codes.ok

    def post_delete_file(self, local_filepath, provider):
        url = API_URL_PREFIX + POST_DELETE_FILE_PATH + "/" + provider
        post_data = {
            "uid": self.userid,
            "lid": local_filepath,
        }
        r = requests.post(url, data=json.dumps(post_data), headers=JSON_HEADER)
        return r.status_code == requests.codes.ok
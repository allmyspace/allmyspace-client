__author__ = 'jknair'

#from box import BoxClient
#from box import client
from StringIO import StringIO
from client import BoxClient
import client
import json
import ntpath

class BoxSyncClient:

    def __init__(self, oauth2_access_token):
        self._client = BoxClient(oauth2_access_token)
        self.folder_ids = {}

    def _get_parent_folder_id(self, path):
        if path == '/': return 0
        elif path in self.folder_ids: return self.folder_ids[path]
        else:
            parent_path, tail = ntpath.split(path)
            parent = self._get_parent_folder_id(parent_path)
            try:
                self.folder_ids[path] = self._client.create_folder(tail, parent)['id']
            except client.ItemAlreadyExists as error:
                errorDict = json.loads(error.message)
                self.folder_ids[path] = errorDict['context_info']['conflicts'][0]['id']
            return self.folder_ids[path]

    def upload_file(self, box_file_path, local_file_path, replace = False):
        parent_path, filename = ntpath.split(box_file_path)

        # Build parent directories
        parent = self._get_parent_folder_id(parent_path)

        # Upload file
        response = self._client.upload_file(filename, StringIO(open(local_file_path).read()), parent=parent)
        return response['id']

    def delete_file(self, file_id):
        self._client.delete_file(file_id)

    def update_cloud_to_local(self, file_id, local_file_path):
        open(local_file_path, 'wb').write(self._client.download_file(file_id).content)

    def update_local_to_cloud(self, file_id, local_file_path):
        fp = open(local_file_path, 'rb')
        self._client.overwrite_file(file_id, fp)




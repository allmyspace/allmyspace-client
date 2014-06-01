__author__ = 'jknair'

from box import BoxClient
from box import client
from StringIO import StringIO
import json

class BoxSyncClient:

    def __init__(self, oauth2_access_token):
        self._client = BoxClient(oauth2_access_token)
        self.sync_folder_name = 'AllMySpace'
        try:
            response = self._client.create_folder(self.sync_folder_name,0)
            self.sync_folder_id = response['id']
        except client.ItemAlreadyExists, error:
            errorDict = json.loads(error.message)
            self.sync_folder_id = errorDict["context_info"]["conflicts"][0]['id']

    def upload_file(self, dropbox_file_path, local_file_path, replace = False):
        split_paths = []
        split_paths = dropbox_file_path.split("/")
        if split_paths <> []:
            root = split_paths.pop(0)
            if root != self.sync_folder_name:
                raise KeyError
            else:
                self.recursive_walk_dir(split_paths, self.sync_folder_id)
                #TODO

        response = self._client.upload_file(local_file_path,StringIO(open(local_file_path).read()),)
        return response

    def recursive_walk_dir(self, split_paths, parent_folder_id):

        for rootFiles in self._client.get_folder_iterator(parent_folder_id):
            nextPath = split_paths.pop(0)
            if rootFiles['name'] == nextPath:
                self.recursive_walk_dir(split_paths, rootFiles['id'])
            else:
                if split_paths <> []:
                    print split_paths
                else:
                    print split_paths

    def generate_public_url(self, dropbox_file_path):
        return self._client.share(dropbox_file_path)['url']

    def delete_file(self, dropbox_file_path):
        self._client.file_delete(dropbox_file_path)

    def update_local_to_cloud(self, dropbox_file_path, local_file_path):
        return self.upload_file(dropbox_file_path, local_file_path, True)

    def update_cloud_to_local(self, dropbox_file_path, local_file_path):
        open(local_file_path, 'wb').write(self._client.get_file(dropbox_file_path).read())

    def get_file_list(self, dropbox_folder_path):
        folder_metadata = self._client.metadata(dropbox_folder_path)
        return [content['path'] for content in folder_metadata['contents']]




box_sync_client = BoxSyncClient('fJphz0qZCc5pou2za2r0sqxReOuoiTrO')

def token_refreshed_callback(access_token, refresh_token):
    """
    this gets called whenever the tokens have been refreshed. Should persist those somewhere.
    """
    print 'new access token: ' + access_token
    print 'new refresh token: ' + refresh_token

#{u'access_token': u'fJphz0qZCc5pou2za2r0sqxReOuoiTrO', u'restricted_to': [], u'token_type': u'bearer', u'expires_in': 3726, u'refresh_token': u'pDayliAqqgJvQ5cGYMeIZlxoNHxwGHEKecCbYwCUIXu9j2qXMf24MmP5sXbkUtSw'}

from box import CredentialsV2
credentials = CredentialsV2('my_access_token', 'my_refresh_token', 'my_client_id', 'my_client_secret', refresh_callback=token_refreshed_callback)
client = BoxClient(credentials)
#box_sync_client._client.upload_file('abc/hello.txt', StringIO('hello world'))
client = box_sync_client._client
split_paths = "/AllMySpace/test".split("/")
box_sync_client.recursive_walk_dir(split_paths, box_sync_client.sync_folder_id)






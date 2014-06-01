from dropbox.client import DropboxClient
import os

class DropboxSyncClient:
    def __init__(self, oauth2_access_token):
        self.access_token = oauth2_access_token
        self._client = DropboxClient(oauth2_access_token) 

    def upload_file(self, dropbox_file_path, local_file_path, replace=False):
        f = open(local_file_path, 'rb')
        response = self._client.put_file(dropbox_file_path, f, replace)
        return 1, response['path']

    def generate_public_url(self, dropbox_file_path):
        return self._client.share(dropbox_file_path)['url']

    def delete_file(self, dropbox_file_path):
        self._client.file_delete(dropbox_file_path)
        return 1, None

    def update_local_to_cloud(self, dropbox_file_path, local_file_path):
        return 1, self.upload_file(dropbox_file_path, local_file_path, replace=True)

    def update_cloud_to_local(self, dropbox_file_path, local_file_path):
        try:
            try:
                os.makedirs(os.path.dirname(local_file_path))
            except Exception as e:
                pass

            open(local_file_path, 'wb').write(self._client.get_file(dropbox_file_path).read())
            return 1, None
        except Exception as e:
            print e
            return 1, None

    def get_file_list(self, dropbox_folder_path):
        folder_metadata = self._client.metadata(dropbox_folder_path)
        return [content['path'] for content in folder_metadata['contents']]

    def set_access_token(self, access_token):
        self._client = DropboxClient(access_token)

    def get_remaining_space(self):
        quota_info = self._client.account_info()['quota_info']
        return quota_info['total'] - (quota_info['shared'] + quota_info['normal'])

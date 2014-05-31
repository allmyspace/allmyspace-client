from dropbox.client import DropboxClient as original_client

class DropboxSyncClient:
    
    def __init__(oauth2_access_token):
        self._client = DropboxClient(oauth2_access_token) 

    def upload_file(dropbox_file_path, local_file_path, replace = False):
        f = open(local_file_path, 'rb')
        response = self._client.put_file(dropbox_file_path, f, replace)
        return response

    def generate_public_url(dropbox_file_path):
        return self._client.share(path)['url']

    def delete_file(dropbox_file_path):
        self._client.file_delete(dropbox_file_path)

    def update_local_to_cloud(dropbox_file_path, local_file_path):
        return upload_file(dropbox_file_path, local_file_path, True)        

    def update_cloud_to_local(dropbox_file_path, local_file_path):
        open(local_file_path, 'wb').write(self._client.get_file(dropbox_file_path))

    def get_file_list(dropbox_folder_path):
        folder_metadata = self._client.metadata(dropbox_folder_path)
        return [content['path'] for content in folder_metadata['contents']]

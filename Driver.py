import sys
import os.path
import pyinotify
from AllMySpaceService import AllMySpaceService
from space_providers.Dropbox import DropboxSyncClient
from DAL import DAL
import time

settings = {
    'watch-manager': None,
    'event-mask': pyinotify.IN_ATTRIB | pyinotify.IN_CLOSE_WRITE | pyinotify.IN_CREATE | pyinotify.IN_DELETE | pyinotify.IN_DELETE_SELF | pyinotify.IN_MODIFY | pyinotify.IN_MOVE_SELF | pyinotify.IN_MOVED_FROM | pyinotify.IN_MOVED_TO
}

DROPBOX_OAUTH_TOKEN = ''
PROVIDER_HOME_DIRECTORY = '/AllMySpace'

PROVIDER_DROPBOX = 'dropbox'
PROVIDER_BOX     = 'box'


def get_path_relative_to_watched_directory(original_path):
    global root_dir_path
    relative_path = ''
    if original_path.startswith(root_dir_path):
        relative_path = original_path[len(root_dir_path):]
    if relative_path.startswith('/'):
        return relative_path
    else:
        return '/' + relative_path


def get_provider_relative_path(relative_path):
    global PROVIDER_HOME_DIRECTORY
    return PROVIDER_HOME_DIRECTORY + relative_path


class EventHandler(pyinotify.ProcessEvent):

    def my_init(self, file_object=sys.stdout):
        self._file_object = file_object

    def process_IN_ATTRIB(self, event):
        self._file_object.write('%s: File metadata changed \n' % event.name)

    def process_IN_CLOSE_WRITE(self, event):
        test='test'

    def process_IN_CREATE(self, event):
        self._file_object.write('%s: created at path %s\n' % (event.name, event.pathname))
        if os.path.isdir(event.pathname) and (not os.path.islink(event.pathname)):
            os.path.walk(event.pathname, visit, settings)
            return

        try:
            #TODO: Choose the service below
            provider = 'box'
            if provider in AllMySpaceService.providers:
                relative_path = get_path_relative_to_watched_directory(event.pathname)
                (status, remote_path) = settings['all-my-space-service'].execute_service('REMOTE_CREATE', get_provider_relative_path(relative_path), relative_path, provider)
                sys.stderr.write("here\n")
                settings['dal'].add_file(relative_path, remote_path, provider, os.path.getmtime(event.pathname))
                settings['all-my-space-service'].post_create_file(event.pathname, remote_path, provider)
            else:
                self.file_object.write("Unrecognized provider %s" % provider)
        except Exception as e:
            print e

    def process_IN_DELETE(self, event):
        self._file_object.write('%s: deleted at path %s\n' % (event.name, event.pathname))
        if os.path.isdir(event.pathname) or os.path.islink(event.pathname):
            return
        try:
            relative_path = get_path_relative_to_watched_directory(event.pathname)
            db_entry = settings['dal'].get_file_mappings(relative_path)
            provider = db_entry['provider']
            if provider in AllMySpaceService.providers:
                settings['all-my-space-service'].execute_service('REMOTE_DELETE', db_entry['remote_path'], relative_path, provider)
            else:
                self.file_object.write("Unrecognized provider %s" % provider)
            settings['dal'].delete_file(relative_path)
            settings['all-my-space-service'].post_delete_file(event.pathname, provider)

        except Exception as e:
            print e

    def process_IN_DELETE_SELF(self, event):
        test='test'

    def process_IN_IGNORED(self, event):
        test='test'

    def process_IN_MODIFY(self, event):
        time.sleep(1)
        self._file_object.write('%s: modified at path %s\n' % (event.name, event.pathname))
        if os.path.isdir(event.pathname) or os.path.islink(event.pathname):
                return
        try:
            relative_path = get_path_relative_to_watched_directory(event.pathname)
            db_entry = settings['dal'].get_file_mappings(relative_path)
            provider = db_entry['provider']
            if provider in AllMySpaceService.providers:
                settings['all-my-space-service'].execute_service('REMOTE_UPDATE', db_entry['remote_path'], relative_path, provider)
                settings['all-my-space-service'].post_modify_file(event.pathname, provider)
        except Exception as e:
            print e

    def process_IN_MOVE_SELF(self, event):
        test='test'

    def process_IN_MOVED_FROM(self, event):
        self._file_object.write('%s: moved at path %s with cookie = %s\n' % (event.name, event.pathname, event.cookie))
        self.process_IN_DELETE(event)

    def process_IN_MOVED_TO(self, event):
        self._file_object.write('%s: moved from %s to %s with cookie %s\n' % (event.name, event.src_pathname, event.pathname, event.cookie))
        self.process_IN_CREATE(event)

    def process_default(self, event):
        self._file_object.write('Default event processing ...')


def visit(settings, dirname, names):
    if not os.path.islink(dirname):
        settings['watch-manager'].add_watch(dirname, settings['event-mask'])

if __name__ == '__main__':
    #dropbox_client = DropboxSyncClient(DROPBOX_OAUTH_TOKEN)
    argsLen = len(sys.argv)
    if argsLen != 2:
        print("Usage: driver.py <allmyspace directory>")
        sys.exit(0)
    else:
        userid = str(raw_input("enter username: "))
        root_dir_path = str(sys.argv[1])
        if os.path.exists(root_dir_path) and (not os.path.islink(root_dir_path)) and os.path.isdir(root_dir_path):
            settings['dal'] = DAL()

            print("Syncing %s with the cloud ... " % root_dir_path)
            all_my_space_service = AllMySpaceService(settings['dal'], userid, root_dir_path)
            settings['all-my-space-service'] = all_my_space_service
            all_my_space_service.get_file_system_updates()

            watch_manager = pyinotify.WatchManager()
            settings['watch-manager'] = watch_manager
            os.path.walk(root_dir_path, visit, settings)

            event_handler = EventHandler()
            notifier = pyinotify.Notifier(watch_manager, default_proc_fun=event_handler)
            try:
                notifier.loop()
            except pyinotify.NotifierError, err:
                print >> sys.stderr, err
        else:
            print "The directory doesn't exist or the appropriate file permissions are not set"
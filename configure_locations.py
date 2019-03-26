import logging
import datetime

import ftrack_api
import ftrack

'''
import ftrack_api
SERVER_URL =r'https://foobar-ltd.ftrackapp.com'
API_KEY = r'ZGUzMDRhNDktMzc0YS00ZmQ2LWFkOTMtMDQ2NjBhOGJjNGJmOjpkZGYzNTFhMC03N2E2LTRjMmMtYmY2ZC05NDljZWE0ODUzMDI'
api_user='trevor@theend.ws'
session = ftrack_api.Session(server_url=SERVER_URL, api_key=API_KEY, api_user=api_user )
'''

# http://ftrack-connect.rtd.ftrack.com/en/latest/developing/tutorial/adding_a_location.html

def configure_locations(event):
    session = event['data']['session']

    # ensure creates only if doesnt exist already
    f_drive_drive_location = session.ensure('Location', {'name': 'foobar-ltd.f_drive'})
    f_drive_drive_location.priority = 0
    f_drive_drive_location.structure = ftrack_api.structure.standard.StandardStructure()
    f_drive_drive_location.accessor = ftrack_api.accessor.disk.DiskAccessor(prefix=prefix='F:\ftrack' )

    # create an alternative location
    d_drive_drive_location = session.ensure('Location', {'name': 'foobar-ltd.d_drive'})
    d_drive_drive_location_drive_drive_location.priority = 0
    d_drive_drive_location.structure = ftrack_api.structure.standard.StandardStructure()
    d_drive_drive_location.accessor = ftrack_api.accessor.disk.DiskAccessor(prefix=prefix='D:\ftrack' )

#on publish one move from one location to another
#notify user

def register(*args, **kwargs):
    '''
    Register plugin only if args[0] is a compatable session object.
    If not, ignore and return
    '''
    if not isinstance(args[0], ftrack_api.Session):
        return

    session.event_hub.subscribe(
        'topic=ftrack.api.session.configure-location',
        configure_locations
    )


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    session = ftrack_api.Session()
    register(session)

    session.event_hub.wait()
import logging
import datetime

import ftrack_api
import ftrack

'''
NOTE: this plugin isnt a class and has no discover() method and 
as such will not show in the connect UI
'''

# http://ftrack-connect.rtd.ftrack.com/en/latest/developing/tutorial/adding_a_location.html

def configure_locations(event):
    '''
    Set up 2 alternative locations on D:\\ and F:\\ drives
    '''
    session = event['data']['session']

    # ensure creates only if doesnt exist already
    f_drive_drive_location = session.ensure('Location', {'name': 'foobar-ltd.f_drive'})
    f_drive_drive_location.priority = 0
    f_drive_drive_location.structure = ftrack_api.structure.standard.StandardStructure()
    f_drive_drive_location.accessor = ftrack_api.accessor.disk.DiskAccessor(prefix='F:\\ftrack')

    # create an alternative location
    d_drive_drive_location = session.ensure('Location', {'name': 'foobar-ltd.d_drive'})
    d_drive_drive_location.priority = 0
    d_drive_drive_location.structure = ftrack_api.structure.standard.StandardStructure()
    d_drive_drive_location.accessor = ftrack_api.accessor.disk.DiskAccessor(prefix='D:\\ftrack')


def register(*args, **kwargs):
    '''
    Register plugin only if args[0] is a compatable session object.
    If not, ignore and return
    '''
    if not isinstance(args[0], ftrack_api.Session):
        return

    args[0].event_hub.subscribe(
        'topic=ftrack.api.session.configure-location',
        configure_locations
    )


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    session = ftrack_api.Session(auto_connect_event_hub=True)
    register(session)

    session.event_hub.wait()
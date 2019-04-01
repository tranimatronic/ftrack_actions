import logging
import datetime
import functools

import ftrack_api
import ftrack

# TODO - Exapnd into a PRE-Render action - pulling all scene assets local
# given shot id, query ALL items and ensure they are local

#Use the event system to transfer the file from one location to another at publish time.
#Notify the user in the web UI about the transfer.


class LocationSyncAction(object):
    label = 'Location Action'
    identifier = 'location.action'
    description = 'Location filesystem sync'

    def __init__(self, session):
        '''
        Initialise action. Capture session as local object
        '''
        super(LocationSyncAction, self).__init__()
        self.session = session
        self.logger = logging.getLogger(__name__ + '.' + self.__class__.__name__)


    def component_event_callback(self, event):
        '''
        This is the callback function called when component added subscription is triggered. 
        If version is PUBLISHED, make sure this component is available to ALL locations.
        '''
        # ensure this is a user-event
        if 'id' in event['source']['user']:
            user_id = event['source']['user']['id']

        # retrieve the required objects
        component_object = self.session.query("Component where id is '%s'"%event['data']['component_id']).first()
        location_object = self.session.query("Location where id is '%s'"%event['data']['location_id']).first()
        version_object = self.session.query("AssetVersion where id is '%s'"%component_object['version_id']).first()

        # if the parent version object is published, ensure 
        # this component is available in all other locations
        if version_object['is_published']:
            complete_locations=[]
            incomplete_locations=[]
            available_locations=[]
            for location_id, availability in component_object.get_availability().iteritems():
                if availability==100.0:
                    complete_locations.append(location_id)
                else:
                    incomplete_locations.append(location_id)

            # if we have locatiions where this item is not 100% available, 
            # add component to that location
            if len(incomplete_locations):
                source_location = self.session.query('Location where id is %s'%complete_locations[0]).one()
                for location_id in incomplete_locations:
                    try:
                        location = self.session.query('Location where id is %s'%location_id).one()
                        location.add_component(component_object, source_location, recursive=True)
                        available_locations.append((component_object['name'], location['name'], True))
                    except ftrack_api.exception.LocationError, e:
                        available_locations.append((component_object['name'], location['name'], False))
                self.session.commit()
        
        # call web-UI noticication of which locations now have file(s)
		# showing 'False' where this item is UNAVAILABLE 
        self.trigger_UI_event(user_id, available_locations)
        return

    def trigger_UI_event(self, user_id, available_locations):
        '''
        trigger new event that shows form in web UI 
        '''
        data={
                'type': 'form',
                'items': [{'value': '## File Location Sync ##', 'type': 'label'}],
                'actionIdentifier':self.identifier
            }

        # populate UI with information on transfer sucess
        for item in available_locations:
            data['items'].append({'value':"Added to location : %s : %s"%(item[1], str(item[2])), 'type': 'label' })

        # create UI event
        event = ftrack_api.event.base.Event(topic='ftrack.action.trigger-user-interface', data=data,
                target=('applicationId=ftrack.client.web and user.id=%s'%user_id)
        )
        # trigger event to show UI
        self.session.event_hub.publish(event)
        return

    def register(self):
        '''
        Register action. Subscribe to event hub topics 
        and direct triggered events to specified function
        '''
        self.session.event_hub.subscribe(
            'topic=ftrack.action.discover and source.user.username={0}'.format(
                self.session.api_user
            ),
            self.discover
        )

        #subscribe to component added to location notifiations
        self.session.event_hub.subscribe('topic=ftrack.location.component-added', self.component_event_callback)

    def discover(self, event):
        '''
        Called by ftrack.action.discover on startup. This shows 
        the plugin exists and is working in the connect UI
        '''
        data = event['data']
        return {
            'items': [{
                'label': self.label,
                'description': self.description,
                'actionIdentifier': self.identifier
            }]
        }

def register(*args, **kw):
    '''
    Register plugin only if args[0] is a compatable session object.
    If not, we are bing called by old API - ignore and return
    '''
    if not isinstance(args[0], ftrack_api.Session):
        return

    action = LocationSyncAction(args[0])
    action.register()


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    session = ftrack_api.Session(auto_connect_event_hub=True)
    register(session)

    session.event_hub.wait()
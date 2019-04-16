import logging
import datetime

import ftrack_api
import ftrack

'''

This is a custom event plugin to be used with the ftrack 
asset management API 
https://www.ftrack.com/en/

Requires ftrack_api to be installed and accessible in sys.path:
pip install ftrack-python-api

If a task object is approved in the WebUI, and there is no 
accompanying note, trigger a popup UI asking for one.
If the response is none, or an empty string, re-show the UI 
until the response is valid 

'''


class ApprovalNoteAction(object):
    '''Custom Approval Note Action'''

    label = 'Approval Note Action'
    identifier = 'approval.note.action'
    description = 'This enforces a note when task set to Approved'

    def __init__(self, session):
        '''Initialise action.'''
        super(ApprovalNoteAction, self).__init__()
        self.session = session
        self.logger = logging.getLogger(
            __name__ + '.' + self.__class__.__name__
        )

    def update_event_callback(self, event):
        '''
        This is the callback function called by update event subscription. 
        Check event type == update, for task selection, for approve status. 
        if there is no approval note, Bring up UI asking for one. Repeat if
        value is invalid
        '''
        #if this is a return call, the event['data'] will contain 'values' key
        user_id = event['source']['user']['id']
        if 'values' in event['data']:
            values = event['data']['values']
            note_text=values['approval_note']
            original_task_id=values['original_task_id']
            #check we have a valid value, if not re-show the UI
            if not 'approval_note' in values or values['approval_note']=="":
                self.trigger_UI_event(user_id)

            #add note to approval. 
            #NOTE: this is added as a COMMENT to the task_object 
            task_object = self.session.query("Task where id is {0}".format(original_task_id).first())
            user_object = self.session.query("User where id is {0}".format(event['source']['user']['id']).first())
            if task_object and user_object:
                note = task_object.create_note(note_text, user_object)
                self.session.commit()
            return
        

        for entity in event['data'].get('entities', []):
            #if event is not update, and is not task return
            if not entity['action']=='update':
                self.logger.warning("ACTION NOT UPDATE {0}".format(entity['action']))
                return
            if not entity['entityType']=='task':
                self.logger.warning("EVENT NOT TASK {0}".format(entity['entityType']))
                return 

            #if we get here the event is an UPDATED task 
            if 'statusid' in entity['changes']:
                #if this status is approved
                if entity['changes']['statusid']['new'] == '44de097a-4164-11df-9218-0019bb4983d8':
                    #check if it has a note, if not show the UI
                    if not 'notes' in entity['changes']:
                        self.trigger_UI_event(user_id, entity['entityId'])
                    else:
                        self.logger.info('Approved Task already contains note')

    def trigger_UI_event(self, user_id, origial_task_id):
        '''
        trigger new event that shows form in web UI 
        to add note, returning data to this action
        '''
        event = ftrack_api.event.base.Event(
        topic='ftrack.action.trigger-user-interface',
        data={
                'type': 'form',
                'items': [{'value': '## User must enter note. ##', 'type': 'label'}, 
                        {'label': 'Please enter approve note', 'name': 'approval_note',
                        'value': '', 'type': 'textarea'},
                        {'value': origial_task_id,'name': 'original_task_id','type': 'hidden'}],
                'actionIdentifier':self.identifier},
        target=('applicationId=ftrack.client.web and user.id={0}'.format(user_id))
        )
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

        self.session.event_hub.subscribe(
            'topic=ftrack.action.launch and data.actionIdentifier={0} and '
            'source.user.username={1}'.format(
                self.identifier,
                self.session.api_user
            ),
            self.update_event_callback
        )
        #register on update action - send event to update_event_callback
        self.session.event_hub.subscribe('topic=ftrack.update', self.update_event_callback)


    def discover(self, event):
        '''
        Return action config if triggered on a single asset version.
        Called by ftrack.action.discover on startup. Makes plugin 
        available if ONE 'assetversion' is selecxted 
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
    If not, ignore and return
    '''
    if not isinstance(args[0], ftrack_api.Session):
        return

    action = ApprovalNoteAction(args[0])
    action.register()


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    # if called via connect, authentication is stored in environment
    # which is picked up by the Session constructor, therefore unneeded here
    session = ftrack_api.Session(auto_connect_event_hub=True)
    register(session)

    session.event_hub.wait()
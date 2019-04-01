import logging
import datetime

import ftrack_api
import ftrack

class PermissionCheckAction(object):
    '''Custom action.'''

    label = 'Permission Check Action'
    identifier = 'permission.check.action'
    description = 'Show warning if incorrect permission'

    def __init__(self, session):
        '''Initialise action.'''
        super(PermissionCheckAction, self).__init__()
        self.session = session
        self.logger = logging.getLogger(
            __name__ + '.' + self.__class__.__name__
        )

    def launch(self, event):
        '''
        This is the callback function called by launch event subscription. 
        Select task, run this action. Then, if we are admin add a note to 
        the task. If not - rollback the session.
        To test as non-admin user, uncomment line 40
        '''
        user_id = event['source']['user']['id']
        user_security_roles = self.session.query('UserSecurityRole where user.id is "{0}"'.format(user_id)).all()
        all_security_ids=[x['security_role']['id'] for x in user_security_roles]
        
        selection = event['data'].get('selection', [])
        event_source_id=selection[0]['entityId']
        event_object_type=selection[0]['entityType']


        #security_role = self.session.query('SecurityRole  where id is "{0}"'.format(securityId)).first()
        admin_id='3142c846-acb6-11e1-b159-f23c91df1211'
        #all_security_ids=['xxxxxxxxxxxxxx'] #set to this one for testing
        if not '3142c846-acb6-11e1-b159-f23c91df1211' in all_security_ids:
            self.trigger_UI_event(user_id, event_source_id, message="Must be administrator to perform this action")
            #rollback last change
            #TODO - only roll back LAST operation
            #local_operations = self.session.recorded_operations
            #self.logger.info("event :  ={0}".format(local_operations))
            self.session.rollback()
            return
        else:
            self.logger.info("event :  ={0}".format(event))
            task_object = self.session.query("%s where id is %s"%(event_object_type.title(), event_source_id)).first()
            user_object = self.session.query("User where id is %s"%event['source']['user']['id']).first()
            if task_object and user_object:
                note_text="Admin Clicked Action"
                note = task_object.create_note(note_text, user_object)
                self.session.commit()
            else:
                self.logger.info("No task/user found %s %s"%(event_object_type.title(),event_source_id))
                self.logger.info("task_object :  ={0}".format(task_object))
                self.logger.info("user_object :  ={0}".format(user_object))

    def trigger_UI_event(self, user_id, origial_task_id, message=None):
        '''
        trigger new event that shows message in web UI 
        REMOVED actionIdentifier to stop callbacks from this notification
        '''
        if not message:
            message='This action is Admin only'

        event = ftrack_api.event.base.Event(
        topic='ftrack.action.trigger-user-interface',
        data={
                'type': 'form',
                'items': [{'value': message, 'type': 'label'}, 
                        {'value': origial_task_id,'name': 'original_task_id','type': 'hidden'}],
                #'actionIdentifier':self.identifier
            },
        target=('applicationId=ftrack.client.web and user.id=%s'%user_id)
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
            self.launch
        )

    def discover(self, event):
        '''
        Called by ftrack.action.discover on startup. 
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

    action = PermissionCheckAction(args[0])
    action.register()


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    session = ftrack_api.Session(auto_connect_event_hub=True)
    register(session)

    session.event_hub.wait()
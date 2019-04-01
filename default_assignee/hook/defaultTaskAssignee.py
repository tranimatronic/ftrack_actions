import os
import logging

import ftrack_api

import os
import sys
import traceback
import getpass
#import yaml
#import json

'''
This action checks any update, and if a new task is created 
and noone is assigned, will assign default user if one is 
specified for that task type in the DEFAULT_USERS dict below.

DEFAULT_USERS ideally should be stored in a YAML/JSON file on a 
per-project basis. Hard coded here for testing
'''


DEFAULT_USERS={'44dbfca2-4164-11df-9218-0019bb4983d8' : ("Generic", None),
    '44dc3636-4164-11df-9218-0019bb4983d8' : ("Animation","trevor@theend.ws"),
    '44dc53c8-4164-11df-9218-0019bb4983d8':("Modeling",None),
    '44dc6ffc-4164-11df-9218-0019bb4983d8':("Previz",None),
    '44dc8cd0-4164-11df-9218-0019bb4983d8':("Lookdev",None),
    '44dcea86-4164-11df-9218-0019bb4983d8':("FX",None),
    '44dd08fe-4164-11df-9218-0019bb4983d8':("Lighting",None),
    '44dd23b6-4164-11df-9218-0019bb4983d8':("Compositing",None),
    '44dd3ed2-4164-11df-9218-0019bb4983d8':("Tracking",'Lemmy'),
    '44dd5868-4164-11df-9218-0019bb4983d8':("Rigging",None),
    '66d145f0-13c6-11e3-abf2-f23c91dfaa16':("Character",None),
    '66d1aedc-13c6-11e3-abf2-f23c91dfaa16':("Prop",None),
    '66d1daba-13c6-11e3-abf2-f23c91dfaa16':("Environment",None),
    '66d2038c-13c6-11e3-abf2-f23c91dfaa16':("Matte Painting",None),
    '7ecbf522-0760-11e4-ba66-04011030cf01':("Paint and Cleanup",None),
    '8009813a-62c1-11e5-9931-42010af0e994':("Feature",None),
    '9d246122-62c1-11e5-879c-42010af0e994':("Bug","trevor@theend.ws"),
    'a5998562-62c1-11e5-a7f9-42010af0e994':("Research","trevor@theend.ws"),
    'ad617412-62c1-11e5-847e-42010af0e994':("Improvement",None),
    'ae1e2480-f24e-11e2-bd1f-f23c91dfaa16':("Deliverable",None),
    'b628a004-ad7d-11e1-896c-f23c91df1211':("Production",None),
    'b70924ba-62c1-11e5-a5c9-42010af0e994':("Documentation",None),
    'be32d268-62c1-11e5-9931-42010af0e994':("Refactor",None),
    'c3b16a60-62c1-11e5-879c-42010af0e994':("Test","trevor@theend.ws"),
    'c3bcfdb4-ad7d-11e1-a444-f23c91df1211':("Rotoscoping",None),
    'cc46c4c6-13d2-11e3-8915-f23c91dfaa16':("Editing",None)
}


class DefaultTaskAssignee(object):
    identifier = 'default.task.assignee'
    label = 'Set Default Assignee'
    description = 'Set Default Assignee for task'

    def __init__(self, session):
        '''
        Capture supplied session object & set up 
        logging formatting
        '''
        super(DefaultTaskAssignee, self).__init__()
        self.logger = logging.getLogger(__name__ + '.' + self.__class__.__name__)
        self.session = session
        
    def update_event_callback(self, event):
        '''
        This is the callback function called by update 
        event subscription
        '''
        for entity in event['data'].get('entities', []):
            # If this event was NOT Added Task, return
            if not entity['action']=='add':
                self.logger.info("ACTION NOT ADD %s"%entity['action'])
                return
            if not entity['entityType']=='task':
                self.logger.info("EVENT NOT TASK %s"%entity['entityType'])
                return 

            #if we get here the event is a task added
            #self.logger.info("TASK ID %s"%str(entity['changes']['id']['new']))
        
            task_id=entity['changes']['id']['new']
            task_object = self.session.query("Task where id=%s"%task_id).first()
            task_type = entity['changes']['typeid']['new']

            #If task is not assigned, assign to default user
            if not 'assignments' in task_object or not len(task_object['assignments']):
                # if we have a default user specified 
                if task_type in DEFAULT_USERS:
                    task_name, username =DEFAULT_USERS[task_type]
                    self.logger.info("assigning %s to ID %s"%(task_name, username))
                    if username:
                        #query user
                        user_object = self.session.query("User where username is '%s'"%username).first()
                        try:
                            assert user_object is not None
                            # Create a new Appointment of type assignment.
                            self.session.create('Appointment', {'context': task_object, 'resource': user_object,'type': 'assignment'})
                        except Exception,e:
                            self.logger.warning('Unable to assign user : "%s"'%str(e))
                            self.session.reset()

        # Finally, commit the new assignment
        self.session.commit()
        return 

    def discover(self, event):
        '''
        called by discover event to return information 
        about this plugin to connect UI
        '''
        logging.warning("DISCOVER: %s"%str(event))
        return {
            'items': [{
                'label': self.label,
                'description': self.description,
                'actionIdentifier': self.identifier
            }]
        }
 
    def register(self):
        '''
        Register action. Subscribe to event hub topics 
        and direct to specified function
        '''
        #DISCOVER subscription. Called on startup - shows this plugin in connect UI
        self.session.event_hub.subscribe(
            'topic=ftrack.action.discover and source.user.username={0}'.format(
                self.session.api_user
            ),
            self.discover
        )

        #on upodate cakk update_event_callback
        self.session.event_hub.subscribe('topic=ftrack.update', self.update_event_callback)
        

# NOTE: OTHER external processes are calling this register() function passing
# a FTrackCore.api.registry.Registry object as first argument. If this is the 
# case, we do not wish to attempt any changes
def register(*args, **kw):
    '''
    Register plugin. Called when used as an plugin.
    '''
    # Validate that args[0] is an instance of ftrack_api.Session. If not,
    # assume that register is being called from an old or incompatible API and
    # return without doing anything.
    if not isinstance(args[0], ftrack_api.session.Session):
        logging.warning("args[0] is of type %s NOT session. Ignoring"%str(args[0]))
        return
    
    action_handler = DefaultTaskAssignee(args[0])
    action_handler.register()


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
	
    # using ftrack.connect application, session login information is 
    # pre-stored into the environment from the config .json file
	# We do not need to re-supply this data at this point - an
    # empty session constructior is all that is needed
    session = ftrack_api.Session(auto_connect_event_hub=True)
    register(session)
	
    # Wait for events
    session.event_hub.wait()
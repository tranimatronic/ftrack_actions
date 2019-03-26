import sys
import os
import argparse
import logging


import ftrack_api
logger= logging.basicConfig(level=logging.INFO)

#This ideally should be picked up in a YAML file in 
#a configuration. Hard coded here for testing
DEFAULT_USERS={'tracking':"Lemmy",
	"animation":"trevor@theend.we",
	}

'''
def main():
    logger = logging.getLogger(os.path.dirname(__file__))
    logger.setLevel(logging.INFO)
    logging.basicConfig()

    parser = argparse.ArgumentParser('status update')
    parser.add_argument('-s', '--src-category', type=str, help='unique name for category to change from', required=True)
    parser.add_argument('-d', '--dst-category', type=str, help='unique name for category to change to', required=True)

    args = parser.parse_args()

    session = ftrack_api.Session()

    def get_category(category_name):
        try:
            return session.query(
                'NoteCategory where name is "{0}"'.format(category_name)).one()
        except ftrack_api.exception.NoResultFoundError as e:
            logger.error(
                'Could not find note category with name "{0}"'.format(category_name ))
            sys.exit(4)

    dst_category = get_category(args.dst_category)
    notes_to_update = session.query('Note where category_id is "{0}"'.format(get_category(args.src_category).get('id')))

    for note in notes_to_update:
        logger.info('updating note "{0}"'.format( note.get('id') ))

        note['category_id'] = dst_category.get('id')

        try:
            session.commit()

        except ftrack_api.exception.ServerError as e:
            logger.warning('Failed updating note "{0}" : '.format( note.get('id'), e))
            # ran into this a few times for some internal notes, should not happen in your case
            session.reset()
'''

def auto_assign(argDict):
	'''
	<dict> argDict contains user and task_type values
	
	for all tasks of type assign specified user 
	(assign all modelling tasks to modeling lead 
	who will in turn sub assign to artists)
	
	'''
	try:
		#find user
		user_object = argDict['session'].query("User where username is '%s'"%argDict['user']).first()
		assert user_object is not None
		
		# Create a new Appointment of type assignment.
		argDict['session'].create('Appointment', {'context': argDict[''], 'resource': user_object,'type': 'assignment'})

		# Finally, persist the new assignment
		argDict['session'].commit()
		
	except Exception,e:
		logger.info('ERROR : "%s"'%str(e))
		argDict['session'].reset()
	return
		
def register(session, **kw):
    '''Register plugin.'''

    # Validate that session is an instance of ftrack_api.Session. If not,
    # assume that register is being called from an incompatible API
    # and return without doing anything.
    if not isinstance(session, ftrack_api.Session):
        # Exit to avoid registering this plugin again.
        return

    #action = MyCustomAction(session)
    #action.register()
	
if __name__ == '__main__':
	# parse any argumnets
	parser = argparse.ArgumentParser('auto assign')
	parser.add_argument('-tt', '--task-type', type=str, dest='task_type', help='type of task', default=None, required=False)
	parser.add_argument('-tid', '--task-id', type=str, dest='task_id', help='task id', required=True)
	parser.add_argument('-usr', '--user', type=str, dest='user', action='store', default=None, help='user to assign task to', required=False)

	args = parser.parse_args()
	session = ftrack_api.Session()
	# retrieve task object
	args['task_object'] = session.query("Task where id is '%s'"%argDict['task_id']).first()
	# ensure type is populated
	if not args['task_type']:
		args['task_type']=args['tasl_object']['type']
		
	# if task type has no default users, bail out	
	if not args['task_type'] in DEFAULT_USERS:
		logger.info('Unknown task id "%s"'%args['task_id'])
	else:
		if not args['user']:
			# no specified user, 
			args['user']=DEFAULT_USERS[args['task_type']]
				
		try:
			args['session']= session
			auto_assign(args)
		except Exception,e:
			print e
	session.close()

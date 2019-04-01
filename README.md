README

default_assignee
- monitor updates for new task
- if task created and no assignee, search default assignees dict for task type
- if task type has a default assignee, assign that user to the new task

ensure_approve_note
- monitor updates for Task Updates.
- if task is being set to 'approved' status, show UI asking for note
- add the note to the selected task
- if invalid value, re-show the UI

location_plugin
- creates 2 alternative locations D:\\ and F:\\
- monitors for new components added to any location
- if component version is published, try to pull component to each available location
- notify user in webUI which locations component now available in using 'location Name': 'True' or 'False'

permission_check
- Select Task, launch this action.
- If we are ADMIN a "Admin Clicked Action" note is added to the selected task
- If not show UI warning insufficient privelidges
- To run as non-admin for testing uncomment line 40

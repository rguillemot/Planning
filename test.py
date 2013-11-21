#!/usr/bin/python

import datetime
import lxml.builder as lb
from lxml import etree

def TimeToDate(time):
	today = datetime.datetime.today()
	today = today + datetime.timedelta(days=time)
	return today.strftime("%Y,%m,%d")

def xml_Chantier(chantier_id,start_time,xml_tasks):
	xml_project = lb.E.project( \
  			name="chantier "+str(chantier_id), \
			startdate=TimeToDate(start_time) \
  			)
	for t in xml_tasks:
		xml_project.append(t)
	return xml_project
 
def xml_Task(task_type,start_time,duration,percentage,xml_task_elements):
	xml_childtasks = lb.E.childtasks()
	for te in xml_task_elements:
		xml_childtasks.append(te)
	return lb.E.task( \
			lb.E.name(task_type), \
			lb.E.est(TimeToDate(start_time)), \
			lb.E.duration(str(duration*8)), \
			lb.E.percentcompleted(str(percentage)), \
			lb.E.predecessortasks(),
			xml_childtasks)


def xml_TaskElement(worker,when):
	return lb.E.task( \
			lb.E.name(worker), \
			lb.E.est(TimeToDate(when)), \
			lb.E.duration(str(8)), \
			lb.E.percentcompleted(str(100)), \
			lb.E.predecessortasks(), \
			lb.E.childtasks())

xml = xml_Chantier(0,0, \
			[ xml_Task( task_type, 0, 1, 100, \
				[xml_TaskElement( \
					name, \
					0) \
				for name in ['Richard','Julien']] \
			  
			) for task_type in ['Ouverture','Refection']]\
)

xml = lb.E.projects(xml)

et = etree.ElementTree(xml)
et.write("data.xml",pretty_print=True)

#!/usr/bin/python

import csv
from collections import OrderedDict
from itertools import count
import lxml.builder as lb
from lxml import etree
import datetime


def load_table(filename):
	table = []
	with open(filename, 'rb') as csvfile:
		spamreader = csv.reader(csvfile, delimiter=';')
		for row in spamreader:
			table += [row]
	return table


def build_worker_list(team_table):
	worker_list = []
	for row in team_table:
		for elt in row:
			if elt <> '':
				worker_list += [elt]
	return worker_list

def build_type_list(skills_table,line_nb):
	type_list = []
	for elt in skills_table[line_nb]:
		if elt <> '' and elt not in type_list:
			type_list += [elt]
	return type_list


def build_team_dico(team_table):
	team_dico = {}
	for row in team_table:
		team = []
		for elt in row:
			if elt <> '':
				team += [elt]
		for elt in team:
			team_dico.update({elt : team})

	return team_dico

def build_skills_dico(skills_table, chantier_type, ouverture_type,task_type, team_dico):
	nb_rows = len(skills_table)
	nb_cols = len(skills_table[0])

	skills_dico = {}

	for i in range(2,nb_cols):
		if skills_table[0][i] == '':
			selected_chantier_type = chantier_type
		else:
			selected_chantier_type = [skills_table[0][i]]
		if skills_table[1][i] == '':
			selected_ouverture_type = ouverture_type
		else:
			selected_ouverture_type = [skills_table[1][i]]
		if skills_table[2][i] == '':
			selected_task_type = task_type
		else:
			selected_task_type = [skills_table[2][i]]
		for c in selected_chantier_type:
			for o in selected_ouverture_type:
				for t in selected_task_type:
					selected_worker = []
					for w in range(3,nb_rows):
						if skills_table[w][i] <> '':
							if  skills_table[w][i] == 'S':
								if skills_table[w][1] not in selected_worker:
									selected_worker += [skills_table[w][1]]
							else:
								if team_dico[skills_table[w][1]] not in selected_worker:
									selected_worker += [team_dico[skills_table[w][1]]]
					skills_dico.update({ (c,o,t) : selected_worker})
	return skills_dico 
						
def build_skillscount_dico(skills_table):
	nb_rows = len(skills_table)
	nb_cols = len(skills_table[0])

	skillscount_dico = {}
	for row_idx in range(3,nb_rows):
		skillscount = 0
		for col_idx in range(2,nb_cols):
			if skills_table[row_idx][col_idx]<>'':
				skillscount += 1
		skillscount_dico.update ({skills_table[row_idx][1] : skillscount })
	
	return skillscount_dico


def sort_skills_dico(skills_dico, skillscount_dico):
	def local_skillscount(worker):
		if isinstance(worker,list):
			return sum([local_skillscount(w) for w in worker])/len(worker)
		else:
			return skillscount_dico[worker]

	for elt in skills_dico:
		workers = skills_dico[elt]
		skills_dico.update({elt : sorted(workers, key = lambda w: local_skillscount(w))})
	return skills_dico

def build_productivity_dico(chantier_type, ouverture_type, task_type, productivity_table):
	productivity_dico = {}
	for row in productivity_table:
		selected_chantier = chantier_type
		if row[0] <> '':
			selected_ouverture = [row[0]]
		else:
			selected_ouverture = ouverture_type
		if row[1] <> '':
			selected_task = [row[1]]
		else:
			selected_task = task_type
		for c in selected_chantier:
			for o in selected_ouverture:
				for t in selected_task:
		 			productivity_dico.update({(c,o,t) : float(row[2])})
	return productivity_dico

def load_data():
	skills_table = load_table('skills.csv')
	productivity_table = load_table('productivity.csv')
	team_table = load_table('team.csv')
	worker_list = build_worker_list(team_table)
	chantier_type = build_type_list(skills_table,0)
	ouverture_type = build_type_list(skills_table,1)
	task_type = build_type_list(skills_table,2)

	team_dico = build_team_dico(team_table)
	skills_dico = build_skills_dico(skills_table,chantier_type, ouverture_type, task_type, team_dico)
	skillscount_dico = build_skillscount_dico(skills_table)
	skills_dico = sort_skills_dico(skills_dico,skillscount_dico)
	productivity_dico = build_productivity_dico(chantier_type,ouverture_type,task_type,productivity_table)

	return worker_list,chantier_type,ouverture_type, task_type, skills_dico, productivity_dico

def TimeToDate(time):
	today = datetime.datetime.today()
	today = today + datetime.timedelta(days=time)
	return today.strftime("%Y,%m,%d")

global taskidcount
taskidcount=0 

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
	global taskidcount
	taskidcount = taskidcount + 1
	return lb.E.task( \
			lb.E.name(task_type), \
			lb.E.est(TimeToDate(start_time)), \
			lb.E.duration(str(duration*8)), \
			lb.E.percentcompleted(str(percentage)), \
			lb.E.predecessortasks(),
			xml_childtasks,
			id=str(taskidcount))


def xml_TaskElement(worker,when,duration):
	global taskidcount
	taskidcount = taskidcount + 1
	return lb.E.task( \
			lb.E.name(worker), \
			lb.E.est(TimeToDate(when)), \
			lb.E.duration(str(duration*8)), \
			lb.E.percentcompleted(str(100)), \
			lb.E.predecessortasks(), \
			lb.E.childtasks(),
			id=str(taskidcount))

class TaskElement:
	def __init__(self,task,worker,time,amount_of_time):
		self.task = task
		self.who = worker
		self.when = time
		self.amount_of_time = amount_of_time

	def display(self):
		return xml_TaskElement(self.who,self.when,self.amount_of_time)
	
class Task:
	def __init__(self,chantier,task_type):
		self.chantier = chantier
		self.task_type = task_type
		self.status = 0
		self.task_elts = []

	def done(self):
		return self.status == 1

	def start_time(self):
		return self.task_elts[0].when

	def end_time(self):
		return self.task_elts[-1].when

	def duration(self):
		return self.end_time()-self.start_time() + 1

	def work(self,productivity,worker,time,max_amount_of_time):
		if self.status < 1:
			if productivity*max_amount_of_time < 1:
				self.status += productivity*max_amount_of_time
				amount_of_time = 1 
			else:
				self.status = 1
				amount_of_time = 1/productivity	

			task_elt = TaskElement(self,worker,time,amount_of_time)
			self.task_elts.append(task_elt)
			return task_elt 
		else:
			print worker
			print self.task_type
			return None 

	def display(self):
		if self.task_elts:
			return xml_Task(self.task_type, self.start_time(), self.duration(),self.status*100,[te.display() for te in self.task_elts])
 		else:
			return None

class Chantier:
	_ids = count(0)

	def __init__(self,chantier_type,ouverture_type,task_types,start_time):
		self.id = self._ids.next()
		self.chantier_type = chantier_type
		self.ouverture_type = ouverture_type
		self.start_time = start_time
		self.tasks = OrderedDict(zip(task_types, [Task(self,t) for t in task_types]))

	def done(self):
		return self.current_task() == None
	
	def current_task(self):
		for tid in self.tasks:
			if not self.tasks[tid].done():
				return self.tasks[tid]
		return None

	def end_time(self):
		if self.done():
			return self.end_time()
		else:
			return None

	def work(self,task_type, productivity, worker, time, max_amount_of_time):
		return self.tasks[task_type].work(productivity,worker,time, max_amount_of_time)

	def request(self):
		if not self.done():
			return (self.chantier_type,self.ouverture_type,self.current_task().task_type)
		else:
			return None
	def display(self):
		return xml_Chantier(self.chantier_type + " " + self.ouverture_type + " " + str(self.id), self.start_time,filter(None,[t.display() for t in [self.tasks[tid] for tid in self.tasks]]))	

class Worker:
	def __init__(self,name):
		self.name = name
		self.status = [1]
		self.task_elements = [[]]

	def current_time(self):
		return len(self.status)-1

	def available(self):
		if self.status[-1] > 0:
			return True
		else:
			return False
	
	def work(self,chantier,request,productivity,max_amount_of_time):
		task_elt = chantier.work(request[2],productivity,self.name,self.current_time(),max_amount_of_time)
		self.status[-1]-=task_elt.amount_of_time
		self.task_elements[-1]+=[task_elt]

	def endofday(self):
		self.status += [1]
		self.task_elements += [[]]

class WorkerPool:
	def __init__(self,worker_list,skills_dico,productivity_dico):
		self.workers = dict(zip(worker_list,[Worker(name) for name in worker_list]))
		self.skills_dico = skills_dico
		self.productivity_dico = productivity_dico

	def work(self,chantier,max_amount_of_time):
		r = c.request()
		if r == None:
			return False
		skilled_workers = skills_dico[r]
		productivity = productivity_dico[r]
		for ws in skilled_workers:
			if isinstance(ws,list):
				all_available = True
				for w in ws:
					all_available &= self.workers[w].available()
				if all_available:
					for w in ws:
						self.workers[w].work(chantier,r,productivity,max_amount_of_time/len(ws))
					return True
				else:
					return False
			else:
				if(self.workers[ws].available()):
					self.workers[ws].work(chantier,r,productivity,max_amount_of_time)
					return True
	
		return False

worker_list,chantier_types, ouverture_types, task_types, skills_dico, productivity_dico = load_data()

chantier_type = 'BRT'
ouverture_type = 'PC'
c = Chantier(chantier_type, ouverture_type, task_types, 0)
pool = WorkerPool(worker_list,skills_dico,productivity_dico)

count = 10 
while True:
	ret = pool.work(c,1)
	count = count + 1
	if not ret or count == 2:
		break
	
xml_chantier = c.display()
xml = lb.E.projects(xml_chantier)
et = etree.ElementTree(xml)
et.write("data.xml",pretty_print=True)

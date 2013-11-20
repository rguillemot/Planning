#!/usr/bin/python

import csv
from collections import OrderedDict
from itertools import count

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

class TaskElement:
	def __init__(self,task,worker,time,amount_of_time):
		self.task = task
		self.who = worker
		self.when = time
		self.amount_of_time = amount_of_time

	def display(self):
		print '\t{} did it at {}.'.format(self.who,self.when)

	def display_for_worker (self):
		print '\t{} did {} at {} int the chantier {} during {}'.format(self.who,self.task.task_type,self.when,self.task.chantier.id,self.amount_of_time)

class Task:
	def __init__(self,chantier,task_type):
		self.chantier = chantier
		self.task_type = task_type
		self.status = 0
		self.task_elts = [[]]

	def done(self):
		return self.status == 1

	def end_time(self):
		return self.when[-1]

	def work(self,productivity,worker,time):
		if isinstance(worker,list):
			for w in worker:
				self.work(productivity/(len(worker)),w,time)
		else:
			if self.status < 1:
				if productivity < 1:
					self.status += productivity
					amount_of_time = productivity
				else:
					self.status = 1
					amount_of_time = 1	

				task_elt = TaskElement(self,worker,time,amount_of_time)
				self.task_elts[-1] += [task_elt]
			else:
				task_elt = None 
			return task_elt

	def display(self):
		print '{} status : {}'.format(self.task_type, self.status)
		for d in self.task_elts:
			for task_elt in d:
				task_elt.display()


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

	def work(self,task_type, productivity, worker, time):
		print(productivity)
		return self.tasks[task_type].work(productivity,worker,time)

	def request(self):
		if not self.done():
			return (self.chantier_type,self.ouverture_type,self.current_task().task_type)
		else:
			return None
	def display(self):
		print(self.chantier_type)
		print(self.ouverture_type)
		print 'start at {}'.format(self.start_time)
		for t in self.tasks:
			self.tasks[t].display()

class Worker:
	def __init__(self,name):
		self.name = name
		self.status = [1]
		self.task_elements = [[]]
		self.current_time = 0

	def available(self):
		if self.status[self.current_time] > 0:
			return True
		else:
			return False
	
	def work(self,chantier,request,productivity):
		task_elt = chantier.work(request[2],productivity,self.name,self.current_time)
		self.task_elements[-1]+=[task_elt]


	def endofday(self):
		self.status += [1]
		self.task_elements += [[]]
		self.current_time += 1

	def display(self):
		for day in range(0,len(self.task_elements)):
			print 'Day : {}'.format(day)
			for task_elt in self.task_elements[day]:
				task_elt.display_for_worker()	

class WorkerPool:
	def __init__(self,worker_list,skills_dico,productivity_dico):
		self.workers = dict(zip(worker_list,[Worker(name) for name in worker_list]))
		self.skills_dico = skills_dico
		self.productivity_dico = productivity_dico

	def work(self,chantier):
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
						self.workers[w].work(chantier,r,productivity)
				return True
			else:
				if(self.workers[ws].available()):
					self.workers[ws].work(chantier,r,productivity)
					return True
	
		return False

	def display(self):
		for w in self.workers:
			self.workers[w].display()
worker_list,chantier_types, ouverture_types, task_types, skills_dico, productivity_dico = load_data()

chantier_type = 'BRT'
ouverture_type = 'PC'
c = Chantier(chantier_type, ouverture_type, task_types, 0)
pool = WorkerPool(worker_list,skills_dico,productivity_dico)

while True:
	ret = pool.work(c)
	if not ret:
		break

c.display()
pool.display()

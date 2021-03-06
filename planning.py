#!/usr/bin/python
# -*- coding: iso-8859-1 -*-

#
# Auteur : Richard Guillemot
# Date de création : Mardi 19 Novembre 2013

# Cette application génère automatiquement des planning sous forme de digrame de Gantt.
# Elle utilise en entrée:
# _ une liste de projets
# _ une liste d'ouvrier constitués en Equipe (équipe)
# _ une table de compétences associées à chaque ouvrier 
# _ une table de productivité associé à chaque tâche (le nombre de fois qu'un ouvrier peut réalisé une tâche en une journée)

# A partir de toutes ces informations le programme génère un planning.
# Il alloue les tâche nécessaires a chaque chantier aux ouvriers disponibles.
# La priorité est simplement donnée au projet les plus anciens et les ouvrier les moins compétents sont alloués en premier.
#

import csv
import math
from collections import OrderedDict
from itertools import count
import lxml.builder as lb
from lxml import etree
import datetime

#-----------------------------------------------------------------------------------------------
#Fonctions Utilitaires
#-----------------------------------------------------------------------------------------------

#
#Utilitaire qui charge un fichier csv sous forme de table python
#
def load_table(filename):
	table = []
	with open(filename, 'rb') as csvfile:
		spamreader = csv.reader(csvfile, delimiter=';')
		for row in spamreader:
			table += [row]
	return table
#
#Crée la liste des ouvriers à partie de la table des équipes
#
def build_worker_list(team_table):
	worker_list = []
	for row in team_table:
		for elt in row:
			if elt <> '':
				worker_list += [elt]
	return worker_list

#
#Crée la liste des types de chantiers/ouvertures à partir de la table des compétences 
#r
def build_type_list(skills_table,line_nb):
	type_list = []
	for elt in skills_table[line_nb]:
		if elt <> '' and elt not in type_list:
			type_list += [elt]
	return type_list
#
#Crée le dictionnaire des équipes
#

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
#
#Crée le dictionnaire des compétences à partir de la table
#

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
#
#Compte de nombre de compétences de chaques ouvrier et sauvegarde dans un dictionnaire
#						
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
#
#Tri les ouvriers dans le dictionnaire par nombre de compétence ascendante
#
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

#
#Construit le dictionnaire de productivité à partir de la table
#
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
#
#Charge l'ensemble des données nécessaire
#
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

#
#Utilitaire qui génère des date à partir de la date d'aujourd'hui (nécessaire pour la génération de l'XML)
#

def TimeToDate(time):
	today = datetime.datetime.today()
	today = today + datetime.timedelta(days=time)
	return today.strftime("%Y,%m,%d")

#
#Compteur de tâches (nécessaire pour la génération de l'XML) 
#

global taskidcount
taskidcount=0 

#
#Utilitaire de génération XML associé à chaque objet
#
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

def xml_TaskElementForWorker(chantier_task, when,duration):
	global taskidcount
	taskidcount = taskidcount + 1
	return lb.E.task( \
			lb.E.name(chantier_task), \
			lb.E.est(TimeToDate(when)), \
			lb.E.duration(str(duration*8)), \
			lb.E.percentcompleted(str(100)), \
			lb.E.predecessortasks(), \
			lb.E.childtasks(),
			id=str(taskidcount))

def xml_Worker(name, xml_task_elements):
	xml_project = lb.E.project( \
  		name=str(name), \
		startdate=TimeToDate(0) \
  		)
	for t in xml_task_elements:
		xml_project.append(t)
	return xml_project

def xml_WorkerPool(xml_workers):
	xml_workerpool = lb.E.projects()

	for w in xml_workers:
		xml_workerpool.append(w)
	return xml_workerpool

def xml_ChantierPool(xml_chantiers):
	xml_chantierpool = lb.E.projetcs()

	for c in xml_chantiers:
		xml_chantierpool.append(c)
	return xml_chantierpool

#-----------------------------------------------------------------------------------------------
#Classes qui modélisent l'application
#-----------------------------------------------------------------------------------------------


#
#Task Element : Fraction d'une tâche effectué par un ouvrier un jour j 
#"

class TaskElement:
	def __init__(self,task,worker,time,amount_of_time):
		self.task = task
		self.who = worker
		self.when = time
		self.amount_of_time = amount_of_time

	def display(self):
		return xml_TaskElement(self.who,self.when,self.amount_of_time)

	def display_for_worker(self):
		return xml_TaskElementForWorker('chantier ' + self.task.chantier.chantier_type + ' ' + self.task.chantier.ouverture_type + ' ' + str(self.task.chantier.id) + ' ' + self.task.task_type, self.when, self.amount_of_time)

#
#Task : Tache composant un chantier associé a un type de compétence
#

class Task:
	def __init__(self,chantier,task_type):
		self.chantier = chantier
		self.task_type = task_type
		self.status = 0
		self.task_elts = []

	def done(self):
		return math.fabs(self.status-1) < 1e-6

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
				amount_of_time = max_amount_of_time 
			else:
				self.status = 1
				amount_of_time = 1/productivity
			task_elt = TaskElement(self,worker,time,amount_of_time)
			self.task_elts.append(task_elt)
			return task_elt 
		else:
			return None 

	def display(self):
		if self.task_elts:
			return xml_Task(self.task_type, self.start_time(), self.duration(),self.status*100,[te.display() for te in self.task_elts])
 		else:
			return None		
#
#Chantier : Ensemble de tâches
#

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
		return xml_Chantier(self.chantier_type + " " + self.ouverture_type + " " + str(self.id), self.start_time,[f for f in [t.display() for t in [self.tasks[tid] for tid in self.tasks]] if f != None])	

#
#Worker : Ouvrier
#

class Worker:
	def __init__(self,name):
		self.name = name
		self.status = [1]
		self.task_elements = []

	def current_time(self):
		return len(self.status)-1

	def available(self):
		if math.fabs(self.status[-1]) > 1e-6:
			return True
		else:
			return False
	
	def work(self,chantier,request,productivity,max_amount_of_time):
		task_elt = chantier.work(request[2],productivity,self.name,self.current_time(),max_amount_of_time)
		if task_elt <> None:
			self.status[-1]-=task_elt.amount_of_time
			self.task_elements+=[task_elt]

	def endofday(self):
		self.status += [1]

	def display(self):
		return xml_Worker(self.name,[te.display_for_worker() for te in self.task_elements]) 

#
#Worker Pool : Ensemble des ouvriers
#

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
						self.workers[w].work(chantier,r,productivity,float(max_amount_of_time)/len(ws))
					return c.done() 
			else:
				if(self.workers[ws].available()):
					self.workers[ws].work(chantier,r,productivity,max_amount_of_time)
				return c.done()
		return c.done()
	def display(self):
		return xml_WorkerPool([self.workers[wid].display() for wid in self.workers])

#
#Chantier Pool : Ensemble des chantiers
#
	
class ChantierPool:
	def __init__(self,chantier_list):
		self.chantier_list = chantier_list

	def display(self):
		return xml_ChantierPool([c.display() for c in self.chantier_list])


#-----------------------------------------------------------------------------------------------
#Code de demonstration - Boucle principale
#-----------------------------------------------------------------------------------------------


#
#Chargement des données statiques à partir des fichiers de configurations et créations des 
#dictionnaires
#

worker_list,chantier_types, ouverture_types, task_types, skills_dico, productivity_dico = load_data()

#
#Création d'un chantier de démonstration
#

chantier_type = 'BRT'
ouverture_type = 'PC'
c = Chantier(chantier_type, ouverture_type, task_types, 0)

#
#Création du pool de chantiers et d'ouvirers
#

cpool = ChantierPool([c])
wpool = WorkerPool(worker_list,skills_dico,productivity_dico)

#
#Boucle de traitement des tâches
#

count = 0 
while True:
	ret = wpool.work(c,1)
	count = count + 1
	if ret or count > 100:
		break
#
#Export des fichiers xml corresponant au planning
#
	
xml_chantier = cpool.display()
et = etree.ElementTree(xml_chantier)

#
#Le Planning par chantier
#

et.write("datachantier.xml",pretty_print=True)
xml_worker = wpool.display()

#
#Le planning par ouvrier
#
et = etree.ElementTree(xml_worker)
et.write("dataworker.xml",pretty_print=True)

#!usr/bin/env python
#coding=utf-8

__author__ = 'ye.cai'

import model_tur
import os
import os.path
from os.path import sep
import time
import queue
import random
import socket
from STP import *
import random

import datetime
import pytz
import dateutil

TUR_Address		=	'127.0.0.1'
PCC_Address		=	'127.0.0.1'
EMS_Address		=	'127.0.0.1'

MAX_MINUTES = 23*60 + 59
AIStatusCode = 'AIStatusCode'
TurbineAPStsAD = 'TurbineAPStsAD'
TZ = pytz.timezone(model_tur.TZ_name)

stpTool = STP_DT()

#################test
sc_list = [0, 20, 21,22, 23]

##################################
##################################
##################################
def getCurMinutesAndSecs(time_secs): #获取指定时间在一天中的分钟数和秒数
	dt = datetime.datetime.fromtimestamp(time_secs, TZ)
	local = dt.timetuple()
	#print("get minute ", local)
	minutes = local.tm_hour * 60 + local.tm_min
	secs = local.tm_sec
	return (minutes, secs)
	
def getSimTime(time_secs):
	diff = time_secs - globalInfo.runStartTime
	simTime = globalInfo.simStartTime + diff%(globalInfo.simEndTime - globalInfo.simStartTime)
	return simTime
	
def getCurSimDate(time_secs): #当前机器日期转换成模拟数据源中的日期
	simTime = getSimTime(time_secs)
	dt = datetime.datetime.fromtimestamp(simTime, TZ)
	local = dt.timetuple()
	#print("get date ", local)
	simDate = time.strftime('%Y%m%d', local) #like return '20140520'
	#print(simDate)
	return simDate
	
def getPointNo(data_name, data_name_list):
	for idx, name in enumerate(data_name_list):
		if name == data_name:
			return idx
	return -1
	
def fitData(data1, data2, period, total, rd):
	if data1 == None and data2 != None:
		return data2
	elif data1 != None and data2 == None:
		return data1
	elif data1 == None and data2 == None:
		return 0
	else:
		return data1 + (data2 - data1) * period / total + rd
	
##################################
##################################
##################################
#一个厂家下可能有多个风场，即多个pcc
class oemInfo(object):
	curRunDataRowCnt = 60 #static, 一个数据文本数据最多保存60行数据
	scValidPeriod = 10    #seconds
	def __init__(self):
		self.oem_name = ''
		self.wtgIdxList = {}   #pcc名称和风机名称索引号队列的映射
		self.wtgCnt = 0
		self.wtgSocketList = {}  #ppc下每台风机的socket
		self.pccSock = {}
		self.bufferList = {}
		
		self.CurDataFiles = [] #data files
		self.oemAiPointSet = set([])
		self.oemPiPointSet = set([])
		
		#用于差值，保存当前分钟的数据和下一分钟的数据
		self.wtgCurData = [] #like [[(……),(……)]
		self.wtgNextData = []
	
		self.curRunData = []
		self.nextDataFromFiles = []
		
		self.curScData = []
		self.aiDataCol = []
		self.piDataCol = []
		self.aiDataNo = []       #ai对应列的点号
		self.piDataNo = []       #点号
		self.AIStatusCodeIdx = 0 #sc的点号
		self.runSc = []
		
	def getOemMinuteDataCol(self, col_name_list): #contains 'occur_time'
		del self.aiDataCol[:]
		del self.aiDataNo[:]
		del self.piDataCol[:]
		del self.piDataNo[:]
		
		for index, col_name in enumerate(col_name_list):
			if col_name == AIStatusCode:
				self.AIStatusCodeIdx = getPointNo(col_name, model_tur.modelCfg[self.oem_name]['AI_name_list']) #sc point number
			if col_name in self.oemAiPointSet:
				self.aiDataCol.append(index)
				self.aiDataNo.append(getPointNo(col_name, model_tur.modelCfg[self.oem_name]['AI_name_list']))
			elif col_name in self.oemPiPointSet:
				self.piDataCol.append(index)
				self.piDataNo.append(getPointNo(col_name, model_tur.modelCfg[self.oem_name]['PI_name_list']))
	
	def clearAndRemoveAllFileHandler(self):
		for data_file in self.CurDataFiles: ##!!!
			if data_file != None:
				data_file.close()
		del self.CurDataFiles[:]
		
	def openSimDateFiles(self, simDate): #打开指定日期的所有风机文件 date = '20140101'
		self.clearAndRemoveAllFileHandler()
		for pcc_name in self.wtgIdxList.keys():
			for wtg_idx in self.wtgIdxList[pcc_name]:
				wtg_name = globalInfo.allWtgList[wtg_idx]
				wtg_data_dir = model_tur.simDataRootDir + sep + self.oem_name + sep + pcc_name + sep + wtg_name + sep +simDate
				print(wtg_data_dir)
				if os.path.exists(wtg_data_dir) == False:
					self.CurDataFiles.append(None)
				
				data_file_name = wtg_data_dir + sep + model_tur.simDataMin + sep + model_tur.simDataMin + '_' + simDate + '.csv'; #minute_20140101.csv
				
				if os.path.exists(data_file_name):
					self.CurDataFiles.append(open(data_file_name, 'r'))
				else:
					self.CurDataFiles.append(None)
				
	def openReadScFiles(self, time_secs):
		if len(self.curScData) == 0:
			self.curScData = [0] * self.wtgCnt
			self.runSc = [model_tur.modelCfg[self.oem_name]['defaultSc']] * self.wtgCnt #默认
			
		file_idx = 0
		for pcc_name in self.wtgIdxList:
			for wtg_idx in self.wtgIdxList[pcc_name]:
				wtg_name = globalInfo.allWtgList[wtg_idx]
				wtg_data_dir = model_tur.simDataRootDir + sep + self.oem_name + sep + pcc_name + sep + wtg_name + sep +globalInfo.curSimDate
				if os.path.exists(wtg_data_dir) == False:
					continue
				sc_file_name = wtg_data_dir + sep + wtg_name + '_sc.csv'
				if os.path.exists(sc_file_name) :
					with open(sc_file_name, 'r') as sc_file:
						self.readCurSc(sc_file, file_idx, time_secs)
				file_idx += 1
	
	def reInitFiles(self, time_secs):
		dt = datetime.datetime.fromtimestamp(time_secs, TZ)
		#date_str = time.strftime('%Y%m%d', time.localtime(time_secs))
		#new_time_secs = int(time.mktime(time.strptime(date_str, '%Y%m%d'))) + globalInfo.oneDaySecs
		new_time_secs = time_secs + globalInfo.oneDaySecs
		newSimDate = getCurSimDate(new_time_secs)
		print('--------open a new file----', newSimDate, dt)
		self.openSimDateFiles(newSimDate)
		self.firstReadLines() #update time_secs????????
		
	def readlines(self, data_file, que, time_secs):
		if data_file != None:
			while que.qsize() < oemInfo.curRunDataRowCnt:
				line = data_file.readline()
				if line:
					que.put_nowait(line)
				else: #need to open the new files
					return False
		return True
			
	def readCurSc(self, sc_file, file_idx, time_secs):
		if sc_file != None:
			lines = []
			simTime = getSimTime(time_secs)
			first_sc_info = None
			first_sc_time = 0
			for line in sc_file: 
				colsInfo = line.strip('\n').split(',')
				if len(colsInfo) != 5:
					continue
				dateTime = colsInfo[1].strip('"')
				sc_time_secs = time.mktime(time.strptime(dateTime, '%m/%d/%Y %I:%M:%S %p'))
				#print('sc time: ', dateTime, sc_time_secs)
				if simTime > sc_time_secs:
					first_sc_info = colsInfo
					first_sc_time = sc_time_secs
				else:
					sc = int(colsInfo[2].strip('"'))
					state = int(colsInfo[4].strip('"'))
					lines.append((sc_time_secs, state, sc)) #(time_secs, state, code)
					
			if first_sc_info != None: #处理当前时间的上一条sc
				sc = int(first_sc_info[2].strip('"'))
				state = int(first_sc_info[4].strip('"'))
				lines[0:0] = [(first_sc_time, state, sc)]
				first_sc_info = None
			self.curScData[file_idx] = lines
		
	def firstReadLines(self): #读取文件中最前面的记录
		is_get_col = False
		for dataFile in self.CurDataFiles:
			title_line = dataFile.readline() #first line of data files
			if is_get_col == False:
				self.getOemMinuteDataCol(title_line.split(',')) #each oem get once
				is_get_col = True
				
		if len(self.curRunData) == 0:#create queues
			for idx in range(self.wtgCnt):
				self.curRunData.append(queue.Queue())        #60 like [[...], [...], [...]]
				self.nextDataFromFiles.append(queue.Queue()) #like [[...], [...], [...]]
				
		for file_idx, data_file in enumerate(self.CurDataFiles):
			self.readlines(data_file, self.curRunData[file_idx], 0)
			self.readlines(data_file, self.nextDataFromFiles[file_idx], 0)
				
	def initLines(self, time_secs): #except title
		is_get_col = False
		for dataFile in self.CurDataFiles:
			title_line = dataFile.readline() #first line of data files
			if is_get_col == False:
				self.getOemMinuteDataCol(title_line.split(',')) #each oem get once
				is_get_col = True
					
		cur_line = 0
		minutes = getCurMinutesAndSecs(time_secs)[0]
		while cur_line < minutes:#skip
			cur_line += 1
			for data_file in self.CurDataFiles:  #假定每个文件的一分钟数据都是全的
				data_file.readline()  
		
		if len(self.curRunData) == 0:#create queues
			for idx in range(self.wtgCnt):
				self.curRunData.append(queue.Queue())        #60 like [[...], [...], [...]]
				self.nextDataFromFiles.append(queue.Queue()) #like [[...], [...], [...]]
		
		for file_idx, data_file in enumerate(self.CurDataFiles):
			if self.readlines(data_file, self.curRunData[file_idx], time_secs) == False: #重新开始
				self.reInitFiles(time_secs)
				return
			if self.readlines(data_file, self.nextDataFromFiles[file_idx], time_secs) == False:
				self.reInitFiles(time_secs)
				return
		
	def getCurLineData(self, time_secs):
		if len(self.curRunData) == 0:
			return
		if self.curRunData[0].empty(): #队列中的内容已取完
			self.updateLines(time_secs)
		
		result = []
		for q in self.curRunData:         
			if q.empty() == False:
				curLine = q.get_nowait()
				#print(self.oem_name + '----' + curLine)  #test
				result.append(curLine)
			else:
				result.append(None)
		return result #[..., ..., ...]
		
	def getDataLine(self, line_data):
		if line_data == None:
			return []
			
		nodes = [] 
		for idx, item in enumerate(line_data.split(',')):
			try:
				if idx != 0:
					nodes.append(float(item))
				else:
					nodes.append(item)
			except:
				nodes.append(0)
			#if item == 'N/A':
			#	nodes.append(0)
			#elif idx != 0:
			#	nodes.append(float(item))
			#else:
			#	nodes.append(item) #occur time
		return nodes
		
	def initWtgCurData(self, time_secs):#系统初始化时执行一次
		result = self.getCurLineData(time_secs)
		for data in result:
			if data:
				self.wtgCurData.append(self.getDataLine(data))
			else:
				self.wtgCurdata.append(None)
				
		result = self.getCurLineData(time_secs)
		for data in result:
			if data:
				self.wtgNextData.append(self.getDataLine(data))
			else:
				self.wtgNextdata.append(None)
				
	def updateWtgCurData(self, time_secs): #一分钟更新一次
		for data_idx, data in enumerate(self.wtgNextData):
			self.wtgCurData[data_idx] = data
		result = self.getCurLineData(time_secs)
		for data_idx, data in enumerate(result):
			if data:
				self.wtgNextData[data_idx] = self.getDataLine(data)
			else:
				self.wtgNextdata[data_idx] = None
				
	def getWtgData(self, period, time_secs):
		wtg_no = 0
		for pcc_name in self.bufferList:
			for wtg_idx in range(len(self.bufferList[pcc_name])):
				cur_data = self.wtgCurData[wtg_no]
				next_data = self.wtgNextData[wtg_no]
				sc_data = self.curScData[wtg_no]
				if len(cur_data) == 0 or len(next_data) == 0:
					print("incorrectly get data: ", len(cur_data), len(next_data))
					wtg_no += 1
					continue
					
				data = []
				ai_start_index = model_tur.modelCfg[self.oem_name]['AI_start_index']
				#print('wtg data---', self.oem_name, cur_data[0])
				for idx, data_idx in enumerate(self.aiDataCol): #get AI
					point_idx = self.aiDataNo[idx]
					#if model_tur.modelCfg[self.oem_name]['AI_name_list'][idx] == 'WindSpeed': #test
					#	print('wind oem ', self.oem_name, model_tur.modelCfg[self.oem_name]['AI2DI'][idx])
					if model_tur.modelCfg[self.oem_name]['AI2DI'][point_idx] == '0':
						data1 = cur_data[data_idx]
						data2 = next_data[data_idx]
						ai_data = fitData(data1, data2, period, globalInfo.times_in_minute, random.uniform(-0.01 * data1, 0.01 * data1))
					else:
						ai_data = cur_data[data_idx] ###????
					data.append([point_idx + ai_start_index, ai_data, 0x1]) #[点号，值，0x1]
				self.bufferList[pcc_name][wtg_idx] = stpTool.Encode(STP_DT.AI,data)
						
				data = []
				pi_start_index = model_tur.modelCfg[self.oem_name]['PI_start_index']
				for idx, data_idx in enumerate(self.piDataCol): #get PI  
					if cur_data[data_idx] > next_data[data_idx]:
						pi_data = cur_data[data_idx]
					elif cur_data[data_idx] < next_data[data_idx]:
						pi_data = next_data[data_idx]
					else:
						continue
					#pi_data = fitData(cur_data[data_idx], next_data[data_idx], period, globalInfo.times_in_minute, 0)
					data.append([self.piDataNo[idx] + pi_start_index, pi_data, 0x0]) #change from 0x1 to 0x0
				if data:
					self.bufferList[pcc_name][wtg_idx] += stpTool.Encode(STP_DT.PI, data)
				
				if sc_data and len(sc_data) > 0:
					simTime = getSimTime(time_secs)
					first_sc_info = sc_data[0] #get sc
					#if not first_sc_info:
						#print('fisrt sc info invalid: ', sc_data)
						#continue
					sc_time_secs = first_sc_info[0]
					err = sc_time_secs - simTime
					if err < self.scValidPeriod: #获取最接近当前时间的sc
						#print('sc_info: ', self.oem_name, first_sc_info) #test
						state = first_sc_info[1]
						code = first_sc_info[2]
						print(globalInfo.curSimDate, sc_time_secs, self.oem_name, state, code, self.AIStatusCodeIdx + ai_start_index)
						del self.curScData[wtg_no][0]  #删除已获取的第一条sc
						if code >= 0: #非负的sc是有效的
							data = [[self.AIStatusCodeIdx + ai_start_index, code, 0x1]] #sc作为AI处理
							self.bufferList[pcc_name][wtg_idx] += stpTool.Encode(STP_DT.AI, data)
						if state >= 0:
							data = [[model_tur.modelCfg[self.oem_name][TurbineAPStsAD], state, 0x1]] #风机状态作为DI
							self.bufferList[pcc_name][wtg_idx] += stpTool.Encode(STP_DT.DI, data)
						self.runSc[wtg_no] = (state, code, sc_time_secs) #update running sc
				wtg_no += 1
	
	def sendOutData(self):
		for pcc_name in self.bufferList: #send wtg buffer
			cur_port = model_tur.modelCfg[self.oem_name][pcc_name]['ems_init_port']
			#first, should send pcc buffer????
			cur_port += 1
			for wtg_idx, buffer in enumerate(self.bufferList[pcc_name]):
				if buffer:
					self.wtgSocketList[pcc_name][wtg_idx].sendto(buffer, (EMS_Address, cur_port))
				cur_port += 1
			
	def updateSc(self):
		wtg_no = 0
		ai_start_index = model_tur.modelCfg[self.oem_name]['AI_start_index']
		for pcc_name in self.bufferList.keys():
			for wtg_idx in range(len(self.bufferList[pcc_name])):
				state = self.runSc[wtg_no][0]
				code = self.runSc[wtg_no][1]
				print('update sc', globalInfo.curSimDate, self.runSc[wtg_no][2], self.oem_name, state, code, self.AIStatusCodeIdx + ai_start_index)
				data = [[self.AIStatusCodeIdx + ai_start_index, code, 0x1]] #sc作为AI处理
				self.bufferList[pcc_name][wtg_idx] = stpTool.Encode(STP_DT.AI, data)
				if state >= 0:
					data = [[model_tur.modelCfg[self.oem_name][TurbineAPStsAD], state, 0x1]] #风机状态作为DI
					self.bufferList[pcc_name][wtg_idx] += stpTool.Encode(STP_DT.DI, data)
				wtg_no += 1
	
	def updateLines(self, time_secs):   #curRunData is empty, then 从文件中获取一定量的内容保存在内存里
		print('update cur data: ', self.curRunData[0].qsize(), self.nextDataFromFiles[0].qsize())
		for file_idx, q in enumerate(self.nextDataFromFiles):
			while q.empty() == False:
				self.curRunData[file_idx].put_nowait(q.get_nowait())
				
		for file_idx, data_file in enumerate(self.CurDataFiles):
			if self.readlines(data_file, self.nextDataFromFiles[file_idx], time_secs) == False:
				self.reInitFiles(time_secs)
				return

##################################
##################################
##################################
class globalInfo(object): #获取所有全局信息
	oneDaySecs = 24*60*60
	oneMinuteSecs = 60
	sleep_step = 3
	times_in_minute = int(oneMinuteSecs // sleep_step) #一分钟运算的次数,左闭右开
	curSimDate = '0'
	allWtgList = []   #所有风机名称的队列
	
	simStartTime =   int(time.mktime(time.strptime(model_tur.simDataStartDate, '%Y%m%d'))) #时间戳
	simEndTime =     int(time.mktime(time.strptime(model_tur.simDataEndDate, '%Y%m%d')))
	runStartTime =   int(time.mktime(time.strptime(model_tur.runDataStartDate, '%Y%m%d')))
	
	def __init__(self):
		self.oemInfoList = {}
		self.getOemWtg()
				
	def getOemWtg(self):  #构建厂家风机信息
		if os.path.exists(model_tur.simDataRootDir) == False:
			print("the root dir ", model_tur.simDataRootDir, "does not exist")
			return
			
		oem_list = os.listdir(model_tur.simDataRootDir)
		for oem in oem_list:
			dir = model_tur.simDataRootDir + sep + oem
			
			print('oem dir: ', dir) #test
			
			pcc_list = os.listdir(dir)
			
			oem_info = oemInfo()
			oem_info.oem_name = oem
			oem_info.oemAiPointSet = set(model_tur.modelCfg[oem]['AI_name_list'])
			oem_info.oemPiPointSet = set(model_tur.modelCfg[oem]['PI_name_list'])
			for pcc_name in pcc_list:
				pcc_dir = dir + sep + pcc_name
				wtg_list = os.listdir(pcc_dir)
				if len(wtg_list) == 0:
					continue
			
				base_idx = len(globalInfo.allWtgList)
				globalInfo.allWtgList += wtg_list
				wtgCnt = len(wtg_list)
				oem_info.wtgCnt += wtgCnt
				
				oem_info.wtgIdxList[pcc_name] = list(range(base_idx, len(globalInfo.allWtgList))) #索引号
				socket_list = []
				print(oem, pcc_name)
				tur_base_port = model_tur.modelCfg[oem][pcc_name]['wtg_start_port']
				for idx in range(wtgCnt):
					sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
					sock.bind((TUR_Address, tur_base_port + idx))
					sock.setblocking(0)
					socket_list.append(sock)
				oem_info.wtgSocketList[pcc_name] = socket_list
				oem_info.bufferList[pcc_name] = [0] * wtgCnt
				
				pcc_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
				pcc_sock.bind((PCC_Address, model_tur.modelCfg[oem][pcc_name]['pcc_port']))
				pcc_sock.setblocking(0)
				oem_info.pccSock[pcc_name] = pcc_sock
			self.oemInfoList[oem] = oem_info
		
	def clearAndRemoveAllFileHandler(self):
		for oem_name in self.oemInfoList.keys():
			self.oemInfoList[oem_name].clearAndRemoveAllFileHandler()
			
	def openSimDateFiles(self, simDate): #打开指定日期的所有风机文件 date = '20140101'
		print('open sim date file: ', simDate)
		self.clearAndRemoveAllFileHandler()
		for oem_name in self.oemInfoList.keys():
			self.oemInfoList[oem_name].openSimDateFiles(simDate)
	
	def initSimFilesData(self, time_secs): #init after open
		for oem_name in self.oemInfoList.keys():
			self.oemInfoList[oem_name].initLines(time_secs)
			print('first init all files ', oem_name, self.oemInfoList[oem_name].curRunData[0].qsize(), self.oemInfoList[oem_name].nextDataFromFiles[0].qsize())
			self.oemInfoList[oem_name].initWtgCurData(time_secs)
			print('init all files ', oem_name, self.oemInfoList[oem_name].curRunData[0].qsize(), self.oemInfoList[oem_name].nextDataFromFiles[0].qsize())
				
	def getSimCurData(self, time_secs, period):
		simDate = getCurSimDate(time_secs)
		if simDate != globalInfo.curSimDate: #如果当前日期发生变化，则读取新的sc文件
			globalInfo.curSimDate = simDate
			for oem_name in self.oemInfoList.keys():
				self.oemInfoList[oem_name].openReadScFiles(time_secs)
				
		for oem_name in self.oemInfoList.keys():
			self.oemInfoList[oem_name].getWtgData(period, time_secs) #获取风机遥测数据
			
	def sendOutData(self):#向scada发送报文
		for oem_name in self.oemInfoList.keys():
			self.oemInfoList[oem_name].sendOutData()
				
	def updateCurData(self, time_secs): #一分钟执行一次
		for oem_name in self.oemInfoList.keys():
			self.oemInfoList[oem_name].updateWtgCurData(time_secs)
			
	def updateSc(self):
		for oem_name in self.oemInfoList.keys():
			self.oemInfoList[oem_name].updateSc()
		self.sendOutData()
			
if __name__ == '__main__':
	gInfo = globalInfo()
	curTime = time.time()
	gInfo.openSimDateFiles(getCurSimDate(curTime))
	gInfo.initSimFilesData(curTime)
	period = 0
	while True:
		#print("before get")
		gInfo.getSimCurData(time.time(), period)
		gInfo.sendOutData()#SEND !!!!!
		#print("after get")
		time.sleep(globalInfo.sleep_step)
		period = (period + 1) % globalInfo.times_in_minute
		if period == 0:
			gInfo.updateCurData(time.time())
			#gInfo.updateSc()

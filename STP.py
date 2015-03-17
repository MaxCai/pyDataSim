import datetime
import struct
import time


class STP_DT:
	SC = 0
	AI = 1
	DI = 2
	PI = 3
	AO = 4
	DO = 5
	HEAD = 6
	STP_HEAD = '<Bh2B'
	AI_FMT = '<hfB'
	DI_FMT = '<h2B'
	PI_FMT = '<hfiB'
	SC_FMT = '<hi7B'
	AO_FMT = '<hfB'
	DO_FMT = '<h2B'
	
	def __init__(self):
		pass
		
	def Encode(self,type,data):
		buff=bytearray()
		if not data:
			return data
		buff = struct.pack(STP_DT.STP_HEAD,0x68,len(data),type,0x68)
		if type == STP_DT.SC:
			for value in data:
				#print(value[0],value[1],value[2])
				buff +=struct.pack(STP_DT.SC_FMT,value[0],value[1],*value[2])
		elif type == STP_DT.AI:
			for value in data:
				#print(value[0],value[1],value[2])
				buff +=struct.pack(STP_DT.AI_FMT,value[0],value[1],value[2])
		elif type == STP_DT.DI:
			for value in data:
				buff +=struct.pack(STP_DT.DI_FMT,value[0],value[1],value[2])
		elif type == STP_DT.PI:
			for value in data:
				buff +=struct.pack(STP_DT.PI_FMT,value[0],value[1],0,value[2])
		return buff
		
	def Decode(self,type,data):
		if type == STP_DT.HEAD:
			size = struct.calcsize(STP_DT.STP_HEAD)
			header1,num,type,header2 = struct.unpack(STP_DT.STP_HEAD,data[0:size])
			return header1,num,type,size
		elif type == STP_DT.AO:
			size = struct.calcsize(STP_DT.AO_FMT)
			addr,value,quality = struct.unpack(STP_DT.AO_FMT,data[0:size])
			#print("AO:",(addr,value,quality))
		elif type == STP_DT.DO:
			size = struct.calcsize(STP_DT.DO_FMT)
			addr,value,quality = struct.unpack(STP_DT.DO_FMT,data[0:size])
			#print("DO:",(addr,value,quality))
		return addr,value
		
if __name__ == "__main__":
	xx = STP_DT()
	print(xx.Encode(STP_DT.AI,[[1,4.2,0x1],[2,3.5,0x1]]))
	dt =datetime.datetime.now()
	print(dt)
	#now =(dt.year,dt.month,dt.day,dt.hour,dt.minute,dt.second,dt.microsecond)
	msec = dt.second*1000+int(dt.microsecond/1000)
	print(msec)
	now = (msec&0xFF,(msec>>8)&0xFF,dt.minute,dt.hour,dt.day,dt.month,dt.year-2000)
	#now = (100,100,100,100,100,100,100)
	print(xx.Encode(STP_DT.SC,[[1,108104,now],[1,208104,now]]))


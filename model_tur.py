#coding=utf-8

simDataRootDir   = 'D:\\solar\\shanghai'   #模拟数据源的路径
simDataMin = 'minute'

scSuffix = '_sc.csv'

simDataStartDate = '20150101'     #模拟数据的起始日期
simDataEndDate   = '20150103'     #模拟数据的结束日期

runDataStartDate = '20150101'     #程序开始运行的时间设定  
TZ_name = 'Asia/Shanghai'       #时区信息


modelCfg ={
	"invSN":{ #20
		'defaultSc':(0, -1),
		"YNXT":
		{
			"wtg_start_port" : 5020, #pcc下风机的起始端口
			"pcc_port":4997,         #pcc自己的端口号
			"ems_init_port" : 9021
		},
		
		"AI_name_list":[
			"CurBranch1",
			"CurBranch10",
			"CurBranch2",
			"CurBranch3",
			"CurBranch4",
			"CurBranch5",
			"CurBranch6",
			"CurBranch7",
			"CurBranch8",
			"CurBranch9",
			"InsResis",
			"TempCab",
			"TempFan",
			"VolPV",
			"APProdDay",
			"APProdYear",
			"ActPowOut",
			"ActPowPh1",
			"ActPowPh2",
			"ActPowPh3",
			"CosPhiPh1",
			"CosPhiPh2",
			"CosPhiPh3",
			"CurDCIn",
			"CurPh1",
			"CurPh2",
			"CurPh3",
			"Freq",
			"InvtEffi",
			"OffTimeH",
			"OffTimeM",
			"OffTimeS",
			"OnHourDay",
			"OnTimeH",
			"OnTimeM",
			"OnTimeS",
			"PVPowIn",
			"ReActPowOut",
			"RePowPh1",
			"RePowPh2",
			"RePowPh3",
			"TempIGBT1MAX",
			"TempIGBT2MAX",
			"VolDCIn",
			"VolPV",
			"VolPh12",
			"VolPh23",
			"VolPh31"
			],
		"AI2DI" : '000000000000000000000000000000000000000000000000',
		"AI_start_index":2,
		
		"PI_name_list":[
			"APProduction"
		],
		"PI_start_index":2,
		
		"TurbineAPStsAD": 1, #风机状态
		"DI_name_list":[],
		"DI_start_index":1,
	},
	"met":{ #20
		'defaultSc':(0, -1),
		"YNXT":
		{
			"wtg_start_port" : 5066, #pcc下风机的起始端口
			"pcc_port":4980,         #pcc自己的端口号
			"ems_init_port" : 9072
		},
		"AI_name_list":[
			"Humidity",
			"Pressure",
			"RadDirect",
			"RadScatter",
			"Radiation",
			"Temperature",
			"WindDirection",
			"WindSpeed"
			],
		"AI2DI" : '00000000',  
		"AI_start_index":2,
		
		"PI_name_list":[
			"APProduction"
		],
		"PI_start_index":2,
		
		"TurbineAPStsAD": 1, #风机状态
		"DI_name_list":[],
		"DI_start_index":1,
	}
}

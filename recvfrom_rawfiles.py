import socket
import time
from threading import Thread
import struct
import os.path
import addr_constants
import functions as fc
from scipy import signal
import numpy as np
class recvfrom_rawdatafiles(Thread):
    def __init__(self):
        Thread.__init__(self)
        self.timenow=fc.timestr()
        self.ffname="data"+self.timenow
        current_path = os.path.dirname(os.path.abspath(__file__))
        self.data_path = os.path.join(current_path, self.ffname)

        self.data = b''
        #0
        self.DRStemp = [[],[],[],[],[],[],[],[]]
        self.DRSdata = [[],[],[],[]]
        self.DRSrawdata = [b'',b'',b'',b'']
        self.linear_para = []
        #1
        self.tottemp = []
        self.totdata = []
        self.totrawdata = b''
        #2
        self.SiPMtemp = []
        self.SiPMdata = []
        self.SiPMrawdata = b''
        #3#拾振器
        self.vibtemp = []
        self.vibdata = []
        self.vibrawdata = b''
        #4#倾角仪
        self.inctemp = []
        self.incdata = []
        self.incrawdata = b''
        #5#pmt控制1
        self.pmt1temp = [[0],[0]*32,[]]
        self.pmt1data = []
        self.pmt1rawdata = b''
        #A#pmt控制2
        self.pmt2temp = [[0],[0]*32,[]]
        self.pmt2data = []
        self.pmt2rawdata = b''
        #D#FPGA核心温度
        self.temptemp = 0
        self.tempdata = []
        self.temprawdata = b''

    def run(self):
        file_paths = fc.select_files()
        for i_file, file_path in enumerate(file_paths):
            print(f"正在读取文件 {i_file+1}/{len(file_paths)}: {os.path.basename(file_path)}")
            with open(file_path, 'rb') as f:
                self.data += f.read()

        ps = fc.process(len(self.data))#建立进度条
        #ps.start()

        dataflag = -1#当前接收的数据类型，-1为未检测到类型
        phasecount = 0#当前数据包接收到哪个阶段了
        cellcount = 0#当前DRS数据包已接收多少字节纯数据了
        end = 0#为1则结束，丢弃当前数据包并重置各参考值，data左移1重新找包头
        fin = 0#为1则本包读取完毕，执行原始数据暂存，data左移p
        #在未读取任何包的情况下发现包头，data左移至新包头
        p = 0#当前处理位置#####
        minlength = 4
        chipid = 0
           
        #数据处理
        while (len(self.data) - p > 0):
            restlen = len(self.data)-p
            if dataflag==-1:
                if restlen>=4:
                    head_value=self.data[p:p+4]
                    if head_value==b'\xff\xff\xff\xf0':
                        dataflag=0
                        minlength=4
                    elif head_value==b'\xff\xff\xff\xf1':
                        dataflag=1
                        minlength=2
                    elif head_value==b'\xff\xff\xff\xf2':
                        dataflag=2
                        minlength=4
                    elif head_value==b'\xff\xff\xff\xf3':
                        dataflag=3
                        minlength=4
                    elif head_value==b'\xff\xff\xff\xf4':
                        dataflag=4
                        minlength=4
                    elif head_value==b'\xff\xff\xff\xf5':
                        dataflag=5 
                        minlength=8
                    elif head_value==b'\xff\xff\xff\xfa':
                        dataflag=10
                        minlength=8
                    elif head_value==b'\xff\xff\xff\xfd':
                        dataflag=13
                        minlength=4
                    else:
                        p+=1
                    if dataflag>=0:
                        self.data=self.data[p:]
                        p=4
                        phasecount = 1
                else:
                    p+=1

            elif dataflag==3 or dataflag==4:
                tempdataflag = -1
                if restlen>=4:
                    head_value=self.data[p:p+4]
                    #以下为3/4型数据接收同时进行的包头检测
                    if head_value==b'\xff\xff\xff\xf0':
                        tempdataflag=0
                        minlength=4
                    elif head_value==b'\xff\xff\xff\xf1':
                        tempdataflag=1
                        minlength=2
                    elif head_value==b'\xff\xff\xff\xf2':
                        tempdataflag=2
                        minlength=4
                    elif head_value==b'\xff\xff\xff\xf3':
                        tempdataflag=3
                        minlength=4
                    elif head_value==b'\xff\xff\xff\xf4':
                        tempdataflag=4
                        minlength=4
                    elif head_value==b'\xff\xff\xff\xf5':
                        tempdataflag=5 
                        minlength=8
                    elif head_value==b'\xff\xff\xff\xfA':
                        tempdataflag=10
                        minlength=8
                    elif head_value==b'\xff\xff\xff\xfD':
                        tempdataflag=13
                        minlength=4
                #若检测到新包头
                if tempdataflag>=0:
                    end=1
                    fin=1
                #未检测到新包头
                else:
                    if dataflag==3:
                        self.vibtemp.append(self.data[p])
                    elif dataflag==4:
                        self.inctemp.append(self.data[p])
                    p+=1

            elif dataflag==0: 
                if phasecount==1:
                    chipid = self.data[p+3]#////////////////////
                    if self.data[p:p+3]==b'\x00\x00\x00' and chipid<4:
                        p+=4
                        minlength=8
                        phasecount+=1
                    else:
                        end=1
                elif phasecount==2:
                    for i in range(8):
                        self.DRStemp[i].append(self.data[p+2:p+8])#?????????trig_ID
                    p+=8
                    minlength=8
                    phasecount+=1
                elif phasecount==3:
                    for i in range(8):
                        self.DRStemp[i].append(self.data[p:p+8])#////////drs1_dtap_coarse_time
                    p+=8
                    minlength=8
                    phasecount+=1
                elif phasecount==4:
                    for i in range(8):
                        self.DRStemp[i].append(int.from_bytes(self.data[p:p+8], byteorder="big", signed=False))#coarse_cnt int.from_bytes(, byteorder="big", signed=False)
                    p+=8
                    minlength=16
                    phasecount+=1
                elif phasecount==5:
                    for i in range(8):
                        self.DRStemp[i].append(self.data[p+2*i:p+2*i+2])#data_decode_cut
                    p+=16
                    minlength=16
                    phasecount+=1
                elif phasecount==6:
                    for i in range(8):
                        self.DRStemp[i].append(int.from_bytes(self.data[p+2*i:p+2*i+2], byteorder="big", signed=False))#drs_stop_posi
                    p+=16
                    minlength=16
                    phasecount+=1
                elif phasecount==7:
                    for i in range(8):
                        self.DRStemp[i].append(self.data[p+1+2*i])#i_channel
                    p+=16
                    minlength=16
                    phasecount+=1
                    cellcount=0
                elif phasecount==8:
                    for i in range(8):
                        self.DRStemp[i].append(int.from_bytes(self.data[p+2*i:p+2*i+2], byteorder="big", signed=False))#chn_id
                    p+=16
                    minlength=16
                    cellcount+=1
                    if cellcount==1024:
                        phasecount+=1
                        minlength=16
                elif phasecount==9:
                    if(self.data[p:p+16]==b'\xc3\xc3\xc3\xc3\xc3\xc3\xc3\xc3\xc3\xc3\xc3\xc3\xc3\xc3\xc3\xc3'):
                        p+=16
                        end=1
                        fin=1
                    else:
                        end=1

            elif dataflag==1:
                if phasecount==1:
                    self.tottemp.append(self.data[p+1])
                    p+=2
                    minlength=10
                    phasecount+=1
                elif phasecount==2:
                    self.tottemp.append(int.from_bytes(self.data[p:p+10], byteorder="big", signed=False))
                    p+=10
                    end=1
                    fin=1

            elif dataflag==2:
                if phasecount==1:
                    chn_flag = self.data[p+3]%16
                    if self.data[p:p+3]==b'\xff\xff\xff' and self.data[p+3]>15*16:#chn_flag的范围是？？？？
                        self.SiPMtemp.append(chn_flag)
                        p+=4
                        minlength=8
                        phasecount+=1
                    else:
                        end=1
                elif phasecount==2:
                    self.SiPMtemp.append(int.from_bytes(self.data[p:p+8], byteorder="big", signed=False))
                    p+=8
                    minlength=4
                    phasecount+=1
                elif phasecount==3:
                    value = int.from_bytes(self.data[p+2:p+4], byteorder="big", signed=False)
                    if self.data[p:p+2]==b'\xff\xff' and value//1024==63:
                        self.SiPMtemp.append(value%512)
                        p+=4
                        minlength=8
                        phasecount+=1
                    else:
                        end=1
                elif phasecount==4:
                    self.SiPMtemp.append(int.from_bytes(self.data[p:p+8], byteorder="big", signed=False))
                    p+=8
                    minlength=4
                    phasecount+=1
                elif phasecount==5:
                    value = int.from_bytes(self.data[p:p+4], byteorder="big", signed=False)
                    if value<1024:
                        self.SiPMtemp.append(value%512)
                        p+=4
                        end=1
                        fin=1
                    else:
                        end=1                      

            elif dataflag==5:
                if phasecount==1:
                    if self.data[p:p+6]==b'\x68\x65\x6c\x6c\x6f\x3a':
                        self.pmt1temp[0]=int.from_bytes(self.data[p+6:p+8])*20#PWM周期
                        p+=8
                        phasecount+=1
                        minlength=32
                    else:
                        #print(f"pmt1有坏包{ps.length-len(self.data)}")
                        end=1
                elif phasecount==2:
                    for i in range(32):
                        self.pmt1temp[1][i]+=self.data[p+i]*20#PWM_width_MSB
                    p+=32
                    phasecount+=1
                    minlength=64
                elif phasecount==3:
                    for i in range(32):
                        self.pmt1temp[1][i]+=self.data[p+2*i]//16*1.25#PWM_width_LSB
                        self.pmt1temp[2].append(int.from_bytes(self.data[p+i*2:p+i*2+2])%2**12/2**12*3.3*1001)#ADCdata
                    p+=64
                    phasecount+=1
                    minlength=4
                elif phasecount==4:
                    p+=4
                    fin=1
                    end=1

            elif dataflag==10:
                if phasecount==1:
                    if self.data[p:p+6]==b'\x68\x65\x6c\x6c\x6f\x3a':
                        self.pmt2temp[0]=int.from_bytes(self.data[p+6:p+8])*20#PWM周期
                        p+=8
                        phasecount+=1
                        minlength=32
                    else:
                        end=1
                elif phasecount==2:
                    for i in range(32):
                        self.pmt2temp[1][i]+=self.data[p+i]*20#PWM_width_MSB
                    p+=32
                    phasecount+=1
                    minlength=64
                elif phasecount==3:
                    for i in range(32):
                        self.pmt2temp[1][i]+=self.data[p+2*i]//16*1.25#PWM_width_LSB
                        self.pmt2temp[2].append(int.from_bytes(self.data[p+i*2:p+i*2+2])%2**12/2**12*3.3*1001)#ADCdata
                    p+=64
                    phasecount+=1
                    minlength=4
                elif phasecount==4:
                    p+=4
                    fin=1
                    end=1

            elif dataflag==13:
                if phasecount==1:
                    if self.data[p:p+2]==b'\x00\x00':
                        self.temptemp=(int.from_bytes(self.data[p+2:p+4])//16)*503.975/4096-273.15
                        p+=4
                        fin=1
                        end=1
                    else:
                        end=1

            if len(self.data)-p<=0:
                if dataflag==3 or dataflag==4:
                    fin=1
                    end=1
                else:
                    end=1
                                    
            if end==1:
                if fin==1:
                    if dataflag==0:
                        self.DRSdata[chipid].append(self.DRStemp)
                        self.DRSrawdata[chipid] += self.data[0:p]
                    elif dataflag==1:
                        self.totdata.append(self.tottemp)
                        self.totrawdata += self.data[0:p]
                    elif dataflag==2:
                        self.SiPMdata.append(self.SiPMtemp)
                        self.SiPMrawdata += self.data[0:p]
                    elif dataflag==3:
                        self.vibdata.append(self.vibtemp)
                        self.vibrawdata += self.data[0:p]
                    elif dataflag==4:
                        self.incdata.append(self.inctemp)
                        self.incrawdata += self.data[0:p]
                    elif dataflag==5:
                        self.pmt1data.append(self.pmt1temp)
                        self.pmt1rawdata += self.data[0:p]
                    elif dataflag==10:
                        self.pmt2data.append(self.pmt2temp)
                        self.pmt2rawdata += self.data[0:p]
                    elif dataflag==13:
                        self.tempdata.append(self.temptemp)
                        self.temprawdata += self.data[0:p]
                    self.data=self.data[p:]

                else:
                    self.data=self.data[1:]
                self.DRStemp = [[],[],[],[],[],[],[],[]]
                self.tottemp = []
                self.SiPMtemp = []
                self.vibtemp = []
                self.inctemp = []
                self.pmt1temp = [[0],[0]*32,[]]
                self.pmt2temp = [[0],[0]*32,[]]
                self.temptemp = 0
                dataflag = -1
                phasecount = 0
                minlength = 4
                p=0
                end=0
                fin=0

            ps.rest=len(self.data)#更新进度条
            ps.layout()
        #ps.stopflag=True#结束进度条
        print("读取完成")

    def direxists(self):
        if not os.path.exists(self.data_path):
            os.makedirs(self.data_path)

    def save(self):
        #root_path = os.path.dirname(current_path)
        self.direxists()
        for i in range(4):            
            f=open(os.path.join(self.data_path,f"DRS"+self.timenow+".data"),"ab")
            if self.DRSrawdata[i]!=b'':
                f.write(self.DRSrawdata[i])
                self.DRSrawdata[i]=b''
        if self.totrawdata!=b'':
            f=open(os.path.join(self.data_path,"tot"+self.timenow+".data"),"wb")
            f.write(self.totrawdata)
            self.totrawdata=b''
        if self.SiPMrawdata!=b'':
            f=open(os.path.join(self.data_path,"SiPM"+self.timenow+".data"),"wb")
            f.write(self.SiPMrawdata)
            self.SiPMrawdata=b''
        if self.vibrawdata!=b'':
            f=open(os.path.join(self.data_path,"vib"+self.timenow+".data"),"wb")
            f.write(self.vibrawdata)
            self.vibrawdata=b''
        if self.incrawdata!=b'':
            f=open(os.path.join(self.data_path,"inc"+self.timenow+".data"),"wb")
            f.write(self.incrawdata)
            self.incrawdata=b''
        if self.pmt1rawdata!=b'':
            f=open(os.path.join(self.data_path,"pmt1"+self.timenow+".data"),"wb")
            f.write(self.pmt1rawdata)
            self.pmt1rawdata=b''
        if self.pmt2rawdata!=b'':
            f=open(os.path.join(self.data_path,"pmt2"+self.timenow+".data"),"wb")
            f.write(self.pmt2rawdata)
            self.pmt2rawdata=b''
        if self.temprawdata!=b'':
            f=open(os.path.join(self.data_path,"temp"+self.timenow+".data"),"wb")
            f.write(self.temprawdata)
            self.temprawdata=b''
        print(f"已保存于{self.ffname}并释放原始数据缓存")
        return self.timenow

    def conclude(self):
        print('各类包的数量：')
        print(f'DRSchip0-3:{len(self.DRSdata[0])},{len(self.DRSdata[1])},{len(self.DRSdata[2])},{len(self.DRSdata[3])}')
        print(f'tot:{len(self.totdata)}')
        print(f'SiPM:{len(self.SiPMdata)}')
        print(f'vib:{len(self.vibdata)}')
        print(f'inc:{len(self.incdata)}')
        print(f'pmt1:{len(self.pmt1data)}')
        print(f'pmt2:{len(self.pmt2data)}')
        print(f'temp:{len(self.tempdata)}')
        if(self.DRSdata!=[[],[],[],[]]):
            for chipid in range(4):
                if self.DRSdata[chipid]!=[]:
                    mintrigid=self.DRSdata[chipid][0][0][0]
                    print(f"chip{chipid}DRS最小触发号：{int.from_bytes(mintrigid)}")
                else:
                    print(f"chip{chipid}DRS无信号")

    def linearpara_load(self, parafilename="linear_fit_para_31chn.npy"):
        self.linear_para = fc.read_npy(parafilename)

    def graph_dns1chn(self, trigid, n_chn, save_flag=1, deburr_flag=0, filter_flag=1):
        chipid=n_chn//8
        i_chn=n_chn%8
        for j in range(len(self.DRSdata[chipid])):
            if int.from_bytes(self.DRSdata[chipid][j][i_chn][0])==trigid:
                num = j
                break
            if int.from_bytes(self.DRSdata[chipid][j][i_chn][0])>trigid:
                print("trigid not found")
                num=-1
                break
        #rawdata       
        data_1cl=(self.DRSdata[chipid][num][i_chn])[6:]
        fc.Graph_group_data(data_1cl)
        #linearfit
        if(len(self.linear_para)==0):
            print("此文件未选择线性校正参数文件,只能输出原始码值")
        else:
            stopposi=self.DRSdata[chipid][num][i_chn][4]
            timeorder_linear_para=fc.cellorder_to_timeorder(self.linear_para[n_chn], stopposi)#///////////
            fitted_data_1cl=np.array(fc.linear_correct(data_1cl, timeorder_linear_para))
            fc.Graph_group_data(fitted_data_1cl)
            #deburr
            if(deburr_flag==1):
                deburred_data_1cl = fitted_data_1cl#///////////////////////////////////////
                fc.Graph_group_data(deburred_data_1cl)
            else:
                deburred_data_1cl = fitted_data_1cl
            #filter
            if(filter_flag==1):
                filtered_data_1cl = deburred_data_1cl[10:]
                filtered_data_1cl = signal.lfilter(fc.FIR_filter, 1.0, filtered_data_1cl)
            fc.Graph_group_data(filtered_data_1cl)
        if(save_flag==1):
            self.direxists()
            fc.Data_save_csv(data_1cl,file_path_name=os.path.join(self.data_path,f"trigid{trigid}_chn{n_chn}_rawdata.csv"),fmt='%d')
            if(len(self.linear_para)!=0):
                fc.Data_save_csv(fitted_data_1cl,file_path_name=os.path.join(self.data_path,f"trigid{trigid}_chn{n_chn}_fitteddata.csv"))

    def graph_dns32chn(self, num):
        groupj=[-1,-1,-1,-1]
        groupn=0
        for i in range(4):
            for j in range(len(self.DRSdata[i])):
                trigid=int.from_bytes(self.DRSdata[i][j][0][0],'big')
                if trigid==num:
                    groupj[i]=j
                    groupn+=1
                    break
                elif trigid>num:
                    break
        if groupn==0:
            print("此触发号未找到对应事件")
        else:
            if(len(self.linear_para)==0):
                print("此文件未选择线性校正参数文件,只能输出原始码值")
            data_32cls=[]#未校正的数据
            fitted_data_32cls=[]
            for i in range(4):
                if groupj[i]>=0:
                    for j in range(8):
                        data_1cl=(self.DRSdata[i][groupj[i]][j])[6:]
                        data_32cls.append(data_1cl)
                        if(len(self.linear_para)!=0):
                            stopposi=self.DRSdata[i][groupj[i]][j][4]
                            timeorder_linear_para=fc.cellorder_to_timeorder(self.linear_para[i*8+j], stopposi)#/////////
                            fitted_data_32cls.append(fc.linear_correct(data_1cl, timeorder_linear_para))
                else:
                    for j in range(8):
                        fitted_data_32cls.append([0]*1024)
                        data_32cls.append([0]*1024)
            fc.graphs32(data_32cls)
            if(len(self.linear_para)!=0):
                fc.graphs32(fitted_data_32cls)

    def print_pmt1(self, n_group):
            print("PWM 周期")
            print(self.pmt1data[n_group][0])
            print("PWM width/ns")
            print(self.pmt1data[n_group][1])
            print("HV/V")
            print(self.pmt1data[n_group][2])

    def print_tot(self, n_group):
        print(self.totdata[n_group])


if __name__=='__main__':
    recv = recvfrom_rawdatafiles()
    recv.run()
    recv.conclude()
    #recv.save()
    if (1):#读入对应线性校正参数
        if(recv.DRSdata!=[[],[],[],[]]):
            linear_para = fc.read_npy("linear_fit_para_31chn_26.npy")#///////////////////////////linear_fit_para_31chn/////
            for chipid in range(4):
                if recv.DRSdata[chipid]!=[]:
                    mintrigid=recv.DRSdata[chipid][0][0][0]
                    print(f"chip{chipid}最小触发号：{int.from_bytes(mintrigid)}")

    if (0):#找单个波形
        trigid=1961826
        n_chn=10      #0-30
        chipid=n_chn//8
        i_chn=n_chn%8
        for j in range(len(recv.DRSdata[chipid])):
            if int.from_bytes(recv.DRSdata[chipid][j][i_chn][0])==trigid:
                num = j
                break
            if int.from_bytes(recv.DRSdata[chipid][j][i_chn][0])>trigid:
                print("not found")
                num=-1
                break
        data_1cl=(recv.DRSdata[chipid][num][i_chn])[6:]
        stopposi=recv.DRSdata[chipid][num][i_chn][4]
        timeorder_linear_para=fc.cellorder_to_timeorder(linear_para[n_chn], stopposi)#///////////
        fitted_data_1cl=fc.linear_correct(data_1cl, timeorder_linear_para)
        fc.Graph_group_data(fitted_data_1cl)
        if(0):
            fc.Data_save_csv(data_1cl,new_name=f"trigid{trigid}_chn{n_chn}_rawdata.csv",fmt='%d')
            fc.Data_save_csv(fitted_data_1cl,new_name=f"trigid{trigid}_chn{n_chn}_fitteddata.csv")

    if (1):#找单个波形
        trigid=1961826
        n_chn=11        #0-30
        chipid=n_chn//8
        i_chn=n_chn%8
        for j in range(len(recv.DRSdata[chipid])):
            if int.from_bytes(recv.DRSdata[chipid][j][i_chn][0])==trigid:
                num = j
                break
            if int.from_bytes(recv.DRSdata[chipid][j][i_chn][0])>trigid:
                print("not found")
                num=-1
                break       
        data_1cl=(recv.DRSdata[chipid][num][i_chn])[6:]
        stopposi=recv.DRSdata[chipid][num][i_chn][4]
        timeorder_linear_para=fc.cellorder_to_timeorder(linear_para[n_chn], stopposi)#///////////
        fitted_data_1cl=np.array(fc.linear_correct(data_1cl, timeorder_linear_para))
        #
        fitted_data_1cl=fitted_data_1cl[10:]
        fitted_data_1cl = signal.lfilter(fc.FIR_filter, 1.0, fitted_data_1cl)
        fc.Graph_group_data(fitted_data_1cl)
        if(0):
            fc.Data_save_csv(data_1cl,new_name=f"trigid{trigid}_chn{n_chn}_rawdata.csv",fmt='%d')
            fc.Data_save_csv(fitted_data_1cl,new_name=f"trigid{trigid}_chn{n_chn}_fitteddata.csv")

    while (1):#根据触发号找31通道波形
        num = int(input("键入触发号查找，回车以确认，输入负数以结束"))
        groupj=[-1,-1,-1,-1]
        groupn=0
        if num<0:
            break
        for i in range(4):
            for j in range(len(recv.DRSdata[i])):
                trigid=int.from_bytes(recv.DRSdata[i][j][0][0],'big')
                if trigid==num:
                    groupj[i]=j
                    groupn+=1
                    break
                elif trigid>num:
                    break
        if groupn==0:
            print("此触发号未找到对应事件")
        else:
            data_32cls=[]
            data_32cls_not=[]#未校正的数据
            for i in range(4):
                if groupj[i]>=0:
                    for j in range(8):
                        data_1cl=(recv.DRSdata[i][groupj[i]][j])[6:]
                        data_32cls_not.append(data_1cl)
                        stopposi=recv.DRSdata[i][groupj[i]][j][4]
                        timeorder_linear_para=fc.cellorder_to_timeorder(linear_para[i*8+j], stopposi)#/////////
                        data_32cls.append(fc.linear_correct(data_1cl, timeorder_linear_para))
                else:
                    for j in range(8):
                        data_32cls.append([0]*1024)
                        data_32cls_not.append([0]*1024)
            fc.graphs32(data_32cls_not)
            fc.graphs32(data_32cls)

    while (0):
        n = int(input("键入包号查找pmt1，回车以确认，输入负数以结束"))
        if n<0:
            break
        else:
            print("PWM 周期")
            print(recv.pmt1data[n][0])
            print("PWM width/ns")
            print(recv.pmt1data[n][1])
            print("HV/V")
            print(recv.pmt1data[n][2])

    while (0):
        n = int(input("键入包号查找tot，回车以确认，输入负数以结束"))
        if n<0:
            break
        else:
            print(recv.totdata[n])
        
    while (0):
        n = int(input("键入包号查找temp，回车以确认，输入负数以结束"))
        if n<0:
            break
        else:
            print(recv.tempdata[n])


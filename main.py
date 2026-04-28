import functions as fc
from recvfrom_rawfiles import recvfrom_rawdatafiles as rr
from rawfiles_linear_fit import Rawfiles_Linear_fit as lf
import os

if __name__ == '__main__':
    while(1):
        try:
            num1 = int(input("键入1以进行两点线性拟合(直流标定),键入2以读取单组文件并分析,负数以退出："))
            if(num1==1):
                while(1):
                    try:
                        y1=int(input("两点线性拟合：键入文件1对应直流电压值："))
                        y2=int(input("两点线性拟合：键入文件2对应直流电压值："))
                        break
                    except Exception as e:
                        print(e)
                        print("两点线性拟合：//////////////出错，请重新键入//////////////")
                        pass
                lf1=lf(linear_fit_ylist=(y1,y2))
                print("两点线性拟合：请依次选择并读取两个文件")
                lf1.run()
                pass

            elif(num1==2):
                rr1 = rr()
                rr1.run()
                rr1.conclude()
                while(1):
                    try:
                        num2 = int(input("读取单组文件：键入1以重新选择直流标定参数文件,2以不选择/保持不变(未选择过则只会输出原始码值),负数以退出："))
                        if(num2==1):
                            file_path = fc.select_file("npy")
                            rr1.linearpara_load(file_path)
                        elif(num2<0):
                            break
                        #
                        num2 = int(input("读取单组文件：键入1以分析所有通道波形,2以分析单通道波形,负数以退出："))
                        if(num2==1):
                            while(1):
                                try:
                                    trigid=int(input("读取单组文件：全通道：键入触发号以查找,负数以退出："))
                                    if(trigid>=0):
                                        rr1.graph_dns32chn(trigid)
                                    elif(trigid<0):
                                        break
                                except Exception as e:
                                    print(e)
                                    pass
                        elif(num2==2):
                            while(1):
                                try:
                                    trigid=int(input("读取单组文件：单通道：键入触发号以查找,负数以退出："))
                                    if(trigid<0):
                                        break
                                    n_chn=int(input("读取单组文件：单通道：键入通道号(0-30)以查找,负数以退出："))
                                    if(n_chn<0 or n_chn>30):
                                        break
                                    deburr_flag=int(input("读取单组文件：单通道：键入1以追加周期毛刺消除（默认信号和毛刺均为负方向）,2以输入信号和毛刺方向，0以不进行,负数以退出："))
                                    if deburr_flag==2:
                                        signal_direction=int(input("读取单组文件：单通道：若信号方向为正，键入1，否则键入负数："))
                                        bur_direction=int(input("读取单组文件：单通道：若毛刺方向为正，键入1，否则键入负数："))
                                    filter_flag=int(input("读取单组文件：单通道：键入1以追加低通滤波,0以不进行,负数以退出："))
                                    if(filter_flag==1):
                                        freq=int(input("读取单组文件：单通道：键入正数以重新选择滤波截止频率(单位MHZ),0以保持不变(默认140MHZ),负数以退出："))
                                        if(freq>0):
                                            fc.cutoff=freq
                                        elif(freq<0):
                                            break
                                    save_flag=int(input("读取单组文件：单通道：键入1以保存原始码值及拟合结果为.csv文件,0以不保存,负数以退出："))
                                    if(save_flag<0):
                                        break
                                    rr1.graph_dns1chn(trigid=trigid, n_chn=n_chn, save_flag=save_flag, deburr_flag=deburr_flag, signal_direction=signal_direction,bur_direction=bur_direction,filter_flag=filter_flag)
                                except Exception as e:
                                    print(e)
                                    print("读取单组文件：单通道：//////////////出错，请重新键入//////////////")
                                    pass
                        elif(num2<0):
                            break
                    except Exception as e:
                        print(e)
                        print("读取单组文件：//////////////出错，请重新键入//////////////")
                while(1):
                    try:
                        allsave_flag=int(input("读取单组文件：键入1以分类保存所有有效原始数据,0以放弃："))
                        if(allsave_flag==1):
                            rr1.save()
                        break
                    except Exception as e:
                        print(e)
                        pass
            elif(num1<0):
                break
        except Exception as e:
            print(e)
            print("//////////////出错，请重新键入//////////////")
            pass
    print("程序结束")

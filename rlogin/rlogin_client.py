#!/usr/bin/env python3
# -*- coding:utf-8 -*-
# Author:zhang yechong
# Emial:641878711@qq.com

#!/usr/bin/env python3
# -*- coding:utf-8 -*-
# Author:zhang yechong
# Emial:641878711@qq.com

import time
import socket
from socket import error as SocketError
import errno
from functools import wraps
from apps import logger

FLUSHREAD = 0x01
START = 0x08
CAN = 0x18
CR = 0x0D
DC1 = 0x11
DC3 = 0x13
DOT = 0x2E
EOM = 0x19
EOT = 0x04
LF = 0x0A
SUB = 0x1A
# // Unused, for now:
DISCARD = 0x02
RAW = 0x10
COOKED = 0x20
WINDOW = 0x80


class RloginException(Exception):
    """
    Exception raised by failures in SSH2 protocol negotiation or logic errors.
    """

    pass

def open_only(func):

    @wraps(func)
    def _check(self, *args, **kwds):
        if (
            self._closed
        ):
            raise RloginException("Channel is not open")
        return func(self, *args, **kwds)

    return _check


class RloginOptions:
    def __init__(self,clientUsername,serverUsername,serverPassword,terminalType="xterm",terminalSpeed=9600):
        self.clientUsername = clientUsername
        self.serverUsername = serverUsername
        self.serverPassword = serverPassword
        self.terminalType = terminalType
        self.terminalSpeed = terminalSpeed


class RloginClient:
    """
    RloginClient
    """
    def __init__(self, clientUsername,serverUsername,serverPassword,terminalType="xterm",terminalSpeed=9600):
        self.options = RloginOptions(clientUsername=clientUsername,
                                     serverUsername=serverUsername,
                                     serverPassword=serverPassword,
                                     terminalType=terminalType,
                                     terminalSpeed=terminalSpeed)
        self.sock = None
        self._closed = False
        self.status = 0  #连接状态 0 失败 1成功
        self.LocalPort = 1023  #端口范围【514-1023】，否则报错
        self.LocalHost = '0.0.0.0'
        self.debug = False
        self.enter = "\r"

    def _connect_socket(self,host, port):
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.bind((self.LocalHost, self.LocalPort))
        self.sock.connect((host, port))

    def set_debug(self):
        self.debug = not self.debug

    def _debug(self,msg,type=0):
        """

        :param msg:
        :param type: 0-info 1-error 2-warning
        :return:
        """
        if self.debug:
            if type == 0:
                logger.info(msg)
            if type == 1:
                logger.error(msg)
            if type == 2:
                logger.warning(msg)


    def _get_socket(self,host,port):
        while True:
            try:
                self._connect_socket(host,port)
                break
            except SocketError as e:
                self._debug(e, type=2)
                if e.errno == errno.WSAEADDRINUSE:
                    # 端口被占用则端口号减一
                    self.LocalPort -= 1
                    if self.LocalPort==513:
                        self.close()
                        break
                else:
                    break


        self._debug(f"当前本地客户端地址以及端口为：{self.LocalHost}-{self.LocalPort}")


    def send(self,data,flags=0):
        self.sock.send(data.encode('utf-8'),flags)

    def sendall(self,data,flags=0):
        self.sock.sendall(data.encode('utf-8'), flags)

    @open_only
    def connect(self,host,port=513,rows=41,columns=95,pixelsX=760,pixelsY=656):
        """
        连接到目标主机
        :param host:目标主机ip地址
        :param port:目标主机端口默认513
        rows=41,columns=95,pixelsX=760,pixelsY=656 窗口大小
        :return:
        """
        self._get_socket(host,port)
        nul = chr(0)
        self.send(nul)
        self._debug(f"client send {nul}")
        self.send(f"{self.options.clientUsername}{nul}")
        self._debug(f"client send {self.options.clientUsername}{nul}")
        self.send(f"{self.options.serverUsername}{nul}")
        self._debug(f"client send {self.options.serverUsername}{nul}")
        self.send(f"{self.options.terminalType}/{self.options.terminalSpeed}{nul}")
        self._debug(f"client send {self.options.terminalType}/{self.options.terminalSpeed}{nul}")
        self.status = self._on_success()
        if self.status != 1 :
            self.close()
            self._debug(f"rlogin登录失败")
            raise RloginException("rlogin登录失败")
        self.rows = rows
        self.columns = columns
        self.pixelsX = pixelsX
        self.pixelsY = pixelsY
        self._auto_login()


    def recv(self,bufsize=1024*2):
        try:
            #设置成非阻塞
            self.sock.setblocking(False)
            self.sock.settimeout(0.0)
            res_01 = self.sock.recv(bufsize,1)
            self._debug(f"flags=1，收到消息：{res_01}")
            if res_01 == b'\x80':
                self.send_win_size(rows=self.rows,columns=self.columns,pixelsX=self.pixelsX,pixelsY=self.pixelsY)
        except SocketError as e:
            if e.errno != errno.EWOULDBLOCK:
                self._debug(e, type=2)
            pass
        except Exception as e:
            self._debug(f"修改屏幕尺寸错误：{e}", type=1)
            pass

        self.sock.setblocking(True)
        self.sock.settimeout(None)
        res = self.sock.recv(bufsize)


        self._debug(f"收到消息：{res}")

        return res

    def _auto_login(self):
        res = self.recv().decode('utf-8')
        if 'assword' in res:  # 实现密码自动登录
            s = self.options.serverPassword
            for i in s:
                self.send(i)
                time.sleep(0.5)  # 该处设置过短会导致密码自动登录不上
            self.send(self.enter)
            self.recv()
            self._debug(f"rlogin登录成功")


    def send_win_size(self,rows=41,columns=95,pixelsX=760,pixelsY=656,clientEscape='~'):
        #修改屏幕大小
        b = b'\xff' + b'\xff' + 'ss'.encode('ASCII')

        cy = rows.to_bytes(2, 'big')
        cx = columns.to_bytes(2, 'big')
        sx = pixelsX.to_bytes(2, 'big')
        sy = pixelsY.to_bytes(2, 'big')

        b += cy
        b += cx
        b += sx
        b += sy

        self.sock.send(b)


    def _on_success(self):
        try:
            res = self.recv()
            if res == b'\x00':
                self._debug(f"rlogin连接成功")
                return 1
            else:
                self._debug(f"rlogin连接失败")
                return 0
        except SocketError as e:
            if e.errno != errno.ECONNRESET:
                self._debug(f"rlogin连接失败:{e}",type=1)
                raise RloginException(e)
            self._debug(f"rlogin连接失败")
            return 0


    def close(self):
        """close the connection"""
        self._debug(f"断开连接")
        if self.sock:
            self.sock.close()
        self._closed = True


    def __exit__(self, *args):
        if not self._closed:
            self.close()



if __name__ == "__main__":
    rlogin_cli = RloginClient(clientUsername='clientUsername',
                              serverUsername='serverUsername',
                              serverPassword="serverPassword",
                              terminalType="xterm",
                              terminalSpeed=9600)
    # rlogin_cli.set_debug()  #需要debug则打开
    rlogin_cli.connect(host="xxx.xxx.xxx.xxx", port=513,rows=41,columns=95,pixelsX=760,pixelsY=656)



# Rlogin
> python的Rlogin客户端
>

本项目是用python开发，rlogin协议端口范围【514-1023】，本项目默认的从1023端口往下使用端口,设置账号密码会自动进行登录，当然，如果自动登录失败会而然可以进行手动登录。

基本功能测试完成,有一些未经测试的功能待完善。

##### 安装

```
pip install rloginclient
```

##### 例子

```
from rlogin.rlogin_client import RloginClient


#连接客户端
rlogin_cli = RloginClient(clientUsername='clientUsername',
                              serverUsername='serverUsername',
                              serverPassword="serverPassword",
                              terminalType="xterm",
                              terminalSpeed=9600)
                              
# rlogin_cli.set_debug()  #需要debug则打开
rlogin_cli.connect(host="xxx.xxx.xxx.xxx", port=513)


#接受消息 bufsize flags 默认可不填：
res = rlogin_cli.recv(bufsize,flags)

#发送消息
rlogin_cli.send(data,flags)

#修改屏幕大小
rlogin_cli.send_win_size(rows=41,columns=95,pixelsX=760,pixelsY=656)
```


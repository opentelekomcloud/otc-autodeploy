**Requires**
Python version is 2.7
```
pip install oslo.config 
pip install ipaddr 
pip install os_client_config 
pip install shade 
pip install tabulate 
pip install humanfriendly 
pip install python-openstackclient 
pip install paramiko 
```
**Usage**
1. Fill the parameters like `user`, `password`,`user_domain` and others in `./conf/user.conf`
2. Enjoy yourself.

**Command**
1. show  
    `python autodeploy.py --config-file ./conf/user.conf --show {flavor|image|az}`  
Example:
```
> python autodeploy.py --config-file ./conf/user.conf --show flavor
>>> Connection OK
+--------------------+------+---------+----------+----------+--------+
|        name        | vcpu |   ram   |   disk   | disabled | public |
+--------------------+------+---------+----------+----------+--------+
|     c1.medium      |  1   |  1 GiB  | 0 bytes  |  False   |  True  |
|      c1.large      |  2   |  2 GiB  | 0 bytes  |  False   |  True  |
......
```
2. deploy  
You can fill the parameters in the conf file or the command line.  
`python autodeploy.py --config-file ./conf/winapp-exchange.conf`  
In this example, we have filled all parameters in the conf file like this:  

```
[DEFAULT]
project_name = ***
project_id = ***
user = ***
user_domain = ***
password = ***

deploy=winapp-exchange
vpc_name=exchange-test
vpc_cidr=10.0.0.0/8
key_name=exchange-keypair

[winapp]
domain_name=exchange-test
domain_netbios_name=exchange-test
addc_flavor=c2.large
addc_disksize=80
server_flavor=c2.xlarge
server_disksize=500

```
After you exec the command, you can see:

```
> python autodeploy.py --config-file ./conf/winapp-exchange.conf
>>> Connection OK
Start deploy windows exchange ...
>>> deploy vpc exchange-test OK >>>
>>> deploy subnet public(10.0.0.0/24) OK >>>
>>> deploy subnet private(10.0.1.0/24) OK >>>
>>> deploy server exchange-test-NAT-server OK >>>
>>> deploy server exchange-test-ADDC OK >>>
>>> deploy server exchange-test-exchange-server OK >>>
Deploy windows exchange end.
```
Then you can find the network and servers form the console on OTC.


3. undeploy  
`python autodeploy.py --config-file ./conf/user.conf --undeploy vpc --vpc-name exchange-test`  

After the command, you can see:  

```
>>> Connection OK
>>> undeploy vpc exchange-test
remove router interface ee63cd28-e5f2-4f70-8b26-532e1c3811e0
remove router interface d010455f-8fda-410f-828e-0d22c80761d2
delete subnet public
delete network 333447b7-f273-472b-8365-71c0b1efc47c
delete subnet private
delete network 333447b7-f273-472b-8365-71c0b1efc47c
delete router exchange-test
OK >>>
```
And then, all the resources in the VPC 'exchange-test' have been deleted. 


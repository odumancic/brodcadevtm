# Brocade vTM failover script

Python script for automating switching pools between main and failover pool.
Authorization and URL is currently hardcoded into the rest.py, see the Configuration chapter.

## Usage

~~~
Usage: rest.py <options>
 Options:
 --remove-failover       Remove from failover
 --add-failover          Add to failover
 --move-failover         Move to failover
 --move-main             Move to main

 The scripts reads from pool.conf the configurations to change.
 Multiple lines can be used to configure different virtual servers.

Example:
vserver:[Virtual Server name];main:[Main Pool name];failover:[Failover Pool name]
~~~

### Configuration
#### Autorization and URL
Authorization and  URL can be changed in the rest.py. Username and password needs to be converted to BASE64 in format ```<username>:<password>```

Example:
~~~
client.headers.update({'Authorization' : 'Basic ****************'})

client.verify = False

url = 'http://localhost:9070/api/tm/3.7/'
~~~

#### Configuring pools
Example of pool.conf. For each Virtual server add the following line
```vserver:[Virtual Server name];main:[Main Pool name];failover:[Failover Pool name]```

Example:
~~~
vserver:webconsole;main:webconsoletest3-1;failover:webconsoletest3-3
vserver:apacs;main:apacstest3-1;failover:apacstest3-3
~~~

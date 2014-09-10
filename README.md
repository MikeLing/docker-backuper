docker-backuper
====================

*THIS DOCUMENTATION IS NOT UP TO DATE CURRENTLY*

a python script to backup/restore the docker containers / volumes.

The idea :
* backup will backup the metadata from a container and its volumes
* restore will recreate a container from the saved metadata and restore its volumes

####Requires Python && Docker-py python package.

```
apt-get install python-pip 
pip install docker-py
```


##How to use
Running backup.py with -h will produce :
```
usage: backup.py [-h] [-s Absolute_Storage_Path | [-b | -t]
                 [-r | -d destcontainername] [-l]
                 container

backup/restore/list a container and its volumes

positional arguments:
  container

optional arguments:
  -h, --help            show this help message and exit
  -s Absolute_Storage_Path, --storage Absolute_Storage_Path
                        where to store/restore data, defaults to current path
                        (for BACKUP running inside a container, this parameter
                        isn't used)
  -b, --backup          Backups a container to a tar file
  -t, --stopcontainer   Should we stop the source container before
                        extracting/saving its volumes (useful for files to be
                        closed prior the backup)
  -r, --restore         Restore a container from tar backup
  -d destcontainername, --destcontainer destcontainername
                        name of the restored container, defaults to source
                        container name
  -l, --list            Lists the volumes of the container
```

### Natively on host, LIST :
```
./backup.py --list containername 
```
This command will list all the volumes/mount points/boindings of containername

### Natively on host, BACKUP :
```
./backup.py --backup containername --storage /tmp 
```
This command will save the metadata and volumes as a tar file named : `/tmp/containername.tar`


```
./backup.py --backup containername --storage /tmp --stopcontainer
```
This command will save the metadata and volumes as a tar file named : `/tmp/containername.tar`
Additionnaly, the source container will be stopped before backup and restarted afterwards

### Natively on host, RESTORE :
```
./backup.py --restore containername --storage /tmp --destcontainer newone
```
This command will restore the container `containername` and its volumes as a new container named `newone` from the tar file named : `/tmp/containername.tar`


### Run as a Container:
First, you need to build it :
```
docker build -t docker-backuper .
```

Once done, can can backup using :
```
docker run -t -i --rm \
  -v /var/run/docker.sock:/var/run/docker.sock \
  --volumes-from <container>
  -v /tmp:/backup \
  acaranta/docker-backuper \
  backup <container> --stopcontainer
```
* The .tar backups will be stored in /backup ... which you can bind to any dir on your docker host.
* In this mode, the `--storage` option is ignored as the data will be stored in the bound directory `/backup`.
* The container's volumes to be backed up are mounted using the --volumes-from option
* if added, the option `--stopcontainer` will stop the container to backup, and restart it afterwards

Then you can restore using :
```
 docker run -t -i --rm \
  -v /var/run/docker.sock:/var/run/docker.sock \
  -v <TarStoragePath>:/backup \
  acaranta/docker-backuper \
  restore <container> --destname <newcontainer> --storage <TarStoragePath>
```
* The .tar backups will be Fetched in the argument passed as `--storage` and which also has to be bound using `-v` option to `/backup`. It works differently from the backup, because for the restore, a container is launched on the docker host with the data storage dir mounted directly in order to read the tar files, it therefore need the `/backup` binding AND the --storage argument both pointing towards the same path.
* the container will be restored under the name `<newcontainer>`


##FULL EXAMPLE
Let's imagine we want a mysql container and we inject some data :
```
$ docker run -p 3306:3306 -e MYSQL_ROOT_PASSWORD=pouet --name mysqlsrv -d mysql
$ mysql -h 127.0.0.1 -uroot -ppouet -e "create database mytestdb ;"
$ echo "CREATE TABLE myTable (id mediumint(8) unsigned NOT NULL auto_increment,naming varchar(255) default NULL,  phone varchar(100) default NULL,  PRIMARY KEY (id)) AUTO_INCREMENT=1;
INSERT INTO myTable (naming,phone) VALUES (\"Brittany Z. Casey\",\"03 38 23 30 49\"),(\"Brandon C. Brady\",\"04 31 19 78 68\"),(\"Celeste I. Fletcher\",\"08 05 11 34 95\"),(\"Jael X. Mueller\",\"04 02 92 34 51\"),(\"Jonah T. Short\",\"09 07 74 41 37\"),(\"Natalie P. Hayes\",\"06 95 60 81 42\"),(\"Idola T. Mason\",\"06 49 92 54 92\"),(\"Indigo D. Chase\",\"04 77 59 48 16\"),(\"David K. Craig\",\"02 98 39 69 02\"),(\"Byron K. Sanders\",\"01 07 76 41 74\");
INSERT INTO myTable (naming,phone) VALUES (\"Brody D. Fitzpatrick\",\"06 60 39 08 84\"),(\"Grady B. Kline\",\"01 11 62 76 30\"),(\"Tanek O. Nelson\",\"04 34 16 80 50\"),(\"Ralph N. Reeves\",\"06 68 22 14 15\"),(\"Finn F. Castro\",\"06 17 23 14 90\"),(\"Imelda Z. Kemp\",\"02 37 63 50 46\"),(\"Denise A. Mcguire\",\"08 16 40 59 90\"),(\"Kellie U. Pierce\",\"02 63 15 98 34\"),(\"Rhiannon P. Holman\",\"05 60 21 05 15\"),(\"Quail A. Copeland\",\"04 26 63 57 14\");
" | mysql -h 127.0.0.1 -uroot -ppouet mytestdb 
$ mysql -h 127.0.0.1 -uroot -ppouet mytestdb -e "select * from myTable"
```
Then we backup this container :
```
$ docker run -t -i --rm \
  -v /var/run/docker.sock:/var/run/docker.sock \
  --volumes-from mysqlsrv
  -v /tmp:/backup \
  acaranta/docker-backuper \
  backup mysqlsrv --stopcontainer 
```
We can remove completely the test container :
```
$ docker rm -f mysqlsrv
```
And restore from backup :
```
$ docker run -t -i --rm \
  -v /var/run/docker.sock:/var/run/docker.sock \
  -v /tmp:/backup \
  acaranta/docker-backuper \
  restore mysqlsrv --destname mysqlnewsrv --storage /tmp
```
And retest :
```
$ mysql -h 127.0.0.1 -uroot -ppouet mytestdb -e "select * from myTable"
```

##IMPORTANT NOTES
if a container was launched with a boud volume, ie :
```
docker run -d  -v /srv/docker-external-volumes/registry:/mnt/registry \
	-e STORAGE_PATH=/mnt/registry/storage \
	-e SQLALCHEMY_INDEX_DATABASE=sqlite:////mnt/registry/db/dbreg.sqlite \
	-p 5000:5000 --name my_registry registry
```
(here `/srv/docker-external-volumes/registry` --> `/mnt/registry`)).
The restore WILL take place in this bound path ... aka it will overwrite (it data is present) the contents of `/srv/docker-external-volumes/registry` !!!
That is not a bug, it was designed like this ;)

##TODO
* remove the bound inplace restore by default and add a `--bound-restore` option ?
* add a way to nicely name the tar files ?
* add a way to timestamp the tar files and let the user choose different restore points ?
* add a check to stop the backup if the container has no volumes !
* add a few other checks and maybe errors interceptions to clean temp containers
* Review all the metadata parameters that still needs to be restored :
** ro or rw volumes
** ...

##DISCLAIMER 
Please TEST your backup/restore procedure, your data, etc ... this is provided as-is and does not garantee anything ! ;)


## Sources
Based on the code from docker-volume-backup : https://github.com/paimpozhil/docker-volume-backup

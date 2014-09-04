import docker
import sys
import pickle
import tarfile
from subprocess import call

c = docker.Client(base_url='unix://var/run/docker.sock',
                  version='1.9',
                  timeout=10)

#Prints Help Message
def usage():
	print "python backup.py [backup/restore] data-container-name [restore-container-name]"

#Determines if we run within a docker container
#Might not be truly cleany as a way to check but it works ;)
def dockerized():
	if 'docker' in open('/proc/1/cgroup').read():
		return True

#first argument is the option backup/restore
if len(sys.argv) < 3:
	print "Not enough arguments !!"
	usage()
	sys.exit(1)

option = sys.argv[1]
name = sys.argv[2]

#Location of the tar files (for a container running)
datadir = "/backup"

if option == "backup":
	# second argument is the container name
	container = c.inspect_container(name)
	container_name =  container['Name']
	print "Backing up : " + container_name
	volumes =  container['Volumes']
	
	print "writing meta data to file "
	pickle.dump ( container , open ("metadata","wb") )

	tar = tarfile.open(name + ".tar", "w:gz")
	if dockerized():
		tar = tarfile.open(datadir + "/" + name + ".tar", "w:gz")
	tar.add("metadata")
	for i, v in enumerate(volumes):
	    print  v, volumes[v]
	    tar.add(volumes[v],v)
	tar.close()

elif option == "restore":
	#third argument is the restored container name
	destname = sys.argv[3]
	
	print "Restoring"
	tar = tarfile.open(name + ".tar")
	if dockerized():
		tar = tarfile.open(datadir + "/" + name + ".tar")
	metadatafile =  tar.extractfile("metadata")
	metadata =  pickle.load(metadatafile)

#	print metadata
	imagename = metadata["Config"]["Image"]
	volumes =  metadata['Volumes']
	print volumes
	vlist = []
	binds = {} 

	for i, v in enumerate(volumes):
       		print  v, volumes[v]
		vlist.append(v)
		#check if volume has a binding, and add it to bindings for inplace restore
		if str(volumes[v]).find('/var/lib/docker/vfs/dir/') < 0:
			binding = { volumes[v]:{'bind':v} }
			binds.update(binding)

	restored_container = c.create_container(imagename,tty=True,volumes=vlist,name=destname)
	c.start(restored_container,binds=binds);
	runstring = "docker run --rm -ti --volumes-from " + restored_container['Id'] +" -v $(pwd):/backup2  ubuntu tar xvf /backup2/"+ name +".tar"
	print runstring
	call(runstring,shell=True)
	
else:
	usage()

#from __future__ import #logger.error_function
from __future__ import with_statement
from googleapiclient.discovery import build
from apiclient.http import MediaFileUpload, MediaIoBaseDownload
from httplib2 import Http
from oauth2client import file, client, tools
import time
import os
import sys
import magic
import shutil
import errno
import random
import datetime
import io
import threading
import glob
from fuse import FUSE, FuseOSError, Operations
import pickle
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
import logging

# If modifying these scopes, delete the file token.json.
logging.basicConfig(filename='logs.txt', filemode='w', format='%(message)s')

logging.disable(logging.WARNING)
logger = logging.getLogger(__name__)

# fp=open("logs.txt","w")

CURRENT_PARENT_ID="root"
root_folder=".backend"
Dict={}
SCOPES = 'https://www.googleapis.com/auth/drive'
# store = file.Storage('token.json')
# creds = store.get()
# if not creds or creds.invalid:
# 	flow = client.flow_from_clientsecrets('credentials.json', SCOPES)
# 	creds = tools.run_flow(flow, store)
# service = build('drive', 'v3', http=creds.authorize(Http()))
creds = None
# The file token.pickle stores the user's access and refresh tokens, and is
# created automatically when the authorization flow completes for the first
# time.
if os.path.exists('token.pickle'):
    with open('token.pickle', 'rb') as token:
        creds = pickle.load(token)
# If there are no (valid) credentials available, let the user log in.
if not creds or not creds.valid:
    if creds and creds.expired and creds.refresh_token:
        creds.refresh(Request())
    else:
        flow = InstalledAppFlow.from_client_secrets_file(
            'credentials.json', SCOPES)
        creds = flow.run_local_server(port=0)
    # Save the credentials for the next run
    with open('token.pickle', 'wb') as token:
        pickle.dump(creds, token)

service = build('drive', 'v3', credentials=creds)


class Passthrough(Operations):
	def __init__(self, root):
		logger.error("Init Called : "+str(root))
		self.root = root

	# Helpers
	# =======

	def _full_path(self, partial):
		partial = partial.lstrip("/")
		path = os.path.join(self.root, partial)
		return path

	# Filesystem methods
	# ==================

	def show_files(self,parentid,full_path):
		global service
		logger.error ("show_files : "+str(full_path))
		try:
			full_path=full_path.rstrip('/')
			files = glob.glob(full_path)
			for f in files:
			    os.remove(f)
		except Exception as e:
			pass

		# #logger.error "1"
		try:
			results = service.files().list(q="'"+parentid+"' in parents",pageSize=100, fields="files(id, name, mimeType)").execute()
			items = results.get('files', [])
			# #logger.error "2"
			if not items:
				logger.error ('No files found.')
			else:
				#logger.error ('Files:')
				for item in items:
					try:
						# logger.error ("Name : ",item['name'],"\nId : ",item['id'],"\n")
						Dict[item['id']]=90
						if item['mimeType']=="application/vnd.google-apps.folder":
							os.mkdir(full_path+"/"+item['name'])
						else:
							os.mknod(full_path+"/"+item['name'])
					except:
						pass

		except Exception as e:
			logger.error (e)


	def access(self, path, mode):
		global service
		full_path = self._full_path(path)

		logger.error ("access called : "+str(full_path)+" "+str(mode))


		if not os.access(full_path, mode):
			raise FuseOSError(errno.EACCES)

	def chmod(self, path, mode):
		logger.error ("chmod called : "+str(path))
		full_path = self._full_path(path)
		return os.chmod(full_path, mode)

	def chown(self, path, uid, gid):
		logger.error ("chown called : "+str(path))
		full_path = self._full_path(path)
		return os.chown(full_path, uid, gid)

	def getattr(self, path, fh=None):
		logger.error ("getattr called : "+str(path))
		full_path = self._full_path(path)
		st = os.lstat(full_path)
		return dict((key, getattr(st, key)) for key in ('st_atime', 'st_ctime',
					 'st_gid', 'st_mode', 'st_mtime', 'st_nlink', 'st_size', 'st_uid'))

	def readdir(self, path, fh):

		full_path = self._full_path(path)
		logger.error ("readir : "+str(full_path))

		if(full_path!=".backend/"):
			#logger.error "Here"
			try:
				req_id=self.getidfrompath(full_path)
			except Exception as e:
				logger.error ("readdir : "+str(e))

		else:
			req_id='root'

		#logger.error "req_id", req_id
		self.show_files(req_id,full_path)



		dirents = ['.', '..']
		if os.path.isdir(full_path):
			dirents.extend(os.listdir(full_path))
		for r in dirents:
			yield r

	def readlink(self, path):
		logger.error ("readlink called : "+str(path))
		pathname = os.readlink(self._full_path(path))
		if pathname.startswith("/"):
			# Path name is absolute, sanitize it.
			return os.path.relpath(pathname, self.root)
		else:
			return pathname

	def mknod(self, path, mode, dev):
		logger.error ("mknod called : "+str(path))
		return os.mknod(self._full_path(path), mode, dev)

	def rmdir(self, path):
		logger.error ("rmdir called : "+str(path))
		full_path = self._full_path(path)
		req_id=self.getidfrompath(full_path)
		service.files().delete(fileId=req_id).execute()
		return os.rmdir(full_path)

	def mkdir(self, path, mode):
		logger.error ("mkdir called : "+str(path))
		global service

		full_path = self._full_path(path)
		full_path=full_path.rstrip('/')
		fp=full_path.split("/")

		fplen=len(fp)
		filename=fp[fplen-1]

		temppath=""
		for i in range(0,fplen-1):
			temppath=temppath+fp[i]+"/"

		req_id=self.getidfrompath(temppath.rstrip('/'))

		file_metadata ={'name' : filename,'mimeType' : 'application/vnd.google-apps.folder','parents':[req_id]}
		file = service.files().create(body=file_metadata,fields='id').execute()
		#logger.error "mkdir called"
		return os.mkdir(self._full_path(path), mode)

	def statfs(self, path):
		logger.error ("statfs called : "+str(path))
		full_path = self._full_path(path)
		stv = os.statvfs(full_path)
		return dict((key, getattr(stv, key)) for key in ('f_bavail', 'f_bfree',
			'f_blocks', 'f_bsize', 'f_favail', 'f_ffree', 'f_files', 'f_flag',
			'f_frsize', 'f_namemax'))

	def unlink(self, path):
		logger.error ("ulink called : "+str(path))
		ids = self.getidfrompath(path)
		logger.error("Id: "+str(ids))
		service.files().delete(fileId=ids).execute()

		return os.unlink(self._full_path(path))

	def symlink(self, name, target):
		logger.error ("symlink called : "+str(path))
		return os.symlink(name, self._full_path(target))

	def trim(self, path):
		l = len(path)
		i=0
		for i in range(l-1,0,-1):
			if(path[i]=='/'):
				break
		return i

	def rename(self, old, new):
		logger.error ("rename called : "+str(old))
		logger.error ("rename called : "+str(new))
		old_path = self._full_path(old)
		new_path = self._full_path(new)
		x = self.trim(old_path)
		y = self.trim(new_path)
		old_name = old_path[x+1:]
		new_name = new_path[y+1:]
		#logger.error "~~~~~~~~~~~~~~~~~~~~~~~~~~"
		#logger.error old_path
		#logger.error new_path
		#logger.error old_name
		#logger.error new_name
		#logger.error "~~~~~~~~~~~~~~~~~~~~~~~~~~"
		parent = new_path[:y]
		old_parent = old_path[:x]
		#logger.error "parent ::  ",parent

		if('.Trash-' in new):
			#logger.error "Deletion Called"
			try:
				#type(recordtomodify)
				full_path = self._full_path(old)
				file_id = self.getidfrompath(full_path)
				service.files().delete(fileId=file_id).execute()
			except Exception as e:
				logger.error (e)
			return shutil.rmtree(str(old_path))

		elif(old_name == new_name):
			try:
				#logger.error "~~~~~~~~~~~~~~~~~~~~~~~~~~"
				#logger.error "move called"
				#logger.error "parent :: ",parent
				#logger.error "~~~~~~~~~~~~~~~~~~~~~~~~~~"
				file_id = self.getidfrompath(old_path)
				parent_id = self.getidfrompath(parent)
				old_parent_id = self.getidfrompath(old_parent)
				updated_file = service.files().update(fileId=str(file_id), addParents=str(parent_id), removeParents=str(old_parent_id)).execute()

				#logger.error "moved..."
			except Exception as e:
				logger.error (e)
			return os.rename(str(old_path), str(new_path))
		# elif(".goutputstream" in old):
    	# 		try:
		# 			fileid=self.getidfrompath(new)
		elif(".goutputstream" in old):
			try:
				file_id=self.getidfrompath(new)
				del Dict[file_id]
				service.files().delete(fileId=file_id).execute()
				file_name=new_path.split("/")[-1]
				body = {'name': file_name }
				media_body = MediaFileUpload(old_path)
				#logger.error "Media Body : ",full_path
				# time.sleep(5)
				fiahl = service.files().create(body=body, media_body=media_body).execute()
				Dict[self.getidfrompath(new)]=90

			except:
				logger.error("error")
			return os.rename(str(old_path), str(new_path))
		else:
			#new = new[1::]

			try:

				file_id = self.getidfrompath(old_path)
				file_id = str(file_id)
				file = service.files().get(fileId=file_id).execute()
				file = {'name': new_name}
				#logger.error "22"
				#logger.error "file id : ", file_id
				# Rename the file.
				updated_file = service.files().update(fileId=file_id, body=file, fields='name').execute()
				#logger.error "33"
			except errors.HttpError:
				logger.error ('An error occurred: s')

			#logger.error "44"

			return os.rename(str(old_path), str(new_path))

	def link(self, target, name):
		logger.error ("link called : "+str(path))
		return os.link(self._full_path(target), self._full_path(name))

	def utimens(self, path, times=None):
		logger.error ("utimens called : "+str(path))
		global service
		full_path = self._full_path(path)
		full_path=full_path.rstrip('/')
		full_path=full_path.replace('Google Drive','.backend')
		fp=full_path.split("/")

		fplen=len(fp)
		filename=fp[fplen-1]

		temppath=""
		for i in range(0,fplen-1):
			temppath=temppath+fp[i]+"/"

		req_id=self.getidfrompath(temppath.rstrip('/'))
		logger.error(full_path)
		logger.error(temppath)
		logger.error(fp)
		#logger.error "$$$$$$$$$$$$$$$$$$$", req_id
		if('trashinfo' not in full_path):
			try:
				body = {'name': filename , 'parents':[req_id]}
				media_body = MediaFileUpload(full_path)
				#logger.error "Media Body : ",full_path
				# time.sleep(5)
				fiahl = service.files().create(body=body, media_body=media_body).execute()
			except Exception as e:
				logger.error (e)
		temppath=""
		for i in range(1,fplen):
			temppath=temppath+"/"+fp[i]
		logger.error(temppath)
		Dict[self.getidfrompath(temppath)]=90




		return os.utime(self._full_path(path), times)

	# File methods
	# ============

	def open(self, path, flags):
			logger.error ("open called : "+str(path))
			full_path = self._full_path(path)
			logger.error (full_path)
			myid=self.getidfrompath(full_path)
			logger.error(myid)
			logger.error(Dict[myid])
			if(Dict[myid]==90):

					Dict[myid]=999

					#logger.error Dict[myid]

					request = service.files().get_media(fileId=myid)
					fh = io.BytesIO()
					fh = io.FileIO(full_path, 'wb')
					downloader = MediaIoBaseDownload(fh, request)
					done = False
					try:
						status,done=downloader.next_chunk()
					except:
						done=True
					while done is False:
							status, done = downloader.next_chunk()
							logger.error ("Download %d%%." % int(status.progress() * 100))
					#logger.error"uioyr.....",id
					# return
			return os.open(full_path, flags)

	def create(self, path, mode, fi=None):
		logger.error ("create called : "+str(path))
		full_path = self._full_path(path)
		return os.open(full_path, os.O_WRONLY | os.O_CREAT, mode)

	def read(self, path, length, offset, fh):
		logger.error ("read called : "+str(path))
		os.lseek(fh, offset, os.SEEK_SET)
		return os.read(fh, length)

	def write(self, path, buf, offset, fh):
		logger.error ("write called : "+str(path))
		os.lseek(fh, offset, os.SEEK_SET)
		return os.write(fh, buf)

	def truncate(self, path, length, fh=None):
		logger.error ("truncate called : "+str(path))
		full_path = self._full_path(path)
		with open(full_path, 'r+') as f:
			f.truncate(length)

	def flush(self, path, fh):
		logger.error ("flush called : "+str(path))
		return os.fsync(fh)

	def release(self, path, fh):
		logger.error ("release called : "+str(path)+" "+str(fh))
		return os.close(fh)

	def destroy(self,data=None):
		logger.error("destroy called")
		shutil.rmtree(".backend")
		return

	def fsync(self, path, fdatasync, fh):
		logger.error ("fsync called : "+str(path))
		try:

		# First retrieve the file from the API.
					global service
					full_path = self._full_path(path)
					if ".goutputstream" in path:
    				         return self.flush(path, fh)
					logger.error ("Path"+str(full_path))

					file_id=self.getidfrompath(full_path)
					#logger.error file_id
					filname=full_path.split('/')
					l=len(filname)
					new_filename=full_path
					#logger.error new_filename
					file = service.files().get(fileId=file_id).execute()

					# File's new content.
					mime = magic.Magic(mime=True)
					new_mime_type=mime.from_file(full_path)

					media_body = MediaFileUpload(
					new_filename, mimetype=new_mime_type, resumable=True)

					# Send the request to the API.
					fiahl = service.files().update(fileId=file_id,media_body=media_body).execute()
					return
					# updated_file = service.files().update(
					# fileId=file_id,
					# body=file,
					# media_body=media_body).execute()
		except Exception as e:
			logger.error (e)

		return self.flush(path, fh)

	def getidfrompath(self,path):
		try:
			path=path.split('/')
			ln=len(path)
			ids=['root']
			for i in range(1,len(path)):
				q="'"+ids[i-1]+"' in parents and name='"+path[i]+"'"
				results = service.files().list(q=q,pageSize=100, fields="files(id)").execute()
				for file in results.get('files', []):
					#logger.error file.get('id')
					ids.append(file.get('id'))

			return ids[ln-1]
		except Exception as e:
			logger.error ("getidfrompath"+str(e))
def main(mountpoint):
	# shutil.rmtree(".backend")
	os.mkdir(".backend")
	FUSE(Passthrough(root_folder), mountpoint, nothreads=True, foreground=True)

if __name__ == '__main__':
	main(sys.argv[1])

#!/usr/bin/env python
# -*- coding: utf-8 -*- 

#
# Es necesario tener instalado:
# 	$ sudo pip install pyapi-gitlab
#
# Documentacion de la API: http://pyapi-gitlab.readthedocs.org/en/latest/#users
#

import gitlab

# configuraciones
GITLAB_HOST="http://pericles.zaffarano.com.ar"
GITLAB_PORT=10080
GITLAB_TOKEN="nAde7J6zTo1pqJdVWTR5"

#
# mi clave publica, para probar...
#
KEY='ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAABAQDVjNvqrY+KE84q8ObvumW/2ItvX6pypedUw7t7k5BQVvCEjEmQxdEnecsz7g0LjVCZQ6KSN4iu8Tpbj5PKwiZxZjyf6Q+8eUeRh9lx0y4n2iCpGafTnJYVoI13bsJVeGnMgqBkZv03evh0fIj25zh4vGt5mhxMpbpz7OkOEnHf4IZkD84/iaDz/RJK/edz+my8hc3QD0mONoTKDbYaKHYeoOFJa47pIHJko6Wi1ZOVr3thSkk05pt8kAI4gDzddDSDnaOsQukUR3tps2dNRzewAqwQzdAUazL4R8hox9AYfRYF9iWFF2qMlxrqzFU9McLKNND6WD8vYpb3fpy+5xut sebas@zaffarano.com.ar'

git = gitlab.Gitlab("%s:%s" % (GITLAB_HOST, GITLAB_PORT), token=GITLAB_TOKEN, verify_ssl=False)

#
# Parametros para createuser
#
#data = {"name": name, "username": username, "password": password,
#                "email": email, "skype": skype,
#                "twitter": twitter, "linkedin": linkedin,
#                "projects_limit": projects_limit, "extern_uid": extern_uid,
#                "provider": provider, "bio": bio}

# despues de crear el usuario hay que actualizar la base para que parezca que el usuario confirmo el alta
# update users set confirmed_at = '2014-06-27 20:06:03.961343' where email='szaffarano@afip.gob.ar';
user = None
for u in git.getusers():
	if u.get('username') == 'szaffarano':
		user = u
		break
if user is None:
	print "creando usuario..."
	user = git.createuser("Sebastián Zaffarano", "szaffarano", "sebas123", "sebas@zaffarano.com.ar")
	if not user:
		print "Error creando usuario"
		import sys
		sys.exit(1)
else:
	print "El usuario ya existia, no se crea"

user_id = user.get("id")
print "Usuario: %s" % user_id

print "Agregando clave publica al usuario %s" % user_id

if git.addsshkeyuser(user_id, "sebas", KEY):
	print "Clave agregada exitosamente"

projects = git.getprojects(page=1, per_page=10000);

for p in projects:
	if p.get('name') in ['rsi', 'storage']:
		print "Agregando usuario al proyecto %s" % p.get('name')
		git.addprojectmember(p.get('id'), user_id, 'master')

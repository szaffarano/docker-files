## Instalación de Redmine+Gitlab con Docker

### Funciones Helpers
Informa la ip local de un contenedor docker
```sh
$ alias dip='docker inspect --format '\''{{ .NetworkSettings.IPAddress }}'\'''
```

Para ubuntu, alias de docker.io a docker para evitar incompatibilidades (no necesario en Fedora :P)
```sh
$ alias docker=docker.io
```

### Definición de volumenes
- /home/git/data
- /var/lib/postgresql
- /var/lib/redis
- /redmine/files

### Containers que se van a usar

- https://github.com/sameersbn/docker-gitlab
- https://github.com/sameersbn/docker-postgresql
- https://github.com/sameersbn/docker-redis
- https://github.com/sameersbn/docker-redmine

```sh
$ docker pull sameersbn/gitlab:latest
$ docker pull sameersbn/postgresql:latest
$ docker pull sameersbn/redis:latest
$ docker pull sameersbn/redmine:latest
```

### Iniciar data-only container
```sh
$ docker run -d --name gitlab-redmine-data \
   -v /home/git/data \
   -v /var/lib/postgresql \
   -v /redmine/files \
   -v /var/lib/redis busybox \
   true
```

### Iniciar container de postgresql
```sh
$ docker run --name postgresql -d \
   --volumes-from gitlab-redmine-data sebas/postgresql
```

### Iniciar container de redis
```sh
$ docker run --name=redis -d \
   --volumes-from gitlab-redmine-data \
   sameersbn/redis:latest
```

### Inicializar base de datos de gitlab y redmine
Obtener contraseña de la base posgres:

```sh
$ docker logs postgresql
```

Entrar con cliente psql

```sh
$ psql -U postgres -h $(dip postgresql)
```

Ejecutar sentencias para gitlab

```sql
CREATE ROLE gitlab with LOGIN CREATEDB PASSWORD 'gitlab';
CREATE DATABASE gitlabhq_production;
GRANT ALL PRIVILEGES ON DATABASE gitlabhq_production to gitlab;
```

Ejecutar sentencias para redmine

```sql
CREATE ROLE redmine with LOGIN CREATEDB PASSWORD 'redmine';
CREATE DATABASE redmine_production;
GRANT ALL PRIVILEGES ON DATABASE redmine_production to redmine;
```

### Generación del certificado autofirmado (por ahora deshabilitado!)
```sh
openssl genrsa -out gitlab.key 2048
openssl req -new -key gitlab.key -out gitlab.csr
openssl x509 -req -days 365 -in gitlab.csr -signkey gitlab.key -out gitlab.crt
openssl dhparam -out dhparam.pem 2048
```

### Copiar certificados para que levante gitlab (por ahora deshabilitado!)
```sh
mkdir -p /opt/gitlab/data/certs
cp gitlab.key /opt/gitlab/data/certs/
cp gitlab.crt /opt/gitlab/data/certs/
cp dhparam.pem /opt/gitlab/data/certs/
chmod 400 /opt/gitlab/data/certs/gitlab.key
```

### Levantar container gitlab para setup de la db
```sh
$ docker run --name=gitlab -i -t --rm \
  --link postgresql:postgresql \
  --link redis:redisio \
  -e "DB_USER=gitlab" -e "DB_PASS=gitlab" \
  -e "DB_NAME=gitlabhq_production" \
  --volumes-from gitlab-redmine-data \
  sebas/gitlab app:rake gitlab:setup
```

### Levantar container gitlab
```sh
docker run --name=gitlab -d \
  --link postgresql:postgresql \
  --link redis:redisio \
  --volumes-from gitlab-redmine-data \
  -v /opt/gitlab/data:/opt/gitlab/data \
  -p 10022:22 -p 10080:80 \
  -e "DB_USER=gitlab" -e "DB_PASS=gitlab" \
  -e "DB_NAME=gitlabhq_production" \
  -e "_GITLAB_HTTPS=true" -e "_SSL_SELF_SIGNED=true" \
  -e "SMTP_HOST=ariadna.afip.gob.ar" \
  -e "SMTP_PORT=25" \
  -e "SMTP_STARTTLS=true" \
  -e "SMTP_DOMAIN=zaffarano.com.ar" \
  -e "SMTP_USER=mailer" \
  -e "SMTP_PASS=mailer" \
  -e "GITLAB_PORT=10080" -e "GITLAB_SSH_PORT=10022" \
  -e "GITLAB_HOST=pericles.zaffarano.com.ar" \
  -e "GITLAB_EMAIL=sebas@zaffarano.com.ar" \
  -e "GITLAB_SUPPORT=sebas@zaffarano.com.ar" \
  -e "_SSL_CERTIFICATE_PATH=/opt/gitlab/data/certs/gitlab.crt" \
  -e "_SSL_KEY_PATH=/opt/gitlab/data/certs/gitlab.key" \
  -e "_SSL_DHPARAM_PATH=/opt/gitlab/data/certs/dhparam.pem" \
  sebas/gitlab
```

### Información útil
Url ejemplo de la api REST para interactuar con gitlab https://pericles.zaffarano.com.ar:10443/api/v3/projects?private_token=QzL9abn3pihuVZFnnVNs

### Modificaciones al container redmine
Para integrarlo con gitlab fue necesario bindear el volúmen gitlab en donde se encuentran los repositorios.  Esto implica que dicho volúmen tiene que tener los permisos para que pueda ser accedido por el usuario de redmine (www-data en el caso de nuestro redmine).

La solución fue modificar el Dockerfile de forma tal que en el caso de tener un directorio con repositorios git, obtenga el grupo de dicho directorio, de no existir el grupo en el contenedor lo crea, y le agrega ese grupo al usuario www-data.

Para más información ver el archivo .patch con los cambios.

### Levantar container redmine para setup de la db
```sh
$ docker run --name redmine -i -t --rm \
  --link postgresql:postgresql \
  --volumes-from gitlab-redmine-data \
  -e "DB_USER=redmine" -e "DB_PASS=redmine" \
  -e "DB_NAME=redmine_production" \
  sebas/redmine app:db:migrate
```

### Levantar container redmine
```sh
docker run --name redmine -d \
  --link postgresql:postgresql \
  --volumes-from gitlab-redmine-data \
  -p 20022:22 -p 20080:80 \
  -e "DB_USER=redmine" -e "DB_PASS=redmine" \
  -e "DB_NAME=redmine_production" \
  -e "SMTP_HOST=ariadna.afip.gob.ar" \
  -e "SMTP_PORT=25" \
  -e "SMTP_STARTTLS=true" \
  -e "SMTP_DOMAIN=zaffarano.com.ar" \
  -e "SMTP_USER=mailer" \
  -e "SMTP_PASS=mailer" \
  sebas/redmine

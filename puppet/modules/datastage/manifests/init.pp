class datastage {
	include supervisor

	Exec { path => "/usr/bin:/usr/sbin/:/bin:/sbin" }

	$user = "datastage"
	$home = "/var/lib/dataflow-datastage/"
	$password_file = "/var/lib/dataflow-datastage/database-password"
	$data_directory = "/srv/datastage"
	$django_settings_module = "datastage.web.settings"

	$uwsgi_config_file = "/usr/share/dataflow-datastage/conf/uwsgi-config.xml"

	$group_leader = "datastage-leader"
	$group_collab = "datastage-collaborator"
	$group_member = "datastage-member"
	$group_orphan = "datastage-orphan"

	user { $user:
		comment => "DataStage",
		ensure => present,
		home => $home,
		managehome => true
	}

	group { [$group_leader, $group_collab, $group_member, $group_orphan] :
		ensure => present
	}

	exec { "collectstatic":
		command => "django-admin collectstatic --settings=${django_settings_module} --noinput --link",
	}

	exec { "createdb":
		command => "sudo -u postgres createdb ${database} -O ${user}",
		require => [User[$user], Exec["postgres-user"]],
	}

	exec { "syncdb":
		command => "django-admin syncdb --settings=datastage.web.settings",
		require => Exec["createdb"],
	}

	exec { "database-password":
		command => "pwgen --secure 16 1 > ${password_file}",
		creates => $password_file,
	}

	exec { "postgres-user":
		command => "sudo -u postgres psql ${database} -c \"CREATE ROLE $SERVER_USER PASSWORD '`cat ${password_file}`' NOSUPERUSER NOCREATEDB NOCREATEROLE INHERIT LOGIN\"",
		require => Exec["database-password"],
	}

	# Allows us to create a tree without having to list all the parent
	# directories
	exec { "data-directory":
		command => "mkdir -p ${data_directory}",
		creates => $data_directory,
	}

	file {
		$data_directory:
			ensure => directory,
			owner => $user,
			group => $user;
		"${data_directory}/private":
			ensure => directory,
			user => $user,
			group => $group_leader;
		"${data_directory}/collab":
			ensure => directory,
			user => $user,
			group => $group_collab;
		"${data_directory}/shared":
			ensure => directory,
			user => $user,
			group => $group_member;
	}

	package { ["uwsgi", "python-celery", "python-django-celery",
	           "openssh-server", "samba"] :
		ensure => "installed"
	}

	service {
		"sshd":
			ensure => running,
			require => Package["openssh-server"];
		"samba":
			ensure => running,
			require => Package["samba"]
	}

	file { $uwsgi_config_file:
		ensure => file,
		content => template("datastage/uwsgi-config.xml"),
		user => $user,
		group => $group;
	}

	supervisor::service {
		"celeryd":
			ensure => present,
			command => "django-admin celeryd --settings=${django_settings_module}",
			user => $user,
			group => $user;
		
		"uwsgi":
			ensure => present,
			command => "uwsgi --xml ${uwsgi_config_file}",
			user => root,
			group => root;

# We're not using celerybeat (yet)
#		"celerybeat":
#			ensure => present,
#			command => "django-admin celerybeat --settings=${django_settings_module} --pidfile='/var/run/datastage-celerybeat.pid'",
#			user => $user,
#			group => $user;
	}	
}

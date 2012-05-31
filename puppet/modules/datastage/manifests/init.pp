class datastage {
	include supervisor
	include postgresql

	Exec { path => "/usr/bin:/usr/sbin/:/bin:/sbin" }

	$user = "datastage"
	$home = "/var/lib/dataflow-datastage/"
	$password_file = "/var/lib/dataflow-datastage/database-password"
	$data_directory = "/srv/datastage"
	$django_settings_module = "datastage.web.settings"
	$database = "datastage"

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

	exec { "syncdb":
		command => "sudo -u ${user} django-admin syncdb --settings=datastage.web.settings",
		require => [Postgresql::Database[$database], Exec["postgres-user-password"]],
	}

	exec { "database-password":
		command => "pwgen --secure 16 1 > ${password_file}",
		creates => $password_file,
	}

	postgresql::user { $user:
		ensure => present,
	}

	postgresql::database { $database:
		ensure => present,
		owner => $user,
	}

	exec { "postgres-user-password":
		command => "sudo -u postgres psql -c \"ALTER ROLE ${user} PASSWORD '`cat ${password_file}`'\"",
		require => Exec["database-password"],
		subscribe => Postgresql::User[$user],
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
			owner => $user,
			group => $group_leader;
		"${data_directory}/collab":
			ensure => directory,
			owner => $user,
			group => $group_collab;
		"${data_directory}/shared":
			ensure => directory,
			owner => $user,
			group => $group_member;
	}

	package { ["uwsgi", "python-celery", "python-django-celery",
	           "openssh-server", "samba", "redis-server"] :
		ensure => "installed"
	}

	service {
		"ssh":
			ensure => running,
			require => Package["openssh-server"];
		"smbd":
			ensure => running,
			require => Package["samba"];
		"redis-server":
			ensure => running,
			require => Package["redis-server"];
	}

	file { $uwsgi_config_file:
		ensure => file,
		content => template("datastage/uwsgi-config.xml"),
		owner => $user,
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

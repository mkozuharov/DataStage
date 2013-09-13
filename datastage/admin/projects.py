# ---------------------------------------------------------------------
#
# Copyright (c) 2012 University of Oxford
#
# Permission is hereby granted, free of charge, to any person obtaining
# a copy of this software and associated documentation files (the
# "Software"), to deal in the Software without restriction, including
# without limitation the rights to use, copy, modify, merge, publish,
# distribute, sublicense, and/or sell copies of the Software, and to
# permit persons to whom the Software is furnished to do so, subject to
# the following conditions:
#
# The above copyright notice and this permission notice shall be
# included in all copies or substantial portions of the Software.
# 
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
# EXPRESS OR IMPLIED, --INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF
# MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT.
# IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY
# CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT,
# TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE
# SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
# 
# ---------------------------------------------------------------------

import grp
import os
import pwd
import re
import subprocess
import shutil
import libmount

from django.contrib.auth.models import User, Group
from datastage.web.dataset.models import Project

from datastage.config import settings

from .menu_util import menu, ExitMenu
from .sync_permissions import sync_permissions
from .samba_config import SambaConfigurer

def projects_menu():
    """Main menu for configuring datastage projects.

    Prints a list with the information about all datastage projects.
    Presents available actions for adding a project or selecting an existing one for further modifications.

    """
    while True:
        print "======================="
        print "List of Datastage projects"
        print
        #print "======================="

        all_projects = Project.objects.all()

        print "Short name           Full name                      Description"
        print "======================================================================"
        for project in sorted(all_projects):
            print "%-20s %-30s %s" % (project.short_name,
                                      project.long_name,
                                      project.description)
        if not all_projects:
            print "--- There are currently no projects defined ---"
        print
        print "=============="
        print " Manage projects "
        print "=============="
        print "Select add(a) to add a new datastage project."
        print "Select remove(r) to remove a datastage project."
        print "Select select(s) to view and edit a datastage project."

        yield menu({'add': add_project,
                    'select': select_project})


def add_project():
    """Configuration screen for creating a new project.

    Asks for the following project attributes:
    short name -- must be unique, one word, shorter than 20 symbols and of this format - [a-z_][a-z0-9_-]*[$]?
    long name -- human-readable name for the project
    description -- general description of the project - purpose, department, etc.

    """
    short_name, long_name, description = None, None, None
    print "===================================="
    print "Add project (press Ctrl-D to cancel)"
    print "===================================="
    print "Short name must be one word, less than 20 characters and conforming to the following regexp:"
    print "[a-z_][a-z0-9_-]*[$]?"

    while True:
        print
        if short_name:
            short_name = raw_input("Short name (one word, max 20 characters) [%s]: " % short_name) or short_name
        else:
            short_name = raw_input("Short name (one word, max 20 characters): ")
        if long_name:
            long_name = raw_input("Long name [%s]: " % long_name) or long_name
        else:
            long_name = raw_input("Long name: ")
        if description:
            description = raw_input("Description [%s...]: " % description[:40]) or description
        else:
            description = raw_input("Description: ")

        #check if the short name can be used for a Debian group name
        match = re.match("^[a-z_][a-z0-9_-]*[$]?$", short_name)
        if not match or len(short_name)>20:
            print "Error: Invalid short project name."
            print "Must be one word, less than 20 characters and conforming to the following regexp:"
            print "[a-z_][a-z0-9_-]*[$]?"
            continue

        print "  Short name: %s" % short_name
        print "  Long name: %s" % long_name
        print "  Description: %s" % description
        yield menu({'yes': create_project(short_name, long_name, description),
                    'no': None},
                   question="Is this correct?",
                   prompt="Pick one> ")


def create_project(short_name, long_name, description):
    """Creates a new project in the database and OS.

    Creates database objects for the project and the corresponding groups - leaders, members and collaborators.
    Delegates OS group creation to sync_permissions()

    """
    try:
        project = Project.objects.get(short_name=short_name)
        if project:
            print "Error: Project with the same name (%s) already exists!" % short_name
            yield ExitMenu()
    except Project.DoesNotExist:
        #Project with same name not found, continue with normal operation
        None
    leader_group, _ = Group.objects.get_or_create(name="-".join([short_name, "leader"]))
    member_group, _ = Group.objects.get_or_create(name="-".join([short_name, "member"]))
    collab_group, _ = Group.objects.get_or_create(name="-".join([short_name, "collab"]))
    project, _ = Project.objects.get_or_create(short_name=short_name,
                                               long_name=long_name,
                                               description=description,
                                               leader_group=leader_group,
                                               member_group=member_group,
                                               collaborator_group=collab_group,
                                               is_archived=False)
    sync_permissions()
    SambaConfigurer.add_samba_groups([project.leader_group.name,
                                      project.member_group.name,
                                      project.collaborator_group.name])
    print "Project %s created successfully." % short_name
    yield ExitMenu(2)


def select_project():
    """Configuration screen for a single project.

    Prompts for a short project name and then displays information about that project.
    Available actions for the project are add/remove user and edit/delete project.

    """
    project_name = None
    while True:
        print
        print "Enter project name (press Ctrl-D to cancel)"
        project_name = raw_input("Project (short name): ")
        if not project_name:
            print "Error: No project name given"
            continue
        try:
            project = Project.objects.get(short_name=project_name)
        except Project.DoesNotExist:
            print "Error: No project with name", project_name, "found"
            continue
        print "======================="
        print
        print project.long_name
        print "Short name:", project.short_name
        print "Description:", project.description
        print "Data directory:", os.path.join(settings.DATA_DIRECTORY, project.short_name)
        print
        print "======================="
        print "Leaders:"
        print
        for user in sorted(project.leaders):
            print user
        print
        print "======================="
        print "Members:"
        print
        for user in sorted(project.members):
            print user
        print
        print "======================="
        print "Collaborators:"
        print
        for user in sorted(project.collaborators):
            print user

        yield menu({'add user': add_user_to_project(project),
                    'remove user': remove_user_from_project(project),
                    'edit project info': edit_project(project),
                    'delete project': remove_project(project)})


def add_user_to_project(project):
    """Configuration screen for adding a user to a project.

    Lists all datastage users and accepts a single username.
    Then delegates the actual work to map_user_with_project().

    """
    username = None
    print "============================================"
    print "Add user to project (press Ctrl-D to cancel)"
    print "============================================"
    print "\nThe Role of the user needs to be provided while adding a user to the project."
    print "Role: Leader/Member/Collaborator"
    print "r/w - Read/Write ; r - read only; NA - No Area"
    print "Leader:"
    print "The leader/head of the research group selects this role."
    print "          Own area      Other's area"
    print " Private:   r/w              r  "
    print " Shared :   r/w              r  "
    print " Collab :   r/w              r/w"
    print "Member:"
    print "Any member who is not the head/leader of the research group selects this role."
    print "          Own area      Other's area"
    print " Private:   r/w           no access"
    print " Shared :   r/w              r  "
    print " Collab :   r/w              r/w"
    print "Collaborator:"
    print " A person from one group holds this role within another research group for collaboration."
    print " A collaborator does not have his own private/shared/collab areas, but just holds an account on the system."
    print "          Own area      Other's area"
    print " Private:   NA            no access"
    print " Shared :   NA            no access"
    print " Collab :   NA               r/w"
    while True:
        print
        print "Username             Name"
        print "==================================================="
        all_users = set(User.objects.all()) - set(project.leaders) - set(project.members) - set(project.collaborators)
        for user in sorted(all_users):
            pwuser = pwd.getpwnam(user.username)
            print "%-20s %-30s" % (user.username, pwuser.pw_gecos)
        if not all_users:
            print "--- There are currently no users defined ---"
        print
        if username:
            username = raw_input("Username [%s]: " % username) or username
        else:
            username = raw_input("Username: ")

        try:
            user = User.objects.get(username=username)
        except User.DoesNotExist:
            print "Error: Username %s not found!" % username
            yield ExitMenu(2)

        if user in ( project.leaders | project.members | project.collaborators):
            print "Error: User %s already is a member of project %s!" % (username, project.short_name)
            yield ExitMenu(2)

        print "Select role for user %s:" % username
        yield menu({'leader': map_user_with_project(project, user, 'leader'),
                    'member': map_user_with_project(project, user, 'member'),
                    'collaborator': map_user_with_project(project, user, 'collab')})


def map_user_with_project(project, user, role):
    """Associates a user with a project in the required role.

    Adds the user database object to the required database group.
    Then calls sync_permissions() to create the filesystem directories and handle the permissions.

    Parameters:
    project -- the project object, to which the user will be added
    user -- the user object
    role -- one of 'leader', 'member', 'collab'

    """
    group = None
    if role == 'leader':
        group = project.leader_group
    elif role == 'member':
        group = project.member_group
    elif role == 'collab':
        group = project.collaborator_group
    else:
        print "Invalid role - %s" % role
        yield ExitMenu()
    group.user_set.add(user)
    sync_permissions()
    print "User", user.username, "added successfully to project", project.short_name
    yield ExitMenu(3)


def edit_project(project):
    """Edit project info.

    Change the project long name or description. The short name cannot be changed.

    """
    short_name = project.short_name
    long_name = project.long_name
    description = project.description
    print "===================================="
    print "Edit project (press Ctrl-D to cancel)"
    print "===================================="
    print
    print "Project: %s" % short_name
    while True:
        print
        if long_name:
            long_name = raw_input("Long name [%s]: " % long_name) or long_name
        else:
            long_name = raw_input("Long name: ")
        if description:
            description = raw_input("Description [%s...]: " % description[:40]) or description
        else:
            description = raw_input("Description: ")

        print "  Short name: %s" % short_name
        print "  Long name: %s" % long_name
        print "  Description: %s" % description
        yield menu({'yes': modify_project(project, long_name, description),
                    'no': None},
                   question="Is this correct?",
                   prompt="Pick one> ")


def modify_project(project, long_name, description):
    """Update the attributes of a project in the database.

    Parameters:
    project -- the project object, which we are modifying
    long_name -- a new value for the long_name attribute
    description -- a new value for the description attribute

    """
    project.long_name = long_name
    project.description = description
    project.save()
    ExitMenu(2)


def remove_user_from_project(project):
    """Configuration screen for removing a user from a project.

    Accessible from the single project menu.
    Prints a list with all users, associated with the project and their roles.
    Available actions are normal deletion, which preserves the user data, or purging, which deletes the data.
    The user is still available in datastage and remains a mamber of any other projects in which it may participate.

    """
    username = None
    while True:
        print "================================================="
        print "Remove user from project (press Ctrl-D to cancel)"
        print "================================================="
        print
        print "List of %s users:" % project.short_name
        print
        print "Username             Name                           Role"
        print "================================================================="
        leaders = project.leaders
        collabs = project.collaborators
        members = project.members

        all_users = leaders | collabs | members

        for user in sorted(all_users):
            pwuser = pwd.getpwnam(user.username)
            role = "leader" if user in leaders \
                else "member" if user in members \
                else "collaborator"
            print "%-20s %-30s %s" % (user.username, pwuser.pw_gecos, role)
        if not all_users:
            print "--- There are currently no users defined ---"
            yield ExitMenu(2)

        print
        if username:
            username = raw_input("Username [%s]: " % username) or username
        else:
            username = raw_input("Username: ")

        try:
            user = User.objects.get(username=username)
        except User.DoesNotExist:
            print "Error: User %s not found!" % username
            yield

        group = None
        if user in leaders:
            group = project.leader_group
        elif user in members:
            group = project.member_group
        elif user in collabs:
            group = project.collaborator_group

        print "\nRemoving user:", username, "from project:", project.short_name

        print "\nSelect purge(p) to delete the user areas with their data from the project."
        print "\nSelect yes(y) to only remove the user from the project and not the data. This process orphans the data."
        yield menu({'purge': purge_user_from_project(user, project, group),
                    'yes': delete_user_from_project(user, project, group),
                    'cancel': ExitMenu()},
                   question="Is this correct?",
                   prompt="Pick one> ")


def purge_user_from_project(user, project, group, sync=True):
    """Remove a user from a project and delete all user data for this project.

    Removes the user from the project's database and OS groups.
    Also deletes the user's directories from the project main directory.

    Parameters:
    :param user: The user object
    :param project: The project object, from which the user is removed
    :param group: The group object, to which the user currently belongs

    """
    data_directory = os.path.join(settings.DATA_DIRECTORY, project.short_name)

    #remove from db
    group.user_set.remove(user)

    #remove from os groups
    subprocess.call(['deluser', user.username, group.name])

    #orphan data
    for name in ('private', 'shared', 'collab'):
        path = os.path.join(data_directory, name, user.username)
        if os.path.exists(path):
            shutil.rmtree(path, True)
    if sync:
        sync_permissions()

    yield ExitMenu()


def delete_user_from_project(user, project, group, sync=True):
    """Remove a user from a project while retaining the data.

    Removes the user from the project's database and OS groups.
    Does not delete any files, only transfers the ownership to the datastage orphan user.

    Parameters:
    :param user: The user object
    :param project: The project object, from which the user is removed
    :param group: The group object, to which the user currently belongs

    """
    data_directory = os.path.join(settings.DATA_DIRECTORY, project.short_name)
    datastage_orphan = pwd.getpwnam(settings.get('main:datastage_orphan'))

    #remove from db
    group.user_set.remove(user)

    #remove from os groups
    subprocess.call(['deluser', user.username, group.name])

    #orphan data
    for name in ('private', 'shared', 'collab'):
        path = os.path.join(data_directory, name, user.username)
        if os.path.exists(path):
            os.chown(path, datastage_orphan.pw_uid, datastage_orphan.pw_gid)

    if sync:
        sync_permissions()
    yield ExitMenu()


def remove_project(project):
    """Configuration screen for deleting a project.

    Available actions are normal deletion, which preserves the user data, or purging, which deletes the data.
    When retaining the data ownership to the project's directory is transferred to the datastage orphan user.

    :param project: The project object to be deleted

    """
    print "======================================="
    print "Remove project (press Ctrl-D to cancel)"
    print "======================================="
    while True:
        print "\nRemoving project: %s" % project.short_name

        print "\nSelect purge(p) to delete the project area including data."
        print "\nSelect yes(y) to only delete the project from datastage and retain the data. This process orphans the data."
        yield menu({'purge': purge_project(project),
                    'yes': delete_project(project),
                    'cancel': ExitMenu()},
                   question="Is this correct?",
                   prompt="Pick one> ")


def purge_project(project):
    """Delete a project including all data."""
    data_directory = os.path.join(settings.DATA_DIRECTORY, project.short_name)

    SambaConfigurer.remove_samba_groups([project.leader_group.name,
                                         project.member_group.name,
                                         project.collaborator_group.name])

    #remove from db
    project.leader_group.delete()
    project.member_group.delete()
    project.collaborator_group.delete()
    project.delete()

    #delete directory from filesystem
    if os.path.exists(data_directory):
        shutil.rmtree(data_directory, True)

    sync_permissions()
    yield ExitMenu(3)


def delete_project(project):
    """Delete a project, but retain the data.

    The new owner of the project data directory is the datastage orphan user.

    """
    data_directory = os.path.join(settings.DATA_DIRECTORY, project.short_name)

    SambaConfigurer.remove_samba_groups([project.leader_group.name,
                                         project.member_group.name,
                                         project.collaborator_group.name])

    #remove from db
    project.leader_group.delete()
    project.member_group.delete()
    project.collaborator_group.delete()
    project.delete()

    #orphan the data
    datastage_orphan = pwd.getpwnam(settings.get('main:datastage_orphan'))
    if os.path.exists(data_directory):
        os.chown(data_directory, datastage_orphan.pw_uid, datastage_orphan.pw_gid)

    sync_permissions()
    yield ExitMenu(3)

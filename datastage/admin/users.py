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
import random
import re
import string
import subprocess
import libmount
import getpass

from django.contrib.auth.models import User

from datastage.config import settings
from .menu_util import menu, ExitMenu
from .sync_permissions import sync_permissions
from datastage.admin.projects import purge_user_from_project, delete_user_from_project


def users_menu():
    """Main configuration menu for users

    Prints a list with all datastage users.
    Available options are:
    - creating a new user on the system and adding it to datastage
    - adding an user to datastage, which already exists on the system
    - changing user password - this changes both system and samba password
    - deleting a user from datastage

    """
    while True:
        print "======================="
        print "List of Datatsage users"
        print "======================="
        print "Username             Name                           Email"
        print "==========================================================================="
        all_users = User.objects.all()
        for user in sorted(all_users):
            print "%-20s %-30s %s" % (user.username, user.get_full_name(), user.email)
        if not all_users:
            print "--- There are currently no users defined ---"
        print "=============="
        print " Manage users "
        print "=============="
        print "Select add_existing(a) to add an existing OS user to datastage."
        print "Select create_new(cr) to create a new user on the system and add it to datastage."
        print "Select remove(r) to remove a datastage user."
        print "Select change_password(ch) to change datastage user password."

        yield menu({'add_existing': add_existing_user,
                    'create_new': add_new_user,
                    'remove': remove_user,
                    'change_password': change_passwd})


def add_new_user():
    """Configuration screen for adding a new user.

    Prompts for user details - username, names, email.
    After that delegates the actual user creation to create_user

    """
    username, first_name, last_name, email = None, None, None, None
    print "================================="
    print "Add user (press Ctrl-D to cancel)"
    print "================================="

    while True:
        print
        if username:
            username = raw_input("Username [%s]: " % username) or username
        else:
            username = raw_input("Username: ")
        if first_name:
            first_name = raw_input("First name [%s]: " % first_name) or first_name
        else:
            first_name = raw_input("First name: ")
        if last_name:
            last_name = raw_input("Last name [%s]: " % last_name) or last_name
        else:
            last_name = raw_input("Last name: ")
        if email:
            email = raw_input("Email [%s]: " % email) or email
        else:
            email = raw_input("Email: ")

        #check if the username can be used for a Debian username
        match = re.match("^[a-z_][a-z0-9_-]*[$]?$", username)
        if not match or len(username) > 32:
            print "Error: Invalid username."
            print "Must be one word, less than 32 characters and must match to the following regexp:"
            print "[a-z_][a-z0-9_-]*[$]?"
            continue

        print "  Username: %s" % username
        print "  First name: %s" % first_name
        print "  Last name: %s" % last_name
        print "  Email: %s" % email
        yield menu({'yes': create_user(username, first_name, last_name, email),
                    'no': None},
                   question="Is this correct?",
                   prompt="Pick one> ")


def create_user(username, first_name, last_name, email):
    """Creates a new user on the system and adds it to datastage.

    Checks for username conflicts, creates the database objects and sets the password to a random string.
    The user is not added to any os or datastage groups, because it is not assigned to a project yet.

    """
    try:
        pwuser = pwd.getpwnam(username)
        if pwuser:
            print "Error: User with such name already exists!"
            yield ExitMenu(1)
    except KeyError:
        #User with such name does not exists. Continue normal operation
        None

    user, _ = User.objects.get_or_create(username=username)
    user.first_name = first_name
    user.last_name = last_name
    user.email = email

    result = subprocess.call(['useradd', username,
                                         '--comment', user.get_full_name(),
                                         '-m'])
    if result:
        print "Error: Unable to create user!"
        user.delete()
        yield ExitMenu(1)

    user.save()

    password = ''.join(random.choice(string.letters + string.digits) for i in range(12))
    with open(os.devnull, 'w') as devnull:
        for args in (['passwd'], ['smbpasswd', '-a', '-s']):
            passwd = subprocess.Popen(args + [username], stdin=subprocess.PIPE, stdout=devnull, stderr=devnull)
            passwd.stdin.write('%s\n%s\n' % (password, password))
            passwd.stdin.close()
            passwd.wait()

    print "The password for the new user is:  %s" % password
    sync_permissions()
    print "User %s successfully created and added to datastage." % username
    yield ExitMenu(2)


def add_existing_user():
    """Configuration screen for adding an existing os user to datastage.

    Prompts for user infirmation - username, names and email and calls create_existing_user

    """
    username, first_name, last_name, email = None, None, None, None
    print "================================="
    print "Add user (press Ctrl-D to cancel)"
    print "================================="
    print "Username             Name                      "
    print "==============================================="
    pwusers = pwd.getpwall()
    for pwuser in pwusers:
        print "%-20s %-30s" % (pwuser[0], pwuser[4])
    while True:
        print
        if username:
            username = raw_input("Username [%s]: " % username) or username
        else:
            username = raw_input("Username: ")
        if first_name:
            first_name = raw_input("First name [%s]: " % first_name) or first_name
        else:
            first_name = raw_input("First name: ")
        if last_name:
            last_name = raw_input("Last name [%s]: " % last_name) or last_name
        else:
            last_name = raw_input("Last name: ")
        if email:
            email = raw_input("Email [%s]: " % email) or email
        else:
            email = raw_input("Email: ")

        print "Enter user details (press Ctrl-D to cancel)"
        print "  Username: %s" % username
        print "  First name: %s" % first_name
        print "  Last name: %s" % last_name
        print "  Email: %s" % email
        yield menu({'yes': create_existing_user(username, first_name, last_name, email),
                    'no': None},
                   question="Is this correct?",
                   prompt="Pick one> ")


def create_existing_user(username, first_name, last_name, email):
    """Registers an existing os user with datastage.

    Checks for username conflicts and creates the database objects. The existing user password is not changed.
    If the /etc/passwd comment field is empty, it is set with the full user name.
    The user is not added to any os or datastage groups, because it is not assigned to a project yet.
    The user has to be registered with a samba password manually, because we do not know the actual user password.

    """
    user, created = User.objects.get_or_create(username=username)
    if not created:
        print "Error: Datastage user with such username already exists!"
        yield ExitMenu(1)

    user.first_name = first_name
    user.last_name = last_name
    user.email = email
    user.save()

    #set full name as comment in /etc/passwd if empty
    pwuser = pwd.getpwnam(username)
    if not pwuser[4]:
        result = subprocess.call(['chfn', '-f', user.get_full_name(), username])
    sync_permissions()
    print "User %s successfully added to datastage." % username
    print "Please run 'smbpasswd -a -s' to configure sabma password for this user,"
    print "or execute the change password routine from this utility."
    yield ExitMenu(2)


def change_passwd():
    """Configuration screen for changing the password of a user.

    Changes both system and samba passwords.

    """
    print "========================================"
    print "Change Password (press Ctrl-D to cancel)"
    print "========================================"
    print "Provide a Username to change the password"
    username = raw_input("Username: ")
    password = getpass.getpass("Password: ")
    with open(os.devnull, 'w') as devnull:
        for args in (['passwd'], ['smbpasswd', '-a', '-s']):
            passwd = subprocess.Popen(args + [username], stdin=subprocess.PIPE, stdout=devnull, stderr=devnull)
            passwd.stdin.write('%s\n%s\n' % (password, password))
            passwd.stdin.close()
            passwd.wait()
    print "Password changed successfully"


def remove_user():
    """Configuration screen for removing a user from datastage,

    The user can be deleted while retaining its data, or the data can be deleted along with the user.

    """
    username = None
    print "===================================="
    print "Remove user (press Ctrl-D to cancel)"
    print "===================================="
    while True:
        print
        if username:
            username = raw_input("Username [%s]: " % username) or username
        else:
            username = raw_input("Username: ")

        print "\nRemoving user: %s" % username

        print "\nSelect purge(p) to delete the user areas with their data and also the user account."
        print "\nSelect yes(y) to only delete the user account and not the data. This process orphans the data."
        yield menu({'purge': purge_user(username),
                    'yes': delete_user(username),
                    'cancel': ExitMenu()},
                   question="Is this correct?",
                   prompt="Pick one> ")


def purge_user(username):
    """Delete a user from datastage including all user data in all projects in which the user participates.

    The os user can be retained or deleted.

    """
    user, groups = None, None
    try:
        user = User.objects.get(username=username)
    except User.DoesNotExist:
        print "Error: User with username %s not found!"
        yield ExitMenu()

    groups = user.groups.all()
    for group in groups:
        #remove the user from all projects, in which it participates
        if group.name.endswith('leader'):
            project = group.leaders_of_project
        elif group.name.endswith('member'):
            project = group.members_of_project
        elif group.name.endswith('collab'):
            project = group.collaborators_of_project
        yield purge_user_from_project(user, project, group, False)

    #delete the user object from the database
    user.delete()

    res = subprocess.call(['smbpasswd', username, '-x'])
    if res:
        print "Unable to delete samba user."

    delete_os_user = menu({'delete': True,
                     'preserve': False},
                    with_quit=False,
                    question="Should the OS user be deleted(d) or preserved(p)?",
                    prompt="Pick one> ")
    if delete_os_user:
        result = subprocess.call(['userdel', username])
        if result:
            print "Unable to delete OS user."
            yield ExitMenu()

    sync_permissions()
    print "User %s and data deleted." % username
    yield ExitMenu(2)


def delete_user(username):
    """Delete a user from datastage while preserving all user data.

    The user data is orphaned and the ownership is transferred to the datastage orphan user.
    The os user can be retained or deleted.

    """
    user, groups, projects = None, None, []
    datastage_orphan = pwd.getpwnam(settings.get('main:datastage_orphan'))
    try:
        user = User.objects.get(username=username)
    except User.DoesNotExist:
        print "Error: User with username %s not found!"
        yield ExitMenu()

    groups = user.groups.all()
    for group in groups:
        #remove the user from all projects, in which it participates
        if group.name.endswith('leader'):
            project = group.leaders_of_project
        elif group.name.endswith('member'):
            project = group.members_of_project
        elif group.name.endswith('collab'):
            project = group.collaborators_of_project
        yield delete_user_from_project(user, project, group, False)

    #delete the user object from the database
    user.delete()

    res = subprocess.call(['smbpasswd', username, '-x'])
    if res:
        print "Unable to delete samba user."

    delete_os_user = menu({'delete': True,
                     'preserve': False},
                    with_quit=False,
                    question="Should the OS user be deleted(d) or preserved(p)?",
                    prompt="Pick one> ")
    if delete_os_user:
        result = subprocess.call(['userdel', username])
        if result:
            print "Unable to delete OS user."
            yield ExitMenu()

    sync_permissions()
    print "User %s deleted." % username
    yield ExitMenu(2)

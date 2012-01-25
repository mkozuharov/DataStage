#!/bin/bash

source /root/admiralconfig.d/admiralconfig.sh

groupadd -g $RGLeaderGID RGLeader
groupadd -g $RGMemberGID RGMember
groupadd -g $RGCollabGID RGCollaborator
groupadd -g $RGOrphanGID RGOrphan

echo =========================
echo Allowing file access
echo =========================

source /root/admiraldataaccess.sh

# End.

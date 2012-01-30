#!/bin/bash

source /root/datastageconfig.d/datastageconfig.sh

groupadd -g $RGLeaderGID RGLeader
groupadd -g $RGMemberGID RGMember
groupadd -g $RGCollabGID RGCollaborator
groupadd -g $RGOrphanGID RGOrphan

echo =========================
echo Allowing file access
echo =========================

source /root/admiraldataaccess.sh

# End.

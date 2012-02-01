#!/bin/bash

# source /root/datastageconfig.d/datastageconfig.sh

echo ==========================================
echo "Extract datastage tools from code repository"
echo ==========================================
echo TODO: tag stable version of tools and use that
echo NOTE: tool directories are owned by root, with RO access for all
echo NOTE: see also /etc/apache2/sites-enabled/default-ssl

if [[ ! -e /mnt/data/tool/DataStage ]]; then
    mkdir -p /mnt/data/tool
    cd /mnt/data/tool
    git clone git@github.com:dataflow/DataStage.git
    cd  /mnt/data/tool/DataStage
    git checkout remotes/origin/ubuntu-10.4
    #mv /mnt/data/tool/DataStage /mnt/data/tool/DataStage
    cd /root
fi

# End.

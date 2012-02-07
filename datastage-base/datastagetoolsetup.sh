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

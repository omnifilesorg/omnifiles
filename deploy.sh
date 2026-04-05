#!/bin/bash
# Παράγει τα αρχεία και τα ανεβάζει στο Fastpath
cd /opt/omnifiles

# 1. Τρέξε generator
# python3 generate_v2.py --input batch.json --output-dir ./output --tpl-dir .

# 2. Ανέβασε στο Fastpath
lftp -u omnifiles.org_0k1qgrf5rcde,nkbvce6?KW5Z9l@k ftp://176.119.210.117 << EOF
set ftp:ssl-allow no
cd httpdocs
mirror -R /opt/omnifiles/output/ .
quit
EOF

echo "Deploy complete."

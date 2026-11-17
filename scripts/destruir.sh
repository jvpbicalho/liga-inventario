#!/usr/bin/env bash
# Esvazia os buckets (o CloudFormation não apaga bucket com arquivos) e apaga a stack inteira.
set -euo pipefail
cd "$(dirname "$0")/.."
source scripts/saidas.sh

for BUCKET in "$(saida PhotosBucketName)" "$(saida SiteBucketName)"; do
  aws s3 rm "s3://$BUCKET" --recursive
done
sam delete --stack-name "$STACK"

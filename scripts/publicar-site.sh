#!/usr/bin/env bash
# Gera o config.js com as saídas da stack, envia o site para o bucket e limpa o cache do CloudFront.
set -euo pipefail
cd "$(dirname "$0")/.."
source scripts/saidas.sh

SITE_BUCKET=$(saida SiteBucketName)
DIST_ID=$(saida DistributionId)

rm -rf .build-site && cp -r site .build-site
cat > .build-site/config.js <<FIM
window.LIGA_CONFIG = {
  apiUrl: "$(saida ApiUrl)",
  cognitoDomain: "$(saida CognitoDomain)",
  clientId: "$(saida UserPoolClientId)",
  redirectUri: window.location.origin + "/",
};
FIM

aws s3 sync .build-site/ "s3://$SITE_BUCKET/" --delete
aws cloudfront create-invalidation --distribution-id "$DIST_ID" --paths "/*" --query Invalidation.Id --output text
echo "Site publicado em $(saida SiteUrl)"

#!/usr/bin/env bash
# Uso: scripts/criar-usuario.sh EMAIL GRUPO   (GRUPO é admin ou membro)
# Cria o usuário já com senha definitiva, sem enviar e-mail de convite.
set -euo pipefail
cd "$(dirname "$0")/.."
source scripts/saidas.sh

EMAIL=${1:?informe o e-mail}
GRUPO=${2:?informe o grupo: admin ou membro}
POOL=$(saida UserPoolId)
read -r -s -p "Senha para $EMAIL: " SENHA
echo

aws cognito-idp admin-create-user --user-pool-id "$POOL" --username "$EMAIL" \
  --user-attributes Name=email,Value="$EMAIL" Name=email_verified,Value=true \
  --message-action SUPPRESS > /dev/null
aws cognito-idp admin-set-user-password --user-pool-id "$POOL" --username "$EMAIL" --password "$SENHA" --permanent
aws cognito-idp admin-add-user-to-group --user-pool-id "$POOL" --username "$EMAIL" --group-name "$GRUPO"
echo "Usuário $EMAIL criado no grupo $GRUPO"

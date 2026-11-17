# Funções compartilhadas pelos scripts: lê as saídas (Outputs) da stack do CloudFormation.
STACK=${STACK:-liga-inventario}

saida() {
  aws cloudformation describe-stacks --stack-name "$STACK" \
    --query "Stacks[0].Outputs[?OutputKey=='$1'].OutputValue" --output text
}

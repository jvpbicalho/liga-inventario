import json, os, uuid, boto3
from datetime import datetime, timezone

tabela = boto3.resource("dynamodb").Table(os.environ["TABELA_ITENS"])

def resposta(status, corpo):
    return {"statusCode": status, "headers": {"Content-Type": "application/json"}, "body": json.dumps(corpo, ensure_ascii=False)}

def eh_admin(event):
    claims = event["requestContext"]["authorizer"]["jwt"]["claims"]
    # no HTTP API a lista de grupos chega como texto: "[admin membro]"
    return "admin" in claims.get("cognito:groups", "").strip("[]").split()

def lambda_handler(event, context):
    if not eh_admin(event):
        return resposta(403, {"erro": "apenas administradores podem cadastrar itens"})
    dados = json.loads(event.get("body") or "{}")
    if not dados.get("nome"):
        return resposta(400, {"erro": "o campo 'nome' é obrigatório"})
    item = {
        "itemId": str(uuid.uuid4()),
        "nome": dados["nome"],
        "categoria": dados.get("categoria", "outros"),
        "status": "disponivel",
        "criadoEm": datetime.now(timezone.utc).isoformat(),
    }
    tabela.put_item(Item=item)
    return resposta(201, item)

import json, os, boto3
from botocore.exceptions import ClientError

tabela = boto3.resource("dynamodb").Table(os.environ["TABELA_ITENS"])
CAMPOS = ("nome", "categoria", "descricao")

def resposta(status, corpo):
    return {"statusCode": status, "headers": {"Content-Type": "application/json"}, "body": json.dumps(corpo, default=float, ensure_ascii=False)}

def eh_admin(event):
    claims = event["requestContext"]["authorizer"]["jwt"]["claims"]
    # no HTTP API a lista de grupos chega como texto: "[admin membro]"
    return "admin" in claims.get("cognito:groups", "").strip("[]").split()

def lambda_handler(event, context):
    if not eh_admin(event):
        return resposta(403, {"erro": "apenas administradores podem editar itens"})
    item_id = event["pathParameters"]["itemId"]
    dados = json.loads(event.get("body") or "{}")
    mudancas = {k: v for k, v in dados.items() if k in CAMPOS}
    if not mudancas:
        return resposta(400, {"erro": "envie ao menos um destes campos: " + ", ".join(CAMPOS)})
    try:
        r = tabela.update_item(
            Key={"itemId": item_id},
            UpdateExpression="SET " + ", ".join(f"#{k} = :{k}" for k in mudancas),
            ExpressionAttributeNames={f"#{k}": k for k in mudancas},
            ExpressionAttributeValues={f":{k}": v for k, v in mudancas.items()},
            ConditionExpression="attribute_exists(itemId)",
            ReturnValues="ALL_NEW",
        )
    except ClientError as e:
        if e.response["Error"]["Code"] == "ConditionalCheckFailedException":
            return resposta(404, {"erro": "item não encontrado"})
        raise
    return resposta(200, r["Attributes"])

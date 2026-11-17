import json, os, boto3
from datetime import datetime, timezone

dynamodb = boto3.client("dynamodb")
TABELA_ITENS = os.environ["TABELA_ITENS"]
TABELA_EMPRESTIMOS = os.environ["TABELA_EMPRESTIMOS"]

def resposta(status, corpo):
    return {"statusCode": status, "headers": {"Content-Type": "application/json"}, "body": json.dumps(corpo, ensure_ascii=False)}

def eh_admin(claims):
    # no HTTP API a lista de grupos chega como texto: "[admin membro]"
    return "admin" in claims.get("cognito:groups", "").strip("[]").split()

def lambda_handler(event, context):
    claims = event["requestContext"]["authorizer"]["jwt"]["claims"]
    item_id = event["pathParameters"]["itemId"]
    item = dynamodb.get_item(TableName=TABELA_ITENS, Key={"itemId": {"S": item_id}}).get("Item")
    if not item:
        return resposta(404, {"erro": "item não encontrado"})
    if item["status"]["S"] != "emprestado":
        return resposta(409, {"erro": "item não está emprestado"})
    if item["emprestadoPara"]["S"] != claims["sub"] and not eh_admin(claims):
        return resposta(403, {"erro": "só quem pegou o item ou um administrador pode devolver"})
    pedido_em = item["emprestimoAtual"]["S"]
    agora = datetime.now(timezone.utc).isoformat()
    try:
        dynamodb.transact_write_items(TransactItems=[
            {"Update": {
                "TableName": TABELA_ITENS,
                "Key": {"itemId": {"S": item_id}},
                "UpdateExpression": "SET #status = :disponivel REMOVE emprestadoPara, emprestimoAtual",
                # garante que ninguém mexeu no item entre a leitura e a escrita
                "ConditionExpression": "#status = :emprestado AND emprestimoAtual = :pedido",
                "ExpressionAttributeNames": {"#status": "status"},
                "ExpressionAttributeValues": {
                    ":disponivel": {"S": "disponivel"},
                    ":emprestado": {"S": "emprestado"},
                    ":pedido": {"S": pedido_em},
                },
            }},
            {"Update": {
                "TableName": TABELA_EMPRESTIMOS,
                "Key": {"itemId": {"S": item_id}, "pedidoEm": {"S": pedido_em}},
                "UpdateExpression": "SET situacao = :devolvido, devolvidoEm = :agora",
                "ConditionExpression": "situacao = :ativo",
                "ExpressionAttributeValues": {
                    ":devolvido": {"S": "devolvido"},
                    ":ativo": {"S": "ativo"},
                    ":agora": {"S": agora},
                },
            }},
        ])
    except dynamodb.exceptions.TransactionCanceledException:
        return resposta(409, {"erro": "o empréstimo mudou enquanto a devolução era registrada, tente de novo"})
    return resposta(200, {"itemId": item_id, "pedidoEm": pedido_em, "devolvidoEm": agora})

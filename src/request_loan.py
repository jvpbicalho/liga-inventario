import json, os, boto3
from datetime import datetime, timezone

dynamodb = boto3.client("dynamodb")
TABELA_ITENS = os.environ["TABELA_ITENS"]
TABELA_EMPRESTIMOS = os.environ["TABELA_EMPRESTIMOS"]

def resposta(status, corpo):
    return {"statusCode": status, "headers": {"Content-Type": "application/json"}, "body": json.dumps(corpo, ensure_ascii=False)}

def lambda_handler(event, context):
    claims = event["requestContext"]["authorizer"]["jwt"]["claims"]
    item_id = event["pathParameters"]["itemId"]
    agora = datetime.now(timezone.utc).isoformat()
    try:
        # as duas escritas acontecem juntas ou nenhuma acontece
        dynamodb.transact_write_items(TransactItems=[
            {"Update": {
                "TableName": TABELA_ITENS,
                "Key": {"itemId": {"S": item_id}},
                "UpdateExpression": "SET #status = :emprestado, emprestadoPara = :sub, emprestimoAtual = :agora",
                "ConditionExpression": "#status = :disponivel",
                "ExpressionAttributeNames": {"#status": "status"},
                "ExpressionAttributeValues": {
                    ":emprestado": {"S": "emprestado"},
                    ":disponivel": {"S": "disponivel"},
                    ":sub": {"S": claims["sub"]},
                    ":agora": {"S": agora},
                },
            }},
            {"Put": {
                "TableName": TABELA_EMPRESTIMOS,
                "Item": {
                    "itemId": {"S": item_id},
                    "pedidoEm": {"S": agora},
                    "membroId": {"S": claims["sub"]},
                    "membroEmail": {"S": claims.get("email", "")},
                    "situacao": {"S": "ativo"},
                },
            }},
        ])
    except dynamodb.exceptions.TransactionCanceledException:
        return resposta(409, {"erro": "item não existe ou já está emprestado"})
    return resposta(201, {"itemId": item_id, "pedidoEm": agora, "situacao": "ativo"})

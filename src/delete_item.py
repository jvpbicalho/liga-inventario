import json, os, boto3
from botocore.exceptions import ClientError

tabela = boto3.resource("dynamodb").Table(os.environ["TABELA_ITENS"])

def eh_admin(event):
    claims = event["requestContext"]["authorizer"]["jwt"]["claims"]
    # no HTTP API a lista de grupos chega como texto: "[admin membro]"
    return "admin" in claims.get("cognito:groups", "").strip("[]").split()

def lambda_handler(event, context):
    if not eh_admin(event):
        return {"statusCode": 403, "headers": {"Content-Type": "application/json"},
                "body": json.dumps({"erro": "apenas administradores podem apagar itens"})}
    item_id = event["pathParameters"]["itemId"]
    try:
        tabela.delete_item(Key={"itemId": item_id}, ConditionExpression="attribute_exists(itemId)")
    except ClientError as e:
        if e.response["Error"]["Code"] == "ConditionalCheckFailedException":
            return {"statusCode": 404, "headers": {"Content-Type": "application/json"},
                    "body": json.dumps({"erro": "item não encontrado"})}
        raise
    return {"statusCode": 204}

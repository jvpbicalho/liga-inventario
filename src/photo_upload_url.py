import json, os, boto3
from botocore.config import Config
from botocore.exceptions import ClientError

REGIAO = os.environ["AWS_REGION"]
# endpoint regional: buckets novos ainda não respondem no endereço global e o S3 devolve 307
s3 = boto3.client(
    "s3",
    region_name=REGIAO,
    endpoint_url=f"https://s3.{REGIAO}.amazonaws.com",
    config=Config(signature_version="s3v4", s3={"addressing_style": "virtual"}),
)
tabela = boto3.resource("dynamodb").Table(os.environ["TABELA_ITENS"])
BUCKET = os.environ["BUCKET_FOTOS"]
VALIDADE = 300  # segundos

def resposta(status, corpo):
    return {"statusCode": status, "headers": {"Content-Type": "application/json"}, "body": json.dumps(corpo, ensure_ascii=False)}

def eh_admin(event):
    claims = event["requestContext"]["authorizer"]["jwt"]["claims"]
    # no HTTP API a lista de grupos chega como texto: "[admin membro]"
    return "admin" in claims.get("cognito:groups", "").strip("[]").split()

def lambda_handler(event, context):
    if not eh_admin(event):
        return resposta(403, {"erro": "apenas administradores podem enviar fotos"})
    item_id = event["pathParameters"]["itemId"]
    chave = f"originais/{item_id}.jpg"
    try:
        tabela.update_item(
            Key={"itemId": item_id},
            UpdateExpression="SET fotoKey = :k",
            ExpressionAttributeValues={":k": chave},
            ConditionExpression="attribute_exists(itemId)",
        )
    except ClientError as e:
        if e.response["Error"]["Code"] == "ConditionalCheckFailedException":
            return resposta(404, {"erro": "item não encontrado"})
        raise
    url = s3.generate_presigned_url(
        "put_object",
        Params={"Bucket": BUCKET, "Key": chave, "ContentType": "image/jpeg"},
        ExpiresIn=VALIDADE,
    )
    return resposta(200, {"uploadUrl": url, "chave": chave, "expiraEmSegundos": VALIDADE})

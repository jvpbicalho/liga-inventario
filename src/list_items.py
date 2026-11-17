import json, os, boto3
from botocore.config import Config

REGIAO = os.environ["AWS_REGION"]
s3 = boto3.client(
    "s3",
    region_name=REGIAO,
    endpoint_url=f"https://s3.{REGIAO}.amazonaws.com",
    config=Config(signature_version="s3v4", s3={"addressing_style": "virtual"}),
)
tabela = boto3.resource("dynamodb").Table(os.environ["TABELA_ITENS"])
BUCKET = os.environ["BUCKET_FOTOS"]

def lambda_handler(event, context):
    itens = tabela.scan()["Items"]
    for item in itens:
        if "fotoKey" in item:
            # o bucket é privado: o site só vê a miniatura por uma URL de leitura temporária
            miniatura = "miniaturas/" + item["fotoKey"].removeprefix("originais/")
            item["miniaturaUrl"] = s3.generate_presigned_url(
                "get_object", Params={"Bucket": BUCKET, "Key": miniatura}, ExpiresIn=3600
            )
    return {
        "statusCode": 200,
        "headers": {"Content-Type": "application/json"},
        "body": json.dumps(itens, default=float, ensure_ascii=False),
    }

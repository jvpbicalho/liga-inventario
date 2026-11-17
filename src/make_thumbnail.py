import io, urllib.parse, boto3
from PIL import Image

s3 = boto3.client("s3")
TAMANHO = (200, 200)

def lambda_handler(event, context):
    for registro in event["Records"]:
        bucket = registro["s3"]["bucket"]["name"]
        chave = urllib.parse.unquote_plus(registro["s3"]["object"]["key"])
        if not chave.startswith("originais/"):
            continue  # proteção extra contra loop: nunca processa as próprias miniaturas
        original = s3.get_object(Bucket=bucket, Key=chave)["Body"].read()
        img = Image.open(io.BytesIO(original)).convert("RGB")
        img.thumbnail(TAMANHO)  # mantém a proporção, lado maior com até 200 px
        saida = io.BytesIO()
        img.save(saida, "JPEG", quality=85)
        destino = "miniaturas/" + chave.removeprefix("originais/")
        s3.put_object(Bucket=bucket, Key=destino, Body=saida.getvalue(), ContentType="image/jpeg")
        print(f"miniatura gerada: {destino} {img.size}")

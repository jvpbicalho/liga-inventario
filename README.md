# Inventário da liga acadêmica

Web app serverless na AWS para o inventário da liga: administradores cadastram itens (placas, cabos, notebooks, kits) com foto, e membros consultam o catálogo e pedem empréstimo.

Projeto de estudo de AWS, feito primeiro clicando no console e depois descrito como infraestrutura como código.

![Arquitetura](docs/arquitetura.png)

## Estrutura

| Pasta | Conteúdo |
| --- | --- |
| `src/` | Código Python das Lambdas (uma função por arquivo) |
| `site/` | Site estático em HTML e JavaScript, servido pelo CloudFront |
| `docs/` | Diagrama da arquitetura |
| `template.yaml` | Toda a infraestrutura descrita em AWS SAM |
| `layers/pillow/` | Receita da layer com a biblioteca de imagens Pillow (compilada para arm64) |
| `scripts/` | Publicar o site, criar usuários e destruir o ambiente |

## Lambdas

| Arquivo | Rota ou gatilho | Quem pode |
| --- | --- | --- |
| `list_items.py` | `GET /itens` | admin e membro |
| `create_item.py` | `POST /itens` | admin |
| `update_item.py` | `PUT /itens/{itemId}` | admin |
| `delete_item.py` | `DELETE /itens/{itemId}` | admin |
| `photo_upload_url.py` | `POST /itens/{itemId}/foto` | admin |
| `request_loan.py` | `POST /itens/{itemId}/emprestimo` | admin e membro |
| `return_item.py` | `POST /itens/{itemId}/devolucao` | quem pegou o item ou admin |
| `make_thumbnail.py` | evento do S3 em `originais/*.jpg` | (automático) |

## Deploy com SAM (pelo CloudShell)

O CloudShell já vem com AWS CLI, SAM CLI, git e as suas credenciais. Use a região **us-east-2 (Ohio)**.

```bash
git clone https://github.com/jvpbicalho/liga-inventario.git
cd liga-inventario
sam build                 # empacota as Lambdas e monta a layer do Pillow
sam deploy                # mostra o que vai ser criado e pede confirmação
scripts/publicar-site.sh  # gera o config.js com as saídas da stack e envia o site
scripts/criar-usuario.sh seuemail+admin@gmail.com admin
scripts/criar-usuario.sh seuemail+membro@gmail.com membro
```

O primeiro `sam deploy` leva uns 5 minutos, a maior parte esperando o CloudFront. No fim, ele mostra as saídas da stack; o endereço do site é o `SiteUrl`.

Se o `sam build` reclamar que não encontrou o `make`, instale com `sudo dnf install -y make`.

Para atualizar depois de mudar o código: `sam build && sam deploy` (Lambdas e infraestrutura) ou `scripts/publicar-site.sh` (só o site).

## Destruir o ambiente

```bash
scripts/destruir.sh
```

O script esvazia os dois buckets, porque o CloudFormation não apaga bucket com arquivos, e depois roda `sam delete`, que remove todo o resto.

## Custo

Pensado para caber nas cotas gratuitas: tabelas provisionadas em 1/1, Lambdas fora de VPC, sem NAT Gateway, sem WAF e sem Route 53. A API tem limite de 10 requisições em rajada e 5 por segundo.

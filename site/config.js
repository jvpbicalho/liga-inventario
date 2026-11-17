// Preencha com os valores da sua conta (Etapa 8c).
window.LIGA_CONFIG = {
  // Invoke URL da liga-api, sem "/" no final
  apiUrl: "https://XXXXXXXX.execute-api.us-east-2.amazonaws.com",
  // Cognito → user pool liga-web → Domínio (inclua o https://)
  cognitoDomain: "https://SEU-DOMINIO.auth.us-east-2.amazoncognito.com",
  // Client ID do app client (o mesmo "aud" do token)
  clientId: "7qi49pf1fru4md4dgq7dojlsde",
  // Endereço do próprio site, igual à callback URL cadastrada no Cognito
  redirectUri: window.location.origin + "/",
};
